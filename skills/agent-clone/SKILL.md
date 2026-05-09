---
name: agent-clone
description: Universal AI Agent cloning/migration tool. Supports Hermes, OpenClaw, and Claude Code. Package, transfer, and deploy agent identity, memory, skills, config, and sessions to any new environment.
---

# Agent Clone — Universal AI Agent Migration Tool

> **This is a reference guide, not a CLI tool.** All commands below are bash snippets — run them directly in your terminal, or have your agent execute them.

Migrate your AI agent's complete identity (config, persona, memory, skills, sessions) to a new machine or environment. Supports **Hermes**, **OpenClaw**, and **Claude Code**.

---

## Step 1: Source Environment Audit

Before packing, check what exists:

```bash
# Detect installed frameworks
for dir in ~/.hermes ~/.openclaw ~/.claude; do
  [ -d "$dir" ] && echo "DETECTED: $dir ($(du -sh "$dir" 2>/dev/null | cut -f1))"
done
```

---

## Step 2: Framework Data Map

### Universal Data Categories

All three frameworks store the same conceptual categories of data:

| Category | What it contains | Why migrate it |
|----------|-----------------|----------------|
| **Config** | API keys, model settings, provider config | Agent cannot start without it |
| **Persona** | Personality, instructions, behavioral rules | Defines who the agent is |
| **Memory** | Long-term facts, user preferences, knowledge | Agent's accumulated understanding |
| **Skills/Tools** | Custom workflows, templates, scripts | Agent's learned capabilities |
| **Sessions** | Conversation history, context | Continuity of work |
| **Channels** | Messaging integrations (WeChat, Telegram, etc.) | Communication channels |
| **Credentials** | Auth tokens, device IDs | Platform access |
| **MCP** | External tool server configs | Tool integrations |

### Hermes

| Category | Path | Notes |
|----------|------|-------|
| Config | `~/.hermes/config.yaml` | YAML, core settings |
| Persona | `~/.hermes/SOUL.md` | Agent personality markdown |
| Memory (structured) | `~/.hermes/memories/MEMORY.md` + `USER.md` | Markdown, human-readable |
| Memory (DB) | `~/.hermes/memory_store.db` | SQLite, fact_store |
| Sessions | `~/.hermes/state.db` + `~/.hermes/sessions/` | SQLite + JSON files |
| Skills | `~/.hermes/skills/` | Directory tree of SKILL.md files |
| Env vars / API keys | `~/.hermes/.env` | Dotenv file |
| Auth | `~/.hermes/auth.json` | Auth tokens |
| Channels | `~/.hermes/pairing/`, `~/.hermes/weixin/`, etc. | Platform-specific dirs |
| Context cache | `~/.hermes/context_length_cache.yaml` | Compression cache |
| MCP config | In `config.yaml` under `mcp_servers:` | Inline YAML |
| Source (optional) | `~/.hermes/hermes-agent/` | Python venv — architecture-specific |
| Binary (optional) | `~/.hermes/bin/tirith` | Architecture-specific, skip if cross-arch |

**Data directory structure:**

```
~/.hermes/
├── config.yaml              # Main config (models, compression, MCP, etc.)
├── SOUL.md                  # Agent personality definition
├── .env                     # API keys, environment variables
├── auth.json                # Auth tokens
├── channel_directory.json   # Channel directory
├── memories/
│   ├── MEMORY.md            # Agent working memory (Markdown)
│   └── USER.md              # User profile (Markdown)
├── memory_store.db          # Structured memory (SQLite / fact_store)
├── state.db                 # Session state (SQLite)
├── sessions/                # Session archives
├── skills/                  # Skills directory (SKILL.md file tree)
├── context_length_cache.yaml # Context compression cache
├── pairing/                 # Channel pairing info
├── hermes-agent/            # Source + venv (arch-specific, not portable)
└── bin/tirith               # Security sandbox binary (arch-specific)
```

### OpenClaw

