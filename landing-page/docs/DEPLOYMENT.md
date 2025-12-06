# Deployment Guide - lexicraft.xyz Landing Page

## Quick Start

This landing page is ready to deploy to Vercel (recommended) or Netlify.

## Pre-Deployment Checklist

- [ ] Email service account created (ConvertKit or Mailchimp)
- [ ] Analytics account created (PostHog or Mixpanel)
- [ ] Environment variables documented
- [ ] Test form submission locally
- [ ] Test analytics tracking locally

## Deployment Steps

### Option 1: Vercel (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Landing page"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will auto-detect Next.js settings

3. **Add Environment Variables**
   In Vercel dashboard → Settings → Environment Variables, add:
   
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

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your site will be live at `https://your-project.vercel.app`

5. **Custom Domain (Optional)**
   - Go to Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

### Option 2: Netlify

1. **Push to GitHub** (same as Vercel)

2. **Import to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect to GitHub and select your repository

3. **Configure Build Settings**
   - Build command: `npm run build`
   - Publish directory: `.next`
   - Framework: Next.js (auto-detected)

4. **Add Environment Variables**
   - Go to Site settings → Environment variables
   - Add the same variables as listed for Vercel above

5. **Deploy**
   - Click "Deploy site"
   - Your site will be live at `https://your-project.netlify.app`

## Post-Deployment Testing

### 1. Test Email Collection

1. Visit your live site
2. Fill out the waitlist form with a real email
3. Check your email service dashboard:
   - **ConvertKit**: Forms → Your form → Subscribers
   - **Mailchimp**: Audience → Your list → Members
4. Verify the email appears and custom fields (number of kids) are captured

### 2. Test Analytics

1. Visit your live site
2. Navigate through different sections
3. Click CTAs and submit the form
4. Check your analytics dashboard:
   - **PostHog**: Events → Live events
   - **Mixpanel**: Events → Live view
5. Verify events are tracking:
   - Page views
   - Form submissions
   - CTA clicks

### 3. Test Mobile Responsiveness

1. Use browser dev tools (F12 → Device toolbar)
2. Test on different screen sizes:
   - Mobile (375px, 414px)
   - Tablet (768px, 1024px)
   - Desktop (1280px+)
3. Test on actual devices:
   - iPhone
   - Android phone
   - iPad/Tablet
4. Verify:
   - All text is readable
   - Form works correctly
   - Navigation is smooth
   - Images load properly

### 4. Test Privacy Policy

1. Click "Privacy Policy" link in footer
2. Verify page loads correctly
3. Verify "Back to Home" link works
4. Check all sections are readable

## Troubleshooting

### Form Not Submitting

**Issue**: Form shows error or doesn't submit

**Solutions**:
1. Check environment variables are set correctly in Vercel/Netlify
2. Verify API keys are valid
3. Check browser console for errors
4. Verify email service API is accessible (not blocked by firewall)

### Analytics Not Tracking

**Issue**: Events not appearing in analytics dashboard

**Solutions**:
1. Check environment variables are set correctly
2. Verify API keys are valid
3. Check browser console for errors
4. Ensure ad blockers are disabled (they can block analytics)
5. Wait a few minutes for events to appear (some services have delay)

### Build Fails

**Issue**: Deployment fails during build

**Solutions**:
1. Check build logs in Vercel/Netlify dashboard
2. Verify all dependencies are in `package.json`
3. Ensure Node.js version is compatible (Vercel uses 18.x by default)
4. Check for TypeScript errors: `npm run build` locally

## Monitoring

### Key Metrics to Track

1. **Page Views**: Total visitors
2. **Form Submissions**: Waitlist signups
3. **Conversion Rate**: Form submissions / Page views
4. **Bounce Rate**: Single-page visits
5. **Time on Page**: Engagement metric

### Weekly Review

- Check email service for new subscribers
- Review analytics for traffic patterns
- Monitor form submission rate
- Check for any errors in logs

## Next Steps After Deployment

1. ✅ Share landing page URL with team
2. ✅ Test with 5+ friends/family members
3. ✅ Collect feedback on:
   - Design and layout
   - Clarity of messaging
   - Form usability
   - Mobile experience
4. ✅ Report back to Master Planning Chat with:
   - Landing page URL
   - Email collection status
   - Analytics setup confirmation
   - Feedback received
   - Any issues discovered

## Support

For deployment issues:
- Vercel: [vercel.com/docs](https://vercel.com/docs)
- Netlify: [docs.netlify.com](https://docs.netlify.com)
- Email: support@earnmoneyback.com

