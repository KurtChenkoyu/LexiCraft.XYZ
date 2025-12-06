'use client'

import { useTranslations } from 'next-intl'
import { DollarSign, BarChart3, Target } from 'lucide-react'

export default function ParentQuestions() {
  const t = useTranslations('parentQuestions')

  const questions = [
    {
      icon: DollarSign,
      questionKey: 'question1',
      answerKey: 'answer1',
    },
    {
      icon: BarChart3,
      questionKey: 'question2',
      answerKey: 'answer2',
    },
    {
      icon: Target,
      questionKey: 'question3',
      answerKey: 'answer3',
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
            Every parent asks these questions
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {questions.map((q, index) => (
            <div
              key={index}
              className="card-primary card-hover-lift group"
            >
              <div className="mb-6 p-4 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-blue-600/20 w-fit">
                <q.icon size={32} className="text-neon-cyan" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4 group-hover:text-neon-cyan transition-colors">
                {t(q.questionKey)}
              </h3>
              <p className="text-slate-300 leading-relaxed">
                {t(q.answerKey)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}


