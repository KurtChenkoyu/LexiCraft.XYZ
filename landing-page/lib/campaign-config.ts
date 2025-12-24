/**
 * Campaign Configuration System
 * 
 * Industry standard approach for managing promotional landing pages:
 * 1. Centralized config for each campaign
 * 2. UTM tracking support
 * 3. Conversion event definitions
 * 4. Easy A/B testing support
 * 5. Lemon Squeezy checkout integration
 */

export interface CampaignConfig {
  // Identity
  id: string
  name: string
  slug: string // URL path: /promo/[slug]
  
  // Dates (for auto-activation)
  startDate: string // ISO date
  endDate: string
  
  // Theme
  theme: {
    primary: string // Tailwind gradient
    accent: string
    emoji: string
    snowflakes?: boolean
    floatingEmojis: string[]
  }
  
  // Content
  content: {
    heroTagline: string
    heroTitle: string
    heroSubtitle: string
    
    finalCTA: {
      title: string
      subtitle: string
      emojis: string
    }
    
    // Pricing
    originalPrice: number
    salePrice: number
    duration: string // e.g., "6個月"
    discountLabel: string // e.g., "-83%"
    priceAnchorText?: string // e.g., "~~原價 NT$599~~ 聖誕限時優惠"
  }
  
  // Checkout Configuration
  checkout: {
    // Lemon Squeezy checkout URL
    lemonSqueezyUrl: string
    // Optional: Stripe checkout (if you want to support both)
    stripeEnabled?: boolean
  }
  
  // Tracking
  tracking: {
    utmSource: string
    utmMedium: string
    utmCampaign: string
    // Conversion events
    events: {
      pageView: string
      ctaClick: string
      signupStart: string
      signupComplete: string
      checkoutStart: string
      checkoutComplete: string
    }
  }
  
  // A/B Testing
  abTest?: {
    enabled: boolean
    variants: Array<{
      id: string
      name: string
      lemonSqueezyUrl: string
      weight: number // 0-100, determines traffic split
    }>
    defaultVariant: string
  }
}

// ===========================================
// CAMPAIGN DEFINITIONS
// ===========================================

