'use client'

import { useState, useEffect, useCallback } from 'react'
import { goalsApi, Goal, GoalSuggestion, CreateGoalRequest } from '@/services/gamificationApi'
import { useAuth } from '@/contexts/AuthContext'

interface UseGoalsReturn {
  goals: Goal[]
  suggestions: GoalSuggestion[]
  isLoading: boolean
  error: string | null
  createGoal: (goal: CreateGoalRequest) => Promise<Goal | null>
  updateGoal: (goalId: string, goal: CreateGoalRequest) => Promise<Goal | null>
  deleteGoal: (goalId: string) => Promise<boolean>
  completeGoal: (goalId: string) => Promise<Goal | null>
  refresh: () => Promise<void>
}

export function useGoals(): UseGoalsReturn {
  const { user } = useAuth()
  const [goals, setGoals] = useState<Goal[]>([])
  const [suggestions, setSuggestions] = useState<GoalSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchGoals = useCallback(async () => {
    if (!user) {
      setGoals([])
      setSuggestions([])
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      const [goalsData, suggestionsData] = await Promise.all([
        goalsApi.getGoals(),
        goalsApi.getSuggestions(),
      ])

      setGoals(goalsData)
      setSuggestions(suggestionsData)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch goals:', err)
      setError('無法載入目標')
    } finally {
      setIsLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchGoals()
  }, [fetchGoals])

  const createGoal = useCallback(async (goal: CreateGoalRequest): Promise<Goal | null> => {
    try {
      const newGoal = await goalsApi.createGoal(goal)
      setGoals((prev) => [...prev, newGoal])
      return newGoal
    } catch (err) {
      console.error('Failed to create goal:', err)
      setError('無法建立目標')
      return null
    }
  }, [])

  const updateGoal = useCallback(async (goalId: string, goal: CreateGoalRequest): Promise<Goal | null> => {
    try {
      const updatedGoal = await goalsApi.updateGoal(goalId, goal)
      setGoals((prev) => prev.map((g) => (g.id === goalId ? updatedGoal : g)))
      return updatedGoal
    } catch (err) {
      console.error('Failed to update goal:', err)
      setError('無法更新目標')
      return null
    }
  }, [])

  const deleteGoal = useCallback(async (goalId: string): Promise<boolean> => {
    try {
      await goalsApi.deleteGoal(goalId)
      setGoals((prev) => prev.filter((g) => g.id !== goalId))
      return true
    } catch (err) {
      console.error('Failed to delete goal:', err)
      setError('無法刪除目標')
      return false
    }
  }, [])

  const completeGoal = useCallback(async (goalId: string): Promise<Goal | null> => {
    try {
      const completedGoal = await goalsApi.completeGoal(goalId)
      setGoals((prev) => prev.map((g) => (g.id === goalId ? completedGoal : g)))
      return completedGoal
    } catch (err) {
      console.error('Failed to complete goal:', err)
      setError('無法完成目標')
      return null
    }
  }, [])

  return {
    goals,
    suggestions,
    isLoading,
    error,
    createGoal,
    updateGoal,
    deleteGoal,
    completeGoal,
    refresh: fetchGoals,
  }
}

