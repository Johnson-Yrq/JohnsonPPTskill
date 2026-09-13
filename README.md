# JohnsonPPTskill

把 PPT 大纲变成**单文件、文字可编辑、可离线打开**的场景化 HTML 演示稿。

本仓库收录 **`scene-html-slides`** skill（v2.6.1）——给 Claude Code / Codex 等 Agent 使用的演示稿制作技能。交付物是**一个 `.html` 文件**：CSS、JS、Logo、图标和配图全部内嵌，双击即可全屏演示，不联网、不依赖 PowerPoint。

```
PPT 大纲(.md) ──► deck.json ──► 配图提示词 ──► 场景配图 ──► 演示稿.html
                    │                                          │
              --check-plan 设计检查                     audit_deck 渲染审查
```

## 特性

- **单文件交付** — 1920×1080，图片默认转 WebP 内嵌；换台电脑、发微信、离线投屏都能直接打开。
- **文字可编辑** — 播放器自带「编辑文字」模式，改完「另存 HTML」导出新的独立文件，不用回到源码。
- **12 种内置版式** — 封面、大场景、左右说明、三段控制、阶段路径、分层架构、流程、多领域、公式、表格、实体关系、收束尾页。
- **场景化配图规范** — 白色哑光立体业务场景（人物在做事、关系看得见），标题与标注留在 HTML 里、不烘焙进图片，随时可改。
- **设计契约可校验** — 生图前用 `--check-plan` 核对每页结构与设计决策；成稿后用 Playwright 逐页审查品牌不变量、图文比例、图标与标注是否真实可见。
- **品牌开箱即用** — 内置普爱智医 Logo、暖白蓝色主题与页头页脚规范，不需要用户再提供模板参数。

## 安装

把 skill 目录放进 Agent 的 skills 目录即可：

```bash
git clone https://github.com/Johnson-Yrq/JohnsonPPTskill.git
```

```bash
# Claude Code
cp -R JohnsonPPTskill/skills/scene-html-slides ~/.claude/skills/
```

```bash
# Codex
cp -R JohnsonPPTskill/skills/scene-html-slides ~/.codex/skills/
```

## 用法

装好后直接在对话里说明需求，Agent 会自动加载本 skill：

> 用 scene-html-slides，根据这份大纲做场景化 HTML 演示稿，沿用默认 Logo、主题与版式，并完成逐页检查。

**两条运行路径**，skill 会按当前环境自动选择：

- **环境有内置生图工具**（如 Codex 的 `image_gen`）：逐页生成场景图 → 直接出成稿。
- **环境没有生图工具**（Claude Code 等）：先交付逐页完整的生图提示词和文件名清单，你生成图片回传后继续排版。

**制作流程**（skill 内部按此推进）：理解大纲并规划每页 → 选版式与设计元素 → 写 `deck.json` 并 `--check-plan` → 准备场景图 → 构建并按实际渲染迭代 → 逐页验证后交付。

## 随附脚本

Python 脚本用 `python3 <skill>/scripts/…` 调用，Node 脚本用 `node <skill>/scripts/…`；路径参数相对本次工作目录。

| 命令 | 作用 |
|---|---|
| `build_deck.py deck.json --check-plan --out design-plan.json` | 生图前核对设计决策与每页结构（项数、字段类型、坐标范围），**不需要图片已存在** |
| `prepare_images.py deck.json --out image-handoff` | 导出逐页生图提示词与供图清单，不调用模型、不联网 |
| `match_paper.py images/*.png` | 把配图背景贴平到纸色 `#F7F6F2`，消除图框四边淡矩形；原图备份到 `images/original/` |
| `build_deck.py deck.json --out 演示稿.html` | 构建唯一交付文件 |
| `audit_deck.cjs 演示稿.html --out qa --browser chrome` | Playwright 渲染审查：品牌不变量、图文比例、DOM 可见性，输出截图与报告 |
| `selftest.py` | 改动 skill 脚本或资源后自测，**不需要浏览器** |

常用参数：`--draft` 允许缺图的内部预排（正式交付禁用）、`--embed-format keep` 保留原图格式、`--embed-quality 85` 调压缩质量、`--builder` 加载项目自定义版式、`--allow-restyle` 仅在用户明确要求换风格时放开封面页头页脚。

