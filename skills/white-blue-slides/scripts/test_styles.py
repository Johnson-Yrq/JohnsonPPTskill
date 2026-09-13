#!/usr/bin/env python3
"""Offline behavioral checks for independent styles sharing the slide runtime.

Run: python3 scripts/test_styles.py
Uses existing raster assets and temporary project/install directories only.
"""
import contextlib
import copy
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SAAS = SKILL.parent / 'navy-glass-slides'
MINIATURE = SKILL.parent / 'realistic-miniature-slides'
sys.path.insert(0, str(HERE))
from build_deck import Builder, check_plan  # noqa: E402
from common import slide_images, ASSETS, LAYOUTS, load_deck  # noqa: E402
from prepare_images import prepare  # noqa: E402


class Document(HTMLParser):
    """Inspect delivered HTML rather than renderer implementation details."""
    def __init__(self, html):
        super().__init__()
        self.body, self.pages, self.images = {}, {}, []
        self.styles, self.scripts, self.editable = [], [], 0
        self.capture = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'body':
            self.body = attrs
        if tag == 'section' and 'slide' in attrs.get('class', '').split():
            self.pages[attrs['id']] = attrs
        if tag == 'img':
            self.images.append(attrs)
        if 'data-edit' in attrs:
            self.editable += 1
        if tag in ('style', 'script'):
            self.capture = tag

    def handle_endtag(self, tag):
        if tag == self.capture:
            self.capture = None

    def handle_data(self, data):
        if self.capture == 'style':
            self.styles.append(data)
        elif self.capture == 'script':
            self.scripts.append(data)


def write_deck(root, data, name='deck.json'):
    path = root / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return path


def quiet_prepare(path, out):
    with contextlib.redirect_stdout(io.StringIO()):
        return prepare(path, out)


def all_layouts_deck(style):
    """Small valid content fixtures exercise every public shared layout."""
    def point(title):
        return {'title': title, 'text': '这项内容说明业务对象与操作。', 'icon': 'CircleCheck'}

    specs = {
        'cover': {'promise': '清楚呈现业务关系', 'benefits': ['统一入口', '过程清楚', '协作有序']},
        'scene': {'left': [point('业务入口')], 'right': [point('处理结果')]},
        'split': {'items': [point('业务入口'), point('处理结果')]},
        'triad': {'items': [point('入口'), point('处理'), point('结果')]},
        'journey': {'items': [point('接收'), point('完成')], 'connected': True},
        'architecture': {'labels': [{'text': '服务层', 'kind': 'layer', 'x': 20, 'y': 20, 'w': 200, 'h': 50}]},
        'flow': {'steps': [point('接收'), point('审核'), point('完成')], 'groups': [
            dict(point('入口控制'), rows=[{'label': '接收', 'text': '核对输入'}]),
            dict(point('结果控制'), rows=[{'label': '完成', 'text': '核对结果'}])]},
        'domains': {'items': [point('领域一'), point('领域二')]},
        'formula': {'formula': {'result': '可用方案', 'terms': [point('业务'), point('产品')]}},
        'table': {'columns': ['业务', '能力'], 'rows': [['任务入口', '统一接收']]},
        'relations': {'chains': [{'nodes': ['业务对象', '处理记录'], 'relation': '对象关联对应记录'}]},
        'closing': {'message': '从工作场景出发'},
        'reading': {'summary': '在同页核对处理顺序和使用边界。', 'blocks': [
            {'type': 'process', 'title': '处理顺序', 'icon': 'Workflow', 'span': 2, 'steps': [point('接收'), point('校验'), point('完成')]},
            {'type': 'facts', 'title': '使用边界', 'icon': 'FileCheck2', 'rows': [{'label': '前提', 'text': '先确认业务对象。'}, {'label': '范围', 'text': '按真实方案实施。'}]}]},
    }
    slides = []
    for layout, extra in specs.items():
        role = layout if layout in ('cover', 'closing', 'architecture', 'table', 'formula', 'domains') else 'explanation'
        treatment = 'labels' if layout == 'architecture' else 'none' if layout in ('cover', 'closing', 'table') else 'open'
        slides.append(dict(extra, id='test-' + layout, layout=layout, title='产品方案',
                           image={'src': 'images/existing.png', 'alt': '离线测试用现有图片'},
                           visual={'role': role, 'treatment': treatment, 'rationale': '按内容验证共享版式。', 'requirements': []}))
    return {'version': 1, 'style': style, 'presentation_mode': 'reading', 'title': '共享版式回归测试', 'slides': slides}


