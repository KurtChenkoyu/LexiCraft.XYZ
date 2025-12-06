'use client'

interface LevelInfo {
  level: number
  total_xp: number
  xp_in_current_level: number
  xp_to_next_level: number
  progress_percentage: number
}

interface LevelBadgeProps {
  levelInfo: LevelInfo | null
}

export function LevelBadge({ levelInfo }: LevelBadgeProps) {
  const level = levelInfo?.level || 1
  const currentXP = levelInfo?.xp_in_current_level || 0
  const nextLevelXP = levelInfo?.xp_to_next_level || 100
  const totalXP = levelInfo?.total_xp || 0
  const progress = levelInfo?.progress_percentage || 0

  return (
    <div className="text-center mb-12">
      {/* Level Badge */}
      <div className="inline-flex flex-col items-center mb-6">
        <div className="relative">
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-yellow-400 via-orange-500 to-red-500 p-1 shadow-2xl shadow-orange-500/30">
            <div className="w-full h-full rounded-full bg-indigo-900 flex items-center justify-center">
              <span className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-yellow-400 to-orange-500">
                {level}
              </span>
            </div>
          </div>
          {/* Glow effect */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-yellow-400 via-orange-500 to-red-500 opacity-30 blur-xl -z-10"></div>
        </div>
        <h1 className="mt-4 text-3xl sm:text-4xl font-bold text-white">
          Level {level}
        </h1>
      </div>

      {/* XP Progress Bar */}
      <div className="max-w-md mx-auto">
        <div className="flex justify-between text-sm text-white/60 mb-2">
          <span>{currentXP} XP</span>
          <span>{nextLevelXP} XP</span>
        </div>
        <div className="h-4 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
          <div
            className="h-full bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="mt-2 text-white/80">
          總經驗值：<span className="font-bold text-yellow-400">{totalXP}</span> XP
        </p>
      </div>
    </div>
  )
}

