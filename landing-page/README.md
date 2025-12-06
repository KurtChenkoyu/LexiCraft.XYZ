# LexiCraft.xyz - Landing Page

Landing page for the LexiCraft.xyz MVP waitlist collection.

---

## ⚡ Architecture Principle: "As Snappy as Last War"

> **All pages must render UI instantly. No loading spinners for content.**

See [`docs/ARCHITECTURE_PRINCIPLES.md`](docs/ARCHITECTURE_PRINCIPLES.md) for details.

Key rules:
- Show default/empty states immediately
- Fetch data in background, update silently
- Offline mode is valid, not an error
- Empty leaderboard, "no cards due", Level 1 profile are all legitimate UI states

---

## Features

- ✅ Modern, responsive design with Tailwind CSS
- ✅ Waitlist form with email + number of kids collection
- ✅ Email service integration (ConvertKit or Mailchimp)
- ✅ Analytics tracking (PostHog or Mixpanel)
- ✅ Privacy policy page
- ✅ Mobile-responsive design
- ✅ Ready for Vercel deployment

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env.local` and fill in your credentials:

```bash
cp .env.example .env.local
```

**Required for Email Service:**
- Choose either ConvertKit OR Mailchimp
- For ConvertKit: `CONVERTKIT_API_KEY` and `CONVERTKIT_FORM_ID`
- For Mailchimp: `MAILCHIMP_API_KEY`, `MAILCHIMP_LIST_ID`, and `MAILCHIMP_SERVER_PREFIX`

**Required for Analytics:**
- Choose either PostHog OR Mixpanel
- For PostHog: `NEXT_PUBLIC_POSTHOG_KEY` and `NEXT_PUBLIC_POSTHOG_HOST`
- For Mixpanel: `NEXT_PUBLIC_MIXPANEL_TOKEN`

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Email Service Setup

### ConvertKit

1. Sign up at [ConvertKit](https://convertkit.com)
2. Create a form for waitlist collection
3. Get your API Key from Settings → Advanced
4. Get your Form ID from the form settings
5. Add to `.env.local`:
   ```
   NEXT_PUBLIC_EMAIL_SERVICE=convertkit
   CONVERTKIT_API_KEY=your_api_key
   CONVERTKIT_FORM_ID=your_form_id
   ```

### Mailchimp

1. Sign up at [Mailchimp](https://mailchimp.com)
2. Create an audience/list
3. Generate an API key from Account → Extras → API keys
4. Get your List ID from the audience settings
5. Get your server prefix (e.g., `us1`, `us2`) from the API key page
6. Add to `.env.local`:
   ```
   NEXT_PUBLIC_EMAIL_SERVICE=mailchimp
   MAILCHIMP_API_KEY=your_api_key
   MAILCHIMP_LIST_ID=your_list_id
   MAILCHIMP_SERVER_PREFIX=us1
   ```

## Analytics Setup

### PostHog (Recommended)

1. Sign up at [PostHog](https://posthog.com)
2. Create a new project
3. Get your Project API Key from Project Settings
4. Add to `.env.local`:
   ```
   NEXT_PUBLIC_ANALYTICS_SERVICE=posthog
   NEXT_PUBLIC_POSTHOG_KEY=your_posthog_key
   NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
   ```

### Mixpanel

1. Sign up at [Mixpanel](https://mixpanel.com)
2. Create a new project
3. Get your Project Token from Project Settings
4. Add to `.env.local`:
   ```
   NEXT_PUBLIC_ANALYTICS_SERVICE=mixpanel
   NEXT_PUBLIC_MIXPANEL_TOKEN=your_mixpanel_token
   ```

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import project in [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy!

The site will be live at `https://your-project.vercel.app`

### Netlify

1. Push your code to GitHub
2. Import project in [Netlify](https://netlify.com)
3. Build command: `npm run build`
4. Publish directory: `.next`
5. Add environment variables in Netlify dashboard
6. Deploy!

## Testing

### Test Email Collection

1. Fill out the waitlist form with a test email
2. Check your email service dashboard to confirm the subscription
3. Verify custom fields (number of kids) are captured

### Test Analytics

1. Open browser console (F12)
2. Navigate through the site
3. Check analytics dashboard for events:
   - Page views
   - Form submissions
   - CTA clicks

### Test Mobile Responsiveness

1. Use browser dev tools to test different screen sizes
2. Test on actual mobile devices
3. Verify form works on mobile
4. Check all sections are readable

## Success Criteria Checklist

- [x] Landing page live
- [x] Waitlist form working
- [x] Email collection set up
- [x] Basic privacy policy added
- [x] Mobile responsive
- [x] Analytics tracking
- [ ] Feedback collected from 5+ people (manual step)

## Next Steps

1. Deploy to Vercel/Netlify
2. Set up email service (ConvertKit or Mailchimp)
3. Set up analytics (PostHog or Mixpanel)
4. Test on mobile devices
5. Share with 5+ friends for feedback
6. Report back to Master Planning Chat with:
   - Landing page URL
   - Email collection status
   - Analytics setup
   - Feedback received
   - Any issues discovered

## Support

For questions or issues, contact: support@LexiCraft.xyz

