---
name: sensitive-data-redact
description: "Safely redact sensitive data (passwords, keys) from Hermes data stores. Covers the critical pitfall of binary replacement on SQLite databases and the recovery procedure if it happens."
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [security, database, hermes, redaction, sqlite, recovery]
    category: devops
---

# Sensitive Data Redaction from Hermes Data Stores

When a user shares a password or secret and later asks to remove it from all stored data, follow this protocol.

## ⚠️ CRITICAL PITFALL: NEVER binary-replace SQLite databases

**What happened (2026-04-19):** Used `sed -i 's/password/***REDACTED***/g'` on `state.db` and `state.db-wal`. The replacement changed string length (8 bytes → 14 bytes), shifting all subsequent bytes and corrupting SQLite page headers. Result: `database disk image is malformed` with hundreds of `btreeInitPage() returns error code 11` errors.

**Rule: SQLite databases are binary formats. Byte-length changes destroy page structure.** Never use sed, perl -pi, or any binary replacement on `.db`, `.db-wal`, `.db-shm` files.

## Safe Redaction Protocol

### Step 1: Text files — use literal replacement

Do not put a secret in a shell command, argument, environment variable, or
regular expression. Shell history and process listings can retain it. Regex
characters can also change which text gets replaced.

Use the bundled helper. It prompts without echoing the secret, treats it as
literal UTF-8 text, skips symlinks and binary files, and defaults to a dry run.
Run it in an interactive local terminal, never through chat or a remote prompt.

These file types are eligible:

- Session JSON files: `~/.hermes/sessions/*.json`
- Session JSONL files: `~/.hermes/sessions/*.jsonl`
- Skills: `~/.hermes/skills/**/*.md`
- Config/logs: `~/.hermes/logs/*.log`, `~/.hermes/*.yaml`, `~/.hermes/*.md`
- Scripts: `~/.hermes/scripts/*`, `~/.hermes/skills/**/scripts/*`

```bash
python3 ${HERMES_SKILL_DIR}/scripts/redact_text_files.py --root ~/.hermes
python3 ${HERMES_SKILL_DIR}/scripts/redact_text_files.py --root ~/.hermes --apply
```

Review every skipped-file warning. Increase `--max-bytes` only after checking
the file type and available memory.

### Step 2: SQLite databases — use SQL UPDATE

For `state.db` (sessions, messages) and `memory_store.db` (Holographic Memory):

```python
from getpass import getpass
import sqlite3

secret = getpass("Secret to redact: ")
if not secret:
    raise SystemExit("Secret cannot be empty")

with sqlite3.connect("/home/<username>/.hermes/state.db") as conn:
    if conn.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise SystemExit("Database is not healthy. Stop and restore it first.")
    conn.execute(
        "UPDATE messages SET content = REPLACE(content, ?, ?) "
        "WHERE instr(content, ?) > 0",
        (secret, "***REDACTED***", secret),
    )
    integrity = conn.execute("PRAGMA integrity_check").fetchone()
    if integrity != ("ok",):
        raise RuntimeError(f"Integrity check failed: {integrity!r}")
```

Stop the Hermes gateway before changing a database. Parameterized SQL treats
the secret literally and keeps it out of source text. SQLite safely handles row
growth when the replacement length differs.

### Step 3: Verify

```bash
# A second dry run must report 0 matches.
python3 ${HERMES_SKILL_DIR}/scripts/redact_text_files.py --root ~/.hermes
# Check database integrity
python3 -c "import sqlite3; c=sqlite3.connect('$HOME/.hermes/state.db'); print(c.execute('PRAGMA integrity_check').fetchone())"
```

## Disaster Recovery: Rebuilding state.db from Session JSONs

If state.db gets corrupted (e.g., from the binary replacement mistake above), it can be rebuilt from the session JSON files which are the ground truth.

### Recovery Procedure