export const CAMPAIGNS: Record<string, CampaignConfig> = {
  // 🎄 Christmas 2024
  christmas: {
    id: 'christmas-2024',
    name: 'Christmas 2024',
    slug: 'christmas',
    startDate: '2024-12-01',
    endDate: '2024-12-31',
    
    theme: {
      primary: 'from-red-500 to-green-500',
      accent: 'text-red-400',
      emoji: '🎄',
      snowflakes: true,
      floatingEmojis: ['🍎', '🐶', '🌟', '🎄', '🎁', '⭐', '🎅', '🦌', '☃️', '🔔'],
    },
    
    content: {
      heroTagline: '🎄 聖誕節特別活動 🎅',
      heroTitle: '用表情符號學英文！',
      heroSubtitle: '專為初學者和 4-10 歲孩子設計的英語學習遊戲',
      
      finalCTA: {
        title: '這個聖誕節',
        subtitle: '送孩子一份學習的禮物',
        emojis: '🎄🎅🎁',
      },
      
      originalPrice: 599,
      salePrice: 99,
      duration: '6個月',
      discountLabel: '-83%',
      priceAnchorText: '~~原價 NT$599~~ 聖誕限時優惠',
    },
    
    checkout: {
      lemonSqueezyUrl: 'https://lexicraft-xyz.lemonsqueezy.com/checkout/buy/07397ed4-50a9-4cb0-aeb2-2c2db295fef1',
    },
    
    tracking: {
      utmSource: 'website',
      utmMedium: 'landing',
      utmCampaign: 'christmas-2024',
      events: {
        pageView: 'promo_christmas_view',
        ctaClick: 'promo_christmas_cta_click',
        signupStart: 'promo_christmas_signup_start',
        signupComplete: 'promo_christmas_signup_complete',
        checkoutStart: 'promo_christmas_checkout_start',
        checkoutComplete: 'promo_christmas_checkout_complete',
      },
    },
    
    // Example A/B Test: Test two different checkout URLs
    // Set enabled: true to activate A/B testing
    abTest: {
      enabled: false,
      variants: [
        {
          id: 'variant-a',
          name: 'Standard Checkout',
          lemonSqueezyUrl: 'https://lexicraft-xyz.lemonsqueezy.com/checkout/buy/07397ed4-50a9-4cb0-aeb2-2c2db295fef1',
          weight: 50, // 50% of traffic
        },
        {
          id: 'variant-b',
          name: 'Alternative Checkout',
          lemonSqueezyUrl: 'https://lexicraft-xyz.lemonsqueezy.com/checkout/buy/alternative-checkout-id',
          weight: 50, // 50% of traffic
        },
      ],
      defaultVariant: 'variant-a',
    },
  },
  
  // 🧧 Chinese New Year 2025
  cny: {
    id: 'cny-2025',
    name: 'Chinese New Year 2025',
    slug: 'cny',
    startDate: '2025-01-15',
    endDate: '2025-02-15',
    
    theme: {
      primary: 'from-red-600 to-amber-500',
      accent: 'text-amber-400',
      emoji: '🧧',
      snowflakes: false,
      floatingEmojis: ['🧧', '🐍', '🏮', '🎊', '💰', '🍊', '🧨', '🎆', '🐲', '✨'],
    },
    
    content: {
      heroTagline: '🧧 新春限定優惠 🐍',
      heroTitle: '用表情符號學英文！',
      heroSubtitle: '長途車程的最佳夥伴，和親戚小孩一起玩',
      
      finalCTA: {
        title: '這個農曆新年',
        subtitle: '讓孩子邊玩邊學，親戚都誇獎！',
        emojis: '🧧🐍🏮',
      },
      
      originalPrice: 599,
      salePrice: 99,
      duration: '6個月',
      discountLabel: '-83%',
      priceAnchorText: '~~原價 NT$599~~ 新春限時優惠',
    },
    
    checkout: {
      lemonSqueezyUrl: 'https://lexicraft-xyz.lemonsqueezy.com/checkout/buy/cny-checkout-id', // Update with actual CNY checkout URL
    },
    
    tracking: {
      utmSource: 'website',
      utmMedium: 'landing',
      utmCampaign: 'cny-2025',
      events: {
        pageView: 'promo_cny_view',
        ctaClick: 'promo_cny_cta_click',
        signupStart: 'promo_cny_signup_start',
        signupComplete: 'promo_cny_signup_complete',
        checkoutStart: 'promo_cny_checkout_start',
        checkoutComplete: 'promo_cny_checkout_complete',
      },
    },
  },
  
  // 📚 Back to School 2025
  backtoschool: {
    id: 'backtoschool-2025',
    name: 'Back to School 2025',
    slug: 'backtoschool',
    startDate: '2025-08-15',
    endDate: '2025-09-15',
    
    theme: {
      primary: 'from-blue-500 to-cyan-500',
      accent: 'text-cyan-400',
      emoji: '📚',
      snowflakes: false,
      floatingEmojis: ['📚', '✏️', '🎒', '📖', '🍎', '🎓', '✨', '🌟', '📝', '🔔'],
    },
    
    content: {
      heroTagline: '📚 開學季特別優惠 ✏️',
      heroTitle: '用表情符號學英文！',
      heroSubtitle: '新學期，新開始！讓孩子贏在起跑點',
      
      finalCTA: {
        title: '這個開學季',
        subtitle: '給孩子最棒的英語啟蒙禮物',
        emojis: '📚✏️🎒',
      },
      
      originalPrice: 599,
      salePrice: 99,
      duration: '6個月',
      discountLabel: '-83%',
      priceAnchorText: '~~原價 NT$599~~ 開學限時優惠',
    },
    
    checkout: {
      lemonSqueezyUrl: 'https://lexicraft-xyz.lemonsqueezy.com/checkout/buy/bts-checkout-id', // Update with actual BTS checkout URL
    },
    
    tracking: {
      utmSource: 'website',
      utmMedium: 'landing',
      utmCampaign: 'backtoschool-2025',
      events: {
        pageView: 'promo_bts_view',
        ctaClick: 'promo_bts_cta_click',
        signupStart: 'promo_bts_signup_start',
        signupComplete: 'promo_bts_signup_complete',
        checkoutStart: 'promo_bts_checkout_start',
        checkoutComplete: 'promo_bts_checkout_complete',
      },
    },
  },
}

