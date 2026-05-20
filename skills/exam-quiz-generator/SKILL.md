---
name: exam-quiz-generator
description: 题库驱动的AI考试备考系统。从Excel题库自动提取主题→生成知识卡(原理+易混淆点+记忆口诀)→构建交互式HTML刷题网页(含"不知道"按钮、三色标记、知识弹窗)→输出定制学习计划。适用于任何有题库的认证考试。
---

# Exam Quiz Generator — 智能备考系统

## 触发条件
用户提供题库文件(Excel)，需要：刷题练习、知识点学习、备考计划。

## 适用场景
- 任何有Excel题库的认证/资格考试
- 题目类型：单选、多选、判断
- 用户希望高效备考(数天至数月周期均可)

## 工作流程

### Step 1: 读取题库
```python
from openpyxl import load_workbook
wb = load_workbook("题库.xlsx", data_only=True)
ws = wb[sheet_name]  # 确认使用哪个工作表

# 提取格式: [序号, 题型, 题干, 选项文本, 正确答案, A, B, C, D, E]
questions = []
for row in ws.iter_rows(min_row=2, values_only=True):
    # 解析选项、判断题型、构建题目对象
```

### Step 2: 主题自动聚类
用**关键词匹配**将题目分到15-20个知识主题：
- 为每个主题定义3-10个关键词
- 每题匹配第一个命中关键词的主题
- 未匹配的归入"综合"

**主题设计原则：**
- 实操类(如YOLO训练)与概念类(如Transformer架构)分开
- 题量过大(>400)的主题考虑拆分
- 题量过小(<30)的合并到关联主题

### Step 3: 生成初始知识卡
每个主题一张知识卡，三部分结构：

```markdown
## 【主题名】
### 核心原理
- 精炼讲解(3-5个要点)，用粗体强调关键术语
- 可包含公式/参数说明

### 易混淆点
- 列出该主题最易混淆的3-4组概念对
- 用"≠"对比，如"epochs ≠ batch"

### 记忆口诀
- 简短口诀或类比，帮助快速记忆
- 可用emoji标记
```

### Step 3.5: 知识卡验证（⚠️ 考试必备，不可跳过）
**AI生成的初始知识卡存在幻觉风险**——事实错误、过时信息、遗漏关键内容。考试场景必须逐张验证。

**验证策略：**
1. 将15-20个主题分3-4批，每批5-6个主题
2. 每批用一个delegate_task，搜索2-3个关键词验证事实准确性
3. delegate_task直接输出修正后的完整知识卡（原理+易混淆+口诀），标记所有【修改】和【新增】

**delegate_task Prompt模板：**
```
你是AI知识卡审核员，需验证N个主题的知识卡内容准确性。
对每个主题：搜索2-3个关键词验证事实→纠正错误→补充遗漏→保持三部分结构。
用中文回复，标记修改了什么。

现有知识卡：
===【主题名】===
原理：...
易混淆：...
口诀：...
```

**常见错误类型：**
- 事实过时（如"YOLO需要classes.txt"→YOLOv8+不再需要）
- 范围过窄（如"GQA仅LLaMA2 70B用"→LLaMA3/Mistral也广泛用）
- 遗漏核心概念（如CoT缺Self-Consistency/ToT变体）
- 判断绝对化（如"投诉分类用BERT"→不限于BERT，可用其他NLP模型）

**综合知识卡特殊处理：**
综合/通用知识卡通常初始内容极薄（几十字空话），需在验证指令中明确要求补全：学习范式、过欠拟合、偏差方差、激活函数、损失函数、梯度下降变体等核心基础。

### Step 4: 构建交互刷题网页
生成单文件HTML(所有题目+知识卡内嵌)，包含：

**核心功能：**
- 四种模式：全部刷题 / 错题本 / 完全不会 / 按主题筛选
- "不知道"按钮：独立于ABCD选项，标记为🔴最高优先级
- 三色标记系统：🟢会 / 🟡错(含猜对) / 🔴完全不会
- 知识弹窗：答错或点"不知道"后自动弹出该题主题的完整知识卡
- 顺序/随机切换
- localStorage持久化(关闭浏览器不丢失)

