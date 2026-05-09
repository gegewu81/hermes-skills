---
name: state-db-repair
description: state.db 诊断、增量修复与全量重建。覆盖 .jsonl/.json 双格式、title UNIQUE 约束 bug、WAL 并发写入等已知坑。
version: 2.0.0
metadata:
  hermes:
    tags: [hermes, state-db, sqlite, recovery, sessions]
---

# state.db 诊断与修复

## 触发条件

- `session_search` 搜不到已知存在的历史对话
- state.db 文件大小异常小（正常应随使用增长）
- session 文件存在但 DB 中 session 数远少于文件数
- `INSERT OR IGNORE` 返回 rowcount=0 但 SELECT 又找不到记录
- state.db 被意外重置/损坏

## 关键文件

```
~/.hermes/state.db          # 主数据库
~/.hermes/sessions/         # 会话记录目录
  ├── *.jsonl               # 会话文件（标准流式格式）
  ├── session_*.json        # 会话文件（完整转储格式，常被忽略！）
  ├── cron_*.jsonl          # cron job 会话（通常不需要手动处理）
  ├── request_dump_*.json   # API 请求转储（无需导入）
  └── sessions.json         # 活跃 session 映射（无需导入）
```

**关键：`session_*.json` 也是有效数据源！** 它们是完整会话转储（session_meta + 全部 messages），
跨平台分叉（CLI→微信延续）或异常退出时产生，经常不在 state.db 中。
修复时必须同时处理 `.jsonl` 和 `.json`。

实际案例 (2026-04-24): PI节点 475个session文件中只有107个在DB中，368个完全缺失（全是.json）。
根因是 title UNIQUE 约束导致 INSERT OR IGNORE 静默跳过。修复后 478个session、43,203条消息入库。

## Hermes 源码修复 (2026-04-24)

已修复 `hermes_state.py` 中的 schema 缺陷：
- **文件**: `~/.hermes/hermes-agent/hermes_state.py`
- **改动**: migration v4 和 post-migration 中的 `CREATE UNIQUE INDEX idx_sessions_title_unique` → `CREATE INDEX idx_sessions_title`
- **影响**: 新部署/重置后不会再出现 UNIQUE 约束问题
- **已有数据库**: 仍需手动 `DROP INDEX IF EXISTS idx_sessions_title_unique` 修复

## 诊断流程（先跑这个，不要直接重建）

```
1. 对比文件数 vs DB session 数
   file_ids = {json文件名提取的session_id} ∪ {jsonl文件名提取的session_id}
   db_ids = SELECT id FROM sessions
   missing = file_ids - db_ids

2. 如果 missing > 0:
   a. 检查 UNIQUE 约束 → DROP INDEX IF EXISTS idx_sessions_title_unique
   b. 增量导入缺失文件
   c. 重建 FTS

3. 如果 missing = 0 但搜不到:
   a. 检查 FTS 索引是否与 messages 数一致
   b. 可能需要 FTS rebuild
```

## 增量修复流程（推荐）

无需重建整个库，只补缺失的部分。

```python
# 1. 备份
shutil.copy2(db_path, f"{db_path}.bak.{datetime.now():%Y%m%d_%H%M%S}")

# 2. 找出缺失 session
# file_ids vs db_ids 取差集

# 3. 移除 title UNIQUE 约束（关键！）
c.execute("DROP INDEX IF EXISTS idx_sessions_title_unique")

# 4. 遍历缺失文件，逐个 INSERT OR IGNORE
# .json: json.load → data['messages'] → INSERT session + messages
# .jsonl: 逐行 json.loads → 跳过 session_meta → INSERT messages
# session_id 优先用文件内的 session_id 字段（比文件名更可靠）

# 5. 重建 FTS
c.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")

# 6. 验证
```

## 全量重建流程（数据库损坏时）

1. 确认环境和节点
2. 备份现有 state.db
3. 删除旧 db，用下方 DDL 重建表结构
4. 遍历 `.jsonl` + `.json` 文件，解析并导入
5. 重建 FTS 索引：`INSERT INTO messages_fts(messages_fts) VALUES('rebuild')`
6. 验证

## 建表 DDL

