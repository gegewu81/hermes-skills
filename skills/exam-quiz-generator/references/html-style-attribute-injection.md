# HTML Style Attribute Injection Bug

## 症状
- 页面部分渲染（标题+按钮可见），但JSON数据泄漏为可见文本
- `ALL_QUESTIONS` / `KNOWLEDGE` 变量 `undefined`
- `browser_console` → `js_errors` 可能为空或显示 `SyntaxError: Unexpected string`
- `document.querySelectorAll('script').length` 返回 1 但 `textContent` 无法正常解析
- `document.body.innerHTML.length` 异常（远小于预期，因为script被解析器吞噬）

## 根因
CSS inline style 属性值中出现**尾随逗号**导致引号未闭合：

```html
<!-- ❌ 错误：margin-top:40px 后面多了个逗号 -->
<footer style="text-align:center; ...; margin-top:40px,">
    © 版权所有
</footer>
```

HTML解析器将 `style="..."` 后的内容全部当作属性值吞噬，直到遇到下一个 `"` 才"闭合"。如果附近有JSON数据块（如 `const KNOWLEDGE = {...}`），JSON中的 `"` 会被误用作属性闭合符，导致大量JSON内容被注入到HTML body中。

## 复现条件
1. 程序化生成HTML（Python f-string / 模板拼接）
2. style属性值末尾有逗号、分号缺失等格式错误
3. `<script>` 标签内嵌大型JSON（`KNOWLEDGE` / `ALL_QUESTIONS`）

## 检测方法

### 快速检测（browser_navigate后）
```javascript
// 如果 variables undefined 但 script tag 存在 → 疑似注入
var v = typeof ALL_QUESTIONS;  // 'undefined' = 异常
var s = document.querySelectorAll('script').length;  // 应该 ≥1
```

### 代码检测（Python脚本）
```python
import re

with open('ai_quiz.html', 'r') as f:
    html = f.read()

# 检查所有HTML属性是否正常闭合
# 匹配 style="..." 或任意 attr="..." 模式，检测值末尾是否有逗号
pattern = r'(style|data-\w+)="([^"]*),'
matches = re.findall(pattern, html)
if matches:
    for attr, val in matches:
        print(f"⚠️ {attr} 属性末尾有逗号: ...{val[-30:]}")
```

## 修复
1. 删除尾随逗号
2. 清除泄漏到body中的JSON文本
3. 重新验证 `browser_console` → ALL_QUESTIONS 不再 undefined

## 预防
- 生成HTML时用模板引擎（如Jinja2），避免字符串拼接
- 或者对每个 `style="..."` 属性做 `rstrip(',')` 处理
- 浏览器验证清单中增加：检查 `ALL_QUESTIONS` / `KNOWLEDGE` 是否为 `undefined`