// ===========================================
// HELPER FUNCTIONS
// ===========================================

/**
 * Get currently active campaign based on date
 * Falls back to default if no campaign is active
 */
export function getActiveCampaign(): CampaignConfig {
  const now = new Date()
  
  for (const campaign of Object.values(CAMPAIGNS)) {
    const start = new Date(campaign.startDate)
    const end = new Date(campaign.endDate)
    
    if (now >= start && now <= end) {
      return campaign
    }
  }
  
  // Fallback to default campaign (never returns null)
  return getDefaultCampaign()
}

/**
 * Get campaign by slug
 */
export function getCampaignBySlug(slug: string): CampaignConfig | null {
  return CAMPAIGNS[slug] || null
}

/**
 * Get default campaign (fallback)
 * 🎯 CHANGE THIS to switch campaigns manually
 * Options: CAMPAIGNS.christmas, CAMPAIGNS.cny, CAMPAIGNS.backtoschool
 */
export function getDefaultCampaign(): CampaignConfig {
  return CAMPAIGNS.christmas
}

/**
 * Get checkout URL with A/B testing support
 * 
 * If A/B testing is disabled, returns the default checkout URL.
 * If enabled, assigns users to variants based on weight and persists
 * the assignment in localStorage for consistent experience.
 */
export function getCheckoutUrl(campaign: CampaignConfig): string {
  // If A/B testing is disabled, return default URL
  if (!campaign.abTest?.enabled) {
    return campaign.checkout.lemonSqueezyUrl
  }
  
  // Get stored variant from localStorage (persistent across sessions)
  const storedVariant = typeof window !== 'undefined' 
    ? localStorage.getItem(`ab_variant_${campaign.id}`)
    : null
  
  if (storedVariant) {
    const variant = campaign.abTest.variants.find(v => v.id === storedVariant)
    if (variant) {
      return variant.lemonSqueezyUrl
    }
  }
  
  // Assign variant based on weight
  const random = Math.random() * 100
  let cumulativeWeight = 0
  
  for (const variant of campaign.abTest.variants) {
    cumulativeWeight += variant.weight
    if (random <= cumulativeWeight) {
      // Store variant for this user
      if (typeof window !== 'undefined') {
        localStorage.setItem(`ab_variant_${campaign.id}`, variant.id)
      }
      return variant.lemonSqueezyUrl
    }
  }
  
  // Fallback to default variant
  const defaultVariant = campaign.abTest.variants.find(
    v => v.id === campaign.abTest!.defaultVariant
  )
  return defaultVariant?.lemonSqueezyUrl || campaign.checkout.lemonSqueezyUrl
}

/**
 * Build UTM URL
 */
export function buildUtmUrl(baseUrl: string, campaign: CampaignConfig, additionalParams?: Record<string, string>): string {
  const params = new URLSearchParams({
    utm_source: campaign.tracking.utmSource,
    utm_medium: campaign.tracking.utmMedium,
    utm_campaign: campaign.tracking.utmCampaign,
    ...additionalParams,
  })
  
  return `${baseUrl}?${params.toString()}`
}

/**
 * Track campaign event (placeholder - integrate with your analytics)
 */
export function trackCampaignEvent(campaign: CampaignConfig, eventType: keyof CampaignConfig['tracking']['events'], metadata?: Record<string, any>) {
  const eventName = campaign.tracking.events[eventType]
  
  // Google Analytics 4
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', eventName, {
      campaign_id: campaign.id,
      campaign_name: campaign.name,
      ...metadata,
    })
  }
  
  // Posthog (if using)
  if (typeof window !== 'undefined' && (window as any).posthog) {
    (window as any).posthog.capture(eventName, {
      campaign_id: campaign.id,
      campaign_name: campaign.name,
      ...metadata,
    })
  }
  
  // Console log for development
  console.log(`📊 Campaign Event: ${eventName}`, {
    campaign: campaign.id,
    ...metadata,
  })
}

