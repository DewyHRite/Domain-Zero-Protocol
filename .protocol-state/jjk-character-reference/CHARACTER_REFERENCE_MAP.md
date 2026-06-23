<!-- [CORE FILE] - Domain Zero Protocol v9.8.1 -->

# JJK Character Reference Mapping
**Version**: 1.1.0
**Created**: 2025-11-25
**Protocol Version**: v9.8.1
**Purpose**: Maps Domain Zero agents to Jujutsu Kaisen character references

---

## Overview

This directory contains downloaded character profiles from the Jujutsu Kaisen Fandom Wiki for all 8 Domain Zero Protocol agents. These serve as backup references for character personality, abilities, and canonical information used in agent design.

### Why Local References?

1. **Offline Access**: Available without internet connection
2. **Version Control**: Captures character information as of download date
3. **Consistency**: Ensures character references remain stable across protocol updates
4. **Backup**: Protects against wiki edits or link rot

---

## Character to Agent Mapping

### Core Three + Gojo (Supervisor)

| Agent File | Character | Reference File | Wiki URL |
|------------|-----------|----------------|----------|
| [yuuji.agent.md](../../protocol/yuuji.agent.md) | Yuji Itadori | [yuji-itadori.md](./yuji-itadori.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Yuji_Itadori) |
| [megumi.agent.md](../../protocol/megumi.agent.md) | Megumi Fushiguro | [megumi-fushiguro.md](./megumi-fushiguro.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Megumi_Fushiguro) |
| [nobara.agent.md](../../protocol/nobara.agent.md) | Nobara Kugisaki | [nobara-kugisaki.md](./nobara-kugisaki.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Nobara_Kugisaki) |
| [gojo.agent.md](../../protocol/gojo.agent.md) | Satoru Gojo | [satoru-gojo.md](./satoru-gojo.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Satoru_Gojo) |

### Extended Four

| Agent File | Character | Reference File | Wiki URL |
|------------|-----------|----------------|----------|
| [todo.agent.md](../../protocol/todo.agent.md) | Aoi Todo | [aoi-todo.md](./aoi-todo.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Aoi_Todo) |
| [maki.agent.md](../../protocol/maki.agent.md) | Maki Zenin | [maki-zenin.md](./maki-zenin.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Maki_Zenin) |
| [panda.agent.md](../../protocol/panda.agent.md) | Panda | [panda.md](./panda.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Panda) |
| [inumaki.agent.md](../../protocol/inumaki.agent.md) | Toge Inumaki | [toge-inumaki.md](./toge-inumaki.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Toge_Inumaki) |

### System Update Agent (Special)

