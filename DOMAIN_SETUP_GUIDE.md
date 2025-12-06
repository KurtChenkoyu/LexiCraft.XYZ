# lexicraft.xyz Domain Setup Guide

**Status:** ✅ Domain Purchased  
**Date:** January 2025

---

## 🎯 Quick Setup Checklist

- [ ] Connect domain to Vercel (Frontend)
- [ ] Set up DNS records
- [ ] Configure SSL (automatic with Vercel)
- [ ] Set up API subdomain (if using Railway backend)
- [ ] Update environment variables
- [ ] Test domain access

---

## Step 1: Connect Domain to Vercel (Frontend)

### 1.1 Add Domain in Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your **landing-page** project
3. Go to **Settings** → **Domains**
4. Click **"Add Domain"**
5. Enter: `lexicraft.xyz`
6. Click **"Add"**

### 1.2 Configure DNS (If using Cloudflare)

Vercel will show you DNS records to add. If you registered with Cloudflare:

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your domain: `lexicraft.xyz`
3. Go to **DNS** → **Records**
4. Add the records Vercel provides:

**For root domain:**
```
Type: A
Name: @
Content: 76.76.21.21 (or Vercel's IP)
Proxy: ✅ (Orange cloud - enabled)
```

**For www subdomain:**
```
Type: CNAME
Name: www
Target: cname.vercel-dns.com
Proxy: ✅ (Orange cloud - enabled)
```

### 1.3 Wait for DNS Propagation

- DNS changes take 5-60 minutes
- Vercel will automatically provision SSL certificate
- You'll see "Valid Configuration" when ready

---

## Step 2: Set Up API Subdomain (Backend on Railway)

### 2.1 Get Railway Domain

1. Go to [Railway Dashboard](https://railway.app)
2. Select your backend service
3. Go to **Settings** → **Networking**
4. Copy your Railway domain: `your-app.railway.app`

### 2.2 Add API Subdomain in Cloudflare

1. Go to Cloudflare Dashboard → DNS → Records
2. Add CNAME record:

```
Type: CNAME
Name: api
Target: your-app.railway.app
Proxy: ❌ (Gray cloud - DNS only, no proxy)
TTL: Auto
```

**Important:** Use **DNS only** (gray cloud) for API subdomain, not proxy. Railway handles SSL.

### 2.3 Update Backend Environment Variables

In Railway dashboard, add:

```
DOMAIN=lexicraft.xyz
API_DOMAIN=api.lexicraft.xyz
```

---

## Step 3: Update Frontend Environment Variables

### 3.1 Update Vercel Environment Variables

Go to Vercel → Settings → Environment Variables, add/update:

```bash
# Domain Configuration
NEXT_PUBLIC_DOMAIN=lexicraft.xyz
NEXT_PUBLIC_API_URL=https://api.lexicraft.xyz

# Existing variables (keep these)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3.2 Update Stripe Webhook URL

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
2. Edit your webhook endpoint
3. Update URL to: `https://lexicraft.xyz/api/webhooks/stripe`
4. Save changes

---

## Step 4: Update Codebase References

### 4.1 Update API Client Configuration

Check these files and update API URLs:

- `landing-page/services/surveyApi.ts`
- `landing-page/components/survey/api.ts`
- Any hardcoded localhost URLs

**Before:**
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

**After:**
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.lexicraft.xyz'
```

### 4.2 Update Email Templates

If you have email templates, update domain references:
- Support email: `support@lexicraft.xyz`
- No-reply email: `noreply@lexicraft.xyz`

---

## Step 5: Test Everything

### 5.1 Test Frontend

```bash
# Visit your site
https://lexicraft.xyz
https://www.lexicraft.xyz

# Check SSL
curl -I https://lexicraft.xyz
# Should return: HTTP/2 200
```

### 5.2 Test API

```bash
# Test API health endpoint
curl https://api.lexicraft.xyz/health

# Should return:
# {"status":"ok","version":"7.1","service":"lexicraft.xyz Survey API"}
```

### 5.3 Test Stripe Webhook

1. Go to Stripe Dashboard → Webhooks
2. Click "Send test webhook"
3. Verify it reaches: `https://lexicraft.xyz/api/webhooks/stripe`

---

## Step 6: DNS Records Summary

### Complete DNS Configuration (Cloudflare)

```
# Root domain → Vercel
Type: A
Name: @
Content: 76.76.21.21
Proxy: ✅

# www → Vercel
Type: CNAME
Name: www
Target: cname.vercel-dns.com
Proxy: ✅

# API → Railway
Type: CNAME
Name: api
Target: your-app.railway.app
Proxy: ❌ (DNS only)

# Email (if needed)
Type: MX
Name: @
Priority: 10
Target: mail.lexicraft.xyz
```

---

## Troubleshooting

### Domain Not Resolving

1. **Check DNS propagation (Online Tools):**
   - **DNS Checker**: https://dnschecker.org/#A/lexicraft.xyz
   - **WhatsMyDNS**: https://www.whatsmydns.net/#A/lexicraft.xyz
   - **IntoDNS**: https://intodns.com/lexicraft.xyz
   
   These tools show DNS propagation status across multiple global locations.

2. **Command Line Tools:**
   ```bash
   # macOS/Linux
   dig lexicraft.xyz
   nslookup lexicraft.xyz
   
   # Check specific record type
   dig A lexicraft.xyz
   dig CNAME www.lexicraft.xyz
   ```

3. **Wait 5-60 minutes** for DNS to propagate globally

4. **Clear DNS cache:**
   ```bash
   # macOS
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   
   # Windows
   ipconfig /flushdns
   
   # Linux
   sudo systemd-resolve --flush-caches
   ```

### SSL Certificate Issues

- Vercel automatically provisions SSL (Let's Encrypt)
- Takes 5-10 minutes after DNS is configured
- Check Vercel dashboard → Domains → SSL status

### API Not Accessible

1. **Check Railway deployment:**
   - Ensure backend is running
   - Check Railway logs for errors

2. **Verify CNAME record:**
   - API subdomain should use **DNS only** (gray cloud)
   - Not proxied through Cloudflare

3. **Check CORS settings:**
   - Update backend CORS to allow `lexicraft.xyz`

---

## Next Steps

1. ✅ Domain connected to Vercel
2. ✅ SSL certificate active
3. ✅ API subdomain configured
4. ⏭️ Set up email (optional - Google Workspace, Zoho, etc.)
5. ⏭️ Configure analytics (PostHog, Google Analytics)
6. ⏭️ Set up monitoring (Uptime monitoring)

---

## Cost Summary

| Service | Cost (Annual) |
|---------|---------------|
| Domain (lexicraft.xyz) | NT$320-500 |
| DNS/CDN (Cloudflare) | Free |
| SSL (Vercel) | Free |
| **Total** | **NT$320-500/year** |

---

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Check Railway deployment logs
3. Check Cloudflare DNS logs
4. Verify environment variables are set correctly

**Useful Links:**
- [Vercel Domains Docs](https://vercel.com/docs/concepts/projects/domains)
- [Cloudflare DNS Docs](https://developers.cloudflare.com/dns/)
- [Railway Networking Docs](https://docs.railway.app/networking/domains)

