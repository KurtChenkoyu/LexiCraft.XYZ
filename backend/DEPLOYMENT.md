# Backend API Deployment Guide

This guide covers deploying the LexiCraft backend API to Railway or Render.

## Prerequisites

1. **Environment Variables**: Ensure you have the following environment variables set:
   - `DATABASE_URL`: PostgreSQL connection string (Supabase)
   - `NEO4J_URI`: Neo4j connection URI
   - `NEO4J_USER`: Neo4j username
   - `NEO4J_PASSWORD`: Neo4j password
   - `PORT`: Port number (usually set automatically by platform)

## Deployment Options

### Option 1: Railway

1. **Install Railway CLI** (optional):
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Initialize Project**:
   ```bash
   cd backend
   railway init
   ```

4. **Set Environment Variables**:
   ```bash
   railway variables set DATABASE_URL=your_postgres_url
   railway variables set NEO4J_URI=your_neo4j_uri
   railway variables set NEO4J_USER=your_neo4j_user
   railway variables set NEO4J_PASSWORD=your_neo4j_password
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

   Or connect to GitHub for automatic deployments:
   ```bash
   railway link
   ```

6. **Verify Deployment**:
   - Check the Railway dashboard for the service URL
   - Visit `https://your-service.railway.app/health` to verify

### Option 2: Render

1. **Create New Web Service**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**:
   - **Name**: `lexicraft-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend`

3. **Set Environment Variables**:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `NEO4J_URI`: Your Neo4j connection URI
   - `NEO4J_USER`: Your Neo4j username
   - `NEO4J_PASSWORD`: Your Neo4j password
   - `PORT`: `10000` (Render default)

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy

5. **Verify Deployment**:
   - Check the service logs
   - Visit `https://your-service.onrender.com/health` to verify

## Post-Deployment

### 1. Update Frontend API URL

Update your frontend `.env` or environment variables:
```bash
NEXT_PUBLIC_API_URL=https://your-service.railway.app
# or
NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

### 2. Test Endpoints

Test the deployed API:
```bash
# Health check
curl https://your-service.railway.app/health

# Start survey
curl -X POST https://your-service.railway.app/api/v1/survey/start \
  -H "Content-Type: application/json" \
  -d '{"cefr_level": "B1"}'
```

### 3. Monitor Logs

- **Railway**: View logs in the Railway dashboard
- **Render**: View logs in the Render dashboard

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify `DATABASE_URL` is correct
   - Check if database allows connections from deployment platform
   - For Supabase: Ensure connection pooling is enabled

2. **Neo4j Connection Errors**:
   - Verify `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` are correct
   - Check if Neo4j Aura allows connections from deployment platform IPs

3. **Port Issues**:
   - Railway and Render set `PORT` automatically
   - Ensure your start command uses `$PORT` environment variable

4. **Build Failures**:
   - Check that all dependencies are in `requirements.txt`
   - Verify Python version compatibility

### Health Check Endpoint

The API includes a health check endpoint at `/health`:
```json
{
  "status": "ok",
  "version": "7.1",
  "service": "LexiCraft Survey API"
}
```

## Local Testing

Before deploying, test locally:
```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Then test endpoints:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/survey/start \
  -H "Content-Type: application/json" \
  -d '{"cefr_level": "B1"}'
```

