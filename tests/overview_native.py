"""Focused Blender overview visibility/metadata regression. Does not render.

blender --background --factory-startup --python-exit-code 1 --python tests/overview_native.py
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
import bpy
from core import save
from catalog import demo,compile_scene
from blender_sync import run,render_visibility,signature

checks=[]
with tempfile.TemporaryDirectory(prefix='room-studio-overview-') as directory:
    project=Path(directory);path=project/'house.scene.json';out=project/'master.blend'
    scene=demo();entities=scene['entities']
    selected={next(e['id'] for e in entities.values() if e['kind']=='wall' and e['visible']),
              next(e['id'] for e in entities.values() if e['kind']=='floorplan' and not e.get('ceiling')),
              next(e['id'] for e in entities.values() if e.get('ceiling')),
              next(e['id'] for e in entities.values() if e['kind']=='window'),
              next(e['id'] for e in entities.values() if e['kind']=='landscape'),
              next(e['id'] for e in entities.values() if e['kind']=='cove'),
              next(e['id'] for e in entities.values() if e['kind']=='sofa')}
    scene['entities']={eid:e for eid,e in entities.items() if eid in selected}
    rooms={e['room'] for e in scene['entities'].values()}
    scene['rooms']={rid:r for rid,r in scene['rooms'].items() if rid in rooms}
    save(path,scene);compiled=compile_scene(scene)
    args=argparse.Namespace(scene=str(path),out=str(out),render=None,room='overview',samples=1,resolution=64)
    run(args)
    # Simulate a saved master whose reused meshes lack the two newer tags.
    for obj in bpy.data.objects:
        if obj.get('rs_id'):
            obj['qa_mesh_identity']=obj.data.name
            for key in ('rs_architecture','rs_facade'):
                if key in obj:del obj[key]
    bpy.ops.wm.save_as_mainfile(filepath=str(out));run(args)
    report=json.loads(out.with_suffix('.validation.json').read_text())
    assert report['updated_parts']==[]
    for p in compiled:
        obj=bpy.data.objects[p['id']]
        assert obj['qa_mesh_identity']==obj.data.name
        assert obj['rs_architecture']==bool(p.get('architecture'))
        assert obj['rs_facade']==bool(p.get('facade'))
    checks.append('fingerprint-reused meshes gain architecture/facade metadata without geometry rebuild')
    snapshot=lambda:{o['rs_id']:(tuple(o.location),tuple(o.scale),o.hide_render) for o in bpy.data.objects if o.get('rs_id')}
    full=snapshot();master_bytes=out.read_bytes()
    with render_visibility('overview',compiled):
        counts={'low_architecture':0,'hidden_facade':0,'hidden_outside':0,'hidden_ceiling':0,'hidden_other_structure':0}
        for p in compiled:
            obj=bpy.data.objects[p['id']]
            if p.get('architecture'):
                assert abs(obj.scale.z-.13)<1e-6 and abs(obj.location.z-p['position'][2]*.13)<1e-6
                assert not obj.hide_render
                counts['low_architecture']+=1
            if p.get('facade'):assert obj.hide_render;counts['hidden_facade']+=1
            if p.get('outside'):assert obj.hide_render;counts['hidden_outside']+=1
            if p.get('ceiling'):assert obj.hide_render;counts['hidden_ceiling']+=1
            if p.get('structural') and not p.get('architecture'):
                assert obj.hide_render;counts['hidden_other_structure']+=1
        assert all(counts.values()),counts
    assert snapshot()==full and out.read_bytes()==master_bytes
    checks.append('overview shows 13 percent architecture with scaled local height; hides facade/outside/ceiling/other structure; restores all transforms and visibility afterward')
    try:
        with render_visibility('overview',compiled):raise RuntimeError('Injected render failure')
    except RuntimeError:pass
    assert snapshot()==full and out.read_bytes()==master_bytes
    with render_visibility(next(iter(scene['rooms'])),compiled):assert snapshot()==full
    checks.append('failed overview render restores state; individual room views remain unchanged')
    bpy.ops.wm.open_mainfile(filepath=str(out));assert snapshot()==full
    for obj in bpy.data.objects:
        if obj.get('rs_id'):assert signature(obj)==obj['rs_signature']
    checks.append('saved master reopens with full-height architecture, original visibility, upgraded metadata and valid signatures')
    assert not list(project.glob('*.png'))
    result={'status':'PASS','blender':bpy.app.version_string,'checks':checks,'overview_counts':counts,
            'scope':'Actual Blender visibility/context, metadata migration and saved-master reopening; no image rendered. Final overview visual QA remains with orchestrator.'}
    evidence=(ROOT if (ROOT/'docs').is_dir() else ROOT.parent)/'docs/qa';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'task-b-overview-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('OVERVIEW_NATIVE_PASS '+json.dumps(result),flush=True)
