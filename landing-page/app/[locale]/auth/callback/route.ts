import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

/**
 * OAuth Callback Route
 * 
 * Handles OAuth provider callbacks (Google, etc.)
 * After successful auth, redirects to /start (Traffic Cop)
 * which handles role-based routing and onboarding checks.
 * 
 * @see .cursorrules - App Architecture Bible, Section 3 "Traffic Cop Pattern"
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const nextParam = requestUrl.searchParams.get('next') // Custom redirect from OAuth
  
  // Extract locale from pathname (e.g., /zh-TW/auth/callback)
  const pathname = requestUrl.pathname
  const locale = pathname.split('/')[1] || 'zh-TW'

  if (code) {
    const supabase = await createClient()
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (error) {
      console.error('Error exchanging code for session:', error)
      // Redirect to login on error
      return NextResponse.redirect(new URL(`/${locale}/login?error=auth_failed`, requestUrl.origin))
    }
    
    // Verify session was created
    if (!data.session) {
      console.error('No session created after code exchange')
      return NextResponse.redirect(new URL(`/${locale}/login?error=no_session`, requestUrl.origin))
    }
  }

  // Use custom redirect if provided, otherwise go to Traffic Cop
  // Traffic Cop handles role-based routing and onboarding checks
  const redirectUrl = nextParam || `/${locale}/start`
  
  return NextResponse.redirect(new URL(redirectUrl, requestUrl.origin))
}

