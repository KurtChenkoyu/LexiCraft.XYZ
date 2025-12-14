'use client'

/**
 * CACHING STRATEGY (IMMUTABLE - DO NOT CHANGE):
 * 
 * This file follows the "Last War" caching approach:
 * - IndexedDB is the ONLY cache for user data
 * - localStorage is FORBIDDEN for user data
 * - Load from IndexedDB first, sync from API in background
 * 
 * See: docs/ARCHITECTURE_PRINCIPLES.md
 * 
 * DO NOT add localStorage usage for user data here.
 */

/**
 * UserDataContext - Client-side caching for user data
 * 
 * @deprecated Prefer using `useAppStore()` from stores/useAppStore.ts for new code.
 * This context is maintained for backward compatibility with existing components,
 * particularly parent routes that haven't been migrated yet.
 * 
 * For NEW components, use:
 * ```typescript
 * import { useAppStore, selectUser } from '@/stores/useAppStore'
 * const user = useAppStore(selectUser)
 * ```
 * 
 * This context caches user profile and children data locally,
 * avoiding constant API calls and providing instant UI updates.
 * 
 * Data is only fetched from API:
 * 1. On initial load (if not in cache)
 * 2. After explicit refresh (add child, update profile)
 * 3. When cache is invalidated
 * 
 * On login, triggers background download of ALL user data for instant page loads.
 */

import { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo, ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { authenticatedGet, authenticatedPost } from '@/lib/api-client'
import { downloadService } from '@/services/downloadService'
import { localStore } from '@/lib/local-store'

// Types
interface Child {
  id: string
  name: string | null
  age: number | null
  email: string
}

interface UserProfile {
  id: string
  email: string
  name: string | null
  age: number | null
  roles: string[]
  email_confirmed: boolean
}

interface Balance {
  total_earned: number
  available_points: number
  locked_points: number
  withdrawn_points: number
}

interface UserDataContextType {
  // Data
  profile: UserProfile | null
  children: Child[]
  selectedChildId: string | null
  balance: Balance
  
  // Loading states
  isLoading: boolean
  isRefreshing: boolean
  isSyncing: boolean
  
  // Actions
  selectChild: (childId: string) => void
  addChild: (name: string, age: number) => Promise<Child | null>
  refreshChildren: () => Promise<void>
  refreshProfile: () => Promise<void>
  refreshBalance: () => Promise<void>
  refreshAll: () => Promise<void>
  triggerSync: () => Promise<void>
}

const defaultBalance: Balance = {
  total_earned: 0,
  available_points: 0,
  locked_points: 0,
  withdrawn_points: 0,
}

const UserDataContext = createContext<UserDataContextType>({
  profile: null,
  children: [],
  selectedChildId: null,
  balance: defaultBalance,
  isLoading: true,
  isRefreshing: false,
  isSyncing: false,
  selectChild: () => {},
  addChild: async () => null,
  refreshChildren: async () => {},
  refreshProfile: async () => {},
  refreshBalance: async () => {},
  refreshAll: async () => {},
  triggerSync: async () => {},
})

// Cache keys (must match downloadService CACHE_KEYS)
const CACHE_KEYS = {
  PROFILE: 'user_profile',
  CHILDREN: 'children',
}

// Cache TTL (30 days - effectively permanent until invalidated)
const CACHE_TTL_MEDIUM = 30 * 24 * 60 * 60 * 1000

// localStorage key for selectedChildId (tiny UI preference - allowed)
const SELECTED_CHILD_KEY = 'lexicraft_selected_child'

export function UserDataProvider({ children: childrenProp }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth()
  
  
  // State
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [children, setChildren] = useState<Child[]>([])
  const [selectedChildId, setSelectedChildIdState] = useState<string | null>(null)
  const selectedChildIdRef = useRef(selectedChildId)
  const [balance, setBalance] = useState<Balance>(defaultBalance)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  
  // Wrapper to track selectedChildId updates
  const setSelectedChildId = useCallback((newId: string | null) => {
    selectedChildIdRef.current = newId
    setSelectedChildIdState(newId)
  }, [])
  
  // Update ref when state changes
  useEffect(() => {
    selectedChildIdRef.current = selectedChildId
  }, [selectedChildId])

  // Load from IndexedDB on mount (Last War approach - single cache system)
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const loadCachedData = async () => {
      try {
        // Load from IndexedDB (single source of truth)
        const [cachedProfile, cachedChildren] = await Promise.all([
          downloadService.getProfile(),
          downloadService.getChildren(),
        ])
        
        // Use cached data immediately if available
        if (cachedProfile) {
          setProfile(cachedProfile)
          console.log('⚡ Loaded profile from IndexedDB cache')
        }
        if (cachedChildren && cachedChildren.length > 0) {
          setChildren(cachedChildren)
          // Set first child as selected if none selected
          const cachedSelectedChild = localStorage.getItem(SELECTED_CHILD_KEY)
          if (cachedSelectedChild && cachedChildren.find(c => c.id === cachedSelectedChild)) {
            setSelectedChildId(cachedSelectedChild)
          } else if (cachedChildren.length > 0) {
            setSelectedChildId(cachedChildren[0].id)
          }
          console.log('⚡ Loaded children from IndexedDB cache')
        }
      } catch (e) {
        console.error('Failed to load cached data from IndexedDB:', e)
      }
    }
    
    loadCachedData()
  }, [])

  // Save to IndexedDB when data changes (Last War approach - single cache system)
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const saveData = async () => {
      try {
        // Save profile to IndexedDB
        if (profile) {
          await localStore.setCache(CACHE_KEYS.PROFILE, profile, CACHE_TTL_MEDIUM)
        }
        
        // Save children to IndexedDB
        if (children.length > 0) {
          await localStore.setCache(CACHE_KEYS.CHILDREN, children, CACHE_TTL_MEDIUM)
        }
        
        // Save selectedChildId to localStorage (tiny UI preference - allowed)
        if (selectedChildId) {
          localStorage.setItem(SELECTED_CHILD_KEY, selectedChildId)
        } else {
          localStorage.removeItem(SELECTED_CHILD_KEY)
        }
      } catch (e) {
        console.error('Failed to save to IndexedDB cache:', e)
      }
    }
    
    saveData()
  }, [profile, children, selectedChildId])

  // Fetch profile from API
  const fetchProfile = useCallback(async (): Promise<UserProfile | null> => {
    try {
      const data = await authenticatedGet<UserProfile>('/api/users/me')
      return data
    } catch (error) {
      console.error('Failed to fetch profile:', error)
      return null
    }
  }, [])

  // Fetch children from API
  const fetchChildren = useCallback(async (): Promise<Child[]> => {
    try {
      const data = await authenticatedGet<Child[]>('/api/users/me/children')
      return data
    } catch (error: any) {
      // 403 means user is not a parent - return empty array
      if (error?.response?.status === 403) {
        return []
      }
      console.error('Failed to fetch children:', error)
      return []
    }
  }, [])

  // Fetch balance from API
  const fetchBalance = useCallback(async (learnerId: string): Promise<Balance> => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/deposits/${learnerId}/balance`
      )
      if (response.ok) {
        return await response.json()
      }
      return defaultBalance
    } catch (error) {
      console.error('Failed to fetch balance:', error)
      return defaultBalance
    }
  }, [])

  // Refresh profile
  const refreshProfile = useCallback(async () => {
    const data = await fetchProfile()
    if (data) {
      setProfile(data)
      // Save to IndexedDB immediately
      await localStore.setCache(CACHE_KEYS.PROFILE, data, CACHE_TTL_MEDIUM)
    }
  }, [fetchProfile])

  // Refresh children
  const refreshChildren = useCallback(async () => {
    const data = await fetchChildren()
    setChildren(data)
    // Save to IndexedDB immediately
    await localStore.setCache(CACHE_KEYS.CHILDREN, data, CACHE_TTL_MEDIUM)
    // Update selected child if needed
    if (data.length > 0 && !selectedChildId) {
      setSelectedChildId(data[0].id)
    } else if (data.length === 0) {
      setSelectedChildId(null)
    }
  }, [fetchChildren, selectedChildId])

  // Refresh balance
  const refreshBalance = useCallback(async () => {
    if (selectedChildId) {
      const data = await fetchBalance(selectedChildId)
      setBalance(data)
    }
  }, [selectedChildId, fetchBalance])

  // Refresh all data
  const refreshAll = useCallback(async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([refreshProfile(), refreshChildren()])
      // Balance is refreshed when selectedChildId changes
    } finally {
      setIsRefreshing(false)
    }
  }, [refreshProfile, refreshChildren])

  // Trigger background sync of ALL user data
  const triggerSync = useCallback(async () => {
    if (!user?.id) return
    
    setIsSyncing(true)
    try {
      console.log('🔄 Triggering background sync...')
      const result = await downloadService.downloadAllUserData(user.id, (progress) => {
        console.debug(`Sync progress: ${progress.completed}/${progress.total} - ${progress.current}`)
      })
      
      if (result.success) {
        console.log('✅ Background sync complete')
        // Refresh from cache to update UI
        await refreshAll()
      } else {
        console.warn('⚠️ Background sync had errors:', result.errors)
      }
    } catch (error) {
      console.error('Background sync failed:', error)
    } finally {
      setIsSyncing(false)
    }
  }, [user?.id, refreshAll])

  // Select a child
  const selectChild = useCallback((childId: string) => {
    setSelectedChildIdState(childId)
  }, [selectedChildId])

  // Add a child
  const addChild = useCallback(async (name: string, age: number): Promise<Child | null> => {
    try {
      const response = await authenticatedPost<{
        success: boolean
        child_id: string
        child_name: string
      }>('/api/users/children', { name, age })
      
      if (response.success) {
        // Create new child object
        const newChild: Child = {
          id: response.child_id,
          name: response.child_name,
          age: age,
          email: `child-${response.child_id}@lexicraft.xyz`,
        }
        
        // Update local state immediately (optimistic update)
        const updatedChildren = [...children, newChild]
        setChildren(updatedChildren)
        
        // Save to IndexedDB immediately
        await localStore.setCache(CACHE_KEYS.CHILDREN, updatedChildren, CACHE_TTL_MEDIUM)
        
        // Select the new child
        setSelectedChildId(response.child_id)
        
        return newChild
      }
      return null
    } catch (error) {
      console.error('Failed to add child:', error)
      throw error
    }
  }, [])

  // Initial data fetch when user is authenticated
  useEffect(() => {
    // Skip if auth is still loading
    if (authLoading) return
    
    // Clear data on logout
    if (!user) {
      setProfile(null)
      setChildren([])
      setSelectedChildId(null)
      setBalance(defaultBalance)
      setIsLoading(false)
      // Clear IndexedDB (downloadService handles all user data)
      // Keep selectedChildId in localStorage (tiny UI preference)
      if (typeof window !== 'undefined') {
        downloadService.clearAll().catch(console.error)
        // Optionally clear selectedChildId on logout
        localStorage.removeItem(SELECTED_CHILD_KEY)
      }
      return
    }

    // Skip if we already have profile data (avoid duplicate fetches)
    if (profile) {
      setIsLoading(false)
      return
    }

    // Fetch data once
    let cancelled = false
    const loadData = async () => {
      setIsLoading(true)
      try {
        // Try to load from IndexedDB cache FIRST for instant display
        const [cachedProfile, cachedChildren] = await Promise.all([
          downloadService.getProfile(),
          downloadService.getChildren(),
        ])
        
        if (cancelled) return
        
        // Use cached data immediately if available
        if (cachedProfile) {
          setProfile(cachedProfile)
          console.log('⚡ Loaded profile from cache')
        }
        if (cachedChildren && cachedChildren.length > 0) {
          setChildren(cachedChildren)
          if (!selectedChildId) {
            setSelectedChildId(cachedChildren[0].id)
          }
          console.log('⚡ Loaded children from cache')
        }
        
        // If we have cached data, show it immediately
        if (cachedProfile) {
          setIsLoading(false)
        }
        
        // Then trigger background sync to get fresh data
        setIsSyncing(true)
        downloadService.downloadAllUserData(user.id, (progress) => {
          console.debug(`Sync: ${progress.completed}/${progress.total} - ${progress.current}`)
        }).then(async (result) => {
          if (cancelled) return
          
          // Update with fresh data from cache
          const [freshProfile, freshChildren, freshLearnerProfile] = await Promise.all([
            downloadService.getProfile(),
            downloadService.getChildren(),
            downloadService.getLearnerProfile(),
          ])
          
          if (freshProfile) setProfile(freshProfile)
          if (freshChildren) {
            setChildren(freshChildren)
            if (freshChildren.length > 0 && !selectedChildId) {
              setSelectedChildId(freshChildren[0].id)
            }
          }
          
          // CRITICAL: Update Zustand with fresh data (for instant reads across app)
          if (freshLearnerProfile) {
            const { useAppStore } = await import('@/stores/useAppStore')
            const store = useAppStore.getState()
            store.setLearnerProfile(freshLearnerProfile)
            console.log('✅ Synced learnerProfile to Zustand:', freshLearnerProfile.level.total_xp, 'XP')
            
            // Also sync achievements and goals
            const [achievements, goals] = await Promise.all([
              downloadService.getAchievements(),
              downloadService.getGoals(),
            ])
            if (achievements) store.setAchievements(achievements)
            if (goals) store.setGoals(goals)
          }
          
          if (result.errors.length > 0) {
            console.warn('⚠️ Some sync errors:', result.errors)
          }
        }).catch(console.error).finally(() => {
          if (!cancelled) {
            setIsSyncing(false)
            setIsLoading(false)
          }
        })
        
        // If no cache, also do a quick fetch for immediate display
        // Then save to IndexedDB for future loads
        if (!cachedProfile) {
          const [profileData, childrenData] = await Promise.all([
            fetchProfile(),
            fetchChildren(),
          ])
          
          if (cancelled) return
          
          if (profileData) {
            setProfile(profileData)
            // Save to IndexedDB immediately
            await localStore.setCache(CACHE_KEYS.PROFILE, profileData, CACHE_TTL_MEDIUM)
          }
          if (childrenData) {
            setChildren(childrenData)
            // Save to IndexedDB immediately
            await localStore.setCache(CACHE_KEYS.CHILDREN, childrenData, CACHE_TTL_MEDIUM)
            if (childrenData.length > 0 && !selectedChildId) {
              setSelectedChildId(childrenData[0].id)
            }
          }
          setIsLoading(false)
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load user data:', error)
          setIsLoading(false)
        }
      }
    }

    loadData()
    
    return () => { cancelled = true }
  }, [user?.id, authLoading]) // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch balance when selected child changes
  // FIXED: Removed refreshBalance from dependencies to break circular dependency
  // Only run when selectedChildId changes, not when refreshBalance function reference changes
  useEffect(() => {
    if (selectedChildId) {
      refreshBalance()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedChildId]) // Only depend on selectedChildId, not refreshBalance

  // FIXED: Memoize context value to prevent unnecessary re-renders of consumers
  // This breaks the infinite loop by ensuring the value object reference is stable
  const contextValue = useMemo(() => ({
    profile,
    children,
    selectedChildId,
    balance,
    isLoading,
    isRefreshing,
    isSyncing,
    selectChild,
    addChild,
    refreshChildren,
    refreshProfile,
    refreshBalance,
    refreshAll,
    triggerSync,
  }), [
    profile,
    children,
    selectedChildId,
    balance,
    isLoading,
    isRefreshing,
    isSyncing,
    selectChild,
    addChild,
    refreshChildren,
    refreshProfile,
    refreshBalance,
    refreshAll,
    triggerSync,
  ])

  return (
    <UserDataContext.Provider value={contextValue}>
      {childrenProp}
    </UserDataContext.Provider>
  )
}

export function useUserData() {
  const context = useContext(UserDataContext)
  // Return default values if provider is not available (e.g., on landing pages)
  // This allows AppTopNav to work on both landing and app pages
  if (!context) {
    return {
      profile: null,
      children: [],
      selectedChildId: null,
      balance: defaultBalance,
      isLoading: false,
      isRefreshing: false,
      isSyncing: false,
      selectChild: () => {},
      addChild: async () => null,
      refreshChildren: async () => {},
      refreshProfile: async () => {},
      refreshBalance: async () => {},
      refreshAll: async () => {},
      triggerSync: async () => {},
    }
  }
  return context
}

