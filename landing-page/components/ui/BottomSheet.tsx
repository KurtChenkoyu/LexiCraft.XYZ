'use client'

import { ReactNode, useEffect, useRef, useState, useCallback } from 'react'
import { useIsMobile } from '@/hooks/useMediaQuery'

interface BottomSheetProps {
  /** Whether the sheet is open */
  isOpen: boolean
  /** Close handler */
  onClose: () => void
  /** Sheet content */
  children: ReactNode
  /** Maximum height as percentage of viewport (default: 90) */
  maxHeight?: number
  /** Whether to show drag handle (default: true) */
  showHandle?: boolean
  /** Title for the sheet (optional) */
  title?: string
}

/**
 * BottomSheet - Mobile-optimized modal that slides up from bottom
 * 
 * - Slide-up animation
 * - Drag handle for closing
 * - Touch-to-dismiss backdrop
 * - Falls back to centered modal on desktop
 */
export function BottomSheet({
  isOpen,
  onClose,
  children,
  maxHeight = 90,
  showHandle = true,
  title,
}: BottomSheetProps) {
  const isMobile = useIsMobile()
  const sheetRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState(0)
  const startY = useRef(0)

  // Handle touch start
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    startY.current = e.touches[0].clientY
    setIsDragging(true)
  }, [])

  // Handle touch move
  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isDragging) return
    
    const currentY = e.touches[0].clientY
    const diff = currentY - startY.current
    
    // Only allow dragging down
    if (diff > 0) {
      setDragOffset(diff)
    }
  }, [isDragging])

  // Handle touch end
  const handleTouchEnd = useCallback(() => {
    setIsDragging(false)
    
    // If dragged more than 100px, close the sheet
    if (dragOffset > 100) {
      onClose()
    }
    
    setDragOffset(0)
  }, [dragOffset, onClose])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  // Desktop: centered modal
  if (!isMobile) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose()
        }}
      >
        <div
          className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-in fade-in slide-in-from-bottom-4"
          onClick={(e) => e.stopPropagation()}
        >
          {title && (
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          {children}
        </div>
      </div>
    )
  }

  // Mobile: bottom sheet
  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        style={{
          opacity: isDragging ? 1 - dragOffset / 300 : 1,
        }}
      />

      {/* Sheet */}
      <div
        ref={sheetRef}
        className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl pb-safe"
        style={{
          maxHeight: `${maxHeight}vh`,
          transform: `translateY(${dragOffset}px)`,
          transition: isDragging ? 'none' : 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          animation: !isDragging ? 'slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1)' : undefined,
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Drag handle */}
        {showHandle && (
          <div className="flex justify-center pt-3 pb-2">
            <div className="w-10 h-1 bg-gray-300 rounded-full" />
          </div>
        )}

        {/* Title bar */}
        {title && (
          <div className="flex items-center justify-between px-4 pb-3 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="p-2 -mr-2 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Content */}
        <div className="overflow-y-auto" style={{ maxHeight: `calc(${maxHeight}vh - 60px)` }}>
          {children}
        </div>
      </div>

      {/* Slide up animation keyframes */}
      <style jsx>{`
        @keyframes slideUp {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}

export default BottomSheet

