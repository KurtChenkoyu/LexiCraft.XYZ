'use client'

import { usePathname } from 'next/navigation'
import { Link } from '@/i18n/routing'
import { useIsMobile } from '@/hooks/useMediaQuery'
import { useAppStore, selectUnreadNotificationsCount } from '@/stores/useAppStore'
import { useRolePreference } from '@/hooks/useRolePreference'

/**
 * Tab configuration for Learner Bottom Navigation
 * 
 * URLs use /learner/* prefix per Architecture Bible
 * @see .cursorrules - App Architecture Bible, Section 2
 */
const tabs = [
  {
    id: 'mine',
    label: '礦區',
    href: '/learner/mine',
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
    id: 'build',
    label: '建造',
    href: '/learner/build',
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
          d="M8.25 21v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21m0 0h4.5V3.545M12.75 21h7.5V10.75M2.25 21h1.5m18 0h-18M2.25 9l4.5-1.636M18.75 3l-1.5.545m0 6.205l3 1m1.5.5l-1.5-.5M6.75 7.364V3h-3v18m3-13.636l10.5-3.819"
        />
      </svg>
    ),
  },
  {
    id: 'quiz',
    label: '驗證',
    href: '/learner/verification',
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
    href: '/learner/leaderboards',
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
    id: 'family',
    label: '家庭',
    href: '/learner/family',
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
          d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"
        />
      </svg>
    ),
    // Only show for parent-learners
    showWhen: (isParent: boolean) => isParent,
  },
  {
    id: 'profile',
    label: '我的',
    href: '/learner/profile',
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
  const { isParent } = useRolePreference()
  
  // Get badge counts from Zustand (instant, no fetch)
  // FIXED: Use stable selector function defined outside component to avoid function recreation
  // Select count directly (primitive) instead of array to avoid infinite loop
  const unreadCount = useAppStore(selectUnreadNotificationsCount)

  // Don't render on desktop
  if (!isMobile) return null

  // Filter tabs based on role (show Family only for parent-learners)
  const visibleTabs = tabs.filter(tab => {
    if (tab.showWhen) {
      return tab.showWhen(isParent)
    }
    return true
  })

  // Determine active tab from pathname
  const getActiveTab = () => {
    // Remove locale prefix for matching (e.g., /zh-TW/mine -> /mine)
    const pathWithoutLocale = '/' + pathname.split('/').slice(2).join('/')
    
    for (const tab of visibleTabs) {
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
        {visibleTabs.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <Link
              key={tab.id}
              href={tab.href}
              prefetch={true}
              className={`flex flex-col items-center justify-center flex-1 h-full py-1 
                transition-all duration-75
                ${isActive
                  ? 'text-cyan-400'
                  : 'text-slate-400 active:text-cyan-300 active:scale-95'
                }`}
            >
              <div className={`relative transition-transform duration-75 ${!isActive ? 'active:scale-110' : ''}`}>
                {tab.icon(isActive)}
                {/* Active indicator glow */}
                {isActive && (
                  <div className="absolute inset-0 bg-cyan-400/20 blur-md rounded-full" />
                )}
                {/* Badge for verification (if due cards exist) */}
                {tab.id === 'quiz' && unreadCount > 0 && (
                  <div className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </div>
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

