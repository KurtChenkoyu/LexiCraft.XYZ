---
name: Architecture Bible and Restructure (Corrected)
overview: Establish the authoritative Architecture Bible in .cursorrules with CORRECT Next.js routing (parent/ and learner/ without parentheses for URL segments, Traffic Cop at /start to avoid root conflict), then implement the folder restructure.
todos:
  - id: update-cursorrules-bible
    content: Replace lines 41-96 in .cursorrules with corrected Architecture Bible
    status: completed
  - id: create-folder-structure
    content: Create parent/, learner/, (shared)/, and start/ folders inside (app)/
    status: completed
  - id: create-parent-layout
    content: Create parent/layout.tsx wrapping ParentSidebar
    status: completed
  - id: create-dashboard-tabs
    content: Create DashboardTabs component and parent/dashboard/layout.tsx
    status: completed
  - id: create-dashboard-views
    content: Create overview, analytics, finance pages under parent/dashboard/
    status: completed
  - id: move-parent-pages
    content: Move children, goals, achievements, settings to parent/
    status: completed
  - id: create-learner-layout
    content: Create learner/layout.tsx wrapping LearnerBottomNav
    status: completed
  - id: move-learner-pages
    content: Move mine, build, verification, leaderboards, profile to learner/ and create home/
    status: completed
  - id: move-shared-pages
    content: Move onboarding, notifications to (shared)/
    status: completed
  - id: create-traffic-cop
    content: Create start/page.tsx that redirects based on user role
    status: completed
  - id: setup-redirects
    content: Update middleware.ts with 301 redirects and login flow to /start
    status: completed
  - id: update-navigation
    content: Update ParentSidebar, rename BottomNav to LearnerBottomNav, update AppTopNav
    status: completed
  - id: cleanup-verify
    content: Delete old folders, verify no broken links, update CURRENT_STATUS.md
    status: completed
---

# Architecture Bible and Full App Restructure (Corrected)

## Critical Fixes from Previous Plan

1. **Route Groups vs URLs**: Use `parent/` and `learner/` WITHOUT parentheses to get `/parent/*` and `/learner/*` URLs. Parentheses `(name)` are invisible in URLs.

2. **Root Conflict**: Cannot have both `(marketing)/page.tsx` and `(app)/page.tsx` - both resolve to `/`. Solution: Traffic Cop moves to `/start` route.

## Part 1: Update .cursorrules Architecture Bible

Replace lines 41-96 in [.cursorrules](.cursorrules) with:

