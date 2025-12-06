# Project Overview: lexicraft.xyz Learning Platform

**Terminology:** This document uses unified Block terminology. See [Terminology Glossary](./00-TERMINOLOGY.md) for definitions.

## Vision

**lexicraft.xyz** creates a platform where parents fund blocks for conversion, and children mine The Mine (vocabulary universe) to forge blocks, earning XP and (if funded) real money through a sophisticated, context-aware learning system.

**Brand:** lexicraft.xyz • 字塊所  
**Brand Story:** Complete learning journey from A to Z

**Economic Model:** Dual economy (XP always active, money requires funding). See [Economic Model Hypotheses](./31-economic-model-hypotheses.md) for details.

## Core Concept

### The Flow
1. **Parent funds** a block package (e.g., "Essential 2000" for NT$2,000)
2. **Child mines** The Mine (explores vocabulary universe) - always free
3. **Child forges** blocks (masters through spaced repetition) - earns XP
4. **Platform verifies** learning through context-dependent testing (Pickaxe quizzes)
5. **Funded blocks** can convert to money when mastered
6. **Child can withdraw** money from mastered funded blocks

### Key Innovation: The Mine (Knowledge Graph)

Unlike simple word-count systems, we use **The Mine** (Neo4j knowledge graph) that understands:
- Blocks have multiple meanings in different contexts
- Phrases/idioms change block meanings
- Frequency matters (common vs. rare usage)
- Relationships matter (prefixes, suffixes, block families)
- Register matters (formal vs. informal)
- **Dynamic value** - blocks increase in value with connections

This enables:
- **Tiered base XP** (complexity = higher base value)
- **Dynamic value scaling** (connections increase value)
- **Rich gamification** (mining, forging, discovery, pattern recognition)
- **Superior verification** (context-dependent testing)
- **Higher revenue potential** (85%+ increase if all blocks funded)

## Business Model

### Block Package Tiers (For Funding)
- **Starter 500**: NT$500 (500 blocks)
- **Essential 2000**: NT$2,000 (2,000 blocks)
- **Academic 5000**: NT$4,500 (5,000 blocks)
- **Complete 10000**: NT$8,000 (10,000 blocks)
- **Elite (All)**: NT$15,000 (all blocks)

**Note:** Kids can mine and forge blocks without funding (XP economy always active). Funding only enables money conversion.

### Earning Potential (If All Blocks Funded)
- **Simple model**: 5,000 blocks × NT$2 = NT$10,000
- **Complex model**: Tiered system = NT$18,500+ (85% increase)
- **With dynamic value**: Hub blocks earn more (connection bonuses)

### Platform Revenue
- 8-10% platform fee on point deposits
- Premium content subscriptions
- Relationship discovery bonuses
- Advanced verification services

## Technical Architecture

### Core Components
1. **The Mine** (Neo4j knowledge graph)
   - Pre-populated block relationships
   - Frequency data
   - Context information
   - Morphological patterns
   - Dynamic value calculation

2. **User Progress** (PostgreSQL)
   - Block mastery tracking
   - Context-specific knowledge
   - Relationship discoveries
   - Assessment history
   - FSRS spaced repetition data

3. **Verification Engine** (Pickaxe)
   - Spaced repetition algorithms (FSRS)
   - Multi-modal assessment (MCQ)
   - Behavioral analytics
   - AI-powered contextual testing
   - Connection pathway explanations

4. **Financial Infrastructure**
   - Block funding management
   - Conversion tracking
   - Withdrawal processing
   - Escrow account management

### Technology Stack
- **Backend**: Python/FastAPI
- **Database**: Neo4j (The Mine - blocks), PostgreSQL (user progress)
- **AI/ML**: LLM for contextual testing, connection pathway explanations
- **Frontend**: React/Next.js (parent + child dashboards)
- **Payments**: Stripe/Plaid for escrow and transfers

## Competitive Advantages

1. **No direct competitor** - Unique dual economy model
2. **The Mine sophistication** - Context-aware, connection-based learning
3. **Dynamic block values** - Hub blocks more valuable, encourages exploration
4. **Platform-controlled verification** - Maintains integrity
5. **Tiered base XP system** - Rewards complexity
6. **Rich gamification** - Mining, forging, discovery, achievements
7. **Connection pathway engine** - Explains WHY blocks mean what they mean

## Success Metrics

### User Metrics
- Completion rate: 70%+ target
- Daily active users: 60%+ target
- Retention (90 days): 50%+ target
- Referral rate: 20%+ target

### Learning Metrics
- Average blocks forged: 3,000-5,000
- Retention rate: 80%+ after 60 days
- Relationship discoveries: 500+ per user
- Context mastery: 200+ contexts per user
- Connection discoveries: 10+ per session

### Financial Metrics (If Funded)
- Average package size: 2,000-5,000 blocks
- Platform fee: 8-10%
- Revenue per customer: NT$600-750 equivalent
- Lifetime value: NT$500+ equivalent (with renewals)
- Withdrawal rate: 20%+ monthly (target)

## Market Opportunity

- **TAM**: $227B global EdTech market
- **SAM**: $47B tutoring/private education
- **SOM**: $1B+ potential (1% of tutoring market)

## Next Steps

1. Review [Terminology Glossary](./00-TERMINOLOGY.md) - Unified vocabulary
2. Review [The Mine Integration](./02-learning-point-integration.md) - Block system
3. Review [UX Vision](./30-ux-vision-game-design.md) - Game design
4. Review [Economic Model](./31-economic-model-hypotheses.md) - Dual economy
5. Review implementation roadmap (`03-implementation-roadmap.md`)
6. Start MVP development

