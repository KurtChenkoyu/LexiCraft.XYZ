'use client'

import { getActiveCampaign, getCheckoutUrl } from '@/lib/campaign-config'
import EmojiLandingPage from '@/components/marketing/EmojiLandingPage'

/**
 * Main Marketing Landing Page
 * 
 * This page automatically displays the active campaign based on:
 * 1. Current date (auto-switches between campaigns)
 * 2. Manual override via getDefaultCampaign() in campaign-config.ts
 * 
 * To manually switch campaigns:
 * - Edit lib/campaign-config.ts
 * - Change getDefaultCampaign() return value
 * - Example: return CAMPAIGNS.cny (for Chinese New Year)
 */
export default function Home() {
  // 🎯 This automatically picks the right campaign
  const campaign = getActiveCampaign()
  
  // Get checkout URL (with A/B testing support if enabled)
  const checkoutUrl = getCheckoutUrl(campaign)
  
  // Pass checkout URL to the landing page component
  return <EmojiLandingPage campaign={campaign} checkoutUrl={checkoutUrl} />
}
