# Get Your Landing Page Live - 3 Simple Steps

Your landing page is **ready** and running locally. Here's how to get it live:

## 🚀 Option 1: Deploy via Vercel Web (Easiest - 5 minutes)

### Step 1: Push to GitHub

**If you already have a GitHub repo:**
```bash
cd /Users/kurtchen/lexicraft-project/landing-page
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**If you need to create a GitHub repo:**
1. Go to https://github.com/new
2. Name it: `lexicraft-landing`
3. **Don't** check any boxes (no README, .gitignore, or license)
4. Click "Create repository"
5. Then run:
```bash
cd /Users/kurtchen/lexicraft-project/landing-page
git remote add origin https://github.com/YOUR_USERNAME/lexicraft-landing.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

1. Go to **https://vercel.com/new**
2. Click **"Continue with GitHub"** (or GitLab/Bitbucket)
3. Select your repository: `lexicraft-landing`
4. Vercel will auto-detect Next.js settings ✅
5. Click **"Deploy"**
6. Wait 1-2 minutes for deployment
7. **Your site will be live!** 🎉

### Step 3: Add Environment Variables

After deployment, go to your Vercel project dashboard:

1. Click on your project
2. Go to **Settings** → **Environment Variables**
3. Add these (choose one email service and one analytics):

**Email Service:**
```
NEXT_PUBLIC_EMAIL_SERVICE=convertkit
CONVERTKIT_API_KEY=your_key
CONVERTKIT_FORM_ID=your_form_id
```

**Analytics:**
```
NEXT_PUBLIC_ANALYTICS_SERVICE=posthog
NEXT_PUBLIC_POSTHOG_KEY=your_key
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

4. Click **"Redeploy"** to apply changes

---

## 🚀 Option 2: Deploy via Vercel CLI (If you prefer CLI)

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

### Step 3: Add Environment Variables
Same as Option 1, Step 3 above.

---

## ✅ After Deployment

1. **Test your live site:**
   - Visit your Vercel URL (e.g., `https://lexicraft-landing.vercel.app`)
   - Test the waitlist form
   - Check mobile responsiveness

2. **Add environment variables** (required for form/analytics to work)

3. **Share for feedback:**
   - Share with 5+ friends
   - Collect feedback

---

## 🎯 Your Landing Page URL

After deployment, your site will be live at:
- `https://your-project-name.vercel.app`
- Or your custom domain (if you add one)

---

## 📝 Quick Commands Reference

```bash
# View locally (already running)
open http://localhost:3000

# Push to GitHub (if repo exists)
cd /Users/kurtchen/lexicraft-project/landing-page
git push

# Deploy via CLI (after login)
vercel --prod
```

---

**Need help?** Check `DEPLOY_NOW.md` for detailed instructions.

