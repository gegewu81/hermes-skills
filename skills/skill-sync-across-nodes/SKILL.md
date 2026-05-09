---
name: skill-sync-across-nodes
title: Cross-Node Skill Synchronization
description: >-
  Compare, integrate, and sync skills across Hermes nodes (PI/WSL/etc).
  Handles the full workflow: discovery, diff, decide (replace vs integrate),
  deploy, and verify.
tags: [devops, skill-management, multi-node, sync]
version: 1.0.0
---

# Cross-Node Skill Synchronization

## When to Use

When you need to sync a skill between Hermes nodes, or when you discover
different versions of the same concept on different nodes and need to
consolidate.

## Node Architecture

- **Brother nodes data mirror**: `~/.hermes/brothers/<node>/skills/` — read-only snapshot of other nodes' skills
- **Local skills**: `~/.hermes/skills/` — active skills on current node
- Node names: `wsl`, `pi` (etc.)

## Workflow

### Step 1: Discover

Find relevant skills on both nodes:
```bash
# Find skill on brother node
find ~/.hermes/brothers -path "*/<skill-name>/SKILL.md" 2>/dev/null

# Find skill on local
find ~/.hermes/skills -path "*/<skill-name>/SKILL.md" 2>/dev/null
```

### Step 2: Read & Compare

Read both SKILL.md files. Compare:

| Dimension | What to Check |
|-----------|--------------|
| Structure | Metadata (version, tags, description) |
| Attack/Feature Coverage | What each version covers that the other doesn't |
| Operational Detail | Tables vs text, checklists, SOPs |
| Scripts | What scripts/templates each version ships |
| Known Limitations | What each version documents about gaps |

### Step 3: Decide Strategy

先向用户展示**对比表格**，列出每个版本独有的价值，让用户选择 Replace 还是 Integrate。

**Replace** — when one version is clearly superior:
- One is a strict superset of the other
- One version is clearly outdated/incomplete
- No meaningful content in the "weaker" version

**Integrate** — when each has unique value:
- Both have unique content the other lacks
- Different organizational approaches (e.g., tables vs text)
- Different but complementary feature sets

**集成方案表格模板**（呈现给用户决策）：
```
| 区域 | 取自 | 理由 |
|------|------|------|
| 整体结构 | WSL | 更完整，有 version metadata |
| 攻击模式 | WSL 表格 | 比 PI 的文字描述更结构化 |
| 防御 Skill 模板 | PI | WSL 没有 |
```
用户确认后再执行合并。

### Step 4: Execute

**For Replace:**
```bash
cp <source>/SKILL.md <target>/SKILL.md
# Don't forget scripts/ directory if present
cp -r <source>/scripts/ <target>/scripts/
```

**For Integrate:**
1. Write merged SKILL.md with: stronger structure + unique content from both
2. Document which parts came from which source (in commit reasoning, not in the file)
3. Version bump to indicate merge (e.g., v1→v2)

### Step 5: Deploy

Deploy to all target nodes:
```bash
# Copy to brother node mirror (will sync on next mirror update)
cp <local>/SKILL.md ~/.hermes/brothers/<node>/skills/<category>/<skill>/SKILL.md
```

If the skill has different names on different nodes, keep the names different
but ensure content is identical (diff should only show the `name:` field).

### Step 6: Verify

```bash
# Content diff (exclude name field if names differ)
diff <(grep -v '^name:' <file1>) <(grep -v '^name:' <file2>)

# Verify skill is registered
hermes skills list | grep <skill-name>

# Run any included scripts to test
python3 <scripts/test-script.py>
```

### Step 7: Publish to GitHub (Optional)

如果用户希望将整合后的 Skill 发布为开源项目：

1. 创建临时目录，复制 SKILL.md
2. 添加 README.md（中英文描述 + 架构说明 + 部署方式）和 LICENSE
3. **安全审查**（强制）：检查敏感信息泄露
   - 私钥、密码、API Key、PAT、.env 内容
   - 私有 IP、真实用户路径
   - 使用 `github-publish` skill 创建仓库并推送
4. 推送后立即从 remote URL 移除 PAT

## Pitfalls

- **Scripts outside skills/**: Some tools (e.g., `glm_quota_monitor.py`) live in `~/.hermes/scripts/` AND inside skills. Sync both locations.
- **State files**: Don't overwrite runtime state files (`.json` state, `.alerted` markers) — only sync code.
- **Name field**: If nodes use different `name:` in frontmatter, that's OK — the content should match.
- **Read-only brother data**: `~/.hermes/brothers/` is a snapshot. Writing there updates the mirror but doesn't automatically push to the other node. The other node picks it up on its next mirror sync.
- **Don't blindly copy**: Always read and compare first. The "other" version might be worse.
