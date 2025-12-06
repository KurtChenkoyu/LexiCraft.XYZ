# Beta Payments Compliance Summary

**Status:** Quick Reference Guide  
**Last Updated:** January 2025

---

## Quick Answer: Can You Accept Payments During Beta?

**✅ YES** - You can accept payments during beta testing in Taiwan, with these requirements:

1. ✅ **7-Day Refund Mechanism** (Mandatory - Taiwan Consumer Protection Act)
2. ✅ **Beta Terms of Service** (Required - Legal protection)
3. ✅ **Business Registration** (Required - For payment processing)
4. ✅ **Enhanced Beta Refund Policy** (Recommended - Better than required)

---

## Three Documents Created

### 1. Beta Terms of Service Template
**File:** `docs/BETA_TERMS_OF_SERVICE_TEMPLATE.md`

**What it includes:**
- Complete beta terms of service template
- Taiwan-specific legal requirements
- 7-day cooling-off period disclosure
- Enhanced beta refund policy
- Age of majority requirements (20 years)
- Parental consent provisions
- Limitation of liability clauses
- Beta disclaimers

**Next steps:**
- [ ] Fill in company information
- [ ] Review with Taiwan legal counsel
- [ ] Translate to Traditional Chinese (if needed)
- [ ] Add to website
- [ ] Require acceptance during signup

**Estimated legal review cost:** NT$50,000-100,000

---

### 2. Refund Mechanism Implementation Plan
**File:** `docs/REFUND_MECHANISM_IMPLEMENTATION_PLAN.md`

**What it includes:**
- Complete database schema for refunds
- API endpoint specifications
- Backend service implementation code
- Frontend component requirements
- Testing checklist
- Migration scripts
- Security considerations

**Implementation timeline:**
- Week 1: Database schema + API endpoints
- Week 2: Frontend components + testing
- Week 3: Integration testing + bug fixes
- Week 4: Deploy to beta

**Key features:**
- 7-day cooling-off period (mandatory)
- Full refund for unused deposits (beta policy)
- Partial refund for used deposits
- Stripe refund integration
- Refund history tracking

---

### 3. Taiwan Business Registration Research
**File:** `docs/TAIWAN_BUSINESS_REGISTRATION_RESEARCH.md`

**What it includes:**
- Company type options (Limited Company recommended)
- Complete registration process
- Cost breakdown (NT$257,300-350,000 one-time)
- Timeline (6-7 weeks)
- Ongoing compliance requirements
- Tax considerations
- Service provider recommendations

**Recommended approach:**
- **Company Type:** Limited Company (有限公司)
- **Capital:** NT$250,000-500,000
- **Timeline:** 6-7 weeks
- **Cost:** NT$257,300-350,000 one-time
- **Ongoing:** NT$13,000-43,000/year

**Alternative:** Use existing entity if available (faster, cheaper)

---

## Implementation Checklist

### Before Accepting Payments

#### Legal Requirements
- [ ] Register Taiwan business entity (or use existing)
- [ ] Draft beta terms of service (template provided)
- [ ] Review terms with Taiwan legal counsel
- [ ] Implement 7-day refund mechanism (plan provided)
- [ ] Set up privacy policy (PDPA compliant)
- [ ] Add beta disclaimers to UI

#### Technical Requirements
- [ ] Implement refund API endpoints
- [ ] Create refund database tables
- [ ] Build refund request UI
- [ ] Integrate Stripe refund functionality
- [ ] Set up refund tracking and reporting
- [ ] Test refund flow end-to-end

#### Business Requirements
- [ ] Set deposit limits (NT$1,000 max during beta)
- [ ] Configure Stripe with business information
- [ ] Set up business bank account
- [ ] Prepare customer support for refund requests
- [ ] Set up monitoring and alerts

---

## Cost Summary

### One-Time Costs

| Item | Cost (NT$) | Cost (USD) |
|------|------------|------------|
| Business registration | 257,300-350,000 | $8,200-11,200 |
| Legal review (terms) | 50,000-100,000 | $1,600-3,200 |
| Development (refunds) | 0 (DIY) or 100,000-200,000 | $0 or $3,200-6,400 |
| **Total** | **307,300-650,000** | **$9,800-20,800** |

### Ongoing Annual Costs

| Item | Cost (NT$) | Cost (USD) |
|------|------------|------------|
| Company maintenance | 13,000-43,000 | $400-1,400 |
| Legal/accounting | 30,000-100,000 | $1,000-3,200 |
| **Total** | **43,000-143,000** | **$1,400-4,600** |

---

## Timeline

### Option 1: Use Existing Entity (Fastest)

**Timeline: 1-2 weeks**
- Week 1: Update business scope (if needed)
- Week 1-2: Implement refund mechanism
- Week 2: Review terms, add to website
- Week 2: Start accepting payments

**Cost:** NT$1,000 (scope amendment) + development time

### Option 2: Register New Entity

