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

