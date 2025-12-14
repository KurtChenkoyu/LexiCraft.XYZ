import { useState, useEffect } from 'react'

/**
 * Hook to detect if the device is mobile
 * Uses a simple width threshold (< 768px = mobile)
 */
export function useIsMobile(breakpoint: number = 768): boolean {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < breakpoint)
    }

    // Check on mount
    checkIsMobile()

    // Listen for resize
    window.addEventListener('resize', checkIsMobile)

    return () => window.removeEventListener('resize', checkIsMobile)
  }, [breakpoint])

  return isMobile
}

