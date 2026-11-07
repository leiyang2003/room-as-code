"""Versioned, metre-scaled Blender surfaces and an explicit glTF PBR fallback.

Object coordinates use the kit's physical mesh coordinates (object scale is one),
so moving/resizing furniture does not stretch a Generated-coordinate texture.
Keep MATERIAL_VERSION in the cache key when changing any recipe.
"""
from core import digest

MATERIAL_VERSION = 3


def rgb(color):
    values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)


def recipe(p):
    if p.get('surface') in ('brushed_steel','blackened_steel','concrete'):return p['surface']
    role=p['role']
    if role in ('wood','frame'):return 'wood'
    if role in ('floor','fabric','stone'):return role
    if role=='white' and 'sheer' in p:return 'fabric'
    return None


def material_id(p):
    key={k:p.get(k) for k in ('role','color','emission','temperature','sheer')}
    if p.get('surface'):key['surface']=p['surface']
    if recipe(p):key['native_material_version']=MATERIAL_VERSION
    return 'RS_'+digest(key)[:16]


def plain_legacy_graph(m):
    """Old signatures did not cover links; only migrate the known plain graph."""
    if not m.use_nodes:return False
    nodes=m.node_tree.nodes
    if len(nodes)!=2 or {n.bl_idname for n in nodes}!={'ShaderNodeBsdfPrincipled','ShaderNodeOutputMaterial'}:return False
    links=list(m.node_tree.links)
    return len(links)==1 and links[0].from_node.bl_idname=='ShaderNodeBsdfPrincipled' and links[0].to_node.bl_idname=='ShaderNodeOutputMaterial' and links[0].from_socket.name=='BSDF' and links[0].to_socket.name=='Surface'