| Category | Path | Notes |
|----------|------|-------|
| Config | `~/.openclaw/openclaw.json` | JSON, top-level config |
| Persona | `~/.openclaw/workspace/SOUL.md` | Agent personality |
| Identity | `~/.openclaw/workspace/IDENTITY.md` | Agent identity doc |
| User profile | `~/.openclaw/workspace/USER.md` | User preferences |
| Tools desc | `~/.openclaw/workspace/TOOLS.md` | Tool descriptions |
| Agents desc | `~/.openclaw/workspace/AGENTS.md` | Agent descriptions |
| Memory | `~/.openclaw/memory/main.sqlite` | SQLite with FTS5 + embeddings |
| Sessions | `~/.openclaw/agents/main/sessions/` | JSONL files |
| Extensions | `~/.openclaw/extensions/` | Installed extensions (WeChat, Weibo, etc.) |
| Credentials | `~/.openclaw/credentials/` | Auth JSON files |
| Identity (device) | `~/.openclaw/identity/` | device.json, device-auth.json |
| Cron | `~/.openclaw/cron/` | Scheduled tasks |
| MCP config | `~/.openclaw/workspace/config/mcporter.json` | MCP server configs |
| Workspace skills | `~/.openclaw/workspace/skills/` | Skill definitions |
| Browser data | `~/.openclaw/browser/` | Browser profiles, cache |
| Logs | `~/.openclaw/logs/` | Usually skip for migration |

**Data directory structure:**

```
~/.openclaw/
├── openclaw.json            # Main config (models, MCP, extensions, channels, credentials)
├── workspace/
│   ├── SOUL.md              # Agent personality
│   ├── IDENTITY.md          # Agent identity
│   ├── USER.md              # User preferences
│   ├── AGENTS.md            # Agent descriptions
│   ├── TOOLS.md             # Tool descriptions
│   ├── HEARTBEAT.md         # Heartbeat config
│   ├── config/mcporter.json # MCP server configs
│   ├── memory/              # Working memory
│   └── skills/              # Skill definitions
├── memory/
│   └── main.sqlite          # Long-term memory (FTS5 + vector embeddings)
├── agents/main/sessions/    # Session records (JSONL)
├── credentials/             # Platform auth (Feishu, WeChat, etc.)
├── identity/                # Device authentication
│   ├── device.json
│   └── device-auth.json
├── cron/                    # Scheduled tasks
├── extensions/              # Installed extensions
├── browser/                 # Browser data (usually skip)
└── logs/                    # Logs (usually skip)
```

### Claude Code

| Category | Path | Notes |
|----------|------|-------|
| Config | `~/.claude/settings.json` | JSON, env vars, plugins |
| Persona (global) | `~/.claude/CLAUDE.md` | Global instructions (if exists) |
| Persona (project) | `<project>/CLAUDE.md` | Per-project instructions |
| Memory | `~/.claude/memory.md` or in projects | Auto-managed memory file |
| Sessions | `~/.claude/sessions/` | Session transcripts |
| Projects | `~/.claude/projects/` | Per-project settings + memory |
| History | `~/.claude/history.jsonl` | Command history |
| Skills | `~/.claude/skills/` | Custom skill directories |
| Todos | `~/.claude/todos/` | Session todo items |
| Plugins | `~/.claude/plugins/` | Installed plugins |
| Stats | `~/.claude/stats-cache.json` | Usage stats (optional) |
| Shell snapshots | `~/.claude/shell-snapshots/` | Shell state (optional) |
| Transcripts | `~/.claude/transcripts/` | Full conversation logs |
| Env vars / API keys | Environment variables or `~/.claude/.env` | `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, etc. |

**Data directory structure:**

```
~/.claude/
├── settings.json            # Global settings (API keys via env, plugins, language)
├── CLAUDE.md                # Global instructions (if exists)
├── .env                     # Environment variables (if exists)
├── memory.md                # Agent memory (if exists)
├── sessions/                # Session records
├── projects/                # Per-project settings and memory
│   └── -path-to-project/
│       ├── CLAUDE.md        # Project-level instructions
│       └── ...
├── skills/                  # Custom skills
├── plugins/                 # Installed plugins
├── history.jsonl            # Command history
├── todos/                   # Session todo items
├── transcripts/             # Full conversation logs
├── stats-cache.json         # Usage statistics (optional)
├── file-history/            # File edit history
└── shell-snapshots/         # Shell state (optional)
```

---

## Step 3: Packaging (Source Machine)

### Hermes — Lean Pack (recommended)

```bash
cd ~
tar czf hermes-clone.tar.gz \
  .hermes/config.yaml \
  .hermes/SOUL.md \
  .hermes/.env \
  .hermes/auth.json \
  .hermes/channel_directory.json \
  .hermes/memories/ \
  .hermes/memory_store.db \
  .hermes/state.db \
  .hermes/sessions/ \
  .hermes/skills/ \
  .hermes/context_length_cache.yaml \
  .hermes/pairing/ \
  .hermes/channels/ \
  2>/dev/null
