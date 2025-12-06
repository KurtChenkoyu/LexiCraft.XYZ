# Deployment Architecture: Cloud-Based MVP

**Date**: January 2025  
**Decision**: Cloud-based SaaS (not standalone app)

---

## Overview

The MVP is a **cloud-based web application** that requires internet connectivity. Users access the platform through web browsers (desktop, tablet, mobile).

**Key Decision**: Internet required for MVP. Offline features can be added in Phase 2 if needed.

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         Users (Web Browsers)             │
│    (Parents + Kids access via browser)   │
│         Internet Connection Required     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      Frontend: Next.js on Vercel         │
│         (Cloud-hosted, free tier)       │
│         - Static site generation         │
│         - Serverless functions          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      Backend: FastAPI on Vercel          │
│      (or Supabase Edge Functions)       │
│         - API endpoints                 │
│         - Authentication                │
└─────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────┐
│   Neo4j      │    │  PostgreSQL  │
│   Aura Free  │    │  (Supabase)  │
│   (Cloud)    │    │  (Cloud)     │
└──────────────┘    └──────────────┘
```

---

## Deployment Stack (MVP)

| Component | Service | Type | Cost (MVP) | Notes |
|-----------|---------|------|------------|-------|
| **Frontend** | Vercel | Cloud (SaaS) | Free | Next.js hosting |
| **Backend API** | Vercel Serverless | Cloud (SaaS) | Free | FastAPI or Edge Functions |
| **Neo4j** | Neo4j Aura Free | Cloud (SaaS) | Free | 50K nodes, 175K relationships |
| **PostgreSQL** | Supabase Free | Cloud (SaaS) | Free | 500MB database |
| **Payments** | Stripe | Cloud (SaaS) | 2.9% + $0.30 | Transaction fees |
| **Email** | Resend | Cloud (SaaS) | Free tier | Transactional emails |
| **Analytics** | PostHog | Cloud (SaaS) | Free tier | User tracking |
| **CDN** | Vercel Edge | Cloud (SaaS) | Free | Global CDN included |

**Total MVP Cost**: ~$0-50/month (mostly Stripe transaction fees)

---

## Neo4j Deployment Options

### Option 1: Neo4j Aura Free (Recommended for MVP)

**Type**: Cloud-managed (SaaS)  
**Cost**: Free  
**Limits**: 50K nodes, 175K relationships  
**Setup Time**: ~5 minutes  
**Maintenance**: None (fully managed)  
**Scalability**: Upgrade to Professional ($65/month) when needed

**Best for**: MVP launch (Weeks 1-4)

**Setup**:
1. Sign up at https://neo4j.com/cloud/aura/
2. Create free database instance
3. Get connection URI and credentials
4. Connect from backend API

### Option 2: Self-Hosted Neo4j (Future)

**Type**: Self-hosted (Docker/VPS)  
**Cost**: $0-20/month (VPS)  
**Setup Time**: 2-4 hours  
**Maintenance**: You manage updates, backups, monitoring  
**Scalability**: Full control

**Best for**: Phase 2+ if you need more control or cost optimization

---

## Internet Requirement

### Why Cloud-Based?

**Advantages**:
- ✅ **Faster to launch**: No server setup required
- ✅ **Lower cost**: Free tiers cover MVP needs
- ✅ **Auto-scaling**: Handles traffic spikes automatically
- ✅ **Global access**: Users access from anywhere
- ✅ **No maintenance**: Managed services handle updates
- ✅ **Mobile-friendly**: Works on any device with browser

**Disadvantages**:
- ⚠️ **Internet required**: Cannot work offline
- ⚠️ **Potential distractions**: Kids may open other tabs/apps
- ⚠️ **Connection issues**: Interruptions can disrupt learning

### Distraction Mitigation Strategies (MVP)

**1. Focused Learning Mode** (Simple to implement)
- Full-screen mode for learning sessions
- Session timer (20 minutes max)
- Progress tracking to encourage completion
- "Focus mode" button that hides browser UI

**2. Parental Controls** (Simple to implement)
- Parent sets daily time limits (2 hours/day)
- Parent can lock device to app (OS-level, not app-level)
- Notifications when session ends
- Parent dashboard with usage tracking

**3. Offline Features** (Phase 2 - Not MVP)
- Download word lists for offline learning
- Offline flashcards
- Sync progress when online
- More complex, not needed for MVP validation

**MVP Recommendation**: Accept internet requirement, add simple distraction controls (full-screen mode, session timers).

---

## Why Not Standalone App?

**Standalone app would require**:
- ❌ Desktop app development (Electron, etc.)
- ❌ Local database setup (complex)
- ❌ Distribution (App Store, etc.)
- ❌ Updates and maintenance
- ❌ Not suitable for MVP timeline

**Cloud-based is better for MVP**:
- ✅ Faster to build (web technologies)
- ✅ Easier to update (no app store approval)
- ✅ Works on all devices (browser-based)
- ✅ Lower cost (free tiers available)

---

## Migration Path

### Phase 1 (MVP): Cloud-Managed
```
Neo4j Aura Free
Supabase Free
Vercel Free
```

### Phase 2 (Growth): Still Cloud, More Control
```
Neo4j Aura Professional ($65/month)
Supabase Pro ($25/month)
Vercel Pro ($20/month)
```

### Phase 3 (Scale): Self-Hosted Option
```
Self-hosted Neo4j (Docker on AWS/GCP)
Self-hosted PostgreSQL (RDS)
Kubernetes cluster
```

---

## Setup Instructions

### 1. Neo4j Aura Setup

```bash
# 1. Sign up at https://neo4j.com/cloud/aura/
# 2. Create free database
# 3. Get connection details:
#    - URI: neo4j+s://xxxxx.databases.neo4j.io
#    - Username: neo4j
#    - Password: [generated]