**UI规范：**
```css
/* 暗色主题 + 移动适配 */
body { background:#0f172a; color:#e2e8f0; }
/* 选项按钮状态: 默认→悬停→选中→正确→错误 */
/* "不知道"按钮: 虚线边框，琥珀色 */
/* 知识面板: 折叠动画，scrollIntoView */
```

**技术要点：**
- 所有2249题用JSON嵌入HTML
- 主题名称映射表嵌入JS
- 知识卡对象嵌入JS（`const KNOWLEDGE = {...}`）
- 单文件无外部依赖
- **HTML更新方法：** 知识卡修正后，用Python正则替换`const KNOWLEDGE = {...}`块，无需重建整个HTML。⚠️ 必须用`json.dumps(ensure_ascii=False)`序列化（自动处理控制字符转义），详见 `references/json-control-char-fix.md`
  ```python
  import re, json
  html = open('ai_quiz.html').read()
  new_knowledge_str = json.dumps(corrected_knowledge, ensure_ascii=False, indent=2)
  html = re.sub(r'const KNOWLEDGE = \{.*?\};', 
                f'const KNOWLEDGE = {new_knowledge_str};', 
                html, flags=re.DOTALL)
  open('ai_quiz.html','w').write(html)
  ```

### Step 5: 制定学习计划
根据题库规模和备考天数，分四阶段：

| 阶段 | 天数 | 策略 | 日题量 |
|------|------|------|--------|
| 诊断摸底 | 10-15% | 快速过题不恋战，建立三色标记 | 600-800 |
| 知识补强 | 25-30% | 错题驱动学习，逐个主题深挖知识卡 | 50-100 |
| 专项突破 | 35-40% | 模拟考为节点，错题反复练 | 100-200 |
| 冲刺巩固 | 15-20% | 高频错题攻坚+知识卡总复习 | 200-300 |

计划文档输出为Markdown，包含每日任务、主题优先级矩阵、使用技巧。

## 输出物
1. `ai_quiz.html` — 交互刷题网页(800KB+)
2. `ai_exam_study_plan.md` — 详细备考计划
3. `ai_skill_training.html` — 实操训练页（如有技能操作部分），结构见 `references/skill-training-page-pattern.md`
4. `/tmp/quiz_data.json` — 中间数据(可删除)

### 交付注意
微信通道发送HTML文件时可能触发iLink限流。**不要反复重试**——限流有冷却期，连续重试只会重置计时器。降级方案：告知用户文件本地路径，用户自行取用。

## Step 4.5: 浏览器功能验证（⚠️ 交付前必须执行）

**数据验证≠功能验证。** UI应用的唯一有效测试方式是和人一样去交互。跳过这步将导致「页面完全无法点击」等致命缺陷漏出。

### 验证清单（全部通过才能交付）

```python
# 用 browser_navigate + browser_snapshot + browser_click 逐项检查：
```

| # | 检查项 | 方法 | 适用 |
|---|--------|------|------|
| 1 | 页面能加载(标题出现) | `browser_navigate(url)` → snapshot确认标题 | 通用 |
| 2 | 题目列表按钮可点击(全部/错题/不会/未做) | 逐个`browser_click`，确认snapshot出现题目内容 | 理论页 |
| 3 | 选项可点击且有反馈 | 点一个选项，snapshot确认出现"正确"/"错误"提示+正确答案 | 理论页 |
| 4 | "不知道"按钮可用 | 点击后确认标记为🔴+知识弹窗出现 | 理论页 |
| 5 | 知识弹窗有内容 | snapshot确认弹窗包含原理/易混淆/口诀三部分 | 理论页 |
| 6 | 下一题正常切换 | 点击"下一题"，确认题号递增 | 理论页 |
| 7 | 主题筛选可用 | select一个主题，确认只显示该主题题目 | 理论页 |
| 8 | Tab切换5模块 | 逐个`browser_click`每个Tab，确认snapshot出现对应模块标题 | 实操页 |
| 9 | 自检清单checkbox | 点一个checkbox，snapshot确认checked=true | 实操页 |
| 10 | 进度条更新 | `browser_console`执行JS确认进度条width>0% | 实操页 |
| 11 | 无JS错误 + 核心变量存在 | `browser_console`确认js_errors=[] **且** `typeof ALL_QUESTIONS !== 'undefined'` **且** `typeof KNOWLEDGE !== 'undefined'` | 通用 |

