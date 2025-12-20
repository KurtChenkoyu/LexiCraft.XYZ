'use client'

/**
 * App Layout for authenticated pages
 * 
 * ⚡ ARCHITECTURE PRINCIPLE: "As Snappy as Last War"
 * See: /docs/ARCHITECTURE_PRINCIPLES.md
 * 
 * This layout wraps ALL authenticated routes. Role-specific layouts
 * (ParentLayout, LearnerLayout) are handled by the route groups:
 * - parent/layout.tsx - ParentSidebar
 * - learner/layout.tsx - LearnerBottomNav
 * 
 * @see .cursorrules - App Architecture Bible
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useAppStore } from '@/stores/useAppStore'
import { UserDataProvider } from '@/contexts/UserDataContext'
import { SidebarProvider } from '@/contexts/SidebarContext'
import { VocabularyLoadingIndicator } from '@/components/features/vocabulary/VocabularyLoadingIndicator'
import { vocabularyLoader } from '@/lib/vocabularyLoader'
import { bootstrapApp } from '@/services/bootstrap'

// Loading step definition
interface LoadingStep {
  id: string
  label: string
  icon: string
  status: 'pending' | 'loading' | 'complete' | 'error'
  detail?: string
}

// Game-style loading screen component
function GameLoadingScreen({ steps, progress, isComplete }: {
  steps: LoadingStep[]
  progress: number
  isComplete: boolean
}) {
  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-cyan-500/10 to-transparent rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-purple-500/10 to-transparent rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 text-center max-w-md px-6 w-full">
        {/* Logo */}
        <div className="mb-8 relative">
          <div className="absolute inset-0 w-24 h-24 mx-auto bg-cyan-500/30 blur-2xl rounded-full" />
          <div className={`relative w-24 h-24 mx-auto bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-cyan-500/30 ${isComplete ? 'animate-bounce' : ''}`}>
            <span className="text-4xl font-bold text-white">塊</span>
          </div>
        </div>

        <h1 className="text-3xl font-bold text-white mb-2">LexiCraft</h1>
        <p className="text-slate-400 mb-8">
          {isComplete ? '✨ 準備完成！' : '正在載入...'}
        </p>

        {/* Loading Steps */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-4 mb-6 border border-slate-700/50">
          <div className="space-y-3">
            {steps.map((step) => (
              <div 
                key={step.id}
                className={`flex items-center gap-3 transition-all duration-300 ${
                  step.status === 'pending' ? 'opacity-40' : 'opacity-100'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg transition-all ${
                  step.status === 'complete' 
                    ? 'bg-emerald-500/20 text-emerald-400' 
                    : step.status === 'loading'
                    ? 'bg-cyan-500/20 text-cyan-400 animate-pulse'
                    : 'bg-slate-700/50 text-slate-500'
                }`}>
                  {step.status === 'complete' ? '✓' : step.icon}
                </div>
                <div className="flex-1 text-left">
                  <div className={`font-medium ${
                    step.status === 'complete' ? 'text-emerald-400' :
                    step.status === 'loading' ? 'text-cyan-400' :
                    'text-slate-500'
                  }`}>
                    {step.label}
                  </div>
                  {step.detail && (
                    <div className="text-xs text-slate-500 truncate">{step.detail}</div>
                  )}
                </div>
                {step.status === 'loading' && (
                  <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
                )}
                {step.status === 'complete' && (
                  <span className="text-emerald-400">✓</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden border border-slate-600/50">
          <div
            className={`h-full transition-all duration-500 ease-out rounded-full ${
              isComplete 
                ? 'bg-gradient-to-r from-emerald-500 to-cyan-500' 
                : 'bg-gradient-to-r from-cyan-500 to-blue-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-sm mt-2">
          <span className="text-slate-500">載入中...</span>
          <span className={`font-bold ${isComplete ? 'text-emerald-400' : 'text-cyan-400'}`}>
            {progress}%
          </span>
        </div>

        {!isComplete && (
          <div className="mt-6 flex justify-center gap-2">
            <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        )}
      </div>
    </div>
  )
}

const INITIAL_STEPS: LoadingStep[] = [
  { id: 'auth', label: '驗證身份', icon: '🔐', status: 'pending' },
  { id: 'data', label: '載入使用者資料', icon: '👤', status: 'pending' },
  { id: 'vocab', label: '載入詞彙庫', icon: '📚', status: 'pending' },
  { id: 'progress', label: '同步學習進度', icon: '📊', status: 'pending' },
  { id: 'mine', label: '準備礦區', icon: '⛏️', status: 'pending' },
  { id: 'verify', label: '載入複習卡片', icon: '📋', status: 'pending' },
  { id: 'rank', label: '載入排行榜', icon: '🏆', status: 'pending' },
  { id: 'pages', label: '預載頁面', icon: '📄', status: 'pending' },
]

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, loading: authLoading } = useAuth()
  const [onboardingChecked, setOnboardingChecked] = useState(false)
  
  // Loading state
  const [showLoading, setShowLoading] = useState(true)
  const [loadingSteps, setLoadingSteps] = useState<LoadingStep[]>(INITIAL_STEPS)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [isLoadingComplete, setIsLoadingComplete] = useState(false)
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  const bootstrapStarted = useRef(false)

  const locale = pathname.split('/')[1] || 'zh-TW'

  // Update a loading step
  const updateStep = useCallback((stepId: string, status: LoadingStep['status'], detail?: string) => {
    setLoadingSteps(prev => prev.map(s => 
      s.id === stepId ? { ...s, status, detail } : s
    ))
  }, [])

  // Track loading progress
  useEffect(() => {
    // Skip loading screen on /start page (it has its own)
    if (pathname.includes('/start')) {
      setShowLoading(false)
      return
    }

    // If already bootstrapped, skip loading
    if (isBootstrapped) {
      setShowLoading(false)
      return
    }

    // Auth step
    if (authLoading) {
      updateStep('auth', 'loading')
      setLoadingProgress(10)
    } else if (user) {
      updateStep('auth', 'complete')
      setLoadingProgress(20)
      
      // Run full bootstrap if not already done
      if (!isBootstrapped && !bootstrapStarted.current) {
        bootstrapStarted.current = true
        
        // Data step - run bootstrap
        updateStep('data', 'loading')
        
        // Run bootstrap in parallel with vocabulary loading
        const runBootstrap = async () => {
          try {
            await bootstrapApp(user.id, (progress) => {
              // Map bootstrap progress to steps
              if (progress.step.includes('profile') || progress.step.includes('children')) {
                updateStep('data', 'loading', progress.step)
              } else if (progress.step.includes('progress') || progress.step.includes('achievements')) {
                updateStep('progress', 'loading', progress.step)
              } else if (progress.step.includes('mining') || progress.step.includes('礦區')) {
                updateStep('mine', 'loading', progress.step)
              } else if (progress.step.includes('due') || progress.step.includes('cards')) {
                updateStep('verify', 'loading', progress.step)
              } else if (progress.step.includes('leaderboard') || progress.step.includes('排行')) {
                updateStep('rank', 'loading', progress.step)
              } else if (progress.step.includes('Preloading') || progress.step.includes('pages')) {
                updateStep('pages', 'loading', progress.step)
              }
            })
            updateStep('data', 'complete')
            updateStep('progress', 'complete')
            updateStep('mine', 'complete')
            updateStep('verify', 'complete')
            updateStep('rank', 'complete')
            updateStep('pages', 'complete')
          } catch (err) {
            console.warn('Bootstrap failed, using cached data:', err)
            updateStep('data', 'complete', '使用快取')
            updateStep('progress', 'complete', '使用快取')
            updateStep('mine', 'complete', '使用快取')
            updateStep('verify', 'complete', '使用快取')
            updateStep('rank', 'complete', '使用快取')
            updateStep('pages', 'complete', '使用快取')
          } finally {
            // Reset lock only on error (success sets isBootstrapped which prevents re-entry)
            if (!useAppStore.getState().isBootstrapped) {
              bootstrapStarted.current = false
            }
          }
        }
        
        runBootstrap()
      } else if (isBootstrapped) {
        updateStep('data', 'complete')
        updateStep('progress', 'complete')
        updateStep('mine', 'complete')
        updateStep('verify', 'complete')
        updateStep('rank', 'complete')
        updateStep('pages', 'complete')
      }
      
      // Check vocabulary and bootstrap status
      const checkBootstrapComplete = () => {
        const store = useAppStore.getState()
        // Default to emoji pack if none selected
        const activePack = store.activePack
        const isEmojiPackActive = activePack?.id === 'emoji_core' || !activePack
        
        // 🎯 MVP Modification:
        if (isEmojiPackActive) {
          // Force vocab step to complete instantly without checking loader
          updateStep('vocab', 'complete', 'Emoji Core')
        } else {
          // Legacy Logic
          const vocabStatus = vocabularyLoader.getCurrentStatus()
          
          // Update vocab step
          if (vocabStatus.state === 'cached' || vocabStatus.state === 'complete') {
            updateStep('vocab', 'complete', `${(vocabStatus as any).count?.toLocaleString() || ''} 詞彙`)
          } else if (vocabStatus.state === 'error') {
            updateStep('vocab', 'complete', '使用快取')
          } else {
            updateStep('vocab', 'loading', 
              vocabStatus.state === 'downloading' ? '下載中...' :
              vocabStatus.state === 'parsing' ? '解析中...' : 
              '檢查中...'
            )
          }
        }
        
        // Only hide loading when FULL BOOTSTRAP is complete (not just vocab)
        // This ensures Mine page starter pack is generated before showing the app
        if (store.isBootstrapped) {
          setLoadingProgress(100)
          setIsLoadingComplete(true)
          setTimeout(() => setShowLoading(false), 300)
        } else if (isEmojiPackActive) {
          // Emoji pack: vocab step is already complete, bootstrap still running
          setLoadingProgress(80)
        } else {
          // Legacy: check vocab status for progress
          const vocabStatus = vocabularyLoader.getCurrentStatus()
          if (vocabStatus.state === 'cached' || vocabStatus.state === 'complete') {
            // Vocab done but bootstrap still running
            setLoadingProgress(80)
          } else {
            setLoadingProgress(50)
          }
        }
      }
      
      // Only start legacy vocab loading if we are explicitly using a non-emoji pack
      const storeState = useAppStore.getState()
      const isEmoji = storeState.activePack?.id === 'emoji_core' || !storeState.activePack
      
      if (!isEmoji) {
        vocabularyLoader.startLoading()
      }
      
      // Poll for bootstrap completion (includes vocab + mine + all data)
      const pollInterval = setInterval(() => {
        checkBootstrapComplete()
        
        // Stop polling when bootstrap is complete
        const store = useAppStore.getState()
        if (store.isBootstrapped) {
          clearInterval(pollInterval)
        }
      }, 200)
      
      // Initial check
      checkBootstrapComplete()
      
      return () => clearInterval(pollInterval)
    } else if (!authLoading && !user) {
      // Not authenticated, will redirect - hide loading
      setShowLoading(false)
    }
  }, [authLoading, user, isBootstrapped, pathname, updateStep, isLoadingComplete])

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push(`/${locale}/login`)
    }
  }, [user, authLoading, router, locale])

  // Check onboarding status
  useEffect(() => {
    if (!authLoading && user && !onboardingChecked) {
      if (pathname.includes('/onboarding') || pathname.includes('/start')) {
        setOnboardingChecked(true)
        return
      }

      const userStore = useAppStore.getState().user
      
      if (!userStore) {
        console.log('⏳ User data not loaded yet, skipping onboarding check')
        setOnboardingChecked(true)
        return
      }
      
      const hasAge = !!userStore.age
      const hasRoles = userStore.roles && userStore.roles.length > 0
      const onboardingComplete = hasAge && hasRoles
      
      if (!onboardingComplete) {
        router.push(`/${locale}/onboarding`)
      }
      
      setOnboardingChecked(true)
    }
  }, [user, authLoading, router, locale, pathname, onboardingChecked])

  // Don't render if not authenticated
  if (!user && !authLoading) {
    return null
  }

  return (
    <UserDataProvider>
      <SidebarProvider>
        {/* Game Loading Overlay */}
        {showLoading && (
          <GameLoadingScreen 
            steps={loadingSteps} 
            progress={loadingProgress} 
            isComplete={isLoadingComplete} 
          />
        )}
        
        {/* Main Content (render behind loading screen for instant transition) */}
        <div className={showLoading ? 'invisible' : 'visible'}>
          {children}
        </div>
        
        <VocabularyLoadingIndicator />
      </SidebarProvider>
    </UserDataProvider>
  )
}

