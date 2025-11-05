# Domain Zero - 5-Minute Quickstart
## Get Started Immediately

**New to Domain Zero?** This guide gets you building in 5 minutes. No theory, just action.

---

## What You Need to Know Right Now

**Domain Zero = Three AI agents working as a team**

- **Yuuji** 🥊 - Writes code + tests
- **Megumi** 🐺 - Reviews security
- **Gojo** 👁️ - Coordinates everything

**Goal**: Zero bugs, zero vulnerabilities, zero compromises.

---

## Your First Feature (Copy & Paste These Commands)

### Step 1: Initialize Your Project (One-Time Setup)

Copy this command into Claude Code:

```
Read protocol/GOJO.md
```

**You'll see**: Mission Control menu with 3 options

**Type**: `2` (New Project Initialization)

**Answer these questions**:
- Project name: `[Your project name]`
- Project description: `[What you're building]`

**Result**: ✅ Project initialized in 30 seconds

---

### Step 2: Implement Your First Feature

Copy this command (replace with your feature):

```
Read protocol/YUUJI.md and implement user registration with email validation
```

**What Happens**:
1. Yuuji asks clarifying questions (answer them)
2. Yuuji creates a backup automatically ✅
3. Yuuji writes tests first ✅
4. Yuuji implements the feature ✅
5. Yuuji documents everything ✅
6. Yuuji tags `@user-review` (ready for you to check)

**You Review**: Look at the code Yuuji wrote. Does it look good?

**If Yes**: Continue to Step 3
**If No**: Tell Yuuji what to fix, repeat Step 2

---

### Step 3: Get Security Review

Copy this command:

```
Read protocol/MEGUMI.md and review user registration
```

**What Happens**:
1. Megumi analyzes code against OWASP Top 10 ✅
2. Megumi checks for security vulnerabilities ✅
3. Megumi verifies backup exists ✅
4. Megumi creates detailed security report ✅

**Two Possible Outcomes**:

**Outcome A: @approved** ✅
- No security issues found
- Feature is ready for production
- **You're done!** 🎉

**Outcome B: @remediation-required** ⚠️
- Megumi found security issues (e.g., SEC-001, SEC-002)
- Go to Step 4

---

### Step 4: Fix Security Issues (If Needed)

If Megumi found issues, copy this command:

```
Read protocol/YUUJI.md and fix all security issues found by Megumi
```

**What Happens**:
1. Yuuji reads Megumi's findings
2. Yuuji fixes each issue thoroughly
3. Yuuji re-tests everything
4. Yuuji tags `@re-review`

**Then**: Repeat Step 3 (Megumi verifies fixes)

**Loop continues until**: @approved ✅

---

## That's It! You Just Used Domain Zero.

**What You Accomplished**:
- ✅ Created backup (can rollback if needed)
- ✅ Wrote tests (code is verified)
- ✅ Implemented feature (working code)
- ✅ Security reviewed (OWASP Top 10 checked)
- ✅ Fixed vulnerabilities (production-ready)
- ✅ Documented everything (maintainable)

**Time Spent**: 15-45 minutes (depending on feature complexity)

**Quality Achieved**: Production-ready code with zero known vulnerabilities

---

## Common Commands Cheat Sheet

### Starting Your Day
```
Read protocol/GOJO.md
[Type: 1 for Resume Current Project]
```

### Implementing Features
```
Read protocol/YUUJI.md and implement [describe your feature]
```

### Security Reviews
```
Read protocol/MEGUMI.md and review [feature or module]
```

### Fixing Issues
```
Read protocol/YUUJI.md and fix [specific issue]
```

### Weekly Intelligence
```
Read protocol/GOJO.md - Trigger 19
```

---

## Real Example: User Authentication

Here's exactly what to type for a real feature:

**Step 1**: Initialize (one-time)
```
Read protocol/GOJO.md
2
Project name: My Awesome App
Description: A web application with user authentication
```

