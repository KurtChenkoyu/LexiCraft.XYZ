# Frontend Reorganization Plan

## Overview

This document outlines the **technical implementation** for reorganizing the LexiCraft frontend codebase.

**For UX/product vision, see:** [docs/30-ux-vision-game-design.md](../../docs/30-ux-vision-game-design.md)

**Estimated Total Time:** 12-15 hours  
**Recommended Approach:** Do it phase by phase, test after each phase

---

## Status (December 2024)

✅ **Phase 1-3 Completed** - Route groups, shared auth layout, component organization  
⏳ **Phase 4-5 Pending** - Page logic extraction, types/hooks consolidation

---

## Phase 1: Quick Wins (1 hour)

### Task 1.1: Move Markdown Docs to docs/

**Current State:** 10+ markdown files cluttering the root directory

**Files to Move:**
```
DEPLOY_NOW.md
DEPLOY_QUICK.md
DEPLOY_TO_VERCEL.md
DEPLOYMENT.md
GET_LIVE.md
IMPLEMENTATION_SUMMARY.md
MULTI_LANGUAGE_SETUP.md
QUICK_START.md
TROUBLESHOOTING.md
UPDATE_SUMMARY.md
```

**Action:**
```bash
mkdir -p docs
mv DEPLOY*.md docs/
mv GET_LIVE.md docs/
mv IMPLEMENTATION_SUMMARY.md docs/
mv MULTI_LANGUAGE_SETUP.md docs/
mv QUICK_START.md docs/
mv TROUBLESHOOTING.md docs/
mv UPDATE_SUMMARY.md docs/
```

### Task 1.2: Create Route Groups

**Current State:** All routes flat under `app/[locale]/`

**Target Structure:**
```
app/[locale]/
├── (marketing)/          # No auth required
│   ├── page.tsx          # Landing page (move from current page.tsx)
│   ├── privacy/
│   └── layout.tsx
│
├── (auth)/               # Auth flow pages
│   ├── login/
│   ├── signup/
│   └── layout.tsx
│
├── (app)/                # Auth required
│   ├── dashboard/
│   ├── verification/
│   ├── profile/
│   ├── goals/
│   ├── leaderboards/
│   ├── settings/
│   ├── coach-dashboard/
│   ├── notifications/
│   ├── survey/
│   ├── onboarding/
│   └── layout.tsx        # Shared auth check here!
│
└── layout.tsx            # Root layout (unchanged)
```

**Important:** Route groups with `()` don't affect the URL path. `/dashboard` still works.

---

## Phase 2: Shared Auth Layout (2 hours)

### Task 2.1: Create (app)/layout.tsx

This eliminates duplicate auth checks across 12 pages.

**Create:** `app/[locale]/(app)/layout.tsx`

```tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { checkOnboardingStatus } from '@/lib/onboarding'
import Navbar from '@/components/layout/Navbar'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (!loading && !user) {
      const locale = window.location.pathname.split('/')[1] || 'zh-TW'
      router.push(`/${locale}/login`)
    }
  }, [user, loading, router])

  // Optional: Check onboarding for specific routes
  useEffect(() => {
    const checkOnboarding = async () => {
      if (!loading && user) {
        const status = await checkOnboardingStatus(user.id)
        if (status && !status.completed) {
          const locale = window.location.pathname.split('/')[1] || 'zh-TW'
          // Don't redirect if already on onboarding
          if (!window.location.pathname.includes('/onboarding')) {
            router.push(`/${locale}/onboarding`)
          }
        }
      }
    }
    checkOnboarding()
  }, [user, loading, router])

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-600"></div>
      </main>
    )
  }

  if (!user) {
    return null // Will redirect
  }

  return (
    <>
      <Navbar />
      {children}
    </>
  )
}
```

### Task 2.2: Simplify All App Pages

**Before (each page had this):**
```tsx
export default function DashboardPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      const currentLocale = window.location.pathname.split('/')[1] || 'zh-TW'
      router.push(`/${currentLocale}/login`)
    }
  }, [user, authLoading, router])

  // Check onboarding status
  useEffect(() => {
    // ... 15 more lines
  }, [user, authLoading, router])

  if (authLoading) {
    return <LoadingSpinner />
  }

  if (!user) {
    return null
  }

  // Actual page content...
}
```

