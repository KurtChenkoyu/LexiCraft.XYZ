'use client'

import { useTranslations } from 'next-intl'
import { GraduationCap, BarChart3, FileText, Search, Network, Star } from 'lucide-react'

export default function BenefitsKids() {
  const t = useTranslations('benefitsKids')

  const benefits = [
    { icon: GraduationCap, key: 'scholarship' },
    { icon: BarChart3, key: 'recognition' },
    { icon: FileText, key: 'portfolio' },
    { icon: Search, key: 'diagnostic' },
    { icon: Network, key: 'structure' },
    { icon: Star, key: 'confidence' },
  ]

  return (
    <section className="section-dark">
      <div className="section-container">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            {t('title')}
          </h2>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            {t('subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {benefits.map((benefit, index) => (
            <div
              key={index}
              className="card-primary card-hover-lift group"
            >
              <div className="mb-6 p-4 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 w-fit">
                <benefit.icon size={36} className="text-cyan-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4 group-hover:text-cyan-400 transition-colors">
                {t(`${benefit.key}.title`)}
              </h3>
              <p className="text-slate-300 leading-relaxed">
                {t(`${benefit.key}.description`)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