**Step 2**: Implement login
```
Read protocol/YUUJI.md and implement user login with JWT authentication. Users should login with email and password, receive a JWT token, and use it to access protected endpoints.
```

**Step 3**: Security review
```
Read protocol/MEGUMI.md and review the JWT authentication implementation
```

**Step 4** (if needed): Fix issues
```
Read protocol/YUUJI.md and fix SEC-001 and SEC-002 found in the security review
```

**Step 5**: Verify fixes
```
Read protocol/MEGUMI.md and verify that SEC-001 and SEC-002 are fixed
```

**Result**: Production-ready authentication system in 1-2 hours

---

## What Happens Behind the Scenes

You don't need to know this now, but here's what Domain Zero does automatically:

**Yuuji (Implementation)**:
- Creates timestamped backup before changing code
- Writes tests first (test-driven development)
- Implements feature to pass tests
- Documents decisions in dev-notes.md
- Creates rollback plan

**Megumi (Security)**:
- Reviews against OWASP Top 10 security standards
- Checks for SQL injection, XSS, authentication flaws, etc.
- Assigns severity (Critical/High/Medium/Low)
- Provides fix recommendations
- Verifies Yuuji's fixes

**Gojo (Coordination)**:
- Maintains project context across sessions
- Coordinates Yuuji and Megumi workflow
- Generates intelligence reports
- Protects protocol integrity

**The Result**: Professional development process without hiring a team.

---

## Next Steps: Level Up Your Skills

### Ready to Learn More?

**Understand the Full System**:
- Read `protocol/CLAUDE.md` - Complete system documentation

**Master Each Agent**:
- Read `protocol/YUUJI.md` - Implementation best practices
- Read `protocol/MEGUMI.md` - Security review details
- Read `protocol/GOJO.md` - Project management features

**Advanced Features**:
- Custom triggers for common operations
- Backup and rollback strategies
- Multi-stage workflows for complex projects
- Intelligence reports (Trigger 19)

### Common Questions

**Q: Do I need to understand everything to use Domain Zero?**
A: No! Just follow the 4 steps above. Learn details gradually.

**Q: What if I make a mistake?**
A: Every change has a timestamped backup. You can always rollback.

**Q: Can I skip security review for quick prototypes?**
A: Yes! Just don't deploy to production without Megumi's @approved tag.

**Q: How much does this cost?**
A: Token costs are $0.15-$0.45 per feature (negligible compared to developer time).

**Q: Is AI-generated code safe?**
A: That's why Megumi exists! 45% of raw AI code has security flaws. Megumi catches them.

**Q: Can I use this for my startup/job/side project?**
A: Absolutely! Domain Zero works for production code, not just learning.

---

## Tips for Success

### 🎯 Be Specific in Your Prompts

**Bad**: "Implement authentication"
**Good**: "Implement JWT authentication with email/password login, 15-minute access token expiry, 7-day refresh tokens, and password hashing using bcrypt"

### 🔍 Review Yuuji's Code

Don't blindly trust AI. Look at what Yuuji implemented. If something seems off, tell Yuuji to fix it.

### 🛡️ Take Security Seriously

Always run Megumi review before deploying. Especially for:
- Authentication
- Payment processing
- User data handling
- Public APIs

### 📝 Keep State Files Updated

Domain Zero tracks context in `.protocol-state/` files. Don't delete them.

### ⚡ Start Simple

First feature: Something straightforward (user registration, basic CRUD)
Build confidence before tackling complex features.

---

## Troubleshooting

### "Yuuji keeps asking questions"

**Why**: Feature description was vague
**Fix**: Provide more details upfront

### "Megumi found 10+ issues"

**Why**: Common for first features (learning curve)
**Fix**: Yuuji will fix them. This is normal and expected.

### "I lost my project context"

**Why**: `.protocol-state/` files were deleted or modified
**Fix**: Use `Read protocol/GOJO.md` → Option 1 (Resume) to restore

### "Tests are failing"

