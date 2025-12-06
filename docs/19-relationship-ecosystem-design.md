# LexiCraft Relationship Ecosystem Design
## Comprehensive User Relationships & Roles

**Status:** Design Phase  
**Last Updated:** 2024  
**Based On:** Industry research (Khan Academy, ClassDojo, Duolingo) + LexiCraft requirements

---

## Table of Contents

1. [Overview](#overview)
2. [Industry Practices](#industry-practices)
3. [Relationship Types](#relationship-types)
4. [Roles & Permissions](#roles--permissions)
5. [Age & Legal Considerations](#age--legal-considerations)
6. [Schema Design](#schema-design)
7. [Use Cases](#use-cases)
8. [Implementation Phases](#implementation-phases)

---

## Overview

### Vision

LexiCraft supports a rich ecosystem of relationships:
- **Parents** managing their children's learning
- **Professional teachers/coaches** guiding students
- **Peer coaches** (kids teaching kids - "slavedrivers")
- **Siblings** learning together
- **Friends** studying and competing
- **Classmates** in organized groups

### Core Principle

**Flexible, relationship-based permissions** - What you can do depends on your relationship, not just your role.

---

## Industry Practices

### What Top Platforms Do

**Khan Academy:**
- Roles: Student, Teacher, Parent, Coach
- Teachers create classes, assign work
- Students can be in multiple classes
- Parents view child's progress
- **No peer-to-peer coaching** (yet)

**ClassDojo:**
- Roles: Teacher, Student, Parent
- Teachers manage classes
- Parents view progress
- **No student-to-student coaching**

**Duolingo:**
- Roles: Learner, Teacher (schools only)
- **No peer coaching** in consumer app
- Schools version has teacher-student relationships

**Peer-to-Peer Learning:**
- Brainly: Students help each other (Q&A, not coaching)
- Quizlet: Study groups (collaborative, not hierarchical)
- **No major platform has kids coaching kids** (legal/liability concerns)

### LexiCraft's Innovation

**We're doing something new:**
- ✅ Allow kids to coach other kids (with parent approval)
- ✅ Reward peer coaches for successful teaching
- ✅ Support multiple relationship types in one system
- ✅ Flexible permissions per relationship

---

## Relationship Types

### Complete Relationship Matrix

| Relationship Type | From User | To User | Age Restrictions | Parent Approval | Use Case |
|-------------------|-----------|---------|------------------|----------------|----------|
| `parent_child` | Parent (20+) | Child (<20) | Parent ≥20, Child <20 | No (legal) | Legal guardian |
| `coach_student` | Coach (any) | Student (any) | None | Yes (if student <20) | Teacher/peer coaching |
| `sibling` | Child | Child | Both <20 | Yes | Siblings learning together |
| `friend` | User | User | None | Yes (if either <20) | Friends studying together |
| `classmate` | Student | Student | None | Yes (if either <20) | Same class/group |
| `tutor_student` | Tutor (usually adult) | Student | None | Yes (if student <20) | Professional tutoring |

### Relationship Descriptions

#### 1. parent_child
**Purpose:** Legal guardian relationship  
**Who:** Parent (20+) managing Child (<20)  
**Permissions:**
- ✅ View all progress
- ✅ Manage account
- ✅ Withdraw money
- ✅ Assign work
- ❌ Verify learning (platform does this)

**Legal:** Required by Taiwan law (age of majority = 20)

#### 2. coach_student
**Purpose:** Teaching/coaching relationship  
**Who:** Anyone can coach anyone (with approval)  
**Permissions (configurable):**
- ✅ View progress (limited or full)
- ✅ Assign vocabulary/work
- ✅ Suggest learning paths
- ❌ Verify learning (platform does this)
- ❌ Withdraw money
- ❌ Manage account

**Special Cases:**
- **Adult Coach → Child:** Professional teacher
- **Kid Coach → Kid:** Peer coaching ("slavedriver" scenario)
- **Parent as Coach:** Parent can also be coach (dual role)

#### 3. sibling
**Purpose:** Siblings learning together  
**Who:** Two children in same family  
**Permissions:**
- ✅ View each other's progress
- ✅ Compete/challenge
- ❌ Assign work
- ❌ Manage accounts

**Auto-created:** When parent creates multiple children

#### 4. friend
**Purpose:** Friends studying together  
**Who:** Any two users  
**Permissions:**
- ✅ View public progress
- ✅ Compete/challenge
- ✅ Study together
- ❌ Assign work
- ❌ Manage accounts

**Requires:** Parent approval if either user <20

#### 5. classmate
**Purpose:** Students in same class/group  
**Who:** Students in organized group  
**Permissions:**
- ✅ View class leaderboard
- ✅ See each other's progress
- ✅ Group challenges
- ❌ Assign work (only teacher can)
- ❌ Manage accounts

**Created by:** Teacher/coach creating a class

#### 6. tutor_student
**Purpose:** Professional tutoring relationship  
**Who:** Professional tutor → Student  
**Permissions:**
- ✅ View progress
- ✅ Assign work
- ✅ Create study plans
- ❌ Verify learning
- ❌ Manage account
- ❌ Withdraw money

**Difference from coach:** More formal, usually paid, professional credentials

---

## Roles & Permissions

### User Roles

```sql
-- Roles in user_roles table
'parent'    -- Legal guardian (20+)
'learner'   -- Student (any age)
'coach'     -- Teacher/instructor (any age, with approval)
'tutor'     -- Professional tutor (usually adult)
'admin'     -- Platform admin
```

### Role Combinations

A user can have **multiple roles**:

| User Type | Roles | Example |
|-----------|-------|---------|
| Parent only | `['parent']` | Parent managing child |
| Learner only | `['learner']` | Adult self-learner |
| Parent + Learner | `['parent', 'learner']` | Parent who also learns |
| Kid Coach | `['learner', 'coach']` | Kid teaching other kids |
| Professional Teacher | `['coach']` or `['tutor']` | School teacher |
| Parent + Coach | `['parent', 'coach']` | Parent teaching own child |

### Permissions Matrix

| Action | Parent | Coach | Tutor | Learner | Friend |
|--------|--------|-------|-------|---------|--------|
| View own progress | ✅ | ✅ | ✅ | ✅ | ✅ |
| View child's progress | ✅ | ❌ | ❌ | ❌ | ❌ |
| View student's progress | ❌ | ✅* | ✅* | ❌ | ❌ |
| Assign work to child | ✅ | ❌ | ❌ | ❌ | ❌ |
| Assign work to student | ❌ | ✅* | ✅* | ❌ | ❌ |
| Withdraw money | ✅ (for child) | ❌ | ❌ | ✅ (own) | ❌ |
| Manage child's account | ✅ | ❌ | ❌ | ❌ | ❌ |
| Verify learning | ❌ | ❌ | ❌ | ❌ | ❌ |

*With relationship and approval

---

## Age & Legal Considerations

### Taiwan Law

**Age of Majority:** 20 years old

**Rules:**
- Users <20: Must have parent account
- Parent approval required for:
  - Creating relationships with others
  - Social features
  - Peer coaching
- Parents control financials for children

### COPPA (If US Market)

**Under 13:**
- Stricter rules
- Parent consent required for social features
- Peer interactions need monitoring
- Data collection restrictions

**Recommendation:**
- Require parent approval for all relationships if user <20
- Log all coaching interactions
- Provide parental oversight tools
- Clear privacy policies

### Age Rules Summary

| Action | Age Requirement | Parent Approval |
|--------|----------------|-----------------|
| Create account | Any | If <20, parent must create |
| Be a learner | Any | If <20, parent must approve |
| Be a coach | Any | If student <20, parent approval needed |
| Coach another kid | Any | Both parents must approve |
| Withdraw money | 20+ | No (or parent for child) |
| Manage child account | 20+ | No (legal requirement) |

---

## Schema Design

### Option 1: Generic Relationships Table (Recommended)

**Replace** `parent_child_relationships` with **generic** `user_relationships`:

```sql
-- Generic user relationships table
CREATE TABLE user_relationships (
    id SERIAL PRIMARY KEY,
    from_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,  -- 'parent_child', 'coach_student', 'sibling', 'friend', 'classmate', 'tutor_student'
    status TEXT DEFAULT 'active',  -- 'active', 'pending_approval', 'blocked', 'suspended'
    
    -- Permissions (what from_user can do for to_user)
    permissions JSONB DEFAULT '{
        "can_view_progress": false,
        "can_assign_work": false,
        "can_verify_learning": false,
        "can_withdraw": false,
        "can_manage_account": false,
        "can_view_financials": false
    }',
    
    -- Metadata (context-specific)
    metadata JSONB DEFAULT '{}',  -- e.g., {"class_name": "English 101", "subject": "vocabulary", "group_id": "..."}
    
    -- Approval tracking (for relationships requiring consent)
    requested_by UUID REFERENCES users(id),  -- Who requested this relationship
    approved_by UUID REFERENCES users(id),   -- Parent/admin who approved
    approved_at TIMESTAMP,
    rejection_reason TEXT,  -- If rejected
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(from_user_id, to_user_id, relationship_type),
    CHECK (from_user_id != to_user_id)
);

CREATE INDEX idx_user_relationships_from ON user_relationships(from_user_id);
CREATE INDEX idx_user_relationships_to ON user_relationships(to_user_id);
CREATE INDEX idx_user_relationships_type ON user_relationships(relationship_type);
CREATE INDEX idx_user_relationships_status ON user_relationships(status);
```

### Default Permissions by Relationship Type

**parent_child:**
```json
{
  "can_view_progress": true,
  "can_assign_work": true,
  "can_verify_learning": false,
  "can_withdraw": true,
  "can_manage_account": true,
  "can_view_financials": true
}
```

**coach_student (adult coach):**
```json
{
  "can_view_progress": true,
  "can_assign_work": true,
  "can_verify_learning": false,
  "can_withdraw": false,
  "can_manage_account": false,
  "can_view_financials": false
}
```

**coach_student (peer coach - kid coaching kid):**
```json
{
  "can_view_progress": true,  // Limited view (not financials)
  "can_assign_work": true,   // Suggest words to learn
  "can_verify_learning": false,
  "can_withdraw": false,
  "can_manage_account": false,
  "can_view_financials": false
}
```

**sibling:**
```json
{
  "can_view_progress": true,  // See each other's progress
  "can_assign_work": false,
  "can_verify_learning": false,
  "can_withdraw": false,
  "can_manage_account": false,
  "can_view_financials": false
}
```

**friend:**
```json
{
  "can_view_progress": true,  // Public progress only
  "can_assign_work": false,
  "can_verify_learning": false,
  "can_withdraw": false,
  "can_manage_account": false,
  "can_view_financials": false
}
```

**classmate:**
```json
{
  "can_view_progress": true,  // Class leaderboard
  "can_assign_work": false,   // Only teacher can assign
  "can_verify_learning": false,
  "can_withdraw": false,
  "can_manage_account": false,
  "can_view_financials": false
}
```

---

## Use Cases

### Use Case 1: Professional Teacher

**Scenario:** School teacher wants to coach students

```
Teacher (age 35, role: 'coach')
  → coach_student relationship
  → Student A (age 10, role: 'learner')
  → Student B (age 10, role: 'learner')
  → Student C (age 10, role: 'learner')
```

**Flow:**
1. Teacher signs up, gets 'coach' role
2. Teacher creates class/group
3. Parents add students to class (approve relationship)
4. Teacher can:
   - Assign vocabulary lists
   - View all students' progress
   - Create group challenges
   - See class leaderboard
5. Teacher cannot:
   - Withdraw money
   - Manage student accounts
   - Verify learning (platform does this)

### Use Case 2: Peer Coaching (Older Sibling)

**Scenario:** Older sibling coaches younger sibling

```
Older Sibling (age 15, roles: ['learner', 'coach'])
  → coach_student relationship
  → Younger Sibling (age 10, role: 'learner')
```

**Flow:**
1. Parent creates both children
2. Parent approves older sibling as coach
3. Older sibling gets 'coach' role added
4. Older sibling can:
   - Suggest words for younger sibling
   - See younger sibling's progress
   - Create challenges
   - Earn bonus points for successful coaching
5. Parent still controls:
   - Financials
   - Account settings
   - Can revoke coaching relationship

### Use Case 3: Friend Study Group

**Scenario:** Two friends studying together

```
Friend A (age 12, role: 'learner')
  → friend relationship (bidirectional)
  → Friend B (age 12, role: 'learner')
```

**Flow:**
1. Friend A requests friendship with Friend B
2. Both parents approve
3. Friends can:
   - See each other's progress
   - Compete in challenges
   - Study together
   - See leaderboard
4. Friends cannot:
   - Assign work
   - Manage accounts
   - See financials

### Use Case 4: Kid as Coach ("Slavedriver")

**Scenario:** Advanced learner coaches beginner (your example)

```
Advanced Learner (age 14, roles: ['learner', 'coach'])
  → coach_student relationship
  → Beginner (age 10, role: 'learner')
```

**Flow:**
1. Advanced learner requests to coach beginner
2. Beginner's parent approves
3. Advanced learner gets 'coach' role
4. Advanced learner can:
   - Assign vocabulary to beginner
   - Track beginner's progress
   - Earn coaching bonuses
5. Beginner's parent:
   - Still controls account
   - Can revoke coaching
   - Monitors all interactions

**Rewards for Coach:**
- Bonus points when student learns assigned words
- Coaching achievements
- Leaderboard ranking

### Use Case 5: Class/Group Structure

**Scenario:** Teacher creates class, students auto-connected

```
Teacher (role: 'coach')
  → Creates class "English 101"
  → Adds students:
    - Student A → classmate → Student B
    - Student A → classmate → Student C
    - Student B → classmate → Student C
  → All students → coach_student → Teacher
```

**Flow:**
1. Teacher creates class
2. Parents add children to class
3. Students auto-connected as classmates
4. Teacher can assign work to all students
5. Students can see class leaderboard

---

## Implementation Phases

### Phase 1: MVP (Current)

**Relationships:**
- ✅ `parent_child` only

**Roles:**
- ✅ `parent`
- ✅ `learner`

**Features:**
- Parent manages child
- Child learns vocabulary
- Basic progress tracking

### Phase 2: Professional Coaching

**Add:**
- `coach_student` relationship
- `coach` role
- `tutor` role (optional)

**Features:**
- Teachers can create classes
- Teachers can assign work
- Parent approval system
- Teacher dashboard

### Phase 3: Peer Relationships

**Add:**
- `sibling` relationship
- `friend` relationship
- `classmate` relationship

**Features:**
- Siblings auto-connected
- Friend requests/approval
- Class groups
- Social features

### Phase 4: Peer Coaching

**Add:**
- Kids as coaches
- Coaching rewards
- Coaching dashboard

**Features:**
- Peer coaching requests
- Coaching bonuses
- Coaching leaderboard
- Parent monitoring tools

---

## Approval Workflows

### Workflow 1: Parent-Child (No Approval Needed)

```
Parent signs up → Creates child → Relationship auto-approved
```

### Workflow 2: Coach-Student (Requires Approval)

```
Coach requests → Student's parent notified → Parent approves → Relationship active
```

**If student <20:**
- Parent must approve
- Parent can revoke anytime
- All interactions logged

**If student ≥20:**
- No approval needed
- Student can accept/reject

### Workflow 3: Peer Coaching (Both Parents Approve)

```
Kid A requests to coach Kid B
  → Kid B's parent approves
  → Kid A's parent approves (optional but recommended)
  → Relationship active
```

### Workflow 4: Friend Request

```
User A requests friendship with User B
  → If User B <20: Parent approves
  → If User B ≥20: User B approves
  → Relationship active (bidirectional)
```

---

## Security & Privacy

### Data Access Rules

**Who can see what:**

| Data Type | Parent | Coach | Student | Friend |
|-----------|--------|-------|---------|--------|
| Learning progress | ✅ Full | ✅ Limited | ✅ Own | ✅ Public only |
| Financial info | ✅ Child's | ❌ | ✅ Own | ❌ |
| Account settings | ✅ Child's | ❌ | ✅ Own | ❌ |
| Verification results | ✅ Child's | ✅ Student's | ✅ Own | ❌ |
| Points balance | ✅ Child's | ❌ | ✅ Own | ❌ |

### Monitoring & Logging

**All coaching interactions logged:**
- Words assigned
- Progress viewed
- Challenges created
- Time spent coaching

**Parent oversight:**
- Parents can view all coach interactions
- Parents can revoke relationships
- Parents get notifications

---

## API Design

### Relationship Management Endpoints

```python
# Request coaching relationship
POST /api/relationships/request
{
  "from_user_id": "coach-uuid",
  "to_user_id": "student-uuid",
  "relationship_type": "coach_student"
}

# Approve relationship (parent)
POST /api/relationships/{relationship_id}/approve

# Reject relationship
POST /api/relationships/{relationship_id}/reject

# Get user's relationships
GET /api/relationships?user_id={uuid}&type={type}

# Get students for coach
GET /api/coaches/{coach_id}/students

# Get coaches for student
GET /api/students/{student_id}/coaches
```

---

## Benefits of This Design

✅ **Flexible:** Supports all relationship types  
✅ **Scalable:** Easy to add new types  
✅ **Safe:** Parent approval for peer relationships  
✅ **Industry-standard:** Similar to Khan Academy, ClassDojo  
✅ **Future-proof:** Can add new relationship types later  
✅ **Legal compliant:** Respects age restrictions  
✅ **Innovative:** Supports peer coaching (unique feature)

---

## Questions & Decisions

### Open Questions

1. **Coaching Rewards:** How much should coaches earn?
   - Recommendation: 10-20% of student's points earned

2. **Age Limits:** Minimum age to be a coach?
   - Recommendation: No hard limit, but parent approval required

3. **Coaching Limits:** How many students can one coach have?
   - Recommendation: Unlimited for MVP, add limits later if needed

4. **Financial Transparency:** Should coaches see student's point balance?
   - Recommendation: No - only learning progress

5. **Coaching Verification:** Should coaches verify learning?
   - Recommendation: No - platform handles verification

### Decisions Made

✅ Use generic `user_relationships` table (not just `parent_child`)  
✅ Support multiple roles per user  
✅ Require parent approval for peer relationships  
✅ Log all coaching interactions  
✅ Parents can revoke relationships anytime  
✅ Coaches cannot access financials  
✅ Platform verifies learning (not coaches)

---

## Next Steps

1. ✅ Document complete (this file)
2. ⏳ Update schema migration (007) to use `user_relationships`
3. ⏳ Update models to support new relationship types
4. ⏳ Implement approval workflows
5. ⏳ Build coaching features
6. ⏳ Add parent monitoring tools

---

**End of Design Document**

