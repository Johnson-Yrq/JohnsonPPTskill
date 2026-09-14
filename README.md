<a id="readme-top"></a>

<div align="center">

<h1>JohnsonPPTskill</h1>

<p><strong>Turn an outline into a polished, editable slide deck.</strong></p>
<p>Three visual styles. Two ways to present. One HTML file that works offline.</p>

<p><strong>English</strong> · <a href="README.zh-CN.md">简体中文</a></p>

<p>
  <a href="#quick-start">Quick start</a> ·
  <a href="#visual-styles">Visual styles</a> ·
  <a href="#presentation-modes">Presentation modes</a> ·
  <a href="#build-and-check">Build &amp; check</a>
</p>

<p><code>Codex / Claude Code</code> &nbsp; <code>Toolkit v3.1.2</code> &nbsp; <a href="LICENSE">MIT License</a></p>

</div>

---

Start with [`ppt-workbench`](skills/ppt-workbench/SKILL.md), choose a visual style and a presentation mode, and build a deck from your outline. Each style maintains its own theme, illustration prompts, and references, while sharing the same layout, editing, and validation toolkit.

| Consistent design | Content that fits the audience | A portable result |
|---|---|---|
| Matching covers, typography, illustrations, and closing slides. | Concise slides for live talks, or detailed pages for independent reading. | Embedded CSS, JavaScript, images, icons, and charts, with editing and printing built in. |

> **Output format:** the builder produces a self-contained `.html` file. For an explicit `.pptx` request, use a PowerPoint-capable workflow; this toolkit does not export HTML to PPTX.

## Visual styles

Actual slide examples from the three included styles. Click an image to view it at full size. Business content and chart values shown here are illustrative.

| White & Blue | Navy Glass | Realistic Miniature |
|:---:|:---:|:---:|
| <a href="skills/white-blue-slides/assets/reference-design/approved-open-icons.jpg"><img src="skills/white-blue-slides/assets/reference-design/approved-open-icons.jpg" alt="White and Blue slide with a matte white model, blue icons, and editable explanations" width="290"></a> | <a href="docs/images/examples/speech-product.png"><img src="docs/images/examples/speech-product.png" alt="Navy Glass product slide with navy headings, teal accents, and a glass display scene" width="290"></a> | <a href="docs/images/examples/miniature-speech-cover.png"><img src="docs/images/examples/miniature-speech-cover.png" alt="Realistic Miniature cover with warm gray paper, graphite typography, and a detailed team workspace" width="290"></a> |
| Warm white · Bright blue · Matte models | Navy · Glass · Champagne gold | Warm gray · Natural materials · Expressive figures |
| [`white-blue-slides`](skills/white-blue-slides/SKILL.md) | [`navy-glass-slides`](skills/navy-glass-slides/SKILL.md) | [`realistic-miniature-slides`](skills/realistic-miniature-slides/SKILL.md) |

All three styles support both presentation modes. Choose one style per deck; the subject, actions, and relationships in each illustration come from the content.

<details>
<summary><strong>Style IDs, visual details, and more examples</strong></summary>

| Style | `style` ID | Visual direction |
|---|---|---|
| **White & Blue** · 素白蓝调 | `scene-white` | Warm white paper, vivid blue accents, matte white model scenes, and miniature figures. |
| **Navy Glass** · 海蓝玻璃 | `saas-3d` | Warm white paper, navy text and emphasis areas, muted teal, a little champagne gold, and detailed glass displays. |
| **Realistic Miniature** · 写实微缩 | `real-miniature` | Warm gray, graphite, gray blue, sage, and a little ochre; 35–45° miniature scenes with realistic PBR materials and expressive figures. Text-free illustrations. |

| White & Blue · Layered architecture | Navy Glass · Presentation cover |
|:---:|:---:|
| <a href="skills/white-blue-slides/assets/reference-design/approved-architecture.jpg"><img src="skills/white-blue-slides/assets/reference-design/approved-architecture.jpg" alt="Layered white architecture model with labels and blue data paths" width="440"></a> | <a href="docs/images/examples/speech-cover.png"><img src="docs/images/examples/speech-cover.png" alt="Navy Glass cover with a value proposition and a three-dimensional product display" width="440"></a> |

