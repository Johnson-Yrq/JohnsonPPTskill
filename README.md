# JohnsonPPTskill

把 PPT 大纲变成**单文件、文字可编辑、可离线打开**的场景化 HTML 演示稿。

以 [`ppt-workbench`](skills/ppt-workbench/SKILL.md) 为统一选择入口，目前提供两套独立风格 Skill，共用 **v3.1.0 制作套件**，支持继续添加风格包。交付物是**一个 `.html` 文件**：CSS、JS、Logo、图标和配图全部内嵌，双击即可全屏演示，不联网、不依赖 PowerPoint。

| 风格入口 | 适用与视觉 |
|---|---|
| [`scene-html-slides`](skills/scene-html-slides/SKILL.md) | 原有暖白蓝色页面、素白蓝调的白色模型场景 |
| [`saas-3d-slides`](skills/saas-3d-slides/SKILL.md) | 海蓝玻璃：暖白纸底、海军蓝文字与重点面、灰青与少量香槟金、玻璃及精细微缩展陈配图 |

每种风格有各自的页面主题、配图基底、参考图与验收规范；原有 12 种版式及新增阅读型复合版式、数据结构、构建器、播放器、文字编辑和检查脚本共用。原有项目不自动换风格。

```
PPT 大纲(.md) ──► deck.json ──► 配图提示词 ──► 场景配图 ──► 演示稿.html
                    │                                          │
              --check-plan 设计检查                     audit_deck 渲染审查
```

## 特性

- **风格与类型独立选择** — 动工前只询问尚未明确的风格和演讲型／阅读型类型；所有风格均支持两种类型，已有选择直接沿用。阅读型增加可编辑流程、矩阵、分层与边界对照，关键解释留在页面。

- **单文件交付** — 1920×1080，图片默认转 WebP 内嵌；换台电脑、发微信、离线投屏都能直接打开。
- **文字可编辑** — 播放器自带「编辑文字」模式，改完「另存 HTML」导出新的独立文件，不用回到源码。
- **13 种内置版式** — 封面、大场景、左右说明、三段控制、阶段路径、分层架构、流程、多领域、公式、表格、实体关系、收束尾页及阅读型复合信息页。
- **风格持续扩展** — 新增同级风格目录和有效 `assets/style.json` 即自动发现，不修改选项列表或复制制作脚本。
- **独立配图风格** — 素白蓝调的白色模型场景或海蓝玻璃；按每页内容决定对象和关系，页面标题与业务标注留在 HTML 中。
- **整页主题切换** — 海蓝玻璃风格同时应用于封面、页头、正文、图标、面板、页码与尾页；选择风格不会关闭自动检查。
- **设计契约可校验** — 生图前用 `--check-plan` 核对每页结构与设计决策；成稿后用 Playwright 逐页审查品牌不变量、图文比例、图标与标注是否真实可见。
- **品牌开箱即用** — 内置普爱智医 Logo、暖白蓝色主题与页头页脚规范，不需要用户再提供模板参数。

## 安装

将 `ppt-workbench`、`scene-html-slides` 与需要的风格包同级放进 Agent 的 skills 目录。`scene-html-slides` 包含共享制作套件，其他风格不复制脚本；更新已有安装前先备份相关目录。仅使用原风格时仍可只安装 `scene-html-slides`。

```bash
git clone https://github.com/Johnson-Yrq/JohnsonPPTskill.git
```

```bash
# Claude Code
cp -R JohnsonPPTskill/skills/ppt-workbench JohnsonPPTskill/skills/scene-html-slides JohnsonPPTskill/skills/saas-3d-slides ~/.claude/skills/
```

```bash
# Codex
cp -R JohnsonPPTskill/skills/ppt-workbench JohnsonPPTskill/skills/scene-html-slides JohnsonPPTskill/skills/saas-3d-slides ~/.codex/skills/
```

## 用法

装好后使用统一入口，Agent 会列出实际可用风格，并合并询问尚未明确的风格与类型：

> 用 ppt-workbench，根据这份大纲制作演示稿，先让我选择风格和演讲型／阅读型。

