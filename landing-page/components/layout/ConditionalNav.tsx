'use client'

import { usePathname } from 'next/navigation'
import AppTopNav from './AppTopNav'

/**
 * Conditional Navigation Wrapper
 * 
 * Shows AppTopNav only for non-learner routes.
 * Learner routes use their own HUD (LearnerTopBar).
 * 
 * Hidden for:
 * - /learner/* routes (have their own HUD)
 * - /start (loading screen)
 * 
 * Shown for:
 * - / (marketing)
 * - /parent/* (parent dashboard)
 * - /onboarding (shared)
 */
export function ConditionalNav({ locale }: { locale: string }) {
  const pathname = usePathname()
  
  // Hide AppTopNav for learner routes (they have their own HUD)
  if (pathname.includes('/learner')) {
    return null
  }
  
  // Hide for /start (loading screen has no nav)
  if (pathname.includes('/start')) {
    return null
  }
  
  return <AppTopNav currentLocale={locale} />
}

