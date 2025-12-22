#!/bin/bash
# Setup Dev Supabase Database
# 
# This script helps set up the dev Supabase project by running all migrations
# in the correct order.
#
# Usage:
#   ./scripts/setup_dev_supabase.sh [DATABASE_URL]
#
# If DATABASE_URL is not provided, it will use the DEV_DATABASE_URL env var
# or prompt you to enter it.

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Dev Supabase Database${NC}"
echo ""

# Get database URL
if [ -n "$1" ]; then
    DATABASE_URL="$1"
elif [ -n "$DEV_DATABASE_URL" ]; then
    DATABASE_URL="$DEV_DATABASE_URL"
else
    echo -e "${YELLOW}⚠️  DATABASE_URL not provided${NC}"
    echo "Please provide your dev Supabase connection string:"
    echo "Format: postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:6543/postgres?sslmode=require"
    echo ""
    read -p "Enter DATABASE_URL: " DATABASE_URL
fi

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ Error: DATABASE_URL is required${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using database: ${DATABASE_URL%%@*}@...${NC}"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ Error: psql is not installed${NC}"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  macOS:    brew install postgresql@15  (or: brew install libpq)"
    echo "  Ubuntu:   sudo apt-get install postgresql-client"
    echo "  Fedora:   sudo dnf install postgresql"
    echo "  Windows:  Download from https://www.postgresql.org/download/windows/"
    echo ""
    echo "Alternative: Use Supabase SQL Editor to run migrations manually:"
    echo "1. Go to Supabase Dashboard → SQL Editor"
    echo "2. Run each migration file from backend/migrations/ in order"
    echo ""
    echo "See docs/PHASE2_SUPABASE_SETUP.md for detailed instructions."
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="$(cd "$SCRIPT_DIR/../migrations" && pwd)"

echo -e "${GREEN}📁 Migrations directory: $MIGRATIONS_DIR${NC}"
echo ""

# List all migration files in order
MIGRATIONS=(
    "001_initial_schema.sql"
    "002_survey_schema.sql"
    "003_survey_questions.sql"
    "004_supabase_auth_integration.sql"
    "005_email_confirmation_tracking.sql"
    "006_update_trigger_for_email_confirmation.sql"
    "007_unified_user_model.sql"
    "008_update_trigger_for_roles.sql"
    "009_add_email_confirmed_at.sql"
    "010_progressive_survey_model.sql"
    "011_fsrs_support.sql"
    "012_create_learners_table.sql"
    "012_mcq_statistics.sql"
    "013_gamification_schema.sql"
    "014_add_birthday_fields.sql"
    "014_backfill_learning_progress_learner_id.sql"
    "015_add_learning_progress_learner_id_index.sql"
    "015_level_achievement_system.sql"
    "016_fix_learning_progress_unique_constraint.sql"
    "016_seed_achievements.sql"
    "017_three_currency_system.sql"
    "018_migrate_xp_to_learners.sql"
    "019_rename_tier_to_rank.sql"
    "020_add_learning_progress_performance_indexes.sql"
    "025_add_subscription_fields.sql"
)

echo -e "${YELLOW}⚠️  WARNING: This will run ALL migrations on the dev database.${NC}"
echo -e "${YELLOW}   Make sure you're using the DEV Supabase project, not production!${NC}"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${GREEN}🔄 Running migrations...${NC}"
echo ""

# Test connection first
echo -e "${GREEN}Testing database connection...${NC}"
if ! psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Cannot connect to database${NC}"
    echo "Please check your DATABASE_URL and try again."
    exit 1
fi

echo -e "${GREEN}✅ Connection successful${NC}"
echo ""

# Run each migration
SUCCESS_COUNT=0
FAILED_COUNT=0
FAILED_MIGRATIONS=()

for migration in "${MIGRATIONS[@]}"; do
    migration_path="$MIGRATIONS_DIR/$migration"
    
    if [ ! -f "$migration_path" ]; then
        echo -e "${YELLOW}⚠️  Skipping $migration (file not found)${NC}"
        continue
    fi
    
    echo -e "${GREEN}Running: $migration${NC}"
    
    if psql "$DATABASE_URL" -f "$migration_path" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $migration completed${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌ $migration failed${NC}"
        ((FAILED_COUNT++))
        FAILED_MIGRATIONS+=("$migration")
    fi
    echo ""
done

# Summary
echo "=========================================="
echo -e "${GREEN}Migration Summary:${NC}"
echo "  ✅ Successful: $SUCCESS_COUNT"
echo "  ❌ Failed: $FAILED_COUNT"
echo ""

if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "${RED}Failed migrations:${NC}"
    for migration in "${FAILED_MIGRATIONS[@]}"; do
        echo "  - $migration"
    done
    echo ""
    echo "Some migrations may have failed because:"
    echo "  - Tables/columns already exist (safe to ignore if re-running)"
    echo "  - Dependencies not met (check migration order)"
    echo "  - Syntax errors (check migration file)"
    echo ""
    echo "You can run individual migrations manually in Supabase SQL Editor."
else
    echo -e "${GREEN}🎉 All migrations completed successfully!${NC}"
fi

echo ""
echo "Next steps:"
echo "1. Verify tables in Supabase Dashboard → Table Editor"
echo "2. Update .env.local with dev Supabase credentials"
echo "3. Test authentication with dev project"

