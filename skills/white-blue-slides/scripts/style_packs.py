"""Discover independent presentation styles beside the shared toolkit.

Only declarative manifests bearing our schema are considered; deck data cannot
supply a package path or executable loader. Adding a sibling style needs no code edit.
"""
import argparse
import json
import math
import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
SCHEMA = 'html-slide-style/v1'
ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def _scan():
    found, errors = {}, []
    for path in sorted(SKILLS.glob('*/assets/style.json')):
        try:
            pack = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError) as exc:
            errors.append(f'不能读取风格清单 {path}: {exc}')
            continue
        if not isinstance(pack, dict) or pack.get('schema') != SCHEMA:
            continue  # unrelated skills may also use a file called style.json
        name = pack.get('id')
        if not isinstance(name, str) or len(name) > 64 or not ID.fullmatch(name):
            errors.append(f'风格 id 需要短横线分隔的小写字母或数字：{path}')
            continue
        found.setdefault(name, []).append((path, pack))
    return found, errors


def _load(path, source, allow_draft=False):
    pack = dict(source)
    for key in ('name', 'description'):
        if not isinstance(pack.get(key), str) or not pack[key].strip():
            raise ValueError(f'风格清单 {key} 需要非空说明：{path}')
    status = pack.get('status')
    if status not in ('ready', 'draft'):
        raise ValueError(f'风格 status 可选 ready / draft：{path}')
    if status != 'ready' and not allow_draft:
        raise ValueError(f'{pack["id"]} 仍为 draft；先完成风格样例确认和验证，再设为 ready')
    assets, root = path.parent.resolve(), path.parent.parent.resolve()
    for field in ('css', 'image_prompt', 'image_reference'):
        value = pack.get(field)
        if value is None and field != 'image_prompt':
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'风格清单 {field} 需要相对文件路径：{path}')
        resource = (assets / value).resolve()
        if Path(value).is_absolute() or not resource.is_relative_to(assets) or not resource.is_file():
            raise ValueError(f'风格资源缺失或路径无效：{field}={value}（{path}）')
        pack[field] = resource
    for file in ('SKILL.md', 'references/design-system.md', 'references/image-workflow.md', 'references/quality-check.md'):
        resource = (root / file).resolve()
        if not resource.is_relative_to(root) or not resource.is_file():
            raise ValueError(f'风格说明缺失或路径无效：{root / file}')
    modes = pack.get('ui_text_modes')
    if not isinstance(modes, list) or not modes or any(not isinstance(m, str) or not ID.fullmatch(m) for m in modes):
        raise ValueError(f'ui_text_modes 需要非空策略名称数组：{path}')
    default = pack.get('default_ui_text')
    if not isinstance(default, str) or default not in modes:
        raise ValueError(f'default_ui_text 必须列于 ui_text_modes：{path}')
    prompts = pack.get('ui_text_prompts')
    if not isinstance(prompts, dict) or any(not isinstance(prompts.get(m), str) for m in modes):
        raise ValueError(f'每种 ui_text 策略需要对应提示词：{path}')
    hints = pack.get('layout_hints', {})
    if not isinstance(hints, dict) or any(not isinstance(v, str) for v in hints.values()):
        raise ValueError(f'layout_hints 需要字符串映射：{path}')
    audit = pack.get('audit')
    if not isinstance(audit, dict):
        raise ValueError(f'风格需要 audit 检查契约：{path}')
    for key in ('max_radius', 'page_number_min'):
        value = audit.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < (1 if key == 'page_number_min' else 0):
            raise ValueError(f'audit.{key} 需要有效的非负数（页码字号至少 1）：{path}')
    for key in ('cover_labels_expected', 'chapter_panel'):
        if key in audit or key == 'cover_labels_expected':
            if not isinstance(audit.get(key), bool):
                raise ValueError(f'audit.{key} 需要布尔值：{path}')
    pack.update(layout_hints=hints, skill_file=root / 'SKILL.md', manifest=path.resolve())
    return pack


def paper_color(deck, pack=None):
    """Resolve paper using the same base → style → deck override order as the builder."""
    from common import ASSETS
    pack = pack or resolve_style(deck)
    result = None
    for css in [ASSETS / 'theme.css', pack.get('css')]:
        if css:
            source = re.sub(r'/\*.*?\*/', '', css.read_text(encoding='utf-8'), flags=re.S)
            colors = re.findall(r'--paper\s*:\s*(#[0-9a-fA-F]{6})\b', source)
            if colors: result = colors[-1]
    theme = deck.get('theme', {})
    if not isinstance(theme, dict):
        raise ValueError('theme 须为对象')
    result = theme.get('paper', result)
    if not isinstance(result, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', result):
        raise ValueError('无法解析当前主题纸色；theme.paper 须为 #RRGGBB')
    return result.upper()


def discover_styles(include_drafts=False):
    found, errors = _scan()
    styles = []
    for name, candidates in sorted(found.items()):
        if len(candidates) != 1:
            errors.append(f'风格 id 重复，无法选择 {name}：' + '、'.join(str(p) for p, _ in candidates))
            continue
        path, source = candidates[0]
        if source.get('status') == 'draft' and not include_drafts:
            continue
        try:
            pack = _load(path, source, allow_draft=include_drafts)
            styles.append({'id': name, 'name': pack['name'], 'description': pack['description'], 'status': pack['status'],
                           'skill_file': str(pack['skill_file']), 'manifest': str(pack['manifest']),
                           'image_reference': str(pack['image_reference']) if pack.get('image_reference') else None,
                           'presentation_modes': ['speech', 'reading']})
        except ValueError as exc:
            errors.append(str(exc))
    return {'styles': styles, 'errors': errors}


def resolve_style(deck):
    name = deck.get('style', 'scene-white')
    if not isinstance(name, str) or len(name) > 64 or not ID.fullmatch(name):
        raise ValueError('style 需要已安装风格的 id；运行 style_packs.py --list 查看')
    found, scan_errors = _scan()
    candidates = found.get(name, [])
    if len(candidates) > 1:
        raise ValueError(f'风格 id 重复，无法选择 {name}：' + '、'.join(str(p) for p, _ in candidates))
    if not candidates:
        available = ', '.join(s['id'] for s in discover_styles()['styles']) or '无'
        raise ValueError(f'缺少或未知的 style：{name}；可用：{available}。将风格技能与 white-blue-slides 同级安装到 skills 目录；运行 style_packs.py --list 查看资源问题。' + ('\n' + '\n'.join(scan_errors) if scan_errors else ''))
    pack = _load(*candidates[0])
    from common import slide_images
    for i, slide in enumerate(deck.get('slides', []), 1):
        if not isinstance(slide, dict):
            continue
        images = slide_images(slide)
        if 'style' in slide or any('style' in image for image in images):
            raise ValueError(f'第 {i} 页不能单独设置 style；整稿在根对象选择一种风格')
        for image in images:
            mode = image.get('ui_text', pack['default_ui_text'])
            if not isinstance(mode, str) or mode not in pack['ui_text_modes']:
                raise ValueError(f'第 {i} 页 image.ui_text 可选 {" / ".join(pack["ui_text_modes"])}（当前 {name} 风格）')
    return pack


def ui_text_prompt(pack, mode):
    return pack['ui_text_prompts'][mode]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='列出已安装且资源有效的风格，输出 JSON')
    parser.add_argument('--include-drafts', action='store_true', help='开发新风格时检查草稿，不使其可用于正式构建')
    args = parser.parse_args()
    result = discover_styles(args.include_drafts)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
