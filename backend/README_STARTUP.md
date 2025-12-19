# Backend Startup Guide

## The Problem

If you have multiple backend projects on your machine (like `earn-money-back-project` and `LexiCraft.xyz`), old backend processes can keep running and cause confusion. The frontend might connect to the wrong backend, leading to timeouts and errors.

## The Solution

Use the **`start-backend.sh`** script to ensure ONLY the correct backend runs.

## Quick Start

### Option 1: Direct Script (Recommended)

```bash
cd backend
./start-backend.sh
```

This script will:
1. ✅ Verify you're in the correct project (`LexiCraft.xyz`)
2. ✅ Kill any old/wrong backend processes
3. ✅ Clear port 8000
4. ✅ Start the backend from the correct location

### Option 2: NPM Script (From Frontend)

```bash
cd landing-page
npm run backend:start
```

### Option 3: Manual (Not Recommended)

```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000 --log-level info
```

⚠️ **Warning:** Manual startup doesn't kill old processes, so you might end up with multiple backends running.

## Verify Backend is Correct

After starting, verify the backend is correct:

```bash
cd backend
./check-backend.sh
```

Or from frontend:

```bash
cd landing-page
npm run backend:stop
```

## Health Check Endpoint

The `/health` endpoint now includes the project path:

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

Look for `"project_path"` to verify it's from `LexiCraft.xyz`.

## Troubleshooting

### "Port 8000 is still in use"

```bash
# Kill all processes on port 8000
lsof -ti :8000 | xargs kill -9

# Or use the npm script
cd landing-page
npm run backend:stop
```

### "Wrong project directory"

Make sure you're running the script from `LexiCraft.xyz/backend/`, not from `earn-money-back-project/backend/`.

### Backend not responding

1. Check if it's running: `lsof -i :8000`
2. Check logs in the terminal where you started it
3. Verify database connection: Check backend logs for connection errors

## NPM Scripts Reference

From `landing-page/` directory:

- `npm run backend:start` - Start backend (kills old processes first)
- `npm run backend:stop` - Stop backend (kills all processes on port 8000)
- `npm run backend:check` - Check backend health (requires `curl` and `python3`)


