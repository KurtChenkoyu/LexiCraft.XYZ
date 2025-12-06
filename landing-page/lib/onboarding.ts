/**
 * Onboarding utility functions
 */

import { authenticatedGet } from './api-client'

export interface OnboardingStatus {
  completed: boolean
  roles: string[]
  missing_info: string[]
  has_age: boolean
}

/**
 * Check if user has completed onboarding
 */
export async function checkOnboardingStatus(
  userId: string
): Promise<OnboardingStatus | null> {
  try {
    // Note: This endpoint now uses auth middleware, so user_id is extracted from token
    // The userId parameter is kept for backward compatibility but not used
    const data = await authenticatedGet<OnboardingStatus>(
      '/api/users/onboarding/status'
    )
    return data
  } catch (error) {
    console.error('Failed to check onboarding status:', error)
    return null
  }
}

/**
 * Check if user needs onboarding
 * Returns true if user needs to complete onboarding
 */
export async function needsOnboarding(userId: string): Promise<boolean> {
  const status = await checkOnboardingStatus(userId)
  return status ? !status.completed : false
}