### DOM Click降级验证

浏览器工具点击有时无法触发元素onclick（如checkbox搭在父div上的事件委托）。此时用`browser_console`直接执行JS验证逻辑：

```javascript
// 验证checkbox+进度条联动
document.querySelector('.tab-content.active input[type=checkbox]').checked = true;
updateProgress();
document.getElementById('progressFill').style.width  // 应返回非0百分比
```

### JS语法隐藏风险：JSON内嵌HTML的特殊检查

```python
import re, json

with open('ai_quiz.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 提取KNOWLEDGE JSON块，验证可被json.loads解析
k_start = html.find('const KNOWLEDGE = {')
if k_start == -1:
    raise RuntimeError("KNOWLEDGE对象未找到——HTML重建失败")

# 查找匹配的结束花括号
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
                knowledge = json.loads(json_str)
                assert len(knowledge) >= 10, f"知识卡数量不足: {len(knowledge)}"
                print(f"✅ JSON有效: {len(knowledge)}张知识卡")
            except json.JSONDecodeError as e:
                raise RuntimeError(f"❌ JSON语法错误(JS将无法解析)→页面完全不可用 错误位置: {e.pos} 上下文: {json_str[e.pos-30:e.pos+30]}")
            break
```

**常见根因**：知识卡文本中的literal换行符(`\n`)或制表符(`\t`)作为真实控制字符嵌入JSON字符串→JS严格JSON解析器报`Invalid control character`→脚本执行中断→页面完全白屏。**必须用`json.dumps(ensure_ascii=False)`序列化，它自动转义控制字符。**

### HTML属性注入风险（⚠️ 隐蔽且致命）

**症状：** JSON数据泄漏为页面可见文本，`ALL_QUESTIONS`/`KNOWLEDGE`为`undefined`，但`js_errors`可能为空。

**根因：** CSS inline style属性值末尾多一个逗号（如`margin-top:40px,`）→引号未闭合→HTML解析器把后续JSON吞入属性值→JSON中的`"`误闭属性→破坏页面结构。

**检测与修复：** 详见 `references/html-style-attribute-injection.md`

## 2026竞赛专项

### 官方学习平台

2026年「生成式人工智能系统应用员S」竞赛官方资料在小鹅通平台，详见 `references/competition-2026-official-resources.md`。**关键结论：官方理论题库当前锁定，不要等待——用已有题库自建刷题页。**

### 小鹅通登录注意事项

- **手机验证码**：点击"获取验证码"后可能跳转空白页（疑似反爬），需刷新重试
- **微信扫码**：需截图发给用户本地扫描，远程浏览器无法扫码。`browser_vision`工具在当前模型(deepseek-v4-pro)上返回400错误(`unknown variant image_url`)，**改用`mcp_zhipu_vision_analyze_image`读取截图**
- **iLink限流**：微信通道发图片会触发rate limiting，冷却期内不要重试

## 注意事项
- 题库列顺序需确认(col[2]=题干, col[3]=选项文本, col[4]=答案, col[5-9]=A-E)
- **⚠️ 知识卡验证不可跳过**——AI训练知识可能存在事实错误/过时/遗漏，考试场景必须通过web搜索逐张验证
- **⚠️ 浏览器功能验证不可跳过**——数据检查(题目数/ID唯一/结构完整性)不能替代实际交互测试。未做这步已导致一次「页面完全无法点击」的交付事故
- 知识卡内容应与题目知识点强对齐，避免泛泛而谈
- 网页移动端必须适配(padding/字号响应式)
- localStorage存储键名应唯一，避免与用户其他网页冲突
- delegate_task批量验证时注意并发限制（hermes默认max_concurrent_children=2），每批≤5个主题
- 综合知识卡初始生成通常内容薄弱，验证阶段需彻底补全基础概念

## 已验证环境
- Python 3, openpyxl
- 题库: 2249题(单选+多选+判断), 15个主题
- 输出HTML: 816KB, Chrome/Safari/Firefox兼容
- 知识卡验证: 3批×5主题, 每批6-12次web_search, 总耗时约5分钟
