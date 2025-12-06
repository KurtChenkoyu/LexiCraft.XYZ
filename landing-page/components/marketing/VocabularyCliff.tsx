'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { trackEvent } from '@/lib/analytics'

export default function VocabularyCliff() {
  const t = useTranslations('vocabularyCliff')

  const handleSurveyClick = () => {
    trackEvent('vocabulary_cliff_survey_clicked')
  }

  return (
    <section className="section-light">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            {t('title')}
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            {t('subtitle')}
          </p>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-xl max-w-4xl mx-auto border border-gray-100">
          <div className="mb-8">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="pb-4 text-gray-700 font-semibold">{t('table.stage')}</th>
                  <th className="pb-4 text-gray-700 font-semibold">{t('table.official')}</th>
                  <th className="pb-4 text-gray-700 font-semibold">{t('table.reality')}</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100">
                  <td className="py-4 text-gray-900 font-medium">{t('table.junior')}</td>
                  <td className="py-4 text-gray-600">~1,200 {t('table.words')}</td>
                  <td className="py-4 text-green-600 font-medium">{t('table.comfortable')}</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-4 text-gray-900 font-medium">{t('table.senior')}</td>
                  <td className="py-4 text-gray-600">4,500 {t('table.words')} {t('table.listed')}</td>
                  <td className="py-4 text-orange-600 font-medium">{t('table.actuallyNeed')}</td>
                </tr>
                <tr className="bg-red-50">
                  <td className="py-4 text-gray-900 font-bold">{t('table.cliff')}</td>
                  <td className="py-4 text-red-600 font-bold">{t('table.gap')}</td>
                  <td className="py-4 text-red-600 font-bold">{t('table.crash')}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-primary-600 p-6 rounded-lg mb-8">
            <p className="text-gray-800 leading-relaxed font-medium">
              {t('diagnostic')}
            </p>
          </div>

          <div className="text-center">
            <p className="text-lg font-bold text-gray-900 mb-6">
              {t('keyQuestion')}
            </p>
            <Link
              href="/survey"
              onClick={handleSurveyClick}
              className="inline-block px-8 py-4 bg-gradient-to-r from-primary-600 to-cyan-600 hover:from-primary-500 hover:to-cyan-500 text-white rounded-full font-bold tracking-wide shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              {t('cta')}
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}


