'use client'

import { useTranslations } from 'next-intl'
import { Search, BarChart3, Network, DollarSign, Pickaxe, TrendingUp } from 'lucide-react'

export default function BenefitsParents() {
  const t = useTranslations('benefitsParents')

  const benefits = [
    { icon: Search, key: 'verify' },
    { icon: BarChart3, key: 'identify' },
    { icon: Network, key: 'structure' },
    { icon: DollarSign, key: 'roi' },
    { icon: Pickaxe, key: 'motivate' },
    { icon: TrendingUp, key: 'ahead' },
  ]

  return (
    <section className="section-light">
      <div className="section-container">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            {t('title')}
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            {t('subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {benefits.map((benefit, index) => (
            <div
              key={index}
              className="card-secondary card-hover-lift group"
            >
              <div className="mb-6 p-4 rounded-xl bg-gradient-to-br from-primary-50 to-cyan-50 w-fit">
                <benefit.icon size={36} className="text-primary-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4 group-hover:text-primary-600 transition-colors">
                {t(`${benefit.key}.title`)}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {t(`${benefit.key}.description`)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
