'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { bootstrapApp } from '@/services/bootstrap'
import { useAppStore } from '@/stores/useAppStore'
import { vocabularyLoader } from '@/lib/vocabularyLoader'

/**
 * 🎮 Game Loading Screen (Traffic Cop + Bootstrap)
 * 
 * The "Airlock" - loads EVERYTHING before letting the user in.
 * Like a mobile game loading screen - shows detailed progress.
 * Once complete, the entire app is instant.
 * 
 * Loading Phases:
 * 1. 🔐 Authentication check
 * 2. 📊 User data (profile, achievements, wallet)
 * 3. 📚 Vocabulary database (10k+ words)
 * 4. 🎯 Learning progress
 * 5. ✅ Ready to play!
 * 
 * @see .cursorrules - "Caching & Bootstrap Strategy"
 */

interface LoadingStep {
  id: string
  label: string
  icon: string
  status: 'pending' | 'loading' | 'complete' | 'error'
  detail?: string
}

const INITIAL_STEPS: LoadingStep[] = [
  { id: 'auth', label: '驗證身份', icon: '🔐', status: 'pending' },
  { id: 'profile', label: '載入個人資料', icon: '👤', status: 'pending' },
  { id: 'vocabulary', label: '載入詞彙庫', icon: '📚', status: 'pending' },
  { id: 'progress', label: '同步學習進度', icon: '📊', status: 'pending' },
  { id: 'cache', label: '準備離線資料', icon: '💾', status: 'pending' },
]