```

### Hermes — Full Pack (same architecture only)

```bash
cd ~
# WARNING: hermes-agent/venv and bin/ are architecture-specific!
# Only use if source and target are same OS + architecture
tar czf hermes-clone-full.tar.gz \
  .hermes/ \
  --exclude='.hermes/checkpoints' \
  --exclude='.hermes/migration' \
  --exclude='.hermes/*.db-shm' \
  --exclude='.hermes/*.db-wal'
```

### OpenClaw — Lean Pack

```bash
cd ~
tar czf openclaw-clone.tar.gz \
  .openclaw/openclaw.json \
  .openclaw/workspace/ \
  .openclaw/memory/ \
  .openclaw/agents/main/sessions/ \
  .openclaw/credentials/ \
  .openclaw/identity/ \
  .openclaw/cron/ \
  .openclaw/extensions/ \
  2>/dev/null
```

### OpenClaw — Full Pack

```bash
cd ~
tar czf openclaw-clone-full.tar.gz \
  .openclaw/ \
  --exclude='.openclaw/browser' \
  --exclude='.openclaw/logs'
```

### Claude Code — Lean Pack

```bash
cd ~
tar czf claude-code-clone.tar.gz \
  .claude/settings.json \
  .claude/CLAUDE.md \
  .claude/memory.md \
  .claude/skills/ \
  .claude/projects/ \
  2>/dev/null
```

### Claude Code — Full Pack

```bash
cd ~
tar czf claude-code-clone-full.tar.gz \
  .claude/ \
  --exclude='.claude/debug' \
  --exclude='.claude/ide' \
  --exclude='.claude/paste-cache' \
  --exclude='.claude/shell-snapshots'
```

### Pack ALL Frameworks (one-liner)

```bash
cd ~ && tar czf agent-backup-$(date +%Y%m%d).tar.gz \
  .hermes/config.yaml .hermes/SOUL.md .hermes/.env .hermes/auth.json \
  .hermes/memories/ .hermes/memory_store.db .hermes/state.db \
  .hermes/sessions/ .hermes/skills/ .hermes/context_length_cache.yaml \
  .openclaw/openclaw.json .openclaw/workspace/ .openclaw/memory/ \
  .openclaw/agents/main/sessions/ .openclaw/credentials/ .openclaw/identity/ \
  .claude/settings.json .claude/CLAUDE.md .claude/skills/ .claude/projects/ \
  2>/dev/null && echo "Done: $(du -sh agent-backup-$(date +%Y%m%d).tar.gz | cut -f1)"
