'use client'

import { useState, useEffect, useCallback } from 'react'
import { notificationsApi, Notification } from '@/services/gamificationApi'
import { useAuth } from '@/contexts/AuthContext'

interface UseNotificationsReturn {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  error: string | null
  markAsRead: (ids: string[]) => Promise<void>
  markAllAsRead: () => Promise<void>
  refresh: () => Promise<void>
}

export function useNotifications(): UseNotificationsReturn {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchNotifications = useCallback(async () => {
    if (!user) {
      setNotifications([])
      setUnreadCount(0)
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      const [notifs, countData] = await Promise.all([
        notificationsApi.getNotifications(false, 50),
        notificationsApi.getUnreadCount(),
      ])
      setNotifications(notifs)
      setUnreadCount(countData.unread_count)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
      setError('無法載入通知')
    } finally {
      setIsLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  const markAsRead = useCallback(async (ids: string[]) => {
    try {
      await notificationsApi.markAsRead(ids)
      setNotifications((prev) =>
        prev.map((n) => (ids.includes(n.id) ? { ...n, read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - ids.length))
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsApi.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }, [])

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    markAsRead,
    markAllAsRead,
    refresh: fetchNotifications,
  }
}

