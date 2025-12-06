# Deploy Now - Quick Guide

Your landing page is **ready to deploy**! The build is successful. Choose one of these options:

## Option 1: Deploy via Vercel CLI (Fastest - 2 minutes)

### Step 1: Login to Vercel
```bash
cd landing-page
vercel login
```
This will open your browser to authenticate with Vercel (GitHub, GitLab, or Bitbucket).

### Step 2: Deploy
```bash
./deploy.sh
```

Or manually:
```bash
vercel --prod --yes
```

### Step 3: Add Environment Variables
After deployment, go to your Vercel dashboard:
1. Select your project
2. Go to Settings → Environment Variables
3. Add these variables:

**Email Service (choose one):**
```
NEXT_PUBLIC_EMAIL_SERVICE=convertkit
CONVERTKIT_API_KEY=your_api_key
CONVERTKIT_FORM_ID=your_form_id
```

OR

```
NEXT_PUBLIC_EMAIL_SERVICE=mailchimp
MAILCHIMP_API_KEY=your_api_key
MAILCHIMP_LIST_ID=your_list_id
MAILCHIMP_SERVER_PREFIX=us1
```

**Analytics (choose one):**
```
NEXT_PUBLIC_ANALYTICS_SERVICE=posthog
NEXT_PUBLIC_POSTHOG_KEY=your_posthog_key
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

OR

```
NEXT_PUBLIC_ANALYTICS_SERVICE=mixpanel
NEXT_PUBLIC_MIXPANEL_TOKEN=your_mixpanel_token
```

4. Redeploy after adding variables (or they'll be added on next deploy)

---

## Option 2: Deploy via Vercel Web Interface (No CLI needed)

### Step 1: Push to GitHub
```bash
cd landing-page

# If you haven't created a GitHub repo yet:
# 1. Go to github.com and create a new repository
# 2. Then run:

git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Import to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Vercel will auto-detect Next.js settings
5. Click "Deploy"

### Step 3: Add Environment Variables
Same as Option 1, Step 3 above.

---

## Option 3: Deploy to Netlify

### Step 1: Push to GitHub
Same as Option 2, Step 1.

### Step 2: Import to Netlify
1. Go to [netlify.com](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Connect to GitHub and select your repository
4. Build settings:
   - Build command: `npm run build`
   - Publish directory: `.next`
5. Click "Deploy site"

### Step 3: Add Environment Variables
1. Go to Site settings → Environment variables
2. Add the same variables as listed above

---

## ✅ After Deployment

1. **Test your live site:**
   - Visit your Vercel/Netlify URL
   - Test the waitlist form
   - Check analytics dashboard

2. **Share for feedback:**
   - Share with 5+ friends/family
   - Collect feedback on design, messaging, usability

3. **Report back:**
   - Landing page URL: `https://your-project.vercel.app`
   - Email collection status
   - Analytics setup
   - Feedback received

---

## 🚨 Important Notes

- **Environment variables are required** for the form and analytics to work
- **Test the form** after adding environment variables
- **Redeploy** after adding environment variables (or wait for next auto-deploy)

---

## Need Help?

- Check `README.md` for detailed setup
- Check `DEPLOYMENT.md` for full deployment guide
- Email: support@earnmoneyback.com

