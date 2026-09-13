# 新增独立风格包

用于用户持续添加视觉方向时。风格包维护自己的视觉资产；数据结构、13 种版式、演讲／阅读密度、图表、编辑、保存、离线与打印共用 `scene-html-slides` 制作套件。

## 目录与自动发现

在同一 skills 根目录新增文件夹，例如 `new-style-slides/`，不要把新方向写进已有风格的提示词或 CSS：

```text
new-style-slides/
├── SKILL.md                         # 独立入口、所选 style id、共享脚本路径
├── agents/openai.yaml               # 显示名称与包含 $技能名 的默认提示
├── assets/
│   ├── style.json                   # 自动发现与资源清单
│   ├── theme.css                    # 整稿视觉主题
│   ├── image-style.txt              # 配图材质、尺度、镜头与禁止项
│   └── reference-design/            # 目标参考与已确认样例（有则保留）
└── references/
    ├── design-system.md            # 页面、字阶、强调与配图的设计规则
    ├── image-workflow.md           # 本风格提示词、复用图片与生图流程
    └── quality-check.md            # 本风格视觉检查 + 共享功能检查
```

构建器只发现同级 `*/assets/style.json` 中声明 `schema: "html-slide-style/v1"` 的包；无需改 Python 注册表、工作台菜单或已有风格。文件夹名用 Skill 名；`id` 是整稿选择值，两者可不同但必须稳定。`id` 在同级包中唯一，只用小写字母、数字和短横线，最长 64 字符。重名时拒绝选择，不按目录顺序覆盖。

## 最小清单示例

下面是新包的结构示例，名称、描述和视觉参数须按新方向填写。现有风格包的清单也可作为字段参考，但不要继承不属于新方向的材质、配色或提示词禁令。

```json
{
  "schema": "html-slide-style/v1",
  "id": "new-style",
  "name": "新风格名称",
  "description": "用一句话说明视觉特点与适用内容。",
  "status": "draft",
  "css": "theme.css",
  "image_prompt": "image-style.txt",
  "ui_text_modes": ["none"],
  "default_ui_text": "none",
  "ui_text_prompts": {
    "none": "No text in the illustration. Keep labels and factual data as editable page content."
  },
  "layout_hints": {},
  "audit": {
    "max_radius": 8,
    "page_number_min": 36,
    "cover_labels_expected": false,
    "chapter_panel": false,
    "closing_title_token": "--ink"
  }
}
```

- `status`：`draft` 供开发时检查，常规清单不列出且构建器拒绝使用；`ready` 表示可用于制作。现有已确认方向不用重新确认。新方向先生成代表性图片／页面样例供用户确认，再在项目源码中设为 ready，完成下面的构建与视觉验证后安装。`--draft` 是演示稿缺图预排，与风格包状态无关，不能绕过风格选择。
- `css / image_prompt / image_reference` 路径相对本包 `assets/`，不接受绝对路径或目录外资源。`image_prompt` 必填；`image_reference` 可选，填写后提示词导出器会随供图清单复制它。`css` 可为 null，但会沿用基础主题；独立新视觉应提供自己的主题。
- `ui_text_modes / default_ui_text / ui_text_prompts` 定义配图内的文字策略，默认值须列于可用策略且每种策略有提示。页面标题、真实数据和业务说明始终由可编辑内容承载；图片上的示意界面不作为事实来源。
- `layout_hints` 可选：`above` 补充上图下文构图，`architecture` 补充分层结构要求。未提供时不注入其他风格的构图提示。
- `audit` 是本风格可检查的约束：最大圆角、最小页码字号、封面是否需层级标签、章节标签是否需底板、尾页标题对应的颜色令牌。数值按设计设置，不能为了跳过真实问题随意降低标准。

## 主题与共享边界

主题加载顺序为基础组件 → 阅读型几何布局（启用时）→ 所选风格 CSS → 用户已要求的项目颜色覆盖。新主题完整声明 `--paper / --blue / --ink / --muted / --line / --panel / --radius`，可用 `--diagram-accent` 指定流程和图表辅助色；颜色令牌使用六位十六进制。覆盖封面、页头、页码、图标、面板、表格、流程、图表与尾页的视觉，但复用内容区布局与阅读型四种分区。不同风格 CSS 不会同时加载。

图表三色依次读取 `--diagram-accent / --diagram-strong / --chart-tertiary`，网格读取 `--chart-grid`。新风格可声明后两项以完成独立配色；未声明时保留现有主题的图表颜色，兼容旧稿。

`SKILL.md` 写清本包对应的 `style`，引用共享的 [类型规则](presentation-modes.md)、[数据结构](deck-format.md)、[图表契约](charts.md) 和运行命令；不读取原风格的 SKILL 正文作为制作流程。使用动态工作台只确认缺少的选择，已确认的模式不再询问。每个包支持 speech 与 reading，差异放在信息组织而非另建重复风格包。

若新风格需要超出现有布局契约的行为，先明确实际需要再扩展共享组件；不要用一个改名主题冒充尚不支持的版式。主题与 JS 保持本地内嵌，不引入 CDN、远程字体或外部图片。配图背景使用本风格 `--paper`；需要校准时向 `match_paper.py` 显式传 `--paper '#RRGGBB'`。

## 接入验证与安装

1. 用 `python3 <shared>/scripts/style_packs.py --list --include-drafts` 检查清单、资源与重复 ID，修复相关错误。
2. 新方向样例已确认后设为 ready。分别以 speech 和 reading 编制代表性 `deck.json`，先 `build_deck.py ... --check-plan`，再 `prepare_images.py ...` 核对独立提示词、参考与逐图文字策略。
3. 复用或生成真实配图，构建并逐页查看；覆盖封面、信息页、尾页及阅读型左右／上下／对角／四分之一布局，有图表时检查编辑、保存重开与离线。计划、成稿与供图清单必须记录新 ID；现有风格不能随之改变。
4. 运行共享 `scripts/selftest.py`。它会验证动态扩展风格在两种类型中可构建、已安装主题可使用全部共享版式、风格资源独立及缺失／重名／草稿等错误处理；实际新主题的视觉仍需第 3 步检查。
5. 将新包同级安装到实际 skills 目录；共享套件有改动时一并更新。运行安装位置的 `style_packs.py --list`，新包应出现在工作台清单。更新现有安装前备份相关目录，不覆盖无关技能。

新增风格只需维护自己的包。现有项目按其 `style` 继续制作，新项目在工作台选择可用风格与类型。
