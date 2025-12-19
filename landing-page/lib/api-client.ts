/**
 * API Client Utilities
 * 
 * Provides helper functions for making authenticated API requests.
 */

import axios, { AxiosInstance } from 'axios'
import { createClient } from '@/lib/supabase/client'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Cache for axios instance and token
let cachedClient: AxiosInstance | null = null
let tokenCache: { token: string | null; timestamp: number } = { token: null, timestamp: 0 }
const TOKEN_CACHE_TTL = 300000 // 5 minute cache (tokens are valid for 1 hour)

// Singleton Supabase client for this module
let supabaseClient: ReturnType<typeof createClient> | null = null

function getSupabaseClient() {
  if (!supabaseClient) {
    supabaseClient = createClient()
  }
  return supabaseClient
}

/**
 * Get Supabase session token for API authentication (with caching)
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    // Return cached token if still valid (within 5 minutes)
    const now = Date.now()
    if (tokenCache.token && (now - tokenCache.timestamp) < TOKEN_CACHE_TTL) {
      return tokenCache.token
    }
    
    // Use singleton client - no new client creation!
    const supabase = getSupabaseClient()
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token || null
    
    // Cache the token
    tokenCache = { token, timestamp: now }
    return token
  } catch (error) {
    console.error('Failed to get auth token:', error)
    return null
  }
}

/**
 * Create an axios instance with authentication headers
 * Note: Creating fresh instances to avoid connection pooling issues
 */
export async function createAuthenticatedClient(): Promise<AxiosInstance> {
  const token = await getAuthToken()
  
  const client = axios.create({
    baseURL: API_BASE,
    timeout: 60000, // 60s timeout (increased for parallel requests on dev backend)
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  })
  
  // Add response interceptor for better error handling
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      // Handle 401 Unauthorized - clear cache and let callers decide how to react
      if (error.response?.status === 401) {
        console.warn('⚠️ Authentication failed (401) in API client, clearing token cache')
        // Clear cached token to force refresh on next request
        clearClientCache()
        return Promise.reject(error)
      }
      
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.debug('Request timeout - backend may be down:', error.config?.url)
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        console.debug('Network error - backend may be unreachable:', error.config?.url)
      }
      return Promise.reject(error)
    }
  )
  
  return client
}

/**
 * Clear cached client (useful when token changes or user logs out)
 */
export function clearClientCache() {
  cachedClient = null
  tokenCache = { token: null, timestamp: 0 }
  supabaseClient = null
}

/**
 * Make an authenticated GET request
 * 
 * Note: By default, we disable caching to ensure fresh data after mutations.
 * If you need caching for a specific request, pass cache: true in options.
 */
export async function authenticatedGet<T>(
  url: string, 
  options?: { cache?: boolean }
): Promise<T> {
  const client = await createAuthenticatedClient()
  const response = await client.get<T>(url, {
    headers: {
      // Disable caching by default (can be overridden with cache: true)
      ...(options?.cache ? {} : {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      }),
    },
  })
  return response.data
}

/**
 * Make an authenticated POST request
 */
export async function authenticatedPost<T>(
  url: string,
  data?: any
): Promise<T> {
  const client = await createAuthenticatedClient()
  const response = await client.post<T>(url, data)
  return response.data
}

/**
 * Make an authenticated PUT request
 */
export async function authenticatedPut<T>(
  url: string,
  data?: any
): Promise<T> {
  const client = await createAuthenticatedClient()
  const response = await client.put<T>(url, data)
  return response.data
}

/**
 * Make an authenticated DELETE request
 */
export async function authenticatedDelete<T>(url: string): Promise<T> {
  const client = await createAuthenticatedClient()
  const response = await client.delete<T>(url)
  return response.data
}

