"""Blender integration: material upgrade, persistence, reuse and conflicts. No render.

blender --background --factory-startup --python-exit-code 1 --python tests/native_materials.py
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
import bpy
from core import apply,digest,load,save
from catalog import compile_scene
from blender_sync import run,signature,kelvin,rgb
from native_materials import MATERIAL_VERSION,recipe,graph_signature,material_id,export_glb


def legacy_material(p):
    """The previous release's exact two-node material ID and scalar values."""
    mid='RS_'+digest({k:p.get(k) for k in ('role','color','emission','temperature','sheer')})[:16]
    m=bpy.data.materials.get(mid)
    if m:return m
    m=bpy.data.materials.new(mid);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');col=rgb(p['color']);role=p['role']
    m.diffuse_color=(*col,1);bs.inputs['Base Color'].default_value=(*col,1)
    bs.inputs['Roughness'].default_value=.24 if role in ('metal','glass','mirror') else .68
    bs.inputs['Metallic'].default_value=1 if role in ('metal','mirror') else 0
    if role=='glass':bs.inputs['Transmission Weight'].default_value=.92;bs.inputs['Roughness'].default_value=.07
    if p.get('sheer'):bs.inputs['Alpha'].default_value=.25;m.surface_render_method='DITHERED'
    if p.get('emission',0)>0:
        bs.inputs['Emission Color'].default_value=(*kelvin(p.get('temperature',3000)),1);bs.inputs['Emission Strength'].default_value=p['emission']
    return m


def glb_json(path):
    data=path.read_bytes();assert data[:4]==b'glTF'
    length,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
    return json.loads(data[20:20+length])


