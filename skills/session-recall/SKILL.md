---
name: session-recall
description: "Systematic session recall — find past work without missing anything. Cross-references memory projects/skills, uses parallel keyword searches, and never relies on surface-level previews alone."
version: 4.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [memory, search, recall, session, cross-reference]
    category: productivity
---

# Session Recall Protocol

Prevent missing relevant past sessions when the user asks vague questions like
"what happened last time", "how did the last task go", or "what were we working on".

## ⛔ 第一法则（不可违反）

**搜索优先级：语义搜索 > FTS5 双语搜索 > 文件级 grep。**

**Step 1 始终先发语义搜索**（Embedding-3 原生理解中文语义，无需翻译）。
仅在语义搜索返回 0 或 <2 个相关结果时，才回退到 FTS5 双语搜索。
FTS5 unicode61 tokenizer 对中文逐字拆分 + 隐式 AND = 系统性假阴性，仅作为兜底。

**语义搜索返回结果时，不要额外跑 FTS5**——避免重复消耗和噪音干扰。
仅在语义搜索结果不足时，FTS5 用于补充关键词精确匹配和 Ranking 噪音场景。

## 根因（为什么纯中文搜不到）

### FTS5 三重惩罚

```
查询: "磁盘测试"   → FTS5: 磁 AND 盘 AND 测 AND 试   ← 逐字拆分 + 隐式AND
查询: "FTS5中文"   → FTS5: F AND T AND S AND 5 AND 中 AND 文  ← 中英混排更惨
```

1. **逐字拆分** — unicode61 tokenizer 按非字母数字字符分割
2. **隐式 AND** — 空格分隔的 token 默认全部必须出现
3. **语义鸿沟** — 用户说"磁盘测试"，原文写"badblocks -w -sv /dev/sdc"，token 零重叠

### LIKE fallback 的局限

`hermes_state.py:1212-1245` 有 CJK LIKE fallback（`%原始连续子串%`），
但只能匹配原文中**完整连续出现**的中文词。原文"对sdc做写入测试"不含"磁盘"→ 0。

### fact_store 更差

`plugins/memory/holographic/store.py:48-49` 的 facts_fts 用同样的 FTS5，
但 `search_facts()` **完全没有 CJK LIKE fallback**。中文搜 fact_store ≈ 必空。

## 强制行为规则

### Rule 1: 中文检测 → 双语首发

任何包含 CJK 字符的搜索 query，发送前必须追加英文技术术语：

```
检测到 CJK → 从下表查映射或自行推演英文术语 → 用 OR 拼接 → 一次发出
```

**高频映射表（必背）：**

| 中文概念 | 强制追加的英文术语 |
|---------|-----------------|
| 磁盘/硬盘/老盘 | badblocks OR sdc OR sdb OR sdd OR disk OR SMART OR fsck |
| 测试/检查/扫描 | test OR scan OR check OR verify OR benchmark |
| 部署/上线/发布 | deploy OR docker OR nginx OR pm2 OR k8s OR release |
| 网页/网站/页面 | web OR browser OR url OR scrape OR html |
| 修复/改bug/排查 | fix OR bug OR patch OR debug OR error OR troubleshoot |
| 搜索/找不到/回忆 | search OR recall OR FTS5 OR miss OR session |
| 推送/GitHub/提交 | git OR push OR commit OR PR OR github OR pull |
| 配置/设置/环境 | config OR yaml OR env OR setting OR setup |
| 报告/方案/文档 | report OR doc OR spec OR plan OR proposal |
| 模型/AI/大模型 | model OR LLM OR fine-tune OR training OR inference |
| 安全/漏洞/审计 | security OR audit OR CVE OR vulnerability OR redact |
| 记忆/数据库/状态 | memory OR state.db OR fact_store OR sqlite |

找不到映射时，用通用发散词：
```
中文词 OR the_english_translation OR related_tool_name OR related_command
```

### Rule 2: session_search 和 fact_store 同等对待

两个搜索系统对中文的假阴性同样严重。对 fact_store 搜索时：
- **永远优先英文术语**
- 中文词可以作为补充，但不要指望它命中

