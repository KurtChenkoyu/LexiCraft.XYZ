# Legal Analysis: LexiCraft Platform - Taiwan

## Executive Summary

**Critical Legal Issues for Taiwan Operations:**

1. ⚠️ **Age of Majority**: 20 years (not 18) - requires parental consent for all users under 20
2. ⚠️ **Reward Limits**: Strict FTC limits on promotional prizes based on company sales
3. ⚠️ **Tax Reporting**: Rewards ≥NT$1,000 require ID; ≥NT$20,010 require 10% lottery tax prepayment
4. ⚠️ **Virtual Currency Restrictions**: Robux/V-Bucks may violate platform ToS if transferred externally
5. ⚠️ **Deposit/Refund Rights**: Consumer Protection Act requires 7-day refund rights
6. ⚠️ **Data Privacy**: PDPA requires parental consent for children under 18

**Recommendation**: Engage Taiwan legal counsel before launch. Consider gift card model instead of direct currency transfer.

---

## 1. Age of Majority & Contractual Capacity

### Legal Framework

**Age of Majority in Taiwan**: **20 years old** (not 18)

| Age Range | Legal Capacity | Requirements |
|-----------|---------------|--------------|
| Under 7 | No capacity | Cannot enter contracts |
| 7-20 | Limited capacity | Requires parental/guardian consent |
| 20+ | Full capacity | Can enter contracts independently |

### Implications for Your Platform

**Critical Requirements**:
- ✅ **Parental consent mandatory** for all users under 20
- ✅ **Parent must be the contracting party** (not the child)
- ✅ **All deposits must be made by parent** (child cannot legally deposit)
- ✅ **Rewards to minors require guardian consent** for tax reporting

**Implementation**:
```
Parent Flow:
1. Parent creates account (legal entity)
2. Parent adds child (requires consent form)
3. Parent deposits funds (parent's payment method)
4. Child earns points (but parent owns the account)
5. Parent approves reward withdrawal
```

**Legal Risk**: ⚠️ **HIGH** - If child enters contract without parental consent, contract may be voidable.

---

## 2. Promotional Rewards & Fair Trade Commission (FTC) Regulations

### Prize Value Limits

**Based on Company's Annual Sales in Taiwan**:

| Annual Sales | Max Annual Prize Value | Max Individual Prize |
|--------------|------------------------|---------------------|
| < NT$750M | NT$150M (or 20% of sales) | NT$5M |
| NT$750M - NT$3B | 20% of sales | NT$5M |
| > NT$3B | NT$600M | NT$5M |

**For Startups** (likely < NT$750M):
- Maximum annual prizes: **NT$150M** (~$4.6M USD)
- Maximum single prize: **NT$5M** (~$150K USD)

### Promotional Gift Limits

When offering rewards as part of service:

| Service Price | Max Gift Value |
|---------------|----------------|
| ≥ NT$100 | 50% of service price |
| < NT$100 | NT$50 |

**Example**:
- Parent deposits NT$500 → Max reward value = NT$250
- Parent deposits NT$1,000 → Max reward value = NT$500

### Disclosure Requirements

- ✅ Must disclose prize value and terms clearly
- ✅ Must disclose odds (if applicable)
- ✅ Must not mislead consumers

**Legal Risk**: ⚠️ **MEDIUM** - Violations can result in FTC fines.

---

## 3. Tax Implications for Rewards

### Tax Reporting Thresholds

| Reward Value (Annual) | Requirement |
|-----------------------|-------------|
| < NT$1,000 | No reporting |
| NT$1,000 - NT$20,009 | ID required for tax reporting |
| ≥ NT$20,010 | 10% lottery tax prepayment + ID |

### For Minors

If reward recipient is under 20:
- ✅ **Household Registration Transcript** required
- ✅ **Written consent from legal guardian** required
- ✅ Guardian must handle tax prepayment

### Implementation Requirements

**Platform Must**:
1. Track annual reward value per user
2. Collect ID when threshold reached (NT$1,000)
3. Withhold 10% tax for rewards ≥NT$20,010
4. File tax reports with Taiwan tax authority
5. Obtain guardian consent for minors

**Legal Risk**: ⚠️ **HIGH** - Tax non-compliance can result in penalties and criminal charges.

---

## 4. Virtual Currency & Gaming Platform Integration

> **⚠️ NOT FOR MVP** - This section explains why we're NOT using game currency for MVP.  
> MVP uses direct cash withdrawal. See `docs/10-mvp-validation-strategy.md` for MVP scope.

