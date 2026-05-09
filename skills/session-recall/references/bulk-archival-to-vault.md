# Bulk Archival to Obsidian Vault

When the user asks to "archive all valuable historical conversations to the vault," this is a distinct workflow from recall — it's a systematic sweep and write operation.

## When to Use

- User says "go through all historical sessions and archive the valuable ones to the vault"
- User says "export important conversations to Obsidian"
- Periodic knowledge base maintenance

## Workflow

### Phase 1: Parallel Topic Search (6-8 clusters)

Don't browse sequentially. Issue parallel `session_search()` calls across topic clusters:

```
Cluster 1: Hermes 架构 — HA, profile, multi-provider, gateway, config
Cluster 2: 项目实战 — 6G, 树洞, MCP, Windows, WSL2, Samba
Cluster 3: 记忆系统 — memory, fact_store, holographic, session-recall, FTS5
Cluster 4: 磁盘/存储 — badblocks, sdc, disk, NAS, legacy-disk
Cluster 5: 安全 — immune-system, CVE, audit, redact
Cluster 6: Obsidian/知识库 — vault, Samba, Obsidian-skill
Cluster 7: 其他 — PI4, 语音助手, 功耗优化
Cluster 8: Semantic search fallback (for hard-to-find topics)
```

Use `session_semantic_search.py` for topics that FTS5 misses (Chinese queries, abstract concepts).

### Phase 2: Identify High-Value Sessions

For each cluster, select sessions that:
- Produced a lasting decision, architecture, or methodology
- Resolved a non-trivial technical problem
- Created or significantly modified a skill/project
- Have rich summaries (not "[Raw preview — summarization unavailable]")

Skip: pure status checks, quick Q&A, session handoffs, cronjob outputs.

### Phase 3: Write Archives in Batches

Use `execute_code` with `from hermes_tools import write_file` for batch writes. Don't write files one at a time — batch 10-15 per call.

**Vault path**: `/mnt/disk_c1/vaults/hermes-knowledge/` (PI4 Samba Vault)

**Session archive template** (`sessions/YYYY-MM-DD-topic.md`):
```markdown
---
date: YYYY-MM-DD
tags: [session]
model: <model-used>
platform: cli|weixin
---

# YYYY-MM-DD <title>

## 概述
1-2 sentence summary

## 关键决策
- Decision → why
- Decision → why

## 产出
- File created / config changed / skill created

## 待办 (optional)
- Unresolved items

## 关联
- [[related-knowledge]]
- [[related-project]]
```

**Knowledge note template** (`knowledge/topic-name.md`):
```markdown
---
date: <today>
tags: [knowledge]
domain: hermes-internal|hermes-infra|linux-tools
source: <session dates/IDs>
trust: 0.8-0.95
---

# <title>

## 核心概念
One-line definition

## 详细信息
Expanded explanation

## 关键命令 / 配置
Copy-paste ready code blocks

## 踩坑记录
Problems encountered and solutions

## 关联
- [[related-note]]
- [[related-project]]
```

### Phase 4: Update Index

After all archives are written, update:
1. **README.md** — Add new entries to the content index tables
2. **Project notes** (projects/) — Update progress timelines for active projects

### Phase 5: Verify

```bash
echo "sessions: $(ls vault/sessions/ | wc -l)"
echo "knowledge: $(ls vault/knowledge/ | wc -l)"
echo "projects: $(ls vault/projects/ | wc -l)"
```

## Pitfalls

- **Subagent timeout**: Don't delegate the full archival to subagents. session_search calls are slow and subagents time out at 600s. Do the searching yourself in the main session, then batch-write files.
- **Duplicate detection**: Check what's already in the vault before writing (`ls -1 vault/sessions/`). Don't overwrite existing archives.
- **File size**: Keep session archives under 2KB each. Knowledge notes can be longer (up to 5KB) for dense technical content.
- **Frontmatter consistency**: All files must have YAML frontmatter with at minimum `date` and `tags`.
- **Cross-references**: Use `[[wikilink]]` format for Obsidian backlinks. Don't link to files that don't exist.
- **Session IDs vs titles**: Session filenames use dates+topics (human-readable), not raw session IDs. Session IDs go in the `source` field of knowledge notes.
