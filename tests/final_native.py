"""Full generated case: native export, local edit preservation, GLB round trip.

Run explicitly in Blender. No image rendering.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/room-studio/scripts'))
import bpy
from catalog import demo, compile_scene
from core import apply, save, travel, content
from blender_sync import run

started = time.perf_counter()
with tempfile.TemporaryDirectory(prefix='room-studio-full-native-') as directory:
    directory = Path(directory)
    scene = demo()
    path = directory / 'scene.json'
    out = directory / 'master.blend'
    save(path, scene)
    args = argparse.Namespace(scene=str(path), out=str(out), render=None,
                              room='living', samples=1, resolution=64)
    run(args)
    compiled = compile_scene(scene)
    expected_meshes = sum(p['shape'] != 'light' for p in compiled)
    assert len([o for o in bpy.data.objects if o.type == 'MESH']) == expected_meshes
    assert len([o for o in bpy.data.objects if o.get('rs_root_entity')]) == len(scene['entities'])
    bpy.context.view_layer.update()
    def snapshot():
        return {o['rs_id']: {'matrix': [list(row) for row in o.matrix_world],
                              'fingerprint': o['rs_fingerprint']}
                for o in bpy.data.objects if o.get('rs_id')}
    before = snapshot()
    sofa = scene['entities']['living.sofa']
    picture = scene['entities']['living.picture']
    changed, report = apply(scene, {'expected_revision': scene['revision'],
        'protect': ['kitchen.island'], 'ops': [
            {'op': 'set', 'target': sofa['id'],
             'position': [sofa['position'][0] + .1, *sofa['position'][1:]]},
            {'op': 'set', 'target': picture['id'],
             'position': [*picture['position'][:2], picture['position'][2] + .05]}]})
    assert set(report['changed']) == {sofa['id'], picture['id']}
    save(path, changed)
    run(args)
    bpy.context.view_layer.update()
    after = snapshot()
    protected = [key for key in before if key.split('/')[0] not in report['changed']]
    assert all(before[key] == after[key] for key in protected)
    undone, _ = travel(changed)
    assert content(undone) == content(scene)
    save(path, undone)
    run(args)
    bpy.context.view_layer.update()
    assert snapshot() == before
    bpy.ops.wm.open_mainfile(filepath=str(out))
    assert len([o for o in bpy.data.objects if o.type == 'MESH']) == expected_meshes
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(out.with_suffix('.glb')))
    imported = len([o for o in bpy.data.objects if o.type == 'MESH'])
    assert imported == expected_meshes
    assert not list(directory.glob('*.png'))
    result = {'status': 'PASS', 'case': 'fresh final Manhattan demo',
              'rooms': len(scene['rooms']), 'entities': len(scene['entities']),
              'compiled_parts': len(compiled), 'native_meshes': expected_meshes,
              'glb_reimport_meshes': imported, 'protected_parts': len(protected),
              'seconds': round(time.perf_counter() - started, 3),
              'checks': ['full case export', 'two local edits preserve all other part matrices and fingerprints',
                         'undo restores full geometry', 'native save and reopen',
                         'GLB reimport mesh count', 'no image render during edits']}
    evidence = ROOT / 'docs/qa'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'final-native-results.json').write_text(json.dumps(result, indent=2))
    print('FINAL_NATIVE_PASS ' + json.dumps(result), flush=True)