| Realistic Miniature · Reading layout | White & Blue · Page reference |
|:---:|:---:|
| <a href="docs/images/examples/miniature-reading-diagonal.png"><img src="docs/images/examples/miniature-reading-diagonal.png" alt="Realistic Miniature reading page with diagonal scenes, a responsibility matrix, and a donut chart" width="440"></a> | <a href="skills/white-blue-slides/assets/reference-design/approved-overview.jpg"><img src="skills/white-blue-slides/assets/reference-design/approved-overview.jpg" alt="White and Blue reference page showing scene composition and visual hierarchy" width="440"></a> |

Illustration references: [Navy Glass product display](skills/navy-glass-slides/assets/reference-design/approved-product-overview.png) · [Realistic Miniature team workspace](skills/realistic-miniature-slides/assets/reference-design/approved-workflow.png).

References establish materials, scale, and visual hierarchy. Their business content is not a factual source for a new project.

</details>

## Quick start

### 1. Install the skills

With Node.js/npm installed, use the [Skills CLI](https://github.com/vercel-labs/skills#options) to install directly from this repository.

**Codex**

```bash
npx skills@latest add Johnson-Yrq/JohnsonPPTskill --skill '*' -g -a codex
```

**Claude Code**

```bash
npx skills@latest add Johnson-Yrq/JohnsonPPTskill --skill '*' -g -a claude-code
```

`--skill '*'` installs the workbench and all three style packages together; keep the quotes around `*`. `-g` makes the skills available across projects; omit it for a project-local installation. `-a` selects the agent.

<details>
<summary><strong>List available skills or install manually</strong></summary>

List the skills without installing:

```bash
npx skills@latest add Johnson-Yrq/JohnsonPPTskill --list
```

Or clone the repository:

```bash
git clone https://github.com/Johnson-Yrq/JohnsonPPTskill.git
cd JohnsonPPTskill
```

Copy the four packages into the directory for your agent.

**Codex**

```bash
mkdir -p ~/.codex/skills
cp -R skills/ppt-workbench skills/white-blue-slides skills/navy-glass-slides skills/realistic-miniature-slides ~/.codex/skills/
```

**Claude Code**

```bash
mkdir -p ~/.claude/skills
cp -R skills/ppt-workbench skills/white-blue-slides skills/navy-glass-slides skills/realistic-miniature-slides ~/.claude/skills/
```

Keep the four directories side by side. `white-blue-slides` includes the shared toolkit used by the other styles; `ppt-workbench` provides the common entry point. Back up existing skill directories before updating. If you only need White & Blue, you can install `white-blue-slides` on its own.

</details>

### 2. Give your agent an outline

**If you want to choose the style and mode together:**

```text
Use $ppt-workbench to turn this outline into a slide deck.
First, let me choose a visual style and a mode: live presentation or independent reading.
```

**If you already know what you want:**

```text
Use $ppt-workbench with the Navy Glass style in reading mode.
Organize this outline into illustrations, processes, matrices, and charts as appropriate.
Check every slide before delivery.
```

<details>
<summary><strong>Call a style directly</strong></summary>

```text
Use $white-blue-slides to make a White & Blue deck for a live presentation from this outline.
```

```text
Use $navy-glass-slides to make a Navy Glass deck for independent reading from this proposal.
```

```text
Use $realistic-miniature-slides to make a reading deck from this team collaboration proposal.
Keep the illustrations free of text.
```

</details>

The agent asks only for missing choices and reuses decisions already confirmed for the current project. If you explicitly delegate the choice, it selects and explains a suitable direction. Template defaults do not count as your choice, and a change of subject does not automatically change an existing deck's style.

### 3. Open, present, and edit

Open the delivered HTML in a browser. Present offline, edit text and chart data, then use **Save HTML** (`另存 HTML`) to keep your changes. Browser edits do not automatically update the source `deck.json`.

The English README documents the existing toolkit; skill instructions, reference documents, examples, and player controls are currently primarily in Chinese.

## Presentation modes

| | Live presentation · `speech` | Independent reading · `reading` |
|---|---|---|
| **Audience** | A speaker guides the audience. | Readers explore the deck on their own. |
| **Content** | One conclusion with a few supporting points; details can go in speaker notes. | Mechanisms, evidence, conditions, and boundaries stay on the page. |
| **Visuals** | A main scene, key steps, and a few annotations. | Illustrations, processes, matrices, tables, icons, and charts. |
| **Illustration area** | May be the main visual focus. | Reserve half or a quarter of the body area first. |
| **When content grows** | Split it into a sequence of slides. | Split it into related pages while preserving readable type and image area. |

Reading mode adds meaningful relationships and evidence, not smaller type or longer paragraphs. When reliable numbers are unavailable, use processes, responsibilities, comparisons, or layers instead of inventing metrics.

Record both choices at the root of `deck.json`:

```json
{
  "style": "saas-3d",
  "presentation_mode": "reading"
}
```

This snippet shows only the two selection fields; a complete project also needs its title and slides. Older decks without these fields remain compatible with White & Blue and speech mode. New projects should record explicit choices. See [modes and information density](skills/white-blue-slides/references/presentation-modes.md).

### Four reading layouts

The proportions apply to the **slide body**, excluding headers, footers, and full-width summaries. Charts, icons, and logos are content elements, not illustrations.

| Layout | `composition` | Illustration placement | Remaining content |
|---|---|---|---|
| **Half · Left / right** | `half_lr` | One main image in the left half. | A chart with explanation, or a process with a responsibility matrix. |
| **Half · Top / bottom** | `half_tb` | 1–3 images in the top half. | Two complementary groups, such as a process and a trend. |
| **Half · Diagonal** | `half_diagonal` | One image at top left and one at bottom right. | One content block in each of the other two quadrants. |
| **Quarter · One image** | `quarter` | One image in the top-left quarter. | Three blocks combining charts, tables, icons, and text. |

<details>
<summary><strong>Preview all four reading layouts</strong></summary>

| Half · Left / right | Half · Top / bottom |
|:---:|:---:|
| <a href="docs/images/examples/reading-half-lr.png"><img src="docs/images/examples/reading-half-lr.png" alt="Left-right reading layout with a product scene, bar chart, and explanatory text" width="440"></a> | <a href="docs/images/examples/reading-half-tb.png"><img src="docs/images/examples/reading-half-tb.png" alt="Top-bottom reading layout with two scenes above a process and a line chart" width="440"></a> |

| Half · Diagonal | Quarter · One image |
|:---:|:---:|
| <a href="docs/images/examples/reading-half-diagonal.png"><img src="docs/images/examples/reading-half-diagonal.png" alt="Diagonal reading layout with two images, a capability matrix, and a donut chart" width="440"></a> | <a href="docs/images/examples/reading-quarter.png"><img src="docs/images/examples/reading-quarter.png" alt="Quarter-image reading layout with a comparison chart, delivery checklist, and usage boundaries" width="440"></a> |

Navy Glass screenshots, each 1920 × 1080. Chart values are sample data.

</details>

Reserve the image areas before arranging the other content. Multiple images should explain different subjects, stages, or viewpoints, with complete subjects and consistent colors and materials. Align headings and content to their regions; use modest changes in size, icon scale, or weight for emphasis. See the [complete reading example](skills/navy-glass-slides/assets/deck.reading.example.json).

### Offline charts and editable data

Reading pages support **horizontal bar, line, and donut charts** for category comparisons, time trends, and parts of a whole. Include units and sources, explain the conclusion and its limits beside the chart, and clearly label sample data.

In the player, select **Edit text** (`编辑文字`), then expand **Edit chart data** (`编辑图表数据`) at the chart's bottom right. Change categories, series names, and values; the chart updates immediately. Saving and reopening the HTML preserves editability. Recheck the accompanying conclusions after changing values.

The library, data, and SVG charts work offline without a CDN. Supported inputs are 2–8 categories and 1–3 series of finite, nonnegative values. Donut charts accept one series with a positive total. See the [chart reference](skills/white-blue-slides/references/charts.md).

## Workflow and illustrations

**Choose style and mode → Read the outline → Plan layouts → Write `deck.json` → Check the plan → Prepare images → Build → Inspect every slide → Deliver**

| Available assets | What happens next |
|---|---|
| **Existing images** | Inspect and reuse them, checking that each image matches its slide's content. |
| **A directly callable image-generation tool** | Generate from per-slide briefs, inspect the images, and refine them before building. |
| **No built-in image-generation tool** | Export complete per-slide prompts and an asset checklist, then continue when images are supplied. Images can arrive in batches. |

Each missing image needs a unique `image.brief` describing subjects and counts, actions or system behavior, relationships, hierarchy, detail, and composition. The exporter checks for missing fields and repeated briefs across slides. Keep titles, real data, business explanations, and architecture labels in editable content.

<details>
<summary><strong>Text inside illustrations and delivery files</strong></summary>

White & Blue and Realistic Miniature use text-free illustrations by default. Realistic Miniature only supports `ui_text: "none"`, including on whiteboards, screens, documents, calendars, and keycaps. Navy Glass defaults to `ui_text: "demo"`, allowing only **Overview**, **Analytics**, **Activity**, and **Demo** inside software screens; it also supports `none`. Decorative charts in illustrations are not real business data.

The final deliverable is one standalone `.html` file. Keep `deck.json`, prompts, asset checklists, and QA screenshots for production and future edits. A `--draft` build with missing images is only an internal layout preview.

</details>

## Build and check

Run these commands from the repository root. `project/` is the working directory for your deck.

```text
project/
├── outline.md
├── deck.json
├── images/          # Project illustrations
├── presentation.html
└── qa/              # Screenshots and inspection reports
```

### Start from an example

| Example | Included content |
|---|---|
| [White & Blue](skills/white-blue-slides/assets/deck.example.json) | Cover, scene-based information pages, and a closing slide. |
| [Navy Glass · Speech](skills/navy-glass-slides/assets/deck.example.json) | A concise product introduction with subtle emphasis. |
| [Navy Glass · Reading](skills/navy-glass-slides/assets/deck.reading.example.json) | All four reading layouts, processes, matrices, and charts. |
| [Realistic Miniature · Speech](skills/realistic-miniature-slides/assets/deck.example.json) | A team workspace, collaboration handoffs, and subtle emphasis. |
| [Realistic Miniature · Reading](skills/realistic-miniature-slides/assets/deck.reading.example.json) | All four reading layouts, responsibilities, and sample task charts. |

Examples include illustration briefs. Prepare the required images before a final build. Image paths are relative to the directory containing `deck.json`. See the [deck format reference](skills/white-blue-slides/references/deck-format.md).

### Validate, prepare, build, and inspect

```bash
# 1. Check design decisions and slide structure; images need not exist yet.
python3 skills/white-blue-slides/scripts/build_deck.py project/deck.json \
  --check-plan --out project/design-plan.json

# 2. Export prompts and an asset checklist; no model or network calls.
python3 skills/white-blue-slides/scripts/prepare_images.py project/deck.json \
  --out project/image-handoff

# 3. Build the self-contained HTML once all images are ready.
python3 skills/white-blue-slides/scripts/build_deck.py project/deck.json \
  --out project/presentation.html

# 4. Inspect the rendered deck and save screenshots of every slide.
node skills/white-blue-slides/scripts/audit_deck.cjs project/presentation.html \
  --out project/qa --browser chrome
```

Automated checks cover structure, image/content regions, visible components, and player behavior (including the PPTX export). Visual review must also verify complete image subjects, accurate image/text relationships, and sufficient context for independent readers. The auditor writes `visual-review.template.json`; after inspecting every page, fill in the review record and pass it back with `--visual-review qa/visual-review.json`. `readyForDelivery` in the report requires both the automated checks and the review record to pass; without a record the exit code is unchanged.

<details>
<summary><strong>Build options and all 13 shared layouts</strong></summary>

| Tool or option | Purpose |
|---|---|
| `match_paper.py project/images/*.png --deck project/deck.json --dry-run` | Diagnose background color and alpha against the active theme; permitted local correction handles mild differences and keeps backups. |
| `--embed-format keep` | Keep the original image format instead of the default WebP preference. |
| `--embed-quality 85` | Set image compression quality. |
| `--builder` | Load project-specific layouts that reuse shared components. |
| `--allow-restyle` | Allow cover, header, or footer customization beyond the chosen theme when explicitly requested by the user. |

Selecting a supplied style does not require `--allow-restyle`.

| Layout | Purpose | Layout | Purpose |
|---|---|---|---|
| `cover` | Cover | `architecture` | Layered architecture with direct labels |
| `scene` | A main scene with notes on both sides | `flow` | Steps and control points |
| `split` / `triad` | Two-sided explanations / three-part controls | `domains` | Multiple domain lists |
| `journey` | Stages, comparisons, or paths | `formula` | Formulas and relationships between factors |
| `table` | Tables and boundary comparisons | `relations` | Entities and connections |
| `closing` | An illustrated closing slide | `reading` | The four composite reading layouts |

Structured fields (see `references/deck-format.md`): `flow` control groups accept `rows_layout` (auto / inline / stacked), a row `kind` (detail / check / exception) and, in reading mode, `align_control_rows` for shared row heights; `architecture` labels accept `prefix`, `detail`, a `leader` line and a flow `direction`; `journey` stages accept a `period` tag and a `fields` group, and the bottom band accepts `bottom.type: groups`; image ratios add `2:1 / 21:9 / 3:1`, and `image.background_mode: white-matte` maps confirmed pure-white assets onto the current paper color consistently in HTML, PDF and PPTX.

</details>

## Present, edit, and save

The player includes **Overview · Fullscreen · Speaker notes · Edit text · Save HTML · Export PPTX · Export PDF / Print**. Its default canvas is 1920 × 1080 and scales proportionally to the window. Use **Save HTML** after editing; browser changes do not write back to `deck.json`.

Fullscreen fits the entire 16:9 slide to the available screen without stretching or cropping; editing reserves space for the toolbar. PDF pages use PowerPoint widescreen dimensions: **960 × 540 pt (13⅓ × 7.5 in)**. The toolbar opens the browser print dialog; select Save as PDF and avoid overriding the slide size with A4 or Letter.

For reproducible PDF dimensions and a single-page, fit-to-page opening preference, export with the included script (requires `pdf-lib` in addition to Playwright):

```bash
# Use the saved HTML as input if you edited the deck in the browser.
node skills/white-blue-slides/scripts/export_pdf.cjs project/presentation.html \
  --out project/presentation.pdf --browser chrome
```

PDF readers may ignore viewing preferences; select **Fit page** if needed. On macOS, Chrome's PDF presentation mode can expose a thin strip of the next page when **Show scroll bars** is set to **Always**. In the reproduced case, changing **System Settings → Appearance → Show scroll bars → When scrolling**, then exiting presentation mode, reloading the PDF, and entering **Present** again removed the strip. This setting affects scroll bars system-wide. Changing PDF paper size does not address that viewer issue. Screens with other aspect ratios retain side or top/bottom bars.

The **HTML player** also provides a **Fullscreen** button. If PDF presentation is requested, verify the actual PDF in the chosen reader; a successful HTML presentation does not validate the PDF viewer.

**Export PPTX** produces an editable PowerPoint file in one universal font (Microsoft YaHei by default, available in Office on Windows and macOS): headings and body text stay text boxes with their size, weight, colour and spacing; panels, tags and rules become shapes; scene images and icons become pictures; ECharts become native PowerPoint charts with an embedded workbook (**Edit Data** works); speaker notes become slide notes. Positions are measured from the rendered page, so the PPTX matches the HTML; fonts are substituted, so Latin text and digits can run slightly wider. The exporter is embedded in every deck and needs no network. The same export is available from the command line, which also handles decks built before the button existed:

```bash
node skills/white-blue-slides/scripts/export_pptx.cjs project/presentation.html \
  --out project/presentation.pptx --browser chrome [--font "PingFang SC"]
```

If only the PDF remains, create an offline HTML presentation with the included converter (Python + Poppler). It displays one page at a time and preserves vector outlines. This presentation copy has no editable or selectable text; keep the PDF and any editable source.

```bash
python3 skills/white-blue-slides/scripts/pdf_to_slides.py project/presentation.pdf \
  --out project/presentation-fullscreen.html
```

Existing HTML files embed their original player; rebuild from the source project to pick up fixes, preserving any browser-edited copies first.

| Key | Action | Key | Action |
|---|---|---|---|
| `→` / `PageDown` / `Space` | Next slide | `O` | Overview |
| `←` / `PageUp` | Previous slide | `F` | Fullscreen |
| `Home` / `End` | First / last slide | `N` | Speaker notes |
| `Esc` | Close overview, editing, or notes | URL `#3` | Open slide 3 directly |

## Extend the toolkit

Each style package owns its theme, illustration base prompt, references, and quality rules. Shared scripts handle layouts and functionality without being duplicated per style.

List the available styles:

```bash
python3 skills/white-blue-slides/scripts/style_packs.py --list
```

Discovery returns the name, ID, description, and skill entry point for valid sibling packages. New packages appear automatically without editing the workbench's options.

<details>
<summary><strong>Package structure and adding a style</strong></summary>

Use a lowercase, hyphenated English package name ending in `-slides`, matching the skill name. The Chinese display name appears in the workbench selection.

```text
skills/
├── ppt-workbench/                 # Common entry point
├── white-blue-slides/             # White & Blue + shared toolkit
│   ├── scripts/                  # Build, asset handoff, discovery, and QA
│   ├── assets/                   # Components, player, layouts, and charts
│   └── references/               # Data, modes, charts, and extension rules
├── navy-glass-slides/             # Independent style package
├── realistic-miniature-slides/    # Independent style package
└── new-style-slides/              # Future sibling package
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

Declare `schema: "html-slide-style/v1"`, a unique ID, style resources, and an audit contract in `assets/style.json`. After sample approval and validation, mark the package `ready` and install it alongside the others. The workbench, builder, and image exporter discover it automatically. New styles reuse both presentation modes and all four reading layouts.

```bash
# Include draft packages for development checks; this does not activate them.
python3 skills/white-blue-slides/scripts/style_packs.py --list --include-drafts
```

See [adding an independent style package](skills/white-blue-slides/references/adding-styles.md) for fields, integration steps, and validation requirements.

</details>

### Dependencies and development checks

| Task | Dependencies |
|---|---|
| Build HTML, export prompts, list styles | Python 3.9+ standard library |
| Optional WebP compression | Pillow; original formats are preserved if unavailable |
| Match illustration backgrounds | NumPy + Pillow |
| Automated browser inspection | Node.js + Playwright + Chrome/Chromium |
| Editable PPTX export from the command line | Playwright + Chrome/Chromium (the toolbar button needs nothing) |
| PDF export and automated print validation | Playwright + pdf-lib + Chrome/Chromium |
| Offline presentation from an existing PDF | Python + Poppler (`pdfinfo`, `pdftocairo`) |
| Optional overview contact sheet | Sharp |

ECharts 5.6.0 is bundled; no separate installation or CDN is needed. Image generation depends on the agent environment and is not installed with the skills. If automated inspection is unavailable, inspect each slide in an available browser and state the scope of validation.

After changing scripts or assets, run:

```bash
python3 skills/white-blue-slides/scripts/selftest.py
```

The self-test covers shared components, both modes, style isolation, dynamic style discovery, chart inputs, and recovery from missing images. After theme or layout changes, also build with real illustrations and inspect every slide; self-tests do not replace visual review.

## License and assets

Project code is licensed under [MIT](LICENSE). Third-party components retain their own licenses:

- Lucide icons: [MIT license](skills/white-blue-slides/assets/lucide-LICENSE.txt).
- Apache ECharts: [Apache 2.0 license](skills/white-blue-slides/assets/vendor/ECHARTS-LICENSE.txt) and [NOTICE](skills/white-blue-slides/assets/vendor/ECHARTS-NOTICE.txt), also embedded in decks that contain charts.

The bundled logo and default footer are brand assets of 普爱智医 (PLANCK AI LABS); replace them for other brands. Reference images demonstrate visual styles. Example business content and numbers are not claims about actual product capabilities or results.

---

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="#readme-top">Back to top ↑</a></p>
