'use client'

import { FamilyLeaderboard } from '@/components/features/emoji/FamilyLeaderboard'

/**
 * Family Page - The "Home Base" for the family unit.
 * 
 * Currently displays the Family Leaderboard to encourage friendly competition.
 * Future Scope: Parent management links, detailed child stats, network/school groups.
 */
export default function FamilyPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 pt-20 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <FamilyLeaderboard />
      </div>
    </main>
  )
}

