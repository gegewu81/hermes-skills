---
name: hermes-multi-provider
description: "Configure and optimize multiple LLM providers in Hermes Agent. Decision framework plus config patterns for three routing strategies: fallback, delegation, and smart routing."
tags: [hermes, provider, routing, config]
version: "1.0"
---

# Hermes Multi-Provider Configuration

## Trigger Conditions

Load this skill when:
- User says multiple providers or wants to configure two or more inference providers
- User asks about fallback, routing, delegation, or provider pooling
- User mentions specific providers (GLM/zai, DeepSeek, OpenRouter)
- User asks about prompt caching, prefix caching, cache hit rate, or KV cache optimization
- User asks about "strong model for X, weak model for Y" role-based routing

## References

- `references/prefix-caching.md` — LLM prefix caching mechanics, provider-specific behavior, and Hermes cache architecture

## First Principle: Resource Analysis

Before configuring, analyze the economics of each provider:

| Type | Economics | Strategy |
|---|---|---|
| Subscription/Fixed plan | Fixed monthly cap, waste if unused | Primary daily driver, run up to cap |
| Pay-as-you-go | Diminishing balance | Reserve for depth work and fallback |
| Free tier | Limited, rate-limited | Consume first, expires if unused |

Do NOT assume stronger model equals default model. The answer depends on cost structure.

## Three Routing Mechanisms

### 1. fallback_model — Auto-Failover

When primary returns 429 or 503, fallback kicks in automatically. The block at config.yaml bottom is commented out by default -- must uncomment.

```yaml
fallback_model:
  provider: deepseek
  model: deepseek-v4-pro
```

### 2. delegation — Sub-Agent Isolation

Sub-agents spawned by delegate_task can use a different provider:

```yaml
delegation:
  model: deepseek-v4-pro
  provider: deepseek
```

Leave base_url and api_key empty to inherit from environment. This is the cleanest way to route complex tasks without auto-classification heuristics.

### 3. credential_pool_strategies — Key Pooling

For providers with multiple API keys, pool them to survive rate limits:

```yaml
credential_pool_strategies:
  zai:
    enable_pool: true
    strategy: sequential
    exhaustion_cooldown: 120
```

## Planner-Executor Delegation Pattern

Use a strong model for planning/analysis/advisory, a cheaper model for daily execution. The key insight: delegation is Hermes's built-in "role assignment" — the main agent is the front desk, delegates are specialists.

> **注意**：此模式已演进为上面的「三层模型架构」，推荐直接用三层方案。以下保留作为原理说明。

```yaml
model:
  default: glm-5-turbo        # 弱模型：日常对话、执行任务（省钱）
  provider: zai

delegation:
  model: deepseek-v4-pro      # 强模型：深度分析、架构规划、问题诊断
  provider: deepseek
```

Usage flow:
1. User asks complex question → main agent (weak) recognizes depth needed
2. `delegate_task(goal="...", model={strong_model})` → strong model does analysis
3. Strong model returns structured analysis → weak model presents to user

This also maximizes prefix cache hit rate for the main agent (system prompt frozen, only user messages change), while paying the strong model only for depth work.

**Variants**:
- **Reverse**: strong model main + weak model delegation. Good when daily conversation itself needs intelligence.
- **Manual switch**: use `hermes config set model.default X` for temporary needs, no config file edit.

## Three-Layer Model Architecture (Recommended)

将模型按性价比分为三层，日常走便宜模型，深度按需调强模型：

| 层级 | 角色 | 配置项 | 何时触发 |
|------|------|--------|----------|
| **日常层** | 主模型对话 | `model.default` | 所有直接对话 |
| **执行层** | 子任务/代码 | `delegation.model` | `delegate_task()` 自动路由 |
| **深度层** | 复杂分析 | `delegate_task(model={...})` | 手动指定强模型 |

```yaml
model:
  default: glm-5-turbo          # 日常层：订阅内消耗，免费额度优先
  provider: zai
  base_url: https://open.bigmodel.cn/api/coding/paas/v4

providers:
  deepseek:
    base_url: https://api.deepseek.com
    model: deepseek-v4-flash    # 执行层：极低价，缓存命中0.02元/百万token
    context_length: 128000

fallback_providers:
  - deepseek

credential_pool_strategies:
  zai:
    enable_pool: true
    strategy: sequential
    exhaustion_cooldown: 120

delegation:
  model: deepseek-v4-flash      # 执行层：delegation 默认走 flash 省钱
  provider: deepseek

fallback_model:
  provider: deepseek
  model: deepseek-v4-flash
```

**深度层按需调用**（在 skill 或对话中显式指定）：
```
delegate_task(model={provider: deepseek, model: deepseek-v4-pro})  # DeepSeek 强模型
delegate_task(model={provider: zai, model: glm-5.1})               # 智谱旗舰
```

### 定价参考（2026-05）

| 模型 | 输入价格 | 缓存命中 | 备注 |
|------|----------|----------|------|
| GLM-5-turbo | 智谱 Coding Plan 包含 | — | 5h/80次 每5小时周期 |
| DeepSeek V4-Flash | 极低 | 0.02元/百万token | 性价比最高 |
| DeepSeek V4-Pro | 标准价 | — | 2.5折优惠至 2026-05-31 |
| GLM-5.1 | 比 GLM-5 涨10% | — | SWE-Bench Pro 超越 Opus 4.6 |

> **⚠️ 促销到期注意**：优惠结束后重新评估 V4-Pro 是否仍适合作为深度层，必要时切换到 GLM-5.1 或其他模型。

## Verification

After config change:
```
hermes config check
```

Verify: GLM_API_KEY and DEEPSEEK_API_KEY appear. No syntax errors. fallback_model and delegation show expected providers.

## Pitfalls

1. Leave delegation.base_url and delegation.api_key empty to inherit from env
2. fallback_model has no base_url field -- relies on fallback_providers or env
3. Always backup config.yaml before editing
4. The fallback_model block at file bottom is commented out by default
5. Planner-Executor pattern: if main agent is weak model, it must recognize when to delegate (complex analysis, architecture, debugging). Add explicit delegation hints in skill instructions.
6. Prefix cache hit rate drops to zero if system prompt or tool list changes between requests — keep Agent config stable within a session
