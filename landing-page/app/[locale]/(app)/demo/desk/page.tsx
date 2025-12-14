'use client'

import { StudyDeskDemo } from '@/components/features/building'

export default function DeskDemoPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-zinc-900 pt-24 pb-20 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            🏠 One Room MVP
          </h1>
          <p className="text-gray-400">
            Testing the Minecraft model: Does leveling up the desk feel rewarding?
          </p>
        </div>

        <StudyDeskDemo />

        <div className="mt-8 bg-white/5 rounded-xl p-6 border border-white/10">
          <h2 className="text-white font-semibold mb-3">🧪 Test Questions</h2>
          <ul className="text-gray-400 text-sm space-y-2">
            <li>• Do you feel excited clicking "+5 Words"?</li>
            <li>• Do you anticipate the next level?</li>
            <li>• Does the level-up animation feel rewarding?</li>
            <li>• Would you grind 100 words to get the Hover Desk?</li>
          </ul>
          
          <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
            <p className="text-yellow-400 text-sm">
              <strong>Success metric:</strong> If users ask "How do I upgrade my desk?" 
              instead of "Where is my money?", we have a winner.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}