# 4. Test connection
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j+s://xxxxx.databases.neo4j.io",
    auth=("neo4j", "password")
)

with driver.session() as session:
    result = session.run("RETURN 1 as test")
    print(result.single()["test"])  # Should print 1
```

### 2. Supabase Setup

```bash
# 1. Sign up at https://supabase.com
# 2. Create new project
# 3. Get connection string from Settings > Database
# 4. Set up environment variables
```

### 3. Vercel Setup

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel

# 3. Set environment variables in Vercel dashboard
```

---

## Security Considerations

### Data Protection
- ✅ HTTPS everywhere (Vercel handles this)
- ✅ Encrypted database connections (Neo4j Aura, Supabase)
- ✅ Secure API authentication (JWT tokens)
- ✅ Environment variables for secrets

### Compliance
- ✅ PDPA compliance (Taiwan) - see legal docs
- ✅ Parental consent for children
- ✅ Data retention policies
- ✅ Right to deletion

---

## Monitoring & Analytics

### PostHog Setup (Free Tier)
- User tracking
- Event analytics
- Conversion funnels
- Retention analysis

### Vercel Analytics
- Page views
- Performance metrics
- Error tracking

---

## Cost Breakdown (MVP)

| Service | Cost | Notes |
|---------|------|-------|
| Vercel | $0 | Free tier sufficient |
| Neo4j Aura | $0 | Free tier (50K nodes) |
| Supabase | $0 | Free tier (500MB) |
| Resend | $0 | Free tier (3K emails/month) |
| PostHog | $0 | Free tier (1M events/month) |
| Stripe | 2.9% + $0.30 | Per transaction |
| **Total** | **~$0-50/month** | Mostly Stripe fees |

---

## Next Steps

1. ✅ Set up Neo4j Aura Free account
2. ✅ Set up Supabase project
3. ✅ Deploy Next.js app to Vercel
4. ✅ Configure environment variables
5. ✅ Test all connections
6. ✅ Set up monitoring (PostHog)

---

**Last Updated**: January 2025