```python
import sqlite3, os, glob, json

session_dir = os.path.expanduser("~/.hermes/sessions")
json_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")))
db_path = os.path.expanduser("~/.hermes/state.db")

# 1. Backup corrupted DB
os.rename(db_path, db_path + ".corrupted")
for ext in ["-wal", "-shm"]:
    p = db_path + ext
    if os.path.exists(p):
        os.remove(p)

# 2. Create fresh database
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA page_size=4096")
conn.executescript("""
    CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
    CREATE TABLE sessions (
        id TEXT PRIMARY KEY, title TEXT, model TEXT, platform TEXT,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        message_count INTEGER DEFAULT 0
    );
    CREATE TABLE messages (
        id TEXT PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL,
        content TEXT, timestamp TEXT, model TEXT, tool_calls TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    CREATE VIRTUAL TABLE messages_fts USING fts5(
        content, content='messages', content_rowid='rowid', tokenize='unicode61'
    );
    CREATE TRIGGER messages_ai AFTER INSERT ON messages BEGIN
        INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
    END;
    CREATE TRIGGER messages_ad AFTER DELETE ON messages BEGIN
        INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.rowid, old.content);
    END;
    CREATE TRIGGER messages_au AFTER UPDATE ON messages BEGIN
        INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.rowid, old.content);
        INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
    END;
""")
conn.execute("INSERT INTO schema_version VALUES (6)")

# 3. Import all sessions
for fpath in json_files:
    with open(fpath) as f:
        data = json.load(f)
    sid = data.get("session_id", os.path.basename(fpath).replace(".json", ""))
    messages = data.get("messages", [])
    conn.execute(
        "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?)",
        (sid, data.get("title",""), data.get("model",""), data.get("platform",""),
         data.get("session_start",""), data.get("last_updated",""), len(messages))
    )
    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        if isinstance(content, list):
            content = json.dumps(content)
        conn.execute(
            "INSERT OR REPLACE INTO messages VALUES (?,?,?,?,?,?,?)",
            (f"{sid}_{i}", sid, msg.get("role",""), content,
             msg.get("timestamp", data.get("session_start","")),
             msg.get("model", data.get("model","")),
             json.dumps(msg.get("tool_calls",[])) if msg.get("tool_calls") else None)
        )
conn.commit()

# 4. Rebuild FTS index
conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
conn.commit()
print(f"OK: {conn.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]} sessions, "
      f"{conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]} messages")
conn.close()
```

### Recovery Notes

- Session JSON files in `~/.hermes/sessions/` are the **ground truth**. They survive database corruption.
- `session_id` field name varies — check both `data.get("session_id")` and `data.get("id")`.
- The FTS rebuild can take 30+ seconds for large datasets.
- After recovery, the gateway needs to reload the database (restart or reconnect).
- Holographic Memory (`memory_store.db`) is separate and not rebuilt by this procedure.
- `sqlite_sequence` is an internal SQLite table — never try to CREATE it explicitly (raises `object name reserved for internal use`).

## Memory/Holographic Store Redaction

For `memory_store.db` (Holographic Memory), inspect its schema first. Update
only allowlisted tables that have a `content` column:

```python
from getpass import getpass
import os
import sqlite3

secret = getpass("Secret to redact: ")
if not secret:
    raise SystemExit("Secret cannot be empty")

with sqlite3.connect(
    os.path.expanduser("~/.hermes/memory_store.db")
) as conn:
    if conn.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise SystemExit("Database is not healthy. Stop and restore it first.")
    for table in ("facts", "entities"):
        columns = {
            row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')
        }
        if "content" not in columns:
            continue
        conn.execute(
            f'UPDATE "{table}" SET content = REPLACE(content, ?, ?) '
            "WHERE instr(content, ?) > 0",
            (secret, "***REDACTED***", secret),
        )
    integrity = conn.execute("PRAGMA integrity_check").fetchone()
    if integrity != ("ok",):
        raise RuntimeError(f"Integrity check failed: {integrity!r}")
```
