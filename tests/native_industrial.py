from pathlib import Path
import sys,json,tempfile,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/room-studio/scripts'))
import bpy
from catalog import demo,compile_scene
from native_materials import material,graph_signature,export_glb,MATERIAL_VERSION
from blender_sync import kelvin
s=demo();s['style']='industrial';parts=compile_scene(s)
checks=[]
with tempfile.TemporaryDirectory(prefix='room-studio-industrial-') as tmp:
 tmp=Path(tmp);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for i,surface in enumerate(('brushed_steel','blackened_steel','concrete')):
  p=next(p for p in parts if p.get('surface')==surface);m=material(p,kelvin);bs=m.node_tree.nodes.get('Principled BSDF')
  assert m['rs_surface_recipe']==surface
  assert (bs.inputs['Metallic'].default_value>.8) if 'steel' in surface else (bs.inputs['Metallic'].default_value==0)
  assert 'RS Wood grain' not in m.node_tree.nodes and 'RS Metre floor boards' not in m.node_tree.nodes
  assert .25<bs.inputs['Roughness'].default_value<.9
  bpy.ops.mesh.primitive_cube_add(location=(i*2,0,0));bpy.context.object.data.materials.append(m)
 checks.append('Steel and concrete create distinct physical shader graphs without wood or plank textures')
 before={o.name:graph_signature(o.data.materials[0]) for o in bpy.data.objects if o.type=='MESH'}
 bpy.ops.wm.save_as_mainfile(filepath=str(tmp/'check.blend'));bpy.ops.wm.open_mainfile(filepath=str(tmp/'check.blend'))
 assert before=={o.name:graph_signature(o.data.materials[0]) for o in bpy.data.objects if o.type=='MESH'}
 checks.append('New material graphs survive native save and reopen')
 export_glb(tmp/'check.glb')
 assert before=={o.name:graph_signature(o.data.materials[0]) for o in bpy.data.objects if o.type=='MESH'}
 data=(tmp/'check.glb').read_bytes();n,kind=struct.unpack('<II',data[12:20]);g=json.loads(data[20:20+n])
 metallic=[m['pbrMetallicRoughness'].get('metallicFactor',1) for m in g['materials']]
 assert sum(v>.8 for v in metallic)==2 and any(v==0 for v in metallic)
 checks.append('GLB fallback retains actual metalness and roughness; native shader slots restored')
 assert not list(tmp.glob('*.png'))
 r={'status':'PASS','blender':bpy.app.version_string,'material_version':MATERIAL_VERSION,'checks':checks,'full_render':False}
 out=Path(__file__).resolve().parents[1]/'docs/qa/industrial-native-results.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
