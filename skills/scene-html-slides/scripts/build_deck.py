#!/usr/bin/env python3
"""Build a standalone, editable HTML deck from planned content and local images."""
import argparse
import base64
from datetime import date
from html import escape
import importlib.util
import json
from pathlib import Path
import re
from common import ASSETS, EMBED_FORMATS, LAYOUTS, convert_image, image_size, load_deck, local_path, number, read_raster
from design_contract import analyze_deck, presentation_for, visual_for


# Header, footer, cover, closing and player chrome are the brand; custom_css may not touch them.
PROTECTED_SELECTOR = re.compile(r'(?:^|[\s,>+~])(?:html|body|main|header|footer|h1|\.head-copy|\.chapter|\.subtitle|\.page-number|\.brand(?:-logo)?|\.footer-label|\.layout-cover|\.layout-closing|\.cover-[a-z-]+|\.ending-[a-z-]+|\.toolbar|\.slide|\.deck|\.viewport)(?![\w-])')
# A project Builder may add layouts; it may not redefine shared components or built-in layouts.
PROTECTED_METHODS = {'__init__', 'data_uri', 'icon', 'heading', 'image', 'point', 'bottom', 'footer', 'logo_defs', 'slide', 'structural_errors', 'render'} | set(LAYOUTS)


def custom_css_errors(css):
    """Selectors that restyle protected chrome, plus !important which signals fighting the theme."""
    errors = []
    body = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    body = re.sub(r'@media[^{]*\{((?:[^{}]*\{[^{}]*\})*)[^{}]*\}', r'\1', body)
    for selector in re.findall(r'([^{}]+)\{[^{}]*\}', body):
        for part in selector.split(','):
            part = part.strip()
            if part and PROTECTED_SELECTOR.search(' ' + part):
                errors.append(f'custom_css 不能改动页头、页脚、封面、尾页或播放器：{part}')
    if '!important' in body:
        errors.append('custom_css 不使用 !important；需要覆盖主题时说明原因并用 --allow-restyle')
    return errors


def txt(value, label='文字', required=False):
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f'{label} 必须是' + ('非空' if required else '') + '字符串')
    return escape(value, quote=True).replace('\n', '<br>')


def editable(tag, value, cls='', required=False, component=''):
    return f'<{tag} data-edit' + (f' class="{cls}"' if cls else '') + (f' data-component="{component}"' if component else '') + f'>{txt(value, required=required)}</{tag}>'


def items(obj, key, low, high):
    value = obj.get(key, [])
    if not isinstance(value, list) or not low <= len(value) <= high:
        raise ValueError(f'{key} 需要 {low}–{high} 项')
    return value


def mapping(value, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} 必须为对象')
    return value


def choice(value, options, label):
    if value not in options:
        raise ValueError(f'{label} 可选：{", ".join(options)}')
    return value


