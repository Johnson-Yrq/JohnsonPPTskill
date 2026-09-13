# 配图与人工供图

每页先明确主要对象、正在发生的动作、一个核心关系和具体场景。抽象名词不能变成一堆图标。结构从分层、流程、闭环、对比、关联、协作等选一个；层数和对象来自本页大纲，不机械套示例。

## 要达到的密度

参考图和已确认的成稿都是**剖开的建筑比例模型**：多层楼板、房间、家具、设备、文件、六到十个小人各做各的事，一条淡蓝通道或一个蓝色对象点出关系。差的图是空平台上站三个大人偶、每页一样的桌子。差距不在风格基底，而在每页简报有没有写出**具体对象清单和物理机制**。

## 填写 `image.brief`

五个字段都写本页自己的内容，英文更稳定，中文也可；`prepare_images.py` 会拒绝过短、跨页相同或 subject 与 structure 相同的简报：

| 字段 | 写什么 | 例（来自已确认稿） |
|---|---|---|
| `subject` | 对象清单，带数量和位置 | A compact four-level stepped office cutaway; each level a small human passing a plain white folder through a doorway to the next |
| `action` | 人物正在做的具体动作 | one lower doorway is closed, leaving a pile of undelivered folders; only a single blue folder at top has arrived for a reviewer |
| `structure` | 表达关系的**物理机制**，不是布局名 | Six small cubic buildings on separate islands with pale water gaps and no bridges; far right a lonely cashier holding one sheet |
| `details` | 层级、房间、设备、文件、留白位置 | five identical pedestals, each scene partly covered by a soft draped cloth, only edges visible: a dental chair, a wall calendar, two dentists back to back… |
| `composition` | 画幅、视角、占比、什么必须完整 | 16:9, near-frontal slightly elevated, scene spans 80% width, empty lower band for HTML captions |

机制词汇：关门 / 文件堆积、盖布遮住、闸门与传送轨道、共用底座的凹槽通道、剖面楼层、岛屿与断桥、放大镜检查蓝色接点、把蓝色模块嵌入设备、路径逐级抬升的台地。每页选一个能解释本页结论的机制。

提示词由 `assets/image-style.txt`（英文基底）和逐页简报合成，**每条都独立完整**，不让用户另找公共前缀。

## 场景约束

- 暖白 `#F7F6F2`，白色哑光建筑黏土比例模型，微小人物自然操作、讨论、核对。
- 用业务动作表达关系，删除解释不了内容的机器人、齿轮、服务器和装饰城市。
- 一个简洁底座，场景约占 70–80%，四周 6–8% 安全边距。默认 4:3；横向流程 16:9；封面可 1:1。
- 天蓝强调不超过约 10%，其它白色和浅灰；均匀柔光，无霓虹、强镜面、戏剧化阴影。
- **纯配图无文字**：中文、英文、数字、伪文字、标签、品牌、箭头、引线、文本框、空白标题牌、PPT 外框全部不要。文件屏幕仅干净表面或非文字几何区块。
- 页面文字另由 HTML 添加，图中不绘制文字底板，也不预留整页标题区。
- 上图下文优先 16:9 横向场景：按实际阶段数横向展开，对象间距与下方列数匹配；不要生成紧凑方形主体再压进宽图框。
- 复杂架构参照 `reference-design/approved-architecture.jpg`：一张完整、多层但清楚的场景图；先在 brief.details 列出每层应有的模块、数量和位置。给层板前缘及各模块旁留下直接标注的清洁表面。
- brief.structure 必须是本页真实关系的物理表达；不能只写"wide/三卡片/左右排版"。布局名称不解释业务。

## 内置生图直接生成

仅在确认当前环境有可直接调用的内置生图工具时采用。按工具文档逐张生成、查看、保存到清单对应的项目内路径。替换时保留原图，用版本化文件名。已有用户图先看再复用。

排版前核对实际对象数量、顺序、视角、边缘留白与纸色；深浅或结构不符时修图，不用全局 multiply 压暗背景。生成图的背景几乎都带轻微光照渐变（四角相差几个灰阶），铺在纸色上就是一圈淡矩形：收到图先跑 `scripts/match_paper.py`，它拟合背景面并贴平到纸色，主体只局部偏移几个灰阶；`--dry-run` 只看数据。之后仍有清楚可见的矩形底色说明背景不是纯色，需要重生成。生成结果若仍是空平台加几个大人偶，按"要达到的密度"补写简报重生成，不将就。

失败时说明缺图并转为提示词供图，不静默改走 API 模型、不索取 Key、不用矢量图冒充场景。

## 人工供图

1. 先完成拆页、版式和 `deck.json`，独立文字工作继续。
2. 运行 `prepare_images.py`，交付 `配图提示词.md` 和 `image-manifest.json`。每页包含页码、主题、文件名、比例、完整提示词。
3. 请用户按文件名回传图片或 ZIP，例如 `images/01.png`。已有图标记 `provided`，不要求重生成。不必要求用户预先压缩：构建器内嵌时会转成 WebP；单边超过 2400px 的图可先缩小。
4. 可分批回传，每批看图并核对映射，并对每张图运行 `match_paper.py`。接收同页码 JPG/WebP 后先更新 JSON 路径；不要仅按到达顺序猜页码。
5. 缺图时精确列出文件名，保留已完成工作。可展示明确标记的草稿，但不把缺图 HTML 当成成品。
6. 收齐并逐张看过后构建、逐页验证，最终交付独立 HTML。

回传图片不等于认可错误层级或错误内容，对齐和验收仍由制作方完成。
