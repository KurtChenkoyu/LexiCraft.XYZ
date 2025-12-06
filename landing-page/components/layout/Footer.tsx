'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'

export default function Footer() {
  const t = useTranslations('footer')

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-white text-lg font-semibold mb-4 font-mono">LexiCraft.xyz • 字塊所</h3>
            <p className="text-sm">
              {t('tagline')}
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">{t('legal')}</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/privacy" className="hover:text-white transition-colors">
                  {t('privacy')}
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">{t('contact')}</h4>
            <p className="text-sm">
              {t('questions')}{' '}
              <a
                href="mailto:support@earnmoneyback.com"
                className="text-primary-400 hover:text-primary-300"
              >
                support@LexiCraft.xyz
              </a>
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
          <p>
            {t('copyright', { year: new Date().getFullYear() })}
          </p>
          <p className="mt-2 text-gray-500">
            {t('taiwan')}
          </p>
        </div>
      </div>
    </footer>
  )
}