**Why**: Yuuji's implementation had a bug
**Fix**: Tell Yuuji "Tests are failing with [error message]. Fix this."

### "It's taking too long"

**Why**: First feature always takes longer (setup, learning)
**Fact**: Second feature will be 2-3x faster. Fifth feature even faster.

---

## Success Checklist

Before considering yourself "Domain Zero ready," complete these:

- [ ] Initialized a project with Gojo
- [ ] Implemented one feature with Yuuji
- [ ] Ran security review with Megumi
- [ ] Fixed at least one security issue (if found)
- [ ] Got @approved from Megumi
- [ ] Deployed feature successfully

**Completed all 6?** Congratulations! You're now a Domain Zero user. 🎉

---

## Comparison: Before vs After Domain Zero

### Before Domain Zero (Traditional Solo Development)

**Your Workflow**:
1. Write code directly
2. Maybe write tests (often skipped under time pressure)
3. Hope you didn't miss security issues
4. Deploy and pray
5. Fix bugs in production 😰

**Result**: Fast initially, but:
- Security vulnerabilities slip through
- No systematic review
- Bugs discovered by users
- Technical debt accumulates

**Time**: Fast to deploy, slow to fix production issues

---

### After Domain Zero

**Your Workflow**:
1. Yuuji writes tests first, then code
2. You review
3. Megumi does security audit
4. Yuuji fixes issues Megumi found
5. Deploy with confidence ✅

**Result**: Slightly slower initially, but:
- Security vulnerabilities caught before production
- Systematic OWASP review
- Bugs caught in development
- Clean, documented code

**Time**: Slightly slower to deploy, zero time fixing production issues

---

## Real User Time Investment

**First Feature**: 1-2 hours
- 30 min: Learning how to invoke agents
- 30-60 min: Implementation with Yuuji
- 15-30 min: Security review with Megumi
- 0-30 min: Fixing issues if found

**Second Feature**: 30-60 minutes
- You know the process now
- Prompts are more effective
- Fewer security issues (you learned from first feature)

**Fifth Feature**: 20-40 minutes
- Muscle memory established
- Common patterns reused
- High-quality prompts from experience

**ROI**: After 3-5 features, Domain Zero pays for itself in time saved vs debugging production issues.

---

## When NOT to Use Domain Zero

**Domain Zero is overkill for**:
- ❌ Quick throwaway scripts
- ❌ "Hello World" learning exercises
- ❌ Rapid prototypes you'll delete anyway
- ❌ Simple HTML/CSS static pages

**Domain Zero is perfect for**:
- ✅ Production web applications
- ✅ SaaS products
- ✅ Client deliverables
- ✅ Open-source projects
- ✅ Startup MVPs
- ✅ Portfolio projects
- ✅ Anything you'll actually deploy

**Rule of Thumb**: If users will see it, use Domain Zero. If nobody will see it, maybe skip.

---

## You're Ready! 🚀

You now know enough to use Domain Zero productively.

**Your Action**: Implement your first feature using the 4-step process above.

**Questions?** Read the full documentation in `protocol/CLAUDE.md`

**Need help?** Review the specific agent guides:
- `protocol/YUUJI.md` for implementation questions
- `protocol/MEGUMI.md` for security questions
- `protocol/GOJO.md` for project management questions

---

## Remember

**Domain Zero is**:
- ✅ AI-assisted development (not AI-autonomous)
- ✅ A force multiplier for solo developers
- ✅ Professional workflow without hiring a team
- ✅ Quality assurance built into every feature

**Domain Zero is NOT**:
- ❌ Magic bullet that eliminates all bugs
- ❌ Replacement for human judgment
- ❌ 100% autonomous coding
- ❌ Suitable for complete beginners

**Start simple. Build confidence. Master gradually.**

**Welcome to Domain Zero. Let's build something great. 🌀**

---

**END OF QUICKSTART**

**Next**: Read `protocol/CLAUDE.md` for complete system documentation.
