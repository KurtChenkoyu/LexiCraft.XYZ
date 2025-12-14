import { redirect } from 'next/navigation'

/**
 * Parent Dashboard Root
 * 
 * This page redirects to the default tab (overview).
 * Per Architecture Bible, root page MUST redirect to default tab.
 * 
 * URL: /parent/dashboard → redirects to /parent/dashboard/overview
 * 
 * @see .cursorrules - App Architecture Bible, Section 4 "Tabbed Page Pattern"
 */
export default function DashboardPage() {
  redirect('/parent/dashboard/overview')
}