def color(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValueError('颜色须为 #RRGGBB')
    return value


class Builder:
    LAYOUTS = frozenset(LAYOUTS)  # a project Builder subclass may extend this with its own layout methods

    def __init__(self, deck, root, draft=False, dry_run=False, embed_format='webp', embed_quality=85, allow_restyle=False):
        self.deck, self.root, self.draft, self.dry_run, self.allow_restyle = deck, root, draft, dry_run, allow_restyle
        for i, s in enumerate(deck['slides'], 1):
            if s['layout'] not in self.LAYOUTS:
                raise ValueError(f'第 {i} 页 layout 无效；可选 {", ".join(sorted(self.LAYOUTS))}')
        self.embed_format = choice(embed_format, list(EMBED_FORMATS), 'embed format')
        self.embed_quality = int(number(embed_quality, 85, 50, 100, 'embed quality'))
        self.brand = json.loads((ASSETS / 'brand.json').read_text(encoding='utf-8'))
        self.icons = json.loads((ASSETS / 'icons.json').read_text(encoding='utf-8'))
        self.cache, self.missing = {}, []
        self.embed = {'format': self.embed_format, 'converted': 0, 'kept': 0, 'notes': []}
        self.design = analyze_deck(deck)
        self.current_slide = {}
        if self.design['errors'] and not draft:
            raise ValueError('设计预检未通过：\n' + '\n'.join(self.design['errors'][:16]) + '\n使用 --check-plan 查看完整报告；先补齐设计决策，再正式构建')
        logo_path = local_path(root, deck['logo']) if 'logo' in deck else ASSETS / 'logo.png'
        mime, data = read_raster(logo_path)
        self.logo = {'uri': self.data_uri(logo_path, convert=False), 'size': image_size(mime, data)}

    def data_uri(self, path, convert=True):
        if path not in self.cache:
            mime, data = read_raster(path)
            if convert:
                original = mime
                mime, data, note = convert_image(mime, data, self.embed_format, self.embed_quality)
                if note and note not in self.embed['notes']:
                    self.embed['notes'].append(note)
                self.embed['converted' if mime != original else 'kept'] += 1
            self.cache[path] = f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')
        return self.cache[path]

    def icon(self, name):
        if not name:
            return ''
        if name not in self.icons:
            raise ValueError(f'未知图标 {name}；查看 assets/icons.json 中的键名')
        nodes = []
        for tag, attrs in self.icons[name]:
            attributes = ' '.join(f'{k}="{escape(str(v), quote=True)}"' for k, v in attrs.items())
            nodes.append(f'<{tag} {attributes}></{tag}>')
        return '<svg class="semantic-icon" data-component="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ''.join(nodes) + '</svg>'

    def heading(self, obj):
        mapping(obj, '内容项')
        return '<h3 class="icon-heading">' + self.icon(obj.get('icon')) + editable('span', obj.get('title', ''), 'heading-label', True) + '</h3>'

    def image(self, slide, cls='hero-scene', extra=''):
        im = slide['image']
        path = local_path(self.root, im['src'])
        zoom = number(im.get('zoom'), 1, .5, 2.5, 'image.zoom')
        x = number(im.get('offset_x'), 0, -1000, 1000, 'image.offset_x')
        y = number(im.get('offset_y'), 0, -1000, 1000, 'image.offset_y')
        fade = number(im.get('edge_fade'), .04, 0, .12, 'image.edge_fade')
        if self.dry_run:
            body = '<div class="missing-image">结构预检：' + txt(im['src']) + '</div>'
        elif not path.is_file():
            if not self.draft:
                raise FileNotFoundError(f'第 {slide["_number"]} 页缺少图片：{im["src"]}；正式构建需要收齐配图')
            self.missing.append(im['src'])
            body = '<div class="missing-image">待补配图：' + txt(im['src']) + '</div>'
        else:
            body = f'<img src="{self.data_uri(path)}" alt="{escape(im["alt"], quote=True)}" style="--image-zoom:{zoom};--image-x:{x}px;--image-y:{y}px;--image-fade:{fade * 100}%" decoding="sync">'
        return f'<figure class="scene-image {cls}"{extra}>{body}</figure>'

    def point(self, obj, allow_panel=True):
        mapping(obj, '说明')
        presentation = presentation_for(obj, self.current_slide)
        cls = 'point panel' if allow_panel and presentation == 'panel' else 'point'
        marker = ' data-component="panel"' if allow_panel and presentation == 'panel' else ''
        return f'<section class="{cls}"{marker}>' + self.heading(obj) + editable('p', obj.get('text', ''), required=True) + '</section>'

    def bottom(self, slide):
        b = slide.get('bottom')
        result = ''
        if b is not None:
            mapping(b, 'bottom')
            kind = choice(b.get('type', 'text'), ['text', 'tags', 'factors'], 'bottom.type')
            if kind == 'text':
                pres = choice(b.get('presentation', 'open'), ['open', 'panel'], 'bottom.presentation')
                result = editable('div', b.get('text', ''), 'takeaway' + (' panel' if pres == 'panel' else ''), True, 'panel' if pres == 'panel' else '')
            else:
                values = items(b, 'items', 1, 12 if kind == 'tags' else 5)
                parts = [editable('span', v, required=True, component='tag' if kind == 'tags' else 'panel') for v in values]
                label = editable('b', b.get('label', '')) if b.get('label') else ''
                result = '<div class="tag-tray">' + label + '<div>' + ''.join(parts) + '</div></div>' if kind == 'tags' else '<div class="factor-row">' + label + '<i aria-hidden="true">×</i>'.join(parts) + '</div>'
        if slide.get('footnote'):
            result += editable('p', slide['footnote'], 'footnote')
        return result

    def cover(self, s, head=''):
        """Chapter tag stays in the header; title, subtitle, promise, benefits and platforms form one block centred on the image; the date sits above the footer."""
        content = '<div class="cover-head">' + head + '</div>'
        content += editable('h2', s['promise'], 'cover-promise', True) if s.get('promise') else ''
        if s.get('description'):
            content += editable('p', s['description'], 'cover-description')
        benefits = items(s, 'benefits', 0, 6)
        if benefits:
            content += '<div class="cover-benefits">' + ''.join(editable('span', v, required=True, component='tag' if i < 3 else '') for i, v in enumerate(benefits)) + '</div>'
        platforms = items(s, 'platforms', 0, 2)
        if platforms:
            content += '<div class="cover-platforms">' + '<i aria-hidden="true">+</i>'.join(editable('span', v, required=True, component='panel') for v in platforms) + '</div>'
        date_line = editable('p', s.get('date', date.today().strftime('%Y.%m')), 'cover-date') if s.get('date', date.today().strftime('%Y.%m')) else ''
        labels = []
        for l in items(s, 'labels', 0, 5):
            mapping(l, '封面标注')
            y = number(l.get('y'), None, 200, 890, 'label.y')
            if y is None:
                raise ValueError('封面 labels 每项需要 y（整页坐标）')
            labels.append(f'<div style="top:{y}px">' + editable('h3', l.get('title', ''), required=True) + editable('p', l.get('text', '')) + '</div>')
        return '<div class="cover-copy">' + content + '</div>' + date_line + self.image(s) + '<div class="cover-labels">' + ''.join(labels) + '</div>'

    def scene(self, s):
        left, right = items(s, 'left', 1, 2), items(s, 'right', 1, 2)
        sides, panels = [], False
        for side, values in [('left', left), ('right', right)]:
            has_panels = any(presentation_for(mapping(v, side), s) == 'panel' for v in values)
            panels |= has_panels
            sides.append(f'<div class="annotation {side}"><div class="points' + (' has-panels' if has_panels else '') + '">' + ''.join(self.point(v) for v in values) + '</div></div>')
        return '<div class="scene-layout" style="--side-width:' + ('365' if panels else '330') + 'px">' + self.image(s) + ''.join(sides) + '</div>' + self.bottom(s)

    def journey(self, s):
        values = items(s, 'items', 2, 7)
        sections = []
        connected = s.get('connected', False)
        if not isinstance(connected, bool):
            raise ValueError('connected 须为布尔值')
        for v in values:
            mapping(v, '阶段/比较项')
        has_states = any(v.get('state') or v.get('states') for v in values)
        for v in values:
            panel = presentation_for(v, s) == 'panel'
            strong = choice(v.get('header_fill', 'light'), ['light', 'blue'], 'header_fill') == 'blue'
            cls = 'journey-item' + (' panel' if panel else '') + (' strong' if panel and strong else '')
            body = self.heading(v) + editable('p', v.get('text', ''), required=True)
            states = items(v, 'states', 0, 3)
            if v.get('state'):
                states = [v['state']] + states
            if has_states:
                body = '<div class="state-tags">' + ''.join(editable('span', state, 'state-tag', True, 'state') for state in states) + '</div>' + body
            if v.get('deliverable'):
                body += editable('span', v['deliverable'], 'deliverable')
            attrs = (' data-component="panel"' if panel else '') + (' data-step="true"' if connected else '')
            sections.append(f'<section class="{cls}"{attrs}>{body}</section>')
        width = number(s.get('content_width'), 1760, 900, 1760, 'content_width')
        caption_width = number(s.get('caption_width'), width, 900, width, 'caption_width')
        return '<div class="journey' + (' compact' if len(values) > 5 else '') + f'" style="width:{width}px;align-self:center">' + self.image(s) + '<div class="journey-labels' + (' connected' if connected else '') + f'" style="--columns:{len(values)};width:{caption_width}px;align-self:center">' + ''.join(sections) + '</div></div>' + self.bottom(s)

    def split(self, s):
        side = choice(s.get('image_side', 'left'), ['left', 'right'], 'image_side')
        values = items(s, 'items', 1, 3)
        return f'<div class="split-layout image-{side}">' + self.image(s) + '<div class="split-points points">' + ''.join(self.point(v) for v in values) + '</div></div>' + self.bottom(s)

    def triad(self, s):
        items(s, 'items', 3, 3)
        return self.split(dict(s, image_side=s.get('image_side', 'right')))

    def formula(self, s):
        f = mapping(s.get('formula'), 'formula')
        operator = choice(f.get('operator', '＋'), ['＋', '×'], 'formula.operator')
        terms = []
        for term in items(f, 'terms', 2, 4):
            panel = presentation_for(mapping(term, '公式因子'), s) == 'panel'
            terms.append('<div class="formula-term' + (' panel' if panel else '') + '"' + (' data-component="panel"' if panel else '') + '>' + self.heading(term) + '</div>')
        equation = '<div class="formula-equation">' + editable('strong', f.get('result', ''), 'formula-result', True) + '<i aria-hidden="true">＝</i>' + f'<i aria-hidden="true">{operator}</i>'.join(terms) + '</div>'
        values = items(s, 'items', 0, 3)
        return equation + '<div class="formula-body">' + self.image(s) + '<div class="points">' + ''.join(self.point(v) for v in values) + '</div></div>' + self.bottom(s)

    def table(self, s):
        columns = items(s, 'columns', 2, 5)
        content = '<div class="table-layout"><div class="table-wrap"><table><thead><tr>' + ''.join(editable('th', c, required=True) for c in columns) + '</tr></thead><tbody>'
        for row in items(s, 'rows', 1, 7):
            cells = items(row, 'cells', len(columns), len(columns)) if isinstance(row, dict) else row
            if not isinstance(cells, list) or len(cells) != len(columns):
                raise ValueError('表格每行单元格数量须与 columns 相同')
            content += '<tr>'
            for i, cell in enumerate(cells):
                if i == 0 and isinstance(row, dict) and row.get('icon'):
                    content += '<td><div class="icon-heading">' + self.icon(row['icon']) + editable('span', cell, required=True) + '</div></td>'
                else:
                    content += editable('td', cell, required=True)
            content += '</tr>'
        return content + '</tbody></table></div>' + self.image(s) + '</div>' + self.bottom(s)

    def relations(self, s):
        content = '<div class="relations-layout"><div class="relation-copy"><div class="relation-chains">'
        for chain in items(s, 'chains', 1, 5):
            if isinstance(chain, list): chain = {'nodes': chain}
            mapping(chain, '关系链')
            nodes = items(chain, 'nodes', 2, 5)
            directional = chain.get('directional', False)
            if not isinstance(directional, bool): raise ValueError('directional 须为布尔值')
            content += '<div class="relation-chain' + (' directional' if directional else '') + '" data-component="relation">'
            for i, node in enumerate(nodes):
                if i: content += '<i class="relation-link" aria-hidden="true">' + ('→' if directional else '—') + '</i>'
                if isinstance(node, str): node = {'text': node}
                mapping(node, '关系对象')
                content += '<div class="relation-node" data-component="tag">' + self.icon(node.get('icon')) + editable('span', node.get('text', ''), required=True) + '</div>'
            content += '</div>'
            if chain.get('relation'): content += editable('p', chain['relation'], 'relation-description')
        content += '</div><div class="points">' + ''.join(self.point(v) for v in items(s, 'items', 0, 3)) + '</div></div>'
        return content + self.image(s) + '</div>' + self.bottom(s)

    def architecture(self, s):
        b = mapping(s.get('board', {}), 'board')
        w = number(b.get('width'), 1760, 600, 2400, 'board.width')
        h = number(b.get('height'), 740, 400, 1600, 'board.height')
        rect = mapping(b.get('image', {}), 'board.image')
        x = number(rect.get('x'), 0, -w, w, 'board.image.x')
        y = number(rect.get('y'), 0, -h, h, 'board.image.y')
        iw = number(rect.get('w'), w, 1, w * 3, 'board.image.w')
        ih = number(rect.get('h'), h, 1, h * 3, 'board.image.h')
        content = self.image(s, 'architecture-image', f' style="left:{x}px;top:{y}px;width:{iw}px;height:{ih}px"')
        for l in items(s, 'labels', 1, 100):
            mapping(l, '架构标注')
            x = number(l.get('x'), None, 0, w, 'label.x')
            y = number(l.get('y'), None, 0, h, 'label.y')
            lw = number(l.get('w'), None, 1, w, 'label.w')
            lh = number(l.get('h'), None, 1, h, 'label.h')
            if None in [x, y, lw, lh] or x + lw > w or y + lh > h:
                raise ValueError('架构标注需要 x/y/w/h，且整体位于 board 内')
            size = number(l.get('font_size'), 24, 21, 40, 'label.font_size')
            align = choice(l.get('align', 'center'), ['left', 'center', 'right'], 'label.align')
            kind = choice(l.get('kind', 'module'), ['layer', 'module', 'source', 'governance', 'flow'], 'label.kind')
            align_map = {'left': 'flex-start', 'center': 'center', 'right': 'flex-end'}
            style = f'left:{x}px;top:{y}px;width:{lw}px;height:{lh}px;font-size:{size}px;text-align:{align};justify-content:{align_map[align]}'
            if l.get('color'):
                style += ';color:' + color(l['color'])
            content += f'<div class="architecture-label" data-component="architecture-label" data-kind="{kind}" style="{style}">' + editable('span', l.get('text', ''), required=True) + '</div>'
        return f'<div class="architecture-viewport"><div class="artboard" data-width="{w}" data-height="{h}" style="width:{w}px;height:{h}px">{content}</div></div>' + self.bottom(s)

    def flow(self, s):
        steps = items(s, 'steps', 3, 5)
        content = f'<div class="flow-steps" style="--columns:{len(steps)}">'
        for i, v in enumerate(steps, 1):
            content += f'<section class="flow-step" data-step="true"><span class="flow-number">{i:02d}</span><div>' + self.heading(v)
            if v.get('text'):
                content += editable('p', v['text'])
            content += '</div></section>'
        content += '</div><div class="flow-bottom">' + self.image(s) + '<div class="control-groups">'
        for v in items(s, 'groups', 2, 3):
            mapping(v, '控制分组')
            panel = presentation_for(v, s) == 'panel'
            content += '<section class="control-group' + (' panel' if panel else '') + '"' + (' data-component="panel"' if panel else '') + '>' + self.heading(v) + '<dl>'
            for row in items(v, 'rows', 1, 3):
                mapping(row, '控制行')
                content += '<div>' + editable('dt', row.get('label', ''), required=True) + editable('dd', row.get('text', ''), required=True) + '</div>'
            content += '</dl></section>'
        return content + '</div></div>' + self.bottom(s)

    def domains(self, s):
        values = items(s, 'items', 2, 10)
        split = (len(values) + 1) // 2
        content = '<div class="domain-layout">' + self.image(s)
        for half in [values[:split], values[split:]]:
            content += '<div class="domain-side"><div class="points">' + ''.join(self.point(v, False) for v in half) + '</div></div>'
        return content + '</div>' + self.bottom(s)

    def closing(self, s):
        content = editable('p', s['message'], 'ending-message') if s.get('message') else ''
        content += editable('p', s.get('product', self.deck['title']), 'ending-product')
        return '<div class="ending-copy">' + content + '</div>' + self.image(s)

    def footer(self):
        w, h = self.logo['size']
        logo = f'<svg class="brand-logo" role="img" aria-label="品牌 Logo" viewBox="0 0 {w} {h}"><use href="#brand-logo"></use></svg>'
        result = '<footer><div class="brand">' + logo + '<i aria-hidden="true"></i>' + editable('span', self.deck.get('company', self.brand['company']))
        result += editable('span', str(self.deck.get('year', date.today().year))) + '</div>'
        return result + editable('span', self.deck.get('footer_label', self.deck['title']), 'footer-label') + '</footer>'

    def logo_defs(self):
        w, h = self.logo['size']
        return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="brand-logo" viewBox="0 0 {w} {h}"><image href="{self.logo["uri"]}" width="{w}" height="{h}"></image></symbol></svg>'

    def slide(self, s, n):
        s['_number'] = n
        self.current_slide = s
        layout = s['layout']
        extra_cls = ' no-cover-labels' if layout == 'cover' and not s.get('labels') else ''
        style = ''
        if 'title_size' in s:
            style += f'--title-size:{number(s["title_size"], 46, 36, 110, "title_size")}px;'
        if 'body_size' in s:
            style += f'--body-size:{number(s["body_size"], 24, 21, 30, "body_size")}px;'
        notes = s.get('notes', '')
        if not isinstance(notes, str):
            raise ValueError('notes 必须为字符串')
        head = editable('div', s['chapter'], 'chapter') if s.get('chapter') else ''
        subtitle = editable('p', s['subtitle'], 'subtitle') if s.get('subtitle') else ''
        if layout == 'cover':
            # the chapter tag stays in the header like every other page; title and subtitle move into the centred block
            prefix = editable('span', s['title_prefix'], 'cover-prefix') if s.get('title_prefix') else ''
            main = self.cover(s, '<h1>' + prefix + editable('em', s['title'], required=True) + '</h1>' + subtitle)
        else:
            head += editable('h1', s['title'], required=True) + subtitle
            main = getattr(self, layout)(s)
        contract = escape(json.dumps(self.design['pages'][n-1], ensure_ascii=False, separators=(',', ':')), quote=True)
        return f'<section id="{s["id"]}" class="slide layout-{layout}{extra_cls}' + (' active' if n == 1 else '') + f'" style="{style}" data-design-contract="{contract}" data-speaker-notes="{escape(notes, quote=True)}" aria-label="第 {n} 页" aria-hidden="' + ('false' if n == 1 else 'true') + '"><header><div class="head-copy">' + head + f'</div><div class="page-number">{n:02d}</div></header><main>{main}</main>{self.footer()}</section>'

    def structural_errors(self):
        """Every page's layout/field problems, without images or output. Used by --check-plan."""
        errors = []
        for n, s in enumerate(self.deck['slides'], 1):
            try:
                self.slide(s, n)
            except (ValueError, OSError) as e:
                errors.append(f'第 {n} 页（{s["title"]}）：{e}')
        return errors

    def render(self):
        slides = []
        for n, s in enumerate(self.deck['slides'], 1):
            try:
                slides.append(self.slide(s, n))
            except (ValueError, OSError) as e:
                raise ValueError(f'第 {n} 页（{s["title"]}）：{e}') from e
        css = (ASSETS / 'theme.css').read_text(encoding='utf-8')
        theme = mapping(self.deck.get('theme', {}), 'theme')
        overrides = ''.join(f'--{k}:{color(v)};' for k, v in theme.items() if k in ['paper', 'blue', 'ink', 'muted', 'line', 'panel'])
        css += '\n:root{' + overrides + '}\n'
        if self.deck.get('custom_css'):
            custom = local_path(self.root, self.deck['custom_css']).read_text(encoding='utf-8')
            if re.search(r'@import|url\s*\(|</style', custom, re.I):
                raise ValueError('custom_css 仅用于布局，不支持 @import、url() 或 HTML；图片请走 image.src')
            problems = [] if self.allow_restyle else custom_css_errors(custom)
            if problems:
                raise ValueError('\n'.join(problems[:8]) + '\n默认设计的页头、页脚、封面与尾页不随大纲的“版式规范”改变；只有用户在对话中明确要求换风格时才用 --allow-restyle')
            css += custom
        template = (ASSETS / 'template.html').read_text(encoding='utf-8')
        values = {'TITLE': escape(self.deck['title']), 'CSS': css,
                  'LICENSE': '<!--\n' + (ASSETS / 'lucide-LICENSE.txt').read_text(encoding='utf-8').replace('--', '—') + '\n-->',
                  'BODY_ATTR': (' class="draft"' if self.draft else '') + (' data-restyle="true"' if self.allow_restyle else ''),
                  'LOGO_DEFS': self.logo_defs(), 'SLIDES': '\n'.join(slides),
                  'COUNT': str(len(slides)), 'JS': (ASSETS / 'player.js').read_text(encoding='utf-8')}
        return re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values[m.group(1)], template)


