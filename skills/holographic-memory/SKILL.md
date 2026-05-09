---
name: holographic-memory
description: Deploy, configure, and customize the Holographic memory provider for Hermes Agent — Chinese regex auto_extract, on_pre_compress hook, plugin config structure, and known pitfalls.
version: 1.0.0
metadata:
  hermes:
    tags: [memory, holographic, plugin, chinese, configuration]
---

# Holographic Memory Provider

Holographic is the recommended memory provider for Hermes: zero-config, zero-network, SQLite + FTS5 + HRR vector store with trust scoring and 5-layer retrieval. This skill covers deployment, customization, and debugging.

## Key Files

```
~/.hermes/hermes-agent/plugins/memory/holographic/
├── __init__.py      # HolographicMemoryProvider class (main logic)
├── store.py          # MemoryStore — SQLite + FTS5 + HRR BLOB storage
├── retrieval.py      # 5-layer retrieval pipeline
├── holographic.py    # HRR vector encoding (dim=1024)
├── plugin.yaml       # Plugin metadata, version, hooks
└── README.md
```

Config: `~/.hermes/config.yaml`
DB: `~/.hermes/memory_store.db` (auto-created)

## Config Structure (TWO-LEVEL)

Holographic reads config from `plugins.hermes-memory-store` section, NOT from `memory.*`:

```yaml
memory:
  provider: 'holographic'        # ← tells Hermes which provider to use
  memory_enabled: true
  user_profile_enabled: true

plugins:
  hermes-memory-store:            # ← Holographic plugin reads THIS section
    auto_extract: true            # enable auto-extract on session end
    default_trust: 0.5
    db_path: $HERMES_HOME/memory_store.db
    hrr_dim: 1024
    min_trust_threshold: 0.3
```

Loading logic in `__init__.py`:
```python
def _load_plugin_config() -> dict:
    all_config = yaml.safe_load(open(config_path))
    return all_config.get("plugins", {}).get("hermes-memory-store", {}) or {}
```

## on_pre_compress Hook

### Interface

```python
# From agent/memory_provider.py (ABC)
def on_pre_compress(self, messages: List[Dict[str, Any]]) -> str:
```

### CRITICAL: Return value is DISCARDED

`run_agent.py` line ~6778 calls `self._memory_manager.on_pre_compress(messages)` WITHOUT assigning the return value. The method must persist facts as a **side-effect** inside the method body, not rely on the return value being passed to the compressor.

```python
def on_pre_compress(self, messages: List[Dict[str, Any]]) -> str:
    # ... extract content from last N messages ...
    # MUST persist here as side-effect:
    self._store.add_fact(content[:800], category="project", tags="pre-compress")
    return ""  # return value is ignored by caller
```

### plugin.yaml Hook Declaration

Must declare `on_pre_compress` in hooks list for it to fire:

```yaml
hooks:
  - on_session_end
  - on_pre_compress
```

## Chinese Regex auto_extract

The `_auto_extract_facts` method matches user messages against regex patterns. Original only had English patterns. Chinese patterns added:

### No \b for Chinese

CJK has no word boundaries — never use `\b` in Chinese regex. Use non-capturing groups with optional following character:

```python
# WRONG: re.compile(r'\b我喜欢\b(.+)')   # \b doesn't work with CJK
# RIGHT: re.compile(r'(?:我喜欢)\S?(.{2,80})')
```

### Pattern Categories

| Category | Config category | Trigger examples |
|----------|----------------|-----------------|
| 偏好/喜好 | `user_pref` | 我喜欢/我偏好/我习惯用/我常用 |
| 习惯/行为 | `user_pref` | 我通常/我总是/我每次都/我从不 |
| 记忆指令 | `user_pref` | 记住/别忘了/以后注意/记一下 |
| 决策 | `project` | 我们决定/方案确定/项目采用 |
| 环境 | `environment` | 系统是/运行在/部署在/OS是 |

### Capture Group Length

Use `.{2,80}` not `.+` — limits capture to prevent storing entire messages as facts.

## Store API Reference

```python
store = provider._store

# Add fact (UNIQUE constraint on content — auto-dedup)
store.add_fact(content, category="user_pref", tags="auto-extract")

# Search (NOT "search" — it's "search_facts")
facts = store.search_facts(query, limit=10)

# Each fact dict has: content, category, tags, trust, created_at, entity_id
```

## Known Pitfalls

### 1. `initialize()` requires `session_id`
```python
# WRONG: p.initialize()
# RIGHT:
p.initialize(session_id="some-session-id")
```

### 2. Method is `search_facts`, not `search`
```python
# WRONG: p._store.search("keyword")
# RIGHT:
p._store.search_facts("keyword", limit=10)
```

### 3. FTS5 Chinese tokenization is limited
SQLite default `unicode61` tokenizer splits Chinese by character, not by word. FTS search for Chinese keywords may not match as expected. HRR vector retrieval (another layer in the 5-layer pipeline) compensates. For better Chinese FTS, consider `simple` tokenizer or jieba integration.

### 4. execute_code quote escaping
When using `execute_code` with `terminal()`, avoid nested `python3 -c "..."` with double quotes. Always write a script file to `/tmp/` and run it instead:

```python
# WRONG in execute_code (SyntaxError: unterminated string):
terminal('python3 -c "import sqlite3; conn=sqlite3.connect(\"...\")"')

# RIGHT:
write_file("/tmp/check.py", "import sqlite3\n...")
terminal("python3 /tmp/check.py")
```

### 5. HRR Bank Capacity
dim=1024, bank capacity ~256 items. SNR degrades above that. Acceptable for typical use. Increase `hrr_dim` in config if needed (costs more memory).

## Verification Checklist

After deploying or modifying Holographic:

1. **Syntax check**: `python3 -c "import ast; ast.parse(open('__init__.py').read())"`
2. **Import test**: `from plugins.memory.holographic import HolographicMemoryProvider`
3. **Instantiate**: `p = HolographicMemoryProvider(config={"auto_extract": True})`
4. **Initialize**: `p.initialize(session_id="test")`
5. **Auto-extract test**: Send Chinese+English test messages, check DB
6. **DB verification**: `sqlite3 ~/.hermes/memory_store.db "SELECT category, substr(content,1,80) FROM facts"`
7. **Restart Hermes**: Changes take effect on next session (not mid-conversation)

## ByteRover vs Holographic Decision

Chose Holographic over ByteRover because:
- ByteRover requires external `brv` CLI binary (npm/curl install, may need VPN in China)
- ByteRover uses subprocess calls with 10s/120s timeouts
- ByteRover has no dedup, no trust scoring, potential network callbacks to byterover.dev
- Holographic is pure Python, zero-config, fully auditable
- Holographic has entity resolution, trust scoring, 5-layer retrieval
