'use client'

import { useEffect } from 'react'
import { trackPageView } from '@/lib/analytics'

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Initialize PostHog if configured
    const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY
    const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com'

    if (posthogKey && typeof window !== 'undefined') {
      // Dynamically load PostHog
      import('posthog-js').then((posthog) => {
        posthog.default.init(posthogKey, {
          api_host: posthogHost,
          loaded: (ph) => {
            if (process.env.NODE_ENV === 'development') {
              ph.debug()
            }
          },
        })
        // Make posthog available globally
        ;(window as any).posthog = posthog.default
        trackPageView()
      })
    } else {
      // Initialize Mixpanel if configured
      const mixpanelToken = process.env.NEXT_PUBLIC_MIXPANEL_TOKEN
      if (mixpanelToken && typeof window !== 'undefined') {
        // Dynamically load Mixpanel
        import('mixpanel-browser').then((mixpanel) => {
          mixpanel.default.init(mixpanelToken, {
            track_pageview: true,
          })
          ;(window as any).mixpanel = mixpanel.default
          trackPageView()
        })
      } else {
        // Fallback: track page view without analytics
        trackPageView()
      }
    }
  }, [])

  return <>{children}</>
}

