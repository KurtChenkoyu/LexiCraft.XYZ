# Quick Deploy Guide

## Option 1: Deploy via Vercel Web (Easiest - 5 minutes)

### Step 1: Push to GitHub (Optional but Recommended)

If you have a GitHub account:

```bash
cd /Users/kurtchen/lexicraft-project/landing-page

# Create a new repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy via Vercel Web

1. Go to **https://vercel.com/new**
2. Click **"Continue with GitHub"** (or GitLab/Bitbucket)
3. Select your repository
4. Vercel will auto-detect Next.js settings ✅
5. Click **"Deploy"**
6. Wait 1-2 minutes
7. **Your site is live!** 🎉

### Step 3: Add Environment Variables

After deployment, in Vercel dashboard:
1. Go to **Settings** → **Environment Variables**
2. Add your email service and analytics credentials
3. Click **"Redeploy"**

---

## Option 2: Deploy via CLI (If you prefer)

### Step 1: Login
```bash
cd /Users/kurtchen/lexicraft-project/landing-page
vercel login
```
(Opens browser for authentication)

### Step 2: Deploy
```bash
vercel --prod --yes
```

---

## After Deployment

Your site will be live at: `https://your-project-name.vercel.app`

**Features:**
- ✅ Multi-language support (Traditional Chinese + English)
- ✅ IP-based auto-detection
- ✅ Language switcher
- ✅ All content translated

**Next:** Add environment variables for email/analytics to enable form submissions.

