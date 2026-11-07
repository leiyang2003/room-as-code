"""Sample registries are explicit allowlists, with existing single-scene behavior."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
from server import sample_registry

class SampleRegistryTests(unittest.TestCase):
    def test_both_examples_resolve_relative_to_manifest(self):
        default,samples=sample_registry(None,ROOT/'examples/samples.json')
        self.assertEqual(default,'japanese')
        self.assertEqual(set(samples),{'manhattan','japanese'})
        self.assertTrue(all(v['path'].is_file() for v in samples.values()))

    def test_single_scene_remains_available(self):
        path=ROOT/'examples/manhattan.scene.json'
        default,samples=sample_registry(path)
        self.assertEqual(default,'default');self.assertEqual(samples[default]['path'],path)

    def test_duplicate_ids_and_missing_default_are_rejected(self):
        scene=str(ROOT/'examples/manhattan.scene.json')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'samples.json'
            item={'id':'one','label':'One','scene':scene}
            for config in ({'default':'one','samples':[item,item]},
                           {'default':'missing','samples':[item]}):
                p.write_text(json.dumps(config))
                with self.assertRaises(ValueError):sample_registry(None,p)
