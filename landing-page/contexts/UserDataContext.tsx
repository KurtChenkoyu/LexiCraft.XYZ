'use client'

/**
 * UserDataContext - Client-side caching for user data
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

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { authenticatedGet, authenticatedPost } from '@/lib/api-client'
import { downloadService } from '@/services/downloadService'

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

// Local storage keys
const STORAGE_KEYS = {
  PROFILE: 'lexicraft_user_profile',
  CHILDREN: 'lexicraft_user_children',
  SELECTED_CHILD: 'lexicraft_selected_child',
  CACHE_TIME: 'lexicraft_cache_time',
}

// Cache duration: 5 minutes
const CACHE_DURATION = 5 * 60 * 1000

export function UserDataProvider({ children: childrenProp }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth()
  
  // State
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [children, setChildren] = useState<Child[]>([])
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null)
  const [balance, setBalance] = useState<Balance>(defaultBalance)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    try {
      const cachedProfile = localStorage.getItem(STORAGE_KEYS.PROFILE)
      const cachedChildren = localStorage.getItem(STORAGE_KEYS.CHILDREN)
      const cachedSelectedChild = localStorage.getItem(STORAGE_KEYS.SELECTED_CHILD)
      const cacheTime = localStorage.getItem(STORAGE_KEYS.CACHE_TIME)
      
      const isCacheValid = cacheTime && (Date.now() - parseInt(cacheTime)) < CACHE_DURATION
      
      if (isCacheValid) {
        if (cachedProfile) setProfile(JSON.parse(cachedProfile))
        if (cachedChildren) {
          const parsedChildren = JSON.parse(cachedChildren)
          setChildren(parsedChildren)
          // Set first child as selected if none selected
          if (cachedSelectedChild) {
            setSelectedChildId(cachedSelectedChild)
          } else if (parsedChildren.length > 0) {
            setSelectedChildId(parsedChildren[0].id)
          }
        }
      }
    } catch (e) {
      console.error('Failed to load cached data:', e)
    }
  }, [])

  // Save to localStorage when data changes
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!profile) return
    
    try {
      localStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(profile))
      localStorage.setItem(STORAGE_KEYS.CHILDREN, JSON.stringify(children))
      if (selectedChildId) {
        localStorage.setItem(STORAGE_KEYS.SELECTED_CHILD, selectedChildId)
      }
      localStorage.setItem(STORAGE_KEYS.CACHE_TIME, Date.now().toString())
    } catch (e) {
      console.error('Failed to save to cache:', e)
    }
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
    }
  }, [fetchProfile])

  // Refresh children
  const refreshChildren = useCallback(async () => {
    const data = await fetchChildren()
    setChildren(data)
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
    setSelectedChildId(childId)
  }, [])

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
        setChildren(prev => [...prev, newChild])
        
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
      // Clear localStorage and IndexedDB
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEYS.PROFILE)
        localStorage.removeItem(STORAGE_KEYS.CHILDREN)
        localStorage.removeItem(STORAGE_KEYS.SELECTED_CHILD)
        localStorage.removeItem(STORAGE_KEYS.CACHE_TIME)
        downloadService.clearAll().catch(console.error)
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
          const [freshProfile, freshChildren] = await Promise.all([
            downloadService.getProfile(),
            downloadService.getChildren(),
          ])
          
          if (freshProfile) setProfile(freshProfile)
          if (freshChildren) {
            setChildren(freshChildren)
            if (freshChildren.length > 0 && !selectedChildId) {
              setSelectedChildId(freshChildren[0].id)
            }
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
        if (!cachedProfile) {
          const [profileData, childrenData] = await Promise.all([
            fetchProfile(),
            fetchChildren(),
          ])
          
          if (cancelled) return
          
          if (profileData) setProfile(profileData)
          if (childrenData) {
            setChildren(childrenData)
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
  useEffect(() => {
    if (selectedChildId) {
      refreshBalance()
    }
  }, [selectedChildId, refreshBalance])

  return (
    <UserDataContext.Provider
      value={{
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
      }}
    >
      {childrenProp}
    </UserDataContext.Provider>
  )
}

export function useUserData() {
  const context = useContext(UserDataContext)
  if (!context) {
    throw new Error('useUserData must be used within a UserDataProvider')
  }
  return context
}

