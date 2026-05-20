# JSON控制字符导致JS解析崩溃的诊断与修复

## 症状
HTML页面在浏览器中加载后**完全无法点击**——所有按钮无响应，脚本未执行。

## 根因
JSON内嵌在HTML的`<script>`标签中时，如果字符串值内包含**literal控制字符**（换行`\n`、制表`\t`、回车`\r`），JS严格JSON解析器会报`Invalid control character`错误，脚本执行中断。

Python的`json.dumps`在默认模式下会正确转义这些字符，但以下情况会导致控制字符泄露：
- 使用`json.dumps(indent=2)`时，indent参数不影响字符串内部的转义
- 通过正则替换`const KNOWLEDGE = {...}`时，如果替换字符串来自未经过`json.dumps`的Python字典
- 长文本来自web搜索返回的原始文本，包含真实换行符

## 诊断命令

```python
import re, json

with open('ai_quiz.html', 'r', encoding='utf-8') as f:
    html = f.read()

k_start = html.find('const KNOWLEDGE = {')
# 找到匹配的结束}
depth = 0
in_string = False
esc = False
for i in range(k_start + len('const KNOWLEDGE = '), len(html)):
    c = html[i]
    if esc: esc = False; continue
    if c == '\\': esc = True; continue
    if c == '"' and not esc: in_string = not in_string; continue
    if in_string: continue 
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            json_str = html[k_start + len('const KNOWLEDGE = '):i+1]
            try:
                json.loads(json_str)
                print("✅ JSON有效")
            except json.JSONDecodeError as e:
                print(f"❌ 错误位置{e.pos}: {json_str[e.pos-30:e.pos+30]}")
            break
```

## 修复方法

### 方案A：从破损JSON恢复（已有HTML时）

```python
# 提取原始JSON并修复字符串内的控制字符
def fix_json_control_chars(bad_json):
    result = []
    i = 0
    in_str = False
    esc = False
    while i < len(bad_json):
        c = bad_json[i]
        if esc:
            result.append(c); esc = False; i += 1; continue
        if c == '\\':
            result.append(c); esc = True; i += 1; continue
        if c == '"':
            in_str = not in_str; result.append(c); i += 1; continue
        if in_str:
            if c == '\n': result.append('\\n')
            elif c == '\t': result.append('\\t')
            elif c == '\r': result.append('\\r')
            else: result.append(c)
        else:
            result.append(c)
        i += 1
    return ''.join(result)

fixed = fix_json_control_chars(raw_json)
data = json.loads(fixed)  # 验证修复是否成功
```

### 方案B：预防（生成HTML时）

```python
# 始终通过json.dumps序列化，自动处理所有转义
import json
knowledge_json = json.dumps(knowledge_data, ensure_ascii=False)
html_snippet = f'const KNOWLEDGE = {knowledge_json};'
```

## 防御性检查

生成/修改HTML后必须验证JSON块可被`json.loads`解析（见上方诊断命令）。

## 历史事故
- 2026-05-20: 2249题AI题库HTML，15张知识卡含真实换行符→JS崩溃→用户收到完全无法点击的页面。根因为`re.sub`替换KNOWLEDGE块时直接拼接Python字符串（含`\n`），未经过`json.dumps`。
