---
name: saas-3d-slides
description: 在用户选择海蓝玻璃风格或续做该风格项目时，根据任意主题的 PPT 大纲制作可编辑、离线 HTML 演示稿，采用暖白纸底、海军蓝文字与重点面、灰青与少量香槟金、玻璃及精细微缩展陈配图。与其他风格独立，共用制作套件；未选择风格的通用请求先经 ppt-workbench 确认。明确要求 PPTX 时不能用 HTML 替代。
metadata:
  version: "1.4.0"
---

# 海蓝玻璃演示稿

将大纲制作成文字可编辑、图文对位、可独立离线打开的单文件 HTML。整份演示稿使用本风格：暖白底、海军蓝文字与重点面、灰青辅助色、少量香槟金、精细微缩展陈配图；封面、信息组件、流程、架构及尾页保持一致。

## 风格与共享套件

**动工前先确认演讲型或阅读型。** 阅读 [用途确认与信息密度](../scene-html-slides/references/presentation-modes.md)。用户未明确用途时，在拆页、排版和生图前问清并等待反馈；已选择、已在当前项目记录或已授权自行选择的模式直接采用。根字段 `presentation_mode` 记录 `speech / reading`，与 `style` 分开选择。

- 风格选择顺序：用户明确选择 > 当前项目已记录的 `style` > 询问缺少的选择。直接调用本 Skill 即选择海蓝玻璃风格；软件主题本身不代表已选择。通用请求先按 [PPT 制作工作台](../ppt-workbench/SKILL.md) 一次确认缺少的风格与类型；明确选择其他风格时通过 `<shared>/scripts/style_packs.py --list` 读取对应入口。续做旧稿保留其风格；要换风格时遵循用户指定的范围。
- 本 Skill 的 `deck.json` 根字段写 `"style": "saas-3d"`。共享构建器中，未写 `style` 的旧项目仍采用原风格。此命名风格已包含独立主题，不需要 `--allow-restyle`。
- `saas-3d-slides` 与 `scene-html-slides` 两个目录须同级安装。`<style>` 指本目录；`<shared>` 指同级 `scene-html-slides`；`<project>` 指当前制作目录。共享脚本、版式、播放器和默认公司／Logo 资源，不复制一套脚本。用户指定的品牌优先。
- 使用本 Skill 时读取本目录的设计、配图与验收规范；不加载另一套 Skill 的 `SKILL.md` 或素白蓝调视觉规范。共享的 [数据结构与构建方法](../scene-html-slides/references/deck-format.md) 只提供技术契约；视觉外观由本风格决定。

首次制作时阅读 [设计系统](references/design-system.md)，查看 `assets/reference-design/approved-product-overview.png`（已确认示例）与 `assets/reference-design/target-style.png`（目标参考）。参考图限定材质、尺度、层级和渲染气质，其中品牌、金额、图表与对象数量不构成事实或模板要求。该设计方向已确认，正常制作与检查不需要重新选择风格。

用途确认后，从 [演讲型示例](assets/deck.example.json) 或 [阅读型示例](assets/deck.reading.example.json) 建立 `<project>/deck.json`，按实际大纲修改页面与配图简报，在项目内准备 `images/`。示例字段不是用户确认，示例中的业务能力也不是产品事实；页数与布局按内容调整。

## 大纲到成稿

