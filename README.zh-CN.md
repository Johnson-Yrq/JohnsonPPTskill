<a id="readme-top"></a>

<div align="center">

<h1>JohnsonPPTskill</h1>

<p><strong>把一份大纲，变成风格完整、可继续编辑的演示稿。</strong></p>
<p>三种视觉风格 · 演讲与阅读双模式 · 单文件 HTML 离线交付</p>

<p><a href="README.md">English</a> · <strong>简体中文</strong></p>

<p>
  <a href="#快速开始">快速开始</a> ·
  <a href="#视觉风格">视觉风格</a> ·
  <a href="#演讲型与阅读型">演讲型与阅读型</a> ·
  <a href="#构建与检查">构建与检查</a>
</p>

<p><code>Codex / Claude Code</code> &nbsp; <code>共享套件 v3.1.2</code> &nbsp; <a href="LICENSE">MIT 许可证</a></p>

</div>

---

通过 [`ppt-workbench`](skills/ppt-workbench/SKILL.md) 统一开始制作，选择视觉风格和演讲型／阅读型，再根据大纲安排配图、流程、图表与文字。不同风格独立维护主题、配图提示词和参考图，共用排版、构建、编辑与检查套件。

| 整稿风格一致 | 信息适配用途 | 单文件离线交付 |
|---|---|---|
| 封面、文字、配图与尾页遵循同一套视觉规范。 | 演讲型服务现场讲解，阅读型保留独立理解所需的解释与依据。 | CSS、JS、图片、图标和图表全部内嵌，支持编辑、另存与打印。 |

> **交付格式**：构建器输出独立 `.html` 文件。明确需要 `.pptx` 时，应使用相应的 PowerPoint 制作流程；本套件不提供 HTML 转 PPTX 导出。

## 视觉风格

三种风格的实际页面预览，点击图片可查看原图。示例业务内容与图表数字仅用于说明视觉与排版。

| 素白蓝调 | 海蓝玻璃 | 写实微缩 |
|:---:|:---:|:---:|
| <a href="skills/white-blue-slides/assets/reference-design/approved-open-icons.jpg"><img src="skills/white-blue-slides/assets/reference-design/approved-open-icons.jpg" alt="素白蓝调业务机制页：白色模型、蓝色语义图标与可编辑说明" width="290"></a> | <a href="docs/images/examples/speech-product.png"><img src="docs/images/examples/speech-product.png" alt="海蓝玻璃产品能力页：海军蓝标题、灰青强调与玻璃展陈场景" width="290"></a> | <a href="docs/images/examples/miniature-speech-cover.png"><img src="docs/images/examples/miniature-speech-cover.png" alt="写实微缩封面：暖灰纸底、石墨标题与细致的团队工作空间" width="290"></a> |
| 暖白纸底 · 明亮主蓝 · 哑光模型 | 海军蓝 · 玻璃材质 · 香槟金 | 暖灰纸底 · 真实材质 · 生动人物 |
| [`white-blue-slides`](skills/white-blue-slides/SKILL.md) | [`navy-glass-slides`](skills/navy-glass-slides/SKILL.md) | [`realistic-miniature-slides`](skills/realistic-miniature-slides/SKILL.md) |

三种风格都支持演讲型与阅读型，可用于不同主题的大纲。配图中的对象、动作与关系由业务内容决定；风格负责视觉表达。同一份演示稿选择一种风格，整稿保持一致。

<details>
<summary><strong>风格 ID、视觉细节与更多示例</strong></summary>

| 风格 | `style` ID | 视觉特点 |
|---|---|---|
| **素白蓝调** | `scene-white` | 暖白纸底、明亮主蓝、白色哑光模型场景与微缩人物 |
| **海蓝玻璃** | `saas-3d` | 暖白纸底、海军蓝文字与重点面、灰青及少量香槟金、玻璃与精细微缩展陈 |
| **写实微缩** | `real-miniature` | 暖灰纸底、石墨与灰蓝、鼠尾草绿及少量赭黄；35–45° 微缩场景、写实 PBR 材质、表情细致的人物，配图无字 |

