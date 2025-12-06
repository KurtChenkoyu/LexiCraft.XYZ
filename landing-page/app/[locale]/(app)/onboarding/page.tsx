'use client'

import { useState } from 'react'
import { useRouter } from '@/i18n/routing'
import { useAuth } from '@/contexts/AuthContext'
import { authenticatedPost } from '@/lib/api-client'

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
  const { user } = useAuth()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<OnboardingData>({
    account_type: null,
  })

  // Get user ID from Supabase user (guaranteed by layout)
  const userId = user?.id

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
        // Redirect to dashboard
        router.push(response.redirect_to || '/dashboard')
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

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-gray-600">載入中...</div>
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
              {error}
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