1. **按已确认用途拆页。** 保留主线、必要事实、明确页数与交付格式；通常一页一个结论。演讲型可将讲解细节放 `notes`；阅读型把理解结论所需的流程、比较、来源、条件和边界放在页面上，`notes` 只作补充；不制造业绩、联系人或产品截图。大纲已含尾页或限制页数时不额外加页，否则可补有配图的简洁收束页。
2. **选择共享版式。** 按关系选择 `cover / scene / split / triad / journey / architecture / flow / domains / formula / table / relations / closing / reading`。普通说明使用图标标题与留白；同层级条目保持相同缩进、正文大小与间距，需要轻量强调时按设计系统设置 `emphasis`，标题与图标可略微放大，不因强调单独增加卡片；真实分组可用浅底面板；字段或状态用标签。按内容形成节奏，不能把每页变成同一块深蓝仪表盘加三台电脑。
3. **建立并检查计划。** 使用共享数据结构，写明每页 `visual` 的角色、分组处理与理由。大纲明确的项数、图标、状态、深浅分组、架构层级等逐条进入 `requirements`。运行 `--check-plan`，先修复结构或缺项，再生图。分组标题默认选语义相关的共享 SVG 图标；不适用时填具体的 `icon_omit_reason`，不为凑数添加。
4. **按需要准备配图。** 阅读 [配图流程](references/image-workflow.md)，对需要配图的页面，按本页对象、用户操作或系统处理、业务关系、层次细节与构图写 `image.brief`。有可直接调用的内置生图工具就生成并查看；用户已给图先看后复用。没有内置工具时导出完整提示词与文件名清单，继续完成独立的文字和版式工作，准确列出尚缺图片。
5. **构建与排版。** 调用共享构建器，自动加载本目录主题与配图基底。页面标题、正文、流程、矩阵、架构标注和真实指标始终可编辑。阅读型按主体版面分区选择 1/2 左右、1/2 上下、1/2 对角双图或 1/4 配图；主体版面不含页头页脚及全宽摘要。先确定配图分区，再用图表、图标、矩阵和文字组织其余内容。有可靠数量数据时可使用 ECharts；不得缩小字号、重复插图或补造指标，放不下则拆页。需要展示的场景主体完整，按实际可见本体调整 `zoom` 与偏移；架构文字直接对齐模块，不能用面板遮错。`custom_css` 只微调内容区，确需新关系时按共享契约新增一两种版式，不覆盖公共组件。
6. **验证并交付。** 按 [质量检查](references/quality-check.md) 完成自动检查及逐页视觉检查，修复图文对应、层次、溢出、缺图和离线功能问题。最终必需交付是独立 `.html`；提示词、JSON、截图、QA 报告是过程文件。用户明确要求的其他导出仍须完成，不能拿 HTML 替代 PPTX。

数量比较、趋势或构成适合图表时，使用 [ECharts 图表契约](../scene-html-slides/references/charts.md)，保留数据来源与相邻解释。图表、数据和播放器一起内嵌，支持离线编辑与保存。

未来增加其他视觉方向时按 [新增独立风格包](../scene-html-slides/references/adding-styles.md) 创建同级包；本包只维护海蓝玻璃的主题、提示词、参考与验收规范。

## 运行命令

根据实际 Skill 安装位置解析 `<shared>`，不要保留开发机器的绝对路径。

```sh
python3 <shared>/scripts/build_deck.py <project>/deck.json --check-plan --out <project>/design-plan.json
python3 <shared>/scripts/prepare_images.py <project>/deck.json --out <project>/image-handoff
python3 <shared>/scripts/build_deck.py <project>/deck.json --out <project>/演示稿.html
node <shared>/scripts/audit_deck.cjs <project>/演示稿.html --out <project>/qa --browser chrome
```

构建器内嵌 CSS、JS、图标、Logo 与配图，不依赖 CDN；Python 标准库可构建，Pillow 用于可选 WebP 压缩。使用环境已有的 Python／Node 与浏览器，不假定固定安装路径。审查器需要 Playwright；不可用时用允许的浏览器逐页检查并如实说明范围。`--draft` 只供缺图预排，不能作为成品交付。

用户已给图片或已有项目时沿用现有映射与确认内容，按改动范围继续；不重新启动问卷或重生成所有图片。生成失败时保留已完成内容，说明缺图，交付可恢复的清单，不静默改走付费 API。修改共享脚本或本风格资源后，运行 `<shared>/scripts/selftest.py`，再用有真实配图的项目验证成稿。
