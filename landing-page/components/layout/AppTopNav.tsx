'use client'

import { useTranslations } from 'next-intl'
import { Link, usePathname, useRouter } from '@/i18n/routing'
import { trackEvent } from '@/lib/analytics'
import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/contexts/UserDataContext'
import { useRolePreference } from '@/hooks/useRolePreference'
import { NotificationsDropdown } from '@/components/features/notifications/NotificationsDropdown'
import { GlobalSearch } from '@/components/search/GlobalSearch'
import { useIsMobile } from '@/hooks/useMediaQuery'
import { useSidebar } from '@/contexts/SidebarContext'

const languages = [
  { code: 'zh-TW', label: '繁體中文', flag: '🇹🇼' },
  { code: 'en', label: 'English', flag: '🇺🇸' },
]

/**
 * Parent navigation items (shown in top nav)
 * URLs use /parent/* prefix per Architecture Bible
 * @see .cursorrules - App Architecture Bible, Section 2
 */
const parentNavItems = [
  { href: '/parent/dashboard', labelKey: 'dashboard', label: '控制台' },
  { href: '/parent/children', labelKey: 'children', label: '孩子管理' },
  { href: '/parent/goals', labelKey: 'goals', label: '目標' },
  { href: '/parent/settings', labelKey: 'settings', label: '設定' },
]

interface AppTopNavProps {
  currentLocale: string
}

