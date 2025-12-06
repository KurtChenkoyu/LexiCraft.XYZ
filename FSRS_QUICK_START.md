# FSRS Quick Start Guide

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install the `fsrs` library (>=4.0.0) along with other dependencies.

## Step 2: Run Database Migration

Apply the FSRS migration to your database:

```bash
# Using psql
psql -d your_database_name -f migrations/011_fsrs_support.sql

# Or using your database connection string
psql $DATABASE_URL -f migrations/011_fsrs_support.sql
```

This migration:
- Adds FSRS columns to `verification_schedule` table
- Creates `user_algorithm_assignment` table for A/B testing
- Creates `fsrs_review_history` table for review tracking
- Creates analytics and comparison tables
- Adds helper functions and views

## Step 3: Verify Setup

Run the verification script:

```bash
python scripts/verify_fsrs_setup.py
```

This checks:
- ✅ All modules can be imported
- ✅ FSRS library is installed
- ✅ Database tables exist
- ✅ Algorithm services work

## Step 4: Test the API

Start your backend server:

```bash
cd backend
uvicorn src.main:app --reload
```

Test the endpoints:

```bash
# Get your algorithm assignment (requires auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/verification/algorithm

# Process a review
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"learning_progress_id": 123, "performance_rating": 2, "response_time_ms": 1500}' \
  http://localhost:8000/api/v1/verification/review

# Get algorithm comparison
curl http://localhost:8000/api/v1/analytics/algorithm-comparison?days=30
```

## Step 5: (Optional) Migrate Existing Users

If you have existing users with SM-2+ data, you can migrate them to FSRS:

```bash
# Migrate all eligible users (100+ reviews)
python scripts/migrate_to_fsrs.py --all

# Migrate specific user
python scripts/migrate_to_fsrs.py --user-id USER_UUID

# Backfill review history
python scripts/backfill_fsrs_history.py --all
```

## How It Works

### Automatic Assignment

New users are automatically assigned to either SM-2+ or FSRS (50/50 split) when they:
- Complete onboarding
- Create their first verification schedule
- Process their first review

### Algorithm Selection

The system automatically uses the user's assigned algorithm:
- When creating verification schedules
- When processing reviews
- When calculating next review dates

### A/B Testing

Both algorithms run in parallel:
- Users are randomly assigned (50/50)
- Performance is tracked separately
- Analytics compare efficiency and retention
- Recommendations are generated based on data

## Monitoring

### Check Algorithm Performance

```bash
GET /api/v1/analytics/algorithm-comparison?days=30
```

Returns:
- User counts per algorithm
- Reviews and retention rates
- FSRS advantage percentages
- Recommendations

### Check Daily Trends

```bash
GET /api/v1/analytics/daily-trend?days=14
```

Returns daily metrics for both algorithms over time.

### Check User Stats

```bash
GET /api/v1/analytics/user-stats
```

Returns individual user's algorithm performance and percentiles.

## Troubleshooting

### FSRS Library Not Installed

```bash
pip install fsrs
```

### Database Migration Fails

Check that:
1. You're connected to the correct database
2. The `verification_schedule` table exists (from previous migrations)
3. You have sufficient permissions

### Import Errors

Make sure you're running from the `backend` directory:
```bash
cd backend
python scripts/verify_fsrs_setup.py
```

### Algorithm Not Assigned

Users get assigned automatically on first use. To manually assign:
```python
from src.spaced_repetition import assign_user_algorithm
assign_user_algorithm(user_id, db_session, algorithm='fsrs')
```

## Next Steps

1. **Monitor A/B Test**: Check analytics endpoints regularly
2. **Collect Data**: Let both algorithms run for at least 2-4 weeks
3. **Analyze Results**: Compare reviews per word, retention rates
4. **Make Decision**: Based on data, decide whether to:
   - Keep both algorithms
   - Migrate all users to FSRS
   - Keep SM-2+ as default

## Support

For issues or questions:
- Check `FSRS_IMPLEMENTATION_SUMMARY.md` for detailed documentation
- Review `backend/src/spaced_repetition/` for implementation details
- Check test files in `backend/tests/spaced_repetition/` for usage examples

