"""Plan-level design checks, independent of the HTML renderer.

This contract records what should be visible. The browser audit counts what
actually rendered, including when a project supplies its own layout methods.
"""
import json
from common import ASSETS, presentation_mode, reading_composition

ROLES = {'cover', 'closing', 'explanation', 'capabilities', 'comparison', 'process',
         'controls', 'architecture', 'entities', 'formula', 'table', 'domains', 'briefing'}
DEFAULT_ROLES = {'cover': 'cover', 'closing': 'closing', 'scene': 'explanation',
                 'split': 'explanation', 'triad': 'controls', 'journey': 'process',
                 'architecture': 'architecture', 'flow': 'process', 'domains': 'domains',
                 'formula': 'formula', 'table': 'table', 'relations': 'entities', 'reading': 'briefing'}
DEFAULT_TREATMENTS = {'cover': 'none', 'closing': 'none', 'architecture': 'labels',
                      'table': 'none', 'domains': 'open', 'explanation': 'open',
                      'capabilities': 'panels', 'comparison': 'panels', 'process': 'panels',
                      'controls': 'mixed', 'entities': 'labels', 'formula': 'panels', 'briefing': 'open'}
FEATURES = {'icons', 'panels', 'tags', 'states', 'architecture_labels', 'steps', 'relations', 'visual_blocks', 'tables', 'layers', 'charts'}
# Journey / image_position: above. The audit reads the same numbers from the page contract.
IMAGE_BALANCE = {'min_height': 460, 'min_main_ratio': 0.60, 'min_width_ratio': 0.72, 'max_caption_height': 220}


def dicts(value):
    """Dict entries of a list-valued field; anything malformed counts as empty here and is reported by shape_errors."""
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def strings(value):
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def visual_for(slide):
    visual = slide.get('visual') if isinstance(slide.get('visual'), dict) else {}
    role = visual.get('role', DEFAULT_ROLES.get(slide.get('layout'), 'explanation'))
    return dict(visual, role=role, treatment=visual.get('treatment', DEFAULT_TREATMENTS.get(role, 'open')))


def presentation_for(item, slide):
    if isinstance(item, dict) and item.get('presentation') in {'open', 'panel'}:
        return item['presentation']
    treatment = visual_for(slide)['treatment']
    return 'panel' if treatment == 'panels' else 'open'


def heading_units(slide):
    """Only headings that benefit from a semantic marker, never every text node."""
    role = visual_for(slide)['role']
    if role in {'cover', 'closing', 'architecture', 'table'}:
        return []
    units = []
    for key in ['left', 'right', 'items', 'groups']:
        units.extend(v for v in dicts(slide.get(key)) if 'title' in v)
    if slide.get('layout') == 'reading':
        units.extend(dicts(slide.get('blocks')))
    if slide.get('layout') == 'formula' and not units:
        formula = slide.get('formula')
        if isinstance(formula, dict):
            units.extend(dicts(formula.get('terms')))
    return units


def shape_errors(slide):
    """Field-type problems that would otherwise crash or silently miscount."""
    errors = []
    def expect_dicts(key, value):
        if value is not None and (not isinstance(value, list) or any(not isinstance(v, dict) for v in value)):
            errors.append(f'{key} 必须为对象数组')
    def expect_strings(key, value):
        if value is not None and (not isinstance(value, list) or any(not isinstance(v, str) for v in value)):
            errors.append(f'{key} 必须为字符串数组')
    for key in ['left', 'right', 'items', 'groups', 'steps', 'labels']:
        expect_dicts(key, slide.get(key))
    for key in ['benefits', 'platforms', 'columns']:
        expect_strings(key, slide.get(key))
    for item in dicts(slide.get('items')):
        expect_strings('items[].states', item.get('states'))
        if item.get('state') is not None and not isinstance(item['state'], str):
            errors.append('items[].state 必须为字符串')
    for group in dicts(slide.get('groups')):
        expect_dicts('groups[].rows', group.get('rows'))
    if slide.get('formula') is not None:
        if not isinstance(slide['formula'], dict):
            errors.append('formula 必须为对象')
        else:
            expect_dicts('formula.terms', slide['formula'].get('terms'))
    chains = slide.get('chains')
    if chains is not None:
        if not isinstance(chains, list):
            errors.append('chains 必须为数组')
        else:
            for chain in chains:
                nodes = chain.get('nodes') if isinstance(chain, dict) else chain
                if not isinstance(nodes, list) or any(not isinstance(n, (str, dict)) for n in nodes):
                    errors.append('chains 每条须为节点数组或含 nodes 数组的对象；节点为字符串或 {text, icon}')
                    break
    rows = slide.get('rows')
    if rows is not None and (not isinstance(rows, list) or any(not isinstance(r, (list, dict)) for r in rows)):
        errors.append('rows 每行须为单元格数组或含 cells 的对象')
    bottom = slide.get('bottom')
    if bottom is not None:
        if not isinstance(bottom, dict):
            errors.append('bottom 必须为对象')
        elif bottom.get('type') in {'tags', 'factors'}:
            expect_strings('bottom.items', bottom.get('items'))
    return errors


