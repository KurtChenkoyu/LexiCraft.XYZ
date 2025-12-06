'use client'

import { useState } from 'react'
import { usePathname, useRouter } from '@/i18n/routing'
import { routing } from '@/i18n/routing'

const languages = [
  { code: 'zh-TW', label: '繁體中文', flag: '🇹🇼' },
  { code: 'en', label: 'English', flag: '🇺🇸' },
  // Future ready (commented out per strategic decision):
  // { code: 'ja', label: '日本語', flag: '🇯🇵' },
  // { code: 'zh-CN', label: '简体中文', flag: '🇨🇳' },
  // { code: 'ko', label: '한국어', flag: '🇰🇷' },
]

export default function LanguageSwitcher({ currentLocale }: { currentLocale: string }) {
  const pathname = usePathname()
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)

  // Find current language from the languages array
  const currentLang = languages.find(l => l.code === currentLocale) || languages[0]

  const switchLanguage = (langCode: string) => {
    // Use next-intl's router to switch locale (maintains current path)
    router.replace(pathname, { locale: langCode })
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors text-sm font-mono"
      >
        <span>{currentLang.flag}</span>
        <span className="hidden sm:inline">{currentLang.label}</span>
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-32 bg-slate-900 border border-cyan-500/20 rounded-lg shadow-xl overflow-hidden z-50">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => switchLanguage(lang.code)}
              className={`w-full text-left px-4 py-3 text-xs font-mono hover:bg-slate-800 flex items-center space-x-3 transition-colors
                ${currentLang.code === lang.code ? 'text-cyan-400 bg-slate-800/50' : 'text-gray-400'}
              `}
            >
              <span>{lang.flag}</span>
              <span>{lang.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