export default function AppTopNav({ currentLocale }: AppTopNavProps) {
  const t = useTranslations('navbar')
  const pathname = usePathname()
  const router = useRouter()
  const { user, signOut } = useAuth()
  
  // UserDataProvider is only available in (app) route group
  // On landing pages, useUserData returns safe defaults (no error thrown)
  const { children, selectedChildId, selectChild } = useUserData()
  const { currentRole, canSwitchRoles, isParent, isLearner, setRole } = useRolePreference()
  const [isLanguageMenuOpen, setIsLanguageMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [isChildSelectorOpen, setIsChildSelectorOpen] = useState(false)
  const languageMenuRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const childSelectorRef = useRef<HTMLDivElement>(null)
  const isMobile = useIsMobile()

  // Find current language
  const currentLang = languages.find(l => l.code === currentLocale) || languages[0]

  const switchLanguage = (langCode: string) => {
    router.replace(pathname, { locale: langCode })
    setIsLanguageMenuOpen(false)
    trackEvent('language_switched', { from: currentLocale, to: langCode })
  }

  // Handle navigation click - redirect to signup if not authenticated
  const handleNavClick = useCallback((href: string, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault()
    }
    
    if (!user) {
      router.push(`/signup?returnUrl=${encodeURIComponent(href)}`)
      trackEvent('nav_clicked_unauth', { href })
    } else {
      router.push(href)
    }
  }, [user, router])

  // Handle role switch
  const handleRoleSwitch = useCallback((role: 'parent' | 'learner') => {
    setRole(role)
    setIsUserMenuOpen(false)
    if (role === 'parent') {
      router.push('/parent/dashboard')
    } else {
      router.push('/learner/mine')
    }
    trackEvent('role_switched', { to: role })
  }, [setRole, router])

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (languageMenuRef.current && !languageMenuRef.current.contains(event.target as Node)) {
        setIsLanguageMenuOpen(false)
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false)
      }
      if (childSelectorRef.current && !childSelectorRef.current.contains(event.target as Node)) {
        setIsChildSelectorOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close menus on route change
  useEffect(() => {
    setIsUserMenuOpen(false)
    setIsChildSelectorOpen(false)
    setIsLanguageMenuOpen(false)
  }, [pathname])

  // Close menus on Escape
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsUserMenuOpen(false)
        setIsChildSelectorOpen(false)
        setIsLanguageMenuOpen(false)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const selectedChild = children.find(c => c.id === selectedChildId)
  const hasChildren = children.length > 0
  const showChildSelector = user && isParent && hasChildren
  const { toggle: toggleSidebar } = useSidebar()
  const showHamburger = isMobile && user && isParent

  return (
    <nav 
      className="fixed top-0 left-0 right-0 z-50 bg-cosmic-950/80 backdrop-blur-md border-b border-white/5 shadow-lg"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className={`flex items-center justify-between ${isMobile ? 'h-16' : 'h-20'}`}>
          {/* Left side: Hamburger menu + Logo */}
          <div className="flex items-center gap-3">
            {/* Hamburger menu button (mobile, authenticated parent only) */}
            {showHamburger && (
              <button
                onClick={toggleSidebar}
                className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors"
                aria-label="開啟選單"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            {/* Logo */}
            <Link 
              href="/" 
              className={`font-bold font-mono tracking-tighter group ${isMobile ? 'text-xl' : 'text-2xl'}`}
              aria-label="LexiCraft.xyz Home"
            >
              <span className="text-white group-hover:text-neon-cyan transition-colors">LexiCraft</span>
              <span className="text-neon-cyan group-hover:text-white transition-colors">.xyz</span>
              {!isMobile && (
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-white/10 text-slate-400 border border-white/10">BETA</span>
              )}
            </Link>
          </div>

          {/* Center section: Navigation or Search */}
          {!isMobile && user && (
            <div className="flex items-center gap-4">
              {/* Parent Navigation Items */}
              {isParent && (
                <div className="flex items-center gap-1">
                  {parentNavItems.map((item) => {
                    const isActive = pathname.includes(item.href)
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`px-3 py-2 text-sm font-mono rounded-lg transition-colors ${
                          isActive
                            ? 'text-neon-cyan bg-neon-cyan/10 border border-neon-cyan/30'
                            : 'text-slate-400 hover:text-white hover:bg-white/5'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        {item.label}
                      </Link>
                    )
                  })}
                </div>
              )}
              
              {/* Global Search (Learner only on desktop) */}
              {isLearner && <GlobalSearch />}
            </div>
          )}

          {/* Right side items */}
          <div className="flex items-center gap-2 lg:gap-4">
            {/* Child Selector (when authenticated + parent + has children) */}
            {showChildSelector && (
              <div className="relative" ref={childSelectorRef}>
                <button
                  onClick={() => setIsChildSelectorOpen(!isChildSelectorOpen)}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-mono text-slate-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors border border-white/10"
                  aria-label="選擇孩子"
                  aria-expanded={isChildSelectorOpen}
                >
                  <span className="text-lg">👤</span>
                  {!isMobile && (
                    <>
                      <span>{selectedChild?.name || '未命名'}</span>
                      {children.length > 1 && (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </>
                  )}
                </button>

                {isChildSelectorOpen && children.length > 1 && (
                  <div className="absolute right-0 mt-2 w-48 bg-cosmic-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                    {children.map((child) => (
                      <button
                        key={child.id}
                        onClick={() => {
                          selectChild(child.id)
                          setIsChildSelectorOpen(false)
                        }}
                        className={`w-full text-left px-4 py-3 text-sm font-mono hover:bg-white/5 flex items-center justify-between transition-colors ${
                          selectedChildId === child.id ? 'text-neon-cyan bg-white/5' : 'text-slate-400'
                        }`}
                      >
                        <span>{child.name || '未命名'}</span>
                        {child.age && <span className="text-xs text-slate-500">{child.age}歲</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Add Child Button (when parent but no children) */}
            {user && isParent && !hasChildren && (
              <Link
                href="/parent/children"
                className="px-3 py-2 text-sm font-mono text-neon-cyan border border-neon-cyan/30 rounded-lg hover:bg-neon-cyan/10 transition-colors"
              >
                {isMobile ? '+' : '新增孩子'}
              </Link>
            )}

            {/* Notifications (when authenticated) */}
            {user && <NotificationsDropdown />}

            {/* User Menu */}
            {user ? (
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-mono text-slate-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                  aria-label="User menu"
                  aria-expanded={isUserMenuOpen}
                >
                  <div className="w-8 h-8 rounded-full bg-neon-cyan/20 border border-neon-cyan/30 flex items-center justify-center">
                    <span className="text-neon-cyan text-xs font-bold">
                      {user.email?.[0]?.toUpperCase() || 'U'}
                    </span>
                  </div>
                  {!isMobile && (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>

                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-cosmic-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-[100]">
                    {/* Dashboard/App Access - Always show first for authenticated users */}
                    <Link
                      href={isParent && currentRole === 'parent' ? '/dashboard' : '/mine'}
                      onClick={() => setIsUserMenuOpen(false)}
                      className="block px-4 py-3 text-sm font-mono hover:bg-white/5 transition-colors text-neon-cyan font-semibold bg-neon-cyan/5 border-b border-neon-cyan/20"
                    >
                      {isParent && currentRole === 'parent' ? '前往控制台' : '前往學習頁面'}
                    </Link>
                    <div className="border-t border-white/10 my-1" />

                    {/* Role Switcher (if user has multiple roles) */}
                    {canSwitchRoles && (
                      <>
                        <div className="px-4 py-2 border-b border-white/10">
                          <span className="text-xs font-mono text-slate-400">切換視角</span>
                        </div>
                        {isParent && isLearner && (
                          <button
                            onClick={() => handleRoleSwitch(currentRole === 'parent' ? 'learner' : 'parent')}
                            className="w-full text-left px-4 py-3 text-sm font-mono hover:bg-white/5 flex items-center justify-between transition-colors text-slate-300"
                          >
                            <span>切換到{currentRole === 'parent' ? '學習者' : '家長'}視角</span>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                            </svg>
                          </button>
                        )}
                        <div className="border-t border-white/10 my-1" />
                      </>
                    )}

                    {/* Profile Links */}
                    <Link
                      href={isParent ? '/parent/settings' : '/learner/profile'}
                      onClick={() => setIsUserMenuOpen(false)}
                      className="block px-4 py-3 text-sm font-mono hover:bg-white/5 transition-colors text-slate-300"
                    >
                      {isParent ? '帳戶設定' : '個人資料'}
                    </Link>
                    <Link
                      href="/parent/settings"
                      onClick={() => setIsUserMenuOpen(false)}
                      className="block px-4 py-3 text-sm font-mono hover:bg-white/5 transition-colors text-slate-300"
                    >
                      設定
                    </Link>
                    <div className="border-t border-white/10 my-1" />
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false)
                        signOut()
                      }}
                      className="w-full text-left px-4 py-3 text-sm font-mono hover:bg-white/5 transition-colors text-slate-300"
                    >
                      登出
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                {/* Sign In / Sign Up (not authenticated) */}
                <Link
                  href="/login"
                  className="hidden sm:block px-4 py-2 text-sm font-mono text-slate-400 hover:text-white transition-colors"
                >
                  登入
                </Link>
                <Link
                  href="/signup"
                  className={`text-sm font-bold text-white bg-white/10 border border-white/10 rounded-full hover:bg-white/20 hover:scale-105 transition-all backdrop-blur-sm ${isMobile ? 'px-4 py-1.5' : 'px-5 py-2'}`}
                >
                  註冊
                </Link>
              </>
            )}

            {/* Language Switcher */}
            <div className="relative" ref={languageMenuRef}>
              <button
                onClick={() => setIsLanguageMenuOpen(!isLanguageMenuOpen)}
                className="flex items-center space-x-1 lg:space-x-2 text-slate-400 hover:text-white transition-colors text-sm font-mono p-2 rounded-lg hover:bg-white/5"
                aria-label="Language selector"
                aria-expanded={isLanguageMenuOpen}
              >
                <span className="text-lg">{currentLang.flag}</span>
                {!isMobile && (
                  <>
                    <span className="hidden lg:inline">{currentLang.label}</span>
                    <svg
                      className={`w-4 h-4 transition-transform ${isLanguageMenuOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </>
                )}
              </button>

              {isLanguageMenuOpen && (
                <div className="absolute right-0 mt-2 w-40 bg-cosmic-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => switchLanguage(lang.code)}
                      className={`w-full text-left px-4 py-3 text-sm font-mono hover:bg-white/5 flex items-center space-x-3 transition-colors
                        ${currentLang.code === lang.code ? 'text-neon-cyan bg-white/5' : 'text-slate-400'}
                      `}
                    >
                      <span className="text-lg">{lang.flag}</span>
                      <span>{lang.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

