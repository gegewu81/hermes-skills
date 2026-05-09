# LLM Prefix Caching — How It Works and Why It Matters for Provider Selection

## The Mechanism

LLM inference has two phases:
1. **Prefill** — process the entire prompt (system + history + user message) through all Transformer layers, computing Key/Value vectors (KV cache) for every token. Purely parallel, cost proportional to prompt length.
2. **Decode** — generate tokens one at a time, using the KV cache from prefill.

**Prefix caching** = the API server saves the KV cache from prefill and reuses it when the next request has the same prefix.

```
Request 1: [system(20k tokens)] + [history(1k)] + [question]
             ↳ full prefill, save KV cache for prefix

Request 2: [system(20k tokens)] + [history(1k)] + [new_history(500)] + [question]
             ↳ first 21k tokens match → skip prefill, reuse KV cache
             ↳ only compute the new 500 tokens
```

## Economic Impact

| Scenario | Without Cache | With Cache Hit |
|----------|--------------|----------------|
| 20k system prompt | Full prefill every request (~2-3s) | Skip (~50ms) |
| Input cost | 100% | 10% (Anthropic/OpenAI pricing for cached input) |
| Latency | High | Significantly reduced |

## What Breaks Cache

- **Any change** in the prefix (even one character, even a trailing newline)
- System prompt changes
- Tool list changes (tools are part of the prompt)
- Model change
- TTL expiry (Anthropic: 5 min ephemeral, OpenAI: varies)
- Different API account/endpoint

## How Hermes Maximizes Cache Hits

1. **Gateway Agent instance cache** — `_agent_config_signature()` SHA256 of (model + api_key + tools + config). If signature matches, reuse frozen Agent instance → identical system prompt + tools sent to API.
2. **Codex/OpenAI transport** — auto-injects `prompt_cache_key = session_id`
3. **Anthropic transport** — auto-injects `cache_control: {"type": "ephemeral"}` on system blocks
4. **Tool registry generation** — incremented on MCP reload, which busts cache intentionally

Cache-busting config keys: `model.context_length`, `compression.*`, `agent.disabled_toolsets`, `ephemeral_prompt`.

## Provider-Specific Notes

### Anthropic
- `cache_control: {"type": "ephemeral"}` — 5 min TTL (changed from 1h in early 2026)
- Cached input priced at 10% of base
- Minimum prefix: 1024 tokens for Sonnet/Opus, 2048 for Haiku
- No user-configurable cache key — client auto-manages

### OpenAI (Codex/Responses API)
- `prompt_cache_key` parameter — server-side session-based caching
- Automatic prompt caching for prompts > 1024 tokens
- Cached input at 50% discount (varies by model)

### Zhipu GLM (zai)
- No confirmed public docs on prefix caching as of 2026-05
- If supported, Hermes's Agent instance cache still helps by reducing prompt variance
- Worth testing: send identical prompts rapidly and check if latency drops

## Practical Tips

1. **Don't change tools mid-session** — adding/removing MCP servers busts cache
2. **Don't switch models mid-session** — trivially busts cache
3. **Keep ephemeral system prompts stable** — avoid dynamic injection that changes per turn
4. **Long system prompts benefit most** — the longer the frozen prefix, the bigger the savings
5. **Planner-Executor pattern helps** — weak main agent keeps its system prompt frozen (high hit rate), strong delegate model is only invoked for depth work (lower total cached volume, but higher value per cached request)
