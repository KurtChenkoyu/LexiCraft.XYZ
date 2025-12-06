# Deploy to Vercel - Quick Guide

## ✅ Changes Already Pushed to GitHub
Your changes have been pushed to: `https://github.com/KurtChenkoyu/lexicraft-landing.git`

---

## Option 1: Auto-Deploy (If Already Connected)

If your Vercel project is already connected to your GitHub repo, it should **automatically deploy** within 1-2 minutes.

**Check your deployment:**
1. Go to https://vercel.com/dashboard
2. Find your project: `lexicraft-landing`
3. You should see a new deployment in progress or completed

---

## Option 2: Connect GitHub to Vercel (First Time)

If this is your first time deploying:

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Click "Add New..." → "Project"**
3. **Import your GitHub repository**:
   - Select: `KurtChenkoyu/lexicraft-landing`
   - Vercel will auto-detect Next.js settings
4. **Configure** (usually auto-detected):
   - Framework Preset: Next.js
   - Root Directory: `landing-page` (if needed)
   - Build Command: `npm run build`
   - Output Directory: `.next`
5. **Click "Deploy"**

Vercel will:
- Deploy your site
- Give you a URL (e.g., `lexicraft-landing.vercel.app`)
- Set up auto-deploy for future pushes

---

## Option 3: Deploy via CLI

If you prefer command line:

```bash
cd landing-page
vercel login
vercel --prod
```

This will:
- Prompt you to log in (opens browser)
- Deploy to production
- Give you a deployment URL

---

## After Deployment

Your updated landing page will be live with:
- ✅ New positioning (verification platform, not teaching app)
- ✅ New sections (Parent Questions, Vocabulary Cliff)
- ✅ Updated terminology throughout
- ✅ Professional navy/gold design

---

## Troubleshooting

**If deployment fails:**
- Check build logs in Vercel dashboard
- Ensure environment variables are set (if needed)
- Verify `package.json` has correct build scripts

**If you need to update environment variables:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add any required variables (e.g., `NEXT_PUBLIC_ANALYTICS_ID`)

---

## Quick Check

After deployment, visit your Vercel URL and verify:
- Hero section shows new headline
- Parent Questions section appears
- Vocabulary Cliff section appears
- All terminology updated (Foundation Elements, Verification Scholarship, etc.)


