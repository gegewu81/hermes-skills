---
name: github-security-audit
description: Audit GitHub repos for leaked secrets, credentials, private IPs, and other sensitive information. Uses GitHub API with PAT to recursively scan all files.
---

# GitHub Security Audit

Scan all repos under a GitHub account for sensitive information leaks.

## When to Use

- After creating a new public repo from private code
- Periodically (quarterly) audit all repos
- Before open-sourcing a project
- After any credential rotation to verify no stale keys remain

## Prerequisites

- GitHub PAT and username configured (same credentials used by github-auth skill)
- Internet access (GitHub API)

## Audit Patterns (Severity Levels)

### CRITICAL
- Private key blocks (`-----BEGIN ... PRIVATE KEY-----`)
- Database connection strings with passwords (`mongodb://user:pass@host`)
- Secret env var names with real values
- Plaintext passwords (`password = "..."`)

### HIGH
- API key assignments (`api_key = "..."`)
- Token assignments (`token = "..."`)
- Credentials in URLs (`https://user:secret@host`)
- Webhook/callback URLs with tokens
- `.env`-style secret assignments

### MEDIUM
- Private IP addresses (10.x.x.x, 172.16-31.x.x, 192.168.x.x)
- Hardcoded SSH `HostName` with real IPs
- Non-generic SSH `User` entries
- Hardcoded paths with real usernames (`/home/realuser/`)

### LOW
- Email addresses (exclude noreply, example)
- Generic user identifiers in documentation

## False Positive Filters

Always skip lines containing these patterns:
- Placeholder markers: `<YOUR_*>`, `CHANGE_ME`, `TODO`, `FIXME`, `xxx+`
- Descriptive words: `placeholder`, `example`, `e.g.`, `such as`
- Env var references: `${*}`
- Loopback addresses: `localhost`, `127.0.0.1`, `0.0.0.0`
- Comment lines starting with `#`

## Key Lessons

1. **SKILL.md "user" keyword false-positives** — Generic words like "user profile" match SSH User pattern. Always check context before flagging.

2. **Git repo and skill directory can diverge** — Code changes to the running skill copy do NOT auto-update the git repo. Always sync both before pushing. Applies to hermes-ha: `~/hermes-ha/` (git) vs `~/.hermes/skills/devops/agent-ha/` (runtime).

3. **FTS5 tables are NOT in MERGE_TABLES** — `messages_fts` search index in state.db is never touched by HA sync. Each node must rebuild FTS independently after corruption.

4. **SCP SQLite while gateway running = corruption** — Holographic on_pre_compress writes to state.db even in standby. Correct procedure: stop gateway, scp, delete WAL/SHM, restart gateway.

5. **WAL/SHM silently corrupt valid DB replacements** — Replacing a .db file via scp leaves old WAL/SHM files. SQLite replays stale WAL against new DB. Always delete WAL/SHM after replacing any SQLite file.
