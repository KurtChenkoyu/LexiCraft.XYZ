'use client'

import { Link, usePathname } from '@/i18n/routing'
import { useUserData } from '@/contexts/UserDataContext'
import { useRolePreference } from '@/hooks/useRolePreference'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useIsMobile } from '@/hooks/useMediaQuery'

interface NavItem {
  href: string
  label: string
  icon: (active: boolean) => React.ReactNode
  badge?: number | string
}

/**
 * Navigation items for Parent Sidebar
 * 
 * URLs use /parent/* prefix per Architecture Bible
 * @see .cursorrules - App Architecture Bible, Section 2
 */
const navItems: NavItem[] = [
  {
    href: '/parent/dashboard',
    label: '控制台',
    icon: (active) => (
      <svg className={`w-5 h-5 ${active ? 'text-neon-cyan' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    href: '/parent/children',
    label: '孩子管理',
    icon: (active) => (
      <svg className={`w-5 h-5 ${active ? 'text-neon-cyan' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
  },
  {
    href: '/parent/goals',
    label: '目標',
    icon: (active) => (
      <svg className={`w-5 h-5 ${active ? 'text-neon-cyan' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    href: '/parent/achievements',
    label: '成就',
    icon: (active) => (
      <svg className={`w-5 h-5 ${active ? 'text-neon-cyan' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
    ),
  },
  {
    href: '/parent/settings',
    label: '設定',
    icon: (active) => (
      <svg className={`w-5 h-5 ${active ? 'text-neon-cyan' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

interface ParentSidebarProps {
  onClose?: () => void
}

export function ParentSidebar({ onClose }: ParentSidebarProps = {}) {
  const pathname = usePathname()
  const { children } = useUserData()
  const { currentRole, isLearner, setRole } = useRolePreference()
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const isMobile = useIsMobile()

  // Determine active route (remove locale prefix)
  const getActiveRoute = () => {
    const pathWithoutLocale = '/' + pathname.split('/').slice(2).join('/')
    return pathWithoutLocale
  }

  const activeRoute = getActiveRoute()

  // Handle role switch to learner
  const handleSwitchToLearner = () => {
    setRole('learner')
    router.push('/learner/home')
  }

  // Update children badge
  const childrenNavItem = navItems.find(item => item.href === '/parent/children')
  if (childrenNavItem) {
    childrenNavItem.badge = children.length
  }

  return (
    <aside
      className={`fixed left-0 ${isMobile ? 'top-16' : 'top-20'} bottom-0 z-40 bg-slate-900 border-r border-white/5 transition-all duration-300 ${
        isCollapsed && !isMobile ? 'w-16' : 'w-60'
      }`}
      aria-label="Parent navigation sidebar"
    >
      <div className="flex flex-col h-full">
        {/* Collapse toggle - Desktop only */}
        {!isMobile && (
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="absolute -right-3 top-4 w-6 h-6 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            aria-label={isCollapsed ? '展開側邊欄' : '收起側邊欄'}
          >
            <svg
              className={`w-4 h-4 transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}
        
        {/* Mobile close button */}
        {isMobile && onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white hover:bg-white/10 transition-colors"
            aria-label="關閉選單"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        {/* Navigation items */}
        <nav className="flex-1 overflow-y-auto py-4 px-2" aria-label="Parent navigation">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = activeRoute === item.href || activeRoute.startsWith(item.href + '/')
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => onClose?.()}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${
                      isActive
                        ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30'
                        : 'text-slate-300 hover:text-white hover:bg-white/5'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <span className="flex-shrink-0">{item.icon(isActive)}</span>
                    {!isCollapsed && (
                      <>
                        <span className="flex-1 font-mono text-sm">{item.label}</span>
                        {item.badge !== undefined && (
                          <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Role switcher (if user has learner role) */}
        {isLearner && !isCollapsed && (
          <div className="border-t border-white/10 p-4">
            <button
              onClick={handleSwitchToLearner}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/5 transition-colors font-mono text-sm"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <span>切換到學習者視角</span>
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}

export default ParentSidebar

