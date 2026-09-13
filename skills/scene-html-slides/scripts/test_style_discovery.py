#!/usr/bin/env python3
"""Verify adding a style without modifying the registry or requiring SaaS."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from build_deck import Builder, check_plan
from common import ASSETS, load_deck
from style_packs import discover_styles, resolve_style
from test_styles import Document, quiet_prepare, write_deck


class StyleDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='slide-discovery-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.skills = self.root / 'skills'
        self.skills.mkdir()
        self.patch = patch('style_packs.SKILLS', self.skills)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def make_pack(self, folder='third-slides', **overrides):
        root = self.skills / folder
        assets = root / 'assets'
        assets.mkdir(parents=True)
        source = json.loads((ASSETS / 'style.json').read_text())
        source.update(id='third-style', name='Third independent style',
                      description='Test a third package with its own resources.',
                      css='theme.css', image_reference='reference.png', layout_hints={},
                      ui_text_modes=['none'], default_ui_text='none',
                      ui_text_prompts={'none': 'Third style policy: no raster text.'})
        source.update(overrides)
        for file in ('SKILL.md', 'references/design-system.md', 'references/image-workflow.md', 'references/quality-check.md'):
            target = root / file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('# Test style fixture\n')
        (assets / 'theme.css').write_text(':root{--third-style-token:#604C70;--ink:#604C70}')
        (assets / 'image-style.txt').write_text('THIRD_STYLE_VISUAL: precise monochrome miniature.')
        shutil.copyfile(ASSETS / 'logo.png', assets / 'reference.png')
        self.save(root, source)
        return root, source

    def save(self, root, source):
        (root / 'assets/style.json').write_text(json.dumps(source))

    def test_third_style_discovered_and_used_in_both_modes(self):
        root, source = self.make_pack()
        # Another installed style must not leak into the selected output.
        self.make_pack('other-slides', id='other-style', name='Other style')
        (self.skills / 'other-slides/assets/theme.css').write_text(':root{--other-style-token:red}')
        (self.skills / 'other-slides/assets/image-style.txt').write_text('OTHER_STYLE_VISUAL')
        inventory = discover_styles()
        self.assertEqual(inventory['errors'], [])
        entry = next(p for p in inventory['styles'] if p['id'] == 'third-style')
        self.assertEqual(Path(entry['skill_file']), root / 'SKILL.md')
        self.assertEqual(entry['presentation_modes'], ['speech', 'reading'])
        base = json.loads((ASSETS / 'deck.example.json').read_text())
        base['slides'] = [base['slides'][0]]
        for mode in ('speech', 'reading'):
            with self.subTest(mode=mode):
                project = self.root / mode
                project.mkdir()
                deck = copy.deepcopy(base)
                deck.update(style='third-style', presentation_mode=mode)
                if mode == 'reading':
                    # Exercise an actual dense layout, not just a mode flag.
                    slide = deck['slides'][0]
                    slide.update(layout='reading', composition='half_lr', summary='完整理解本页业务关系。',
                                 visual={'role': 'explanation', 'treatment': 'open', 'rationale': '流程和条件互补。', 'requirements': []},
                                 blocks=[{'type': 'process', 'title': '处理过程', 'icon': 'Workflow',
                                          'steps': [{'title': '接收', 'text': '根据资料确认输入。', 'icon': 'Inbox'},
                                                    {'title': '处理', 'text': '关联业务对象。', 'icon': 'Workflow'},
                                                    {'title': '完成', 'text': '保留处理记录。', 'icon': 'CircleCheck'}]}])
                path = write_deck(project, deck)
                data, work = load_deck(path)
                plan = check_plan(data, work)
                self.assertTrue(plan['ok'], plan['errors'])
                self.assertEqual(plan['style'], 'third-style')
                manifest = quiet_prepare(path, project / 'handoff')
                self.assertEqual(manifest['style'], 'third-style')
                self.assertEqual(manifest['presentation_mode'], mode)
                prompt = manifest['images'][0]['prompt']
                self.assertIn('THIRD_STYLE_VISUAL', prompt)
                self.assertIn(source['ui_text_prompts']['none'], prompt)
                self.assertNotIn('OTHER_STYLE_VISUAL', prompt)
                self.assertEqual((project / 'handoff' / manifest['style_reference']).read_bytes(),
                                 (root / 'assets/reference.png').read_bytes())
                image = project / deck['slides'][0]['image']['src']
                image.parent.mkdir(parents=True)
                shutil.copyfile(ASSETS / 'logo.png', image)
                doc = Document(Builder(data, work, embed_format='keep').render())
                self.assertEqual(doc.body['data-style'], 'third-style')
                self.assertEqual(doc.body['data-presentation-mode'], mode)
                self.assertIn('--third-style-token', '\n'.join(doc.styles))
                self.assertNotIn('--other-style-token', '\n'.join(doc.styles))
                self.assertGreater(doc.editable, 0)
                self.assertEqual(json.loads(doc.body['data-style-contract']), source['audit'])

    def test_draft_is_inspectable_but_cannot_build(self):
        self.make_pack(status='draft')
        self.assertEqual(discover_styles(), {'styles': [], 'errors': []})
        detailed = discover_styles(include_drafts=True)
        self.assertEqual(detailed['errors'], [])
        self.assertEqual(detailed['styles'][0]['status'], 'draft')
        with self.assertRaisesRegex(ValueError, 'draft'):
            resolve_style({'style': 'third-style'})

    def test_duplicates_are_rejected_without_first_match_fallback(self):
        self.make_pack()
        self.make_pack('duplicate-slides')
        self.assertEqual(discover_styles()['styles'], [])
        self.assertTrue(discover_styles()['errors'])
        with self.assertRaisesRegex(ValueError, '重复'):
            resolve_style({'style': 'third-style'})

    def test_invalid_package_does_not_disable_another_valid_style(self):
        self.make_pack()
        invalid, source = self.make_pack('broken-slides', id='broken')
        for update in ({'css': 'missing.css'}, {'image_prompt': '../../third-slides/assets/image-style.txt'},
                       {'default_ui_text': 'unavailable'}, {'audit': {}}):
            with self.subTest(update=update):
                self.save(invalid, dict(source, **update))
                listing = discover_styles()
                self.assertEqual([s['id'] for s in listing['styles']], ['third-style'])
                self.assertTrue(listing['errors'])
                self.assertEqual(resolve_style({'style': 'third-style'})['id'], 'third-style')
                with self.assertRaises(ValueError):
                    resolve_style({'style': 'broken'})

    def test_missing_instructions_and_unknown_id_fail(self):
        root, _ = self.make_pack()
        (root / 'references/design-system.md').unlink()
        with self.assertRaisesRegex(ValueError, 'design-system'):
            resolve_style({'style': 'third-style'})
        with self.assertRaisesRegex(ValueError, 'unknown-style'):
            resolve_style({'style': 'unknown-style'})

    def test_unrelated_manifest_is_not_a_slide_style(self):
        self.make_pack()
        other = self.skills / 'unrelated/assets'
        other.mkdir(parents=True)
        (other / 'style.json').write_text('{"id":"third-style","schema":"another-app/v1"}')
        listing = discover_styles()
        self.assertEqual(listing['errors'], [])
        self.assertEqual(len(listing['styles']), 1)


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StyleDiscoveryTests))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(run())