### Robux/V-Bucks Transfer Restrictions

**Critical Issue**: Most gaming platforms **prohibit external transfers** of virtual currency.  
**This is why we're using direct cash withdrawal for MVP instead.**

**Roblox Terms of Service**:
- ❌ Person-to-person Robux transfers are restricted
- ❌ Robux cannot be transferred outside Roblox ecosystem
- ❌ External rewards may violate ToS

**Fortnite V-Bucks**:
- ❌ V-Bucks are non-transferable
- ❌ Cannot be gifted externally (only within Epic ecosystem)

### Legal Workaround: Gift Cards

**Recommended Approach**:
- ✅ Purchase Robux/V-Bucks **gift cards** (retail)
- ✅ Deliver gift card codes to parents
- ✅ Parents redeem codes in child's gaming account
- ✅ Complies with platform ToS

**Alternative**: Build **Roblox-native experience** (see docs/08-robux-integration-analysis.md)

**Legal Risk**: ⚠️ **HIGH** - Violating platform ToS can result in account bans and legal action.

---

## 5. Consumer Protection Act & Deposit Regulations

### 7-Day Cooling-Off Period

**Consumer Protection Act Requirements**:
- ✅ Consumers can **terminate contract within 7 days** without cause
- ✅ **Full refund** required for unused points/value
- ✅ Must be clearly disclosed in terms

**For Your Platform**:
```
Parent deposits NT$1,000
Day 1-7: Can request full refund (even if child started learning)
Day 8+: Refund policy applies (see terms)
```

### Service Fee Changes

- ✅ Must announce **30 days in advance**
- ✅ Cannot apply retroactively

### Standard Contract Requirements

Online game/service contracts must include:
- ✅ Clear refund policy
- ✅ Service termination rights
- ✅ Dispute resolution process
- ✅ Consumer protection provisions

**Legal Risk**: ⚠️ **MEDIUM** - Non-compliance can result in consumer complaints and regulatory action.

---

## 6. Personal Data Protection Act (PDPA)

### Data Collection Requirements

**For Minors (Under 18)**:
- ✅ **Parental consent required** for data collection
- ✅ Must disclose purpose of data collection
- ✅ Must obtain consent before processing
- ✅ Data minimization (collect only necessary data)

**For Children Under 7**:
- ✅ **Only parent/guardian can provide consent**
- ✅ Child cannot consent independently

**For Ages 7-18**:
- ✅ **Both minor and parent consent** required

### Data Protection Requirements

- ✅ Implement security measures
- ✅ Provide data access rights
- ✅ Allow data deletion requests
- ✅ Notify of data breaches
- ✅ Appoint data protection officer (if required)

**Penalties**: 
- Fines up to **NT$20M** (~$600K USD)
- Criminal penalties for serious violations

**Legal Risk**: ⚠️ **HIGH** - PDPA violations can result in significant fines.

---

## 7. Protection of Children and Youths Welfare and Rights Act

### Content Rating Requirements

**Game Software Rating Categories**:
- **General Audience**: All ages
- **Parent Protection (6+)**: Ages 6+
- **Parental Guidance 12**: Ages 12+
- **Parental Guidance 15**: Ages 15+
- **Restricted (18+)**: Ages 18+

**Your Platform**:
- Likely rated: **Parent Protection (6+)** or **General Audience**
- Must display rating clearly
- Must restrict access based on age

### Harmful Content Restrictions

- ✅ Must prevent access to harmful content
- ✅ Must implement age verification
- ✅ Must comply with NCC (National Communications Commission) guidelines

**Legal Risk**: ⚠️ **MEDIUM** - Non-compliance can result in content removal and fines.

---

## 8. Screen Time Regulations

### Legal Requirements

**Taiwan Law**:
- Parents can be **fined** if children's screen time is excessive
- Must promote healthy usage patterns
- No specific time limits defined (case-by-case)

**For Your Platform**:
- ✅ Implement usage time limits
- ✅ Provide parental controls
- ✅ Encourage breaks
- ✅ Monitor for excessive usage

**Legal Risk**: ⚠️ **LOW** - Risk is on parents, but platform should promote healthy usage.

---

## 9. Money Transmission & Escrow Regulations

### Third-Party Payment Services

**Taiwan Regulations**:
- Third-party payment services require **licensing** from Financial Supervisory Commission (FSC)
- Escrow services may require **money transmission license**
- Foreign companies may need **local entity** or partnership

### Options for Your Platform