```

---

## Step 4: Target Environment Preparation

### Prerequisites Check

Run on the **target** machine:

```bash
echo "=== OS ===" && uname -a
echo "=== Architecture ===" && uname -m  # x86_64, aarch64, armv7l
echo "=== Disk ===" && df -h ~ | tail -1
echo "=== Memory ===" && free -h | grep Mem
echo "=== Python ===" && python3 --version 2>/dev/null || echo "NOT FOUND"
echo "=== Node.js ===" && node --version 2>/dev/null || echo "NOT FOUND"
echo "=== SQLite ===" && sqlite3 --version 2>/dev/null || echo "NOT FOUND"
echo "=== Git ===" && git --version 2>/dev/null || echo "NOT FOUND"
```

### Install Framework (if not already)

```bash
# Hermes
pip install hermes-agent

# OpenClaw
npm install -g openclaw

# Claude Code
npm install -g @anthropic-ai/claude-code
```

---

## Step 5: Deployment (Target Machine)

### Hermes Deploy

```bash
cd ~

# 1. Install Hermes first (creates initial directory structure)
pip install hermes-agent

# 2. Stop Hermes if running
pkill -f hermes 2>/dev/null

# 3. Extract backup
tar xzf hermes-clone.tar.gz

# 4. Architecture adaptation
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
  echo "Non-x86_64 detected ($ARCH) — disabling tirith"
  sed -i 's/tirith_enabled: true/tirith_enabled: false/' ~/.hermes/config.yaml 2>/dev/null
fi

# 5. Recreate venv (architecture-specific, cannot copy from source)
cd ~/.hermes/hermes-agent 2>/dev/null && python3 -m venv venv && ./venv/bin/pip install -e . 2>/dev/null

# 6. Verify database compatibility
sqlite3 ~/.hermes/state.db "SELECT * FROM schema_version;" 2>/dev/null || echo "state.db may need rebuild"

# 7. Clean up environment-specific config (DELETE, don't comment!)
#    See "Environment-Specific Config Cleanup" section below for details.
#    Key items:
#    - DELETE MCP servers that only work on source OS (e.g. windows-mcp on non-WSL)
#    - DELETE ollama provider if target has no ollama
#    - DELETE channels that require hardware not present on target
#    - UPDATE API key endpoints for target network
#    - ENSURE Node.js is in PATH (needed for MCP servers)

# 8. Create symlink
mkdir -p ~/.local/bin
ln -sf ~/.hermes/hermes-agent/venv/bin/hermes ~/.local/bin/hermes 2>/dev/null

# 9. Test
hermes doctor 2>/dev/null || echo "Run 'hermes' to verify manually"
```

### Environment-Specific Config Cleanup (All Frameworks)

**Critical principle: DELETE environment-specific config blocks, do NOT just comment them out.** Commented-out blocks can still be parsed by some frameworks, cause confusing warnings, or make future debugging harder.

#### Hermes config.yaml cleanup checklist

| Config block | When to delete | Why |
|-------------|---------------|-----|
| `windows-mcp` under `mcp_servers` | Target is NOT WSL | Requires Windows host filesystem at `/mnt/` |
| `ollama` under `custom_providers` | Target has no ollama installed | Connection errors on every request |
| Any MCP server with `localhost:PORT` | Service not running on target | Timeout delays on startup |
| WSL-specific paths (`/mnt/c/...`) | Target is NOT WSL | Path resolution failures |
| Channel configs (weixin, telegram) | Target doesn't have credentials | Auth errors |

#### OpenClaw openclaw.json cleanup checklist

| Config block | When to delete | Why |
|-------------|---------------|-----|
| `extensions` entries | Extension not installed on target | Startup errors |
| `channels` entries | Channel credentials invalid on target | Auth failures |
| `mcpServers` entries | Server not reachable from target | Connection timeouts |

#### Claude Code settings.json cleanup checklist

| Config block | When to delete | Why |
|-------------|---------------|-----|
| `env.ANTHROPIC_BASE_URL` | URL unreachable from target | All API calls fail |
| `enabledPlugins` | Plugin not available | Warnings / errors |

#### How to delete blocks from YAML (Hermes)

When SSH'd into a remote machine, use a Python script via base64 to surgically remove config blocks:

```python
# Example: remove windows-mcp block from config.yaml
import sys
path = sys.argv[1]
with open(path, "r") as f:
    lines = f.readlines()
