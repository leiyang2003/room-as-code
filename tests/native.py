"""Execute with Blender's --python; runs against a temporary master copy."""
import argparse,hashlib,json,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/room-studio/scripts'))
import bpy
from core import load,save,apply
from blender_sync import run

root=Path(__file__).resolve().parents[1];checks=[]
with tempfile.TemporaryDirectory(prefix='room-studio-native-') as d:
    p=Path(d);scene=p/'scene.json';out=p/'master.blend'
    shutil.copy2(root/'examples/quiet-house.scene.json',scene)
    args=argparse.Namespace(scene=str(scene),out=str(out),room='living',render=None,samples=8,resolution=500)
    run(args);run(args);report=json.loads(out.with_suffix('.validation.json').read_text())
    assert not report['updated_parts'],report['updated_parts'];assert report['unchanged_parts'];checks.append('unchanged native master reopened and all managed primitives reused')
    s=load(scene);table=s['entities']['dining.table'].copy();changed,_=apply(s,{'expected_revision':s['revision'],'label':'native island regression','ops':[{'op':'set','target':'kitchen.island','params':{'w':1.2}}]});save(scene,changed)
    run(args);report=json.loads(out.with_suffix('.validation.json').read_text());assert report['updated_parts'];assert all(x.startswith('kitchen.island/') for x in report['updated_parts']);assert changed['entities']['dining.table']==table;checks.append('island width native sync only rebuilds island primitives and preserves table')
    assert bpy.data.objects['kitchen.island/basin_inner'].location.x==0;checks.append('native sink remains centered')
    stable=out.read_bytes()
    bpy.data.objects['dining.table/top'].data.vertices[0].co.x+=.12;bpy.ops.wm.save_as_mainfile(filepath=str(out));external=out.read_bytes()
    try:run(args)
    except RuntimeError as e:assert 'External edits' in str(e)
    else:raise AssertionError('External geometry edit was overwritten')
    assert out.read_bytes()==external;checks.append('external mesh edit conflict rejects sync without changing saved file')
    out.write_bytes(stable);bpy.ops.wm.open_mainfile(filepath=str(out));bpy.data.objects['entity:dining.table'].location.x+=.2;bpy.ops.wm.save_as_mainfile(filepath=str(out));external=out.read_bytes()
    try:run(args)
    except RuntimeError as e:assert 'External edits' in str(e)
    else:raise AssertionError('External root transform was overwritten')
    assert out.read_bytes()==external;checks.append('external whole-entity transform conflict rejects sync')
    glb=out.with_suffix('.glb');bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb))
    meshes=[o for o in bpy.data.objects if o.type=='MESH'];lights=[o for o in bpy.data.objects if o.type=='LIGHT'];assert len(meshes)==report['mesh_count'];assert lights;checks.append('GLB reimport mesh count matches actual export and retains real punctual lights')
result={'status':'PASS','checks':checks,'blender':bpy.app.version_string,'reimport_meshes':len(meshes),'reimport_lights':len(lights)}
(root/'docs/qa').mkdir(parents=True,exist_ok=True)
(root/'docs/qa/native-results.json').write_text(json.dumps(result,indent=2))
print('NATIVE_INTEGRATION_PASS '+json.dumps(result),flush=True)
