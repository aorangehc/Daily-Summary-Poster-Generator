# 每日总结海报生成器（Daily Summary Poster Generator）

一个面向普通用户的桌面应用：输入当天总结内容，选择主题与模块，一键生成高质感的海报图片（PNG/JPG）。默认提供四个高端配色主题与四类常用模块，支持自定义模块数量与主题。应用可离线运行，无需编程知识。

---

## 1. 项目目标与定位
- 面向人群：日常复盘、工作日报、打卡分享、社群输出的普通用户与创作者。
- 使用门槛：无需编程、无需网络、双击可用（提供打包版本）。
- 输出质量：高对比、高层次配色，排版整洁，图像清晰（支持 2x 导出）。
- 可扩展性：模块、主题可配置，保留插件式扩展空间。

---

## 2. 功能特性（概览）
- 模块化编辑：
  - 默认四个模块：标题/日期、今日摘要、数据统计、金句/引言。
  - 支持添加/删除/排序模块，自由组合。
- 主题与配色：
  - 内置四个「高端」主题：极简黑金、奶油莫兰迪、薄雾蓝紫、清爽夏日。
  - 支持自定义主题色板、圆角、阴影、网格密度等。
- 版式与排版：
  - 统一网格与间距系统、可选对齐方式、文本自动换行。
  - 字体优先匹配「思源黑体/Noto Sans CJK」，并提供平台回退字体。
- 导出图片：
  - PNG/JPG 导出，支持倍率导出（如 2x），可选背景纯色/渐变。
- 体验与易用性：
  - 拖拽排序、所见即所得预览、主题一键切换、颜色选择器。
  - 离线运行、自动保存草稿、本地 JSON 模板文件。
- 安全与隐私：
  - 完全本地处理，不上传任何数据。

---

## 3. 设计方案（技术与架构）

### 3.1 技术栈选择
- 桌面框架：Python + Tkinter（内置于多数 Python 发行版，打包后可一体化分发）。
- 绘制与导出：Pillow（PIL）进行画布绘制、文本测量、图片合成与导出。
- 数据建模：Pydantic（可选）用于配置与状态的校验与序列化。
- 存储与配置：JSON（`.poster.json`）保存场景与模板。
- 打包：PyInstaller 生成 Windows `.exe`、macOS `.app`、Linux 可执行文件。

选择理由：依赖少、跨平台、打包成熟、离线稳定、学习/维护成本低。

### 3.2 核心架构
- UI 层（Tkinter）
  - 左侧：模块列表与编辑器；右侧：海报画布预览区；顶部：主题/尺寸/导出控制。
- 领域层
  - 模块系统：定义标准接口（数据字段 + 渲染逻辑），提供内置模块与扩展点。
  - 主题系统：统一色板、字体、圆角、阴影、网格与间距等设计 tokens。
  - 布局引擎：网格/栅格与自动换行，块级模块自动流式排版，支持多列与卡片样式。
  - 渲染器：基于 Pillow 的绘制适配层，负责文本、图形、图片渲染与导出。
- 基础设施
  - 本地存储（草稿/最近使用/用户主题），平台目录管理（`platformdirs`）。
  - 字体加载与替代、颜色对比与无障碍检查、图像缓存。

### 3.3 目录结构（建议）
```
app/
  main.py                    # 应用入口（UI 启动）
  ui/
    window.py               # 主窗体与布局
    preview_canvas.py       # 预览画布（渲染到内存位图）
    module_editor.py        # 模块编辑侧栏
    theme_picker.py         # 主题/尺寸/导出控制区
  core/
    models.py               # 配置与数据模型（Pydantic 可选）
    layout.py               # 布局与网格系统
    renderer.py             # 渲染适配（Pillow）
    theme.py                # 主题与设计 tokens
    fonts.py                # 字体加载&回退策略
    storage.py              # 草稿/模板/主题的读写
    utils/
      text.py               # 文本测量&换行
      color.py              # 颜色与对比计算
  modules/
    base.py                 # 模块抽象与接口
    title.py                # 标题/日期模块
    summary.py              # 今日摘要模块（要点列表）
    stats.py                # 数据统计模块（网格卡片）
    quote.py                # 金句/引言模块
    image.py                # 图片模块（可选）
  assets/
    fonts/                  # 内置或可选字体（注意版权）
    icons/                  # 内置图标
    themes/                 # 主题预设（JSON）
examples/
  sample.poster.json        # 示例配置
requirements.txt
pyproject.toml              # 可选：项目元数据与打包配置
README.md
```

---

## 4. 海报与模块设计

### 4.1 画布与尺寸
- 默认尺寸：`1240 x 1754`（约 A4 的 150DPI 竖版，便于社交媒体分享）。
- 可选尺寸：
  - A4 高分辨率：`2480 x 3508`（300DPI）。
  - 竖屏社媒：`1080 x 1920`。
  - 自定义：宽高 + 导出倍率（如 1x/2x/3x）。

