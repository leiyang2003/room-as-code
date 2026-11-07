"""Run in Blender: stable primitive sync, conflict detection, native/GLB export."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import argparse,json,math
from contextlib import contextmanager
import bpy
from mathutils import Vector
from core import load,digest,content
from catalog import compile_scene
from render_state import manifest_path, record_render
from framing import room_camera, overview_camera
from native_materials import MATERIAL_VERSION,graph_signature,plain_legacy_graph,export_glb,rgb
from native_materials import material as surface_material

def kelvin(k):
    t=k/100
    r=255 if t<=66 else 329.698727446*(t-60)**-.1332047592
    g=99.4708025861*math.log(t)-161.1195681661 if t<=66 else 288.1221695283*(t-60)**-.0755148492
    b=255 if t>=66 else 0 if t<=19 else 138.5177312231*math.log(t-10)-305.0447927307
    return tuple(max(0,min(255,v))/255 for v in (r,g,b))

def signature(o,version=2,material_cache=None):
    data={'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale),'type':o.type}
    if o.type=='MESH':
        data['v']=[list(v.co) for v in o.data.vertices];data['f']=[list(p.vertices) for p in o.data.polygons]
        mats=[]
        for m in o.data.materials:
            if m is None:mats.append(None);continue
            bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
            mats.append({'color':list(m.diffuse_color),'bsdf':{key:list(bs.inputs[key].default_value) if hasattr(bs.inputs[key].default_value,'__len__') else bs.inputs[key].default_value for key in ['Base Color','Metallic','Roughness','Emission Color','Emission Strength','Alpha']} if bs else {}})
            if version>=2:
                key=m.as_pointer()
                if material_cache is None:mats[-1]['graph']=graph_signature(m)
                else:
                    if key not in material_cache:material_cache[key]=graph_signature(m)
                    mats[-1]['graph']=material_cache[key]
        data['materials']=mats
        data['modifiers']=[{'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers]
    if o.type=='LIGHT':data['light']=[o.data.energy,list(o.data.color)]
    return digest(data)

def material(p,cache=None):return surface_material(p,kelvin,cache)

def part_metadata(o,p):
    # Refresh even on fingerprint reuse: older masters predate these flags.
    for key in ('outside','ceiling','structural','architecture','facade'):
        o['rs_'+key]=bool(p.get(key,False))

@contextmanager
def render_visibility(room,compiled):
    """Overview cutaway is temporary, including when rendering raises."""
    snapshots=[]
    try:
        if room=='overview':
            parts={p['id']:p for p in compiled}
            for o in bpy.data.objects:
                p=parts.get(o.get('rs_id'))
                if p is None:continue
                snapshots.append((o,o.location.copy(),o.scale.copy(),o.hide_render))
                if o.get('rs_architecture',False):
                    o.scale.z=.13;o.location.z=p['position'][2]*.13
                elif o.get('rs_structural',False):o.hide_render=True
                if o.get('rs_facade',False) or o.get('rs_outside',False) or o.get('rs_ceiling',False):o.hide_render=True
        yield
    finally:
        for o,location,scale,hidden in snapshots:
            o.location=location;o.scale=scale;o.hide_render=hidden

def make(p,material_cache=None):
    shape=p['shape'];size=p['size'];name=p['id']
    if shape=='light':
        data=bpy.data.lights.new(name,'SPOT');data.energy=p['power'];data.color=kelvin(p['temperature']);data.spot_size=2.6;data.spot_blend=.7;data.shadow_soft_size=.3
        o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
        o.rotation_euler=Vector(p['target']).to_track_quat('-Z','Y').to_euler()
    elif shape=='mesh':
        me=bpy.data.meshes.new(name);me.from_pydata(p['vertices'],[],p['faces']);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
        if 'sheer' in p:
            sol=o.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.004
    else:
        # Data API avoids rebuilding the complete dependency graph per primitive.
        verts=[];faces=[]
        if shape=='sphere':
            for j in range(9):
                theta=math.pi*j/8
                for i in range(16):
                    phi=2*math.pi*i/16
                    verts.append((math.sin(theta)*math.cos(phi)*size[0]/2,math.sin(theta)*math.sin(phi)*size[1]/2,math.cos(theta)*size[2]/2))
            for j in range(8):
                for i in range(16):faces.append((j*16+i,j*16+(i+1)%16,(j+1)*16+(i+1)%16,(j+1)*16+i))
        elif shape=='cylinder':
            for z in [-.5,.5]:
                for i in range(16):verts.append((math.cos(i*math.pi/8)*size[0]/2,math.sin(i*math.pi/8)*size[1]/2,z*size[2]))
            faces=[tuple(reversed(range(16))),tuple(range(16,32))]
            faces += [(i,(i+1)%16,(i+1)%16+16,i+16) for i in range(16)]
        else:
            verts=[(x*size[0]/2,y*size[1]/2,z*size[2]/2) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
            faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
        if shape=='box':
            bevel=o.modifiers.new('Edge detail','BEVEL');bevel.width=min(p.get('roundness',.009),min(size)*.3);bevel.segments=3
            o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
        else:
            for poly in o.data.polygons:poly.use_smooth=True
    if o.type=='MESH':o.data.materials.append(material(p,material_cache))
    o.location=p['position'];o['rs_id']=name;o['rs_entity']=p['entity'];o['rs_room']=p['room'];o['rs_rooms']=json.dumps(p['rooms']);o['rs_fingerprint']=p['fingerprint'];part_metadata(o,p)
    return o

def run(args):
    s=load(args.scene);compiled=compile_scene(s);out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():bpy.ops.wm.open_mainfile(filepath=str(out))
    else:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    managed={o.get('rs_id'):o for o in bpy.data.objects if o.get('rs_id')}
    signature_cache={}
    def external(o):
        version=o.get('rs_signature_version',1)
        if version==1 and o.type=='MESH' and any(m is None or not plain_legacy_graph(m) for m in o.data.materials):return True
        return o.get('rs_signature') and signature(o,version,signature_cache)!=o['rs_signature']
    conflicts=[key for key,o in managed.items() if external(o)]
    conflicts += [o.name for o in bpy.data.objects if o.get('rs_root_entity') and external(o)]
    if conflicts:raise RuntimeError('External edits detected; source file preserved. Conflicts: '+', '.join(conflicts[:12]))
    roots={}
    for eid,e in s['entities'].items():
        root=bpy.data.objects.get('entity:'+eid)
        if not root:
            root=bpy.data.objects.new('entity:'+eid,None);bpy.context.collection.objects.link(root)
        root.location=e['position'];root.rotation_euler=(0,0,math.radians(e['rotation']));root['rs_root_entity']=eid;root['rs_signature_version']=2;root['rs_signature']=signature(root);roots[eid]=root
    updated=[];unchanged=[];updated_materials=[];material_cache={};signature_cache={}
    expected={p['id'] for p in compiled}
    for key,o in managed.items():
        if key not in expected:bpy.data.objects.remove(o,do_unlink=True)
    for p in compiled:
        o=managed.get(p['id'])
        if o and o['rs_fingerprint']==p['fingerprint']:
            unchanged.append(p['id'])
            if o.type=='MESH':
                expected_material=material(p,material_cache)
                if len(o.data.materials)!=1 or o.data.materials[0]!=expected_material:
                    o.data.materials.clear();o.data.materials.append(expected_material);updated_materials.append(p['id'])
        else:
            if o:bpy.data.objects.remove(o,do_unlink=True)
            o=make(p,material_cache);updated.append(p['id'])
        part_metadata(o,p)
        o.parent=roots[p['entity']];o.hide_render=not p['visible'];o.hide_viewport=not p['visible'];o['rs_signature_version']=2;o['rs_signature']=signature(o,material_cache=signature_cache)
    print(f'GEOMETRY_READY updated={len(updated)} unchanged={len(unchanged)}',flush=True)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.samples=args.samples;scene.cycles.use_denoising=True
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');night=s['period']=='night'
    bg.inputs['Color'].default_value=(.52,.67,.85,1) if not night else (.018,.034,.065,1);bg.inputs['Strength'].default_value=.45 if not night else .16
    sun=bpy.data.objects.get('Daylight')
    if not sun:
        data=bpy.data.lights.new('Daylight','SUN');sun=bpy.data.objects.new('Daylight',data);bpy.context.collection.objects.link(sun)
    sun.data.energy=0 if night else 2;sun.data.angle=.12;sun.data.color=(1,.9,.75);sun.rotation_euler=(.45,-.5,-.5)
    for rid,r in s['rooms'].items():
        name='WindowSky_'+rid;o=bpy.data.objects.get(name)
        if not o:o=bpy.data.objects.new(name,bpy.data.lights.new(name,'SPOT'));bpy.context.collection.objects.link(o)
        x,y=r['center'];side=1 if y>0 else -1
        o.location=(x,y+side*2.25,2);o.rotation_euler=(Vector((x,y-side*.5,.8))-o.location).to_track_quat('-Z','Y').to_euler()
        o.data.energy=0 if night or rid=='entry' else 160;o.data.color=(.82,.9,1);o.data.spot_size=2.6;o.data.spot_blend=.8;o.data.shadow_soft_size=1
    # Cameras are part of the deliverable; render visibility is transient and restored before saving.
    def camera(name,pos,target,lens):
        o=bpy.data.objects.get(name)
        if not o:o=bpy.data.objects.new(name,bpy.data.cameras.new(name));bpy.context.collection.objects.link(o)
        o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;o.data.clip_end=200;return o
    for rid,r in s['rooms'].items():
        pos,target,lens=room_camera(rid,r);camera('View_'+rid,pos,target,lens)
    pos,target,lens=overview_camera(s);camera('View_overview',pos,target,lens)
    if args.room!='overview' and args.room not in s['rooms']:raise ValueError('Unknown render room')
    scene.camera=bpy.data.objects['View_'+args.room];scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
    scene.render.resolution_x=args.resolution;scene.render.resolution_y=round(args.resolution*.7);scene.render.resolution_percentage=100
    scene['room_studio_revision']=s['revision'];scene['room_studio_style']=s['style'];scene['room_studio_period']=s['period']
    scene['room_studio_source']=json.dumps(s,ensure_ascii=False)
    scene['room_studio_material_version']=MATERIAL_VERSION
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    fallback_count=export_glb(out.with_suffix('.glb'))
    report={'revision':s['revision'],'updated_parts':updated,'unchanged_parts':unchanged,'updated_material_parts':updated_materials,'material_version':MATERIAL_VERSION,'glb_surface_mode':'constant PBR fallback; procedural textures not baked','glb_fallback_materials':fallback_count,'entities':len(roots),'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),'blender':bpy.app.version_string}
    out.with_suffix('.validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if args.render:
        scene.render.filepath=args.render;scene.render.image_settings.file_format='PNG';scene.render.use_file_extension=False
        Path(args.render).parent.mkdir(parents=True,exist_ok=True)
        # Invalidate previous provenance before a render that could fail midway.
        manifest_path(args.render).unlink(missing_ok=True)
        with render_visibility(args.room,compiled):
            bpy.ops.render.render(write_still=True)
        record_render(args.render,s,room=args.room,samples=args.samples,resolution=[scene.render.resolution_x,scene.render.resolution_y],blender=bpy.app.version_string)
        # Do not persist cutaway render flags into the editable master.
    print('ROOM_STUDIO_SYNC '+json.dumps({k:v for k,v in report.items() if k not in ('updated_parts','unchanged_parts','updated_material_parts')})+f' updated={len(updated)} unchanged={len(unchanged)} material_updates={len(updated_materials)}',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--scene',required=True);ap.add_argument('--out',required=True);ap.add_argument('--render');ap.add_argument('--room',default='living');ap.add_argument('--samples',type=int,default=32);ap.add_argument('--resolution',type=int,default=1100)
    run(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))
