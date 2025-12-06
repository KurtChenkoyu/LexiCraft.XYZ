'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/routing'
import { trackEvent } from '@/lib/analytics'
import { ShieldCheck, Pickaxe, Gem } from 'lucide-react'
import WordCloud from './WordCloud'

export default function Hero() {
  const t = useTranslations('hero')

  const handleScrollToForm = () => {
    trackEvent('hero_waitlist_clicked')
    document.getElementById('waitlist-form')?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSurveyClick = () => {
    trackEvent('hero_survey_clicked')
  }

  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden bg-cosmic-950 text-white pt-20">
      {/* Animated Word Cloud Background */}
      <WordCloud />

      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-neon-violet/20 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute top-[40%] -right-[10%] w-[40%] h-[40%] bg-neon-cyan/20 rounded-full blur-[100px] animate-pulse delay-1000"></div>
        <div className="absolute -bottom-[20%] left-[20%] w-[60%] h-[60%] bg-blue-600/10 rounded-full blur-[120px]"></div>
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 flex flex-col items-center text-center z-10">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6 sm:mb-8 animate-fade-in-up">
          <span className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse"></span>
          <span className="text-xs sm:text-sm font-medium text-slate-200">Beta Launch • Early Access</span>
        </div>

        {/* Headline - Mobile Optimized */}
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold mb-4 sm:mb-6 animate-fade-in-up delay-100 leading-tight px-2">
          <span className="block mb-2">你出資，他挖礦</span>
          <span className="block text-gradient-premium mb-3 sm:mb-4">知識與財富，同步繼承</span>
          <span className="block text-xl sm:text-2xl md:text-3xl lg:text-4xl font-normal text-slate-300 mt-4 sm:mt-6">LexiCraft.xyz • 字塊所</span>
        </h1>

        {/* Subtitle - Mobile Optimized */}
        <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-slate-300 max-w-3xl mb-8 sm:mb-12 animate-fade-in-up delay-200 leading-relaxed px-4">
          首創知識資產交易所。<br className="hidden sm:inline" />把資金轉成待解鎖的字塊。
        </p>

        {/* Value Props Cards - Floating */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 max-w-5xl mx-auto w-full perspective-1000">

          {/* Card 1 */}
          <div className="glass-card glass-card-hover rounded-2xl p-6 text-left transform transition-all hover:-translate-y-2 animate-fade-in-up delay-300">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-violet to-blue-600 flex items-center justify-center text-white mb-4 shadow-lg shadow-neon-violet/30">
              <ShieldCheck size={24} />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Safe Investment</h3>
            <p className="text-sm text-slate-300 leading-relaxed">{t('valueProp1')}</p>
          </div>

          {/* Card 2 - Center Card */}
          <div className="glass-card glass-card-hover rounded-2xl p-6 text-left transform transition-all hover:-translate-y-2 animate-fade-in-up delay-150 md:-mt-4 border-neon-cyan/30 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan to-blue-500 flex items-center justify-center text-white mb-4 shadow-lg shadow-neon-cyan/30">
              <Pickaxe size={24} />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Earn Back</h3>
            <p className="text-sm text-slate-300 leading-relaxed">{t('valueProp2')}</p>
          </div>

          {/* Card 3 */}
          <div className="glass-card glass-card-hover rounded-2xl p-6 text-left transform transition-all hover:-translate-y-2 animate-fade-in-up delay-500">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-fuchsia to-pink-600 flex items-center justify-center text-white mb-4 shadow-lg shadow-neon-fuchsia/30">
              <Gem size={24} />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Mastery</h3>
            <p className="text-sm text-slate-300 leading-relaxed">{t('valueProp3')}</p>
          </div>
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-5 justify-center items-center mb-12 animate-fade-in-up delay-700 w-full sm:w-auto">
          <Link
            href="/survey"
            onClick={handleSurveyClick}
            className="group relative px-8 py-4 bg-white text-slate-900 rounded-full font-bold text-lg tracking-wide shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)] hover:scale-105 transition-all duration-300 overflow-hidden"
          >
            <span className="relative z-10 flex items-center gap-2">
              {t('cta')}
              <span className="group-hover:translate-x-1 transition-transform">→</span>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-200 via-white to-cyan-200 opacity-0 group-hover:opacity-50 transition-opacity duration-300"></div>
          </Link>

          <button
            onClick={handleScrollToForm}
            className="px-8 py-4 bg-transparent border border-white/20 text-white rounded-full text-lg font-semibold hover:bg-white/10 hover:border-white/40 transition-all backdrop-blur-sm"
          >
            {t('ctaSecondary')}
          </button>
        </div>

        {/* Trust Bar */}
        <div className="flex flex-wrap justify-center items-center gap-6 text-sm text-slate-400 animate-fade-in-up delay-1000 border-t border-white/5 pt-8 w-full max-w-2xl">
          <span className="uppercase tracking-widest text-xs font-semibold text-slate-500">Trusted By Parents In</span>
          <span className="flex items-center gap-2 text-white"><span className="text-lg">🇹🇼</span> Taiwan</span>
          <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
          <span className="flex items-center gap-2 text-white"><span className="text-lg">🇺🇸</span> USA</span>
          <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
          <span className="flex items-center gap-2 text-white"><span className="text-lg">🇯🇵</span> Japan</span>
        </div>
      </div>
    </section>
  )
}

