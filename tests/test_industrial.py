import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'skills/room-studio/scripts'))
from catalog import demo, compile_scene
from core import apply, travel, content, STYLES
from native_materials import recipe, material_id


class IndustrialStyleTests(unittest.TestCase):
    def test_theme_changes_surfaces_and_preserves_layout_overrides_and_undo(self):
        scene = demo()
        scene['entities']['living.sofa']['overrides']['fabric'] = '#556677'
        scene['rooms']['bedroom']['style'] = 'warm'
        before = copy.deepcopy(scene)
        edited, _ = apply(scene, {'expected_revision': scene['revision'], 'ops': [
            {'op': 'style', 'target': 'all', 'value': 'industrial'}]})
        self.assertEqual(edited['entities'], before['entities'])
        self.assertEqual(edited['rooms'], before['rooms'])
        parts = compile_scene(edited)
        island = [p for p in parts if p['entity'] == 'kitchen.island' and p['role'] == 'wood']
        self.assertTrue(island)
        self.assertTrue(all(recipe(p) == 'brushed_steel' for p in island))
        floor = next(p for p in parts if p['room'] == 'living' and p['role'] == 'floor')
        self.assertEqual(recipe(floor), 'concrete')
        self.assertTrue(all('surface' not in p for p in parts if p['room'] == 'bedroom'))
        fabrics = [p for p in parts if p['entity'] == 'living.sofa' and p['role'] == 'fabric']
        self.assertTrue(all(p['color'] == '#556677' and 'surface' not in p for p in fabrics))
        restored, _ = travel(edited)
        self.assertEqual(content(restored), content(before))

    def test_legacy_mono_loads_like_industrial_and_new_patch_uses_canonical_name(self):
        old = demo(); old['style'] = 'mono'
        new = copy.deepcopy(old); new['style'] = 'industrial'
        self.assertEqual(compile_scene(old), compile_scene(new))
        edited, _ = apply(demo(), {'expected_revision': 0, 'ops': [
            {'op': 'style', 'target': 'all', 'value': 'mono'}]})
        self.assertEqual(edited['style'], 'industrial')
        part = next(p for p in compile_scene(new) if p.get('surface') == 'brushed_steel')
        normal = {k: v for k, v in part.items() if k != 'surface'}
        self.assertNotEqual(material_id(part), material_id(normal))

    def test_protection_detects_surface_change_even_with_all_colors_overridden(self):
        scene = demo()
        scene['entities']['dining.table']['overrides'].update(STYLES['warm'])
        with self.assertRaises(ValueError):
            apply(scene, {'expected_revision': scene['revision'], 'protect': ['dining.table'],
                          'ops': [{'op': 'style', 'target': 'all', 'value': 'industrial'}]})


if __name__ == '__main__':
    unittest.main()
