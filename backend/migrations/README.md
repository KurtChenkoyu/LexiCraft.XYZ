# Database Migrations

This directory contains all SQL migration files for the LexiCraft database schema.

## Migration Order

Migrations should be run in this order:

1. `001_initial_schema.sql` - Core tables (users, children, learning_progress, etc.)
2. `002_survey_schema.sql` - Survey system tables
3. `003_survey_questions.sql` - Survey questions data
4. `004_supabase_auth_integration.sql` - Supabase auth integration
5. `005_email_confirmation_tracking.sql` - Email confirmation tracking
6. `006_update_trigger_for_email_confirmation.sql` - Email confirmation triggers
7. `007_unified_user_model.sql` - Unified user model
8. `008_update_trigger_for_roles.sql` - Role update triggers
9. `009_add_email_confirmed_at.sql` - Email confirmation timestamp
10. `010_progressive_survey_model.sql` - Progressive survey model
11. `011_fsrs_support.sql` - FSRS (spaced repetition) support
12. `012_create_learners_table.sql` - Learners table
13. `012_mcq_statistics.sql` - MCQ statistics tables
14. `013_gamification_schema.sql` - Gamification system
15. `014_add_birthday_fields.sql` - Birthday fields
16. `014_backfill_learning_progress_learner_id.sql` - Backfill learner IDs
17. `015_add_learning_progress_learner_id_index.sql` - Performance indexes
18. `015_level_achievement_system.sql` - Level achievement system
19. `016_fix_learning_progress_unique_constraint.sql` - Fix constraints
20. `016_seed_achievements.sql` - Seed achievement data
21. `017_three_currency_system.sql` - Currency system
22. `018_migrate_xp_to_learners.sql` - XP migration
23. `019_rename_tier_to_rank.sql` - Rename tier to rank
24. `020_add_learning_progress_performance_indexes.sql` - Performance indexes
25. `025_add_subscription_fields.sql` - Subscription fields

## Running Migrations

### Option 1: Using Setup Script (Recommended)

```bash
cd backend
./scripts/setup_dev_supabase.sh [DATABASE_URL]
```

Or set environment variable:
```bash
export DEV_DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:6543/postgres?sslmode=require"
./scripts/setup_dev_supabase.sh
```

### Option 2: Using Supabase SQL Editor

1. Go to Supabase Dashboard → SQL Editor
2. Click "New query"
3. Copy and paste each migration file content
4. Run in order (001, 002, 003, etc.)

### Option 3: Using psql

```bash
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:6543/postgres?sslmode=require"

for migration in migrations/*.sql; do
  echo "Running $migration..."
  psql "$DATABASE_URL" -f "$migration"
done
```

## Environment-Specific Migrations

### Development
- Run all migrations on `lexicraft-dev` project
- Use dev database connection string
- Safe to re-run (uses `IF NOT EXISTS` clauses)

### Production
- Migrations should already be applied
- Only run new migrations as they're added
- Always test in dev first!

## Notes

- Most migrations use `IF NOT EXISTS` and `CREATE OR REPLACE` for safety
- Some migrations may fail if re-run (e.g., unique constraints) - this is normal
- Always backup production database before running migrations
- Test migrations in dev environment first

## Troubleshooting

### "relation already exists" errors
- Safe to ignore if re-running migrations
- Tables already exist from previous run

### "column already exists" errors
- Safe to ignore if re-running migrations
- Columns already added from previous run

### Connection errors
- Verify DATABASE_URL format
- Check password is correct
- Ensure using Transaction mode (port 6543) for Supabase