```markdown
## App Architecture Bible (IMMUTABLE - DO NOT CHANGE)

**This is the authoritative routing and architecture standard. All route changes must follow this structure.**

### 1. Core Philosophy: Role-Based Routing

We strictly separate user contexts using folder structure.
Do NOT mix Parent and Learner logic in the same views.

- **parent/**: Administrative, Financial, and Monitoring views (URL: `/parent/*`)
- **learner/**: Gamified, Learning, and Arcade views (URL: `/learner/*`)
- **(shared)/**: Common views with NO URL prefix (`/onboarding`, `/notifications`)

**IMPORTANT**: Use parentheses `(name)` ONLY when you want the folder invisible in the URL.
- `parent/dashboard` → URL: `/parent/dashboard` (correct)
- `(parent)/dashboard` → URL: `/dashboard` (WRONG - loses parent segment)

### 2. Directory Structure Standard

```

app/[locale]/

├── (marketing)/              # PUBLIC - Landing pages (serves /)

│   ├── page.tsx              # Home/landing page (URL: /)

│   ├── privacy/              # Privacy policy

│   └── survey/               # Public survey

│

├── (auth)/                   # PUBLIC - Auth flow

│   ├── login/

│   └── signup/

│

└── (app)/                    # PROTECTED - Authenticated users only

├── layout.tsx            # AuthGuard + UserDataProvider + SidebarProvider

├── start/                # TRAFFIC COP (URL: /start)

│   └── page.tsx          # Redirects based on role

│

├── parent/               # PARENT WORLD (URL: /parent/*)

│   ├── layout.tsx        # Renders <ParentSidebar>

│   ├── dashboard/        # Main Hub with Tabs

│   │   ├── layout.tsx    # Renders <DashboardTabs>

│   │   ├── page.tsx      # Redirects -> /parent/dashboard/overview

│   │   ├── overview/     # Combined summary

│   │   ├── analytics/    # Learning metrics (deep dive)

│   │   └── finance/      # Wallet & transactions

│   ├── children/         # Manage child accounts

│   ├── goals/            # Goal tracking

│   ├── achievements/     # Achievement gallery

│   └── settings/         # Parent-specific settings

│

├── learner/              # LEARNER WORLD (URL: /learner/*)

│   ├── layout.tsx        # Renders <LearnerBottomNav> + GamificationProvider

│   ├── home/             # The "City" view or Map

│   ├── mine/             # Vocabulary Mining (MCQ)

│   ├── build/            # The Tycoon Game (Room/City Builder)

│   ├── verification/     # Due Reviews / Quiz

│   ├── leaderboards/     # Rankings

│   └── profile/          # Stats, Badges, Avatar

│

└── (shared)/             # SHARED - No URL prefix

├── onboarding/       # URL: /onboarding

└── notifications/    # URL: /notifications

````

### 3. The "Traffic Cop" Pattern

Because `(marketing)/page.tsx` owns the root `/`, we use `/start` as the post-login entry point.

```typescript
// app/[locale]/(app)/start/page.tsx
import { redirect } from 'next/navigation'
import { getUserRole } from '@/lib/auth'

export default async function StartPage() {
  const role = await getUserRole()
  
  if (role === 'parent') redirect('/parent/dashboard')
  if (role === 'learner') redirect('/learner/home')
  redirect('/onboarding') // No role yet
}
````

**Login Flow:**

1. User logs in at `/login`
2. Auth redirects to `/start`
3. Traffic Cop checks role and redirects to appropriate home

### 4. The "Tabbed Page" Pattern

When a page needs sub-views (like Parent Dashboard), use NESTED ROUTES, not state-based tabs.

**Structure:**

- `dashboard/layout.tsx` - Contains the `<DashboardTabs>` component
- `dashboard/page.tsx` - Redirects to default tab
- `dashboard/overview/page.tsx` - First tab content
- `dashboard/analytics/page.tsx` - Second tab content
- `dashboard/finance/page.tsx` - Third tab content

**Rules:**

- URL MUST change when tab changes (`/parent/dashboard/analytics`)
- Root page MUST redirect to default tab
- Tabs are `<Link>` components, NOT onClick state handlers

### 5. Context Providers Hierarchy

| Context | Root Layout | (app) Layout | parent/ Layout | learner/ Layout |

|---------|-------------|--------------|----------------|-----------------|

| `AuthProvider` | YES | NO | NO | NO |

| `UserDataProvider` | NO | YES | NO | NO |

| `SidebarProvider` | NO | YES | NO | NO |

| `GamificationProvider` | NO | NO | NO | YES |

### 6. Navigation Components

| Component | Location | Purpose |

|-----------|----------|---------|

| `ParentSidebar.tsx` | parent/layout.tsx | Desktop sidebar for /parent/* |

| `LearnerBottomNav.tsx` | learner/layout.tsx | Mobile bottom nav for /learner/* |

| `AppTopNav.tsx` | (app)/layout.tsx | Top bar for all authenticated pages |

| `DashboardTabs.tsx` | parent/dashboard/layout.tsx | Tab navigation |

### 7. Navigation Rules

**Hard Boundaries:**

- Parent views should NEVER link directly to Learner views
- Learner views should NEVER link directly to Parent views
- For role switching, redirect through `/start`

**URL Patterns:**

- Parent links: `/parent/*` (e.g., `/parent/dashboard/finance`)
- Learner links: `/learner/*` (e.g., `/learner/mine`)
- Shared links: Direct path (e.g., `/onboarding`, `/notifications`)

### 8. How to Discover Routes

NEVER assume documentation is complete. Always verify:

1. **Check file system**: `ls app/[locale]/(app)/parent/`
2. **Check navigation components**: ParentSidebar, LearnerBottomNav
3. **Search for links**: `grep -r "href=" components/layout/`

```

## Part 2: Implement the Structure

### Phase 1: Create Folder Structure

1. Create `(app)/parent/` folder (NO parentheses)
2. Create `(app)/learner/` folder (NO parentheses)
3. Create `(app)/(shared)/` folder (WITH parentheses - no URL prefix)
4. Create `(app)/start/` folder for Traffic Cop

### Phase 2: Parent Layout and Dashboard Tabs

1. Create `parent/layout.tsx` wrapping ParentSidebar
2. Create `DashboardTabs.tsx` component
3. Create `parent/dashboard/layout.tsx` with tabs
4. Create `parent/dashboard/page.tsx` (redirect to overview)
5. Create `parent/dashboard/overview/page.tsx`
6. Move coach-dashboard to `parent/dashboard/analytics/page.tsx`
7. Move current dashboard to `parent/dashboard/finance/page.tsx`

### Phase 3: Move Parent Pages

1. Move `children/` to `parent/children/`
2. Move `goals/` to `parent/goals/`
3. Move `achievements/` to `parent/achievements/`
4. Move `settings/` to `parent/settings/`

### Phase 4: Learner Layout and Pages

1. Create `learner/layout.tsx` wrapping LearnerBottomNav
2. Create `learner/home/page.tsx` (new learner landing)
3. Move `mine/` to `learner/mine/`
4. Move `build/` to `learner/build/`
5. Move `verification/` to `learner/verification/`
6. Move `leaderboards/` to `learner/leaderboards/`
7. Move `profile/` to `learner/profile/`

### Phase 5: Shared Pages and Traffic Cop

1. Move `onboarding/` to `(shared)/onboarding/`
2. Move `notifications/` to `(shared)/notifications/`
3. Create `start/page.tsx` Traffic Cop

### Phase 6: Redirects and Auth Flow

1. Update middleware.ts with 301 redirects for old URLs
2. **Verify middleware `matcher` config** - ensure `/parent/:path*` and `/learner/:path*` are covered by the matcher pattern (current broad matcher should work, but verify)
3. Update login success redirect to `/start`
4. Test redirect chain works

**Note:** Current middleware uses broad matcher `/((?!_next/static|...).*)`which should automatically include new routes. However, if auth protection is added later via explicit route matching, ensure new paths are included.

### Phase 7: Update Navigation Components

1. Update [ParentSidebar.tsx](landing-page/components/layout/ParentSidebar.tsx) - change hrefs to `/parent/*`
2. Rename BottomNav.tsx to LearnerBottomNav.tsx, update hrefs to `/learner/*`
3. Update [AppTopNav.tsx](landing-page/components/layout/AppTopNav.tsx) - update nav items
4. Remove coach-dashboard from sidebar (now a tab)

### Phase 8: Cleanup

1. Delete old folders (dashboard/, coach-dashboard/, etc.)
2. Verify no broken links
3. Update CURRENT_STATUS.md

## URL Migration Table (Corrected)

| Old URL | New URL | Redirect |

|---------|---------|----------|

| /dashboard | /parent/dashboard | 301 |

| /coach-dashboard | /parent/dashboard/analytics | 301 |

| /children | /parent/children | 301 |

| /deposits | /parent/dashboard/finance | 301 (merged) |

| /goals | /parent/goals | 301 |

| /achievements | /parent/achievements | 301 |

| /settings | /parent/settings | 301 |

| /mine | /learner/mine | 301 |

| /build | /learner/build | 301 |

| /verification | /learner/verification | 301 |

| /leaderboards | /learner/leaderboards | 301 |

| /profile | /learner/profile | 301 |

| /onboarding | /onboarding | No change |

| /notifications | /notifications | No change |

## Success Criteria

- [ ] .cursorrules contains corrected Architecture Bible
- [ ] `parent/` folder exists (NOT `(parent)/`) with correct URLs
- [ ] `learner/` folder exists (NOT `(learner)/`) with correct URLs
- [ ] Dashboard tabs work at `/parent/dashboard/*`
- [ ] Traffic Cop at `/start` redirects correctly
- [ ] Old URLs redirect to new locations
- [ ] No Next.js build errors
- [ ] No console errors or broken links