# Cover copy budget: every tier is one line at its fixed size, and the three copy tiers never say the same thing twice.
COVER_LIMITS = {'chapter': 12, 'title_prefix': 10, 'title': 9, 'subtitle': 24, 'promise': 18, 'description': 24}


def cover_rules(slide):
    """Errors and warnings for the cover's left column; see design-system 「封面文案层级」."""
    errors, warnings = [], []
    for key, limit in COVER_LIMITS.items():
        value = slide.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        text = value.strip()
        if '\n' in text:
            errors.append(f'封面 {key} 只写一行，不用换行；多出的意思放 notes 或尾页')
        elif len(text) > limit:
            errors.append(f'封面 {key} 有 {len(text)} 字，上限 {limit}：一行读完，不靠缩字号')
    tiers = [k for k in ('subtitle', 'promise', 'description') if isinstance(slide.get(k), str) and slide[k].strip()]
    if 'promise' in tiers and 'description' in tiers:
        errors.append('封面 promise 与 description 只保留一个：subtitle 写对象与范围，promise 写一句价值；description 仅在没有 promise 时使用')
    benefits = strings(slide.get('benefits'))
    for text in benefits:
        if len(text.strip()) > 4:
            errors.append(f'封面 benefits「{text}」超过 4 字：用能排进一格的短词')
    if benefits and len(benefits) not in (3, 6):
        warnings.append('封面 benefits 用 3 或 6 个短词才能排成整行')
    for text in strings(slide.get('platforms')):
        if len(text.strip()) > 10:
            errors.append(f'封面 platforms「{text}」超过 10 字')
    return errors, warnings


