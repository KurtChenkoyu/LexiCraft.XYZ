import { redirect } from 'next/navigation'

/**
 * Learner Root - Redirects to /learner/home
 * 
 * There's no content at /learner, so redirect to the home page.
 * Next.js will automatically prefix with the locale.
 */
export default function LearnerPage() {
  redirect('/learner/home')
}

