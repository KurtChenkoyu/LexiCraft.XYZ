'use client'

/**
 * Learner Template - Zero Animation for Maximum Speed
 * 
 * ARCHITECTURE: "Last War" instant feel
 * 
 * Since all data is pre-loaded into Zustand by Bootstrap,
 * pages render instantly. No animation needed - animation
 * would only add overhead without benefit.
 * 
 * The navigation click feedback is handled in BottomNav.tsx
 * (scale + color change on active:).
 * 
 * @see .cursorrules - "Bootstrap Frontloading Strategy"
 */
export default function LearnerTemplate({
  children,
}: {
  children: React.ReactNode
}) {
  // No animation - instant render from Zustand
  return <>{children}</>
}