checks=[]
with tempfile.TemporaryDirectory(prefix='room-studio-materials-') as directory:
    project=Path(directory);path=project/'house.scene.json';out=project/'master.blend'
    fixture=ROOT/'examples/quiet-house.scene.json'
    scene=load(fixture if fixture.exists() else ROOT/'examples/kit-grid.scene.json')
    ids={'living.sofa','living.floor','living.picture','living.sheer','kitchen.island','kitchen.back_cabinets','dining.table'}
    scene['entities']={eid:e for eid,e in scene['entities'].items() if eid in ids}
    scene['rooms']={rid:r for rid,r in scene['rooms'].items() if rid in {'living','kitchen','dining'}}
    scene['entities']['living.sofa']['overrides']['fabric']='#778899'
    scene['entities']['living.floor']['overrides']['floor']='#a67c52'
    scene['entities']['kitchen.back_cabinets']['overrides']['stone']='#b7b5a8'
    save(path,scene)
    args=argparse.Namespace(scene=str(path),out=str(out),render=None,room='living',samples=1,resolution=64)
    run(args)
    parts={p['id']:p for p in compile_scene(scene)}
    # Emulate the old master format without depending on a large stale dist file.
    for obj in bpy.data.objects:
        if obj.get('rs_id'):
            p=parts[obj['rs_id']]
            if obj.type=='MESH':obj.data.materials.clear();obj.data.materials.append(legacy_material(p))
            obj['qa_identity']=obj.name
        if obj.get('rs_id') or obj.get('rs_root_entity'):
            if 'rs_signature_version' in obj:del obj['rs_signature_version']
            obj['rs_signature']=signature(obj,version=1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out));legacy_bytes=out.read_bytes()
    run(args);report=json.loads(out.with_suffix('.validation.json').read_text())
    expected={key for key,p in parts.items() if p['shape']!='light' and recipe(p)}
    assert set(report['updated_material_parts'])==expected
    assert report['updated_parts']==[] and len(report['unchanged_parts'])==len(parts)
    for obj in bpy.data.objects:
        if obj.get('rs_id'):assert obj['qa_identity']==obj.name
    checks.append('prior two-node materials and v1 object signatures migrate; only affected material slots replaced; geometry identities preserved')
    families={}
    for key in expected:
        obj=bpy.data.objects[key];m=obj.data.materials[0];p=parts[key]
        assert m.name==material_id(p) and m['rs_material_version']==MATERIAL_VERSION
        assert m['rs_surface_signature']==graph_signature(m)
        assert any(link.to_socket.name=='Normal' and link.to_node.bl_idname=='ShaderNodeBsdfPrincipled' for link in m.node_tree.links)
        assert any(link.from_node.bl_idname=='ShaderNodeTexCoord' and link.from_socket.name=='Object' for link in m.node_tree.links)
        assert not any(link.from_node.bl_idname=='ShaderNodeTexCoord' and link.from_socket.name=='Generated' for link in m.node_tree.links)
        assert all(abs(a-b)<1e-6 for a,b in zip(m.diffuse_color[:3],rgb(p['color'])))
        if 'RS User color tint' in m.node_tree.nodes:
            assert all(abs(a-b)<1e-6 for a,b in zip(m.node_tree.nodes['RS User color tint'].inputs[1].default_value[:3],rgb(p['color'])))
        families[m['rs_surface_recipe']]=m.name
    assert set(families)=={'wood','floor','fabric','stone'},families
    checks.append('wood grain, metre-sized floor boards, cross-weave fabric and stone micro surfaces use physical Object coordinates and preserve supplied role colors')
    run(args);report=json.loads(out.with_suffix('.validation.json').read_text())
    assert report['updated_parts']==[] and report['updated_material_parts']==[]
    assert not any(m.name.endswith('_GLB_PBR') for m in bpy.data.materials)
    bpy.ops.wm.open_mainfile(filepath=str(out))
    for obj in bpy.data.objects:
        if obj.get('rs_id'):assert signature(obj)==obj['rs_signature']
    checks.append('saved master reopens with shader graphs and v2 signatures intact; unchanged second sync reuses all geometry and materials; GLB fallback copies cleaned up')
    source=next(o for o in bpy.data.objects if o.get('rs_id') and o.type=='MESH' and o.data.materials[0].get('rs_surface_recipe'))
    linked=bpy.data.objects.new('QA shared mesh',source.data);bpy.context.collection.objects.link(linked)
    material_before=source.data.materials[0];signature_before=signature(source)
    def fail_export(**kwargs):raise RuntimeError('Injected exporter failure')
    try:export_glb(project/'failed.glb',exporter=fail_export)
    except RuntimeError as error:assert str(error)=='Injected exporter failure'
    else:raise AssertionError('Expected test export failure')
    assert source.data.materials[0]==material_before and linked.data.materials[0]==material_before
    assert signature(source)==signature_before
    assert not any(m.name.endswith('_GLB_PBR') for m in bpy.data.materials)
    bpy.data.objects.remove(linked,do_unlink=True)
    checks.append('failed GLB export restores native graph slots and removes fallback copies, including linked meshes sharing one datablock')
    edited,result=apply(scene,{'expected_revision':scene['revision'],'protect':sorted(ids-{'living.sofa'}),
        'ops':[{'op':'material','target':'living.sofa','role':'fabric','color':'#336699'}]})
    save(path,edited);run(args)
    report=json.loads(out.with_suffix('.validation.json').read_text())
    assert report['updated_parts'] and all(key.startswith('living.sofa/') for key in report['updated_parts'])
    old_fabric_ids={key for key,p in parts.items() if p['entity']=='living.sofa' and p['role']=='fabric'}
    for key in old_fabric_ids:
        m=bpy.data.objects[key].data.materials[0]
        assert all(abs(a-b)<1e-6 for a,b in zip(m.diffuse_color[:3],rgb('#336699')))
    checks.append('user fabric color edit changes only sofa material inputs and preserves every protected entity')
    exported=glb_json(out.with_suffix('.glb'))
    assert not exported.get('textures') and not exported.get('images')
    assert any(all(abs(a-b)<1e-6 for a,b in zip(m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[])[:3],rgb('#336699')))
               and len(m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[]))==4 for m in exported['materials'])
    checks.append('actual GLB contains constant PBR colors including the user override, with no falsely claimed baked procedural textures')
    # Recolor and resize/move must not change texture frequency or recipes.
    fabric_key=next(iter(old_fabric_ids));m=bpy.data.objects[fabric_key].data.materials[0]
    surface_before=graph_signature(m);material_name=m.name
    sofa=edited['entities']['living.sofa'];position=list(sofa['position']);position[0]+=.3
    moved,_=apply(edited,{'expected_revision':edited['revision'],'ops':[{'op':'set','target':'living.sofa','position':position,'params':{'w':sofa['params']['w']+.1}}]})
    save(path,moved);run(args)
    m=bpy.data.objects[fabric_key].data.materials[0]
    assert m.name==material_name and graph_signature(m)==surface_before
    checks.append('moving and resizing a sofa reuses the exact metre-scaled material recipe without stretching a Generated map')
    stable=out.read_bytes();glb_stable=out.with_suffix('.glb').read_bytes()
    def expect_conflict(mutator,label,base=stable):
        out.write_bytes(base);bpy.ops.wm.open_mainfile(filepath=str(out));mutator()
        bpy.ops.wm.save_as_mainfile(filepath=str(out));external=out.read_bytes()
        try:run(args)
        except RuntimeError as error:assert 'External edits' in str(error)
        else:raise AssertionError('External material edit was overwritten: '+label)
        assert out.read_bytes()==external and out.with_suffix('.glb').read_bytes()==glb_stable
        checks.append('external '+label+' rejected before native/GLB overwrite')
    def wood():return next(m for m in bpy.data.materials if m.users and m.get('rs_surface_recipe')=='wood')
    def change_noise():wood().node_tree.nodes['RS Wood grain'].inputs['Scale'].default_value=2
    def change_link():
        m=wood();link=next(link for link in m.node_tree.links if link.to_socket.name=='Normal');m.node_tree.links.remove(link)
    def add_node():wood().node_tree.nodes.new('ShaderNodeTexNoise')
    expect_conflict(change_noise,'noise parameter edit')
    expect_conflict(change_link,'shader link removal')
    expect_conflict(add_node,'shader node addition')
    def legacy_extra_node():
        m=next(o.data.materials[0] for o in bpy.data.objects if o.get('rs_id') and o.type=='MESH');m.node_tree.nodes.new('ShaderNodeTexNoise')
    expect_conflict(legacy_extra_node,'legacy graph extension',legacy_bytes)
    out.write_bytes(stable);bpy.ops.wm.open_mainfile(filepath=str(out))
    checks.append('no renders produced during material acceptance')
    assert not list(project.glob('*.png'))
    existing=ROOT/'dist/quiet-house.blend'
    existing_report=None
    if existing.is_file():
        original_hash=hashlib.sha256(existing.read_bytes()).hexdigest()
        copied=project/'existing-master.blend';shutil.copy2(existing,copied)
        bpy.ops.wm.open_mainfile(filepath=str(copied))
        embedded=json.loads(bpy.context.scene['room_studio_source'])
        existing_scene=project/'existing.scene.json';save(existing_scene,embedded)
        existing_args=argparse.Namespace(scene=str(existing_scene),out=str(copied),render=None,room='living',samples=1,resolution=64)
        run(existing_args);first=json.loads(copied.with_suffix('.validation.json').read_text())
        run(existing_args);second=json.loads(copied.with_suffix('.validation.json').read_text())
        assert second['updated_parts']==[] and second['updated_material_parts']==[]
        assert hashlib.sha256(existing.read_bytes()).hexdigest()==original_hash
        existing_report={'source_filename':existing.name,'material_slots_upgraded':len(first['updated_material_parts']),
                         'geometry_updates_due_to_current_compiler':len(first['updated_parts']),
                         'second_sync_geometry_updates':0,'second_sync_material_updates':0,'original_preserved':True}
        checks.append('actual existing dist master upgraded in an isolated copy using its embedded source; second sync stable; original file hash unchanged')
    evidence=(ROOT if (ROOT/'docs').is_dir() else ROOT.parent)/'docs/qa';evidence.mkdir(parents=True,exist_ok=True)
    result={'status':'PASS','blender':bpy.app.version_string,'material_version':MATERIAL_VERSION,
            'material_families':sorted(families),'checks':checks,'legacy_scope':'Synthetic legacy master recreates previous material IDs, two-node graphs and v1 object signature format.',
            'existing_master_check':existing_report,
            'glb_limit':'Native procedural wood/floor/fabric/stone graphs are not baked or exported as textures; GLB receives explicit constant PBR fallback colors and scalar properties.',
            'visual_scope':'Graph, persistence, export-data and conflict behavior checked in actual Blender; no render or appearance-quality claim.'}
    (evidence/'task-b-material-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('NATIVE_MATERIALS_PASS '+json.dumps(result),flush=True)