def reading_errors(slide):
    """Validate the content semantics before the composite renderer runs."""
    errors = []
    if not isinstance(slide.get('summary'), str) or not slide['summary'].strip():
        errors.append('阅读页需要可独立理解的 summary')
    blocks = slide.get('blocks')
    if not isinstance(blocks, list) or not 1 <= len(blocks) <= 4 or any(not isinstance(b, dict) for b in blocks):
        return errors + ['阅读页 blocks 需要 1–4 个模块对象']
    if not any(isinstance(b.get('type'), str) and b['type'] in {'process', 'matrix', 'layers', 'chart'} for b in blocks):
        errors.append('阅读页至少需要一种流程、矩阵或层级关系，不能只把正文拆成多个框')
    rows, filled = 1, 0
    def required_text(value, label):
        if not isinstance(value, str) or not value.strip(): errors.append(f'{label} 需要非空字符串')
    for b in blocks:
        kind, span = b.get('type'), b.get('span', 1)
        if isinstance(span, bool) or span not in (1, 2):
            errors.append('blocks[].span 可选 1 / 2'); span = 1
        if filled + span > 2: rows, filled = rows + 1, 0
        filled += span
        required_text(b.get('title'), '阅读模块标题')
        if 'note' in b: required_text(b['note'], '阅读模块 note')
        if not isinstance(kind, str) or kind not in {'process', 'matrix', 'layers', 'facts', 'chart'}:
            errors.append('blocks[].type 可选 process / matrix / layers / facts / chart'); continue
        if kind == 'chart':
            from chart_contract import chart_errors
            errors.extend(chart_errors(b))
            continue
        key, low, high = {'process': ('steps', 3, 6), 'matrix': ('rows', 2, 6), 'layers': ('layers', 2, 4), 'facts': ('rows', 2, 5)}[kind]
        values = b.get(key)
        if not isinstance(values, list) or not low <= len(values) <= high:
            errors.append(f'{kind}.{key} 需要 {low}–{high} 项'); continue
        if kind == 'matrix':
            cols = b.get('columns')
            if not isinstance(cols, list) or not 2 <= len(cols) <= 5:
                errors.append('matrix.columns 需要 2–5 个表头'); continue
            for c in cols: required_text(c, '矩阵表头')
            for row in values:
                if not isinstance(row, list) or len(row) != len(cols):
                    errors.append('阅读矩阵每行单元格数量须与 columns 相同'); continue
                for cell in row: required_text(cell, '矩阵单元格')
        else:
            for v in values:
                if not isinstance(v, dict): errors.append(f'{kind}.{key} 每项需要对象'); continue
                required_text(v.get('label' if kind == 'facts' else 'title'), f'{kind} 条目标题')
                if kind == 'layers':
                    modules = v.get('items')
                    if not isinstance(modules, list) or not 1 <= len(modules) <= 5:
                        errors.append('layers[].items 需要 1–5 个模块'); continue
                    for module in modules: required_text(module, '分层模块')
                else:
                    required_text(v.get('text'), f'{kind} 条目说明')
                    if 'output' in v: required_text(v['output'], '步骤 output')
    if rows > 2: errors.append('阅读页模块超过两行；调整 span 或拆页，保留足够的阅读空间')
    return errors


def planned_features(slide):
    counts = {k: 0 for k in FEATURES}
    texts = {k: [] for k in FEATURES}
    def add(feature, text='', count=1):
        counts[feature] += count
        if isinstance(text, str) and text.strip(): texts[feature].append(text.strip())
    units = heading_units(slide)
    if slide.get('layout') == 'table': add('tables', slide.get('title', ''))
    for item in units:
        if item.get('icon'): add('icons', item.get('title', ''))
        if slide.get('layout') not in {'domains', 'reading'} and presentation_for(item, slide) == 'panel':
            add('panels', item.get('title', ''))
    if slide.get('layout') == 'reading':
        for block in dicts(slide.get('blocks')):
            add('visual_blocks', block.get('title', ''))
            if block.get('type') == 'process':
                for stage in dicts(block.get('steps')): add('steps', stage.get('title', ''))
            elif block.get('type') == 'matrix': add('tables', block.get('title', ''))
            elif block.get('type') == 'chart': add('charts', block.get('title', ''))
            elif block.get('type') == 'layers':
                for layer in dicts(block.get('layers')):
                    add('layers', layer.get('title', ''))
                    for text in strings(layer.get('items')): add('tags', text)
    # Cover labels are direct inscriptions, not grouped information panels.
    for text in strings(slide.get('benefits'))[:3]: add('tags', text)
    for text in strings(slide.get('platforms')): add('panels', text)
    for item in dicts(slide.get('steps')):
        add('steps', item.get('title', ''))
        if item.get('icon'): add('icons', item.get('title', ''))
    items = dicts(slide.get('items'))
    if slide.get('connected'):
        for item in items: add('steps', item.get('title', ''))
    for item in items:
        for state in strings(item.get('states')): add('states', state)
        if isinstance(item.get('state'), str) and item['state']: add('states', item['state'])
    if slide.get('layout') == 'formula':
        formula = slide.get('formula')
        terms = dicts(formula.get('terms')) if isinstance(formula, dict) else []
        # With annotation headings present, operand icons are optional and extra.
        for term in terms:
            if term not in units:
                if presentation_for(term, slide) == 'panel': add('panels', term.get('title', ''))
                if term.get('icon'): add('icons', term.get('title', ''))
    for row in dicts(slide.get('rows')):
        if row.get('icon'):
            cells = row.get('cells')
            add('icons', cells[0] if isinstance(cells, list) and cells and isinstance(cells[0], str) else '')
    if visual_for(slide)['role'] == 'architecture':
        for label in dicts(slide.get('labels')):
            if 'text' in label: add('architecture_labels', label['text'])
    for chain in slide.get('chains') if isinstance(slide.get('chains'), list) else []:
        nodes = chain.get('nodes') if isinstance(chain, dict) else chain
        if not isinstance(nodes, list): continue
        add('relations')
        for node in nodes:
            if isinstance(node, dict):
                add('tags', node.get('text', ''))
                if node.get('icon'): add('icons', node.get('text', ''))
            elif isinstance(node, str): add('tags', node)
    bottom = slide.get('bottom')
    if isinstance(bottom, dict):
        if bottom.get('type') == 'tags':
            for text in strings(bottom.get('items')): add('tags', text)
        elif bottom.get('type') == 'factors':
            for text in strings(bottom.get('items')): add('panels', text)
        elif bottom.get('presentation') == 'panel': add('panels', bottom.get('text', ''))
    return counts, texts


