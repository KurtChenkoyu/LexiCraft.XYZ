# Run Gamification Migration (013)

The leaderboard page requires gamification tables. Run this migration via **Supabase Dashboard**.

## Steps

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select project **cwgexbjyfcqndeyhravb**
3. Go to **SQL Editor** (left sidebar)
4. Create new query
5. Copy & paste the entire contents of:
   - `backend/migrations/013_gamification_schema.sql`
6. Click **Run**

## Tables Created

- `achievements` - Achievement definitions
- `user_achievements` - User achievement progress
- `user_xp` - User XP and levels
- `xp_history` - XP earning history
- `learning_goals` - User goals
- `leaderboard_entries` - Leaderboard statistics
- `user_connections` - Friends/classmates
- `notifications` - User notifications

## Verify

After running, check the Tables tab - you should see all 8 new tables.

---

**Note**: The connection pooler (port 6543) has issues with large DDL statements. The SQL Editor uses a direct connection and works reliably.