**After:**
```tsx
export default function DashboardPage() {
  // Auth already handled by layout!
  // Just render the content
  return (
    <main>
      {/* Page content */}
    </main>
  )
}
```

**Pages to Update:**
- [ ] dashboard/page.tsx
- [ ] verification/page.tsx
- [ ] profile/page.tsx
- [ ] goals/page.tsx
- [ ] leaderboards/page.tsx
- [ ] settings/page.tsx
- [ ] coach-dashboard/page.tsx
- [ ] notifications/page.tsx
- [ ] survey/page.tsx
- [ ] onboarding/page.tsx (special case - may need own logic)

---

## Phase 3: Component Organization (3 hours)

### Task 3.1: Create components/ui/

Generic, reusable UI primitives with consistent styling.

```
components/ui/
├── Button.tsx
├── Card.tsx
├── Input.tsx
├── Select.tsx
├── Modal.tsx
├── Badge.tsx
├── Spinner.tsx
└── index.ts
```

**Example Button.tsx:**
```tsx
import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'font-semibold rounded-lg transition-all',
          {
            'bg-cyan-600 hover:bg-cyan-500 text-white': variant === 'primary',
            'bg-gray-100 hover:bg-gray-200 text-gray-700': variant === 'secondary',
            'bg-transparent hover:bg-gray-100': variant === 'ghost',
            'bg-red-600 hover:bg-red-500 text-white': variant === 'danger',
          },
          {
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2': size === 'md',
            'px-6 py-3 text-lg': size === 'lg',
          },
          className
        )}
        {...props}
      />
    )
  }
)
```

### Task 3.2: Create components/layout/

```
components/layout/
├── Navbar.tsx           # Move from components/
├── Footer.tsx           # Move from components/
├── AppShell.tsx         # Main app wrapper
├── Sidebar.tsx          # If needed
└── index.ts
```

### Task 3.3: Create components/marketing/

Landing page components only:

```
components/marketing/
├── Hero.tsx
├── FAQ.tsx
├── Pricing.tsx
├── BenefitsKids.tsx
├── BenefitsParents.tsx
├── HowItWorks.tsx
├── ParentQuestions.tsx
├── VocabularyCliff.tsx
├── WaitlistForm.tsx
├── WordCloud.tsx
└── index.ts
```

### Task 3.4: Reorganize components/features/

Group by feature domain:

```
components/features/
├── auth/
│   ├── LoginForm.tsx
│   ├── SignupForm.tsx
│   └── EmailConfirmationBanner.tsx
│
├── dashboard/
│   ├── ChildrenOverview.tsx      # Extract from dashboard page
│   ├── BalanceCard.tsx           # Extract from dashboard page
│   ├── QuickActions.tsx          # Extract from dashboard page
│   └── VerificationCard.tsx      # Extract from dashboard page
│
├── deposit/
│   ├── DepositForm.tsx
│   └── DepositButton.tsx
│
├── gamification/
│   ├── GamificationWidget.tsx
│   ├── GamificationWidgetCompact.tsx
│   ├── AchievementCard.tsx
│   └── StreakIndicator.tsx
│
├── mcq/
│   ├── MCQCard.tsx
│   ├── MCQSession.tsx
│   └── index.ts
│
├── survey/
│   ├── SurveyEngine.tsx
│   ├── SurveyProgress.tsx
│   ├── MultiSelectMatrix.tsx
│   ├── PreSurveyCalibration.tsx
│   ├── ResultDashboard.tsx
│   └── index.ts
│
└── notifications/
    ├── NotificationsDropdown.tsx
    └── NotificationCard.tsx
```

---

## Phase 4: Extract Page Logic (4+ hours)

### Task 4.1: Break Down DashboardPage

**Current:** 380 lines in one file

**Target:** ~50 lines in page, logic in components

**Extract these components:**
1. `ChildrenOverview.tsx` - Grid of children cards
2. `BalanceCard.tsx` - Balance display with gradient
3. `QuickActions.tsx` - Button list for actions
4. `DepositSection.tsx` - Child selector + deposit form
5. `VerificationCard.tsx` - "開始複習" card