也可以一次指定两个维度，直接开始：

> 用 ppt-workbench，选择海蓝玻璃风格，做成阅读型，按内容安排配图、图表、矩阵和说明。

已确定风格时仍可直接调用原有入口：

> 用 scene-html-slides，根据这份大纲做场景化 HTML 演示稿，沿用默认 Logo、主题与版式，并完成逐页检查。

选择海蓝玻璃风格时：

> 用 saas-3d-slides，根据这份产品大纲制作海军蓝与玻璃三维风格的 HTML 演示稿，复用现有排版和制作套件，完成逐页检查。

选择海蓝玻璃风格时，`deck.json` 根对象写 `"style": "saas-3d"`；选择素白蓝调风格写 `"scene-white"`。其他风格使用自动清单返回的 ID。旧稿省略 style 时仍兼容原风格；新稿不能用此默认代替用户选择。同一稿只选一种，不在各页混搭。命名风格无需 `--allow-restyle`。新风格示例见 [`assets/deck.example.json`](skills/saas-3d-slides/assets/deck.example.json)，已确认配图及目标图保存在它的 `assets/reference-design/` 中。

用途用根字段 `presentation_mode: "speech" / "reading"` 记录，与风格分开。未说明时先询问，已有确认不重复询问；旧稿省略字段仍兼容演讲型。查看 [模式规则](skills/scene-html-slides/references/presentation-modes.md) 与 [阅读型完整示例](skills/saas-3d-slides/assets/deck.reading.example.json)。

阅读型按主体版面分区选择 1/2 左右、1/2 上下、1/2 对角双图或 1/4 配图；主体版面不含页头页脚及全宽摘要。先确定配图分区，再用图表、图标、矩阵和文字组织其余内容。有可靠数量数据时可使用 ECharts；不得缩小字号、重复插图或补造指标，放不下则拆页。 共享 `reading` 版式支持四类分区与 1–3 张配图，含可编辑图注及离线 ECharts 图表。

**两条运行路径**，skill 会按当前环境自动选择：

- **环境有内置生图工具**（如 Codex 的 `image_gen`）：逐页生成场景图 → 直接出成稿。
- **环境没有生图工具**（Claude Code 等）：先交付逐页完整的生图提示词和文件名清单，你生成图片回传后继续排版。

**制作流程**（skill 内部按此推进）：识别并确认缺少的风格和演讲型／阅读型选择 → 理解大纲并规划每页 → 选版式与设计元素 → 写 `deck.json` 并 `--check-plan` → 准备场景图 → 构建并按实际渲染迭代 → 逐页验证后交付。

## 随附脚本

Python 脚本用 `python3 <skill>/scripts/…` 调用，Node 脚本用 `node <skill>/scripts/…`；路径参数相对本次工作目录。

| 命令 | 作用 |
|---|---|
| `style_packs.py --list` | 自动列出同级可用风格及入口；`--include-drafts` 用于检查开发中的包 |
| `build_deck.py deck.json --check-plan --out design-plan.json` | 生图前核对设计决策与每页结构（项数、字段类型、坐标范围），**不需要图片已存在** |
| `prepare_images.py deck.json --out image-handoff` | 导出逐页生图提示词与供图清单，不调用模型、不联网 |
| `match_paper.py images/*.png` | 把配图背景贴平到纸色 `#F7F6F2`，消除图框四边淡矩形；原图备份到 `images/original/` |
| `build_deck.py deck.json --out 演示稿.html` | 构建唯一交付文件 |
| `audit_deck.cjs 演示稿.html --out qa --browser chrome` | Playwright 渲染审查：品牌不变量、图文比例、DOM 可见性，输出截图与报告 |
| `selftest.py` | 改动 skill 脚本或资源后自测，**不需要浏览器** |

所有风格均调用 `scene-html-slides/scripts`。提示词导出按根 style 读取独立配图基底；海蓝玻璃供图目录附带 `style-reference.png`，清单记录 style 与各页 `ui_text`。海蓝玻璃默认 demo，保留已确认示例的指定短屏幕标签；纯无字需求可设 none。原风格仍为 none，原配图基底不变。

