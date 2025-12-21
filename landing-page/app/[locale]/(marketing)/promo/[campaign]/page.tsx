'use client'

import { use } from 'react'
import { notFound } from 'next/navigation'
import { getCampaignBySlug, CAMPAIGNS, getCheckoutUrl } from '@/lib/campaign-config'
import EmojiLandingPage from '@/components/marketing/EmojiLandingPage'

interface PageProps {
  params: Promise<{
    campaign: string
    locale: string
  }>
}

export default function CampaignPage({ params }: PageProps) {
  const { campaign: slug } = use(params)
  const campaign = getCampaignBySlug(slug)
  
  if (!campaign) {
    notFound()
  }
  
  // Get checkout URL (with A/B testing support if enabled)
  const checkoutUrl = getCheckoutUrl(campaign)
  
  return <EmojiLandingPage campaign={campaign} checkoutUrl={checkoutUrl} />
}

