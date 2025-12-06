# Supabase Setup Instructions

## Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Sign up or log in
3. Click "New Project"
4. Fill in project details:
   - **Name**: lexicraft-mvp
   - **Database Password**: (choose a strong password, save it!)
   - **Region**: Choose closest to Taiwan (e.g., `Southeast Asia (Singapore)`)
5. Click "Create new project"
6. Wait for project to be created (2-3 minutes)

## Step 2: Get Connection String

1. In your Supabase project dashboard, go to **Settings** → **Database**
2. Click **"Connect to your project"** button (or find it in the Database settings page)
3. In the modal that opens, select the **"Connection String"** tab
4. Configure the connection:
   - **Type**: Select "URI"
   - **Source**: Select "Primary Database"
   - **Method**: Select "Direct connection" (for applications with persistent connections)
5. Copy the connection string (it will look like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with your actual database password

**Note about IPv4 Warning**: If you see an "Not IPv4 compatible" warning:
- For local development: You can usually ignore this if your network supports IPv6
- For production/cloud deployments: Use **Session Pooler** instead (change "Method" to "Session Pooler" in the dropdown)
- Or purchase the IPv4 add-on if needed

## Step 3: Set Environment Variable

Create a `.env` file in the `backend/` directory:

```bash
# PostgreSQL (Supabase)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres
```

**Important**: Add `.env` to `.gitignore` to avoid committing credentials!

## Step 4: Run Migration

You can run the migration in two ways:

### Option A: Using Supabase SQL Editor (Recommended for first time)

1. Go to **SQL Editor** in Supabase dashboard
2. Click **New query**
3. Copy and paste the contents of `migrations/001_initial_schema.sql`
4. Click **Run** (or press Cmd/Ctrl + Enter)
5. Verify tables were created in **Table Editor**

### Option B: Using Python Script

```bash
cd backend
python scripts/run_migration.py
```

## Step 5: Verify Setup

Run the test script:

```bash
cd backend
python scripts/test_postgres_connection.py
```

You should see:
- ✅ Connection successful
- ✅ All tables created
- ✅ All CRUD operations working

## Troubleshooting

### Connection Error
- Verify your `DATABASE_URL` is correct
- Check that your IP is allowed (Supabase allows all by default, but check if you have restrictions)
- Verify password is correct
- If you see IPv4 errors, try using Session Pooler connection string instead (change "Method" to "Session Pooler" in the connection modal)

### IPv4 Compatibility Issues
- If your network only supports IPv4, use the **Session Pooler** connection string instead
- In the connection modal, change "Method" from "Direct connection" to "Session Pooler"
- The Session Pooler connection string will have a different format (usually includes `pooler.supabase.co`)

### Table Already Exists
- If you see "table already exists" errors, you can either:
  - Drop existing tables and re-run migration
  - Or modify migration to use `CREATE TABLE IF NOT EXISTS` (already done)

### Permission Errors
- Make sure you're using the `postgres` user connection string
- Check that your project is fully initialized (wait a few minutes after creation)

## Next Steps

After setup is complete:
1. Test all CRUD operations using `test_postgres_connection.py`
2. Review the models in `src/database/models.py`
3. Start using the CRUD functions in `src/database/postgres_crud/`

