import { notFound } from 'next/navigation'
import { getCampaignBySlug, CAMPAIGNS } from '@/lib/campaign-config'
import EmojiLandingPage from '@/components/marketing/EmojiLandingPage'

interface PageProps {
  params: Promise<{
    campaign: string
    locale: string
  }>
}

// Generate static params for all campaigns
export async function generateStaticParams() {
  return Object.keys(CAMPAIGNS).map((slug) => ({
    campaign: slug,
  }))
}

// Generate metadata for SEO
export async function generateMetadata({ params }: PageProps) {
  const { campaign: slug } = await params
  const campaign = getCampaignBySlug(slug)
  
  if (!campaign) {
    return { title: 'Not Found' }
  }
  
  return {
    title: `${campaign.name} - LexiCraft 表情學英文`,
    description: campaign.content.heroSubtitle,
    openGraph: {
      title: `${campaign.name} - LexiCraft`,
      description: campaign.content.heroSubtitle,
    },
  }
}

export default async function CampaignPage({ params }: PageProps) {
  const { campaign: slug } = await params
  const campaign = getCampaignBySlug(slug)
  
  if (!campaign) {
    notFound()
  }
  
  return <EmojiLandingPage campaign={campaign} />
}

