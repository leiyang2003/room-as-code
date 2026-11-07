"""Minimal actual Blender check for editing/render separation, not a final house render.

blender --background --factory-startup --python-exit-code 1 --python tests/editing_native.py
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
import bpy
from core import apply, content, load, save, travel
from blender_sync import run
from render_state import render_status, manifest_path

checks=[]
started=time.perf_counter()
with tempfile.TemporaryDirectory(prefix='room-studio-editing-native-') as directory:
    project=Path(directory);path=project/'house.scene.json';out=project/'master.blend';image=project/'check.png'
    fixture=ROOT/'examples/quiet-house.scene.json'
    scene=load(fixture if fixture.exists() else ROOT/'examples/kit-grid.scene.json')
    scene['rooms']={'living':scene['rooms']['living']}
    scene['rooms']['living']['camera']={'position':[4,-4,1.8],'target':[1.6,-1,.8]}
    scene['layout']={'outline':[[0,-5],[4,-5],[4,0],[0,0]]}
    keep={'living.sofa','living.picture','living.sheer','living.cove_back'}
    scene['entities']={eid:e for eid,e in scene['entities'].items() if eid in keep}
    scene['entities']['living.sofa']['overrides']['fabric']='#778899'
    floor=copy.deepcopy(scene['entities']['living.sofa'])
    floor.update(id='living.qa_floor',label='QA floor',kind='floorplan',position=[2,-2.5,-.1],rotation=0,
                 params={'points':[[-2,-2.5],[2,-2.5],[2,2.5],[-2,2.5]],'thickness':.1},overrides={})
    scene['entities'][floor['id']]=floor
    save(path,scene)
    args=argparse.Namespace(scene=str(path),out=str(out),render=None,room='living',samples=1,resolution=64)
    run(args)
    assert all(abs(a-b)<1e-5 for a,b in zip(bpy.data.objects['View_living'].location,scene['rooms']['living']['camera']['position']))
    from framing import overview_camera
    overview_position,_,_=overview_camera(scene)
    assert all(abs(a-b)<1e-5 for a,b in zip(bpy.data.objects['View_overview'].location,overview_position))
    checks.append('native room camera adopts authored position; overview uses layout outline framing')
    assert not image.exists() and not manifest_path(image).exists()
    floor_parts=[o for o in bpy.data.objects if o.get('rs_entity')==floor['id']]
    assert floor_parts and not any(m.type=='SOLIDIFY' for o in floor_parts for m in o.modifiers)
    fabric_parts=[o for o in bpy.data.objects if o.get('rs_entity')=='living.sheer' and o.type=='MESH']
    assert any(m.type=='SOLIDIFY' for o in fabric_parts for m in o.modifiers)
    checks.append('extruded floorplan has no fabric SOLIDIFY; curtain mesh retains thickness')
    def matrix_snapshot(o):return tuple(tuple(row) for row in o.matrix_world)
    protected={o['rs_id']:(matrix_snapshot(o),o['rs_fingerprint']) for o in bpy.data.objects if o.get('rs_entity') not in {'living.sofa','living.picture'} and o.get('rs_id')}
    sofa=scene['entities']['living.sofa'];picture=scene['entities']['living.picture']
    edited,result=apply(scene,{'expected_revision':scene['revision'],'label':'Native move check',
        'protect':['living.sheer','living.qa_floor','living.cove_back'],
        'ops':[{'op':'set','target':sofa['id'],'position':[sofa['position'][0]+.3,*sofa['position'][1:]],'rotation':15},
               {'op':'set','target':picture['id'],'position':[*picture['position'][:2],picture['position'][2]+.15]}]})
    save(path,edited);run(args)
    report=json.loads(out.with_suffix('.validation.json').read_text())
    assert report['updated_parts'] and all(p.split('/')[0] in result['changed'] for p in report['updated_parts'])
    assert report['unchanged_parts']
    for key,(matrix,fingerprint) in protected.items():
        obj=bpy.data.objects[key]
        assert matrix_snapshot(obj)==matrix and obj['rs_fingerprint']==fingerprint,key
    assert abs(bpy.data.objects['entity:living.sofa'].location.x-sofa['position'][0]-.3)<1e-5
    assert abs(bpy.data.objects['entity:living.picture'].location.z-picture['position'][2]-.15)<1e-5
    assert not image.exists()
    checks.append('furniture and fixed art transforms sync natively; unrelated matrices and primitives unchanged; no render')
    args.render=str(image);render_started=time.perf_counter();run(args);render_seconds=time.perf_counter()-render_started
    assert image.is_file() and manifest_path(image).is_file()
    assert render_status(edited,image)['status']=='CURRENT'
    checks.append('explicit low-resolution render writes real PNG and content-bound provenance; CURRENT')
    later,_=apply(edited,{'expected_revision':edited['revision'],'ops':[{'op':'set','target':'living.picture','position':[*picture['position'][:2],picture['position'][2]+.25]}]})
    save(path,later);assert render_status(load(path),image)['status']=='STALE'
    undone,_=travel(later);save(path,undone)
    assert content(undone)==content(edited) and render_status(undone,image)['status']=='CURRENT'
    checks.append('subsequent saved edit marks image STALE; undo to identical content restores CURRENT at newer revision')
    original=image.read_bytes();image.write_bytes(original+b'replaced')
    assert render_status(undone,image)['reason']=='image_changed';image.write_bytes(original)
    checks.append('changed image bytes rejected as STALE')
    # Reopen the editable master after temporary render cutaways.
    bpy.ops.wm.open_mainfile(filepath=str(out))
    assert all(not o.hide_render for o in bpy.data.objects if o.get('rs_entity')==floor['id'])
    checks.append('editable native master reopens with structural floor visibility preserved')
    evidence=(ROOT if (ROOT/'docs').is_dir() else ROOT.parent)/'docs/qa'
    evidence.mkdir(parents=True,exist_ok=True)
    shutil.copy2(image,evidence/'task-b-render-check.png')
    shutil.copy2(manifest_path(image),evidence/'task-b-render-check.render.json')
    save(evidence/'task-b-render-check.scene.json',edited)
    result={'status':'PASS','checks':checks,'blender':bpy.app.version_string,
            'render_resolution':[64,45],'samples':1,'render_step_seconds':round(render_seconds,3),
            'total_script_seconds':round(time.perf_counter()-started,3),
            'native_mesh_count':report['mesh_count'],
            'scope':'Minimal subset from historical example; verifies real native sync and rendering mechanism only, not final Manhattan layout or visual quality.'}
    (evidence/'task-b-native-render.json').write_text(json.dumps(result,indent=2)+'\n')
    print('EDITING_NATIVE_PASS '+json.dumps(result),flush=True)
