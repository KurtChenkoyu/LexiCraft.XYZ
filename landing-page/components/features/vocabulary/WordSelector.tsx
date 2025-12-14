'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'

interface WordSelectorProps {
  senseId: string
  isSelected: boolean
  onToggle: () => void
  variant?: 'checkbox' | 'button' | 'icon'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

/**
 * WordSelector - Universal selector for adding words to queue
 * 
 * Works consistently across:
 * - Mining grid squares
 * - Word detail pages
 * - Synonym/antonym chips
 * 
 * Variants:
 * - checkbox: Traditional checkbox (for grid)
 * - button: Full "Add to Queue" button
 * - icon: Just the + icon (for chips)
 */
export function WordSelector({ 
  senseId, 
  isSelected, 
  onToggle, 
  variant = 'checkbox',
  size = 'md',
  className = '' 
}: WordSelectorProps) {
  const [isAnimating, setIsAnimating] = useState(false)
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    setIsAnimating(true)
    onToggle()
    
    // Reset animation after a short delay
    setTimeout(() => setIsAnimating(false), 300)
  }
  
  // Size classes
  const sizeClasses = {
    sm: 'w-4 h-4 text-xs',
    md: 'w-5 h-5 text-sm',
    lg: 'w-6 h-6 text-base',
  }
  
  if (variant === 'checkbox') {
    return (
      <motion.button
        onClick={handleClick}
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center 
          transition-all shadow-md ${className}
          ${isSelected 
            ? 'bg-cyan-500 text-white border-2 border-cyan-400' 
            : 'bg-white/90 text-slate-700 border-2 border-slate-300 hover:border-cyan-400'
          }`}
        whileTap={{ scale: 0.9 }}
        animate={isAnimating ? { scale: [1, 1.2, 1] } : {}}
      >
        {isSelected && <span>✓</span>}
      </motion.button>
    )
  }
  
  if (variant === 'button') {
    return (
      <motion.button
        onClick={handleClick}
        className={`px-3 py-1.5 rounded-lg font-medium transition-all ${className}
          ${isSelected
            ? 'bg-cyan-600 text-white'
            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        whileTap={{ scale: 0.95 }}
      >
        {isSelected ? '✓ In Queue' : '+ Add to Queue'}
      </motion.button>
    )
  }
  
  // Icon variant
  return (
    <motion.button
      onClick={handleClick}
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center
        transition-all ${className}
        ${isSelected
          ? 'bg-cyan-500/30 text-cyan-400'
          : 'bg-slate-700/50 text-slate-400 hover:bg-cyan-500/20 hover:text-cyan-400'
        }`}
      whileTap={{ scale: 0.9 }}
      animate={isAnimating ? { scale: [1, 1.3, 1] } : {}}
    >
      {isSelected ? '✓' : '+'}
    </motion.button>
  )
}


