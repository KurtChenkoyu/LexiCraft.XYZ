import {
  Hero,
  ParentQuestions,
  VocabularyCliff,
  HowItWorks,
  BenefitsParents,
  BenefitsKids,
  Pricing,
  WaitlistForm,
  FAQ,
} from '@/components/marketing'
import { Footer } from '@/components/layout'

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero />
      <ParentQuestions />
      <VocabularyCliff />
      <HowItWorks />
      <BenefitsParents />
      <BenefitsKids />
      <Pricing />
      <FAQ />
      <WaitlistForm />
      <Footer />
    </main>
  )
}