**Option 1: Use Licensed Payment Processor**
- ✅ Stripe (if available in Taiwan)
- ✅ Local payment processors (requires Taiwan entity)
- ✅ Third-party escrow service (licensed)

**Option 2: Direct Bank Account**
- ⚠️ May require money transmission license
- ⚠️ Complex compliance requirements

**Option 3: Gift Card Model** (Recommended)
- ✅ Purchase gift cards with deposits
- ✅ Hold gift cards until earned
- ✅ Deliver codes when points earned
- ✅ Simpler compliance (retail purchase, not money transmission)

**Legal Risk**: ⚠️ **HIGH** - Operating unlicensed money transmission is illegal.

---

## 10. Educational Service Regulations

### Licensing Requirements

**Ministry of Education Guidelines**:
- Educational content should align with national standards
- No specific licensing for online learning platforms (yet)
- May require business registration

### Business Registration

- ✅ Must register business in Taiwan
- ✅ May need specific business category
- ✅ Tax registration required

**Legal Risk**: ⚠️ **LOW-MEDIUM** - Regulations evolving, but basic business registration required.

---

## 11. Anti-Fraud & Security Requirements

### Digital Credit Fraud Prevention

**Regulatory Expectations**:
- ✅ Implement identity verification
- ✅ Monitor unusual transaction patterns
- ✅ Prevent account takeovers
- ✅ Secure payment processing

**Legal Risk**: ⚠️ **MEDIUM** - Failure to prevent fraud can result in liability.

---

## 12. Intellectual Property

### Content Licensing

- ✅ Ensure all educational content is licensed or original
- ✅ Do not infringe on copyrights
- ✅ Respect trademark rights (Roblox, Fortnite, etc.)

**Legal Risk**: ⚠️ **MEDIUM** - IP violations can result in lawsuits.

---

## Recommended Legal Structure

### Entity Setup Options

#### Option 1: Use Existing Cram School Entity (Recommended for MVP)

**Advantages**:
- ✅ Already registered - no new registration needed
- ✅ Educational business - aligns with learning platform
- ✅ Existing bank account - can use for payments
- ✅ Faster to start - no waiting for registration
- ✅ Lower cost - no new entity fees

**Considerations**:
- ⚠️ Check if business scope covers online learning platforms
- ⚠️ May need to track revenue separately (cram school vs platform)
- ⚠️ Consider separate entity later if successful (cleaner for investors)

**Best for**: MVP validation (Weeks 1-4)

#### Option 2: Register New Taiwan Company

**When to use**:
- If existing entity doesn't cover business scope
- If you want clean separation from cram school
- If preparing for investor funding (cleaner cap table)

**Requirements**:
- Register as foreign company or local entity
- Obtain business license
- Register for taxes
- Cost: NT$50,000-100,000 (~$1,500-3,000 USD)

**Best for**: Phase 2+ (after validation)

### Landing Page (Waitlist Only)

**✅ No company registration needed for waitlist collection**

**Requirements**:
- Basic privacy policy (what data collected, how used, opt-out)
- Email service compliance (ConvertKit/Mailchimp handle this)
- Can use existing cram school entity name or personal name

**When company needed**: Only when accepting payments (Week 2+)

### Payment Processing Setup

1. **Stripe Account**
   - Use existing cram school entity (for MVP)
   - Or register new entity (if needed)
   - Stripe available in Taiwan (may require Taiwan entity)

2. **Bank Account**
   - Use existing cram school bank account (for MVP)
   - Or open new account for platform

3. **Legal Counsel**
   - Engage Taiwan law firm
   - Review all terms and policies
   - Ongoing compliance support

### Terms of Service Requirements

**Must Include**:
- ✅ Age restrictions (20+ for independent use)
- ✅ Parental consent requirements
- ✅ 7-day refund policy
- ✅ Tax reporting obligations
- ✅ Reward limits and terms
- ✅ Data privacy policy (PDPA compliant)
- ✅ Dispute resolution
- ✅ Service termination rights

### Privacy Policy Requirements

**Must Include**:
- ✅ Data collection purposes
- ✅ Parental consent mechanisms
- ✅ Data retention policies
- ✅ User rights (access, deletion)
- ✅ Security measures
- ✅ Third-party disclosures

---

## Compliance Checklist

### Pre-Launch (Landing Page - Week 1)

