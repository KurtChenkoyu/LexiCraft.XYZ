'use client'

import { useTranslations } from 'next-intl'
import { ShieldCheck, Blocks, Pickaxe, Sparkles, Gem } from 'lucide-react'

export default function HowItWorks() {
  const t = useTranslations('howItWorks')

  const steps = [
    {
      number: '1',
      icon: ShieldCheck,
      titleKey: 'step1.title',
      descKey: 'step1.description',
    },
    {
      number: '2',
      icon: Blocks,
      titleKey: 'step2.title',
      descKey: 'step2.description',
    },
    {
      number: '3',
      icon: Pickaxe,
      titleKey: 'step3.title',
      descKey: 'step3.description',
    },
    {
      number: '4',
      icon: Sparkles,
      titleKey: 'step4.title',
      descKey: 'step4.description',
    },
    {
      number: '5',
      icon: Gem,
      titleKey: 'step5.title',
      descKey: 'step5.description',
    },
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {steps.map((step, index) => (
            <div
              key={index}
              className="card-primary card-hover-lift relative group"
            >
              <div className="absolute -top-4 -right-4 w-12 h-12 bg-gradient-to-br from-neon-cyan to-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg shadow-lg shadow-neon-cyan/30">
                {step.number}
              </div>
              <div className="mb-6 p-3 rounded-xl bg-gradient-to-br from-white/10 to-white/5 w-fit">
                <step.icon size={40} className="text-neon-cyan" />
              </div>
              <h3 className="text-lg font-bold text-white mb-3 group-hover:text-neon-cyan transition-colors">
                {t(step.titleKey)}
              </h3>
              <p className="text-slate-300 text-sm leading-relaxed">
                {t(step.descKey)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

