'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { clearClientCache } from '@/lib/api-client'
import { User, Session } from '@supabase/supabase-js'
import { useRouter } from '@/i18n/routing'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
  refreshUser: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    // Check if Supabase is configured
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

    if (!supabaseUrl || !supabaseAnonKey) {
      // Supabase not configured - set loading to false and continue without auth
      setLoading(false)
      return
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }: { data: { session: Session | null } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    }).catch(() => {
      // If Supabase fails, just set loading to false
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event: string, session: Session | null) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [supabase])

  const signOut = async () => {
    try {
      // Clear API client cache to ensure fresh tokens on next login
      clearClientCache()
      
      // CRITICAL: Reset Zustand state (clears isBootstrapped flag AND learnerCache)
      try {
        const { useAppStore } = await import('@/stores/useAppStore')
        const store = useAppStore.getState()
        store.reset() // Sets isBootstrapped: false, clears learnerCache: {}, and all other state
        
        // Also clear IndexedDB (Tier 1 cache)
        const { downloadService } = await import('@/services/downloadService')
        await downloadService.clearAll()
      } catch (error) {
        console.error('Failed to reset app state on logout:', error)
        // Continue with logout even if reset fails
      }
      
      // Sign out from Supabase with global scope to clear all sessions
      const { error: signOutError } = await supabase.auth.signOut({ scope: 'global' })
      
      if (signOutError) {
        console.error('Sign out error:', signOutError)
        // Continue with redirect even if signOut fails
      }
      
      // Force hard redirect to clear any cached state (especially important for Chrome)
      // Use window.location.href instead of router.push for a full page reload
      window.location.href = '/'
    } catch (error) {
      console.error('Logout error:', error)
      // Fallback: force redirect even if something fails
      window.location.href = '/'
    }
  }

  const refreshUser = async () => {
    const { data: { user } } = await supabase.auth.getUser()
    setUser(user)
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

