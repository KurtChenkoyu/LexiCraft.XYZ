'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Link } from '@/i18n/routing'
import { notificationsApi, Notification } from '@/services/gamificationApi'

const notificationTypeConfig: Record<string, { icon: string; color: string; bgColor: string }> = {
  achievement: { icon: '🏆', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10' },
  streak_risk: { icon: '🔥', color: 'text-orange-400', bgColor: 'bg-orange-500/10' },
  goal_progress: { icon: '🎯', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10' },
  milestone: { icon: '⭐', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  level_up: { icon: '🎉', color: 'text-green-400', bgColor: 'bg-green-500/10' },
}

export default function NotificationsPage() {
  const { user } = useAuth()

  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  // Fetch notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      if (!user) return

      try {
        setIsLoading(true)
        const data = await notificationsApi.getNotifications(filter === 'unread', 100)
        setNotifications(data)
      } catch (err) {
        console.error('Failed to fetch notifications:', err)
      } finally {
        setIsLoading(false)
      }
    }

    if (user) {
      fetchNotifications()
    }
  }, [user, filter])

  // Mark as read
  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationsApi.markAsRead([notificationId])
      setNotifications(
        notifications.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      )
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }

  // Mark all as read
  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead()
      setNotifications(notifications.map((n) => ({ ...n, read: true })))
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white/80 text-lg">載入中...</p>
        </div>
      </main>
    )
  }

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 pt-20 pb-20">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              🔔 通知中心
            </h1>
            <p className="text-white/60 mt-1">
              {unreadCount > 0 ? `${unreadCount} 則未讀通知` : '沒有未讀通知'}
            </p>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm transition-colors"
            >
              全部已讀
            </button>
          )}
        </div>

        {/* Filter */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              filter === 'all' ? 'bg-white text-slate-900' : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            全部
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              filter === 'unread' ? 'bg-white text-slate-900' : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            未讀 ({unreadCount})
          </button>
        </div>

        {/* Notifications List */}
        {notifications.length === 0 ? (
          <div className="bg-white/5 rounded-2xl p-12 text-center border border-white/10">
            <div className="text-6xl mb-4">🔔</div>
            <p className="text-white/60 text-lg">
              {filter === 'unread' ? '沒有未讀通知' : '暫無通知'}
            </p>
            <Link
              href="/learner/verification"
              className="inline-block mt-4 text-cyan-400 hover:text-cyan-300"
            >
              開始學習獲得通知 →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((notification) => (
              <NotificationCard
                key={notification.id}
                notification={notification}
                onMarkAsRead={handleMarkAsRead}
              />
            ))}
          </div>
        )}

        {/* Back Link */}
        <div className="text-center mt-8">
          <Link href="/parent/dashboard" className="text-white/60 hover:text-white transition-colors">
            ← 返回儀表板
          </Link>
        </div>
      </div>
    </main>
  )
}

// Notification Card Component
function NotificationCard({
  notification,
  onMarkAsRead,
}: {
  notification: Notification
  onMarkAsRead: (id: string) => void
}) {
  const config = notificationTypeConfig[notification.type] || {
    icon: '📌',
    color: 'text-gray-400',
    bgColor: 'bg-gray-500/10',
  }

  return (
    <div
      className={`rounded-xl p-5 border transition-all cursor-pointer ${
        !notification.read
          ? 'bg-white/10 border-white/20 hover:bg-white/15'
          : 'bg-white/5 border-white/10 hover:bg-white/10 opacity-70'
      }`}
      onClick={() => !notification.read && onMarkAsRead(notification.id)}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`w-12 h-12 rounded-full ${config.bgColor} flex items-center justify-center`}>
          <span className="text-2xl">{config.icon}</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className={`font-semibold ${!notification.read ? 'text-white' : 'text-white/80'}`}>
              {notification.title_zh || notification.title_en}
            </h3>
            {!notification.read && <div className="w-2 h-2 rounded-full bg-cyan-500 mt-2 flex-shrink-0"></div>}
          </div>

          {(notification.message_zh || notification.message_en) && (
            <p className="text-white/60 mt-1">
              {notification.message_zh || notification.message_en}
            </p>
          )}

          <p className="text-white/40 text-sm mt-2">{formatTimeAgo(notification.created_at)}</p>
        </div>
      </div>
    </div>
  )
}

// Helper function to format time ago
function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return '剛剛'
  if (diffMins < 60) return `${diffMins} 分鐘前`
  if (diffHours < 24) return `${diffHours} 小時前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString()
}


