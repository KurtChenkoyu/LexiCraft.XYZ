'use client'

import { useState, useEffect } from 'react'
import { useRouter } from '@/i18n/routing'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { authenticatedPost, authenticatedGet } from '@/lib/api-client'
import { useAppStore } from '@/stores/useAppStore'

type AccountType = 'parent' | 'learner' | 'both' | null

interface OnboardingData {
  account_type: AccountType
  parent_age?: number
  child_name?: string
  child_age?: number
  learner_age?: number
  cefr_level?: string
}

export default function OnboardingPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, loading: authLoading } = useAuth()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSkipOption, setShowSkipOption] = useState(true)
  const [checkingPayment, setCheckingPayment] = useState(true)
  const [paymentPollingAttempt, setPaymentPollingAttempt] = useState(0)
  const [data, setData] = useState<OnboardingData>({
    account_type: null,
  })

  // Get user ID from Supabase user (guaranteed by layout)
  const userId = user?.id

  // Poll for payment status (replaces binary check)
  const pollForPaymentStatus = async (): Promise<boolean> => {
    const maxAttempts = 30 // 30 attempts × 1000ms = 30 seconds
    const pollInterval = 1000 // ms
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        setPaymentPollingAttempt(attempt + 1)
        const profile = await authenticatedGet<{
          subscription_status?: string
          plan_type?: string
        }>('/api/users/me')
        
        const hasActiveSubscription = profile.subscription_status === 'active' || 
                                     profile.subscription_status === 'trial'
        
        if (hasActiveSubscription) {
          console.log(`✅ Payment verified after ${attempt + 1} attempt(s)`)
          return true
        }
        
        // If not found and not last attempt, wait before retrying
        if (attempt < maxAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, pollInterval))
        }
      } catch (err) {
        // Log error but continue polling (might be transient)
        console.warn(`⚠️ Payment check attempt ${attempt + 1} failed:`, err)
        if (attempt < maxAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, pollInterval))
        }
      }
    }
    
    // Timeout - no active subscription found after 30 seconds
    console.warn('⚠️ Payment verification timed out after 30 seconds')
    return false
  }

  // Retry payment check (restarts full 30-second polling loop)
  const handleRetryPaymentCheck = async () => {
    if (!userId || authLoading) return
    
    try {
      setCheckingPayment(true)
      setError(null)
      setPaymentPollingAttempt(0)
      
      // Poll for payment status (waits up to 30 seconds)
      const hasPayment = await pollForPaymentStatus()
      
      if (!hasPayment) {
        // Timeout - no payment found after polling
        setError('付款確認中，請稍候。如果已完成付款，請稍候幾分鐘讓系統處理。')
        setShowSkipOption(false) // Hide skip option when payment is required
      } else {
        // Payment verified - proceed to onboarding
        setError(null)
      }
    } catch (err: any) {
      console.error('Failed to check payment status:', err)
      setError('無法驗證付款狀態，請稍後再試')
    } finally {
      setCheckingPayment(false)
    }
  }

  // Check payment status on mount (with polling)
  useEffect(() => {
    const checkPayment = async () => {
      if (!userId || authLoading) return
      
      try {
        setCheckingPayment(true)
        setError(null)
        setPaymentPollingAttempt(0)
        
        // Check if user came from successful checkout (optimization)
        const checkoutSuccess = searchParams.get('checkout_success') === 'true'
        if (checkoutSuccess) {
          console.log('🔄 User came from checkout - starting payment polling immediately')
        }
        
        // Poll for payment status (waits up to 30 seconds)
        const hasPayment = await pollForPaymentStatus()
        
        if (!hasPayment) {
          // Timeout - no payment found after polling
          setError('付款確認中，請稍候。如果已完成付款，請稍候幾分鐘讓系統處理。')
          setShowSkipOption(false) // Hide skip option when payment is required
        } else {
          // Payment verified - proceed to onboarding
          setError(null)
        }
      } catch (err: any) {
        console.error('Failed to check payment status:', err)
        setError('無法驗證付款狀態，請稍後再試')
      } finally {
        setCheckingPayment(false)
      }
    }
    
    checkPayment()
  }, [userId, authLoading, searchParams])

  const handleAccountTypeSelect = (type: AccountType) => {
    setData({ ...data, account_type: type })
    setStep(2)
  }

  const handleParentInfo = (age: number) => {
    // For "both" account type, parent and learner are the same person
    // So use the same age for both
    if (data.account_type === 'both') {
      setData({ ...data, parent_age: age, learner_age: age })
      setStep(3) // Next: optional child info (skip learner age step)
    } else {
      setData({ ...data, parent_age: age })
      setStep(3) // Next: optional child info
    }
  }

  const handleLearnerInfo = (age: number, cefr?: string) => {
    setData({ ...data, learner_age: age, cefr_level: cefr })
    if (data.account_type === 'learner') {
      // Ready to submit
      handleSubmit()
    } else if (data.account_type === 'both') {
      setStep(3) // Next: optional child info
    }
  }

  const handleChildInfo = (name: string, age: number) => {
    setData({ ...data, child_name: name, child_age: age })
    handleSubmit()
  }

  const handleSubmit = async () => {
    if (!userId) {
      setError('請先登入')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Note: user_id is now extracted from JWT token via auth middleware
      // No need to pass it in query params or body
      const response = await authenticatedPost<{
        success: boolean
        redirect_to: string
      }>('/api/users/onboarding/complete', data)

      if (response.success) {
        // CRITICAL: Poll for learners until they appear (replaces fixed delay)
        // This ensures the new child/learner appears immediately in the UI
        // Polls every 500ms, stops when learners.length > 0 or after 5 seconds
        const pollForLearners = async (): Promise<any[]> => {
          const maxAttempts = 10 // 10 attempts × 500ms = 5 seconds
          const pollInterval = 500 // ms
          
          const { downloadService } = await import('@/services/downloadService')
          const { localStore } = await import('@/lib/local-store')
          
          // CRITICAL: Clear stale cache first to force fresh fetch
          const { CACHE_KEYS } = await import('@/services/downloadService')
          await localStore.deleteCache(CACHE_KEYS.LEARNERS)
          await localStore.deleteCache(CACHE_KEYS.CHILDREN)
          console.log('🗑️ Cleared stale learners/children cache')
          
          for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
              // Force refresh from API (bypasses all cache)
              const learners = await downloadService.refreshLearners()
              
              if (learners && learners.length > 0) {
                console.log(`✅ Onboarding: Found ${learners.length} learners after ${attempt + 1} attempt(s)`)
                return learners
              }
              
              // If not found and not last attempt, wait before retrying
              if (attempt < maxAttempts - 1) {
                await new Promise(resolve => setTimeout(resolve, pollInterval))
              }
            } catch (refreshError) {
              // Log error but continue polling (might be transient)
              console.warn(`⚠️ Onboarding: Poll attempt ${attempt + 1} failed:`, refreshError)
              if (attempt < maxAttempts - 1) {
                await new Promise(resolve => setTimeout(resolve, pollInterval))
              }
            }
          }
          
          // Timeout - no learners found after all attempts
          console.warn('⚠️ Onboarding: Polling timed out - no learners found after 5 seconds')
          return []
        }
        
        let freshLearners: any[] = []
        
        try {
          freshLearners = await pollForLearners()
          
          if (freshLearners && freshLearners.length > 0) {
            // Update Zustand store so LearnerSwitcher sees the new learners
            const { useAppStore } = await import('@/stores/useAppStore')
            const store = useAppStore.getState()
            store.setLearners(freshLearners)
            
            // Auto-select first learner (parent or child)
            const parentLearner = freshLearners.find(l => l.is_parent_profile)
            if (parentLearner) {
              store.setActiveLearner(parentLearner)
            } else if (freshLearners.length > 0) {
              store.setActiveLearner(freshLearners[0])
            }
            
            console.log(`✅ Onboarding: Refreshed ${freshLearners.length} learners after completion`)
          } else {
            console.warn('⚠️ Onboarding: No learners returned from API after polling')
            // Show error to user but don't block redirect (they can refresh manually)
            setError('學習者資料載入中，如果稍後仍未顯示，請重新整理頁面')
          }
        } catch (refreshError) {
          // Non-critical - log but don't block redirect
          console.error('❌ Failed to poll for learners after onboarding:', refreshError)
          setError('學習者資料載入失敗，請重新整理頁面')
        }
        
        // Also refresh children cache (for parent dashboard)
        try {
          const { downloadService } = await import('@/services/downloadService')
          const { CACHE_KEYS } = await import('@/services/downloadService')
          const { localStore } = await import('@/lib/local-store')
          await localStore.deleteCache(CACHE_KEYS.CHILDREN)
          await downloadService.getChildren() // This will refresh if needed
        } catch (childrenError) {
          console.warn('⚠️ Failed to refresh children after onboarding (non-critical):', childrenError)
        }
        
        // Determine redirect path based on account type
        // Don't reset bootstrap - just redirect directly to the right place
        const { useAppStore } = await import('@/stores/useAppStore')
        const store = useAppStore.getState()
        const userRoles = store.user?.roles || []
        const isParent = userRoles.includes('parent')
        const isLearner = userRoles.includes('learner')
        
        let redirectPath = '/start' // Default fallback
        
        if (isParent && freshLearners && freshLearners.length > 0) {
          // Parent with learners → go directly to parent dashboard
          redirectPath = '/parent/dashboard'
          console.log('✅ Onboarding: Redirecting parent to dashboard')
        } else if (isParent) {
          // Parent but no learners yet → stay on onboarding (shouldn't happen, but safety check)
          redirectPath = '/onboarding'
          console.warn('⚠️ Onboarding: Parent has no learners after refresh')
        } else if (isLearner) {
          // Learner only → go to learner home
          redirectPath = '/learner/home'
          console.log('✅ Onboarding: Redirecting learner to home')
        }
        
        // Redirect directly (don't reset bootstrap - let it run fresh on next page load)
        router.push(redirectPath)
      } else {
        throw new Error('Onboarding failed')
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || err.message || '設定失敗，請重試'
      )
      setLoading(false)
    }
  }

  if (authLoading || checkingPayment) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
          </div>
          <div className="text-gray-700 font-medium mb-2">正在確認付款狀態...</div>
          {paymentPollingAttempt > 0 && (
            <div className="text-sm text-gray-500">
              嘗試 {paymentPollingAttempt} / 30
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!user) {
    return null // Will redirect
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20">
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-2xl font-bold text-gray-900">
                完成帳戶設定
              </h1>
              <span className="text-sm text-gray-700">
                步驟 {step} / 4
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-cyan-600 to-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(step / 4) * 100}%` }}
              />
            </div>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
              <div className="mb-2">{error}</div>
              {error.includes('付款確認中') && (
                <div className="mt-3 flex gap-3">
                  <button
                    onClick={handleRetryPaymentCheck}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors"
                  >
                    重試
                  </button>
                  <button
                    onClick={() => router.push('/start')}
                    className="px-4 py-2 border border-red-300 text-red-700 hover:bg-red-50 rounded-lg text-sm transition-colors"
                  >
                    稍後再試
                  </button>
                </div>
              )}
              {showSkipOption && error.includes('timeout') && (
                <div className="mt-3">
                  <button
                    onClick={() => router.push('/start')}
                    className="text-sm text-red-600 hover:text-red-800 underline"
                  >
                    ⚠️ 已完成設定？點此跳過
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Skip button for returning users */}
          {showSkipOption && step === 1 && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 mb-2">
                ℹ️ 已完成過帳戶設定？
              </p>
              <button
                onClick={() => router.push('/start')}
                className="text-sm text-blue-600 hover:text-blue-800 underline font-semibold"
              >
                跳過並前往應用程式 →
              </button>
            </div>
          )}

          {/* Step 1: Account Type Selection */}
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-gray-700 mb-6">
                這個帳戶是給誰使用的？
              </p>
              <button
                onClick={() => handleAccountTypeSelect('parent')}
                className="w-full p-6 border-2 border-gray-300 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-all text-left"
              >
                <div className="font-semibold text-gray-900 mb-1">
                  家長帳戶
                </div>
                <div className="text-sm text-gray-700">
                  管理孩子的學習進度
                </div>
              </button>
              <button
                onClick={() => handleAccountTypeSelect('learner')}
                className="w-full p-6 border-2 border-gray-300 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-all text-left"
              >
                <div className="font-semibold text-gray-900 mb-1">
                  學習者帳戶
                </div>
                <div className="text-sm text-gray-700">
                  自己學習英語詞彙
                </div>
              </button>
              <button
                onClick={() => handleAccountTypeSelect('both')}
                className="w-full p-6 border-2 border-gray-300 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-all text-left"
              >
                <div className="font-semibold text-gray-900 mb-1">
                  家長 + 學習者
                </div>
                <div className="text-sm text-gray-700">
                  管理孩子並自己學習
                </div>
              </button>
            </div>
          )}

          {/* Step 2: Parent Age (if parent or both) */}
          {(step === 2 && (data.account_type === 'parent' || data.account_type === 'both')) && (
            <ParentAgeForm
              onSubmit={handleParentInfo}
              onBack={() => setStep(1)}
            />
          )}

          {/* Step 3: Learner Age (if learner or both) */}
          {(step === 2 && data.account_type === 'learner') && (
            <LearnerAgeForm
              onSubmit={handleLearnerInfo}
              onBack={() => setStep(1)}
            />
          )}

          {/* Step 4: Learner Age (if both) - REMOVED: parent and learner are same person */}

          {/* Step 3/4: Optional Child Info (if parent or both) */}
          {(step === 3 && (data.account_type === 'parent' || data.account_type === 'both')) && (
            <ChildInfoForm
              onSubmit={handleChildInfo}
              onSkip={handleSubmit}
              onBack={() => {
                if (data.account_type === 'parent') {
                  setStep(2)
                } else {
                  setStep(4)
                }
              }}
              loading={loading}
            />
          )}
        </div>
      </div>
    </main>
  )
}

// Parent Age Form Component
function ParentAgeForm({
  onSubmit,
  onBack,
}: {
  onSubmit: (age: number) => void
  onBack: () => void
}) {
  const [age, setAge] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const ageNum = parseInt(age)
    if (ageNum < 20) {
      alert('家長必須年滿 20 歲（台灣法定成年年齡）')
      return
    }
    onSubmit(ageNum)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="parent_age" className="block text-sm font-medium text-gray-700 mb-2">
          您的年齡
        </label>
        <input
          id="parent_age"
          type="number"
          value={age}
          onChange={(e) => setAge(e.target.value)}
          required
          min={20}
          max={120}
          className="w-full px-4 py-3 border-2 border-gray-400 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900 placeholder-gray-500"
          placeholder="20"
        />
        <p className="mt-2 text-sm text-gray-700">
          必須年滿 20 歲（台灣法定成年年齡）
        </p>
      </div>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-900"
        >
          返回
        </button>
        <button
          type="submit"
          className="flex-1 px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg font-semibold transition-colors"
        >
          下一步
        </button>
      </div>
    </form>
  )
}

// Learner Age Form Component
function LearnerAgeForm({
  onSubmit,
  onBack,
}: {
  onSubmit: (age: number, cefr?: string) => void
  onBack: () => void
}) {
  const [age, setAge] = useState('')
  const [cefr, setCefr] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const ageNum = parseInt(age)
    if (ageNum < 20) {
      alert('未滿 20 歲的學習者需要家長帳戶。請選擇「家長帳戶」或「家長 + 學習者」。')
      return
    }
    onSubmit(ageNum, cefr || undefined)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="learner_age" className="block text-sm font-medium text-gray-700 mb-2">
          您的年齡
        </label>
        <input
          id="learner_age"
          type="number"
          value={age}
          onChange={(e) => setAge(e.target.value)}
          required
          min={20}
          max={120}
          className="w-full px-4 py-3 border-2 border-gray-400 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900 placeholder-gray-500"
          placeholder="20"
        />
        <p className="mt-2 text-sm text-gray-700">
          必須年滿 20 歲（台灣法定成年年齡）
        </p>
      </div>
      <div>
        <label htmlFor="cefr_level" className="block text-sm font-medium text-gray-700 mb-2">
          英語程度（選填）
        </label>
        <select
          id="cefr_level"
          value={cefr}
          onChange={(e) => setCefr(e.target.value)}
          className="w-full px-4 py-3 border-2 border-gray-400 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900 placeholder-gray-500"
        >
          <option value="">不知道</option>
          <option value="A1">A1 - 初級</option>
          <option value="A2">A2 - 基礎</option>
          <option value="B1">B1 - 中級</option>
          <option value="B2">B2 - 中高級</option>
          <option value="C1">C1 - 高級</option>
          <option value="C2">C2 - 精通</option>
        </select>
      </div>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-900"
        >
          返回
        </button>
        <button
          type="submit"
          className="flex-1 px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg font-semibold transition-colors"
        >
          完成
        </button>
      </div>
    </form>
  )
}

// Child Info Form Component
function ChildInfoForm({
  onSubmit,
  onSkip,
  onBack,
  loading,
}: {
  onSubmit: (name: string, age: number) => void
  onSkip: () => void
  onBack: () => void
  loading: boolean
}) {
  const [name, setName] = useState('')
  const [age, setAge] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const ageNum = parseInt(age)
    if (ageNum >= 20) {
      alert('孩子必須未滿 20 歲')
      return
    }
    onSubmit(name, ageNum)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-gray-700 mb-4">
          您可以現在建立孩子的帳戶，或稍後再建立。
        </p>
      <div>
        <label htmlFor="child_name" className="block text-sm font-medium text-gray-700 mb-2">
          孩子姓名
        </label>
        <input
          id="child_name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-4 py-3 border-2 border-gray-400 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900 placeholder-gray-500"
          placeholder="孩子的名字"
        />
      </div>
      <div>
        <label htmlFor="child_age" className="block text-sm font-medium text-gray-700 mb-2">
          孩子年齡
        </label>
        <input
          id="child_age"
          type="number"
          value={age}
          onChange={(e) => setAge(e.target.value)}
          min={1}
          max={19}
          className="w-full px-4 py-3 border-2 border-gray-400 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-600 bg-white text-gray-900 placeholder-gray-500"
          placeholder="5"
        />
        <p className="mt-2 text-sm text-gray-700">
          必須未滿 20 歲
        </p>
      </div>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-900"
        >
          返回
        </button>
        <button
          type="button"
          onClick={onSkip}
          disabled={loading}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 text-gray-900"
        >
          稍後再建立
        </button>
        <button
          type="submit"
          disabled={loading || !name || !age}
          className="flex-1 px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
        >
          {loading ? '處理中...' : '建立帳戶'}
        </button>
      </div>
    </form>
  )
}

