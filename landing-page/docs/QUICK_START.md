# Quick Start Guide

Get your landing page up and running in 15 minutes!

## Step 1: Install Dependencies (2 min)

```bash
cd landing-page
npm install
```

## Step 2: Set Up Environment Variables (5 min)

1. Copy the example file:
   ```bash
   cp .env.example .env.local
   ```

2. Choose your email service and get credentials:

   **Option A: ConvertKit** (Recommended for simplicity)
   - Sign up: https://convertkit.com
   - Create a form
   - Get API Key: Settings → Advanced → API Secret
   - Get Form ID: Form settings → Form ID
   - Add to `.env.local`:
     ```
     NEXT_PUBLIC_EMAIL_SERVICE=convertkit
     CONVERTKIT_API_KEY=your_key_here
     CONVERTKIT_FORM_ID=your_form_id_here
     ```

   **Option B: Mailchimp**
   - Sign up: https://mailchimp.com
   - Create an audience/list
   - Get API Key: Account → Extras → API keys
   - Get List ID: Audience settings → Settings → List name and defaults
   - Get Server Prefix: From API key page (e.g., `us1`)
   - Add to `.env.local`:
     ```
     NEXT_PUBLIC_EMAIL_SERVICE=mailchimp
     MAILCHIMP_API_KEY=your_key_here
     MAILCHIMP_LIST_ID=your_list_id_here
     MAILCHIMP_SERVER_PREFIX=us1
     ```

3. Choose your analytics service:

   **Option A: PostHog** (Recommended - free tier available)
   - Sign up: https://posthog.com
   - Create project
   - Get Project API Key: Project Settings → Project API Key
   - Add to `.env.local`:
     ```
     NEXT_PUBLIC_ANALYTICS_SERVICE=posthog
     NEXT_PUBLIC_POSTHOG_KEY=your_key_here
     NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
     ```

   **Option B: Mixpanel**
   - Sign up: https://mixpanel.com
   - Create project
   - Get Project Token: Project Settings → Project Token
   - Add to `.env.local`:
     ```
     NEXT_PUBLIC_ANALYTICS_SERVICE=mixpanel
     NEXT_PUBLIC_MIXPANEL_TOKEN=your_token_here
     ```

## Step 3: Run Development Server (1 min)

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

## Step 4: Test Everything (5 min)

1. **Test Form Submission**
   - Fill out the waitlist form
   - Check your email service dashboard to confirm the email was added
   - Verify custom fields (number of kids) are captured

2. **Test Analytics**
   - Open browser console (F12)
   - Navigate through the site
   - Check your analytics dashboard for events

3. **Test Mobile**
   - Use browser dev tools (F12 → Device toolbar)
   - Test on mobile viewport (375px width)
   - Verify form works on mobile

## Step 5: Deploy to Vercel (2 min)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Landing page"
   # Create repo on GitHub, then:
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to https://vercel.com
   - Click "New Project"
   - Import your GitHub repo
   - Add environment variables (same as `.env.local`)
   - Click "Deploy"

3. **Test Live Site**
   - Visit your Vercel URL
   - Test form submission
   - Test analytics tracking

## ✅ Done!

Your landing page is now live! 

**Next Steps:**
- Share with 5+ friends for feedback
- Monitor email signups
- Track analytics
- Report back to Master Planning Chat

## Troubleshooting

**Form not working?**
- Check environment variables are set correctly
- Verify API keys are valid
- Check browser console for errors

**Analytics not tracking?**
- Check environment variables
- Disable ad blockers (they block analytics)
- Wait a few minutes for events to appear

**Build fails?**
- Check build logs in Vercel dashboard
- Verify all dependencies are installed
- Check for TypeScript errors: `npm run build`

## Need Help?

- Check README.md for detailed setup
- Check DEPLOYMENT.md for deployment guide
- Email: support@earnmoneyback.com