**New dashboard/page.tsx:**
```tsx
import { ChildrenOverview } from '@/components/features/dashboard/ChildrenOverview'
import { VerificationCard } from '@/components/features/dashboard/VerificationCard'
import { DepositSection } from '@/components/features/dashboard/DepositSection'
import { QuickActions } from '@/components/features/dashboard/QuickActions'
import { GamificationWidget } from '@/components/features/gamification'
import { BalanceCard } from '@/components/features/dashboard/BalanceCard'

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pt-20 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <DashboardHeader />
        <ChildrenOverview />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <VerificationCard />
          <DepositSection />
          <aside className="space-y-6">
            <GamificationWidget />
            <QuickActions />
          </aside>
        </div>
        
        <BalanceCard />
      </div>
    </main>
  )
}
```

### Task 4.2: Break Down ProfilePage

Extract:
1. `ProfileHeader.tsx` - Avatar, level, XP bar
2. `AchievementsGrid.tsx` - Achievement cards
3. `StreakDisplay.tsx` - Streak info

### Task 4.3: Other Pages to Simplify

- `SettingsPage` - Extract form sections
- `LeaderboardsPage` - Extract leaderboard table
- `GoalsPage` - Extract goal cards
- `VerificationPage` - Extract due cards list

---

## Phase 5: Types & Hooks (2 hours)

### Task 5.1: Create types/ Directory

```
types/
├── api.ts          # API response wrappers
├── user.ts         # User, Child, Parent types
├── mcq.ts          # MCQ related types
├── survey.ts       # Survey types
├── gamification.ts # Achievements, XP, levels
└── index.ts        # Re-exports
```

**Example types/user.ts:**
```tsx
export interface User {
  id: string
  email: string
  created_at: string
}

export interface Child {
  id: string
  name: string | null
  age: number | null
  parent_id: string
}

export interface Balance {
  available_points: number
  locked_points: number
}
```

### Task 5.2: Create hooks/ Directory

```
hooks/
├── useAuth.ts           # Wrapper around AuthContext
├── useUserData.ts       # Wrapper around UserDataContext  
├── useMCQ.ts            # MCQ loading/submission logic
├── useGamification.ts   # Dashboard data fetching
├── useOnboarding.ts     # Onboarding status check
└── index.ts
```

**Example useGamification.ts:**
```tsx
import { useState, useEffect } from 'react'
import { dashboardApi, DashboardResponse } from '@/services/gamification'
import { useAuth } from './useAuth'

export function useGamification() {
  const { user } = useAuth()
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!user) return

    const fetchData = async () => {
      try {
        setIsLoading(true)
        const result = await dashboardApi.getDashboard()
        setData(result)
      } catch (err) {
        setError(err as Error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [user])

  return { data, isLoading, error }
}
```

### Task 5.3: Move messages/ into i18n/

```
i18n/
├── messages/
│   ├── en.json
│   └── zh-TW.json
├── request.ts
└── routing.ts
```

Update imports in `next.config.js` or wherever messages are loaded.

---

## Testing Checklist

After each phase, verify:

- [ ] `npm run dev` starts without errors
- [ ] Landing page loads at `/`
- [ ] Login/signup flows work
- [ ] Dashboard loads when logged in
- [ ] MCQ verification flow works
- [ ] All links navigate correctly
- [ ] i18n switching works

---

## Import Path Updates

When moving files, update imports. Consider using path aliases in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"],
      "@/components/*": ["./components/*"],
      "@/features/*": ["./components/features/*"],
      "@/ui/*": ["./components/ui/*"],
      "@/hooks/*": ["./hooks/*"],
      "@/types/*": ["./types/*"],
      "@/services/*": ["./services/*"],
      "@/lib/*": ["./lib/*"]
    }
  }
}
```

---

## Notes

- **Don't do everything at once** - Complete one phase, test, commit, then move to next
- **Git commits** - Commit after each task for easy rollback
- **IDE search** - Use "Find all references" before moving files
- **Keep old files temporarily** - Re-export from old location during transition

