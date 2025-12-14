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

import { getActiveCampaign, getDefaultCampaign } from '@/lib/campaign-config'
import EmojiLandingPage from '@/components/marketing/EmojiLandingPage'

export const metadata = {
  title: '表情學英文 - LexiCraft',
  description: '用表情符號學英文！專為 4-10 歲孩子設計的英語學習遊戲。',
}

export default function EmojiFunPage() {
  // Auto-select active campaign or use default
  const campaign = getActiveCampaign() || getDefaultCampaign()
  
  return <EmojiLandingPage campaign={campaign} />
}
