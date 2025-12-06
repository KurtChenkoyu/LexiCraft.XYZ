'use client'

import { ReactNode, useCallback } from 'react'
import { useIsMobile } from '@/hooks/useMediaQuery'

interface FloatingActionButtonProps {
  /** Button label text */
  label: string
  /** Icon to display (optional) */
  icon?: ReactNode
  /** Click handler */
  onClick: () => void
  /** Whether to show the button */
  visible?: boolean
  /** Color variant */
  variant?: 'primary' | 'secondary' | 'amber'
  /** Position from bottom (accounts for bottom nav) */
  position?: 'above-nav' | 'bottom-right'
}

/**
 * FloatingActionButton - Primary action button for mobile
 * 
 * - Positioned above bottom nav on mobile
 * - Provides haptic feedback on tap
 * - Animated entrance/exit
 */
export function FloatingActionButton({
  label,
  icon,
  onClick,
  visible = true,
  variant = 'primary',
  position = 'above-nav',
}: FloatingActionButtonProps) {
  const isMobile = useIsMobile()

  // Haptic feedback handler
  const handleClick = useCallback(() => {
    // Trigger haptic feedback if available
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      navigator.vibrate(10) // Short vibration
    }
    onClick()
  }, [onClick])

  // Don't render on desktop or when not visible
  if (!isMobile || !visible) return null

  // Variant styles
  const variantStyles = {
    primary: 'bg-cyan-500 hover:bg-cyan-400 text-white shadow-cyan-500/30',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-white shadow-slate-500/30',
    amber: 'bg-amber-500 hover:bg-amber-400 text-white shadow-amber-500/30',
  }

  // Position styles
  const positionStyles = {
    'above-nav': 'bottom-[72px] right-4 mb-safe',
    'bottom-right': 'bottom-4 right-4 mb-safe',
  }

  return (
    <button
      onClick={handleClick}
      className={`
        fixed z-40
        ${positionStyles[position]}
        px-5 py-3
        rounded-full
        font-semibold
        shadow-lg
        ${variantStyles[variant]}
        flex items-center gap-2
        transition-all duration-200
        active:scale-95
        animate-fade-in-up
      `}
      style={{
        animation: 'slideInBottom 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {icon && <span className="w-5 h-5">{icon}</span>}
      <span>{label}</span>
    </button>
  )
}

// Common FAB icons
export const FABIcons = {
  forge: (
    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z"
      />
    </svg>
  ),
  quiz: (
    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z"
      />
    </svg>
  ),
  deposit: (
    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  ),
  plus: (
    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  ),
}

export default FloatingActionButton

