'use client'

import { Link } from '@/i18n/routing'

export function VerificationCard() {
  return (
    <div className="bg-gradient-to-br from-cyan-600 to-blue-600 rounded-xl shadow-lg p-6 text-white mb-6">
      <h3 className="text-xl font-bold mb-2">複習驗證</h3>
      <p className="text-cyan-100 text-sm mb-4">
        根據間隔重複系統進行單字複習
      </p>
      <Link
        href="/learner/verification"
        className="block w-full text-center px-4 py-3 bg-white text-cyan-600 rounded-lg font-semibold hover:bg-cyan-50 transition-colors"
      >
        開始複習 →
      </Link>
    </div>
  )
}

