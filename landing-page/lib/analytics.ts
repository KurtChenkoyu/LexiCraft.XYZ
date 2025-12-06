// Analytics tracking functions
// Supports PostHog (primary) and Mixpanel (fallback)

export function trackEvent(eventName: string, properties?: Record<string, any>) {
  if (typeof window === 'undefined') return

  // Try PostHog first
  if (window.posthog) {
    window.posthog.capture(eventName, properties)
    return
  }

  // Fallback to Mixpanel
  if (window.mixpanel) {
    window.mixpanel.track(eventName, properties)
    return
  }

  // Fallback: console log in development
  if (process.env.NODE_ENV === 'development') {
    console.log('Analytics Event:', eventName, properties)
  }
}

export function trackPageView() {
  if (typeof window === 'undefined') return

  // Try PostHog first
  if (window.posthog) {
    window.posthog.capture('$pageview')
    return
  }

  // Fallback to Mixpanel
  if (window.mixpanel) {
    window.mixpanel.track('Page View', {
      page: window.location.pathname,
    })
    return
  }

  // Fallback: console log in development
  if (process.env.NODE_ENV === 'development') {
    console.log('Page View:', window.location.pathname)
  }
}

// Extend Window interface for TypeScript
declare global {
  interface Window {
    posthog?: {
      capture: (eventName: string, properties?: Record<string, any>) => void
      debug: () => void
    }
    mixpanel?: {
      track: (eventName: string, properties?: Record<string, any>) => void
    }
  }
}

