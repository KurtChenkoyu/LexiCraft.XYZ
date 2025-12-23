'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { CampaignConfig, trackCampaignEvent } from '@/lib/campaign-config'
import { DemoFlow } from './DemoFlow'

// ===========================================
// SHARED COMPONENTS FOR EMOJI LANDING PAGES
// ===========================================

interface EmojiLandingPageProps {
  campaign: CampaignConfig
  checkoutUrl: string
}

// Floating emoji animation
function FloatingEmoji({ emoji, delay }: { emoji: string; delay: number }) {
  return (
    <motion.div
      className="absolute text-4xl opacity-20 pointer-events-none"
      initial={{ 
        x: Math.random() * 100 + '%',
        y: '100vh',
        rotate: 0,
      }}
      animate={{ 
        y: '-20vh',
        rotate: 360,
      }}
      transition={{
        duration: 15 + Math.random() * 10,
        repeat: Infinity,
        delay,
        ease: 'linear',
      }}
    >
      {emoji}
    </motion.div>
  )
}

// Snowflake component
function Snowflake({ delay }: { delay: number }) {
  return (
    <motion.div
      className="absolute text-white text-xl opacity-60 pointer-events-none"
      style={{ left: `${Math.random() * 100}%` }}
      initial={{ y: -20 }}
      animate={{ 
        y: '100vh',
        x: [0, 30, -30, 0],
      }}
      transition={{
        duration: 8 + Math.random() * 4,
        repeat: Infinity,
        delay,
        ease: 'linear',
      }}
    >
      ❄️
    </motion.div>
  )
}