| 素白蓝调 · 分层架构 | 海蓝玻璃 · 演讲型封面 |
|:---:|:---:|
| <a href="skills/white-blue-slides/assets/reference-design/approved-architecture.jpg"><img src="skills/white-blue-slides/assets/reference-design/approved-architecture.jpg" alt="五层白色立体架构模型，模块直接标注，蓝色通道展示数据流向" width="440"></a> | <a href="docs/images/examples/speech-cover.png"><img src="docs/images/examples/speech-cover.png" alt="海蓝玻璃演讲型封面：左侧价值主张，右侧三维产品展陈" width="440"></a> |

| 写实微缩 · 阅读型布局 | 素白蓝调 · 页面参考 |
|:---:|:---:|
| <a href="docs/images/examples/miniature-reading-diagonal.png"><img src="docs/images/examples/miniature-reading-diagonal.png" alt="写实微缩阅读型对角布局：全景与协作近景搭配责任矩阵和环形图" width="440"></a> | <a href="skills/white-blue-slides/assets/reference-design/approved-overview.jpg"><img src="skills/white-blue-slides/assets/reference-design/approved-overview.jpg" alt="素白蓝调页面与场景参考，展示构图和视觉层级" width="440"></a> |

配图参考：[海蓝玻璃产品展陈](skills/navy-glass-slides/assets/reference-design/approved-product-overview.png) · [写实微缩团队工作空间](skills/realistic-miniature-slides/assets/reference-design/approved-workflow.png)。

参考图用于说明材质、尺度与视觉层级，其中的业务内容不作为新项目事实。

</details>

## 快速开始

### 1. 安装 Skill

