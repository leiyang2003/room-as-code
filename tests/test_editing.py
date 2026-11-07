"""Behavior checks against the retained historical fixture, independent of new layouts."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import socket
import time
from urllib.request import urlopen,Request
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/room-studio/scripts'
sys.path.insert(0, str(SCRIPTS))
from core import apply, content, load, save
from catalog import compile_scene, demo
from render_state import record_render, render_status, manifest_path
from room import export_paths
from framing import room_camera,overview_camera


class EditingTests(unittest.TestCase):
    def setUp(self):
        fixture=ROOT/'examples/quiet-house.scene.json'
        self.scene = load(fixture if fixture.exists() else ROOT/'examples/kit-grid.scene.json')
        self.scene['entities']['living.sofa']['overrides']['fabric'] = '#778899'

    def patch(self, **extra):
        sofa = self.scene['entities']['living.sofa']
        picture = self.scene['entities']['living.picture']
        return {'expected_revision': self.scene['revision'],
                'label': 'Move furniture and attached decoration',
                'protect': ['dining.table', 'kitchen.island'],
                'ops': [{'op': 'set', 'target': sofa['id'],
                         'position': [sofa['position'][0] + .3, *sofa['position'][1:]],
                         'rotation': sofa['rotation'] + 15},
                        {'op': 'set', 'target': picture['id'],
                         'position': [*picture['position'][:2], picture['position'][2] + .15]}],
                **extra}

    def test_move_preserves_unrelated_entities_and_local_primitives(self):
        out, result = apply(self.scene, self.patch())
        self.assertEqual(set(result['changed']), {'living.sofa', 'living.picture'})
        for eid, entity in self.scene['entities'].items():
            if eid not in result['changed']:
                self.assertEqual(out['entities'][eid], entity)
        self.assertEqual(out['entities']['living.sofa']['overrides'], {'fabric': '#778899'})
        self.assertEqual(out['entities']['living.picture']['rotation'], self.scene['entities']['living.picture']['rotation'])
        before={p['id']:p for p in compile_scene(self.scene)}
        after={p['id']:p for p in compile_scene(out)}
        self.assertEqual(before.keys(),after.keys())
        for key,p in after.items():
            if p['entity'] in result['changed']:
                self.assertEqual({k:v for k,v in p.items() if k not in ('parent_position','parent_rotation','fingerprint')},
                                 {k:v for k,v in before[key].items() if k not in ('parent_position','parent_rotation','fingerprint')})
            else:self.assertEqual(p,before[key])
        self.assertIn('position', result['changes']['living.picture'])
        self.assertIn('rotation', result['changes']['living.sofa'])

    def test_protection_rejects_effective_changes_atomically(self):
        before = copy.deepcopy(self.scene)
        for ops in ([{'op': 'set', 'target': 'dining.table', 'rotation': 15}],
                    [{'op': 'style', 'target': 'all', 'value': 'mono'}]):
            with self.assertRaisesRegex(ValueError, 'Protected entities'):
                apply(self.scene, self.patch(ops=ops))
            self.assertEqual(self.scene, before)

    def test_malformed_patch_rejects_unknown_and_wrong_types(self):
        for patch in (self.patch(protected=['dining.table']),
                      self.patch(protect=['missing']), self.patch(protect='living.sofa'),
                      self.patch(ops=[42]),
                      self.patch(ops=[{'op':'material','target':'living.sofa','role':'fabric'}]),
                      self.patch(ops=[{'op':'set','target':'living.sofa','params':[]}])):
            with self.assertRaises(ValueError):
                apply(self.scene, patch)

    def test_cli_persistence_undo_redo_dry_run_and_no_render(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'house.scene.json'
            patch = Path(d) / 'edit.json'
            save(path, self.scene)
            patch.write_text(json.dumps(self.patch()))
            def cli(*args):
                return json.loads(subprocess.check_output([sys.executable, str(SCRIPTS/'room.py'), *map(str,args)], text=True))
            cli('apply', path, patch, '--dry-run')
            self.assertEqual(load(path), self.scene)
            result = cli('apply', path, patch)
            edited = load(path)
            self.assertEqual(result['revision'], self.scene['revision'] + 1)
            self.assertEqual(cli('inspect', path)['entities'][0]['rotation'], next(iter(edited['entities'].values()))['rotation'])
            cli('undo', path)
            self.assertEqual(content(load(path)), content(self.scene))
            cli('redo', path)
            self.assertEqual(content(load(path)), content(edited))
            self.assertEqual(load(path)['revision'], self.scene['revision'] + 3)
            self.assertFalse(list(Path(d).glob('*.blend')) + list(Path(d).glob('*.png')))

    def test_inspect_distinguishes_wall_art_and_detail_decor_without_writes(self):
        scene=demo()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'house.scene.json';save(path,scene);before=path.read_bytes()
            output=json.loads(subprocess.check_output([sys.executable,str(SCRIPTS/'room.py'),'inspect',str(path)],text=True))
            self.assertEqual(path.read_bytes(),before)
            entities={e['id']:e for e in output['entities']}
            wall=next(e for e in scene['entities'].values() if e['kind']=='art' and 'detail' not in e)
            self.assertNotIn('detail',entities[wall['id']])
            for detail in ('table_setting','ceramic_vessel'):
                decor=next(e for e in scene['entities'].values() if e.get('detail')==detail)
                summary=entities[decor['id']]
                self.assertEqual(summary['kind'],wall['kind'])
                for key in ('detail','label','semantic_group','provenance'):
                    self.assertEqual(summary[key],decor[key])
                # Inspection exposes metadata without expanding the mutation protocol.
                for extra in ({'detail':'table_setting'},{'params':{'detail':'table_setting'}}):
                    with self.assertRaises(ValueError):
                        apply(scene,{'expected_revision':scene['revision'],'ops':[{'op':'set','target':decor['id'],**extra}]})
                position=list(decor['position']);position[2]+=.1
                moved,result=apply(scene,{'expected_revision':scene['revision'],'protect':[wall['id']],
                    'ops':[{'op':'set','target':decor['id'],'position':position}]})
                self.assertEqual(result['changed'],[decor['id']])
                self.assertEqual(moved['entities'][wall['id']],wall)
                self.assertEqual(moved['entities'][decor['id']],{**decor,'position':position})

    def test_render_status_content_image_corruption_missing(self):
        with tempfile.TemporaryDirectory() as d:
            image = Path(d)/'check.png'
            self.assertEqual(render_status(self.scene,image)['status'], 'MISSING')
            image.write_bytes(b'synthetic unit-test bytes, not a rendered image')
            self.assertEqual(render_status(self.scene,image)['reason'], 'provenance_missing')
            record_render(image,self.scene,room='living')
            self.assertEqual(render_status(self.scene,image)['status'], 'CURRENT')
            info=json.loads(manifest_path(image).read_text())
            info.pop('material_version');manifest_path(image).write_text(json.dumps(info))
            self.assertEqual(render_status(self.scene,image)['reason'], 'renderer_changed')
            record_render(image,self.scene,room='living')
            out,_=apply(self.scene,self.patch())
            self.assertEqual(render_status(out,image)['reason'], 'scene_changed')
            restored=copy.deepcopy(self.scene);restored['revision']+=2
            self.assertEqual(render_status(restored,image)['status'], 'CURRENT')
            image.write_bytes(b'replaced')
            self.assertEqual(render_status(self.scene,image)['reason'], 'image_changed')
            for invalid in ('{', '[]', '{}', '{"schema":"unsupported"}'):
                manifest_path(image).write_text(invalid)
                self.assertEqual(render_status(self.scene,image)['reason'], 'provenance_invalid')

    def test_export_paths_cannot_overwrite_scene_or_each_other(self):
        for scene,out,image in [('house.blend','house.blend',None),
                                ('house.json','master.blend','house.json'),
                                ('house.json','master.blend','master.glb'),
                                ('house.json','master.blend','master.validation.json'),
                                ('house.json','master.blend','check.render.json')]:
            with self.assertRaises(ValueError):export_paths(scene,out,image)
        export_paths('house.json','master.blend','living.png')

    def test_preview_reads_saved_moves_without_rendering(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'house.scene.json';save(path,self.scene)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            server=subprocess.Popen([sys.executable,str(SCRIPTS/'room.py'),'serve',str(path),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            url=f'http://127.0.0.1:{port}'
            try:
                def get():
                    with urlopen(url+'/api/scene',timeout=2) as response:return json.load(response)
                for attempt in range(50):
                    try:get();break
                    except OSError:
                        if server.poll() is not None:raise AssertionError('Preview exited')
                        time.sleep(.02)
                else:self.fail('Preview failed to start')
                request=Request(url+'/api/patch',data=json.dumps(self.patch()).encode(),headers={'Content-Type':'application/json'},method='POST')
                with urlopen(request,timeout=2) as response:result=json.load(response)
                latest=get()
                self.assertEqual(set(result['changed']),{'living.sofa','living.picture'})
                self.assertEqual(latest['scene'],load(path))
                for part in latest['parts']:
                    if part['entity']=='living.picture':self.assertEqual(part['parent_position'][2],1.75)
                self.assertFalse(list(Path(d).glob('*.blend'))+list(Path(d).glob('*.png')))
            finally:
                server.terminate();server.wait(timeout=5)

    def test_authored_cameras_and_outline_framing(self):
        scene=copy.deepcopy(self.scene)
        camera={'position':[3,-4,1.8],'target':[1,0,1]}
        scene['rooms']['living']['camera']=camera
        self.assertEqual(room_camera('living',scene['rooms']['living'])[:2],(camera['position'],camera['target']))
        scene['layout']={'outline':[[20,10],[40,10],[40,14],[20,14]]}
        position,target,lens=overview_camera(scene)
        self.assertEqual(target[:2],(30,12));self.assertGreater(position[2],target[2]);self.assertEqual(lens,42)
        scene['rooms']['living']['camera']['position']=camera['target']
        from core import validate
        with self.assertRaises(ValueError):validate(scene)


if __name__ == '__main__':
    unittest.main(verbosity=2)