- [ ] Set up landing page (Framer/Carrd)
- [ ] Add basic privacy policy (waitlist collection)
- [ ] Set up email service (ConvertKit/Mailchimp)
- [ ] Use existing cram school entity name (or personal name)
- [ ] **No company registration needed for waitlist only**

### Pre-Launch (MVP - Week 2+)

- [ ] Use existing cram school entity OR register new Taiwan business entity
- [ ] Obtain business license (if new entity)
- [ ] Open bank account or set up payment processor (Stripe)
- [ ] Engage Taiwan legal counsel
- [ ] Draft Terms of Service (Taiwan law compliant)
- [ ] Draft Privacy Policy (PDPA compliant)
- [ ] Implement parental consent system
- [ ] Set up tax reporting system
- [ ] Design reward limits (FTC compliant)
- [ ] Create refund policy (7-day cooling-off)
- [ ] Implement age verification
- [ ] Set up data protection measures

### Ongoing

- [ ] Track annual reward values per user
- [ ] Collect ID for rewards ≥NT$1,000
- [ ] Withhold tax for rewards ≥NT$20,010
- [ ] File tax reports
- [ ] Monitor FTC compliance
- [ ] Update terms as regulations change
- [ ] Conduct regular security audits
- [ ] Maintain PDPA compliance

---

## Cost Estimates

| Item | Estimated Cost |
|------|----------------|
| Taiwan company registration | NT$50,000-100,000 |
| Legal counsel (initial setup) | NT$200,000-500,000 |
| Legal counsel (ongoing) | NT$50,000-100,000/month |
| Tax compliance setup | NT$50,000-100,000 |
| Payment processor setup | Varies |
| **Total First Year** | **NT$1M-2M** (~$30K-60K USD) |

---

## Key Recommendations

### 1. Start with Gift Card Model

**Why**: Avoids money transmission licensing and platform ToS violations.

**How**:
- Parent deposits → Platform purchases gift cards
- Hold gift cards until child earns points
- Deliver gift card codes to parent
- Parent redeems in child's gaming account

### 2. Parent as Account Owner

**Why**: Complies with age of majority (20) and contractual capacity.

**How**:
- Parent creates account (legal entity)
- Parent adds child (with consent)
- All deposits/withdrawals through parent account
- Child uses platform but parent owns account

### 3. Conservative Reward Limits

**Why**: FTC limits based on sales (startup = NT$150M annual max).

**How**:
- Start with small deposits (NT$500-1,000)
- Limit individual rewards to NT$5,000-10,000
- Track annual totals per user
- Scale as sales increase

### 4. Tax Compliance from Day 1

**Why**: Tax violations can result in criminal penalties.

**How**:
- Collect ID for all users (even if <NT$1,000 threshold)
- Set up tax withholding system
- File reports quarterly
- Engage tax advisor

### 5. Engage Legal Counsel Early

**Why**: Taiwan regulations are complex and evolving.

**How**:
- Find Taiwan law firm with fintech/EdTech experience
- Review business model before launch
- Draft compliant terms and policies
- Ongoing compliance support

---

## Red Flags to Avoid

1. ❌ **Direct Robux/V-Bucks transfer** → Violates platform ToS
2. ❌ **Child as account owner** → Violates age of majority
3. ❌ **No parental consent** → Violates PDPA and contract law
4. ❌ **Rewards >NT$5M** → Violates FTC limits
5. ❌ **No tax reporting** → Criminal penalties
6. ❌ **No 7-day refund** → Violates Consumer Protection Act
7. ❌ **Unlicensed money transmission** → Illegal

---

## Next Steps

1. **Engage Taiwan Legal Counsel** (Priority 1)
   - Review business model
   - Draft compliant terms
   - Set up entity structure

2. **Choose Business Model**
   - Gift card model (recommended)
   - Or Roblox-native experience

3. **Set Up Compliance Systems**
   - Parental consent
   - Tax reporting
   - Reward tracking
   - Refund processing

4. **Test with Small Beta**
   - 10-20 families
   - Monitor compliance
   - Adjust as needed

---

## Resources

- **Fair Trade Commission**: https://www.ftc.gov.tw/
- **Personal Data Protection Commission**: https://www.pdpc.gov.tw/
- **Ministry of Education**: https://www.edu.tw/
- **Financial Supervisory Commission**: https://www.fsc.gov.tw/

---

## Disclaimer

**This document is for informational purposes only and does not constitute legal advice. You must engage qualified Taiwan legal counsel before launching your platform in Taiwan.**

---

**Last Updated**: January 2025
**Next Review**: Q2 2025 (regulations may change)