```sql
CREATE TABLE schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version VALUES (1);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT,
    model TEXT,
    model_config TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_sessions_started ON sessions(started_at);
CREATE INDEX idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX idx_sessions_source ON sessions(source);
CREATE INDEX idx_sessions_title ON sessions(title);
-- 注意：title 索引是普通的，不是 UNIQUE！

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_details TEXT,
    codex_reasoning_items TEXT
);

CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

## 文件格式

### .jsonl（标准流式）

每行一个 JSON 对象：

| role | 说明 | 典型 keys |
|------|------|-----------|
| `session_meta` | 会话元信息（第1行，可选） | role, model, platform, tools, timestamp |
| `user` | 用户消息 | role, content, timestamp |
| `assistant` | 助手回复 | role, content, timestamp, tool_calls, finish_reason, reasoning |
| `tool` | 工具调用结果 | role, content, timestamp, tool_call_id/name/call_id |

文件名 = session_id（去掉 `.jsonl`），格式 `YYYYMMDD_HHMMSS_hash`

### .json（完整转储）

单个完整 JSON 对象：

```json
{
  "session_id": "20260421_170331_703aa2",
  "model": "glm-5-turbo",
  "platform": "weixin",
  "session_start": "2026-04-21T17:03:31.547172",
  "last_updated": "2026-04-21T17:05:27.463785",
  "system_prompt": "...",
  "tools": [...],
  "message_count": 13,
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "...", "reasoning": "...", "tool_calls": [...], "finish_reason": "..."},
    {"role": "tool", "content": "...", "tool_call_id": "..."}
  ]
}
```

session 元信息从顶层字段提取（session_id、platform、model、session_start、last_updated）。
**session_id 优先使用文件内 `session_id` 字段，比文件名更可靠。**

## 字段映射

| sessions 列 | .jsonl 来源 | .json 来源 |
|-------------|-------------|------------|
| id | 文件名去掉 `.jsonl` | data.session_id |
| source | meta.platform 或 `'cli'` | data.platform 或 `'cli'` |
| model | meta.model 或 `'unknown'` | data.model 或 `'unknown'` |
| started_at | 第一条消息 timestamp 或文件名时间 | data.session_start |
| ended_at | 最后一条消息 timestamp | data.last_updated |
| title | 第一条 user 消息前 60 字符 | 同左 |

| messages 列 | 来源 |
|-------------|------|
| session_id | 文件名 / data.session_id |
| role | line.role |
| content | line.content |
| tool_calls | json.dumps(line.tool_calls) |
| tool_call_id | line.tool_call_id 或 line.call_id |
| tool_name | line.tool_name 或 line.name |
| timestamp | line.timestamp（无则从 session_start 递增 0.1s） |
| reasoning | line.reasoning |
| finish_reason | line.finish_reason |

**不可恢复字段：** input_tokens, output_tokens, cache_*_tokens, reasoning_tokens, cost 相关。

## 坑和注意事项

### 1. ⚠️ title 列 UNIQUE 约束 bug（最常见的隐秘数据丢失原因）

Hermes schema v4 会在 `sessions.title` 上创建 UNIQUE 索引
`idx_sessions_title_unique`。当多个 session 的首条用户消息相同时（如空消息、
"树洞"、"/help"等短文本），`INSERT OR IGNORE` 会因 title 冲突而**静默跳过
整个 session**，无任何报错。

**诊断：**
```sql
PRAGMA index_list(sessions);  -- 查看是否有 title_unique
SELECT title, COUNT(*) FROM sessions GROUP BY title HAVING cnt > 1;  -- 重复 title
```

**修复：**
```sql
DROP INDEX IF EXISTS idx_sessions_title_unique;
```

**症状：** session 文件存在且内容完好，但 session_search 搜不到、DB session 数
远少于文件数、INSERT OR IGNORE 返回 rowcount=0 但 SELECT 找不到记录。

### 2. ⚠️ FTS rebuild 会清除触发器（重启后新消息不进FTS）

执行 `INSERT INTO messages_fts(messages_fts) VALUES('rebuild')` 后，FTS内容同步触发器
会被删除。Hermes 重启时 `_init_schema` 用 `SELECT * FROM messages_fts LIMIT 0` 检测
表是否存在——表在，就不执行 FTS_SQL（含触发器创建）。结果是**新消息不进FTS**，
session_search 只能搜到rebuild时的历史数据，越来越过时。

**修复：** rebuild后必须手动重建三个触发器：
```sql
CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```

**验证：** 插入测试消息后 FTS MATCH 能搜到。

### 3. WAL 模式并发写入

Hermes 使用 WAL journal mode，state.db 可能被 gateway 进程并发写入：
- `sqlite3.connect(db_path, timeout=30)` 增加超时
- WAL 文件（`state.db-wal`）超过 10MB 说明有大量未 checkpoint 的写入
- 发现批量静默失败时优先检查 UNIQUE 约束（第1条），而非 WAL 问题

### 3. 部分文件无 session_meta（.jsonl）

CLI session 可能没有 `session_meta` 行，第一条直接是 `user`。
此时 source=`'cli'`、model=`'unknown'`。

### 4. 部分消息无 timestamp

从文件名提取时间：`datetime.strptime(fname[:15], '%Y%m%d_%H%M%S')`
每条消息递增 0.1s 避免时间戳重复。

### 5. FTS5 中文分词有限

`unicode61` 分词器按字符拆中文，搜索"功耗"可能搜不到包含"功耗"的消息。
HRR 向量（holographic memory）可兜底。不影响数据完整性。

### 6. FTS 搜索需要 JOIN

FTS 表只有 `content` 列，查 session_id/role 需 JOIN messages 表：
```sql
SELECT m.session_id, m.role, substr(m.content,1,80)
FROM messages_fts f JOIN messages m ON f.rowid = m.id
WHERE messages_fts MATCH '关键词';
```

### 7. 当前活跃 session 不在文件中

正在运行的 session 可能尚未写入文件。Hermes 会自动处理，无需手动导入。

### 8. 备份先于一切

```python
shutil.copy2(db_path, f"{db_path}.bak.{datetime.now():%Y%m%d_%H%M%S}")
```

### 9. .db 文件操作规则

**绝对禁止** sed/patch/awk 操作 .db 文件（会导致二进制损坏）。
必须用 sqlite3 或 Python sqlite3 模块操作。

## 验证清单

- [ ] sessions 表行数 ≈ session 文件总数（.json + .jsonl，排除 cron）
- [ ] messages 表行数 == FTS 索引行数
- [ ] FTS 搜索能命中已知关键词
- [ ] FTS 触发器存在（`SELECT name FROM sqlite_master WHERE type='trigger'`，应有3个 messages_fts_*）
- [ ] `idx_sessions_title_unique` 索引已被移除
- [ ] 文件在但 DB 没有的 gap 为 0：`file_ids - db_ids`
- [ ] 时间戳合理（非 0 或 1970）
- [ ] 备份文件存在且大小正常
