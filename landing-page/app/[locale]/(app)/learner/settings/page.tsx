'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAppStore, selectLearnerProfile } from '@/stores/useAppStore'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'

export default function LearnerSettingsPage() {
  const router = useRouter()
  const { user, signOut } = useAuth()
  const learnerProfile = useAppStore(selectLearnerProfile)
  
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [musicEnabled, setMusicEnabled] = useState(true)
  const [hapticEnabled, setHapticEnabled] = useState(true)

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">⚙️ Settings</h1>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
          >
            Back
          </button>
        </div>

        {/* Profile Section */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-4">
          <h2 className="text-lg font-bold text-cyan-400 mb-4">👤 Profile</h2>
          <div className="space-y-3">
            <div>
              <span className="text-slate-400 text-sm">Email:</span>
              <p className="text-white font-semibold">{user?.email || 'Guest'}</p>
            </div>
            <div>
              <span className="text-slate-400 text-sm">Level:</span>
              <p className="text-white font-semibold">Level {learnerProfile?.level.level || 1}</p>
            </div>
            <div>
              <span className="text-slate-400 text-sm">Current Streak:</span>
              <p className="text-white font-semibold">⚡ {learnerProfile?.current_streak || 0} days</p>
            </div>
          </div>
        </div>

        {/* Audio Settings */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-4">
          <h2 className="text-lg font-bold text-cyan-400 mb-4">🔊 Audio</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-white">Sound Effects</span>
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  soundEnabled ? 'bg-cyan-500' : 'bg-slate-600'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                    soundEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white">Background Music</span>
              <button
                onClick={() => setMusicEnabled(!musicEnabled)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  musicEnabled ? 'bg-cyan-500' : 'bg-slate-600'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                    musicEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Haptic Feedback */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-4">
          <h2 className="text-lg font-bold text-cyan-400 mb-4">📳 Haptic Feedback</h2>
          <div className="flex items-center justify-between">
            <span className="text-white">Vibration on Interactions</span>
            <button
              onClick={() => setHapticEnabled(!hapticEnabled)}
              className={`w-12 h-6 rounded-full transition-colors ${
                hapticEnabled ? 'bg-cyan-500' : 'bg-slate-600'
              }`}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                  hapticEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Cache Management */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-4">
          <h2 className="text-lg font-bold text-cyan-400 mb-4">🗂️ Data</h2>
          <div className="space-y-3">
            <button
              onClick={async () => {
                if (confirm('Clear vocabulary cache? This will re-download ~80MB of enriched data.')) {
                  try {
                    const dbs = await indexedDB.databases()
                    console.log('Found databases:', dbs.map(db => db.name))
                    
                    // Delete each database with proper async handling
                    const deletions = dbs
                      .filter(db => db.name && !db.name.includes('supabase'))
                      .map(db => {
                        return new Promise<void>((resolve, reject) => {
                          if (!db.name) return resolve()
                          console.log(`Deleting ${db.name}...`)
                          const request = indexedDB.deleteDatabase(db.name)
                          request.onsuccess = () => {
                            console.log(`✅ Deleted ${db.name}`)
                            resolve()
                          }
                          request.onerror = () => {
                            console.error(`❌ Failed to delete ${db.name}`)
                            reject(request.error)
                          }
                          request.onblocked = () => {
                            console.warn(`⚠️ ${db.name} deletion blocked - close all tabs using this DB`)
                            resolve() // Don't block the reload
                          }
                        })
                      })
                    
                    // Wait for all deletions to complete
                    await Promise.all(deletions)
                    console.log('✅ All databases cleared!')
                    
                    alert('Cache cleared! Reloading...')
                    window.location.reload()
                  } catch (err) {
                    console.error('Cache clear error:', err)
                    alert('Cache clear may have failed. Try closing other tabs and retry.')
                  }
                }
              }}
              className="w-full px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-500 transition-colors"
            >
              🗑️ Clear Vocabulary Cache
            </button>
            <p className="text-xs text-slate-500">
              Use this if you see old vocabulary data or experience loading issues. (Preserves login)
            </p>
          </div>
        </div>

        {/* Account */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-4">
          <h2 className="text-lg font-bold text-cyan-400 mb-4">👤 Account</h2>
          {user ? (
            <div className="space-y-3">
              <div>
                <span className="text-slate-400 text-sm">Email:</span>
                <p className="text-white font-semibold">{user.email}</p>
              </div>
              <button
                onClick={async () => {
                  if (confirm('Sign out?')) {
                    await signOut()
                    router.push('/login')
                  }
                }}
                className="w-full px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors"
              >
                🚪 Sign Out
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-slate-400 text-sm">You are not signed in</p>
              <Link
                href="/login"
                className="block w-full px-4 py-3 bg-cyan-600 text-white text-center rounded-lg hover:bg-cyan-500 transition-colors"
              >
                🔐 Sign In
              </Link>
            </div>
          )}
        </div>

        {/* About */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h2 className="text-lg font-bold text-cyan-400 mb-4">ℹ️ About</h2>
          <div className="space-y-2 text-sm text-slate-400">
            <p>LexiCraft.xyz v1.0</p>
            <p>Vocabulary Database: 10,470 senses</p>
            <p>Enriched with Gemini ESL data (v5.0-gemini)</p>
          </div>
        </div>
      </div>
    </div>
  )
}