result = []
in_block = False
for line in lines:
    if "windows-mcp" in line and ":" in line:
        in_block = True
        continue  # skip this line
    if in_block:
        if line.strip() and not line.startswith(" ") and not line.startswith("#"):
            in_block = False
            result.append(line)
        else:
            continue  # skip lines within the block
    else:
        result.append(line)
with open(path, "w") as f:
    f.writelines(result)
```

Apply the same pattern for any other environment-specific block by changing the keyword in the `if` check.

### OpenClaw Deploy

```bash
cd ~

# 1. Stop OpenClaw if running
pkill -f openclaw 2>/dev/null

# 2. Extract backup
tar xzf openclaw-clone.tar.gz

# 3. Ensure proper permissions
chmod 600 ~/.openclaw/credentials/*.json 2>/dev/null
chmod 600 ~/.openclaw/identity/*.json 2>/dev/null
chmod 700 ~/.openclaw/

# 4. Adapt config:
#    - Update any hardcoded paths in openclaw.json
#    - Verify network reachability of API endpoints
#    - Re-link extensions if paths changed

# 5. Verify memory DB
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT count(*) FROM chunks;" 2>/dev/null || echo "Memory DB issue"

# 6. Test
openclaw --version 2>/dev/null || echo "Verify manually"
```

### Claude Code Deploy

```bash
cd ~

# 1. Extract backup
tar xzf claude-code-clone.tar.gz

# 2. Adapt settings:
#    - Update env vars in settings.json (ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL)
#    - Or set them in shell: export ANTHROPIC_AUTH_TOKEN=xxx
#    - Or use ~/.claude/.env if available
#    - Check plugin compatibility

# 3. Per-project CLAUDE.md files must be in their respective project dirs
#    If you have project-level CLAUDE.md, restore them to the correct paths

# 4. Test
claude --version 2>/dev/null || echo "Verify manually"
claude  # Start interactive session
```

---

## Step 6: Cross-Architecture Compatibility Matrix

Critical when source and target have different CPU architectures:

| Data Type | x86→x86 | x86→arm64 | arm64→x86 | arm64→arm64 |
|-----------|---------|-----------|-----------|-------------|
| **Config files** (YAML/JSON/MD) | ✅ Copy | ✅ Copy | ✅ Copy | ✅ Copy |
| **SQLite databases** | ✅ Copy | ✅ Copy | ✅ Copy | ✅ Copy |
| **Text skills** (*.md, *.py) | ✅ Copy | ✅ Copy | ✅ Copy | ✅ Copy |
| **Python venv** | ✅ Copy | ❌ Rebuild | ❌ Rebuild | ✅ Copy |
| **Native binaries** (tirith, etc.) | ✅ Copy | ❌ Reinstall | ❌ Reinstall | ✅ Copy |
| **Node modules** (native deps) | ✅ Copy | ⚠️ Check | ⚠️ Check | ✅ Copy |
| **npm global packages** | ✅ Copy | ❌ Reinstall | ❌ Reinstall | ✅ Copy |

**Rule of thumb**: Pure text/data files are portable. Anything compiled (venv, binaries, native node modules) must be rebuilt on target.

---

## Step 7: Version Compatibility

### Hermes
- `state.db` has a schema version. Check with: `sqlite3 ~/.hermes/state.db "SELECT * FROM schema_version;"`
- Minor version differences (e.g., v0.9.0 → v0.10.0) may have schema changes
- **Recommendation**: If target has a newer version, install it first, let it create a fresh DB, then test importing the old one. If incompatible, keep the new DB and only restore config/skills/memories.

### OpenClaw
- `memory/main.sqlite` uses FTS5 and embedding vectors
- Schema may differ between versions
- **Recommendation**: Prefer letting the new version create its DB, then migrate content if needed

### Claude Code
- `settings.json` schema is simple and stable
- `projects/` structure may evolve but is generally backward-compatible
- **Recommendation**: Low risk, just copy

---

## Step 8: Security & Privacy

### Sensitive Data Checklist

Before transferring ANY backup, be aware these files contain secrets:

| Framework | File | Contains |
|-----------|------|----------|
| Hermes | `.env` | API keys, tokens |
| Hermes | `auth.json` | Auth tokens |
| Hermes | `config.yaml` | May contain MCP server URLs, provider keys inline |
| OpenClaw | `credentials/` | Platform auth (WeChat, Feishu, etc.) |
| OpenClaw | `identity/device-auth.json` | Device authentication |
| OpenClaw | `openclaw.json` | May contain API keys |
| Claude Code | `settings.json` | `ANTHROPIC_AUTH_TOKEN` in env section |
| Claude Code | `.env` (if exists) | API keys, base URLs |

### Transfer Recommendations

```bash
# Option A: SCP over LAN (encrypted in transit via SSH)
scp agent-backup.tar.gz targethost:~

# Option B: Encrypted archive (recommended for public networks)
tar czf - <files> | gpg --symmetric --cipher-algo AES256 -o agent-backup.tar.gz.gpg
# On target:
gpg -d agent-backup.tar.gz.gpg | tar xzf -

# Option C: rsync over SSH
rsync -avz --progress agent-backup.tar.gz targethost:~
```

### NEVER commit these to public repos:
- `.env` files
- `auth.json`, `credentials/`
- `settings.json` (contains tokens)
- `identity/device-auth.json`
- Any file containing API keys or auth tokens

---

## Step 9: Post-Deploy Verification

### Hermes
```bash
hermes doctor
# Then inside a hermes session:
# - memory → should show saved memories
# - fact_store search "test" → should return results
# - session_search → should show past sessions
# - skills_list → should show all skills
# - Test MCP server connections
```

### OpenClaw
```bash
openclaw --version
# Start openclaw and verify:
# - Memory recall works
# - Extensions load (check channels)
# - Workspace files present (SOUL.md, USER.md)
# - Sessions history accessible
```

### Claude Code
```bash
claude --version
claude
# Then verify:
# - /memory → shows saved memories
# - Settings loaded (check env vars)
# - Skills available
# - Projects and their CLAUDE.md files
```

---

## Practical Tips for Remote Migration

When migrating via SSH, you'll hit shell quoting hell trying to run Python one-liners on the remote machine. Use **base64 encoding** to bypass all quoting issues:

```bash
# Local machine: encode a Python script, pipe to remote python3
import base64
script = '''
import sqlite3
c = sqlite3.connect("/home/user/.hermes/state.db")
print("sessions:", c.execute("SELECT count(*) FROM sessions").fetchone()[0])
'''
encoded = base64.b64encode(script.encode()).decode()
# Then: ssh user@host 'echo <encoded> | base64 -d | python3'
```

This pattern is infinitely more reliable than trying to nest quotes across bash → ssh → python.

### Other lessons from real deployments

- **Hermes venv installed via `uv` has no `pip`**: The `hermes doctor` warning about "reinstall entry point" can be ignored if `hermes` binary already works. `uv` installs don't include pip in the venv.
- **state.db schema v6 is compatible from v0.9.0 → v0.10.0**: Verified in practice. Both versions use `SCHEMA_VERSION = 6`.
- **Windows-MCP and other environment-specific configs must be DELETED, not commented**: On a non-WSL target (bare metal Linux, Pi, Mac), delete the entire `windows-mcp:` block from config.yaml. Commenting leaves dead config that can cause confusing errors later. Same principle: delete any MCP server, provider, or channel that references hardware/OS/software not present on the target.
- **Node.js PATH**: If hermes installed Node in `~/.hermes/node/bin/`, add to `~/.bashrc`: `export PATH=$HOME/.hermes/node/bin:$PATH`

---

## Troubleshooting

### "state.db schema mismatch" (Hermes)
- Let the new version create a fresh state.db
- Only restore: config, SOUL.md, memories/, skills/, .env

### "tirith segfault" (Hermes)
- Binary is wrong architecture. Set `tirith_enabled: false` in config.yaml

### "MCP server won't connect"
- Check Node.js is in PATH: `which npx`
- Check network reachability: `curl <mcp-server-url>`
- Check config paths are valid on target

### "Memory DB locked/corrupt" (OpenClaw/Hermes)
- Ensure no other instance is running
- Copy without `-shm` and `-wal` files
- Run `sqlite3 <db> "PRAGMA integrity_check;"`

### "API key not working"
- Some keys are bound to IP/machine. Regenerate for new environment
- Check endpoint URLs are reachable from new network

### "Python venv broken"
- Never copy venv across architectures. Always rebuild:
```bash
cd ~/.hermes/hermes-agent
rm -rf venv
python3 -m venv venv
./venv/bin/pip install -e .
```

---

## Cross-Framework Migration

Want to move data FROM one framework TO another? Here's the mapping:

| From → To | Config | Persona | Memory | Skills |
|-----------|--------|---------|--------|--------|
| Hermes → OpenClaw | Manual rewrite | SOUL.md → workspace/SOUL.md | MEMORY.md → workspace/memory/ | Manual port |
| OpenClaw → Hermes | Manual rewrite | workspace/SOUL.md → SOUL.md | memory/main.sqlite → text extraction → memories/ | Manual port |
| Claude Code → Hermes | Manual rewrite | CLAUDE.md → SOUL.md | memory.md → memories/ | Manual port |
| Hermes → Claude Code | Manual rewrite | SOUL.md → CLAUDE.md | memories/ → memory.md | skills/ → manual |
| Any → Any | Manual | Copy MD content | Extract to text | Rewrite |

Cross-framework migration is NOT automatic — frameworks have fundamentally different architectures. But persona (personality markdown) and memory (text content) are the most portable elements.

---

## Channel Conflict Warning

When running multiple agent instances with the **same credentials** (e.g., same WeChat bot token on both WSL and Pi), messaging channels will conflict:

- **Last-connection-wins**: The instance that connects last takes over the channel
- **Unstable behavior**: Messages may route to either instance unpredictably, or connections may drop repeatedly
- **Solution**: Only enable channels on ONE instance. On the backup/secondary machine, either:
  - Delete the channel config blocks from config.yaml (e.g. `weixin` section)
  - Or simply don't start that instance when the primary is running
  - If both must run, use different bot tokens / channel accounts

### Hermes weixin (微信) channel details
- Credentials stored in: `~/.hermes/weixin/accounts/`, `~/.hermes/pairing/weixin-approved.json`
- The bot token in `weixin/accounts/<id>@im.bot.json` can only sustain one long-poll connection at a time
- If you clone these files to a second machine, both instances will fight over the same WeChat connection

---

## Verified Deployments

### Raspberry Pi (aarch64) — tested 2026-04-17
- **Source**: WSL x86_64, Hermes v0.9.0, schema_version=6
- **Target**: Pi arm64 (aarch64), Debian 13, Hermes v0.10.0
- **Result**: Fully compatible. state.db schema v6 works on v0.10.0 (both use SCHEMA_VERSION=6)
- **Lean pack size**: 14MB (805 files: config, SOUL.md, memories, state.db, memory_store.db, 91 skills, 106 sessions)
- **Actions taken**:
  1. `tirith_enabled: false` (arm64 has no tirith binary)
  2. Deleted `windows-mcp` block from config.yaml (not WSL)
  3. Added `export PATH=$HOME/.hermes/node/bin:$PATH` to `~/.bashrc`
  4. Synced local SKILL.md to Pi
- **uv-installed venv**: No pip in venv, hermes doctor warns "reinstall entry point" but hermes binary works fine — safe to ignore
- **hermes doctor result**: All core checks pass (Python, packages, config, memories, state.db, skills, Node.js, API connectivity)
