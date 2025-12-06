'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { Footer } from '@/components/layout'

export default function PrivacyPage() {
  const t = useTranslations('privacy')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <Link href="/" className="text-primary-600 hover:text-primary-700 mb-8 inline-block">
          ← {t('back')}
        </Link>
        
        <h1 className="text-4xl font-bold text-gray-900 mb-8">{t('title')}</h1>
        
        <div className="bg-white rounded-lg shadow-sm p-8 space-y-6 text-gray-700">
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section1.title')}</h2>
            <p className="mb-4">{t('section1.intro')}</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>{t('section1.email')}</strong> - {t('section1.emailDesc')}</li>
              <li><strong>{t('section1.numKids')}</strong> - {t('section1.numKidsDesc')}</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section2.title')}</h2>
            <p className="mb-4">{t('section2.intro')}</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>{t('section2.use1')}</li>
              <li>{t('section2.use2')}</li>
              <li>{t('section2.use3')}</li>
              <li>{t('section2.use4')}</li>
            </ul>
            <p className="mt-4">{t('section2.noShare')}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section3.title')}</h2>
            <p className="mb-4">{t('section3.content')}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section4.title')}</h2>
            <p className="mb-4">{t('section4.intro')}</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>{t('section4.access')}</strong> - {t('section4.accessDesc')}</li>
              <li><strong>{t('section4.update')}</strong> - {t('section4.updateDesc')}</li>
              <li><strong>{t('section4.delete')}</strong> - {t('section4.deleteDesc')}</li>
              <li><strong>{t('section4.optout')}</strong> - {t('section4.optoutDesc')}</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section5.title')}</h2>
            <p className="mb-4">{t('section5.intro')}</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>{t('section5.method1')}</li>
              <li>{t('section5.method2')}</li>
            </ul>
            <p className="mt-4">{t('section5.note')}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section6.title')}</h2>
            <p className="mb-4">{t('section6.content')}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section7.title')}</h2>
            <p className="mb-4">{t('section7.content')}</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">{t('section8.title')}</h2>
            <p className="mb-4">{t('section8.intro')}</p>
            <p className="ml-4">
              <strong>{t('section8.email')}</strong> privacy@earnmoneyback.com<br />
              <strong>{t('section8.subject')}</strong> {t('section8.subjectText')}
            </p>
          </section>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              <strong>{t('lastUpdated')}</strong> {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