### 4.2 网格与间距（建议默认）
- 画布边距：`64 px`。
- 网格：12 列栅格，列间距 `40 px`。
- 模块卡片圆角：`20 px`；卡片内边距：`24 px`。
- 模块间距：`24–32 px`（随主题略有差异）。

### 4.3 字体与排版
- 字体优先级：
  - 首选：思源黑体（Source Han Sans）/ Noto Sans CJK。
  - Windows 回退：`Microsoft YaHei`, `Segoe UI`。
  - macOS 回退：`PingFang SC`, `Hiragino Sans GB`。
  - Linux 回退：`Noto Sans CJK SC`。
- 层级建议：
  - 标题：32–48；副标题/日期：18–24；正文：16–18；标签：12–14。
- 行距建议：1.3–1.6；对齐方式：左对齐为主；金句可居中。
- 自动换行：按渲染宽度计算 `textbbox`，逐词或逐字断行（中英文兼容）。

### 4.4 主题与色彩（内置 4 款）
1) 极简黑金（`black_gold`）
- background: `#0F0F0F`
- primary: `#D4AF37`（金）
- text: `#EDEDED`
- muted: `#858585`
- accent: `#6C5CE7`

2) 奶油莫兰迪（`morandi_cream`）
- background: `#F3F1ED`
- primary: `#BEB4A7`
- text: `#2B2B2B`
- accent: `#D4A5A5`
- contrast: `#40514E`

3) 薄雾蓝紫（`mist_blueviolet`）
- background: `#101522`
- primary: `#7A88FF`
- text: `#ECEFF4`
- accent: `#D0A2F7`
- muted: `#7C8190`

4) 清爽夏日（`fresh_summer`）
- background: `#F2FBF7`
- primary: `#2BB673`
- text: `#22303C`
- accent: `#00B8D9`
- muted: `#6B7F94`

说明：主题不仅包含色板，还包含圆角、阴影、分割线、卡片风格与网格密度等设计 tokens。

### 4.5 模块类型（默认 + 可选）
- 标题（`title`）：主标题、副标题/日期、对齐方式（left/center）。
- 摘要（`summary`）：要点列表；前缀符号（•/—/✓）；可选编号。
- 统计（`stats`）：标签+数值卡片，支持 2–4 列自适应；可加图标。
- 金句（`quote`）：句子、作者/来源；可中置大引号装饰。
- 图片（`image`，可选）：插入本地图片，支持裁剪填充与圆角遮罩。

### 4.6 模块数据字段（示例）
```
{
  "type": "stats",
  "title": "今日数据",
  "metrics": [
    { "label": "番茄", "value": "6" },
    { "label": "步数", "value": "8123" },
    { "label": "阅读", "value": "42min" }
  ],
  "columns": 3,
  "style": { "card": true, "icon": null }
}
```

---

## 5. 使用指南

### 5.1 免安装版本（推荐给普通用户）
- 下载对应平台的打包文件（Windows `.exe` / macOS `.app` / Linux 可执行）。
- 双击运行 → 选择主题 → 填写模块 → 预览 → 导出图片。

注：首个版本发布后，将在 Releases 中提供下载链接与校验信息。

### 5.2 源码运行（开发者/高级用户）
1) 准备环境
```
python -m venv .venv
. .venv/bin/activate         # Windows: .\\.venv\\Scripts\\activate
pip install -r requirements.txt
```
2) 启动应用
```
python app/main.py
```

### 5.3 基本操作流程
- 新建海报 → 选择主题与画布尺寸 → 按需添加模块。
- 单击列表中的模块进入编辑；拖拽模块可调整顺序。
- 右侧即时预览；点击导出选择 PNG/JPG 与倍率（如 2x）。

### 5.4 导出清晰度建议
- 社交平台分享：`1240 x 1754` 导出 2x，清晰且兼顾体积。
- 打印或留档：A4（`2480 x 3508`）导出 1x 或更高倍率。

---

## 6. 配置文件与示例

### 6.1 保存/加载格式（`.poster.json`）
```
{
  "canvas": { "width": 1240, "height": 1754, "dpi": 150, "padding": 64 },
  "theme": "black_gold",
  "modules": [
    { "type": "title", "title": "今日总结", "subtitle": "2025-06-01", "align": "left" },
    { "type": "summary", "items": ["完成海报生成器设计", "实现模块化布局", "编写 README"], "bullet": "•" },
    { "type": "stats", "title": "今日数据", "metrics": [
        { "label": "番茄", "value": "6" },
        { "label": "步数", "value": "8123" }
      ], "columns": 2 },
    { "type": "quote", "text": "不积跬步，无以至千里。", "author": "荀子" }
  ]
}
```