@unittest.skipUnless((SAAS / 'assets/style.json').is_file(), 'optional sibling navy-glass-slides is not installed')
class StyleRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='slide-styles-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.legacy = json.loads((ASSETS / 'deck.example.json').read_text(encoding='utf-8'))
        self.saas = json.loads((SAAS / 'assets/deck.example.json').read_text(encoding='utf-8'))
        self.reading = json.loads((SAAS / 'assets/deck.reading.example.json').read_text(encoding='utf-8'))

    def provide(self, slides):
        for slide in slides:
            for im in slide_images(slide):
                path = self.root / im['src']
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ASSETS / 'logo.png', path)

    def render(self, deck, draft=False):
        data, root = load_deck(write_deck(self.root, deck))
        return Builder(data, root, draft=draft, embed_format='keep').render()

    def cli(self, script, deck, *args, scripts=HERE):
        return subprocess.run([sys.executable, str(scripts / script), str(deck), *map(str, args)],
                              cwd=self.root, capture_output=True, text=True, timeout=30)

    def test_implicit_and_explicit_legacy_are_equivalent(self):
        self.legacy.pop('style', None)
        self.provide(self.legacy['slides'])
        implicit = self.render(copy.deepcopy(self.legacy))
        explicit_deck = dict(copy.deepcopy(self.legacy), style='scene-white')
        self.assertEqual(implicit, self.render(explicit_deck))
        path = write_deck(self.root, self.legacy)
        first = quiet_prepare(path, self.root / 'implicit')
        second = quiet_prepare(write_deck(self.root, explicit_deck), self.root / 'explicit')
        self.assertEqual(first, second)
        self.assertIsNone(first['style_reference'])
        self.assertEqual(Document(implicit).body['data-style'], 'scene-white')

    def test_presentation_mode_is_independent_and_legacy_default_is_preserved(self):
        for style in ('scene-white', 'saas-3d'):
            deck = copy.deepcopy(self.saas if style == 'saas-3d' else self.legacy)
            deck['style'] = style
            self.provide(deck['slides'])
            explicit = self.render(deck)
            deck.pop('presentation_mode', None)
            self.assertEqual(explicit, self.render(deck))
            data, root = load_deck(write_deck(self.root, deck))
            report = check_plan(data, root)
            self.assertFalse(report['mode_recorded'])
            self.assertEqual(report['presentation_mode'], 'speech')
        for value in ('auto', 'mixed', None, False, ['reading']):
            deck = dict(copy.deepcopy(self.saas), presentation_mode=value)
            for script, args in (('build_deck.py', ('--check-plan',)),
                                 ('prepare_images.py', ('--out', self.root / 'invalid-mode'))):
                result = self.cli(script, write_deck(self.root, deck), *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('presentation_mode', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
        deck = copy.deepcopy(self.saas)
        deck['slides'][1]['presentation_mode'] = 'reading'
        with self.assertRaisesRegex(ValueError, '不能单独设置 presentation_mode'):
            load_deck(write_deck(self.root, deck))

    def test_reading_requires_illustrations_and_keeps_multiple_images_editable(self):
        deck = copy.deepcopy(self.reading)
        deck['slides'] = [deck['slides'][3]]  # two independent images above one complete process
        slide = deck['slides'][0]
        missing = copy.deepcopy(deck)
        missing['slides'][0].pop('images')
        with self.assertRaisesRegex(ValueError, '每页需要 image'):
            self.render(missing)
        complete_example = quiet_prepare(write_deck(self.root, self.reading), self.root / 'example-prompts')
        self.assertEqual(len(complete_example['images']), sum(len(slide_images(s)) for s in self.reading['slides']))
        first = quiet_prepare(write_deck(self.root, deck), self.root / 'multi-prompts')
        self.assertEqual([im['image_index'] for im in first['images']], [1, 2])
        self.assertTrue(all(im['status'] == 'missing' for im in first['images']))
        self.assertNotEqual(first['images'][0]['prompt'], first['images'][1]['prompt'])
        self.assertEqual(len(Document(self.render(deck, draft=True)).images), 0)
        self.provide([dict(slide, images=[slide['images'][0]])])
        partial = quiet_prepare(write_deck(self.root, deck), self.root / 'multi-partial')
        self.assertEqual([im['status'] for im in partial['images']], ['provided', 'missing'])
        self.assertEqual(len(Document(self.render(deck, draft=True)).images), 1)
        with self.assertRaisesRegex(ValueError, '缺少图片'):
            self.render(deck)
        self.provide(deck['slides'])
        html = self.render(deck)
        doc = Document(html)
        self.assertEqual(doc.body['data-presentation-mode'], 'reading')
        self.assertEqual(len(doc.images), 2)
        self.assertGreater(doc.editable, 20)
        self.assertIn('data-edit class="reading-caption"', html)
        self.assertIn('data-visual-type="process"', html)
        self.assertNotIn('class="missing-image"', html)
        data, root = load_deck(write_deck(self.root, deck))
        self.assertEqual(check_plan(data, root)['pages'][0]['illustration_region_ratio'], .5)
        deck['presentation_mode'] = 'speech'
        with self.assertRaisesRegex(ValueError, 'reading 版式需要'):
            self.render(deck)

    def test_visual_reading_content_is_not_reported_as_plain_text(self):
        from design_contract import analyze_deck
        report = analyze_deck(self.reading)
        self.assertTrue(report['ok'], report['errors'])
        self.assertFalse(any('只有无框文字' in w for w in report['warnings']))
        # Keep the useful warning for a genuinely unstructured speech deck.
        speech = copy.deepcopy(self.saas)
        speech['slides'] = []
        for i in range(3):
            slide = copy.deepcopy(self.saas['slides'][1])
            slide['id'] = f'plain-{i}'
            for point in slide['items']:
                point['presentation'] = 'open'
            speech['slides'].append(slide)
        self.assertTrue(any('只有无框文字' in w for w in analyze_deck(speech)['warnings']))

    def test_multiple_images_reject_ambiguous_or_ignored_fields(self):
        cases = [
            lambda s: s.update(image=s['images'][0]),
            lambda s: s.update(images=[]),
            lambda s: s.update(images='invalid'),
            lambda s: s.update(images=s['images'] * 2),
            lambda s: s.update(images=[None]),
            lambda s: s.update(images=[s['images'][0], s['images'][0]]),
            lambda s: s['images'][1].update(style='scene-white'),
            lambda s: s['images'][1].update(ui_text='invalid'),
            lambda s: s['images'][1].update(alt=''),
            lambda s: s['images'][1].update(caption=False),
            lambda s: s['images'][1].update(src='../outside.png'),
            lambda s: s.update(layout='split'),
        ]
        for mutate in cases:
            deck = copy.deepcopy(self.reading)
            deck['slides'] = [deck['slides'][3]]
            mutate(deck['slides'][0])
            with self.assertRaises(ValueError):
                load_deck(write_deck(self.root, deck))

    def test_compositions_and_chart_inputs_are_checked(self):
        for slide in self.reading['slides'][1:-1]:
            deck = dict(copy.deepcopy(self.reading), slides=[copy.deepcopy(slide)])
            data, root = load_deck(write_deck(self.root, deck))
            report = check_plan(data, root)
            self.assertTrue(report['ok'], report['errors'])
            self.assertEqual(report['pages'][0]['composition'], slide['composition'])
        chart = copy.deepcopy(self.reading['slides'][1]['blocks'][0])
        from chart_contract import chart_errors
        for field, value in [('chart_type', 'pie3d'), ('source', ''), ('unit', ''), ('categories', ['one']), ('series', [{'name': 'bad', 'values': [float('nan')]*4}]), ('series', [{'name': 'bad', 'values': [-1]*4}])]:
            self.assertTrue(chart_errors(dict(chart, **{field: value})), field)
        for composition in ('diagonal', None, ['half_lr']):
            deck = dict(copy.deepcopy(self.reading), slides=[dict(copy.deepcopy(self.reading['slides'][1]), composition=composition)])
            with self.assertRaises(ValueError): load_deck(write_deck(self.root, deck))
        quarter = copy.deepcopy(self.reading['slides'][5]); quarter['blocks'].pop()
        with self.assertRaisesRegex(ValueError, '三个内容模块'):
            load_deck(write_deck(self.root, dict(self.reading, slides=[quarter])))

    def test_chart_data_is_inert_and_runtime_is_only_bundled_when_needed(self):
        deck = dict(copy.deepcopy(self.reading), slides=[copy.deepcopy(self.reading['slides'][1])])
        chart = deck['slides'][0]['blocks'][0]
        chart['categories'][0] = '</script><script>window.injected=true</script>'
        self.provide(deck['slides'])
        html = self.render(deck)
        self.assertNotIn('<script>window.injected=true</script>', html)
        doc = Document(html)
        config = json.loads(doc.scripts[0])
        self.assertEqual(config['categories'][0], chart['categories'][0])
        self.assertIn('echarts', doc.scripts[-1])
        self.assertIn('Apache License', html)
        self.provide(self.saas['slides'])
        self.assertNotIn('window.slideCharts={refresh}', self.render(self.saas))

    def test_reading_capacity_increases_without_changing_speech_limits(self):
        deck = all_layouts_deck('saas-3d')
        variants = {s['layout']: copy.deepcopy(s) for s in deck['slides']}
        variants['split']['items'] *= 3  # six explanation items
        variants['table']['rows'] *= 10
        variants['flow']['steps'] *= 2
        variants['flow']['groups'] = [copy.deepcopy(g) for g in variants['flow']['groups'] * 2]
        for group in variants['flow']['groups']:
            group['rows'] = group['rows'] * 4
        for layout in ('split', 'table', 'flow'):
            sample = dict(deck, slides=[variants[layout]])
            data, root = load_deck(write_deck(self.root, sample))
            self.assertTrue(check_plan(data, root)['ok'], layout)
            sample['presentation_mode'] = 'speech'
            data, root = load_deck(write_deck(self.root, sample))
            self.assertFalse(check_plan(data, root)['ok'], layout)

    def test_reading_rejects_unstructured_filler_and_invalid_visual_data(self):
        cases = [
            lambda s: s.update(summary=''),
            lambda s: s.update(blocks=[s['blocks'][1], copy.deepcopy(s['blocks'][1])]),
            lambda s: s['blocks'][0].update(type=['matrix']),
            lambda s: s['blocks'][0]['rows'].append(['列数不一致']),
            lambda s: s['blocks'][1]['rows'].append('无结构正文'),
        ]
        for mutate in cases:
            deck = copy.deepcopy(self.reading)
            sample = copy.deepcopy(deck['slides'][5])
            sample['composition'] = 'half_lr'
            sample['blocks'] = sample['blocks'][1:]  # stable matrix + facts fixture
            deck['slides'] = [sample]
            mutate(deck['slides'][0])
            result = self.cli('build_deck.py', write_deck(self.root, deck), '--check-plan')
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr + result.stdout)

    def test_all_shared_layouts_render_in_installed_styles(self):
        from style_packs import discover_styles
        documents = {}
        for style in (item['id'] for item in discover_styles()['styles']):
            with self.subTest(style=style):
                deck = all_layouts_deck(style)
                self.assertEqual({slide['layout'] for slide in deck['slides']}, LAYOUTS)
                self.provide(deck['slides'])
                data, root = load_deck(write_deck(self.root, deck))
                report = check_plan(data, root)
                self.assertTrue(report['ok'], report['errors'])
                doc = documents[style] = Document(self.render(deck))
                self.assertEqual(len(doc.pages), len(LAYOUTS))
                self.assertEqual(doc.body['data-style'], style)
                self.assertNotIn('data-restyle', doc.body)
                for layout in LAYOUTS:
                    self.assertIn('layout-' + layout, doc.pages['test-' + layout]['class'].split())
                self.assertEqual(len(doc.images), len(LAYOUTS))
                self.assertTrue(all(image['src'].startswith('data:image/png;base64,') for image in doc.images))
                self.assertGreater(doc.editable, len(LAYOUTS))
        legacy, saas = documents['scene-white'], documents['saas-3d']
        self.assertEqual(legacy.scripts, saas.scripts, 'both themes must retain the same offline player')
        self.assertEqual(legacy.editable, saas.editable)
        self.assertNotEqual(legacy.styles, saas.styles)
        # These are the approved palette values, not a CSS implementation snapshot.
        css = '\n'.join(saas.styles).upper()
        for color in ('#F7F6F2', '#1D3446', '#477F80', '#BC9B59'):
            self.assertIn(color, css)
        for style, doc in documents.items():
            self.assertEqual(legacy.scripts, doc.scripts, style)
            self.assertEqual(legacy.editable, doc.editable, style)
        if 'real-miniature' in documents:
            css = '\n'.join(documents['real-miniature'].styles)
            for color in ('#EEEDE8', '#26313A', '#55748A', '#798469', '#B88A43'):
                self.assertIn(color, css)
            self.assertNotIn('--saas-', css, 'new theme must not load the glass theme')

    def test_style_does_not_bypass_protected_project_css(self):
        self.provide(self.saas['slides'])
        (self.root / 'project.css').write_text('header { color: #ff0000; }', encoding='utf-8')
        self.saas['custom_css'] = 'project.css'
        result = self.cli('build_deck.py', write_deck(self.root, self.saas), '--out', self.root / 'out.html', '--embed-format', 'keep')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('custom_css', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse((self.root / 'out.html').exists())

    def test_omitted_ui_text_uses_the_selected_styles_default(self):
        for source, style, default_mode in ((self.legacy, 'scene-white', 'none'),
                                             (self.saas, 'saas-3d', 'demo')):
            with self.subTest(style=style):
                implicit_deck = copy.deepcopy(source)
                implicit_deck['style'] = style
                for slide in implicit_deck['slides']:
                    slide['image'].pop('ui_text', None)
                implicit = quiet_prepare(write_deck(self.root, implicit_deck), self.root / f'{style}-default')
                self.assertEqual([image['ui_text'] for image in implicit['images']],
                                 [default_mode] * len(implicit_deck['slides']))
                explicit_deck = copy.deepcopy(implicit_deck)
                for slide in explicit_deck['slides']:
                    slide['image']['ui_text'] = default_mode
                explicit = quiet_prepare(write_deck(self.root, explicit_deck), self.root / f'{style}-explicit')
                self.assertEqual(implicit, explicit, 'omitted mode must export the same policy as the style default')
                if style == 'saas-3d':
                    for image in implicit['images']:
                        for label in ('"Overview"', '"Analytics"', '"Activity"', '"Demo"'):
                            self.assertIn(label, image['prompt'])

    def test_invalid_styles_and_text_modes_fail_cleanly(self):
        cases = []
        for value in ('unknown-style', '../white-blue-slides', None, ['saas-3d']):
            cases.append(('style', lambda deck, value=value: deck.update(style=value)))
        for value in ('arbitrary', None, ['demo']):
            cases.append(('ui_text', lambda deck, value=value: deck['slides'][0]['image'].update(ui_text=value)))
        cases.extend([
            ('style', lambda deck: deck['slides'][0].update(style='scene-white')),
            ('style', lambda deck: deck['slides'][0]['image'].update(style='scene-white')),
            ('ui_text', lambda deck: (deck.update(style='scene-white'),
                                     deck['slides'][0]['image'].update(ui_text='demo'))),
        ])
        for field, mutate in cases:
            deck = copy.deepcopy(self.saas)
            mutate(deck)
            path = write_deck(self.root, deck)
            for script, args in (('build_deck.py', ('--check-plan',)),
                                 ('prepare_images.py', ('--out', self.root / 'invalid-prompts'))):
                with self.subTest(field=field, value=deck.get('style'), script=script):
                    result = self.cli(script, path, *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(field, result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
        self.assertFalse((self.root / 'invalid-prompts/image-manifest.json').exists())

    def test_prompt_reference_and_ui_policies_are_independent(self):
        # Exercise both special composition paths with both text policies.
        for layout in ('journey', 'architecture'):
            exported = {}
            for mode in ('none', 'demo'):
                deck = copy.deepcopy(self.saas)
                deck['slides'] = [deck['slides'][0]]
                slide = deck['slides'][0]
                slide['layout'] = layout
                slide['image']['ui_text'] = mode
                out = self.root / f'{layout}-{mode}'
                manifest = quiet_prepare(write_deck(self.root, deck), out)
                exported[mode] = prompt = manifest['images'][0]['prompt']
                self.assertEqual(manifest['style'], 'saas-3d')
                self.assertEqual(manifest['images'][0]['ui_text'], mode)
                reference = out / manifest['style_reference']
                self.assertEqual(reference.read_bytes(), (SAAS / 'assets/reference-design/approved-product-overview.png').read_bytes())
                self.assertIn(manifest['style_reference'], (out / '配图提示词.md').read_text(encoding='utf-8'))
                for concept in ('navy', 'glass', 'gold', 'miniature'):
                    self.assertIn(concept, prompt.lower())
                # Reject inherited legacy bans that directly contradict this material palette.
                for conflict in ('no neon, glass', 'only accent is soft sky blue', 'strictly no text:'):
                    self.assertNotIn(conflict, prompt.lower())
                self.assertIn(slide['image']['brief']['subject'], prompt)
            self.assertNotEqual(exported['none'], exported['demo'])
            for label in ('"Overview"', '"Analytics"', '"Activity"', '"Demo"'):
                self.assertIn(label, exported['demo'])
                self.assertNotIn(label, exported['none'])
            self.assertIn('letters and numbers', exported['none'])
            self.assertNotIn('no letters', exported['demo'].lower())

    def test_missing_assets_resume_without_regeneration(self):
        path = write_deck(self.root, self.saas)
        first = quiet_prepare(path, self.root / 'handoff')
        self.assertTrue(all(image['status'] == 'missing' for image in first['images']))
        with self.assertRaises((ValueError, OSError)):
            self.render(copy.deepcopy(self.saas))
        draft = Document(self.render(copy.deepcopy(self.saas), draft=True))
        self.assertIn('draft', draft.body.get('class', '').split())
        self.assertEqual(draft.images, [])

        self.provide(self.saas['slides'][:1])
        source = self.root / self.saas['slides'][0]['image']['src']
        original = source.read_bytes()
        self.saas['slides'][0]['image'].pop('brief')
        partial = quiet_prepare(write_deck(self.root, self.saas), self.root / 'handoff')
        self.assertEqual([image['status'] for image in partial['images']], ['provided', 'missing', 'missing'])
        self.assertIsNone(partial['images'][0]['prompt'])
        self.assertEqual(partial['images'][1:], first['images'][1:])
        self.assertEqual(source.read_bytes(), original)

        self.provide(self.saas['slides'][1:])
        complete = quiet_prepare(write_deck(self.root, self.saas), self.root / 'handoff')
        self.assertTrue(all(image['status'] == 'provided' for image in complete['images']))
        self.assertEqual(source.read_bytes(), original)
        doc = Document(self.render(copy.deepcopy(self.saas)))
        self.assertNotIn('draft', doc.body.get('class', '').split())
        self.assertEqual(len(doc.images), len(self.saas['slides']))
        self.assertEqual(doc.body['data-style'], 'saas-3d')

    def test_scene_only_install_works_and_missing_saas_errors_clearly(self):
        installed = self.root / 'installed/white-blue-slides'
        shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns('__pycache__', 'reference-design'))
        scripts = installed / 'scripts'
        self.legacy.pop('style', None)
        self.provide(self.legacy['slides'])
        path = write_deck(self.root, self.legacy)
        result = self.cli('build_deck.py', path, '--out', self.root / 'standalone.html', '--embed-format', 'keep', scripts=scripts)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Document((self.root / 'standalone.html').read_text(encoding='utf-8')).body['data-style'], 'scene-white')
        result = self.cli('prepare_images.py', path, '--out', self.root / 'standalone-prompts', scripts=scripts)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads((self.root / 'standalone-prompts/image-manifest.json').read_text(encoding='utf-8'))['style_reference'])

        path = write_deck(self.root, self.saas)
        for script, args in (('build_deck.py', ('--check-plan',)),
                             ('prepare_images.py', ('--out', self.root / 'unavailable'))):
            with self.subTest(script=script):
                result = self.cli(script, path, *args, scripts=scripts)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertIn('saas-3d', result.stderr)
                self.assertIn('white-blue-slides', result.stderr)
                self.assertIn('skills', result.stderr)


@unittest.skipUnless((MINIATURE / 'assets/style.json').is_file(), 'optional sibling realistic-miniature-slides is not installed')
class MiniatureStyleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='miniature-style-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_examples_export_distinct_text_free_briefs_and_own_reference(self):
        for filename, mode in [('deck.example.json', 'speech'), ('deck.reading.example.json', 'reading')]:
            with self.subTest(mode=mode):
                deck = json.loads((MINIATURE / 'assets' / filename).read_text(encoding='utf-8'))
                path = write_deck(self.root, deck)
                data, root = load_deck(path)
                plan = check_plan(data, root)
                self.assertTrue(plan['ok'], plan['errors'])
                self.assertEqual(plan['presentation_mode'], mode)
                out = self.root / mode
                manifest = quiet_prepare(path, out)
                self.assertEqual(manifest['style'], 'real-miniature')
                self.assertEqual((out / manifest['style_reference']).read_bytes(),
                                 (MINIATURE / 'assets/reference-design/approved-workflow.png').read_bytes())
                for entry in manifest['images']:
                    self.assertEqual(entry['status'], 'missing')
                    self.assertEqual(entry['ui_text'], 'none')
                    self.assertIn('35–45', entry['prompt'])
                    self.assertIn('PBR', entry['prompt'])
                    self.assertIn('expressive faces', entry['prompt'])
                    self.assertIn('no letters or numbers', entry['prompt'])
                    self.assertNotIn('"Overview"', entry['prompt'])
                # Omitted UI mode must be exactly equivalent to explicit none.
                for slide in deck['slides']:
                    for im in slide_images(slide):
                        im.pop('ui_text')
                implicit = quiet_prepare(write_deck(self.root, deck), self.root / (mode + '-implicit'))
                self.assertEqual(manifest, implicit)
                if mode == 'reading':
                    self.assertEqual({s['composition'] for s in deck['slides'] if s['layout'] == 'reading'},
                                     {'half_lr', 'half_tb', 'half_diagonal', 'quarter'})

    def test_unsupported_raster_labels_fail_before_output(self):
        deck = json.loads((MINIATURE / 'assets/deck.example.json').read_text(encoding='utf-8'))
        deck['slides'][0]['image']['ui_text'] = 'demo'
        with self.assertRaisesRegex(ValueError, 'image.ui_text 可选 none'):
            quiet_prepare(write_deck(self.root, deck), self.root / 'invalid')
        self.assertFalse((self.root / 'invalid').exists())

    def test_all_layouts_and_special_image_hints_use_independent_style(self):
        deck = all_layouts_deck('real-miniature')
        image = self.root / 'images/existing.png'
        image.parent.mkdir(parents=True)
        shutil.copyfile(ASSETS / 'logo.png', image)
        data, root = load_deck(write_deck(self.root, deck))
        self.assertTrue(check_plan(data, root)['ok'])
        document = Document(Builder(data, root, embed_format='keep').render())
        self.assertEqual(document.body['data-style'], 'real-miniature')
        self.assertEqual(len(document.pages), len(LAYOUTS))
        self.assertNotIn('--saas-', '\n'.join(document.styles))
        example = json.loads((MINIATURE / 'assets/deck.example.json').read_text(encoding='utf-8'))
        example['slides'] = example['slides'][:1]
        for layout, expected in [('journey', 'Display above editable captions'),
                                 ('architecture', 'exact architecture tiers')]:
            example['slides'][0]['layout'] = layout
            manifest = quiet_prepare(write_deck(self.root, example), self.root / layout)
            self.assertIn(expected, manifest['images'][0]['prompt'])


def run():
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (StyleRegressionTests, MiniatureStyleTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run())
