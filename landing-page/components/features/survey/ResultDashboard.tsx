'use client'

import { TriMetricReport } from './types'

interface ResultDashboardProps {
  metrics: TriMetricReport
  onRestart?: () => void
}

/**
 * ResultDashboard: Final Results Display
 * 
 * Displays the Tri-Metric Report (Volume, Reach, Density)
 * in a visually appealing dashboard format.
 */
export default function ResultDashboard({ metrics, onRestart }: ResultDashboardProps) {
  const { volume, reach, density } = metrics

  // Calculate density percentage
  const densityPercent = Math.round(density * 100)

  // Format numbers with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-TW')
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          掃描完成
        </h2>
        <p className="text-xl text-gray-600">
          您的詞彙資產報告已生成
        </p>
      </div>

      {/* Tri-Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {/* Volume Card */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-8 border-2 border-blue-200 shadow-lg">
          <div className="text-center">
            <div className="text-4xl mb-2">📊</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">資產總量</h3>
            <p className="text-sm text-gray-600 mb-4">Volume (Est. Reserves)</p>
            <div className="text-4xl font-bold text-blue-600">
              {formatNumber(volume)}
            </div>
            <p className="text-sm text-gray-500 mt-2">個單字</p>
          </div>
        </div>

        {/* Reach Card */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-8 border-2 border-green-200 shadow-lg">
          <div className="text-center">
            <div className="text-4xl mb-2">🎯</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">有效邊界</h3>
            <p className="text-sm text-gray-600 mb-4">Reach (Horizon)</p>
            <div className="text-4xl font-bold text-green-600">
              {formatNumber(reach)}
            </div>
            <p className="text-sm text-gray-500 mt-2">排名</p>
          </div>
        </div>

        {/* Density Card */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-8 border-2 border-purple-200 shadow-lg">
          <div className="text-center">
            <div className="text-4xl mb-2">💎</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">資產密度</h3>
            <p className="text-sm text-gray-600 mb-4">Density (Solidity)</p>
            <div className="text-4xl font-bold text-purple-600">
              {densityPercent}%
            </div>
            <p className="text-sm text-gray-500 mt-2">一致性</p>
          </div>
        </div>
      </div>

      {/* Summary Section */}
      <div className="bg-white rounded-xl p-8 border-2 border-gray-200 shadow-lg mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">報告摘要</h3>
        <div className="space-y-4 text-gray-700">
          <p>
            根據掃描結果，您估計擁有 <strong className="text-blue-600">{formatNumber(volume)}</strong> 個單字的詞彙量。
          </p>
          <p>
            您的有效邊界位於排名 <strong className="text-green-600">{formatNumber(reach)}</strong>，
            這表示您在此排名以下的單字掌握度較高。
          </p>
          <p>
            您的資產密度為 <strong className="text-purple-600">{densityPercent}%</strong>，
            這反映了您在已掌握區域內的知識一致性。
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="text-center space-x-4">
        {onRestart && (
          <button
            onClick={onRestart}
            className="px-8 py-4 bg-primary-600 text-white rounded-lg text-lg font-semibold hover:bg-primary-700 transition-colors shadow-lg hover:shadow-xl"
          >
            重新掃描
          </button>
        )}
        <button
          onClick={() => window.print()}
          className="px-8 py-4 bg-gray-200 text-gray-700 rounded-lg text-lg font-semibold hover:bg-gray-300 transition-colors"
        >
          列印報告
        </button>
      </div>
    </div>
  )
}

