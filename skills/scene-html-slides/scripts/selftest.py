#!/usr/bin/env python3
"""Offline self-test for the skill scripts. No browser, no network; uses only skill assets and a temp dir.

Run after editing scripts/ or assets/: python3 scripts/selftest.py
"""
import copy
import io
import json
import shutil
import struct
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import ASSETS, image_size, load_deck, pillow, read_raster  # noqa: E402
from build_deck import Builder, check_plan  # noqa: E402
from design_contract import analyze_deck  # noqa: E402
from prepare_images import prepare  # noqa: E402

FAILURES = []


def check(name, condition, detail=''):
    print(('PASS ' if condition else 'FAIL ') + name + (f'  {detail}' if detail and not condition else ''))
    if not condition:
        FAILURES.append(name)


def solid_png(width, height, rgb=(247, 246, 242)):
    """Minimal valid PNG using only the standard library."""
    raw = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')


def run():
    work = Path(tempfile.mkdtemp(prefix='scene-html-slides-selftest-'))
    try:
        example = json.loads((ASSETS / 'deck.example.json').read_text(encoding='utf-8'))
        deck_path = work / 'deck.json'
        deck_path.write_text(json.dumps(example, ensure_ascii=False), encoding='utf-8')

        # 1. Plan check passes on the shipped example and reports structure as well as design.
        data, root = load_deck(deck_path)
        report = check_plan(data, root)
        check('example --check-plan ok', report['ok'], json.dumps(report['errors'], ensure_ascii=False))
        check('example has no structural errors', report['structural_errors'] == [])

        # 2. Structural problems are caught before any image exists.
        bad = copy.deepcopy(example); bad['slides'][1]['left'] = []
        data, root = load_deck(_write(work, 'structural.json', bad))
        r = check_plan(data, root)
        check('check-plan reports items out of range', not r['ok'] and any('left 需要 1–2 项' in e for e in r['errors']), json.dumps(r['errors'], ensure_ascii=False))

        # 3. Malformed field types produce clean errors, never tracebacks or miscounts.
        cases = {
            'string item in list': lambda s: s['left'].__setitem__(0, '纯字符串'),
            'benefits as string': lambda s: s.__setitem__('benefits', '对象清楚'),
            'visual as string': lambda s: s.__setitem__('visual', 'open'),
            'formula terms as strings': lambda s: s.update(layout='formula', formula={'terms': ['a', 'b']}, visual={'role': 'formula', 'treatment': 'panels', 'rationale': 'x', 'requirements': []}),
        }
        for name, mutate in cases.items():
            case = copy.deepcopy(example); mutate(case['slides'][1])
            try:
                data, root = load_deck(_write(work, 'shape.json', case))
                r = check_plan(data, root)
                check(f'clean error: {name}', not r['ok'])
            except Exception as e:  # noqa: BLE001
                check(f'clean error: {name}', False, f'raised {type(e).__name__}: {e}')
        case = copy.deepcopy(example); case['slides'][0]['benefits'] = '对象清楚'
        counts = analyze_deck(case)['pages'][0]['planned']
        check('string benefits are not counted as tags', counts['tags'] == 0, str(counts))

        # 4. Design contract rejects the classic omissions.
        for name, mutate in {
            'missing visual': lambda s: s.pop('visual'),
            'heading without icon or reason': lambda s: s['left'][0].pop('icon'),
            'explicit panels not implemented': lambda s: s['visual'].update(requirements=[{'feature': 'panels', 'min': 3, 'source': '测试'}]),
            'unknown icon': lambda s: s['left'][0].__setitem__('icon', 'NoSuchIcon'),
        }.items():
            case = copy.deepcopy(example); mutate(case['slides'][1])
            check(f'plan rejects: {name}', not analyze_deck(case)['ok'])

        # 4b. Cover copy budget: one line per tier, promise xor description, short benefit words.
        for name, mutate, expect in [
            ('two-line promise', lambda s: s.__setitem__('promise', '围绕同一业务对象\n让相关团队共享上下文'), '只写一行'),
            ('promise plus description', lambda s: s.__setitem__('description', '把分散的协作连接成一条可追溯路径。'), '只保留一个'),
            ('subtitle too long', lambda s: s.__setitem__('subtitle', '从需求、决策到履约，连接任务、责任、证据与每一次交接记录'), '上限 24'),
            ('benefit word too long', lambda s: s.__setitem__('benefits', ['对象清楚', '过程可见', '证据完整可追溯']), '超过 4 字'),
        ]:
            case = copy.deepcopy(example); mutate(case['slides'][0]); r = analyze_deck(case)
            check(f'cover rule: {name}', not r['ok'] and any(expect in e for e in r['errors']), json.dumps(r['errors'], ensure_ascii=False))
        drp = copy.deepcopy(example); drp['slides'][0].update(chapter='集团监管数字化底座', title_prefix='DRP 智能化', title='穿透式监管平台', subtitle='面向超大型集团的穿透式监管操作系统', promise='从集团全局，直达业务与凭证', benefits=['看得清', '看得透', '看得全', '管得住', '防得早', '查得清'], platforms=['本体数据建模平台', 'DRP 智能体平台'])
        check('cover rule: approved DRP cover passes', analyze_deck(drp)['ok'])

        # 5. Handoff: prompts export with missing images; formal build refuses; draft builds with markers.
        manifest = prepare(deck_path, work / 'handoff')
        check('prepare_images lists 3 missing', [i['status'] for i in manifest['images']] == ['missing'] * 3)
        check('prompt files written', (work / 'handoff' / '配图提示词.md').is_file() and (work / 'handoff' / 'image-manifest.json').is_file())
        data, root = load_deck(deck_path)
        try:
            Builder(data, root).render(); check('formal build refuses missing images', False)
        except (ValueError, OSError):
            check('formal build refuses missing images', True)
        draft = Builder(data, root, draft=True, embed_format='keep').render()
        check('draft build marks missing images', 'class="draft"' in draft and 'missing-image' in draft)

        # 6. Full build with generated images: single logo symbol, embedded payloads, conversion when Pillow exists.
        (work / 'images').mkdir(exist_ok=True)
        for i in (1, 2, 3):
            (work / 'images' / f'{i:02d}.png').write_bytes(solid_png(64, 48))
        manifest = prepare(deck_path, work / 'handoff2')
        check('prepare_images marks provided images', all(i['status'] == 'provided' for i in manifest['images']))
        data, root = load_deck(deck_path)
        builder = Builder(data, root)
        html = builder.render()
        check('html has one logo symbol and one use per slide', html.count('id="brand-logo"') == 1 and html.count('<use href="#brand-logo"') == 3)
        cover_html = html.split('</section>')[0]
        check('cover keeps the chapter tag in the header and centres the block from the title down', '<header><div class="head-copy"><div data-edit class="chapter">' in cover_html and '<div class="cover-copy"><div class="cover-head"><h1>' in cover_html and cover_html.count('<h1>') == 1 and 'class="cover-date"' in cover_html)
        check('no template placeholders left', '{{' not in html.replace('{{SLIDES}}', ''))
        check('no external references', 'src="http' not in html and '@import' not in html)
        if pillow():
            check('scene images converted to webp', builder.embed['converted'] == 3 and 'data:image/webp' in html, json.dumps(builder.embed, ensure_ascii=False))
        else:
            check('without Pillow images are kept with a note', builder.embed['kept'] == 3 and builder.embed['notes'])
        kept = Builder(data, root, embed_format='keep').render()
        check('--embed-format keep preserves png', 'data:image/png' in kept and 'data:image/webp' not in kept)

        # 7. Brand protection: custom_css may not restyle chrome; --allow-restyle marks the body; builders may not override components.
        from build_deck import custom_css_errors, load_builder
        errs = custom_css_errors('header h1{font-size:30px}.layout-cover{background:#102D51}#p02 .hero-scene{width:1100px}.point p{font-size:22px!important}')
        check('custom_css protected selectors rejected', len([e for e in errs if '不能改动' in e]) == 2 and any('!important' in e for e in errs), '\n'.join(errs))
        check('custom_css content-area rules allowed', custom_css_errors('#p02 .hero-scene{width:1100px}.journey-labels{gap:18px}@media print{.point{gap:4px}}') == [])
        (work / 'layout.css').write_text('.layout-cover h1{font-size:40px}', encoding='utf-8')
        restyled = copy.deepcopy(example); restyled['custom_css'] = 'layout.css'
        data, root = load_deck(_write(work, 'restyle.json', restyled))
        try:
            Builder(data, root, embed_format='keep').render(); check('build rejects restyling custom_css', False)
        except ValueError as e:
            check('build rejects restyling custom_css', '不能改动' in str(e))
        html = Builder(data, root, embed_format='keep', allow_restyle=True).render()
        check('--allow-restyle marks body', 'data-restyle="true"' in html)
        (work / 'bad_builder.py').write_text('from build_deck import Builder as Base\nclass Builder(Base):\n    def triad(self, s):\n        return ""\n', encoding='utf-8')
        try:
            load_builder(work, 'bad_builder.py'); check('builder overriding built-in layout rejected', False)
        except ValueError as e:
            check('builder overriding built-in layout rejected', 'triad' in str(e))
        (work / 'ok_builder.py').write_text('from build_deck import Builder as Base, items\nclass Builder(Base):\n    LAYOUTS = Base.LAYOUTS | {"timeline"}\n    def timeline(self, s):\n        return self.image(s) + "".join(self.point(v) for v in items(s, "items", 1, 6)) + self.bottom(s)\n', encoding='utf-8')
        check('builder adding a layout accepted', 'timeline' in load_builder(work, 'ok_builder.py').LAYOUTS)

        # 8. Brief quality: template sentences are rejected before prompts are exported.
        from prepare_images import brief_errors
        good = copy.deepcopy(example)
        seen = {}
        check('example briefs pass quality checks', all(not brief_errors(sl, i, seen) for i, sl in enumerate(good['slides'], 1)))
        templated = copy.deepcopy(example)
        for i, sl in enumerate(templated['slides'], 1):
            sl['image']['src'] = f'images/t{i:02d}.png'  # missing on purpose so brief checks run
            sl['image']['brief'] = {'subject': 'A wide miniature dental clinic with staff working at several stations on one platform.', 'action': '工作人员在核对记录。',
                                    'structure': 'A wide miniature dental clinic with staff working at several stations on one platform.', 'details': '白色哑光立体业务场景。'}
        seen = {}
        errs = [e for i, sl in enumerate(templated['slides'], 1) for e in brief_errors(sl, i, seen)]
        check('template briefs rejected', any('完全相同' in e for e in errs) and any('structure 与 subject 相同' in e for e in errs) and any('过短' in e for e in errs), '\n'.join(errs[:4]))
        try:
            prepare(_write(work, 'templated.json', templated), work / 'handoff3'); check('prepare_images refuses template briefs', False)
        except ValueError as e:
            check('prepare_images refuses template briefs', '简报不合格' in str(e))

        # 9. Paper matching flattens a lighting gradient onto the paper colour (needs numpy + Pillow).
        try:
            import numpy as np
            from PIL import Image as PILImage
            from match_paper import process, edge_stats
            h, w = 240, 320
            yy, xx = np.mgrid[0:h, 0:w]
            grad = (244 + 8 * xx / w + 4 * yy / h)[..., None] + np.array([0, -1, -5])
            arr = np.clip(grad, 0, 255).astype(np.uint8).copy()
            arr[90:150, 120:200] = (230, 229, 226)  # a grey object with a darker shadow band
            arr[150:160, 120:200] = (205, 204, 200)
            src = work / 'grad.png'; PILImage.fromarray(arr).save(src)
            rep = process(src, (247, 246, 242), 8, False)
            out = np.asarray(PILImage.open(src).convert('RGB')).astype(int)
            med, spread = edge_stats(out)
            obj_delta = abs(out[120, 160] - np.array([230, 229, 226])).max()
            check('match_paper flattens background to paper', tuple(int(v) for v in med) == (247, 246, 242) and spread <= 2, str(rep))
            check('match_paper keeps the subject (shift <= 8 levels)', obj_delta <= 8, str(obj_delta))
            check('match_paper keeps a backup', (work / 'original' / 'grad.png').is_file())
        except ImportError:
            print('SKIP match_paper (numpy not installed)')

        # 10. Header parsing for logo dimensions.
        check('png size parsed', image_size('image/png', solid_png(64, 48)) == (64, 48))
        Image = pillow()
        if Image:
            im = Image.new('RGB', (37, 21), (200, 200, 200))
            for fmt, mime in [('JPEG', 'image/jpeg'), ('WEBP', 'image/webp')]:
                buf = io.BytesIO(); im.save(buf, fmt); mime2, data = read_raster(_write_bytes(work, f'dim.{fmt.lower()}', buf.getvalue()))
                check(f'{fmt.lower()} size parsed', mime2 == mime and image_size(mime2, data) == (37, 21))
            buf = io.BytesIO(); im.save(buf, 'WEBP', lossless=True)
            check('webp lossless size parsed', image_size('image/webp', buf.getvalue()) == (37, 21))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    from test_style_discovery import run as run_discovery_tests
    check('automatic style discovery', run_discovery_tests() == 0)
    from test_styles import run as run_style_tests
    check('independent style regressions', run_style_tests() == 0)
    print(f'\n{"FAILED" if FAILURES else "OK"}: {len(FAILURES)} failure(s)')
    return 1 if FAILURES else 0


def _write(work, name, data):
    path = work / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return path


def _write_bytes(work, name, data):
    path = work / name
    path.write_bytes(data)
    return path


if __name__ == '__main__':
    sys.exit(run())
