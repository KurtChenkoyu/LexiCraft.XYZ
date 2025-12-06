'use client'

import { usePathname } from 'next/navigation'
import { Link } from '@/i18n/routing'
import { useIsMobile } from '@/hooks/useMediaQuery'

// Tab configuration
const tabs = [
  {
    id: 'mine',
    label: '礦區',
    href: '/mine',
    icon: (active: boolean) => (
      <svg
        className={`w-6 h-6 ${active ? 'text-cyan-400' : 'text-slate-400'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={active ? 2.5 : 2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"
        />
      </svg>
    ),
  },
  {
    id: 'quiz',
    label: '驗證',
    href: '/verification',
    icon: (active: boolean) => (
      <svg
        className={`w-6 h-6 ${active ? 'text-cyan-400' : 'text-slate-400'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={active ? 2.5 : 2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    id: 'ranks',
    label: '排行',
    href: '/leaderboards',
    icon: (active: boolean) => (
      <svg
        className={`w-6 h-6 ${active ? 'text-cyan-400' : 'text-slate-400'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={active ? 2.5 : 2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0"
        />
      </svg>
    ),
  },
  {
    id: 'profile',
    label: '我的',
    href: '/profile',
    icon: (active: boolean) => (
      <svg
        className={`w-6 h-6 ${active ? 'text-cyan-400' : 'text-slate-400'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={active ? 2.5 : 2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
        />
      </svg>
    ),
  },
]

export function BottomNav() {
  const pathname = usePathname()
  const isMobile = useIsMobile()

  // Don't render on desktop
  if (!isMobile) return null

  // Determine active tab from pathname
  const getActiveTab = () => {
    // Remove locale prefix for matching (e.g., /zh-TW/mine -> /mine)
    const pathWithoutLocale = '/' + pathname.split('/').slice(2).join('/')
    
    for (const tab of tabs) {
      if (pathWithoutLocale.startsWith(tab.href)) {
        return tab.id
      }
    }
    return null
  }

  const activeTab = getActiveTab()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-md border-t border-slate-800 pb-safe">
      <div className="flex items-center justify-around h-14">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <Link
              key={tab.id}
              href={tab.href}
              className={`flex flex-col items-center justify-center flex-1 h-full py-1 transition-all ${
                isActive
                  ? 'text-cyan-400'
                  : 'text-slate-400 active:text-slate-300'
              }`}
            >
              <div className="relative">
                {tab.icon(isActive)}
                {/* Active indicator glow */}
                {isActive && (
                  <div className="absolute inset-0 bg-cyan-400/20 blur-md rounded-full" />
                )}
              </div>
              <span
                className={`text-[10px] mt-0.5 font-medium ${
                  isActive ? 'text-cyan-400' : 'text-slate-500'
                }`}
              >
                {tab.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

export default BottomNav

