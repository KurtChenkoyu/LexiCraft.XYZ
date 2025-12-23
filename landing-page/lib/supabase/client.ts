import { createBrowserClient } from '@supabase/ssr'

// Singleton client - only create once for performance!
let cachedClient: ReturnType<typeof createBrowserClient> | null = null

export function createClient() {
  // Return cached client if available (singleton pattern)
  if (cachedClient) {
    return cachedClient
  }
  
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    console.warn('Supabase environment variables not set. Authentication will not work.')
    cachedClient = createBrowserClient(
      'https://placeholder.supabase.co',
      'placeholder-key'
    )
  } else {
    cachedClient = createBrowserClient(supabaseUrl, supabaseAnonKey)
  }

  return cachedClient
}

/**
 * Reset the cached Supabase client (useful after connection issues)
 */
export function resetClient() {
  cachedClient = null
  console.log('🔄 Supabase client reset')
}

/**
 * Test Supabase connection health
 * Returns true if connection is healthy, false otherwise
 */
export async function testConnection(): Promise<boolean> {
  try {
    const client = createClient()
    const { data, error } = await client.auth.getSession()
    
    if (error) {
      console.warn('⚠️ Supabase connection test failed:', error.message)
      return false
    }
    
    // If we get here, connection is working (even if no session)
    console.log('✅ Supabase connection healthy')
    return true
  } catch (error: any) {
    console.error('❌ Supabase connection test error:', error.message)
    return false
  }
}

// Expose to window for browser console testing (development only)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).testSupabaseConnection = async () => {
    console.log('🔍 Testing Supabase connection...')
    const isHealthy = await testConnection()
    if (!isHealthy) {
      console.log('⚠️ Connection unhealthy, resetting client...')
      resetClient()
      const retryHealthy = await testConnection()
      if (retryHealthy) {
        console.log('✅ Connection restored after reset!')
      } else {
        console.error('❌ Connection still failing after reset')
      }
    }
    return isHealthy
  }
  
  // Expose createClient for console use
  (window as any).getSupabaseClient = () => {
    return createClient()
  }
  
  // Helper to assign parent role
  (window as any).assignParentRole = async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token
    
    if (!token) {
      console.error('❌ No session token. Please log in again.')
      return
    }
    
    const response = await fetch('http://localhost:8000/api/users/me/roles', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ role: 'parent' })
    })
    
    const result = await response.json()
    console.log('✅ Result:', result)
    
    if (result.success) {
      console.log('🔄 Refreshing page...')
      location.reload()
    } else {
      console.error('❌ Failed:', result)
    }
  }
  
  console.log('💡 Console helpers available:')
  console.log('   - testSupabaseConnection() - Test Supabase connection')
  console.log('   - getSupabaseClient() - Get Supabase client instance')
  console.log('   - assignParentRole() - Assign parent role to current user')
}