```python
# ✅ 正确
session_search(query="磁盘测试 OR badblocks OR sdc OR disk")
fact_store(search="badblocks OR sdc OR disk")

# ❌ 错误（v2.0 时代实际犯的错误）
session_search(query="磁盘测试")           # → 0
session_search(query="磁盘 disk 老硬盘")   # → 0
session_search(query="磁盘整理 老硬盘 旧盘 SMART")  # → 0
```

### Rule 3: 0 结果 ≠ 不存在

一次双语搜索 0 结果不代表没有相关记录。可能的未命中原因：
1. 英文术语选择不对 → 换一批同义词重搜
2. 跨平台 fork（CLI→微信）→ session 文件未被索引 → 用文件级搜索
3. state.db 被版本升级重建清空 → 查 brother 镜像
4. **Ranking 噪音淹没** → 短关键词被 tool output 高频出现挤到后排 → 用 `grep -rl` 验证

### Rule 4: Session 摘要可能不准确

session_search 返回的是 LLM 生成的摘要，可能与实际内容有偏差。
如果摘要看起来不相关但 session ID 和时间吻合，应该进一步查看。

## 完整协议

### Step 1: 快速感知

```python
session_search()  # 无 query，最近 3 个 session
```

看 previews 但**不做结论**。只是起点。

### Step 2: 识别搜索意图

用户问题属于哪类？
- **具体任务进展** → 直接用英文术语搜索（Rule 1）
- **模糊回顾**（"上次做了什么"）→ 需要完整协议

### Step 3: 语义搜索（首选，智谱 Embedding-3）⭐

**默认先发语义搜索**，中文直接传入，无需翻译：

```python
# 用自然语言搜索，Embedding-3 原生理解中文
terminal("python3 ~/.hermes/scripts/session_semantic_search.py '磁盘测试进展' --top 5 --json")
```

**为什么优先语义搜索**：

| 维度 | 语义搜索 (Embedding-3) | FTS5 关键词 |
|------|---------------------|-----------|
| 原理 | 2048维向量余弦相似度 | 关键词逐字 AND |
| 中文 | ✅ 原生理解中文语义 | ❌ 逐字拆分假阴性 |
| 噪音 | 不受词频影响 | 高频词淹没低频 |
| 跨语言 | ✅ 理解同义表达 | 语义鸿沟 |
| 速度 | ~1秒（1次API调用） | 毫秒级 |
| 成本 | ~1000 tokens/次 | 免费 |

**限制**:
- 依赖 `~/.hermes/session_index.db`（`session_embedder.py` 构建）
- 每次搜索消耗 1 次 Embedding API 调用
- 索引需增量更新（cron 每日 09:00 自动增量）
- 语义返回的是摘要级匹配，具体细节需进一步查看

### Step 3.5: FTS5 双语搜索（语义搜索的补充/回退）

**触发条件**: 语义搜索返回 0 或 <2 个相关结果

```python
# 并行发出，中文 + 英文发散
session_search(query="磁盘测试 OR badblocks OR sdc OR disk")
fact_store(search="badblocks OR sdc OR disk")
```

FTS5 适用于：精确关键词匹配、代码/命令名搜索、语义搜索索引过期时的兜底。
详见下方「根因」章节理解 FTS5 的中文问题。

> 📁 部署细节、API成本、故障排查见 `references/semantic-search-deployment.md`

### Step 4: 如仍 0 结果，FTS5 换词重搜

换一批英文同义词/相关工具名，例如磁盘话题换成：
```
disk-blocks OR ddrescue OR filesystem OR partition OR mount
```

最多换 2 批词（6 次搜索调用），仍然 0 → Step 5。

### Step 5: 文件级搜索

```bash
# grep 原始 session 文件，绕过 FTS5
grep -rl "关键词" ~/.hermes/sessions/ 2>/dev/null | head -5
```

Session 文件有两种格式：`.jsonl`（已索引）和 `.json`（可能未索引）。
跨平台 fork 的 session 常以 `.json` 存在但不在 state.db 中。

### Step 6: 综合 + 呈现

按项目/任务分组，不是按 session 分组。包括：
- 做了什么、结果如何、当前状态
- 未解决的事项

## 确认失败案例（2026-04，7例，铁证）