### 6.2 JSON 字段说明（简化）
- `canvas.width/height/dpi/padding`：画布与边距；导出倍率独立选择。
- `theme`：主题 ID（内置或用户自定义）。
- `modules[]`：按顺序渲染；不同 `type` 有各自字段（见模块章节）。

---

## 7. 高级能力与扩展

### 7.1 自定义主题
- 在 `assets/themes/` 新增主题 JSON，字段包含：`palette`（色板）、`typography`、`card`（圆角/阴影）、`grid`（边距/栅格）。
- UI 主题选择器自动读取并列出用户主题。

### 7.2 自定义模块
- 在 `modules/` 目录新增模块文件，实现：
  - 数据模型（字段声明 + 默认值）。
  - 渲染方法（接收画布上下文、主题 tokens、可用区域，返回占用高度）。
- 注册模块：在模块索引中添加 `type` 与映射关系。

### 7.3 命令行（可选）
```
python app/main.py --config examples/sample.poster.json --export out/poster.png --scale 2
```
- 适用于自动化或批处理使用场景。

---

## 8. 打包与发布

### 8.1 Windows（PyInstaller）
```
pyinstaller \
  --noconfirm --windowed --onefile \
  --name DailySummaryPoster \
  --add-data "app/assets;app/assets" \
  app/main.py
```
- 输出在 `dist/`；可配合 Inno Setup 生成安装包（可选）。

### 8.2 macOS（PyInstaller）
```
pyinstaller \
  --noconfirm --windowed --onefile \
  --name DailySummaryPoster \
  --add-data "app/assets:app/assets" \
  app/main.py
```
- 如需分发，建议签名与公证（可选）。

### 8.3 Linux
- 同 Windows 命令（用 `:` 作为分隔符），注意系统字体依赖。

### 8.4 常见打包问题
- 字体缺失：在 `assets/fonts/` 放置授权字体并在 `fonts.py` 声明；无法打包时使用系统回退字体。
- 图片/资源路径：打包后使用 `sys._MEIPASS` 安全解析资源目录。

---

## 9. 质量与可用性
- 性能：
  - 预渲染背景与重复元素；文本测量结果做缓存；仅在必要时重绘。
- 可访问性：
  - 主题内置对比度校验（尽量 ≥ 4.5:1），避免浅色文本在浅底上难以辨识。
- 可靠性：
  - 自动保存草稿与最近文件；导出操作日志与错误提示；异常回退默认主题。

---

## 10. 安全与隐私
- 全本地离线运行，不上传任何内容。
- 用户图片与配置仅保存在本地（可选自定义目录）。

---

## 11. 路线图（Roadmap）
- v0.1 原型：核心模块、四套主题、PNG 导出、基础 UI。
- v0.2 体验：拖拽排序、2x/3x 导出、用户主题、图片模块。
- v0.3 进阶：PDF 导出、富文本（加粗/高亮/链接）、主题市场（本地）。
- v0.4 协作：模板分享、导入/导出、命令行批处理。
- v0.5 智能：写作建议/金句推荐（本地可选，后续再评估）。

---

## 12. 贡献指南
- 提交 Issue 反馈需求与缺陷，欢迎 PR。
- 代码风格：尽量保持模块内聚、函数纯粹、命名清晰，避免过早抽象。
- 资源版权：确保引入字体、图标、图片具备可分发授权或替换为开源资源。

---

## 13. 常见问题（FAQ）
- Q：导出图片不够清晰？
  - A：提高导出倍率（2x/3x），或选择更高画布尺寸（如 A4 300DPI）。
- Q：中文字体显示异常？
  - A：确保系统存在中文字体，或在 `assets/fonts/` 放置授权字体并在设置中切换。
- Q：深色主题可读性差？
  - A：使用内置对比度校验与自动调暗背景/调亮文本的选项。
- Q：无法联网环境下可用吗？
  - A：完全离线可用，资源全部本地。

---

## 14. 示例配置（快速开始）
```
{
  "canvas": { "width": 1240, "height": 1754, "dpi": 150, "padding": 64 },
  "theme": "morandi_cream",
  "modules": [
    { "type": "title", "title": "周一复盘", "subtitle": "2025-06-01", "align": "left" },
    { "type": "summary", "items": ["需求评审完成", "修复两个高优缺陷", "整理下周计划"], "bullet": "✓" },
    { "type": "stats", "title": "效率数据", "metrics": [
      { "label": "专注番茄", "value": "5" },
      { "label": "邮件处理", "value": "34" },
      { "label": "代码提交", "value": "12" }
    ], "columns": 3 },
    { "type": "quote", "text": "日日精进，久久为功。", "author": "——" }
  ]
}
```

---

如需我基于本 README 脚手架初版代码与默认主题，请告知你的优先平台（Windows/macOS/Linux）与是否需要打包。