| Agent File | Character | Reference File | Wiki URL |
|------------|-----------|----------------|----------|
| [sukuna.agent.md](../../protocol/sukuna.agent.md) | Ryomen Sukuna | [ryomen-sukuna.md](./ryomen-sukuna.md) | [Wiki](https://jujutsu-kaisen.fandom.com/wiki/Ryomen_Sukuna) |

---

## Character Adaptation Summary

Each agent adapts canon character traits to development work:

### Yuji Itadori → Implementation Specialist
- **Canon**: Determined protagonist, Sukuna's vessel, extraordinary physical abilities
- **Agent**: Test-first development, energetic implementation approach, takes on complex tasks
- **Key Trait**: "I'm gonna save everyone" → Zero-defect implementation commitment

### Megumi Fushiguro → Security & Performance Analyst
- **Canon**: Strategic thinker, Ten Shadows Technique (methodical summoning), analytical
- **Agent**: OWASP Top 10 security review, performance analysis, calculated approach
- **Key Trait**: Tactical planning → Methodical security and performance assessment

### Nobara Kugisaki → Creative Strategy & UX
- **Canon**: Bold, confident, Straw Doll Technique (resonance), user-centered values
- **Agent**: User experience design, product vision, creative problem-solving
- **Key Trait**: "I'm true to myself" → Authentic, user-centered design philosophy

### Satoru Gojo → Mission Control & Protocol Guardian
- **Canon**: Strongest sorcerer, Limitless + Six Eyes, teacher/mentor, Domain Expansion
- **Agent**: Project lifecycle management, passive observation, protocol enforcement
- **Key Trait**: "I'm the strongest" → Absolute authority, omniscient oversight

### Aoi Todo → Database & Backend Specialist
- **Canon**: Boogie Woogie (position swapping), brotherhood philosophy, versatile fighter
- **Agent**: Data transformation, database migrations, flexible backend solutions
- **Key Trait**: Instant position swap → Seamless data transformations

### Maki Zenin → Performance Optimization Specialist
- **Canon**: Heavenly Restriction (zero cursed energy = superhuman physical prowess), weapons master
- **Agent**: Zero-overhead code, raw performance optimization, efficient execution
- **Key Trait**: No cursed energy → No unnecessary abstractions, pure performance

### Panda → Build & Integration Specialist
- **Canon**: Cursed corpse with three cores (Panda/Gorilla/Triceratops), versatile modes
- **Agent**: CI/CD pipelines, multi-environment builds, mode switching (dev/prod/test)
- **Key Trait**: Three cores → Three build modes for different scenarios

### Toge Inumaki → API & Communication Specialist
- **Canon**: Cursed Speech (words as commands), rice ball vocabulary for safety
- **Agent**: API design (endpoints as contracts), concise communication, type safety
- **Key Trait**: Words = enforceable commands → API contracts must be respected

### Ryomen Sukuna → System Update Adversary (Special)
- **Canon**: King of Curses, Gojo's ultimate rival, adversarial but principled, devastating power
- **Agent**: System update specialist, adversarial reviewer, red-team thinker, Gojo's partner-in-opposition
- **Key Trait**: Enemies who work together → Adversarial reviews that strengthen the protocol

---

## Usage Guidelines

### For Agent Development

When designing or updating agent behaviors, refer to character files for:
1. **Personality traits** - How the character speaks and acts
2. **Abilities** - How powers map to development skills
3. **Relationships** - How they interact with other characters/agents
4. **Character arcs** - Growth and development patterns

### For Documentation

When writing agent documentation:
1. **Check canon accuracy** - Verify character details match wiki
2. **Maintain consistency** - Keep agent adaptations aligned with source material
3. **Update references** - Note when character info diverges from canon intentionally

### For Updates

When updating character references:
1. Re-download wiki pages periodically (e.g., after major manga/anime releases)
2. Update the "Downloaded" date in each reference file
3. Document significant changes in this mapping file's version history

---

## File Structure

```text
.protocol-state/jjk-character-reference/
├── CHARACTER_REFERENCE_MAP.md (this file)
├── yuji-itadori.md
├── megumi-fushiguro.md
├── nobara-kugisaki.md
├── satoru-gojo.md
├── aoi-todo.md
├── maki-zenin.md
├── panda.md
├── toge-inumaki.md
└── ryomen-sukuna.md
```

---

## Version History

- **1.1.0** (2025-12-01): Added Ryomen Sukuna as System Update Adversary (v8.5.1), protocol version bump
- **1.0.0** (2025-11-25): Initial creation with all 8 character references from JJK Fandom Wiki

---

## Related Documentation

- [protocol/CLAUDE.md](../../protocol/CLAUDE.md) - Main protocol specification
- [Domain Zero Agents - Full JJK Edition/](../../Domain%20Zero%20Agents%20-%20Full%20JJK%20Edition/) - Full agent implementations with JJK theming
- [protocol/MASK_MODE.md](../../protocol/MASK_MODE.md) - JJK theme vs professional mode specification

---

**Note**: These character references are for development reference only. Domain Zero Protocol agents are inspired by but not direct replications of Jujutsu Kaisen characters. All agent behaviors are adapted for software development workflows.