def graph_signature(m):
    """Hash shader values, topology and node settings, excluding editor layout."""
    ignored={'rna_type','name','label','location','location_absolute','width','height','dimensions',
             'select','show_options','show_preview','show_texture','parent','color','use_custom_color',
             'inputs','outputs','internal_links'}
    def value(v):
        if isinstance(v,(str,bool,int,float)) or v is None:return v
        if hasattr(v,'__len__'):return list(v)
        return str(v)
    def tree_state(tree):
        nodes=[]
        for n in sorted(tree.nodes,key=lambda n:n.name):
            props={}
            for prop in n.bl_rna.properties:
                key=prop.identifier
                if key not in ignored and prop.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM'):
                    props[key]=value(getattr(n,key))
            state={'name':n.name,'type':n.bl_idname,'properties':props,
                   'inputs':[(i.identifier,value(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]}
            if getattr(n,'node_tree',None):state['group']=tree_state(n.node_tree)
            if getattr(n,'image',None):
                state['image']={'name':n.image.name,'path':n.image.filepath,'source':n.image.source}
            if getattr(n,'object',None):state['object']=n.object.name
            if hasattr(n,'color_ramp'):
                ramp=n.color_ramp;state['ramp']={'mode':ramp.color_mode,'interpolation':ramp.interpolation,
                    'elements':[(e.position,list(e.color)) for e in ramp.elements]}
            nodes.append(state)
        links=sorted((link.from_node.name,link.from_socket.identifier,link.to_node.name,link.to_socket.identifier) for link in tree.links)
        return {'nodes':nodes,'links':links}
    return digest({'use_nodes':m.use_nodes,'diffuse':list(m.diffuse_color),
                   'surface_method':getattr(m,'surface_render_method',None),
                   'tree':tree_state(m.node_tree) if m.use_nodes else None})


def add_surface(m,p,bs):
    surface=recipe(p)
    if not surface:return
    tree=m.node_tree;nodes=tree.nodes;links=tree.links
    def node(kind,name):
        n=nodes.new(kind);n.name=name;n.label=name;return n
    coords=node('ShaderNodeTexCoord','RS Physical coordinates')
    def scaled(vector):
        n=node('ShaderNodeVectorMath','RS Grain metres');n.operation='MULTIPLY'
        n.inputs[1].default_value=vector;links.new(coords.outputs['Object'],n.inputs[0]);return n.outputs['Vector']
    def noise(name,scale,vector=None):
        n=node('ShaderNodeTexNoise',name);n.noise_dimensions='3D'
        n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=3
        n.inputs['Roughness'].default_value=.65
        links.new(vector if vector is not None else coords.outputs['Object'],n.inputs['Vector'])
        return n.outputs['Fac']
    def remap(source,name,lo,hi):
        n=node('ShaderNodeMapRange',name);n.inputs['To Min'].default_value=lo;n.inputs['To Max'].default_value=hi
        links.new(source,n.inputs['Value']);return n.outputs['Result']
    def multiply(a,b,name):
        n=node('ShaderNodeMath',name);n.operation='MULTIPLY';links.new(a,n.inputs[0]);links.new(b,n.inputs[1]);return n.outputs[0]
    def tint(source):
        n=node('ShaderNodeMixRGB','RS User color tint');n.blend_type='MULTIPLY'
        n.inputs[0].default_value=1;n.inputs[1].default_value=(*rgb(p['color']),1)
        links.new(source,n.inputs[2]);links.new(n.outputs[0],bs.inputs['Base Color'])
    if surface in ('brushed_steel','blackened_steel'):
        grain=noise('RS Brushed steel grain',1,scaled((4,650,18)))
        tint(remap(grain,'RS Steel color',.96,1.0))
        dark=surface=='blackened_steel'
        bs.inputs['Metallic'].default_value=.82 if dark else .92
        bs.inputs['Roughness'].default_value=.44 if dark else .34
        bs.inputs['Anisotropic'].default_value=.25 if dark else .55
        roughness=remap(grain,'RS Steel roughness',.38 if dark else .27,.5 if dark else .40)
        height=grain;distance=.000035;strength=.10
    elif surface=='concrete':
        coarse=noise('RS Concrete variation',7)
        tint(remap(coarse,'RS Concrete color',.92,1.0))
        height=noise('RS Concrete pores',150);distance=.0003;strength=.20
        roughness=remap(coarse,'RS Concrete roughness',.72,.86)
        bs.inputs['Roughness'].default_value=.79
    elif surface in ('wood','floor'):
        grain=noise('RS Wood grain',1,scaled((2,70,7)))
        shade=remap(grain,'RS Subtle grain color',.84,1.0)
        if surface=='floor':
            boards=node('ShaderNodeTexBrick','RS Metre floor boards')
            boards.inputs['Scale'].default_value=1;boards.inputs['Brick Width'].default_value=1.2
            boards.inputs['Row Height'].default_value=.18;boards.inputs['Mortar Size'].default_value=.002
            boards.inputs['Mortar Smooth'].default_value=.001
            boards.inputs['Color1'].default_value=(1,1,1,1);boards.inputs['Color2'].default_value=(.94,.94,.94,1)
            boards.inputs['Mortar'].default_value=(.72,.72,.72,1)
            links.new(coords.outputs['Object'],boards.inputs['Vector'])
            # Scalar modulation keeps the user's explicit color as the common tint.
            shade=multiply(shade,boards.outputs['Color'],'RS Board and grain color')
        tint(shade);height=grain;distance=.00035;strength=.22
        roughness=remap(grain,'RS Grain roughness',.46 if surface=='floor' else .38,.62 if surface=='floor' else .54)
        bs.inputs['Roughness'].default_value=.56 if surface=='floor' else .48
    elif surface=='fabric':
        waves=[]
        for axis in ('X','Y'):
            n=node('ShaderNodeTexWave','RS Weave '+axis);n.wave_type='BANDS';n.bands_direction=axis
            n.inputs['Scale'].default_value=220;links.new(coords.outputs['Object'],n.inputs['Vector']);waves.append(n.outputs['Fac'])
        height=multiply(*waves,'RS Cross weave');distance=.0004;strength=.18
        roughness=remap(height,'RS Weave roughness',.86,.96)
        bs.inputs['Roughness'].default_value=.92;bs.inputs['Sheen Weight'].default_value=.18
    else:
        coarse=noise('RS Stone variation',5)
        tint(remap(coarse,'RS Subtle stone color',.94,1.0))
        height=noise('RS Stone pores',180);distance=.00022;strength=.15
        roughness=remap(coarse,'RS Stone roughness',.30,.46);bs.inputs['Roughness'].default_value=.38
    links.new(roughness,bs.inputs['Roughness'])
    bump=node('ShaderNodeBump','RS Physical micro surface');bump.inputs['Distance'].default_value=distance
    bump.inputs['Strength'].default_value=strength;links.new(height,bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    m['rs_surface_recipe']=surface;m['rs_material_version']=MATERIAL_VERSION
    m['rs_coordinate_units']='object-local metres; unapplied object scale is unsupported'


def material(p,kelvin,cache=None):
    import bpy
    mid=material_id(p)
    if cache is not None and mid in cache:return cache[mid]
    m=bpy.data.materials.get(mid)
    if m:
        if m.get('rs_surface_signature') and graph_signature(m)!=m['rs_surface_signature']:
            raise RuntimeError('External edits detected in cached managed material: '+m.name)
    else:
        m=bpy.data.materials.new(mid);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');col=rgb(p['color']);role=p['role']
        m.diffuse_color=(*col,1);bs.inputs['Base Color'].default_value=(*col,1)
        bs.inputs['Roughness'].default_value=.24 if role in ('metal','glass','mirror') else .68
        bs.inputs['Metallic'].default_value=1 if role in ('metal','mirror') else 0
        if role=='glass':bs.inputs['Transmission Weight'].default_value=.92;bs.inputs['Roughness'].default_value=.07
        if p.get('sheer'):bs.inputs['Alpha'].default_value=.25;m.surface_render_method='DITHERED'
        if p.get('emission',0)>0:
            bs.inputs['Emission Color'].default_value=(*kelvin(p.get('temperature',3000)),1);bs.inputs['Emission Strength'].default_value=p['emission']
        add_surface(m,p,bs)
        m['rs_surface_signature']=graph_signature(m)
    if cache is not None:cache[mid]=m
    return m


def export_glb(filepath,exporter=None):
    """glTF cannot carry these noise/wave/bump graphs. Export constant PBR values.

Do not silently pretend they were baked. Native graphs are restored even if the
exporter raises, and are never removed from the saved editable master.
"""
    import bpy
    fallbacks={};slots=[];seen_meshes=set()
    try:
        for obj in bpy.data.objects:
            if obj.type!='MESH':continue
            if obj.data.as_pointer() in seen_meshes:continue
            seen_meshes.add(obj.data.as_pointer())
            for index,m in enumerate(obj.data.materials):
                if not m or not m.get('rs_surface_recipe'):continue
                if m.name not in fallbacks:
                    fallback=m.copy();fallback.name=m.name+'_GLB_PBR'
                    for n in list(fallback.node_tree.nodes):
                        if n.bl_idname not in ('ShaderNodeBsdfPrincipled','ShaderNodeOutputMaterial'):fallback.node_tree.nodes.remove(n)
                    fallback['rs_gltf_surface']='constant PBR fallback; procedural texture not baked'
                    fallbacks[m.name]=fallback
                slots.append((obj.data,index,m));obj.data.materials[index]=fallbacks[m.name]
        (exporter or bpy.ops.export_scene.gltf)(filepath=str(filepath),export_format='GLB',export_extras=True,export_cameras=True,export_lights=True,export_yup=True)
    finally:
        for mesh,index,m in slots:mesh.materials[index]=m
        for fallback in fallbacks.values():
            if fallback.users==0:bpy.data.materials.remove(fallback)
    return len(fallbacks)
