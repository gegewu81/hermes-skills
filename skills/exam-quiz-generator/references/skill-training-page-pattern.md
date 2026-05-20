# 实操训练页模式（Skill Training Page Pattern）

## 适用场景
当考试包含"技能操作"部分（非纯理论题），需要为每个技能模块提供训练材料时使用。

## 页面结构

### 整体布局
- 顶部标题 + 5个Tab切换按钮
- 每个Tab对应一个竞赛模块
- 底部统一的时间分配建议表 + 版权footer

### 每个模块内部结构

```
## 模块标题（含竞赛分值）

### 🔁 核心流程
- 4个编号步骤，每步3个子项列表
- 用"→"链式表达流程关系

### 💡 关键TIPS
表格形式：步骤 | 实战技巧
- 每个步骤1-2条具体可操作的竞赛技巧
- 带上具体参数/工具名/方法论名

### ⚠️ 常见错误
- 3-5个竞赛中容易犯的错误
- 每个错误附带"致命程度"和"正确做法"

### 🎯 练习场景
- 1-3个模拟竞赛场景
- 每个场景：项目背景 + 任务 + 评判要点

### ✅ 自检清单
- 4-6个可勾选的技能检查项
- 每个checkbox有onclick更新进度条
```

### 底部统一元素
- **时间分配建议表**：模块 | 建议时间 | 占比 | 策略
- **版权声明**：footer固定格式

## 技术要点

### Tab切换
```css
.tab-btn.active { background: #2563eb; color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }
```

### 进度条（自检清单联动）
```javascript
function updateProgress() {
  const all = document.querySelectorAll('.tab-content.active input[type=checkbox]');
  const done = document.querySelectorAll('.tab-content.active input[type=checkbox]:checked');
  const pct = all.length ? Math.round(done.length / all.length * 100) : 0;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressText').textContent = pct + '%';
}
```

### checkbox点击事件
onclick绑定在父div上（不是input本身），以保证点击整行都触发：
```html
<div class="chk-item" onclick="toggleChk(this,0)">
  <input type="checkbox" id="chk0_0">
  <label for="chk0_0">掌握XXX</label>
</div>
```
```javascript
function toggleChk(el, modIdx) {
  const cb = el.querySelector('input[type=checkbox]');
  cb.checked = !cb.checked;
  updateProgress();
}
```

## 浏览器验证要点（实操页专用）
1. 每个Tab点击后内容正确切换（不是空白）
2. checkbox点击后进度条数字更新
3. browser_console无JS错误
4. 如果DOM click未触发onclick（浏览器工具限制），用browser_console直接执行toggleChk验证JS逻辑