// Interactive Demo MCQ
function DemoMCQ({ campaign }: { campaign: CampaignConfig }) {
  const [selected, setSelected] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  
  const question = { word: 'apple', correct: '🍎', options: ['🍎', '🍌', '🍊', '🍇'] }
  
  const handleSelect = (option: string) => {
    setSelected(option)
    trackCampaignEvent(campaign, 'ctaClick', { action: 'demo_select', option })
  }
  
  const handleCheck = () => {
    setShowResult(true)
    setTimeout(() => {
      setShowResult(false)
      setSelected(null)
    }, 2000)
  }
  
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 }}
      className="bg-slate-800/80 backdrop-blur-sm rounded-3xl p-6 shadow-2xl border border-slate-700 max-w-sm mx-auto"
    >
      <div className="text-center mb-4">
        <span className={`bg-gradient-to-r ${campaign.theme.primary} text-transparent bg-clip-text text-sm font-bold`}>
          試玩看看！
        </span>
      </div>
      
      <div className="text-center mb-6">
        <span className="text-4xl font-black text-white">{question.word}</span>
        <p className="text-slate-400 text-sm mt-1">選擇正確的表情符號</p>
      </div>
      
      <div className="grid grid-cols-4 gap-2 mb-4">
        {question.options.map((opt) => (
          <button
            key={opt}
            onClick={() => handleSelect(opt)}
            className={`text-4xl p-3 rounded-xl transition-all ${
              selected === opt 
                ? showResult 
                  ? opt === question.correct 
                    ? 'bg-emerald-500 scale-110' 
                    : 'bg-red-500 shake'
                  : 'bg-cyan-500 scale-105'
                : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
      
      <button
        onClick={handleCheck}
        disabled={!selected || showResult}
        className={`w-full py-3 rounded-xl font-bold transition-all ${
          selected && !showResult
            ? `bg-gradient-to-r ${campaign.theme.primary} text-white`
            : 'bg-slate-700 text-slate-500'
        }`}
      >
        {showResult 
          ? selected === question.correct ? '🎉 正確！' : '😅 再試一次'
          : '確認答案'
        }
      </button>
    </motion.div>
  )
}

// Hero Section - All CTAs lead to checkout/login, NOT into the game
function HeroSection({ campaign, isLoggedIn, checkoutUrl }: { 
  campaign: CampaignConfig
  isLoggedIn: boolean
  checkoutUrl: string
}) {
  const handleCheckout = () => {
    trackCampaignEvent(campaign, 'checkoutStart')
    window.open(checkoutUrl, '_blank')
  }

  return (
    <section className="relative z-10 min-h-screen flex items-center px-4 py-20">
      <div className="max-w-6xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-block mb-4"
            >
              <span className={`bg-gradient-to-r ${campaign.theme.primary} text-white px-4 py-2 rounded-full text-sm font-bold`}>
                {campaign.content.heroTagline}
              </span>
            </motion.div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white mb-6 leading-tight">
              用 <span className={`bg-gradient-to-r ${campaign.theme.primary} text-transparent bg-clip-text`}>表情符號</span> 學英文！
            </h1>
            
            <p className="text-xl text-slate-300 mb-8">
              {campaign.content.heroSubtitle}。
              <br className="hidden sm:block" />
              200個常用單字 × 有趣表情符號 = 快樂學習！
            </p>

            {/* Price Anchor Text */}
            {campaign.content.priceAnchorText && (
              <div className="mb-6 text-center sm:text-left">
                <p className="text-slate-400 text-sm">
                  {(() => {
                    const parts = campaign.content.priceAnchorText.split('~~')
                    const originalPrice = parts[1] || ''
                    const promoText = parts[2] || parts[0] || ''
                    return (
                      <>
                        <span className="line-through">{originalPrice}</span>
                        {' '}
                        <span className="text-red-400 font-bold">{promoText.trim()}</span>
                      </>
                    )
                  })()}
                </p>
              </div>
            )}
            
            <div className="flex flex-wrap gap-4">
              {/* Primary CTA: Always leads to checkout flow */}
              {isLoggedIn ? (
                <motion.a
                  href={checkoutUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={handleCheckout}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold rounded-xl shadow-lg cursor-pointer"
                >
                  💳 NT${campaign.content.salePrice} 立即購買
                </motion.a>
              ) : (
                <Link href="/login">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-8 py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold rounded-xl shadow-lg"
                  >
                    🎁 免費註冊
                  </motion.button>
                </Link>
              )}
              <Link href="#pricing">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-4 bg-slate-800 text-white font-bold rounded-xl border border-slate-700"
                >
                  查看方案
                </motion.button>
              </Link>
            </div>
          </motion.div>
          
          {/* Right: Demo */}
          <div className="relative">
            <DemoFlow campaign={campaign} />
          </div>
        </div>
      </div>
    </section>
  )
}

// Word Forge Section (字塊所)
function WordForgeSection({ campaign }: { campaign: CampaignConfig }) {
  const stages = [
    { icon: '📦', title: '生字塊', subtitle: 'Raw Block', desc: '剛學到的新單字，還沒熟悉', color: 'from-slate-600 to-slate-700', textColor: 'text-slate-300' },
    { icon: '🔥', title: '鍛造中', subtitle: 'Forging', desc: '透過間隔複習不斷加強記憶', color: 'from-orange-500 to-red-600', textColor: 'text-orange-300' },
    { icon: '✨', title: '熟練塊', subtitle: 'Mastered', desc: '連續答對，記憶已經穩固！', color: 'from-cyan-500 to-blue-600', textColor: 'text-cyan-300' },
    { icon: '💎', title: '永久塊', subtitle: 'Permanent', desc: '長期記憶，永遠是你的！', color: 'from-purple-500 to-pink-600', textColor: 'text-purple-300' },
  ]
  
  return (
    <section className="relative z-10 px-4 py-20 bg-gradient-to-b from-slate-900 to-indigo-950">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <span className="text-5xl mb-4 block">⚒️</span>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            字塊所 <span className={campaign.theme.accent}>Word Forge</span>
          </h2>
          <p className="text-xl text-slate-400">
            LexiCraft 獨創的記憶驗證系統
          </p>
        </motion.div>
        
        {/* Forge Process Visual */}
        <div className="grid md:grid-cols-4 gap-4 mb-12">
          {stages.map((stage, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="relative"
            >
              <div className={`bg-gradient-to-br ${stage.color} rounded-2xl p-6 text-center h-full`}>
                <div className="text-4xl mb-3">{stage.icon}</div>
                <h3 className="text-lg font-bold text-white">{stage.title}</h3>
                <p className="text-xs text-white/60 mb-2">{stage.subtitle}</p>
                <p className={`text-sm ${stage.textColor}`}>{stage.desc}</p>
              </div>
              {i < 3 && (
                <div className="hidden md:block absolute top-1/2 -right-2 transform -translate-y-1/2 text-2xl text-slate-500">
                  →
                </div>
              )}
            </motion.div>
          ))}
        </div>
        
        {/* Key Benefits */}
        <div className="grid md:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700"
          >
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-2xl">🧠</span> 間隔複習科學
            </h3>
            <p className="text-slate-400">
              基於艾賓浩斯遺忘曲線，系統會在你「快要忘記」的時候提醒複習。
              不浪費時間重複已經會的，專注練習需要加強的！
            </p>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700"
          >
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-2xl">🎮</span> 遊戲化收集
            </h3>
            <p className="text-slate-400">
              每個單字都是你的「資產」！看著自己的字塊從生疏變成永久，
              就像在遊戲裡收集裝備一樣令人上癮！
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

// Pricing Section
function PricingSection({ campaign, isLoggedIn, checkoutUrl }: { 
  campaign: CampaignConfig
  isLoggedIn: boolean
  checkoutUrl: string
}) {
  const handleCheckout = () => {
    trackCampaignEvent(campaign, 'checkoutStart')
    window.open(checkoutUrl, '_blank')
  }
  
  const features = [
    '200個精選表情符號單字',
    '雙向配對遊戲 (單字↔表情)',
    '語音發音 (AI朗讀)',
    '學習進度追蹤',
    '間隔複習系統',
    '家長監控面板',
    '無廣告・無限制',
  ]
  
  return (
    <section id="pricing" className="relative z-10 px-4 py-20 bg-gradient-to-b from-slate-900 to-slate-800">
      <div className="max-w-xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className={`bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-8 border-2 border-amber-500/50 shadow-2xl relative overflow-hidden`}
        >
          {/* Badge */}
          <div className="absolute top-4 right-4">
            <span className={`bg-gradient-to-r ${campaign.theme.primary} text-white px-3 py-1 rounded-full text-xs font-bold`}>
              {campaign.content.heroTagline.replace(/🎄|🎅|🧧|🐍|📚|✏️/g, '').trim()}
            </span>
          </div>
          
          <h3 className="text-2xl font-bold text-white mb-2">表情學英文 啟動包</h3>
          <p className="text-slate-400 mb-6">200個表情符號單字・無限練習</p>
          
          {/* Price */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-1">
              <span className="text-slate-500 line-through text-xl">NT${campaign.content.originalPrice}</span>
              <span className="bg-amber-500 text-black px-2 py-0.5 rounded text-sm font-bold">
                {campaign.content.discountLabel}
              </span>
            </div>
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-5xl font-black text-white">NT${campaign.content.salePrice}</span>
            </div>
            <p className="text-emerald-400 font-medium mt-1">
              一次付費，{campaign.content.duration}暢玩！
            </p>
            {/* Price Anchor Text */}
            {campaign.content.priceAnchorText && (
              <p className="text-slate-400 text-sm mt-2">
                <span className="line-through">
                  {campaign.content.priceAnchorText.match(/~~([^~]+)~~/)?.[1] || ''}
                </span>
                {' '}
                <span className="text-red-400 font-bold">
                  {campaign.content.priceAnchorText.split('~~').slice(-1)[0]?.trim() || ''}
                </span>
              </p>
            )}
          </div>
          
          {/* Features */}
          <ul className="space-y-3 mb-8">
            {features.map((feature, i) => (
              <li key={i} className="flex items-center gap-2 text-slate-300">
                <span className="text-emerald-400">✓</span> {feature}
              </li>
            ))}
          </ul>
          
          {/* CTA */}
          {isLoggedIn ? (
            <>
              <motion.a
                href={checkoutUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={handleCheckout}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="block w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 text-black font-black text-xl rounded-xl shadow-lg transition-all text-center"
              >
                💳 立即購買 NT${campaign.content.salePrice}
              </motion.a>
              <p className="text-center text-slate-400 text-sm mt-4">
                安全付款，立即開通
              </p>
            </>
          ) : (
            <>
              <Link href="/login">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-4 bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 text-black font-black text-xl rounded-xl shadow-lg transition-all"
                >
                  🎁 免費註冊，立即體驗
                </motion.button>
              </Link>
              <p className="text-center text-slate-400 text-sm mt-4">
                先試玩，滿意再付款
              </p>
            </>
          )}
        </motion.div>
      </div>
    </section>
  )
}

// Final CTA Section - All CTAs lead to checkout/login
function FinalCTASection({ campaign, isLoggedIn, checkoutUrl }: { 
  campaign: CampaignConfig
  isLoggedIn: boolean
  checkoutUrl: string
}) {
  const handleCheckout = () => {
    trackCampaignEvent(campaign, 'checkoutStart')
    window.open(checkoutUrl, '_blank')
  }

  return (
    <section className="relative z-10 px-4 py-20 text-center">
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <div className="text-6xl mb-6">{campaign.content.finalCTA.emojis}</div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            {campaign.content.finalCTA.title}<br />
            {campaign.content.finalCTA.subtitle}
          </h2>
          <p className="text-xl text-slate-400 mb-8">
            快樂學習，從今天開始！
          </p>
          {isLoggedIn ? (
            <motion.a
              href={checkoutUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleCheckout}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="inline-block px-12 py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold text-xl rounded-xl shadow-lg"
            >
              💳 NT${campaign.content.salePrice} 立即購買
            </motion.a>
          ) : (
            <Link href="/login">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-12 py-4 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold text-xl rounded-xl shadow-lg"
              >
                🎁 免費註冊
              </motion.button>
            </Link>
          )}
        </motion.div>
      </div>
    </section>
  )
}

// ===========================================
// MAIN COMPONENT
// ===========================================

export default function EmojiLandingPage({ campaign, checkoutUrl }: EmojiLandingPageProps) {
  const [mounted, setMounted] = useState(false)
  const { user, loading: authLoading } = useAuth()
  
  const isLoggedIn = !authLoading && !!user
  
  // Track page view
  useEffect(() => {
    if (mounted) {
      trackCampaignEvent(campaign, 'pageView')
    }
  }, [mounted, campaign])
  
  useEffect(() => {
    setMounted(true)
  }, [])
  
  if (!mounted) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-6xl animate-bounce">{campaign.theme.emoji}</div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 relative">
        {/* Background Effects */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          {campaign.theme.floatingEmojis.map((emoji, i) => (
            <FloatingEmoji key={i} emoji={emoji} delay={i * 2} />
          ))}
          {campaign.theme.snowflakes && Array.from({ length: 20 }).map((_, i) => (
            <Snowflake key={`snow-${i}`} delay={i * 0.5} />
          ))}
        </div>
        
        {/* Sections - No duplicate nav, global nav handles it */}
        <div className="pt-4">
          <HeroSection campaign={campaign} isLoggedIn={isLoggedIn} checkoutUrl={checkoutUrl} />
        </div>
        <WordForgeSection campaign={campaign} />
        <PricingSection 
          campaign={campaign} 
          isLoggedIn={isLoggedIn} 
          checkoutUrl={checkoutUrl}
        />
        <FinalCTASection campaign={campaign} isLoggedIn={isLoggedIn} checkoutUrl={checkoutUrl} />
        
        {/* Footer */}
        <footer className="relative z-10 py-8 border-t border-slate-800">
          <div className="max-w-6xl mx-auto px-4 text-center text-slate-500 text-sm">
            <div className="flex justify-center gap-4 mb-4">
              <Link href="/privacy" className="hover:text-slate-300">隱私政策</Link>
              <Link href="/" className="hover:text-slate-300">主網站</Link>
            </div>
            <p>© 2024 LexiCraft. Made with {campaign.theme.emoji} in Taiwan.</p>
          </div>
        </footer>
      </div>
  )
}