电脑已安装 Node.js/npm 后，可以通过 [Skills CLI](https://github.com/vercel-labs/skills#options) 直接从本 GitHub 仓库安装，无需手动克隆或单独发布 npm 包。

**安装到 Codex：**

```bash
npx skills@latest add Johnson-Yrq/JohnsonPPTskill --skill '*' -g -a codex
```

**安装到 Claude Code：**

```bash
npx skills@latest add Johnson-Yrq/JohnsonPPTskill --skill '*' -g -a claude-code
```

- `--skill '*'`：安装仓库中的全部 Skill，目前包含 `ppt-workbench`、`white-blue-slides`、`navy-glass-slides` 和 `realistic-miniature-slides`，确保统一入口、共享套件和风格包一起安装。保留星号两侧的引号。
- `-g`：全局安装，跨项目使用；去掉该参数则安装到当前项目。
- `-a`：选择目标 Agent。

<details>
<summary><strong>查看可用 Skill 或手动安装</strong></summary>

只查看仓库提供的 Skill，不执行安装：

```bash
npx skills@latest add Johnson-Yrq/JohnsonPPTskill --list
```

克隆仓库并进入目录：

```bash
git clone https://github.com/Johnson-Yrq/JohnsonPPTskill.git
cd JohnsonPPTskill
```

**Codex：**

```bash
mkdir -p ~/.codex/skills
cp -R skills/ppt-workbench skills/white-blue-slides skills/navy-glass-slides skills/realistic-miniature-slides ~/.codex/skills/
```

**Claude Code：**

```bash
mkdir -p ~/.claude/skills
cp -R skills/ppt-workbench skills/white-blue-slides skills/navy-glass-slides skills/realistic-miniature-slides ~/.claude/skills/
```

四个目录须同级放置。`white-blue-slides` 同时包含共享制作套件，其他风格依赖它；`ppt-workbench` 负责统一选择。更新已有安装时，先备份相关技能目录，再同步新版本。仅使用素白蓝调时，也可单独安装 `white-blue-slides`。

</details>

### 2. 提供大纲，开始制作

尚未确定风格或类型时：

```text
用 $ppt-workbench，根据这份大纲制作演示稿，先让我选择风格和演讲型／阅读型。
```

已经明确两个选择时：

```text
用 $ppt-workbench，选择海蓝玻璃风格，做成阅读型。按内容安排配图、流程、矩阵和图表，完成逐页检查。
```

<details>
<summary><strong>直接调用指定风格</strong></summary>

```text
用 $white-blue-slides，把这份大纲做成素白蓝调风格的演讲型演示稿。
```

```text
用 $navy-glass-slides，把这份方案做成海蓝玻璃风格的阅读型演示稿。
```

```text
用 $realistic-miniature-slides，把这份团队协作方案做成写实微缩风格的阅读型演示稿，配图不要文字。
```

</details>

Agent 只询问缺少的选择；当前任务已经确认的风格和类型直接沿用。用户明确授权由 Agent 选择时，会按目标选择并说明。模板默认值不代表用户选择，续做项目也不会因主题变化自动换风格。

### 3. 打开、演示与编辑

在浏览器中打开交付的 HTML，即可离线演示、编辑文字和图表数据。修改后点击**另存 HTML**保留变更；浏览器内的编辑不会自动回写源文件 `deck.json`。

本次提供中英文 README；Skill 指令、参考文档、示例内容和播放器控件目前仍以中文为主。

## 演讲型与阅读型

| 维度 | 演讲型 `speech` | 阅读型 `reading` |
|---|---|---|
| 使用方式 | 现场讲解、投屏演示 | 发给读者独立阅读 |
| 信息组织 | 一个结论和少量支撑，细节可放讲稿 | 页面保留机制、依据、条件与边界 |
| 可视化 | 主场景、关键步骤、少量标注 | 配图配合流程、矩阵、表格、图标和图表 |
| 配图分工 | 可作为页面的主要视觉 | 先安排主体版面的 1/2 或 1/4 配图分区 |
| 内容超量时 | 分页逐步讲解 | 拆成关联页面，保持可读字号和配图面积 |

阅读型的信息密度来自更多有意义的关系和证据，不靠缩小字号或堆满段落。没有可靠数值时，用流程、职责、比较和分层关系表达；不为了丰富页面而编造指标。

整稿选择记录在 `deck.json` 根对象。以下仅展示两个选择字段，完整项目另需标题与页面内容：

```json
{
  "style": "saas-3d",
  "presentation_mode": "reading"
}
```

旧稿省略字段时，仍兼容素白蓝调与演讲型。新稿应根据用户选择显式记录两个字段。详细规则见 [用途与信息密度](skills/white-blue-slides/references/presentation-modes.md)。

### 阅读型的四种图文分区

比例按**主体版面分区**计算，不含页头、页脚及全宽摘要。图表、图标和 Logo 属于内容元素，不计为配图。

| 布局 | `composition` | 配图安排 | 其余内容的组织示例 |
|---|---|---|---|
| **1/2 左右** | `half_lr` | 左半区放一张主图 | 右半区放图表＋解释，或流程＋责任矩阵 |
| **1/2 上下** | `half_tb` | 上半区放 1–3 张图 | 下半区安排两组互补内容，如流程＋趋势 |
| **1/2 对角** | `half_diagonal` | 左上、右下各一张图 | 右上、左下各一个内容模块，共两图两模块 |
| **1/4 配图** | `quarter` | 左上四分之一区域放一张图 | 其余三区放图表、表格、图标与文字，共一图三模块 |

<details>
<summary><strong>查看四种阅读型布局</strong></summary>

| 1/2 左右 | 1/2 上下 |
|:---:|:---:|
| <a href="docs/images/examples/reading-half-lr.png"><img src="docs/images/examples/reading-half-lr.png" alt="阅读型左右各半：左侧产品场景，右侧条形图与工作说明" width="440"></a> | <a href="docs/images/examples/reading-half-tb.png"><img src="docs/images/examples/reading-half-tb.png" alt="阅读型上下各半：上方双场景，下方处理流程与趋势折线图" width="440"></a> |

| 1/2 对角双图 | 1/4 配图 |
|:---:|:---:|
| <a href="docs/images/examples/reading-half-diagonal.png"><img src="docs/images/examples/reading-half-diagonal.png" alt="阅读型对角双图：左上和右下配图，其余区域展示能力矩阵与环形图" width="440"></a> | <a href="docs/images/examples/reading-quarter.png"><img src="docs/images/examples/reading-quarter.png" alt="阅读型四分之一配图：其余三区展示数量比较、交付核对表和使用边界" width="440"></a> |

以上为海蓝玻璃风格的 1920 × 1080 实际页面截图，图表数字均为示例。

</details>

先确定图区，再组织其余内容。多张配图各自解释不同对象、阶段或视角；主体完整，色彩与材质一致。标题和内容按分区对齐，重点项可用字号、图标与字重轻量强调。具体字段与完整页面见 [阅读型示例](skills/navy-glass-slides/assets/deck.reading.example.json)。

### ECharts 与可编辑数据

阅读型复合页支持**横向条形图、折线图和环形图**，用于类别比较、时间趋势和整体构成。图表需提供单位与来源，并在相邻文字解释判断和边界；示例数字必须标明示例性质。

播放器进入「编辑文字」后，可展开图表右下的「编辑图表数据」，修改类别、系列名和数值。图表同步刷新，「另存 HTML」后重新打开仍可继续编辑；修改数值后需核对文字结论是否仍成立。

图表库、数据与 SVG 图表均随 HTML 离线工作，无需 CDN。当前模板支持 2–8 个类别、1–3 组有限非负数；环形图仅一组且合计大于零。详细约束、字段与示例见 [图表使用说明](skills/white-blue-slides/references/charts.md)。

## 制作流程与配图

**确认风格与类型 → 理解大纲 → 选择版式 → 建立 `deck.json` → 检查计划 → 准备配图 → 构建 → 逐页检查 → 交付**

| 素材条件 | 后续处理 |
|---|---|
| **已有图片** | 先查看并复用，按页面内容核对图片与文字的对应关系。 |
| **有可直接调用的内置生图工具** | 按逐页简报生成、查看和调整，再构建成稿。 |
| **没有内置生图工具** | 先导出逐页完整提示词和供图清单，收到图片后继续制作；可以分批提供。 |

每张缺图都需要本页独有的 `image.brief`，描述对象与数量、动作或系统处理、关系机制、层级细节与构图。导出器会检查缺项和跨页重复的简报。页面标题、真实数据、业务说明和架构标注留在可编辑内容中。

<details>
<summary><strong>配图内文字与交付文件</strong></summary>

素白蓝调与写实微缩配图默认无字；写实微缩只提供 `ui_text: "none"`，包括白板、屏幕、文件、日历和键帽都不生成文字。海蓝玻璃默认为 `ui_text: "demo"`，只允许软件屏幕内的 Overview、Analytics、Activity、Demo 四个示意标签，也可选择 `none`。配图内的示意图表不充当真实业务数据。

最终交付物为一个独立 `.html` 文件；`deck.json`、提示词、图片清单和 QA 截图用于制作与续改。缺图的 `--draft` 版本仅用于内部预排。

</details>

## 构建与检查

以下命令在仓库根目录执行，`project/` 表示本次演示稿的工作目录。

```text
project/
├── 大纲.md
├── deck.json
├── images/                  # 本项目配图
├── 演示稿.html              # 最终交付
└── qa/                      # 截图与检查报告
```

### 从完整示例开始

可从以下示例建立项目并替换为自己的内容：

| 示例 | 内容 |
|---|---|
| [素白蓝调示例](skills/white-blue-slides/assets/deck.example.json) | 封面、场景信息页和尾页 |
| [海蓝玻璃演讲型示例](skills/navy-glass-slides/assets/deck.example.json) | 低密度产品介绍与轻量强调 |
| [海蓝玻璃阅读型示例](skills/navy-glass-slides/assets/deck.reading.example.json) | 四类图文分区、流程、矩阵与图表 |
| [写实微缩演讲型示例](skills/realistic-miniature-slides/assets/deck.example.json) | 团队工作系统、协作交接与轻量强调 |
| [写实微缩阅读型示例](skills/realistic-miniature-slides/assets/deck.reading.example.json) | 四类图文分区、职责流程与示例任务图表 |

示例附带配图简报；正式构建前，需要按清单准备对应图片。项目图片路径相对 `deck.json` 所在目录，完整数据格式见 [内容数据与构建](skills/white-blue-slides/references/deck-format.md)。

### 检查、准备、构建与审查

```bash
# 1. 检查设计决策和页面结构，不要求图片已经存在
python3 skills/white-blue-slides/scripts/build_deck.py project/deck.json \
  --check-plan --out project/design-plan.json

# 2. 导出提示词与供图清单，不调用模型或网络
python3 skills/white-blue-slides/scripts/prepare_images.py project/deck.json \
  --out project/image-handoff

# 3. 图片齐全后，构建单文件 HTML
python3 skills/white-blue-slides/scripts/build_deck.py project/deck.json \
  --out project/演示稿.html

# 4. 渲染审查并保存逐页截图
node skills/white-blue-slides/scripts/audit_deck.cjs project/演示稿.html \
  --out project/qa --browser chrome
```

自动检查覆盖结构、图文分区、可见组件和播放器功能（含 PPTX 导出）；逐页视觉检查还需核对配图主体、图文对应和独立阅读时的完整性。审查器会生成 `visual-review.template.json`，制作方逐页看图后填写复核记录并用 `--visual-review qa/visual-review.json` 回传，报告中的 `readyForDelivery` 需要自动检查与复核记录同时通过；不传记录时退出码与以前相同。

<details>
<summary><strong>构建选项与 13 种共享版式</strong></summary>

| 可选工具或参数 | 用途 |
|---|---|
| `match_paper.py project/images/*.png --deck project/deck.json --dry-run` | 按当前主题诊断底色与透明通道；允许脚本校准时去掉 dry-run，仅处理轻微偏差并备份 |
| `--embed-format keep` | 保留原始图片格式；默认优先转 WebP 内嵌 |
| `--embed-quality 85` | 设置图片压缩质量 |
| `--builder` | 加载项目新增版式；复用共享组件 |
| `--allow-restyle` | 用户明确要求超出所选主题，自定义封面或页头页脚时使用 |

选择现有命名风格无需 `--allow-restyle`。

| 版式 | 用途 | 版式 | 用途 |
|---|---|---|---|
| `cover` | 封面 | `architecture` | 分层架构与直接标注 |
| `scene` | 大场景与两侧说明 | `flow` | 步骤与控制点 |
| `split` / `triad` | 左右说明／三段控制 | `domains` | 多领域清单 |
| `journey` | 阶段、比较或路径 | `formula` | 公式与因素关系 |
| `table` | 表格与边界对照 | `relations` | 实体与关联 |
| `closing` | 有配图的收束尾页 | `reading` | 四类阅读型复合信息页 |

结构化字段（详见 `references/deck-format.md`）：`flow` 控制分组支持 `rows_layout`（自动／同行／标签在上）、行 `kind`（说明／校验／异常）与阅读型 `align_control_rows` 共享行高；`architecture` 标注支持 `prefix`、`detail`、`leader` 引线和流向 `direction`；`journey` 阶段支持 `period` 时间标签与 `fields` 字段组，页底可用 `bottom.type: groups`；配图比例新增 `2:1 / 21:9 / 3:1`，`image.background_mode: white-matte` 可把已确认纯白底的素材映射到当前纸色，HTML、PDF 与 PPTX 一致。

</details>

## 播放、编辑与保存

工具栏提供：**总览 · 全屏 · 讲稿 · 编辑文字 · 另存 HTML · 导出 PPTX · 导出 PDF / 打印**。默认画布为 1920 × 1080，并按窗口等比适配。文字编辑后需「另存 HTML」保留修改，浏览器内的修改不会自动回写 `deck.json`。

全屏按屏幕可用区域完整等比显示 16:9 页面，编辑时为工具栏留出空间。PDF 使用 PowerPoint 宽屏尺寸：**960 × 540 pt（13⅓ × 7.5 英寸）**。点击“导出 PDF / 打印”后，在浏览器打印窗口选择另存为 PDF，避免用 A4 或 Letter 覆盖幻灯片纸张尺寸。

需要稳定的 PDF 尺寸与单页适配观看偏好时，可使用随附脚本（除 Playwright 外另需 `pdf-lib`）：

```bash
# 如果在浏览器中编辑过，请使用“另存 HTML”保存后的文件作为输入
node skills/white-blue-slides/scripts/export_pdf.cjs project/演示稿.html \
  --out project/演示稿.pdf --browser chrome
```

部分 PDF 阅读器可能忽略观看偏好，此时选择“适合页面”。macOS 将**显示滚动条**设为**始终**时，Chrome PDF 演示可能露出下一页顶部的细条。在已复现案例中，将**系统设置 → 外观 → 显示滚动条 → 滚动时**，然后退出演示、重新加载 PDF、再次选择**演示**，即可消除白条。该设置会影响系统内其他应用的滚动条显示；改 PDF 纸张尺寸不能解决这类阅读器问题。非 16:9 屏幕会保留边带，以免拉伸或裁切。

**HTML 播放器**也提供**全屏**按钮。用户要求 PDF 演示时，应验证指定阅读器中的实际 PDF，不能把 HTML 演示通过当作 PDF 已修复。

**导出 PPTX** 生成可编辑的 PowerPoint 文件，统一使用一种通用字体（默认微软雅黑，Windows 与 macOS 的 Office 都自带）：标题与正文保留为文本框，字号、粗细、颜色与字距不变；信息块、标签与分隔线转为形状；场景图与图标转为图片；ECharts 转为 PowerPoint 原生图表并内嵌数据表（可用“编辑数据”）；讲稿写入备注。位置按实际渲染测量，与 HTML 一致；字体替换后，英文与数字会略宽。导出器内嵌在每份演示稿中，不联网。命令行也可导出，并兼容加入该按钮之前构建的旧稿：

```bash
node skills/white-blue-slides/scripts/export_pptx.cjs project/演示稿.html \
  --out project/演示稿.pptx --browser chrome [--font "PingFang SC"]
```

只有 PDF 时，可用随附转换器生成离线 HTML 演示版（需要 Python + Poppler）。它一次只显示当前页，保留矢量轮廓的清晰度。该演示副本的文字不可编辑、不可选择；保留原 PDF 和可编辑源稿。

```bash
python3 skills/white-blue-slides/scripts/pdf_to_slides.py project/演示稿.pdf \
  --out project/全屏演示版.html
```

旧 HTML 内嵌旧播放器，需要从源项目重新构建才能应用修复；先保留浏览器编辑后的副本，避免覆盖修改。

| 按键 | 作用 | 按键 | 作用 |
|---|---|---|---|
| `→` / `PageDown` / `空格` | 下一页 | `O` | 总览 |
| `←` / `PageUp` | 上一页 | `F` | 全屏 |
| `Home` / `End` | 首页／末页 | `N` | 讲稿面板 |
| `Esc` | 退出总览、编辑或讲稿 | URL `#3` | 直接打开第 3 页 |

## 扩展与开发

每个风格包维护独立的页面主题、配图基底、参考素材和验收规范。共享脚本负责布局与功能，不随风格复制。

查看当前可用风格：

```bash
python3 skills/white-blue-slides/scripts/style_packs.py --list
```

清单自动发现同级有效的风格包，返回名称、ID、说明和 Skill 入口。新包接入后会出现在清单中，无需手动修改工作台选项。

<details>
<summary><strong>包结构与新增风格</strong></summary>

新包按视觉特点使用小写英文与短横线命名，统一以 `-slides` 结尾；目录名与 Skill 名一致，中文显示名称用于工作台选择。

```text
skills/
├── ppt-workbench/                 # 统一选择入口
├── white-blue-slides/             # 素白蓝调 + 共享制作套件
│   ├── scripts/                  # 构建、配图清单、自动发现与检查
│   ├── assets/                   # 基础组件、播放器、阅读布局与图表
│   └── references/               # 数据、类型、图表与接入规范
├── navy-glass-slides/             # 海蓝玻璃独立风格包
├── realistic-miniature-slides/    # 写实微缩独立风格包
└── new-style-slides/              # 未来新增的同级包
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/
    │   ├── style.json
    │   ├── theme.css
    │   ├── image-style.txt
    │   └── reference-design/
    └── references/
        ├── design-system.md
        ├── image-workflow.md
        └── quality-check.md
```

新增包在 `assets/style.json` 声明 `schema: "html-slide-style/v1"`、唯一 ID、风格资源和检查契约。新方向完成样例确认与验证后设为 `ready`，再同级安装；工作台、构建器和配图导出器自动识别。所有新风格继续复用演讲型／阅读型和四种阅读布局。

```bash
# 开发时连同 draft 包一起检查；不会使草稿变成可用风格
python3 skills/white-blue-slides/scripts/style_packs.py --list --include-drafts
```

完整字段、接入步骤和验证要求见 [新增独立风格包](skills/white-blue-slides/references/adding-styles.md)。

</details>

### 依赖与开发检查

| 用途 | 依赖 |
|---|---|
| 构建 HTML、导出提示词、列出风格 | Python 3.9+ 标准库 |
| 可选 WebP 压缩 | Pillow；缺少时保留原图格式 |
| 配图底色校准 | NumPy + Pillow |
| 自动浏览器审查 | Node.js + Playwright + Chrome/Chromium |
| 命令行导出可编辑 PPTX | Playwright + Chrome/Chromium（工具栏按钮不需要任何依赖） |
| PDF 导出与自动打印验证 | Playwright + pdf-lib + Chrome/Chromium |
| 已有 PDF 转离线演示版 | Python + Poppler（`pdfinfo`、`pdftocairo`） |
| 可选总览拼图 | Sharp |

ECharts 5.6.0 已随套件内置，无需额外安装或访问 CDN。生图能力由当前 Agent 环境提供，安装 Skill 不等于安装生图工具。无法运行自动审查时，使用可用浏览器逐页检查并说明验证范围。

修改脚本或资源后运行自测：

```bash
python3 skills/white-blue-slides/scripts/selftest.py
```

自测覆盖共享组件、两种类型、风格独立性、动态新增风格、图表输入与缺图恢复。主题或版式发生变化时，再使用真实配图构建并逐页检查；自测不替代视觉验收。

## 许可证与素材

项目代码采用 [MIT](LICENSE)。第三方组件保留各自许可证：

- Lucide 图标：[MIT 许可证](skills/white-blue-slides/assets/lucide-LICENSE.txt)。
- Apache ECharts：[Apache 2.0 许可证](skills/white-blue-slides/assets/vendor/ECHARTS-LICENSE.txt) 与 [NOTICE](skills/white-blue-slides/assets/vendor/ECHARTS-NOTICE.txt)，同时内嵌于含图表的成稿。

内置 Logo 与默认页脚为普爱智医品牌资源；用于其他品牌项目时，应替换为对应资源。包内参考图用于说明视觉风格，示例业务内容与数字不构成实际产品能力或效果声明。

---

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="#readme-top">返回顶部 ↑</a></p>
