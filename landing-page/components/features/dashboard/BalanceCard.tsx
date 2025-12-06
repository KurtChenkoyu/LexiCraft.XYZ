'use client'

import { useTranslations } from 'next-intl'

interface BalanceCardProps {
  availablePoints: number
  lockedPoints: number
}

export function BalanceCard({ availablePoints, lockedPoints }: BalanceCardProps) {
  const t = useTranslations('dashboard')
  const total = availablePoints + lockedPoints

  return (
    <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl shadow-lg p-6 text-white">
      <h3 className="text-lg font-semibold mb-2">{t('balance.title')}</h3>
      <div className="text-3xl font-bold mb-2">
        NT$ {total.toLocaleString()}
      </div>
      <p className="text-cyan-100 text-sm">
        {t('balance.available')}：{availablePoints.toLocaleString()} | {t('balance.locked')}：{lockedPoints.toLocaleString()}
      </p>
    </div>
  )
}

