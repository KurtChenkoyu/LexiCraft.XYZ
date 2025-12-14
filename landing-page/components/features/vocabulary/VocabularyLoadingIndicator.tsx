/**
 * Vocabulary Loading Indicator
 * 
 * Shows loading indicator while vocabulary is being downloaded.
 * FIRST TIME: Full-screen blocking overlay (one-time setup)
 * SUBSEQUENT: Small subtle indicator in corner
 */

'use client'

import { useEffect, useState } from 'react'
import { vocabularyLoader, type LoaderStatus } from '@/lib/vocabularyLoader'

export function VocabularyLoadingIndicator() {
  const [status, setStatus] = useState<LoaderStatus>(vocabularyLoader.getCurrentStatus())
  const [isFirstTime, setIsFirstTime] = useState(false)

  useEffect(() => {
    // Start loading when component mounts
    vocabularyLoader.startLoading()
    
    // Subscribe to status updates
    const unsubscribe = vocabularyLoader.onStatusChange((newStatus) => {
      setStatus(newStatus)
      
      // Detect first-time setup (needs_hydration or downloading/parsing/inserting)
      if (newStatus.state === 'needs_hydration' || 
          newStatus.state === 'downloading' || 
          newStatus.state === 'parsing' || 
          newStatus.state === 'inserting') {
        setIsFirstTime(true)
      }
    })
    
    return unsubscribe
  }, [])

  // Hide indicator when vocabulary is ready
  if (status.state === 'idle' || 
      status.state === 'cached' || 
      status.state === 'complete') {
    return null
  }

  // FIRST TIME: Full-screen blocking overlay
  if (isFirstTime) {
    return (
      <div className="fixed inset-0 bg-slate-950/98 backdrop-blur-sm z-[100] flex items-center justify-center">
        <div className="max-w-md w-full mx-4 text-center">
          {/* Logo/Icon */}
          <div className="text-6xl mb-6 animate-bounce">📚</div>
          
          {/* Title */}
          <h2 className="text-2xl font-bold text-white mb-2">
            First Time Setup
          </h2>
          <p className="text-slate-400 mb-8">
            Downloading vocabulary dictionary for offline use.
            <br />
            <span className="text-cyan-400">This only happens once!</span>
          </p>
          
          {/* Status */}
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 mb-4">
            {status.state === 'needs_hydration' && (
              <div className="flex items-center justify-center gap-3">
                <div className="animate-spin h-5 w-5 border-2 border-cyan-400 border-t-transparent rounded-full" />
                <span className="text-white">Preparing...</span>
              </div>
            )}
            
            {status.state === 'downloading' && (
              <div className="space-y-3">
                <div className="flex items-center justify-center gap-3">
                  <div className="animate-spin h-5 w-5 border-2 border-cyan-400 border-t-transparent rounded-full" />
                  <span className="text-white">Downloading dictionary...</span>
                </div>
                <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                    style={{ width: `${status.progress}%` }}
                  />
                </div>
                <span className="text-cyan-400 font-mono text-lg">{status.progress}%</span>
              </div>
            )}
            
            {status.state === 'parsing' && (
              <div className="space-y-3">
                <div className="flex items-center justify-center gap-3">
                  <div className="animate-spin h-5 w-5 border-2 border-cyan-400 border-t-transparent rounded-full" />
                  <span className="text-white">Processing words...</span>
                </div>
                <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                    style={{ width: `${status.progress}%` }}
                  />
                </div>
                <span className="text-cyan-400 font-mono text-lg">{status.progress}%</span>
              </div>
            )}
            
            {status.state === 'inserting' && (
              <div className="space-y-3">
                <div className="flex items-center justify-center gap-3">
                  <div className="animate-spin h-5 w-5 border-2 border-cyan-400 border-t-transparent rounded-full" />
                  <span className="text-white">Building dictionary...</span>
                </div>
                {status.current !== undefined && status.total !== undefined && (
                  <div className="text-slate-400 text-sm">
                    {status.current.toLocaleString()} / {status.total.toLocaleString()} words
                  </div>
                )}
                <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                    style={{ width: `${status.progress || 0}%` }}
                  />
                </div>
                <span className="text-cyan-400 font-mono text-lg">{status.progress || 0}%</span>
              </div>
            )}
            
            {status.state === 'checking' && (
              <div className="flex items-center justify-center gap-3">
                <div className="animate-spin h-5 w-5 border-2 border-cyan-400 border-t-transparent rounded-full" />
                <span className="text-white">Checking cache...</span>
              </div>
            )}
            
            {status.state === 'error' && (
              <div className="space-y-3">
                <div className="text-red-400">❌ {status.error}</div>
                <button
                  onClick={() => vocabularyLoader.forceReload()}
                  className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                >
                  Retry Download
                </button>
              </div>
            )}
          </div>
          
          <p className="text-slate-500 text-sm">
            ⚡ After this, everything works offline!
          </p>
        </div>
      </div>
    )
  }

  // SUBSEQUENT LOADS: Subtle corner indicator (shouldn't normally show)
  return (
    <div className="fixed bottom-4 right-4 bg-slate-900/95 backdrop-blur-sm text-white px-4 py-3 rounded-lg shadow-xl border border-slate-700 z-[60]">
      <div className="flex items-center gap-3">
        <div className="animate-spin h-4 w-4 border-2 border-cyan-400 border-t-transparent rounded-full" />
        <span className="text-sm">
          {status.state === 'checking' && 'Checking dictionary...'}
          {status.state === 'needs_hydration' && 'Preparing dictionary...'}
          {status.state === 'downloading' && `Downloading... ${status.progress}%`}
          {status.state === 'parsing' && `Parsing... ${status.progress}%`}
          {status.state === 'inserting' && `Building... ${status.progress || 0}%`}
          {status.state === 'error' && '❌ Error'}
        </span>
      </div>
    </div>
  )
}

