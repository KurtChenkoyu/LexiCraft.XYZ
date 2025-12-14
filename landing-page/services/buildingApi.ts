/**
 * Building API Service
 * 
 * Handles currencies and item upgrades for the building system.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Auth token management - set by components that have access to auth context
let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
}

export function getAuthToken(): string | null {
  return authToken
}

// --- Types ---

export interface Currencies {
  sparks: number
  essence: number
  energy: number
  blocks: number
  level: number
  total_xp: number
  xp_to_next_level: number
  xp_in_current_level: number
  level_progress: number
}

export interface ItemBlueprint {
  id: string
  code: string
  name_en: string
  name_zh: string | null
  room: string
  max_level: number
  emoji_levels: string[]
  is_starter: boolean
  display_order: number
}

export interface UpgradeCost {
  energy: number
  essence: number
  blocks: number
}

export interface UserItem {
  blueprint: ItemBlueprint
  current_level: number
  current_emoji: string
  next_level: number | null
  next_emoji: string | null
  upgrade_cost: UpgradeCost | null
  can_upgrade: boolean
  upgraded_at: string | null
}

export interface RoomData {
  room: string
  room_name_en: string
  room_name_zh: string
  items: UserItem[]
}

export interface UpgradeResponse {
  success: boolean
  error: string | null
  item_code: string
  old_level: number
  new_level: number
  new_emoji: string
  energy_spent: number
  essence_spent: number
  blocks_spent: number
  currencies_after: {
    energy: number
    essence: number
    blocks: number
  }
}

// --- API Functions ---

/**
 * Get all currency balances for the current user.
 */
export async function getCurrencies(): Promise<Currencies> {
  const token = getAuthToken()
  
  const response = await fetch(`${API_BASE}/api/v1/currencies`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get currencies: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get all rooms with items and user progress.
 */
export async function getRooms(): Promise<RoomData[]> {
  const token = getAuthToken()
  
  const response = await fetch(`${API_BASE}/api/v1/items/rooms`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get rooms: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Upgrade an item to the next level.
 */
export async function upgradeItem(itemCode: string): Promise<UpgradeResponse> {
  const token = getAuthToken()
  
  const response = await fetch(`${API_BASE}/api/v1/items/upgrade`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ item_code: itemCode }),
  })

  if (!response.ok) {
    throw new Error(`Failed to upgrade item: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get a specific item with user progress.
 */
export async function getItem(itemCode: string): Promise<UserItem> {
  const token = getAuthToken()
  
  const response = await fetch(`${API_BASE}/api/v1/items/${itemCode}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get item: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get all item blueprints.
 */
export async function getBlueprints(room?: string): Promise<ItemBlueprint[]> {
  const token = getAuthToken()
  const url = room 
    ? `${API_BASE}/api/v1/items/blueprints?room=${room}`
    : `${API_BASE}/api/v1/items/blueprints`
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get blueprints: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get the energy rewards for each level-up.
 */
export async function getLevelEnergyRewards(): Promise<{
  rewards: Record<string, number>
  description: string
}> {
  const response = await fetch(`${API_BASE}/api/v1/currencies/level-rewards`)

  if (!response.ok) {
    throw new Error(`Failed to get level rewards: ${response.statusText}`)
  }

  return response.json()
}

