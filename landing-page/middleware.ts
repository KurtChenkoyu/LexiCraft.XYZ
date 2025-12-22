import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import { routing } from './i18n/routing'

export async function middleware(request: NextRequest) {
  // Early return for static assets to avoid any processing
  const pathname = request.nextUrl.pathname
  if (pathname.startsWith('/_next/static') || pathname.startsWith('/_next/image')) {
    return NextResponse.next()
  }

  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  // Only initialize Supabase if environment variables are set
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (supabaseUrl && supabaseAnonKey) {
    try {
      // Create Supabase client
      const supabase = createServerClient(
        supabaseUrl,
        supabaseAnonKey,
        {
          cookies: {
            getAll() {
              return request.cookies.getAll()
            },
            setAll(cookiesToSet) {
              cookiesToSet.forEach(({ name, value, options }) => request.cookies.set(name, value))
              response = NextResponse.next({
                request,
              })
              cookiesToSet.forEach(({ name, value, options }) =>
                response.cookies.set(name, value, options)
              )
            },
          },
        }
      )

      // Refresh session if expired
      await supabase.auth.getUser()
    } catch (error) {
      // If Supabase fails, continue without auth (for graceful degradation)
      // Only log in development to avoid noise in production
      if (process.env.NODE_ENV === 'development') {
        console.error('Supabase auth error:', error)
      }
    }
  }

  // Handle locale routing (existing i18n logic)
  // (pathname already defined above)
  
  // Skip locale redirect for static assets (workers, vocabulary, audio) and API routes
  if (pathname.startsWith('/workers/') || pathname.startsWith('/api/') || pathname.startsWith('/audio/') || pathname.startsWith('/auth/callback') || pathname.endsWith('.json')) {
    return response
  }
  
  const pathnameHasLocale = routing.locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )

  if (!pathnameHasLocale) {
    const locale = routing.defaultLocale
    return NextResponse.redirect(
      new URL(`/${locale}${pathname.startsWith('/') ? '' : '/'}${pathname}`, request.url)
    )
  }

  // === URL MIGRATION REDIRECTS ===
  // Redirect old URLs to new role-based structure
  // @see .cursorrules - App Architecture Bible
  const redirectMap: Record<string, string> = {
    // Parent routes
    '/dashboard': '/parent/dashboard',
    '/coach-dashboard': '/parent/dashboard/analytics',
    '/children': '/parent/children',
    '/goals': '/parent/goals',
    '/achievements': '/parent/achievements',
    '/settings': '/parent/settings',
    '/deposits': '/parent/dashboard/finance',
    // Learner routes
    '/mine': '/learner/mine',
    '/build': '/learner/build',
    '/verification': '/learner/verification',
    '/leaderboards': '/learner/leaderboards',
    '/profile': '/learner/profile',
  }

  // Check if pathname matches any redirect (with locale prefix)
  for (const locale of routing.locales) {
    for (const [oldPath, newPath] of Object.entries(redirectMap)) {
      if (pathname === `/${locale}${oldPath}`) {
        return NextResponse.redirect(
          new URL(`/${locale}${newPath}`, request.url),
          { status: 301 } // Permanent redirect
        )
      }
    }
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
