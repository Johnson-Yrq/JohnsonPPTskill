"""Regression cases for reading controls, architecture labels and stage fields."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest

from build_deck import Builder, check_plan
from common import ASSETS, load_deck
from prepare_images import prepare
from style_packs import paper_color


def example():
    image = {'src': 'image.png', 'alt': '验证用微缩场景', 'ratio': '3:1'}
    def slide(layout, **kw):
        return dict(id=layout, layout=layout, title='阅读布局验证', image=copy.deepcopy(image),
                    visual={'treatment': 'labels' if layout == 'architecture' else 'open',
                            'rationale': '核对结构化内容保留、字段边界和可编辑性', 'requirements': []}, **kw)
    point = lambda title: {'title': title, 'text': '核对依据', 'icon': 'Filter'}
    return {'version': 1, 'title': '排版回归', 'style': 'real-miniature', 'presentation_mode': 'reading', 'slides': [
        slide('flow', align_control_rows=True, steps=[point(t) for t in ['接入', '核查', '归档']], groups=[
            dict(point('分析前'), rows_layout='stacked', rows=[
                {'label': '校验要求', 'text': '来源与时间\n唯一标识', 'kind': 'check'},
                {'label': '缺数据', 'text': '补证后重新校验', 'kind': 'exception'}]),
            dict(point('执行前'), rows=[{'label': '核查至执行', 'text': '支持与反驳证据，资格和范围，以及参数与批准版本'}])]),
        slide('architecture', labels=[
            {'kind': 'layer', 'prefix': '01', 'text': '数据层', 'x': 20, 'y': 20, 'w': 300, 'h': 60, 'leader': 'right'},
            {'kind': 'flow', 'text': '向上供给', 'detail': '数据与语义', 'direction': 'up', 'x': 20, 'y': 100, 'w': 320, 'h': 100}]),
        slide('journey', connected=True, items=[{'title': title, 'icon': 'Map', 'period': period,
              'fields': [{'label': '交付', 'text': text}, {'label': '准入', 'text': '负责人确认'}]}
              for title, period, text in [('范围', 'M1', '对象清单'), ('演练', 'M2', '闭环记录'), ('交接', 'M3', '运行手册')]],
              bottom={'type': 'groups', 'items': [{'label': '数据线', 'text': '主数据映射'}, {'label': '规则线', 'text': '规则回测'}]})]}


class EditableText(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.stack = []; self.values = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in ('img', 'br', 'input', 'meta', 'link'): return
        self.stack.append('data-edit' in dict(attrs))

    def handle_endtag(self, tag):
        if self.stack: self.stack.pop()

    def handle_data(self, data):
        if any(self.stack): self.values.append(data)


class Refinements(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='slide-refinements-')
        self.root = Path(self.tmp.name)
        (self.root / 'image.png').write_bytes((ASSETS / 'logo.png').read_bytes())
        self.deck = example()

    def tearDown(self):
        self.tmp.cleanup()

    def test_structured_content_remains_editable(self):
        self.assertTrue(check_plan(self.deck, self.root)['ok'])
        text = EditableText(Builder(self.deck, self.root).render()).values
        for value in ['校验要求', '缺数据', '01', '数据层', '向上供给', '数据与语义', 'M1', '交付', '准入', '对象清单', '主数据映射']:
            self.assertIn(value, text)

    def test_legacy_rows_and_stages(self):
        stage = self.deck['slides'][2]['items'][0]
        stage.pop('fields'); stage.pop('period')
        stage.update(text='旧版正文', deliverable='旧版条件', state='进行中')
        self.deck['slides'][0]['groups'][0].pop('rows_layout')
        self.assertTrue(check_plan(self.deck, self.root)['ok'])
        text = EditableText(Builder(self.deck, self.root).render()).values
        for value in ['旧版正文', '旧版条件', '进行中']: self.assertIn(value, text)

    def test_invalid_fields_fail_before_render(self):
        mutations = [
            lambda d: d['slides'][2]['items'][0].update(text='不能被静默丢掉'),
            lambda d: d['slides'][2]['items'][0].update(fields=[]),
            lambda d: d['slides'][0]['groups'][0].update(rows_layout='unknown'),
            lambda d: d['slides'][0]['groups'][0]['rows'][0].update(kind='unknown'),
            lambda d: d['slides'][1]['labels'][0].update(prefix=1),
            lambda d: d['slides'][1]['labels'][0].update(direction='up'),
            lambda d: d['slides'][2]['bottom']['items'][0].update(text=''),
            lambda d: d['slides'][1]['image'].update(background_mode='guess')]
        for mutation in mutations:
            d = copy.deepcopy(self.deck); mutation(d)
            self.assertFalse(check_plan(d, self.root)['ok'])

    def test_style_paper_and_panorama_manifest(self):
        self.assertEqual(paper_color(self.deck), '#EEEDE8')
        self.assertEqual(paper_color(dict(self.deck, style='scene-white')), '#F7F6F2')
        self.deck['theme'] = {'paper': '#E8E7E0'}
        brief = {'subject': '一个完整的横向微缩工作场景，三个不同业务阶段分别由对应的人物和设备组成',
                 'action': '人物依次核对资料并将文件交给下一个岗位',
                 'structure': '三个阶段沿水平基座均匀展开，顺序与下方说明一致，完整保留路径和基座',
                 'details': '办公桌、文件和可信的小型设备支撑具体动作，人物姿态自然且没有任何文字'}
        self.deck['slides'] = [self.deck['slides'][2]]
        self.deck['slides'][0]['image']['brief'] = brief
        file = self.root / 'deck.json'; file.write_text(json.dumps(self.deck))
        manifest = prepare(file, self.root / 'handoff')
        self.assertEqual(manifest['paper'], '#E8E7E0')
        self.assertEqual(manifest['images'][0]['ratio'], '3:1')
        self.assertIn('RGB (232, 231, 224)', manifest['images'][0]['prompt'])
        self.deck['slides'][0]['image']['ratio'] = 'wrong'
        file.write_text(json.dumps(self.deck))
        with self.assertRaises(ValueError): load_deck(file)

    def test_background_diagnostics_preserve_unsafe_inputs(self):
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            self.skipTest("可选的 numpy/Pillow 未安装")
        from match_paper import process
        for name, array in [('transparent', np.zeros((64, 64, 4), dtype=np.uint8)),
                            ('wrong-matte', np.full((64, 64, 3), 190, dtype=np.uint8))]:
            path = self.root / (name + '.png'); Image.fromarray(array).save(path)
            before = path.read_bytes(); result = process(path, (238, 237, 232), 8, False)
            self.assertIn('skipped', result)
            self.assertEqual(before, path.read_bytes())
        self.assertTrue(process(self.root / 'transparent.png', (238, 237, 232), 8, True)['has_transparency'])


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Refinements))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(run())