常用参数：`--draft` 允许缺图的内部预排（正式交付禁用）、`--embed-format keep` 保留原图格式、`--embed-quality 85` 调压缩质量、`--builder` 加载项目自定义版式、`--allow-restyle` 仅在用户明确要求超出所选风格自定义封面页头页脚时使用。

## deck.json

```json
{
  "version": 1,
  "title": "采购协同方案",
  "style": "scene-white",
  "presentation_mode": "speech",
  "footer_label": "采购协同 · 方案示例",
  "slides": [
    {
      "id": "p02",
      "layout": "scene",
      "chapter": "协作机制",
      "title": "每一次交接，都保留业务上下文",
      "subtitle": "让任务、责任人与证据沿流程一起流转",
      "left":  [{ "title": "统一任务", "text": "需求与订单围绕同一个业务对象", "icon": "Blocks", "presentation": "open" }],
      "right": [{ "title": "核对材料", "text": "在执行前确认必需的业务证据", "icon": "ClipboardCheck", "presentation": "panel" }],
      "bottom": { "type": "text", "text": "把分散的动作连接成可追溯的协作过程" },
      "notes": "本页口播、原始大纲与事实状态",
      "image": { "src": "images/02.png", "alt": "团队围绕订单与核对材料开展协作", "ratio": "4:3", "brief": { "subject": "…", "action": "…" } },
      "visual": { "role": "…", "reason": "…" }
    }
  ]
}
```

需要配图的页面，`image.brief` 必须**本页独有**（对象清单带数量、人物动作、表达关系的物理机制、层级细节、构图）；`prepare_images.py` 会拒绝模板句和跨页复制的简报。完整字段说明见 [`references/deck-format.md`](skills/scene-html-slides/references/deck-format.md)，可运行示例见 [`assets/deck.example.json`](skills/scene-html-slides/assets/deck.example.json)。

### 内置版式

| 版式 | 用途 | 版式 | 用途 |
|---|---|---|---|
| `cover` | 封面：价值与层级场景 | `architecture` | 与模型对齐的直接标注 |
| `scene` | 大场景与两侧说明 | `flow` | 步骤与控制点 |
| `split` / `triad` | 左右说明 / 三段控制 | `domains` | 多领域清单 |
| `journey` | 横向比较、阶段或路径 | `formula` | 公式与平台解释 |
| `table` | 指标与边界 | `relations` | 实体、字段与关系 |
| `closing` | 有配图的收束尾页 | `reading` | 四类图文分区的阅读型复合信息页 |

## 演示稿播放器

工具栏：总览 · 全屏 · 讲稿 · 编辑文字 · 另存 HTML · 打印。

| 按键 | 作用 | 按键 | 作用 |
|---|---|---|---|
| `→` `PageDown` `空格` | 下一页 | `O` | 总览 |
| `←` `PageUp` | 上一页 | `F` | 全屏 |
| `Home` / `End` | 首页 / 末页 | `N` | 讲稿面板 |
| `Esc` | 退出总览／编辑／讲稿 | `#3` | URL hash 直达第 3 页 |

## 原风格默认设计

| 令牌 | 值 | 用途 |
|---|---|---|
| `--paper` | `#F7F6F2` | 暖白底 |
| `--blue` | `#3B7BC8` | 主蓝 |
| `--ink` | `#2B3140` | 正文 |
| `--muted` | `#5A6373` | 副标题与说明 |
| `--panel` | `#E7EEF6` | 信息块浅底 |
| `--radius` | `8px` | 圆角，不胶囊化 |

原风格的封面、尾页、页头（浅底章节标签 / 46px 主标题 / 25px 灰色副标题 / 右上 110px 页码）、页脚、暖白底与主蓝属于本套视觉规范：`custom_css` 触碰受保护区域会被构建器拒绝。海蓝玻璃风格按自身契约检查海军蓝标题、开放式章节标签与 40px 页码等；均逐页核对 `brandOK`。

