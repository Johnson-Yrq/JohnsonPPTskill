#!/usr/bin/env python3
"""Export self-contained prompts and a resumable asset manifest; never generate."""
import argparse
import json
import shutil
from pathlib import Path
from common import load_deck, local_path, read_raster, presentation_mode, slide_images, IMAGE_RATIOS
from style_packs import resolve_style, ui_text_prompt, paper_color

RATIOS = IMAGE_RATIOS
FIELDS = [('subject', 'Scene inventory 场景对象与数量'), ('action', 'Action 用户操作或系统处理'),
          ('structure', 'Mechanism 表达关系的物理机制'), ('details', 'Details 层级、房间、设备与文件细节'),
          ('composition', 'Composition 构图与视角')]
REQUIRED = {'subject': 30, 'action': 12, 'structure': 25, 'details': 25}


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


def build_prompt(style, ratio, slide, visual, brief, upper, pack=None, mode='speech'):
    pack = pack or resolve_style({})
    lines = [f'{label}: {" ".join(brief[key].split())}' for key, label in FIELDS if isinstance(brief.get(key), str) and brief[key].strip()]
    hint = ''
    if upper:
        hint = pack['layout_hints'].get('above', '')
        hint += '\nUse the requested aspect ratio and distribute the actual subject across the composition, aligned with the caption columns. If a panoramic frame is requested, compose a shallow wide scene; do not stretch the objects or simulate width with empty side margins.'
    elif slide['layout'] == 'architecture' or visual.get('role') == 'architecture':
        hint = pack['layout_hints'].get('architecture', '')
    if mode == 'reading' and slide['layout'] == 'reading':
        hint += '\nThis illustration is a substantial visual explanation on a reading slide: illustrations occupy the selected half or quarter of the content-body regions, separate from the header and footer. Compose a large, complete, clearly legible subject with modest safety margins. Each image explains its own part of the content; avoid duplicate scenes or decorative filler. Detailed processes, matrices, labels and factual data remain separate editable content; do not bake those into the image.'
    policy = ui_text_prompt(pack, slide['image'].get('ui_text', pack['default_ui_text']))
    return f'{style}\n\nAspect ratio {ratio}.' + (f'\n{hint}' if hint else '') + (f'\n{policy}' if policy else '') + '\nThis page (describe the scene; never render these words as text):\n' + '\n'.join(lines)


def prepare(filename, out):
    deck, root = load_deck(filename, layouts=None)
    pack = resolve_style(deck)
    style = pack['image_prompt'].read_text(encoding='utf-8').strip()
    reference = pack.get('image_reference')
    reference_name = 'style-reference' + reference.suffix if reference else None
    mode = presentation_mode(deck)
    paper = paper_color(deck, pack)
    manifest = {'version': 1, 'title': deck['title'], 'presentation_mode': mode, 'style': pack['id'], 'paper': paper, 'style_reference': reference_name, 'images': []}
    text_note = ('屏幕内文字按每页 ui_text 策略生成，页面标题与业务说明在 HTML 中制作。' if pack['ui_text_modes'] != ['none']
                 else '配图不含文字，页面文字将在 HTML 中制作。')
    blocks = [f'# {deck["title"]} · 逐页配图提示词',
              '每条提示词可独立复制。请按指定相对文件名保存并回传图片，可分批提供或打包 ZIP。已提供的图无需重生成。' + text_note,
              f'整稿风格：{pack["name"]}（`{pack["id"]}`）。']
    if reference:
        blocks.append(f'生成时同时附上本目录的 `{reference_name}`，作为已确认的材质、比例与视觉层次参考；本页对象与关系仍以逐页简报为准。')
    errors, seen = [], {}
    for i, slide in enumerate(deck['slides'], 1):
        for image_index, im in enumerate(slide_images(slide), 1):
            file = local_path(root, im['src'])
            exists = file.is_file()
            if exists:
                read_raster(file)
            brief = im.get('brief', {})
            visual = slide.get('visual') if isinstance(slide.get('visual'), dict) else {}
            upper = slide['layout'] == 'journey' or visual.get('image_position') == 'above'
            ratio = im.get('ratio', '16:9' if upper or slide['layout'] == 'reading' else '4:3')
            if ratio not in RATIOS:
                raise ValueError(f'第 {i} 页图片比例不支持：{ratio}')
            if not exists:
                errors.extend(brief_errors(dict(slide, image=im), f'{i}（配图 {image_index}）', seen))
            prompt = None
            if isinstance(brief, dict) and isinstance(brief.get('subject'), str) and brief['subject'].strip():
                prompt = build_prompt(style, ratio, dict(slide, image=im), visual, brief, upper, pack, mode)
                rgb = tuple(int(paper[j:j+2], 16) for j in (1, 3, 5))
                prompt += f'\nRequired background for BOTH new generation and image edits: {paper}, RGB {rgb}. Generate directly on this exact flat page colour across all exposed margins and gaps between objects. Preserve local contact shadows; do not add a contrasting rectangular studio backdrop or vignette. Do not substitute a white intermediate matte, another neutral grey, or a painted transparency checkerboard. This target overrides any different background in the reference or source image. Inspect the actual output against the page before accepting it.'
            entry = {'page': i, 'image_index': image_index, 'slide_id': slide['id'], 'title': slide['title'], 'file': im['src'],
                     'ratio': ratio, 'paper': paper, 'ui_text': im.get('ui_text', pack['default_ui_text']), 'alt': im['alt'], 'status': 'provided' if exists else 'missing', 'prompt': prompt}
            manifest['images'].append(entry)
            blocks.append(f'## 第 {i:02d} 页 · 配图 {image_index} · {slide["title"]}\n\n文件名：`{im["src"]}`\n\n比例：{ratio}；状态：' + ('已提供' if exists else '待生成'))
            blocks.append('```text\n' + prompt + '\n```' if prompt else '使用已提供的配图。')
    if errors:
        raise ValueError('配图简报不合格，先补写再导出：\n' + '\n'.join(errors))
    dest = Path(out).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    if reference and reference.resolve() != (dest / reference_name).resolve():
        shutil.copy2(reference, dest / reference_name)
    (dest / '配图提示词.md').write_text('\n\n'.join(blocks) + '\n', encoding='utf-8')
    (dest / 'image-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    missing = [x['file'] for x in manifest['images'] if x['status'] == 'missing']
    print(json.dumps({'pages': len(deck['slides']), 'image_count': len(manifest['images']), 'presentation_mode': mode, 'style': pack['id'], 'missing': missing, 'output': str(dest)}, ensure_ascii=False))
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
