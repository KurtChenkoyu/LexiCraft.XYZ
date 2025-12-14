# Game Engine - Usage Examples

Quick reference guide for using the new Zustand + Bootstrap pattern.

---

## Reading Data

### Basic Usage
```typescript
import { useAppStore } from '@/stores/useAppStore'

function MyComponent() {
  // Read directly from store
  const user = useAppStore((state) => state.user)
  const balance = useAppStore((state) => state.balance)
  
  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <p>Balance: {balance.available_points} pts</p>
    </div>
  )
}
```

### Using Selectors (Optimized)
```typescript
import { useAppStore, selectBalance, selectUnreadNotifications } from '@/stores/useAppStore'

function Dashboard() {
  // Only re-renders when balance changes (not when other state changes)
  const balance = useAppStore(selectBalance)
  
  // Only re-renders when unread notifications change
  const unreadCount = useAppStore(selectUnreadNotifications).length
  
  return (
    <div>
      <WalletBadge balance={balance} />
      <NotificationBell count={unreadCount} />
    </div>
  )
}
```

### Multiple Values
```typescript
function StatsPanel() {
  const { learnerProfile, achievements, progress } = useAppStore((state) => ({
    learnerProfile: state.learnerProfile,
    achievements: state.achievements,
    progress: state.progress,
  }))
  
  return (
    <div>
      <p>Level: {learnerProfile?.level.level}</p>
      <p>Achievements: {achievements.length}</p>
      <p>Words: {progress.total_discovered}</p>
    </div>
  )
}
```

---

## Writing Data

### Simple Update
```typescript
function UpdateProfileButton() {
  const setUser = useAppStore((state) => state.setUser)
  
  const handleUpdate = async () => {
    // 1. Update Zustand (instant UI)
    setUser({
      id: '123',
      email: 'user@example.com',
      name: 'New Name',
      age: 25,
      roles: ['learner'],
      email_confirmed: true,
    })
    
    // 2. Sync to backend (background)
    await api.updateProfile({ name: 'New Name' })
  }
  
  return <button onClick={handleUpdate}>Update Profile</button>
}
```

### Optimistic Update (Recommended)
```typescript
function VerifyWordButton({ senseId, currentSolidCount }: Props) {
  const updateProgress = useAppStore((state) => state.updateProgress)
  
  const handleVerify = async () => {
    // 1. Optimistic update (instant UI feedback)
    updateProgress({ solid_count: currentSolidCount + 1 })
    
    try {
      // 2. Sync to backend
      await api.verifyWord(senseId)
      // Success! UI already updated
    } catch (error) {
      // 3. Rollback on error
      updateProgress({ solid_count: currentSolidCount })
      alert('Verification failed')
    }
  }
  
  return <button onClick={handleVerify}>Verify</button>
}
```

### Batch Update
```typescript
function CompleteGoalButton({ goalId }: Props) {
  const { goals, setGoals, updateWallet } = useAppStore((state) => ({
    goals: state.goals,
    setGoals: state.setGoals,
    updateWallet: state.updateWallet,
  }))
  
  const handleComplete = async () => {
    // 1. Update multiple pieces of state
    const updatedGoals = goals.map(g => 
      g.id === goalId ? { ...g, status: 'completed' } : g
    )
    setGoals(updatedGoals)
    updateWallet(100) // Add 100 points
    
    // 2. Sync to backend
    await api.completeGoal(goalId)
  }
  
  return <button onClick={handleComplete}>Complete Goal</button>
}
```

---

## Custom Hooks (Reusable Patterns)

### useCurrentChild
```typescript
// hooks/useCurrentChild.ts
import { useAppStore, selectSelectedChild } from '@/stores/useAppStore'

export function useCurrentChild() {
  return useAppStore(selectSelectedChild)
}

// Usage
function ChildProfile() {
  const child = useCurrentChild()
  
  if (!child) return <p>No child selected</p>
  
  return <div>{child.name}</div>
}
```

### useWallet
```typescript
// hooks/useWallet.ts
import { useAppStore } from '@/stores/useAppStore'

export function useWallet() {
  const balance = useAppStore((state) => state.balance)
  const updateWallet = useAppStore((state) => state.updateWallet)
  
  const addPoints = (amount: number) => {
    updateWallet(amount)
    // Could trigger confetti animation here
  }
  
  const deductPoints = (amount: number) => {
    if (balance.available_points >= amount) {
      updateWallet(-amount)
      return true
    }
    return false
  }
  
  return {
    balance,
    addPoints,
    deductPoints,
  }
}

// Usage
function BuyItemButton({ cost }: Props) {
  const { balance, deductPoints } = useWallet()
  
  const handleBuy = () => {
    if (deductPoints(cost)) {
      alert('Purchase successful!')
    } else {
      alert('Insufficient points')
    }
  }
  
  return (
    <button 
      onClick={handleBuy}
      disabled={balance.available_points < cost}
    >
      Buy ({cost} pts)
    </button>
  )
}
```

