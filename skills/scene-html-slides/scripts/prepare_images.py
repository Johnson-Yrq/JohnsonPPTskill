#!/usr/bin/env python3
"""Export self-contained prompts and a resumable asset manifest; never generate."""
import argparse
import json
from pathlib import Path
from common import ASSETS, load_deck, local_path, read_raster

RATIOS = {'1:1', '4:3', '3:2', '16:9', '3:4'}
FIELDS = [('subject', 'Scene inventory 场景对象与数量'), ('action', 'Action 人物正在做的事'),
          ('structure', 'Mechanism 表达关系的物理机制'), ('details', 'Details 层级、房间、设备与文件细节'),
          ('composition', 'Composition 构图与视角')]
REQUIRED = {'subject': 30, 'action': 12, 'structure': 25, 'details': 25}
UPPER_HINT = ('Display: image above, short captions below. Lay the scene out horizontally on one long low base, near-frontal slightly elevated view, '
              'no strong diagonal depth; objects ordered as in the mechanism, evenly spaced to match the columns below. The subject spans about 80% of the '
              'width with little empty space above and below; every station, figure and platform complete. Do not squeeze a compact square scene into a wide frame.')
ARCH_HINT = ('Display: one complete layered architecture model carries the whole structure; the number of tiers and modules must match the details. '
             'Leave clean surfaces on each tier front edge and beside each module for HTML labels added later; no text, label plates or frames inside the image.')


def brief_errors(slide, n, seen):
    """Reject template briefs: missing or short fields, sentences copied across pages, subject repeated as structure."""
    brief = slide['image'].get('brief')
    if not isinstance(brief, dict):
        return [f'第 {n} 页缺图，需要 image.brief（subject/action/structure/details）后才能导出提示词']
    errors = []
    for key, minimum in REQUIRED.items():
        value = brief.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f'第 {n} 页 brief.{key} 缺失：每页都要写本页自己的{dict(FIELDS)[key]}')
            continue
        text = ' '.join(value.split())
        if len(text) < minimum:
            errors.append(f'第 {n} 页 brief.{key} 过短（{len(text)} 字符，至少 {minimum}）：写具体对象、数量、动作或机制，不用通用模板句')
        if (key, text) in seen:
            errors.append(f'第 {n} 页 brief.{key} 与第 {seen[(key, text)]} 页完全相同：每页需要各自的场景描述，不能复用模板句')
        else:
            seen[(key, text)] = n
    subject, structure = brief.get('subject'), brief.get('structure')
    if isinstance(subject, str) and isinstance(structure, str) and ' '.join(subject.split()) == ' '.join(structure.split()):
        errors.append(f'第 {n} 页 brief.structure 与 subject 相同：structure 要写表达关系的物理机制（门关着、文件堆积、盖布、闸门、共用底座的通道），不是重复对象清单')
    return errors


def build_prompt(style, ratio, slide, visual, brief, upper):
    lines = [f'{label}: {" ".join(brief[key].split())}' for key, label in FIELDS if isinstance(brief.get(key), str) and brief[key].strip()]
    hint = ''
    if upper:
        hint = UPPER_HINT
    elif slide['layout'] == 'architecture' or visual.get('role') == 'architecture':
        hint = ARCH_HINT
    return f'{style}\n\nAspect ratio {ratio}.' + (f'\n{hint}' if hint else '') + '\nThis page (describe the scene; never render these words as text):\n' + '\n'.join(lines)


def prepare(filename, out):
    deck, root = load_deck(filename, layouts=None)
    style = (ASSETS / 'image-style.txt').read_text(encoding='utf-8').strip()
    manifest = {'version': 1, 'title': deck['title'], 'images': []}
    blocks = [f'# {deck["title"]} · 逐页配图提示词',
              '每条提示词可独立复制。请按指定相对文件名保存并回传图片，可分批提供或打包 ZIP。已提供的图无需重生成。配图不含文字，页面文字将在 HTML 中制作。']
    errors, seen = [], {}
    for i, slide in enumerate(deck['slides'], 1):
        im = slide['image']
        file = local_path(root, im['src'])
        exists = file.is_file()
        if exists:
            read_raster(file)
        brief = im.get('brief', {})
        visual = slide.get('visual') if isinstance(slide.get('visual'), dict) else {}
        upper = slide['layout'] == 'journey' or visual.get('image_position') == 'above'
        ratio = im.get('ratio', '16:9' if upper else '4:3')
        if ratio not in RATIOS:
            raise ValueError(f'第 {i} 页图片比例不支持：{ratio}')
        if not exists:
            errors.extend(brief_errors(slide, i, seen))
        prompt = None
        if isinstance(brief, dict) and isinstance(brief.get('subject'), str) and brief['subject'].strip():
            prompt = build_prompt(style, ratio, slide, visual, brief, upper)
        entry = {'page': i, 'slide_id': slide['id'], 'title': slide['title'], 'file': im['src'],
                 'ratio': ratio, 'alt': im['alt'], 'status': 'provided' if exists else 'missing', 'prompt': prompt}
        manifest['images'].append(entry)
        blocks.append(f'## 第 {i:02d} 页 · {slide["title"]}\n\n文件名：`{im["src"]}`\n\n比例：{ratio}；状态：' + ('已提供' if exists else '待生成'))
        blocks.append('```text\n' + prompt + '\n```' if prompt else '使用已提供的配图。')
    if errors:
        raise ValueError('配图简报不合格，先补写再导出：\n' + '\n'.join(errors))
    dest = Path(out).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / '配图提示词.md').write_text('\n\n'.join(blocks) + '\n', encoding='utf-8')
    (dest / 'image-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    missing = [x['file'] for x in manifest['images'] if x['status'] == 'missing']
    print(json.dumps({'pages': len(manifest['images']), 'missing': missing, 'output': str(dest)}, ensure_ascii=False))
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('deck')
    p.add_argument('--out', required=True)
    args = p.parse_args()
    try:
        prepare(args.deck, args.out)
    except (ValueError, OSError) as e:
        p.exit(1, f'提示词导出失败：{e}\n')


if __name__ == '__main__':
    main()
