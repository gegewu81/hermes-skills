# Semantic Search Deployment Reference

## Architecture

```
~/.hermes/scripts/session_embedder.py   -- Build embedding index (full/incremental)
~/.hermes/scripts/session_semantic_search.py -- Query index by cosine similarity
~/.hermes/session_index.db              -- SQLite DB (session_embeddings table)
~/.hermes/.glm_quota_state.json         -- Quota tracking (placeholder)
```

Embedding model: Zhipu **embedding-3** (2048-dim vectors)
API: `https://open.bigmodel.cn/api/paas/v4/embeddings`

## Index Schema

```sql
CREATE TABLE session_embeddings (
    session_id TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,       -- struct.pack 2048 floats
    summary_text TEXT NOT NULL,    -- extracted user messages + tool names
    msg_count INTEGER DEFAULT 0,
    started_at REAL,               -- parsed from session_id timestamp
    indexed_at REAL NOT NULL
);
```

Storage: each embedding = 2048 × 4 bytes = 8 KB. 1242 sessions = ~10 MB.

## Text Extraction Logic

From each session JSON:
1. Extract all `role=user` messages (max 500 chars each, total 2000 chars)
2. Extract all assistant tool_call names → "Tools used: tool1, tool2, ..."
3. Concatenate as summary_text for embedding
4. Skip sessions with <20 chars of text

## Commands

```bash
# Full rebuild (first deployment or after schema change)
python3 ~/.hermes/scripts/session_embedder.py --full

# Incremental update (only new sessions, cron job)
python3 ~/.hermes/scripts/session_embedder.py

# Index statistics
python3 ~/.hermes/scripts/session_embedder.py --stats

# Semantic search (human-readable)
python3 ~/.hermes/scripts/session_semantic_search.py "查询文本" --top 5

# Semantic search (JSON for programmatic use)
python3 ~/.hermes/scripts/session_semantic_search.py "查询文本" --top 5 --json
```

## Cron Maintenance

Job: `session-embedder-daily` (job_id: 5f513bafe0e8)
Schedule: daily at 3:00 AM Asia/Shanghai
Mode: no_agent (runs script directly, no LLM)
Script: `session_embedder.py` (incremental by default, no --full flag)

## Cost Model

- Embedding API call: ~1000 tokens per search query
- Index build: ~30万 tokens for 1242 sessions (one-time)
- Incremental: proportional to new sessions since last index
- NOT covered by GLM Coding Plan chat quota — separate embedding API billing

## When To Rebuild

Full rebuild (`--full`) needed when:
- Schema change in session_embeddings table
- Embedding model upgrade (e.g., embedding-3 → embedding-4)
- Index corruption detected
- Summary text extraction logic changed

Otherwise, incremental mode is sufficient.

## Failure Modes

1. **GLM_API_KEY missing**: `session_embedder.py` reads from `~/.hermes/.env` (GLM_API_KEY=...). Falls back to env var.
2. **No session files**: Check `~/.hermes/sessions/session_*.json` exists
3. **API rate limit**: Batch size=16, 0.5s sleep between batches to avoid throttling
4. **Empty index after build**: Check if sessions have user messages (skip threshold: <20 chars)
5. **Search returns no results**: Index may be stale, run incremental update first
