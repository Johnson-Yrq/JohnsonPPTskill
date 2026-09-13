---
name: realistic-miniature-slides
description: 在用户选择写实微缩风格或续做该风格项目时，根据 PPT 大纲制作可编辑、离线 HTML 演示稿。整稿采用暖灰、石墨、灰蓝与鼠尾草绿，配图为 35–45° 等距微缩场景、写实 PBR 材质及表情细致的人物，默认无文字。风格独立，复用演讲／阅读排版套件；未选择风格的通用请求先经 ppt-workbench 确认。明确要求 PPTX 时不能用 HTML 替代。
metadata:
  version: "1.0.0"
---

# 写实微缩演示稿

将大纲制作成可编辑、可独立离线打开的单文件 HTML。整稿使用暖灰纸底、石墨文字、灰蓝重点、鼠尾草绿辅助色与少量赭黄；配图以真实材质的微缩场景呈现人物、物件与工作关系。适合软件产品、生产力系统、团队协作和解决方案，具体场景由实际内容决定。

## 选择与共享边界

- 直接调用本 Skill 即选择写实微缩；`deck.json` 根字段设为 `"style": "real-miniature"`。通用请求由 [PPT 制作工作台](../ppt-workbench/SKILL.md) 确认缺少的选择，不能仅凭“软件”“办公”等主题擅自选风格。续做保留当前项目已选方向。
- **真实演示稿动工前确认演讲型或阅读型**，按 [用途与信息密度](../white-blue-slides/references/presentation-modes.md) 执行。已在任务／项目中确认或已授权自行选择时直接采用；根字段 `presentation_mode` 记录 `speech / reading`。工具开发和两种模式的验证示例不重复触发用途问卷。
- 本包与 `white-blue-slides` 同级安装。`<style>` 为本包，`<shared>` 为同级 `white-blue-slides`，`<project>` 为当前制作目录。共用脚本、13 种版式、播放器、图标、默认公司／Logo 资源；用户品牌优先。本包只维护自己的主题、提示词、参考与规范，不复制脚本，也不加载其他风格的 SKILL 或视觉规则。
- 首次制作阅读 [设计系统](references/design-system.md)，查看 `assets/reference-design/approved-workflow.png`。这是已确认的无文字风格参考，`review-scene.png` 是同方向的协作近景样例。参考中的四区、人数、植物、箭头、顶部图形并非每页必备元素；品牌和场景内容不作为产品事实。

用途明确后，从 [演讲型示例](assets/deck.example.json) 或 [阅读型示例](assets/deck.reading.example.json) 建立项目。示例文案与数字仅用于展示排版，按实际大纲替换，不视作用户的选择或产品承诺。

## 从内容到成稿

1. **按用途拆页。** 保留用户的主线、事实、页数与格式要求。演讲型一页一个结论，细节可放 `notes`；阅读型在页面补足机制、责任、依据、条件与边界，信息密度来自可视化关系而非小字。已有尾页或页数限制时不额外加页。
2. **选共享版式并建立计划。** 按 [数据结构与构建方法](../white-blue-slides/references/deck-format.md) 使用 `cover / scene / split / triad / journey / architecture / flow / domains / formula / table / relations / closing / reading`。写明每页 `visual` 的角色、分组与理由，明确要求写入 `requirements`，先运行 `--check-plan` 并修复错误。标题默认配语义图标，不适用时写具体 `icon_omit_reason`。
3. **按页准备配图。** 阅读 [配图流程](references/image-workflow.md)。逐图简报描述对象、动作、结构、材质细节与构图；保持 35–45° 镜头和 PBR 材质，人物在场时有细致五官、自然手势与衣物褶皱。数量和关系以本页内容为准，可用无人设备场景，不把每页套成四个办公分区。默认 `ui_text: "none"`，标题、说明、数字均由 HTML 承载。
4. **组织可编辑内容。** 先给阅读型配图划出主体版面的 1/2 或 1/4；主体不含页头页脚及全宽摘要。支持左右、上下、对角双图和四分之一四种构图；多图分别解释不同阶段或视角。其余分区组合流程、矩阵、图标、解释和 [ECharts](../white-blue-slides/references/charts.md)。数量图表标明单位与来源，示例标明示例，不补造产品效果。普通条目保持无框、相同缩进；重点标题和图标可放大约 10%，不突然增加一张卡片。
5. **构建与检查。** 使用共享构建器，自动加载本包主题。按 [质量检查](references/quality-check.md) 自动检查并逐页查看，修复溢出、弱对比、图文错位、裁切及离线功能问题。必要时拆页，不用面板掩盖错位。最终交付独立 `.html`，JSON、截图和提示词是过程文件；明确要求 PPTX 或其他导出仍须完成相应格式，不能用 HTML 替代。

## 命令

解析实际安装位置，不使用开发机器的固定路径：

```sh
python3 <shared>/scripts/build_deck.py <project>/deck.json --check-plan --out <project>/design-plan.json
python3 <shared>/scripts/prepare_images.py <project>/deck.json --out <project>/image-handoff
python3 <shared>/scripts/build_deck.py <project>/deck.json --out <project>/演示稿.html
node <shared>/scripts/audit_deck.cjs <project>/演示稿.html --out <project>/qa --browser chrome
```

CSS、脚本、图表、图标、Logo 与配图全部内嵌。构建用 Python 标准库，Pillow 可压缩配图；审查器需要 Node、Playwright 与浏览器。使用环境已有运行时。没有审查器时用允许的浏览器逐页验证并说明范围，`--draft` 仅供缺图预排，不是成品。

已有素材先查看后复用。有内置生图工具时直接生成和检查；不可用时导出完整供图清单，继续独立的文字与布局工作，如实列出尚缺素材，不静默改走付费 API。修改本包或共享脚本后运行 `<shared>/scripts/selftest.py` 并用真实配图验证。未来增加方向按 [新增独立风格包](../white-blue-slides/references/adding-styles.md) 创建同级包。