### useProgress
```typescript
// hooks/useProgress.ts
import { useAppStore } from '@/stores/useAppStore'

export function useProgress() {
  const progress = useAppStore((state) => state.progress)
  const updateProgress = useAppStore((state) => state.updateProgress)
  
  const addWord = (status: 'raw' | 'hollow' | 'solid') => {
    updateProgress({
      total_discovered: progress.total_discovered + 1,
      [`${status}_count`]: progress[`${status}_count`] + 1,
    })
  }
  
  const upgradeWord = (from: 'raw' | 'hollow', to: 'hollow' | 'solid') => {
    updateProgress({
      [`${from}_count`]: progress[`${from}_count`] - 1,
      [`${to}_count`]: progress[`${to}_count`] + 1,
    })
  }
  
  return {
    progress,
    addWord,
    upgradeWord,
  }
}

// Usage
function MineButton({ senseId }: Props) {
  const { addWord } = useProgress()
  
  const handleMine = async () => {
    // 1. Optimistic update
    addWord('raw')
    
    // 2. Sync to backend
    await api.mineWord(senseId)
  }
  
  return <button onClick={handleMine}>Mine Word</button>
}
```

---

## Loading States

### Check Bootstrap Status
```typescript
function App() {
  const isBootstrapped = useAppStore((state) => state.isBootstrapped)
  const isSyncing = useAppStore((state) => state.isSyncing)
  
  if (!isBootstrapped) {
    // This should rarely happen (only if user navigates directly to a page)
    return <LoadingScreen />
  }
  
  return (
    <div>
      {isSyncing && <SyncIndicator />}
      <MainContent />
    </div>
  )
}
```

### Sync Indicator (Optional)
```typescript
function SyncIndicator() {
  const isSyncing = useAppStore((state) => state.isSyncing)
  
  if (!isSyncing) return null
  
  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="flex items-center gap-2 bg-blue-500 text-white px-3 py-2 rounded-lg shadow-lg">
        <SpinnerIcon className="animate-spin" />
        <span className="text-sm">Syncing...</span>
      </div>
    </div>
  )
}
```

---

## Background Sync

### Manual Trigger
```typescript
function RefreshButton() {
  const setIsSyncing = useAppStore((state) => state.setIsSyncing)
  const user = useAppStore((state) => state.user)
  
  const handleRefresh = async () => {
    if (!user) return
    
    setIsSyncing(true)
    try {
      await downloadService.downloadAllUserData(user.id)
      // Data will automatically update in Zustand
      alert('Data refreshed!')
    } catch (error) {
      alert('Refresh failed')
    } finally {
      setIsSyncing(false)
    }
  }
  
  return <button onClick={handleRefresh}>Refresh Data</button>
}
```

---

## Logout

### Clear All Data
```typescript
import { resetBootstrap } from '@/services/bootstrap'
import { useAppStore } from '@/stores/useAppStore'

function LogoutButton() {
  const reset = useAppStore((state) => state.reset)
  
  const handleLogout = async () => {
    // 1. Clear Zustand store
    reset()
    
    // 2. Clear IndexedDB
    await resetBootstrap()
    
    // 3. Clear auth (Supabase)
    await supabase.auth.signOut()
    
    // 4. Redirect to login
    router.push('/login')
  }
  
  return <button onClick={handleLogout}>Logout</button>
}
```

---

## Testing

### Access Store in Tests
```typescript
import { useAppStore } from '@/stores/useAppStore'

describe('WalletBadge', () => {
  beforeEach(() => {
    // Set up test data
    useAppStore.setState({
      balance: {
        total_earned: 500,
        available_points: 300,
        locked_points: 200,
        withdrawn_points: 0,
      }
    })
  })
  
  it('displays balance', () => {
    render(<WalletBadge />)
    expect(screen.getByText('300 pts')).toBeInTheDocument()
  })
  
  afterEach(() => {
    // Clean up
    useAppStore.setState(useAppStore.getInitialState())
  })
})
```

---

## Common Patterns

### Loading with Fallback
```typescript
function UserProfile() {
  const user = useAppStore((state) => state.user)
  
  // Should rarely be null if Bootstrap ran correctly
  if (!user) {
    return <div>Loading profile...</div>
  }
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  )
}
```

### Conditional Rendering
```typescript
function AchievementBadge({ achievementId }: Props) {
  const achievement = useAppStore((state) => 
    state.achievements.find(a => a.id === achievementId)
  )
  
  if (!achievement?.unlocked) {
    return <LockedBadge />
  }
  
  return <UnlockedBadge achievement={achievement} />
}
```

### Computed Values
```typescript
function ProgressBar() {
  const progress = useAppStore((state) => state.progress)
  
  // Derive values from state
  const totalWords = progress.total_discovered
  const masteredPercentage = totalWords > 0 
    ? (progress.solid_count / totalWords) * 100 
    : 0
  
  return (
    <div>
      <p>{totalWords} words discovered</p>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-green-500 h-2 rounded-full"
          style={{ width: `${masteredPercentage}%` }}
        />
      </div>
    </div>
  )
}
```

---

## Migration Checklist

When migrating a component from old pattern to new:

- [ ] Remove `useState` for data that's in Zustand
- [ ] Remove `useEffect` that fetches data
- [ ] Replace with `useAppStore(selector)`
- [ ] Remove loading spinners (data is already loaded)
- [ ] Add optimistic updates for mutations
- [ ] Test offline behavior

**Before:**
```typescript
function OldComponent() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetch('/api/data')
      .then(res => res.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [])
  
  if (loading) return <Spinner />
  return <div>{data.value}</div>
}
```

**After:**
```typescript
function NewComponent() {
  const data = useAppStore((state) => state.data)
  return <div>{data.value}</div>
}
```

---

## Tips

1. **Use selectors** for performance (component only re-renders when selected data changes)
2. **Optimistic updates** for instant UI feedback
3. **Batch updates** when changing multiple pieces of state
4. **Custom hooks** for reusable logic
5. **Check `isBootstrapped`** if rendering conditionally

---

See `GAME_ENGINE.md` for architecture details.

