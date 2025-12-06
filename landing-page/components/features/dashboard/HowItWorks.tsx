'use client'

import { useTranslations } from 'next-intl'

export function HowItWorks() {
  const t = useTranslations('dashboard')

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
      <h3 className="text-lg font-bold text-blue-900 mb-3">{t('howItWorks.title')}</h3>
      <ul className="space-y-2 text-sm text-blue-800">
        <li>1. {t('howItWorks.step1')}</li>
        <li>2. {t('howItWorks.step2')}</li>
        <li>3. {t('howItWorks.step3')}</li>
      </ul>
    </div>
  )
}