| # | 用户说 | 错误做法 | 正确做法 | 根因 |
|---|--------|---------|---------|------|
| 1 | 磁盘测试进展 | 中文×3全空 | `磁盘测试 OR badblocks OR sdc OR disk` → 命中 | 逐字AND+语义鸿沟 |
| 2 | 上次那个网页 | `网页` → 0 | `网页 OR web OR browser OR url` → 命中 | 通用词+AND |
| 3 | 修复情况怎么样 | ×3 "DB not available" | state.db被重建，数据丢失 | 非搜索问题 |
| 4 | 日志陷阱进展 | 中文×3全空 | 同案例1 | 同案例1 |
| 5 | FTS5中文缺陷 | `FTS5 中文 搜索失败` → 0 | `FTS5 OR tokenizer OR unicode61 OR session-search` | **搜索系统无法自引用** |
| 6 | 搜索假阴性 | `search failure OR 假阴性` | 1/3相关 | 英文也只能匹配原文含该短语的 |
| 7 | NAS搭建（英文关键词） | `NAS` → 3个全是测试代码噪音session；`NAS install storage server` → AND逻辑0结果 | `grep -rl "NAS" ~/.hermes/sessions/*0426*.jsonl` → 秒找到5个正确session | **Ranking噪音淹没（非CJK问题）** |

**案例 5 终极讽刺** — 搜索"FTS5缺陷讨论"的对话，FTS5 返回 0。

**案例 7 Ranking噪音淹没（非CJK问题）** — 详见下方"失败模式 #7"专节。

## Anti-Patterns（绝不做的行为）

1. **Never skip semantic search to go straight to FTS5** — 语义搜索是第一选择，FTS5 仅回退
2. **Never send pure-Chinese query to session_search/fact_store** — 回退到 FTS5 时仍需双语（Rule 1）
3. **Never conclude from 3 previews alone** — 总要做定向搜索
4. **Never answer "没有相关记录" after only 1-2 searches** — 语义+FTS5+换词至少 2 轮
5. **Never trust fact_store Chinese results** — 无 CJK LIKE fallback，中文必空
6. **Never search Chinese synonyms repeatedly in FTS5** — 换了中文词还是逐字 AND，不会变好
7. **Never trust session_search ranking for short keywords** — 短关键词极易被噪音淹没

## Pitfalls

- **FTS5 AND vs OR**: 空格分隔默认 AND。用 OR 连接替代词
- **FTS5 ranking 噪音淹没**: 短关键词（如 "NAS"、"docker"）在 tool output 高频出现时，用户对话（仅1-2次提及）会被挤到 rank 第26+名，被 limit=3 截断。本质：FTS5 rank 无法区分"代码变量名高频出现"和"用户对话中少量提及"。**绕过方案：语义搜索 或 `grep -rl` 直接搜 jsonl 文件**。
- **fact_store 无 CJK 兜底**: 对 fact_store 搜索永远优先英文
- **Session 摘要 vs 原文**: 摘要由 LLM 生成，可能遗漏关键信息
- **Orphaned .json 文件**: 跨平台 fork 的 session 可能未索引，需文件级 grep
- **state.db 重建风险**: Hermes 版本升级可能清空历史，brother 节点可能有镜像
- **LIKE fallback 只匹配连续子串**: `%磁盘测试%` 匹配不到"磁盘写入测试完成"
- **Embedding 索引过期**: 新 session 产生后需运行 `session_embedder.py` 增量更新，否则语义搜索看不到新对话。cron 每日 09:00 自动增量
- **Embedding API 成本**: 每次语义搜索=1次 API 调用(~1000 tokens)。不要滥用，仅在 FTS5 失败时启用
- **语义搜索不返回原文**: 只返回 session 摘要文本的相似度排名，要查看完整内容需进一步打开 session 文件

## 失败模式 #7: FTS5 Ranking 噪音淹没（非CJK问题）

### 现象

英文短关键词（如 `NAS`、`docker`）通过 `session_search` 返回的 top-3 session 全是无关噪音，
用户真正想找的对话完全不在结果中。0 结果 ≠ 数据丢失，数据完整但被排名淹没。

### 根因（三层叠加）