**Timeline: 6-8 weeks**
- Week 1-2: Prepare registration documents
- Week 3-4: Submit registration, wait for approval
- Week 5-6: Complete tax registration, open bank account
- Week 7-8: Implement refund mechanism, review terms
- Week 8: Start accepting payments

**Cost:** NT$307,300-650,000

---

## Legal Requirements Summary

### Mandatory (Must Have)

1. **7-Day Cooling-Off Period**
   - Full refund within 7 days of deposit
   - Must be clearly disclosed
   - No questions asked

2. **Business Registration**
   - Taiwan entity required for payment processing
   - Can use existing entity or register new

3. **Terms of Service**
   - Must include refund policy
   - Must include beta disclaimers
   - Must comply with Consumer Protection Act

4. **Privacy Policy**
   - Must comply with PDPA
   - Must include data collection disclosure
   - Parental consent for children under 18

### Recommended (Best Practice)

1. **Enhanced Beta Refund Policy**
   - Full refund for unused deposits anytime during beta
   - Better than legal minimum
   - Builds trust with beta users

2. **Clear Beta Disclaimers**
   - Service may have bugs
   - Features may change
   - No guarantee of uptime

3. **Limited Deposit Amounts**
   - NT$1,000 max during beta
   - Reduces risk
   - Easier refund processing

---

## Risk Mitigation

### Low Risk (If Done Correctly)

✅ Limited beta scope (50-100 families)  
✅ Enhanced refund policy (better than required)  
✅ Clear beta disclaimers  
✅ Using licensed payment processor (Stripe)  
✅ Staying under NT$2B threshold (no EPI registration needed)

### Medium Risk

⚠️ Not having proper terms of service  
⚠️ Not implementing 7-day refunds  
⚠️ Not monitoring transaction volumes

### High Risk (Avoid)

❌ Accepting large deposits during beta  
❌ Not having business registration  
❌ Ignoring consumer protection laws  
❌ Not having refund mechanism

---

## Next Steps

### Immediate (This Week)

1. **Review documents:**
   - Read beta terms of service template
   - Review refund implementation plan
   - Review business registration research

2. **Decide on approach:**
   - Use existing entity or register new?
   - DIY or use professional service?
   - Timeline and budget constraints?

3. **Start implementation:**
   - Begin refund mechanism development
   - Prepare terms of service for legal review
   - Start business registration (if needed)

### Short-Term (1-2 Weeks)

1. **Complete legal setup:**
   - Finalize terms of service with legal counsel
   - Complete business registration (if new entity)
   - Set up business bank account

2. **Complete technical setup:**
   - Implement refund API endpoints
   - Build refund UI components
   - Test refund flow

3. **Prepare for beta:**
   - Add beta disclaimers to website
   - Set deposit limits
   - Prepare customer support

### Before Beta Launch

- [ ] Terms of service live on website
- [ ] Refund mechanism fully tested
- [ ] Business registration complete
- [ ] Stripe configured with business info
- [ ] Beta disclaimers visible
- [ ] Customer support ready
- [ ] Monitoring and alerts set up

---

## Support Resources

### Documents Created

1. **Beta Terms of Service Template**
   - Location: `docs/BETA_TERMS_OF_SERVICE_TEMPLATE.md`
   - Status: Ready for legal review

2. **Refund Mechanism Implementation Plan**
   - Location: `docs/REFUND_MECHANISM_IMPLEMENTATION_PLAN.md`
   - Status: Ready for implementation

3. **Taiwan Business Registration Research**
   - Location: `docs/TAIWAN_BUSINESS_REGISTRATION_RESEARCH.md`
   - Status: Complete research guide

### Related Documents

- `docs/13-legal-analysis-taiwan.md` - Full legal analysis
- `docs/14-legal-quick-reference-taiwan.md` - Quick legal reference
- `WITHDRAWAL_IMPLEMENTATION_GUIDE.md` - Withdrawal system guide

---

## Questions?

**For legal questions:**
- Consult Taiwan legal counsel
- Review `docs/13-legal-analysis-taiwan.md`

**For technical questions:**
- Review refund implementation plan
- Check existing codebase for patterns

**For business registration:**
- Review business registration research document
- Contact MOEA or service provider

---

## Summary

**You CAN accept payments during beta testing** if you:

1. ✅ Implement 7-day refund mechanism (mandatory)
2. ✅ Have beta terms of service (required)
3. ✅ Register business entity (required)
4. ✅ Add beta disclaimers (recommended)
5. ✅ Limit deposit amounts (recommended)

**All three documents are ready for use:**
- Terms of service template (needs legal review)
- Refund implementation plan (ready to code)
- Business registration guide (complete research)

**Estimated timeline:** 1-2 weeks (with existing entity) or 6-8 weeks (new entity)

**Estimated cost:** NT$307,300-650,000 one-time + NT$43,000-143,000/year

---

**Last Updated:** January 2025  
**Status:** All documents complete and ready for implementation

