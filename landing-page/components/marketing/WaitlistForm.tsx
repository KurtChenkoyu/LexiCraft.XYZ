'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname } from '@/i18n/routing'
import { trackEvent } from '@/lib/analytics'
import { PartyPopper } from 'lucide-react'

export default function WaitlistForm() {
  const t = useTranslations('waitlist')
  const pathname = usePathname()
  const [email, setEmail] = useState('')
  const [numKids, setNumKids] = useState('1')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setErrorMessage('')

    trackEvent('waitlist_form_submitted', {
      email,
      numKids: parseInt(numKids),
    })

    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          numKids: parseInt(numKids),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong')
      }

      setStatus('success')
      setEmail('')
      setNumKids('1')
      trackEvent('waitlist_form_success')
    } catch (error) {
      setStatus('error')
      setErrorMessage(
        error instanceof Error ? error.message : 'Failed to join waitlist. Please try again.'
      )
      trackEvent('waitlist_form_error', { error: errorMessage })
    }
  }

  return (
    <section id="waitlist-form" className="py-20 bg-gradient-to-br from-primary-600 to-primary-800 text-white">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            {t('title')}
          </h2>
          <p className="text-xl text-primary-100">
            {t('subtitle')}
          </p>
        </div>

        {status === 'success' ? (
          <div className="bg-white text-gray-900 rounded-lg p-8 text-center">
            <div className="mb-4"><PartyPopper size={64} className="text-primary-600" /></div>
            <h3 className="text-2xl font-bold mb-4">{t('success.title')}</h3>
            <p className="text-gray-600 mb-6">
              {t('success.message')}
            </p>
            <button
              onClick={() => setStatus('idle')}
              className="text-primary-600 hover:text-primary-700 font-semibold"
            >
              {t('success.another')}
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-white rounded-lg p-8 shadow-xl">
            <div className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                  {t('form.email')} *
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
                  placeholder="your.email@example.com"
                />
              </div>

              <div>
                <label htmlFor="numKids" className="block text-sm font-semibold text-gray-700 mb-2">
                  {t('form.numKids')} *
                </label>
                <select
                  id="numKids"
                  value={numKids}
                  onChange={(e) => setNumKids(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
                >
                  <option value="1">{t('options.one')}</option>
                  <option value="2">{t('options.two')}</option>
                  <option value="3">{t('options.three')}</option>
                  <option value="4">{t('options.four')}</option>
                </select>
              </div>

              {status === 'error' && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {errorMessage}
                </div>
              )}

              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full bg-primary-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {status === 'loading' ? t('form.loading') : t('form.submit')}
              </button>

              <p className="text-xs text-gray-500 text-center">
                {t('form.privacy')}{' '}
                <a href={`${pathname}/privacy`} className="text-primary-600 hover:text-primary-700 ml-1">
                  {t('form.privacyLink')}
                </a>
              </p>
            </div>
          </form>
        )}
      </div>
    </section>
  )
}