1. **FTS5 rank 无噪音区分能力**
   - `nas_system`、`nas_storage` 等 tool output 变量名在测试代码 session 中高频出现（每 session 8-12 条匹配）
   - 用户对话中仅 1-2 次提及"NAS"，rank 远低于噪音 session
   - FTS5 BM25 rank 只看词频，不区分"用户对话"vs"tool output 代码变量"

2. **session_search limit=3 截断**
   - `session_search_tool.py` 默认 `limit = max(1, min(limit, 5))`，去重后只保留 top 3 session
   - 目标 session 排第 26-27 名，被截断
   - 实际 FTS5 有 140 条匹配 / 33 个 session，数据完整

3. **多词 query AND 逻辑雪上加霜**
   - `"NAS install storage server"` → FTS5 要求同时包含所有词 → 0 结果
   - `"NAS搭建 storage server"` → AND + 中文逐字拆分 → 0 结果
   - 多词复合搜索在 ranking 问题之上进一步过滤，命中从 140 骤降到 0

### 诊断方法

```python
# 1. 直接查 FTS5 确认数据存在（绕过 session_search 的 ranking + limit）
python3 -c "
import sqlite3, json
db = sqlite3.connect(' ~/.hermes/state.db')
rows = db.execute('''
    SELECT s.id, s.title, COUNT(*) as hits
    FROM messages_fts f
    JOIN messages m ON m.rowid = f.rowid
    JOIN sessions s ON s.id = m.session_id
    WHERE f.content MATCH ? AND m.source != 'tool'
    GROUP BY s.id ORDER BY hits DESC LIMIT 30
''', ('NAS',)).fetchall()
for r in rows: print(f'{r[0]} | {r[1][:40]} | hits={r[2]}')
"
# 如果目标 session 出现在结果中但排名靠后 → 确认是 ranking 噪音问题
```

```bash
# 2. 终极绕过：grep 原始 jsonl 文件（秒级，绕过 FTS5 全部问题）
grep -rl "NAS" ~/.hermes/sessions/*0426*.jsonl    # 按日期缩窄
grep -rl "NAS" ~/.hermes/sessions/*.jsonl           # 全量扫描
```

### 已知易受影响的关键词

代码/工具名常见于 tool output，极易被噪音淹没：
`NAS`、`docker`、`redis`、`nginx`、`postgres`、`aws`、`k8s`、`api`

### 改进建议（需修改 Hermes 源码，非 skill 层面可解决）

1. ranking 加权：按 session 最近活跃时间加权，近 session rank 提升
2. 来源权重：用户消息(source='user')的匹配权重 > tool output(source='tool')
3. 多词 query 默认 OR 而非 AND（与 `_contains_cjk` 已有的 OR 逻辑对齐）
4. 支持日期过滤参数 `session_search(query="NAS", after="2026-04-25")`

## Bulk Archival — 批量归档到 Obsidian Vault

当用户要求"把有价值的对话归档到 Vault"时，这是一个与 recall 不同的操作——系统性地搜索+写入。

> 📁 完整工作流：并行主题搜索 → 识别高价值会话 → 批量写入 → 更新索引 → 验证
> 详见 `references/bulk-archival-to-vault.md`

**核心要点**：
- 不要委托给 subagent（session_search 太慢，subagent 会超时）
- 自己在主 session 中并行搜索 6-8 个主题集群
- 用 `execute_code` + `write_file` 批量写入（一次 10-15 篇）
- Vault 路径：`/mnt/disk_c1/vaults/hermes-knowledge/`

## Fallback — 文件级搜索

**触发条件**: 双语搜索 + 换词 2 轮 = 0 结果，但确定对话发生过。

```bash
# 1. 按日期找 session 文件
ls -la ~/.hermes/sessions/ | grep "YYYYMMDD"

# 2. grep 关键词（绕过 FTS5）
grep -rl "关键词1\|关键词2" ~/.hermes/sessions/ 2>/dev/null | head -5

# 3. 提取内容
grep -n "关键词" ~/.hermes/sessions/session_YYYYMMDD_XXXXXXXX.json | head -5
```

Session 文件双格式：
- `.jsonl` — 流式格式（state-db-rebuild 可索引）
- `.json` — 完整 dump（可能未被索引，跨平台 fork 常见）
