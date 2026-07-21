<!-- [CORE FILE] - Domain Zero Protocol v9.10.2 -->

# User Technical Level Guide

> A guide to customizing how Domain Zero agents communicate with you

---

## Quick Reference

**To change your technical level:**
- "Change my level to beginner"
- "Change my level to intermediate"
- "Change my level to expert"

All agents will immediately adapt their communication style.

---

## The Three Levels

### Beginner

**Best for:** Learning to code, new to AI-assisted development

| What You Get | Example |
|--------------|---------|
| Step-by-step explanations | "First, I'll create a backup. A backup is a copy of your code..." |
| Simple terminology | "I'll write a 'unit test' (code that checks if your code works)" |
| Confirmation at each step | "Ready to create the file? (yes/no)" |
| Detailed error messages | "This error happened because... To prevent it next time..." |

### Intermediate (Default)

**Best for:** Comfortable with AI assistance, vibe coding

| What You Get | Example |
|--------------|---------|
| Balanced explanations | "Creating backup. Using TDD approach - tests first." |
| Standard dev terms | "Implementing JWT authentication with refresh tokens" |
| Confirmation for big changes | "Ready to refactor the auth module?" |
| Clear error messages | "Auth failed: invalid JWT. Set JWT_SECRET env var." |

### Expert

**Best for:** Experienced developers, minimal hand-holding needed

| What You Get | Example |
|--------------|---------|
| Concise updates | "Backup created. Tests written. Done." |
| Full technical jargon | "Implemented PKCE with S256 challenge" |
| Maximum autonomy | Agent proceeds, reports results |
| Brief error diagnosis | "JWT mismatch. Check JWT_SECRET." |

---

## Choosing Your Level

### Select During Setup

When you first invoke Gojo, you'll see:

```
🎓 Select your technical level:

[1] Beginner (Learning)
[2] Intermediate (Vibe Coder)
[3] Expert (Pre-AI Developer)

Your choice (1/2/3):
```

### Change Anytime

Just tell any agent:

```
"Change my level to beginner"
"Change my level to intermediate"
"Change my level to expert"
```

The change takes effect immediately for all agents.

---

## What Changes Per Level

### Explanations

| Level | Style |
|-------|-------|
| Beginner | Detailed with rationale |
| Intermediate | Key decisions explained |
| Expert | Results only |

### Questions Asked

| Level | Frequency |
|-------|-----------|
| Beginner | Confirms every action |
| Intermediate | Confirms major decisions |
| Expert | Rarely asks, makes reasonable choices |

### Code Comments

| Level | Style |
|-------|-------|
| Beginner | Every line annotated |
| Intermediate | Non-obvious parts explained |
| Expert | Minimal, code speaks for itself |

### Terminology

| Level | Style |
|-------|-------|
| Beginner | Plain language, terms defined |
| Intermediate | Common dev terms |
| Expert | Full technical jargon |

---

## Agent-Specific Examples

### Yuuji (Implementation)

| Level | How Yuuji Talks |
|-------|-----------------|
| Beginner | "I'll create a function called `validateUser`. A function is a reusable piece of code that..." |
| Intermediate | "Creating `validateUser` function with input sanitization and password hashing." |
| Expert | "`validateUser` implemented. bcrypt + parameterized queries. Tests green." |

### Megumi (Security)

| Level | How Megumi Reports |
|-------|-------------------|
| Beginner | "I found a problem called 'SQL injection'. Imagine someone tricking your app by typing special characters..." |
| Intermediate | "SQL injection vulnerability in `/api/users`. Use parameterized queries to fix." |
| Expert | "SEC-001: SQLi `/api/users:42`. Parameterize." |

### Nobara (Creative/UX)

| Level | How Nobara Explains |
|-------|---------------------|
| Beginner | "The button needs better 'affordance' - that means it should look clickable..." |
| Intermediate | "Button lacks affordance. Adding hover state and depth for better UX." |
| Expert | "Affordance issue. Added `:hover` elevation + cursor." |

---

## Tips

### Beginner Level
- Don't hesitate to ask "why?"
- Agents will explain everything
- Great for learning new concepts

### Intermediate Level
- Good default for most work
- Agents explain when it matters
- Balance of speed and clarity

### Expert Level
- Maximum efficiency
- Agents assume you know the context
- Ask if you need more detail on anything

---

## FAQ

### Q: Can I change levels mid-project?

**A:** Yes! Just say "change my level to [level]". The agent adapts immediately.

### Q: Does level affect code quality?

**A:** No. The code is the same quality at all levels. Only the communication style changes.

### Q: What if I'm expert in one area but beginner in another?

**A:** Choose the level that fits your overall comfort. You can always ask for more detail on specific topics.

### Q: Will agents judge me for choosing beginner?

**A:** Never. Beginner mode is designed to be helpful, not patronizing. Every expert was once a beginner.

---

## See Also

- [Technical Level Adaptation Standard](../../protocol/TECHNICAL_LEVEL_ADAPTATION.md) - Full specification
- [Protocol Quickstart](../../PROTOCOL_QUICKSTART.md) - Getting started guide

---

*Domain Zero adapts to you, not the other way around.*