def analyze_deck(deck):
    from style_packs import resolve_style
    style = resolve_style(deck)
    mode = presentation_mode(deck)
    icons = json.loads((ASSETS / 'icons.json').read_text(encoding='utf-8'))
    result = {'version': 2, 'presentation_mode': mode, 'mode_recorded': 'presentation_mode' in deck, 'errors': [], 'warnings': [], 'pages': []}
    for n, slide in enumerate(deck['slides'], 1):
        prefix = f'第 {n} 页（{slide["title"]}）'
        errors, warnings = shape_errors(slide), []
        if slide.get('layout') == 'reading':
            errors.extend(reading_errors(slide))
            if mode != 'reading': errors.append('reading 版式需要 presentation_mode: reading')
        raw = slide.get('visual')
        if not isinstance(raw, dict):
            errors.append('需要 visual 设计决策，包含 role、treatment、rationale、requirements；先按本页内容选择设计元素')
            raw = {}
        visual = visual_for(dict(slide, visual=raw))
        if visual['role'] not in ROLES: errors.append('visual.role 无效')
        if visual['treatment'] not in {'open', 'panels', 'mixed', 'labels', 'none'}: errors.append('visual.treatment 无效')
        if not isinstance(raw.get('rationale'), str) or not raw.get('rationale', '').strip():
            errors.append('visual.rationale 需要简述为何采用本页的图标、分组与标注方式')
        if not isinstance(raw.get('requirements'), list):
            errors.append('visual.requirements 需要数组，保留大纲明确要求的图标、卡片、状态等；无明确要求可为空')
        if visual['role'] == 'architecture' and visual['treatment'] != 'labels':
            errors.append('架构图使用 labels：模型层名与模块文字直接标注，无底板')
        units = heading_units(dict(slide, visual=visual))
        omissions = []
        for item in units:
            title = item.get('title', '')
            if item.get('icon'):
                if item['icon'] not in icons: errors.append(f'未知图标 {item["icon"]}：{title}')
            elif isinstance(item.get('icon_omit_reason'), str) and item['icon_omit_reason'].strip():
                omissions.append({'title': title, 'reason': item['icon_omit_reason']})
            else:
                errors.append(f'「{title}」缺少语义图标；选择 icon，或用 icon_omit_reason 记录真实的不适用原因')
            if visual['treatment'] == 'mixed' and item.get('presentation') not in {'open', 'panel'}:
                errors.append(f'「{title}」在 mixed 版式中需要显式选择 presentation: open/panel')
            if 'presentation' in item and item['presentation'] not in {'open', 'panel'}:
                errors.append(f'「{title}」的 presentation 无效')
            if 'emphasis' in item and not isinstance(item['emphasis'], bool):
                errors.append(f'「{title}」的 emphasis 须为布尔值')
        counts, texts = planned_features(dict(slide, visual=visual))
        requirements, manual = [], []
        for req in raw.get('requirements', []) if isinstance(raw.get('requirements'), list) else []:
            if not isinstance(req, dict):
                errors.append('视觉要求每项须为对象'); continue
            feature = req.get('feature')
            if not isinstance(req.get('source'), str) or not req['source'].strip():
                errors.append('视觉要求需要 source，注明大纲原句或已确认设计要求')
            if feature == 'manual':
                if not isinstance(req.get('text'), str) or not req['text'].strip(): errors.append('manual 要求需要 text')
                else: manual.append(req)
                continue
            if feature not in FEATURES:
                errors.append(f'不支持的视觉要求 feature：{feature}'); continue
            minimum = req.get('min', 1)
            if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0:
                errors.append(f'{feature}.min 必须为非负整数'); continue
            required_texts = req.get('texts', [])
            if not isinstance(required_texts, list) or any(not isinstance(t, str) or not t.strip() for t in required_texts):
                errors.append(f'{feature}.texts 必须为非空字符串数组'); continue
            if counts[feature] < minimum:
                errors.append(f'视觉要求未落实：{feature} 需要至少 {minimum} 个，计划只有 {counts[feature]} 个')
            missing = [t for t in required_texts if t not in texts[feature]]
            if missing: errors.append(f'视觉要求缺少 {feature} 文案：' + '、'.join(missing))
            requirements.append(dict(req, min=minimum))
        if visual['role'] == 'architecture' and not counts['architecture_labels']:
            errors.append('架构角色需要对应模型的 labels；不能只用普通段落代替直接标注')
        if slide.get('layout') == 'cover':
            cover_errors, cover_warnings = cover_rules(slide)
            errors.extend(cover_errors); warnings.extend(cover_warnings)
            if style['audit'].get('cover_labels_expected', True) and not slide.get('labels'):
                warnings.append('封面没有右侧层级标注 labels；配图含可指的层级、站点或对象时应逐项标注（参照默认封面）')
        # Include planned components even when the outline did not prescribe a count.
        expected = [{'feature': k, 'min': v, 'source': '本页设计决策'} for k, v in counts.items() if v]
        expected.extend(requirements)
        page = {'slide_id': slide['id'], 'page': n, 'presentation_mode': mode, 'role': visual['role'], 'treatment': visual['treatment'],
                'rationale': raw.get('rationale', ''), 'expected': expected, 'manual': manual,
                'omissions': omissions, 'planned': counts, 'errors': errors, 'warnings': warnings}
        if mode == 'reading':
            if slide.get('layout') == 'reading':
                composition = reading_composition(slide)
                page['composition'] = composition
                page['illustration_region_ratio'] = .25 if composition == 'quarter' else .5
            manual.append({'feature': 'manual', 'source': '阅读型主体版面分区', 'text': '按主体版面分区核对 1/2 或 1/4 配图位置；逐图确认主体完整、尺度清晰，与相邻图表和文字有对应。图表不计作插画区。'})
        if slide.get('layout') == 'journey' or raw.get('image_position') == 'above':
            page['image_balance'] = dict(IMAGE_BALANCE)
            manual.append({'feature': 'manual', 'source': '上图下文展示要求',
                           'text': '确认可见场景主体占横向图框约八成，主要对象完整；下方各列对齐对应场景。不能仅凭图片元素宽度通过。'})
        result['pages'].append(page)
        result['errors'].extend(prefix + '：' + e for e in errors)
        result['warnings'].extend(prefix + '：' + e for e in warnings)
    rich = [p for p in result['pages'] if p['role'] not in {'cover', 'closing', 'table', 'architecture'}]
    if len(rich) >= 3 and not any(p['planned']['icons'] for p in rich):
        result['warnings'].append('整稿内容页没有语义图标；复核是否确为用户要求，避免默认为纯文字模板')
    if len(rich) >= 3 and not any(sum(p['planned'].get(k, 0) for k in ['panels', 'tags', 'states', 'tables', 'charts', 'visual_blocks']) for p in rich):
        result['warnings'].append('整稿内容页只有无框文字；按阶段、能力、实体、状态逐项复核是否需要信息块或标签，不按比例硬加')
    result['ok'] = not result['errors']
    return result