## deck.json

```json
{
  "version": 1,
  "title": "采购协同方案",
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

每页 `image.brief` 必须**本页独有**（对象清单带数量、人物动作、表达关系的物理机制、层级细节、构图）；`prepare_images.py` 会拒绝模板句和跨页复制的简报。完整字段说明见 [`references/deck-format.md`](skills/scene-html-slides/references/deck-format.md)，可运行示例见 [`assets/deck.example.json`](skills/scene-html-slides/assets/deck.example.json)。

### 内置版式

| 版式 | 用途 | 版式 | 用途 |
|---|---|---|---|
| `cover` | 封面：价值与层级场景 | `architecture` | 与模型对齐的直接标注 |
| `scene` | 大场景与两侧说明 | `flow` | 步骤与控制点 |
| `split` / `triad` | 左右说明 / 三段控制 | `domains` | 多领域清单 |
| `journey` | 横向比较、阶段或路径 | `formula` | 公式与平台解释 |
| `table` | 指标与边界 | `relations` | 实体、字段与关系 |
| `closing` | 有配图的收束尾页 | | |

## 演示稿播放器

工具栏：总览 · 全屏 · 讲稿 · 编辑文字 · 另存 HTML · 打印。

| 按键 | 作用 | 按键 | 作用 |
|---|---|---|---|
| `→` `PageDown` `空格` | 下一页 | `O` | 总览 |
| `←` `PageUp` | 上一页 | `F` | 全屏 |
| `Home` / `End` | 首页 / 末页 | `N` | 讲稿面板 |
| `Esc` | 退出总览／编辑／讲稿 | `#3` | URL hash 直达第 3 页 |

## 默认设计

| 令牌 | 值 | 用途 |
|---|---|---|
| `--paper` | `#F7F6F2` | 暖白底 |
| `--blue` | `#3B7BC8` | 主蓝 |
| `--ink` | `#2B3140` | 正文 |
| `--muted` | `#5A6373` | 副标题与说明 |
| `--panel` | `#E7EEF6` | 信息块浅底 |
| `--radius` | `8px` | 圆角，不胶囊化 |

封面、尾页、页头（浅底章节标签 / 46px 主标题 / 25px 灰色副标题 / 右上 110px 页码）、页脚、暖白底与主蓝属于**品牌，不是版式选项**：`custom_css` 触碰它们会被构建器拒绝，审查器也会逐页核对（`brandOK`）。需要换风格时显式加 `--allow-restyle`。

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
skills/scene-html-slides/
├── SKILL.md                  # 技能说明与工作流
├── agents/openai.yaml        # Codex 界面配置
├── references/               # 设计系统、deck 格式、配图流程、验收标准
├── scripts/
│   ├── build_deck.py         # 构建器 + --check-plan 设计检查
│   ├── prepare_images.py     # 导出生图提示词与供图清单
│   ├── match_paper.py        # 配图背景贴平到纸色
│   ├── design_contract.py    # 设计契约校验
│   ├── common.py  selftest.py
│   ├── add_icons.cjs         # 按名字向 icons.json 追加 Lucide 图标
│   └── audit_deck.cjs        # Playwright 渲染审查
└── assets/
    ├── theme.css  player.js  template.html
    ├── icons.json            # 120 个 Lucide 蓝色线性图标
    ├── brand.json  logo.png  image-style.txt
    ├── deck.example.json     # 可运行示例（cover / scene / closing）
    └── reference-design/     # 6 张风格参考图（只作质量参照）
```

## 开发

```bash
python3 skills/scene-html-slides/scripts/selftest.py
```

改动脚本或资源后先跑自测（10 项检查，不需要浏览器），再用真实 `deck.json` 走一遍 `--check-plan` 与构建。

## 许可证

[MIT](LICENSE)。内置图标来自 [Lucide](https://lucide.dev)（MIT，见 [`assets/lucide-LICENSE.txt`](skills/scene-html-slides/assets/lucide-LICENSE.txt)）。`assets/logo.png` 与页脚为普爱智医品牌资源，请替换为你自己的品牌后再对外使用。
