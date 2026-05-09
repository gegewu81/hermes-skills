---
name: skill-audit-and-enhance
description: Systematically audit Hermes skills against an external reference (e.g., agent-skills), prioritize gaps, and batch-enhance with proper backup and verification.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, audit, enhancement, quality, methodology]
    related_skills: [skill-sync-across-nodes, openclaw-skill-offline-install]
---

# Skill Audit and Enhancement

## Overview

When integrating patterns from an external skill collection into Hermes, follow this structured workflow to ensure nothing is missed, changes are safe, and the result is verifiable.

## When to Use

- After identifying gaps via a skill-to-skill comparison (e.g., Hermes vs agent-skills)
- When adopting best practices from an external methodology
- When a batch of related skill improvements need coordinated execution

## Workflow: Six Phases

### Phase 0: Principle Extraction & Scenario Remapping

**Before touching any code, understand WHAT to borrow and WHY.** This is the cognitive step that determines whether the integration will be useful or just cargo-cult copying.

#### Step 1: Re-categorize by Underlying Principle

Don't use the external repo's taxonomy — they organized for their audience. Re-group by the **underlying principle** each skill embodies:

```
Original:             Principle-based:
├─ engineering/       ├─ Language alignment (grill, CONTEXT.md)
├─ productivity/      ├─ Feedback loop priority (diagnose)
└─ misc/              ├─ Vertical slicing (to-issues)
                     ├─ Rejection memory (triage)
                     ├─ Brevity discipline (caveman)
                     └─ Meta-skills (write-a-skill)
```

#### Step 2: Map to YOUR User's Scenarios

The original author's audience may be completely different. For each principle, ask:
- Does this apply to non-developers doing transactional work?
- Does this apply to small tool development?
- Does this apply to task planning/arrangement?

**Rate each principle:** A (strongly applicable) / B (useful) / C (already covered)

#### Step 3: Prefer Merge Over Create

User preference: merge principles into existing skills rather than creating new ones. For each A/B principle, find the closest existing Hermes skill and plan a minimal patch.

**Rule of thumb:** If you can express the principle in ≤10 lines and insert it into an existing section, don't create a new skill.

#### Deliverable of Phase 0

A mapping table like:

| External Principle | Target Hermes Skill | Change Type | Priority |
|---|---|---|---|
| Language alignment | spec-driven-development | +Term Alignment section | P0 |
| Feedback loop first | systematic-debugging | +Phase 0 verification | P0 |
| Vertical slicing | writing-plans | +Vertical Slicing section | P0 |

This table becomes the input for Phase 3 (Prioritize Changes).

### Phase 1: Backup

**Always backup before modifying any skill.**

```bash
mkdir -p ~/.hermes/skills_backup_$(date +%Y%m%d_%H%M%S)
cp -r ~/.hermes/skills/<target-skill> ~/.hermes/skills_backup_<timestamp>/
```

- Backup ALL files that will be modified in one batch
- Use timestamped directory names
- Verify backup exists before proceeding

### Phase 2: Gather Reference Material

Fetch the source patterns you're adapting:

- Use `delegate_task` with terminal+web to fetch from GitHub/raw URLs
- China fallback: `ghfast.top` or `bgithub.xyz` when github.com is blocked
- Extract ONLY the sections you need (not entire files) to stay focused
- Save reference material to `/tmp/` for the session

**Common fetch pattern:**
```bash
curl -sL "https://ghfast.top/https://raw.githubusercontent.com/<org>/<repo>/main/<path>" -o /tmp/ref.md
```

### Phase 3: Prioritize Changes

Classify changes into priority tiers:

| Tier | Risk | Type | Examples |
|------|------|------|----------|
| **P0** | None | Add missing sections to existing skills | Anti-rationalization tables, verification gates |
| **P1** | Low-Medium | Restructure existing content | Merge skills, extract references/, update cross-references |
| **P2** | Low | Add new capabilities to existing skills | Task sizing, build discipline, honesty clauses |
| **P3** | None | Create new skills | spec, ship, slash-chain |

**Rules:**
- P0 first (no dependencies, pure additions)
- P1 requires checking reference chains (which skills mention which)
- P2 and P3 can often run in parallel
- NEVER modify Hermes source code — all changes are SKILL.md content

### Phase 4: Execute in Parallel

Use `delegate_task` for independent changes:

- **Independent tasks:** Skills that don't reference each other → run in parallel (max 3 subagents)
- **Dependent tasks:** Skill A references Skill B → modify B first, then A
- **Cross-reference updates:** After merging/renaming a skill, search all other skills for references

**Common patterns:**

#### Pattern A: Add a Section to Existing Skill
Use `patch(mode='replace')` with enough context for unique matching. If old_string matches multiple locations, add more surrounding context or use `search_files` first to find the exact location.

#### Pattern B: Merge Skill X into Skill Y
1. Identify unique content in X
2. Add that content to Y (as a new section)
3. Replace X/SKILL.md with a lightweight redirect (version bump to 2.0.0)
4. Search all skills for references to X and add Y

#### Pattern C: Extract to references/ (Progressive Disclosure)
1. Create `references/<topic>.md` with verbose content
2. Replace the verbose section in main SKILL.md with a brief pointer
3. Useful for: API setup code, prerequisite instructions, environment config

#### Pattern D: Create New Skill
1. Write complete SKILL.md with YAML frontmatter
2. Include: Common Rationalizations table, When to Use/Not Use
3. Set correct `related_skills` in metadata

### Phase 5: Verify

Run a comprehensive check after all changes:

```
delegate_task: verify ALL of these:
1. Every modified file has valid YAML frontmatter (--- delimiters)
2. Every new section exists where expected
3. Cross-references are consistent (no broken skill names)
4. Backup directory has all original files
5. New skills have complete structure (frontmatter + sections)
```

## Anti-Rationalization Patterns to Import

When auditing against agent-skills or similar projects, check for these common enhancement patterns:

| Pattern | Where It Goes | What It Does |
|---------|--------------|--------------|
| Anti-rationalization table | Every skill | Prevents agent from skipping discipline |
| Verification gate/checklist | Planning + review skills | Blocks advancement until quality criteria met |
| ASSUMPTIONS I'M MAKING | Spec + plan + review skills | Forces assumption surfacing before work |
| Build discipline | Code review + implementation | Feature flags, scope limits, safe defaults |
| Honesty in review | Code review | Anti-sycophancy, severity scale |
| Success criteria reframing | Spec + planning | Converts vague requirements to measurable targets |

## Pitfalls

- **patch uniqueness:** If `old_string` matches multiple locations, read the file first with `search_files` to find exact line numbers, then add more context
- **Frontmatter versioning:** Bump version when making structural changes (merge = 2.0.0, additions = 1.x.0 patch)
- **Memory limits:** Memory has 2200 char limit. When saving progress, use `replace` to update existing entries rather than `add`
- **Compaction risk:** In long sessions, context compaction can lose plan details. Save the full plan to memory AND to a file early
- **skills_sync.py:** Hermes skips skills with hash mismatches during update — user modifications are preserved
