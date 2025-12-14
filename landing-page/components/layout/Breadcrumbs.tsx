'use client'

import { Link, usePathname } from '@/i18n/routing'

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[]
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  const pathname = usePathname()

  // Auto-generate breadcrumbs from pathname if not provided
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (items) return items

    const pathWithoutLocale = '/' + pathname.split('/').slice(2).join('/')
    const segments = pathWithoutLocale.split('/').filter(Boolean)

    const breadcrumbs: BreadcrumbItem[] = [
      { label: '控制台', href: '/dashboard' },
    ]

    const routeLabels: Record<string, string> = {
      'coach-dashboard': '學習分析',
      'children': '孩子管理',
      'deposits': '存款付款',
      'goals': '目標',
      'achievements': '成就',
      'settings': '設定',
    }

    segments.forEach((segment, index) => {
      const href = '/' + segments.slice(0, index + 1).join('/')
      const label = routeLabels[segment] || segment
      if (index < segments.length - 1) {
        breadcrumbs.push({ label, href })
      } else {
        breadcrumbs.push({ label })
      }
    })

    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs()

  if (breadcrumbs.length <= 1) return null

  return (
    <nav aria-label="Breadcrumb" className="mb-6">
      <ol className="flex items-center gap-2 text-sm font-mono text-slate-400">
        {breadcrumbs.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {index > 0 && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
            {item.href && index < breadcrumbs.length - 1 ? (
              <Link
                href={item.href}
                className="hover:text-neon-cyan transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className={index === breadcrumbs.length - 1 ? 'text-white' : ''}>
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

export default Breadcrumbs