export default function StartPage() {
  const router = useRouter()
  const pathname = usePathname()
  const { user, loading: authLoading } = useAuth()
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  
  const [steps, setSteps] = useState<LoadingStep[]>(INITIAL_STEPS)
  const [currentStep, setCurrentStep] = useState(0)
  const [overallProgress, setOverallProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [hasRun, setHasRun] = useState(false)
  const [isComplete, setIsComplete] = useState(false)

  const locale = pathname.split('/')[1] || 'zh-TW'

  const updateStep = useCallback((stepId: string, status: LoadingStep['status'], detail?: string) => {
    setSteps(prev => prev.map(s => 
      s.id === stepId ? { ...s, status, detail } : s
    ))
  }, [])

  useEffect(() => {
    if (authLoading) {
      updateStep('auth', 'loading')
      return
    }

    updateStep('auth', 'complete')

    if (!user) {
      router.replace(`/${locale}/login`)
      return
    }

    if (isBootstrapped && !hasRun) {
      console.log('⚡ Already bootstrapped, redirecting...')
      setSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'complete' as const })))
      setOverallProgress(100)
      setIsComplete(true)
      
      const roles = useAppStore.getState().user?.roles || []
      const isLearner = roles.includes('learner')
      const isParent = roles.includes('parent')
      
      const redirectTo = isLearner 
        ? `/${locale}/learner/mine`
        : isParent 
        ? `/${locale}/parent/dashboard`
        : `/${locale}/onboarding`
      
      setTimeout(() => router.replace(redirectTo), 500)
      return
    }

    if (hasRun) return
    setHasRun(true)

    const runFullBootstrap = async () => {
      console.log('🚀 Starting full bootstrap...')
      
      try {
        setCurrentStep(1)
        updateStep('profile', 'loading')
        setOverallProgress(10)
        
        const result = await bootstrapApp(user.id, (progressUpdate) => {
          const percent = Math.min(50, 10 + (progressUpdate.percentage * 0.4))
          setOverallProgress(percent)
          
          // Map bootstrap steps to UI steps - only show relevant details
          const stepRaw = progressUpdate.step.toLowerCase()

          if (stepRaw.includes('profile') || stepRaw.includes('children') || stepRaw.includes('learners')) {
            updateStep('profile', 'loading', progressUpdate.step)
          } else if (stepRaw.includes('wallet') || stepRaw.includes('currencies')) {
            // Map wallet/currency loading to profile
            updateStep('profile', 'loading', progressUpdate.step)
          } else if (stepRaw.includes('progress') || stepRaw.includes('achievements') || stepRaw.includes('goals')) {
            updateStep('progress', 'loading', progressUpdate.step)
          } else if (stepRaw.includes('vocabulary')) {
            updateStep('vocabulary', 'loading', progressUpdate.step)
          } else {
            // Background tasks (leaderboard, due cards, mining, finalizing)
            // Don't change the text, just let the progress bar fill up.
            // This prevents "Loading leaderboard..." from appearing under "Profile"
          }
        })

        if (!result.success) {
          throw new Error(result.error || 'Bootstrap failed')
        }
        
        updateStep('profile', 'complete')
        setOverallProgress(50)
        
        setCurrentStep(2)
        
        const store = useAppStore.getState()
        const activePack = store.activePack
        // Default to emoji pack if none selected (Safety for MVP)
        const isEmojiPackActive = activePack?.id === 'emoji_core' || !activePack

        if (isEmojiPackActive) {
          // 🎯 MVP Mode: Skip 10k vocabulary loading
          console.log('🎯 Start: Skipping 10k vocabulary (Emoji Pack Active)')
          updateStep('vocabulary', 'complete', '使用表情包核心詞彙')
          setOverallProgress(70)
          // Short UX delay
          await new Promise(resolve => setTimeout(resolve, 500))
        } else {
          // Legacy Mode: Load full 10k vocabulary
          updateStep('vocabulary', 'loading', '檢查詞彙快取...')
          vocabularyLoader.startLoading()
          
          await new Promise<void>((resolve) => {
            let attempts = 0
            const maxAttempts = 60
            const poll = setInterval(() => {
              attempts++
              const status = vocabularyLoader.getCurrentStatus()
              
              if (status.state === 'cached' || status.state === 'complete') {
                clearInterval(poll)
                const count = 'count' in status ? status.count : 0
                updateStep('vocabulary', 'complete', `${count.toLocaleString()} 個詞彙`)
                setOverallProgress(70)
                resolve()
              } else if (status.state === 'error' || attempts >= maxAttempts) {
                clearInterval(poll)
                updateStep('vocabulary', 'complete', '使用快取資料')
                setOverallProgress(70)
                resolve()
              } else {
                const detail = status.state === 'downloading' ? '下載詞彙庫...' 
                  : status.state === 'parsing' ? '解析中...'
                  : status.state === 'inserting' ? `載入中 ${(status as any).current || 0}/${(status as any).total || 0}`
                  : '檢查中...'
                updateStep('vocabulary', 'loading', detail)
                setOverallProgress(50 + (attempts / maxAttempts) * 20)
              }
            }, 500)
          })
        }
        
        setCurrentStep(3)
        updateStep('progress', 'loading', '同步學習紀錄...')
        setOverallProgress(80)
        
        await new Promise(r => setTimeout(r, 300))
        updateStep('progress', 'complete')
        
        setCurrentStep(4)
        updateStep('cache', 'loading', '準備離線模式...')
        setOverallProgress(90)
        
        await new Promise(r => setTimeout(r, 200))
        updateStep('cache', 'complete')
        setOverallProgress(100)
        
        setIsComplete(true)
        console.log('✅ Full bootstrap complete!')
        
          setTimeout(() => {
            router.replace(`/${locale}${result.redirectTo}`)
        }, 800)
        
      } catch (err) {
        console.error('❌ Bootstrap error:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
        
        setSteps(prev => prev.map((s, i) => 
          i === currentStep ? { ...s, status: 'error' as const } : s
        ))
      }
    }

    runFullBootstrap()
  }, [user, authLoading, isBootstrapped, hasRun, router, locale, updateStep, currentStep])

  // Error State
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md px-6">
          <div className="text-red-400 mb-4 text-6xl">⚠️</div>
          <h2 className="text-xl font-bold text-white mb-2">載入失敗</h2>
          <p className="text-slate-400 mb-4 text-sm">{error}</p>
          {error.includes('Server') && (
            <div className="mb-4 p-3 bg-yellow-900/30 border border-yellow-600/50 rounded-lg text-sm text-left">
              <p className="text-yellow-400 text-xs">
                後端服務可能未啟動。請檢查 <code className="bg-yellow-900/50 px-1 rounded">localhost:8000</code>
              </p>
            </div>
          )}
          <div className="flex gap-2">
            <button
              onClick={() => window.location.reload()}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl font-bold hover:from-cyan-500 hover:to-blue-500 transition-all"
            >
              🔄 重試
            </button>
            <button
              onClick={() => router.push(`/${locale}/onboarding`)}
              className="flex-1 px-6 py-3 bg-slate-700 text-slate-300 rounded-xl font-bold hover:bg-slate-600 transition-colors"
            >
              ⏭️ 跳過
            </button>
          </div>
        </div>
      </div>
    )
  }

  // 🎮 Game Loading Screen
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-cyan-500/10 to-transparent rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-purple-500/10 to-transparent rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 text-center max-w-md px-6 w-full">
        {/* App Logo with Glow */}
        <div className="mb-8 relative">
          <div className="absolute inset-0 w-24 h-24 mx-auto bg-cyan-500/30 blur-2xl rounded-full" />
          <div className={`relative w-24 h-24 mx-auto bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-cyan-500/30 ${isComplete ? 'animate-bounce' : ''}`}>
            <span className="text-4xl font-bold text-white">單</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-white mb-2 tracking-wide">LexiCraft</h1>
        <p className="text-slate-400 mb-8">
          {isComplete ? '✨ 準備完成！' : '正在載入你的世界...'}
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
                {/* Status Icon */}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg transition-all ${
                  step.status === 'complete' 
                    ? 'bg-emerald-500/20 text-emerald-400' 
                    : step.status === 'loading'
                    ? 'bg-cyan-500/20 text-cyan-400 animate-pulse'
                    : step.status === 'error'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-slate-700/50 text-slate-500'
                }`}>
                  {step.status === 'complete' ? '✓' : 
                   step.status === 'loading' ? step.icon :
                   step.status === 'error' ? '✕' : step.icon}
                </div>
                
                {/* Label & Detail */}
                <div className="flex-1 text-left">
                  <div className={`font-medium transition-colors ${
                    step.status === 'complete' ? 'text-emerald-400' :
                    step.status === 'loading' ? 'text-cyan-400' :
                    step.status === 'error' ? 'text-red-400' :
                    'text-slate-500'
                  }`}>
                    {step.label}
                  </div>
                  {step.detail && (
                    <div className="text-xs text-slate-500 truncate">
                      {step.detail}
                    </div>
                  )}
                </div>

                {/* Spinner or Checkmark */}
                <div className="w-6">
                  {step.status === 'loading' && (
                    <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
                  )}
                  {step.status === 'complete' && (
                    <span className="text-emerald-400">✓</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="mb-2">
          <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden border border-slate-600/50">
            <div
              className={`h-full transition-all duration-500 ease-out rounded-full ${
                isComplete 
                  ? 'bg-gradient-to-r from-emerald-500 to-cyan-500' 
                  : 'bg-gradient-to-r from-cyan-500 to-blue-600'
              }`}
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>

        {/* Percentage */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">載入中...</span>
          <span className={`font-bold ${isComplete ? 'text-emerald-400' : 'text-cyan-400'}`}>
            {overallProgress}%
          </span>
        </div>

        {/* Completion Message */}
        {isComplete && (
          <div className="mt-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-full text-emerald-400 font-medium">
              <span className="animate-bounce">🎮</span>
              進入遊戲中...
            </div>
          </div>
        )}

        {/* Animated Dots */}
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