def load_builder(root, filename):
    """A project file defining `class Builder(build_deck.Builder)` for extra layouts."""
    import build_deck as base
    path = local_path(root, filename)
    if not path.is_file():
        raise FileNotFoundError(f'--builder 文件不存在：{filename}')
    spec = importlib.util.spec_from_file_location('project_builder', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, 'Builder', None)
    if not (isinstance(cls, type) and issubclass(cls, base.Builder)):
        raise ValueError('--builder 文件需定义 `class Builder(build_deck.Builder)`；从 build_deck 导入基类后继承')
    overridden = sorted(name for name in vars(cls) if name in PROTECTED_METHODS)
    if overridden:
        raise ValueError('自定义 Builder 只能新增版式方法，不能覆盖共享组件或内置版式：' + ', '.join(overridden) + '。需要不同结构时登记一个新版式名')
    return cls


def check_plan(data, root, builder_cls=None, allow_restyle=False):
    """Design contract plus a dry-run render of every page; needs no images."""
    report = analyze_deck(data)
    try:
        builder = (builder_cls or Builder)(data, root, draft=True, dry_run=True, allow_restyle=allow_restyle)
        structural = builder.structural_errors()
        if data.get('custom_css') and not allow_restyle:
            structural.extend(custom_css_errors(local_path(root, data['custom_css']).read_text(encoding='utf-8')))
    except (ValueError, OSError) as e:
        structural = [str(e)]
    report['structural_errors'] = structural
    report['errors'].extend('结构：' + e for e in structural)
    report['ok'] = not report['errors']
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('deck')
    p.add_argument('--out')
    p.add_argument('--check-plan', action='store_true', help='在生图前核对设计选择、大纲视觉要求与每页结构，不需要图片已存在')
    p.add_argument('--draft', action='store_true', help='允许缺图，仅供内部排版；带明显草稿标识')
    p.add_argument('--builder', help='项目内 Python 文件，定义继承 build_deck.Builder 的 Builder 类以扩展版式')
    p.add_argument('--embed-format', default='webp', choices=EMBED_FORMATS, help='配图内嵌格式，默认 webp（需 Pillow；缺少时保留原格式并提示）')
    p.add_argument('--embed-quality', type=int, default=85, help='WebP/JPEG 质量，50–100，默认 85')
    p.add_argument('--allow-restyle', action='store_true', help='仅当用户明确要求更换品牌或版式风格时使用：允许 custom_css 改动页头页脚封面尾页，并在 HTML 标记 data-restyle')
    args = p.parse_args()
    try:
        data, root = load_deck(args.deck, layouts=None)
        builder_cls = load_builder(root, args.builder) if args.builder else Builder
        load_deck(args.deck, layouts=builder_cls.LAYOUTS)
        if args.check_plan:
            report = check_plan(data, root, builder_cls, allow_restyle=args.allow_restyle)
            report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
            if args.out:
                plan_out = Path(args.out).resolve()
                plan_out.parent.mkdir(parents=True, exist_ok=True)
                plan_out.write_text(report_text, encoding='utf-8')
                print(json.dumps({'ok': report['ok'], 'pages': len(data['slides']), 'errors': report['errors'], 'warnings': report['warnings'], 'report': str(plan_out)}, ensure_ascii=False))
            else:
                print(report_text)
            if not report['ok']: p.exit(1)
            return
        if not args.out:
            raise ValueError('正式构建需要 --out 演示稿.html；仅检查设计可使用 --check-plan')
        out = Path(args.out).resolve()
        if out.suffix.lower() != '.html':
            raise ValueError('输出文件扩展名必须为 .html')
        builder = builder_cls(data, root, args.draft, embed_format=args.embed_format, embed_quality=args.embed_quality, allow_restyle=args.allow_restyle)
        html = builder.render()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
        print(json.dumps({'output': str(out), 'pages': len(data['slides']), 'bytes': out.stat().st_size,
                          'draft': args.draft, 'restyle': args.allow_restyle, 'missing': builder.missing, 'embed': builder.embed}, ensure_ascii=False))
    except (ValueError, OSError) as e:
        p.exit(1, f'构建失败：{e}\n')


if __name__ == '__main__':
    main()
