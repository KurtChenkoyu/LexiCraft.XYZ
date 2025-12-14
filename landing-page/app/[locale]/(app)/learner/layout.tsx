'use client'

import { BottomNav } from '@/components/layout/BottomNav'
import { LearnerTopBar } from '@/components/layout/LearnerTopBar'

/**
 * Learner Layout - The "Game Frame"
 * 
 * ARCHITECTURE PRINCIPLE: "As Snappy as Last War"
 * See: .cursorrules - "UI/UX & Game Feel Standards"
 * 
 * This layout enforces the Game Viewport Law:
 * - Fixed viewport (h-[100dvh], no scrolling on body)
 * - Z-Index layering (HUD above World)
 * - HUD never unmounts (persistent navigation)
 * 
 * URL: /learner/*
 * 
 * Layers:
 * - z-0: World/Map (children content)
 * - z-10: Full-screen activities (Mine, Workshop)
 * - z-40: HUD (Top Bar + Bottom Nav)
 * 
 * @see .cursorrules - "The Game Viewport Law"
 * @see .cursorrules - App Architecture Bible, Section 2
 */
export default function LearnerLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="game-container flex flex-col">
      {/* Top HUD Bar (z-40) - Persistent across navigation */}
      <div className="z-hud absolute top-0 left-0 right-0 pt-safe">
        <LearnerTopBar />
      </div>

      {/* World Layer (z-0) - Scrollable content area */}
      <main className="z-world flex-1 overflow-y-auto scrollable pt-16 pb-20 px-4">
        {children}
      </main>

      {/* Bottom HUD Nav (z-40) - Persistent across navigation */}
      <div className="z-hud absolute bottom-0 left-0 right-0 pb-safe">
        <BottomNav />
      </div>
    </div>
  )
}

