import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'
import { routing } from '@/i18n/routing'

/**
 * Root OAuth Callback Route (Locale-Agnostic)
 * 
 * Handles OAuth provider callbacks (Google, etc.) for ALL locales.
 * After successful auth, redirects to /start (Traffic Cop) with locale.
 * 
 * This allows a single callback URL in Google OAuth settings:
 * https://lexicraft.xyz/auth/callback
 * 
 * Locale persistence strategy:
 * 1. Check query parameter first (?locale=zh-TW) - most explicit
 * 2. Fallback to cookie (NEXT_LOCALE) - for bookmarked links
 * 3. Default to routing.defaultLocale - ensures stable experience
 * 
 * @see .cursorrules - App Architecture Bible, Section 3 "Traffic Cop Pattern"
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const nextParam = requestUrl.searchParams.get('next') // Custom redirect from OAuth
  const localeParam = requestUrl.searchParams.get('locale') // Locale from OAuth
  
  // Determine locale: query param (most explicit) > cookie > default
  let locale = localeParam || routing.defaultLocale
  
  // Try to get locale from cookie (set during OAuth initiation or previous visit)
  if (!localeParam) {
    const cookies = request.headers.get('cookie')
    if (cookies) {
      const localeCookie = cookies
        .split(';')
        .find(c => c.trim().startsWith('NEXT_LOCALE='))
        ?.split('=')[1]
        ?.trim()
      
      if (localeCookie && routing.locales.includes(localeCookie as any)) {
        locale = localeCookie
      }
    }
  }
  
  // Validate locale against supported locales
  if (!routing.locales.includes(locale as any)) {
    locale = routing.defaultLocale
  }

  if (code) {
    const supabase = await createClient()
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (error) {
      console.error('Error exchanging code for session:', error)
      // Redirect to login on error (with locale)
      return NextResponse.redirect(new URL(`/${locale}/login?error=auth_failed`, requestUrl.origin))
    }
    
    // Verify session was created
    if (!data.session) {
      console.error('No session created after code exchange')
      return NextResponse.redirect(new URL(`/${locale}/login?error=no_session`, requestUrl.origin))
    }
  }

  // Use custom redirect if provided, otherwise go to Traffic Cop (with locale)
  // Traffic Cop handles role-based routing and onboarding checks
  const redirectUrl = nextParam || `/${locale}/start`
  
  return NextResponse.redirect(new URL(redirectUrl, requestUrl.origin))
}