海蓝玻璃整稿规范见 [`saas-3d-slides/references/design-system.md`](skills/saas-3d-slides/references/design-system.md)。其配图基底与参考独立维护，字体、色彩、面板、封面和尾页外观由主题层应用，共用布局组件。

设计规则与参考图见 [`references/design-system.md`](skills/scene-html-slides/references/design-system.md)；配图流程见 [`references/image-workflow.md`](skills/scene-html-slides/references/image-workflow.md)；验收标准见 [`references/quality-check.md`](skills/scene-html-slides/references/quality-check.md)。三维场景化配图的完整生成提示词规范见 [`ppt_illustration_prompt.md`](ppt_illustration_prompt.md)。

## 依赖

| 用途 | 依赖 |
|---|---|
| 构建 HTML | Python 3 标准库即可 |
| 配图压缩为 WebP（可选） | Pillow |
| `match_paper.py` 背景校准 | numpy + Pillow |
| `audit_deck.cjs` 渲染审查（可选） | Node.js + Playwright + Chrome/Chromium |

构建器不联网。没有 Playwright 时用可用浏览器逐页人工检查，并在交付说明里写明检查范围。

## 目录结构

```
skills/ppt-workbench/
├── SKILL.md                  # 统一确认风格与类型，按清单进入所选风格
└── agents/openai.yaml

skills/scene-html-slides/
├── SKILL.md                  # 技能说明与工作流
├── agents/openai.yaml        # Codex 界面配置
├── references/               # 设计系统、deck 格式、配图流程、验收标准
├── scripts/
│   ├── build_deck.py         # 构建器 + --check-plan 设计检查
│   ├── prepare_images.py     # 导出生图提示词与供图清单
│   ├── match_paper.py        # 配图背景贴平到纸色
│   ├── design_contract.py    # 设计契约校验
│   ├── style_packs.py        # 自动发现同级风格、校验资源与检查契约
│   ├── test_styles.py        # 跨风格与独立安装回归
│   ├── test_style_discovery.py # 新包自动发现、两种类型与错误处理
│   ├── common.py  selftest.py
│   ├── add_icons.cjs         # 按名字向 icons.json 追加 Lucide 图标
│   └── audit_deck.cjs        # Playwright 渲染审查
└── assets/
    ├── theme.css  player.js  template.html
    ├── icons.json            # 120 个 Lucide 蓝色线性图标
    ├── brand.json  logo.png  image-style.txt
    ├── deck.example.json     # 可运行示例（cover / scene / closing）
    └── reference-design/     # 6 张风格参考图（只作质量参照）

skills/saas-3d-slides/
├── SKILL.md                  # 新风格独立入口，调用上面的共享工具
├── agents/openai.yaml
├── references/               # 本风格设计、配图与验收规范
└── assets/
    ├── style.json            # 风格资源及自动检查契约
    ├── theme.css             # 整页主题，复用共享布局
    ├── image-style.txt       # 独立配图基底
    ├── deck.example.json     # 本风格示例
    └── reference-design/     # 已确认配图及目标参考
```

## 新增风格

按 [新增独立风格包](skills/scene-html-slides/references/adding-styles.md) 新建同级目录，声明 `schema: "html-slide-style/v1"`、唯一 ID、主题、配图提示词与验收契约。新方向确认并验证后设为 `ready`；工作台、构建器和提示词导出器自动识别。每个新风格继续支持演讲型／阅读型及四类阅读版式。

```bash
python3 skills/scene-html-slides/scripts/style_packs.py --list
```

## 开发

```bash
python3 skills/scene-html-slides/scripts/selftest.py
```

改动脚本或资源后先跑自测（无需浏览器；两目录同级时自动运行风格回归），再用真实配图走一遍 `--check-plan`、构建与逐页浏览器检查。

## 许可证

[MIT](LICENSE)。内置图标来自 [Lucide](https://lucide.dev)（MIT，见 [`assets/lucide-LICENSE.txt`](skills/scene-html-slides/assets/lucide-LICENSE.txt)）。`assets/logo.png` 与页脚为普爱智医品牌资源，请替换为你自己的品牌后再对外使用。
