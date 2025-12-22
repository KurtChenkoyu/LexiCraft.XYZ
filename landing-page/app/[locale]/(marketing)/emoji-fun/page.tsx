/**
 * Main Emoji Fun Landing Page
 * 
 * This is the default/evergreen landing page.
 * For promotional campaigns, use /promo/[campaign] routes:
 * - /promo/christmas
 * - /promo/cny
 * - /promo/backtoschool
 * 
 * Each campaign has its own config in lib/campaign-config.ts
 */

'use client'

import { getActiveCampaign, getDefaultCampaign, getCheckoutUrl } from '@/lib/campaign-config'
import EmojiLandingPage from '@/components/marketing/EmojiLandingPage'

export default function EmojiFunPage() {
  // Auto-select active campaign or use default
  const campaign = getActiveCampaign() || getDefaultCampaign()
  
  // Get checkout URL (with A/B testing support if enabled)
  const checkoutUrl = getCheckoutUrl(campaign)
  
  return <EmojiLandingPage campaign={campaign} checkoutUrl={checkoutUrl} />
}
