# Update Vercel to Use New GitHub Repository

## Step 1: Update Git Remote

First, update your local Git remote to point to the new repository:

```bash
# Remove the old remote
git remote remove origin

# Add the new remote (replace with your new repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO_NAME.git

# Verify the new remote
git remote -v

# Push to the new repository
git push -u origin main
```

## Step 2: Update Vercel Project Settings

You have two options:

### Option A: Update Existing Vercel Project (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to **Settings** → **Git**
4. Click **Disconnect** next to the current GitHub repository
5. Click **Connect Git Repository**
6. Select your new GitHub repository
7. Vercel will automatically detect the framework and deploy

### Option B: Create New Vercel Project

If you prefer to start fresh:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New Project**
3. Import your new GitHub repository
4. Configure settings (framework should auto-detect as Next.js)
5. Add environment variables if needed
6. Click **Deploy**

## Step 3: Verify Deployment

After connecting the new repository:

1. Vercel will automatically trigger a deployment
2. Check the deployment logs to ensure it succeeds
3. Test your live site to confirm everything works
4. Update any custom domains if needed (Settings → Domains)

## Important Notes

- **Environment Variables**: If you created a new project, you'll need to re-add all environment variables in the Vercel dashboard
- **Custom Domains**: If you had custom domains configured, you may need to reconnect them
- **Deploy Hooks**: Any webhooks or integrations will need to be updated with the new project URL

## Quick Command Reference

```bash
# Check current remote
git remote -v

# Update remote (replace with your new repo)
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO_NAME.git

# Push to new repo
git push -u origin main
```

