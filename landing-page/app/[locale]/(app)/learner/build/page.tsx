'use client'

/**
 * Build Page - Collection Showcase
 * 
 * For Emoji MVP: Shows EmojiCollectionShowcase (trophy room for mastered words)
 * For Legacy: Shows room builder (coming soon)
 * 
 * ⚡ ARCHITECTURE PRINCIPLE: "As Snappy as Last War"
 * - UI renders INSTANTLY using Zustand data
 * - No loading spinners blocking content
 */

import { useAppStore, selectActivePack } from '@/stores/useAppStore'
import { EmojiCollectionShowcase } from '@/components/features/emoji/EmojiCollectionShowcase'

export default function BuildPage() {
  // ⚡ Read active pack from Zustand (instant, pre-loaded by Bootstrap!)
  const activePack = useAppStore(selectActivePack)
  
  // Emoji Mode: Show collection showcase
  const isEmojiPack = activePack?.id === 'emoji_core'
  
  if (isEmojiPack) {
    return (
      <div className="min-h-[calc(100vh-4rem)] lg:min-h-[calc(100vh-5rem)] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <EmojiCollectionShowcase />
        </div>
      </div>
    )
  }
  
  // Legacy Mode: Placeholder for room builder
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] p-4 text-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-md mx-auto space-y-6">
        <div className="text-6xl mb-4">🏗️</div>
        <h1 className="text-4xl font-bold text-white mb-4">建造模式</h1>
        <p className="text-gray-400 text-lg mb-8">
          此功能正在開發中，敬請期待！
          <br />
          <span className="text-sm text-gray-500">(Under Construction)</span>
        </p>
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <p className="text-slate-300 text-sm">
            建造功能即將推出。你將能夠使用資源建造和升級你的學習空間。
          </p>
        </div>
      </div>
    </div>
  )
}
