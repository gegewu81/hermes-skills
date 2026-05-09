# Hermes Agent Custom Skills

A curated collection of 12 high-value custom skills for [Hermes Agent](https://github.com/NousResearch/hermes-agent), covering DevOps, Security, Productivity, and GitHub workflows.

## Skills Overview

| # | Skill | Category | Description | Status |
|---|-------|----------|-------------|--------|
| 1 | `agent-clone` | DevOps | Universal AI Agent cloning/migration tool for Hermes, OpenClaw, and Claude Code | ✅ Stable |
| 2 | `hermes-clone` | DevOps | Clone/migrate Hermes Agent to new environments (e.g., Raspberry Pi) | ✅ Stable |
| 3 | `hermes-multi-provider` | DevOps | Multi-LLM provider routing with fallback, delegation, and smart routing | ✅ Stable |
| 4 | `state-db-repair` | DevOps | Diagnose and repair Hermes state.db — incremental fix and full rebuild | ✅ Stable |
| 5 | `skill-audit-and-enhance` | DevOps | Audit skills against external references, prioritize gaps, batch-enhance | ✅ Stable |
| 6 | `skill-sync-across-nodes` | DevOps | Compare, integrate, and sync skills across multiple Hermes nodes | ✅ Stable |
| 7 | `sensitive-data-redact` | DevOps | Safely redact sensitive data (passwords, keys) from Hermes data stores | ✅ Stable |
| 8 | `holographic-memory` | DevOps | Deploy and configure Holographic memory provider with Chinese regex support | ✅ Stable |
| 9 | `immune-system` | Security | Adaptive immune system for AI Agent runtime defense (MITRE ATT&CK based) | ✅ Stable |
| 10 | `session-recall` | Productivity | Systematic session recall with cross-referenced memory search | ✅ Stable |
| 11 | `caveman` | Productivity | Concise reply mode for WeChat/mobile channels — cut fluff, keep substance | ✅ Stable |
| 12 | `github-security-audit` | GitHub | Audit repos for leaked secrets, credentials, and sensitive information | ✅ Stable |

## Installation

### Prerequisites

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed and configured
- Git

### Quick Install

```bash
# Clone the skills repo
git clone https://github.com/gegewu81/hermes-skills.git /tmp/hermes-skills

# Copy desired skills into Hermes
cp -r /tmp/hermes-skills/skills/<skill-name> ~/.hermes/skills/<category>/

# Example: install agent-clone
cp -r /tmp/hermes-skills/skills/agent-clone ~/.hermes/skills/devops/

# Example: install immune-system
cp -r /tmp/hermes-skills/skills/immune-system ~/.hermes/skills/security/
```

### Install All Skills

```bash
git clone https://github.com/gegewu81/hermes-skills.git /tmp/hermes-skills
cp -r /tmp/hermes-skills/skills/* ~/.hermes/skills/
```

**Note:** If a skill requires specific category placement, move it to the correct category directory (e.g., `devops/`, `security/`, `productivity/`, `github/`).

## Directory Structure

```
hermes-skills/
├── skills/
│   ├── agent-clone/
│   │   └── SKILL.md
│   ├── caveman/
│   │   └── SKILL.md
│   ├── github-security-audit/
│   │   └── SKILL.md
│   ├── hermes-clone/
│   │   └── SKILL.md
│   ├── hermes-multi-provider/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── prefix-caching.md
│   ├── holographic-memory/
│   │   └── SKILL.md
│   ├── immune-system/
│   │   └── SKILL.md
│   ├── sensitive-data-redact/
│   │   └── SKILL.md
│   ├── session-recall/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── bulk-archival-to-vault.md
│   │       └── semantic-search-deployment.md
│   ├── skill-audit-and-enhance/
│   │   └── SKILL.md
│   ├── skill-sync-across-nodes/
│   │   └── SKILL.md
│   └── state-db-repair/
│       └── SKILL.md
├── LICENSE
├── .gitignore
└── README.md
```

## License

MIT — see [LICENSE](LICENSE) for details.
