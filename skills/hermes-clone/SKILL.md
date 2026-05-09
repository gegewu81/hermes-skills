---
name: hermes-clone
description: Clone/migrate Hermes Agent to a new environment (e.g. Raspberry Pi). Full data audit, compatibility check, and deployment.
---

# Hermes 完全克隆/迁移

> **NOTE**: 本 skill 已被通用版 `agent-clone` 取代（支持 Hermes/OpenClaw/Claude Code）。
> 本文件保留作为 Hermes 专用细节参考。通用流程请用 `devops/agent-clone`。
> GitHub: https://github.com/gegewu81/agent-clone

## 触发条件
超要把当前 Hermes 实例克隆到新环境时使用。

## 迁移前核查清单

### 1. 目标环境检查
```bash
uname -a                          # 架构 (x86_64 vs aarch64)
df -h /                           # 磁盘空间
free -h                           # 内存
python3 --version                 # 系统Python
sqlite3 --version                 # SQLite CLI
which node && node --version      # Node.js
which npm && npm --version        # npm
hermes --version 2>/dev/null || echo "未安装"
hermes doctor 2>/dev/null
ls -la ~/.hermes/
cat ~/.hermes/config.yaml 2>/dev/null || echo "无配置"
```

### 2. 源环境数据审计
```bash
du -sh ~/.hermes/
du -sh ~/.hermes/*/ | sort -rh
# 关键文件: config.yaml, SOUL.md, .env, auth.json, channel_directory.json
# 记忆: memories/MEMORY.md, memories/USER.md, memory_store.db*
# 会话: state.db*, sessions/
# 技能: skills/
# 通道: pairing/, weixin/
# 外部: ~/shudong/, ~/hermes/
# 架构敏感: file ~/.hermes/bin/tirith, file ~/.hermes/hermes-agent/venv/bin/python
# Schema版本: sqlite3 ~/.hermes/state.db 'SELECT * FROM schema_version;'
```

### 3. 架构兼容性矩阵

| 数据 | x86→x86 | x86→arm64 | arm64→arm64 |
|------|---------|-----------|-------------|
| config.yaml / SOUL.md / .env | 直接拷贝 | 直接拷贝 | 直接拷贝 |
| memories/*.md / memory_store.db | 直接拷贝 | 直接拷贝 | 直接拷贝 |
| state.db | 直接拷贝 | **需验证schema版本** | 直接拷贝 |
| skills/ (Python/MD) | 直接拷贝 | 直接拷贝 | 直接拷贝 |
| bin/tirith | 直接拷贝 | **不兼容, 禁用** | 直接拷贝 |
| hermes-agent/venv | 直接拷贝 | **不兼容** | 直接拷贝 |

### 4. config.yaml 目标环境适配

- **tirith_enabled**: 目标无匹配架构tirith时设 false
- **mcp_servers.windows-mcp**: 非WSL环境必须删除/注释
- **custom_providers.ollama**: 目标无ollama或内存不足时删除
- **MCP servers**: 确认网络可达性
- **.env**: 确认API Keys在新网络可用
- **Node.js PATH**: 确保npx可找到（zhipu-vision MCP依赖）

## 迁移执行

### 打包（源机器）
```bash
tar czf hermes-clone.tar.gz \
  .hermes/config.yaml \
  .hermes/SOUL.md \
  .hermes/.env \
  .hermes/auth.json \
  .hermes/channel_directory.json \
  .hermes/memories/ \
  .hermes/skills/ \
  .hermes/memory_store.db \
  .hermes/state.db \
  .hermes/sessions/ \
  .hermes/pairing/ \
  .hermes/weixin/ \
  .hermes/context_length_cache.yaml \
  shudong/ \
  hermes/
# 排除: bin/tirith(可能不兼容), hermes-agent/(目标自有), checkpoints/, migration/, *.db-shm/*.db-wal
```

### 部署（目标机器）
```bash
cd ~ && tar xzf hermes-clone.tar.gz
ln -sf ~/.hermes/hermes-agent/venv/bin/hermes ~/.local/bin/hermes
# 修改 config.yaml（按第4步）
hermes doctor && hermes
```

## 验证清单

- [ ] hermes 启动不报错
- [ ] memory 返回工作笔记和用户画像
- [ ] fact_store 能搜到历史 fact
- [ ] skills 全部可加载
- [ ] session_search 能搜到历史会话
- [ ] MCP servers 连接正常
- [ ] 树洞数据 ~/shudong/ 完整

## 已知环境: 树莓派 (<pi4-ip>)

- SSH: `ssh <username>@<pi4-ip>` (key auth configured)
- 架构: arm64 (aarch64), Debian 13
- 磁盘: 117G / 105G可用
- 内存: 7.6G / 7.0G可用
- Hermes: v0.10.0 (源机v0.9.0, schema_version=6)
- Python: 3.11.15 (venv) + 3.13.5 (系统)
- Node.js: v22.22.2 (在 ~/.hermes/node/bin/, 需加PATH)
- sqlite3 CLI: 未安装, 需 sudo apt install sqlite3
- 缺失包: croniter, python-telegram-bot (可选)
- state.db schema可能不兼容(v0.9.0→v0.10.0), 需先测试

## Pitfalls

1. **state.db schema**: v0.9.0→v0.10.0 都是 schema_version=6, 实测兼容. 但版本差>1 minor时仍需单独测试.
2. **tirith 架构**: x86_64在arm64上段错误, 必须 tirith_enabled: false
3. **venv 不能跨架构拷贝**: 目标环境独立创建. 注意: uv安装的venv没有pip, hermes doctor报"reinstall entry point"可忽略(hermes二进制已可用).
4. **Node.js PATH**: Pi的node在~/.hermes/node/bin/, 需加.bashrc: `export PATH=$HOME/.hermes/node/bin:$PATH`
5. **环境特定配置必须删除而非注释**: 非WSL环境必须删除windows-mcp块, 非ollama环境删除ollama provider. 注释会留下残留导致混淆. 用base64编码Python脚本远程删除YAML块.
6. **.env 泄露风险**: 含API密钥, 局域网scp可接受
7. **SSH远程执行Python**: bash嵌套引号地狱. 用base64编码绕过: `echo <base64> | base64 -d | python3`. 这个模式在远程迁移中极其有用.
8. **微信通道冲突**: 两台机器共用同一微信bot token时, 后连接的接管通道, 不稳定. 需确保只在一台运行微信通道, 或在备用机的config中禁用weixin通道.
