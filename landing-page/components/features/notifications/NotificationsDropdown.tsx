'use client'

import { useEffect, useState, useRef } from 'react'
import { Link } from '@/i18n/routing'
import { useAuth } from '@/contexts/AuthContext'
import { notificationsApi, Notification } from '@/services/gamificationApi'

const notificationTypeConfig: Record<string, { icon: string; color: string }> = {
  achievement: { icon: '🏆', color: 'text-yellow-400' },
  streak_risk: { icon: '🔥', color: 'text-orange-400' },
  goal_progress: { icon: '🎯', color: 'text-cyan-400' },
  milestone: { icon: '⭐', color: 'text-purple-400' },
  level_up: { icon: '🎉', color: 'text-green-400' },
}

export function NotificationsDropdown() {
  const { user } = useAuth()
  const userId = user?.id
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch unread count on mount and poll
  useEffect(() => {
    if (!userId) return

    const fetchUnreadCount = async () => {
      try {
        const data = await notificationsApi.getUnreadCount()
        setUnreadCount(data.unread_count)
      } catch (err) {
        console.error('Failed to fetch unread count:', err)
      }
    }

    fetchUnreadCount()
    // Poll every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [userId])

  // Fetch notifications when dropdown opens
  useEffect(() => {
    const fetchNotifications = async () => {
      if (!isOpen || !userId) return
      try {
        setIsLoading(true)
        const data = await notificationsApi.getNotifications(false, 10)
        setNotifications(data)
      } catch (err) {
        console.error('Failed to fetch notifications:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchNotifications()
  }, [isOpen, userId])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Mark notification as read
  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationsApi.markAsRead([notificationId])
      setNotifications(
        notifications.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      )
      setUnreadCount(Math.max(0, unreadCount - 1))
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }

  // Mark all as read
  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead()
      setNotifications(notifications.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }

  if (!user) return null

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
        aria-label="Notifications"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">通知</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-sm text-cyan-600 hover:text-cyan-700"
              >
                全部已讀
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent mx-auto"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <div className="text-4xl mb-2">🔔</div>
                <p className="text-gray-500">暫無通知</p>
              </div>
            ) : (
              <div>
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={handleMarkAsRead}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <Link
            href="/notifications"
            className="block px-4 py-3 text-center text-sm text-cyan-600 hover:bg-gray-50 border-t border-gray-200"
            onClick={() => setIsOpen(false)}
          >
            查看全部通知 →
          </Link>
        </div>
      )}
    </div>
  )
}

// Notification Item Component
function NotificationItem({
  notification,
  onMarkAsRead,
}: {
  notification: Notification
  onMarkAsRead: (id: string) => void
}) {
  const config = notificationTypeConfig[notification.type] || { icon: '📌', color: 'text-gray-400' }

  return (
    <div
      className={`px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer ${
        !notification.read ? 'bg-cyan-50/50' : ''
      }`}
      onClick={() => !notification.read && onMarkAsRead(notification.id)}
    >
      <div className="flex items-start gap-3">
        <span className={`text-2xl ${config.color}`}>{config.icon}</span>
        <div className="flex-1 min-w-0">
          <p className={`font-medium text-sm ${!notification.read ? 'text-gray-900' : 'text-gray-700'}`}>
            {notification.title_zh || notification.title_en}
          </p>
          {(notification.message_zh || notification.message_en) && (
            <p className="text-gray-500 text-sm mt-0.5 line-clamp-2">
              {notification.message_zh || notification.message_en}
            </p>
          )}
          <p className="text-gray-400 text-xs mt-1">
            {formatTimeAgo(notification.created_at)}
          </p>
        </div>
        {!notification.read && (
          <div className="w-2 h-2 rounded-full bg-cyan-500 mt-2"></div>
        )}
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


