'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'

export default function Pricing() {
  const t = useTranslations('pricing')

  return (
    <section className="py-20 bg-gradient-to-br from-cyan-50 to-blue-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {t('title')}
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            {t('subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-1 gap-8 max-w-2xl mx-auto">
          <div className="bg-white rounded-xl p-8 shadow-lg ring-4 ring-cyan-500 transform scale-105">
            <div className="bg-gradient-to-r from-cyan-600 to-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-full inline-block mb-4">
              ⭐ {t('tier.name')}
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {t('tier.name')}
            </h3>
            <div className="mb-4">
              <span className="text-4xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
                {t('tier.price')}
              </span>
              <span className="text-gray-600 ml-2">deposit</span>
            </div>
            <p className="text-gray-600 mb-6">{t('tier.description')}</p>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.daily')}</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.sessions')}</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.quizzes')}</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.withdrawal')}</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.dashboard')}</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.tracking')}</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-cyan-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-700">{t('features.discount')}</span>
              </li>
            </ul>

            {/* CTA Button */}
            <Link
              href="/dashboard"
              className="block w-full px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white rounded-lg font-bold text-center transition-all shadow-lg hover:shadow-xl"
            >
              立即開始 →
            </Link>
          </div>
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-4">
            <strong>{t('note')}</strong>
          </p>
          <p className="text-sm text-gray-500">
            {t('regular')}
          </p>
        </div>
      </div>
    </section>
  )
}
