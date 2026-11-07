"""Persistent scene transactions. No model/API dependencies; SI units, Z up."""
import copy
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from contextlib import contextmanager

STYLES = {
 'warm': {'wood':'#b79367','fabric':'#d2c4ad','wall':'#eee8db','floor':'#d3c6af','metal':'#51595b','accent':'#a56e53','stone':'#c9c5b9','frame':'#826541'},
 'industrial': {'wood':'#899397','fabric':'#62686b','wall':'#c3c0b8','floor':'#888b88','metal':'#abb4b8','accent':'#a27355','stone':'#959b98','frame':'#30383c'},
 'heritage': {'wood':'#674536','fabric':'#b49a72','wall':'#e4d9c5','floor':'#ac9274','metal':'#967342','accent':'#6d7962','stone':'#c5baa5','frame':'#5c3d2b'},
}
STYLE_ALIASES = {'mono': 'industrial'}

def style_key(value):
    return STYLE_ALIASES.get(value,value) if isinstance(value,str) else value

def surface_profile(s,e,role):
    style=style_key(s['rooms'][e['room']].get('style') or s['style'])
    if style!='industrial':return None
    return {'wood':'brushed_steel','metal':'brushed_steel','frame':'blackened_steel',
            'floor':'concrete','stone':'concrete','wall':'concrete'}.get(role)
KINDS = {'shell','sofa','table','chair','cabinet','bed','island','art','window','curtain','cove','plant','rug','toilet','shower','basin','mirror','rail','books','landscape','appliance','wall','floorplan'}
ROLES=(*STYLES['warm'].keys(),'ceramic','glass','leaf','soil','paper','screen','white','light','mirror','skyline','sea')
PARAMS = {
 'shell': {'w':(1,12),'d':(1,12),'h':(2,5),'edge':None,'opening':None},
 'sofa': {'w':(.6,5),'d':(.4,2),'h':(.4,2)},
 'table': {'w':(.3,5),'d':(.3,4),'h':(.2,1.5),'glass':None},
 'chair': {'w':(.3,1.2),'d':(.3,1.2),'h':(.5,1.5)},
 'cabinet': {'w':(.2,6),'d':(.15,1.2),'h':(.2,3),'shelves':None},
 'bed': {'w':(.8,2.5),'d':(1.5,2.7),'h':(.2,1)},
 'island': {'w':(.7,2),'d':(1,3),'h':(.7,1.2)},
 'art': {'w':(.15,3),'h':(.15,3),'image':None},
 'window': {'w':(.5,5),'h':(.5,2.6)},
 'curtain': {'w':(.5,5),'h':(.5,3),'openness':(0,1),'sheer':None},
 'cove': {'w':(.2,6),'power':(0,300),'temperature':(1800,10000),'enabled':None},
 'plant': {'h':(.2,3)}, 'rug': {'w':(.3,5),'d':(.3,5)},
 'toilet': {}, 'shower': {'w':(.7,2),'d':(.7,2)},
 'basin': {'w':(.5,2)}, 'mirror': {'w':(.2,2),'h':(.2,2)},
 'rail': {'w':(.5,6)}, 'books': {'w':(.1,2)}, 'landscape': {'w':(3,40)},'appliance':{'w':(.2,3),'d':(.02,2),'h':(.02,3),'model':None},
 'wall':{'w':(.1,30),'h':(2,5),'thickness':(.05,.5),'opening':None,'gap':(.4,20),'offset':(-15,15),'sill':(0,2),'head':(1.8,4)},
 'floorplan':{'points':None,'thickness':(.01,.5)}
}

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def number(v, lo, hi):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not lo <= v <= hi:
        raise ValueError(f'Expected finite number in [{lo}, {hi}]')

def validate(s):
    if s.get('schema') != 'room-studio/1': raise ValueError('Unsupported scene schema')
    if type(s.get('revision')) is not int or s['revision'] < 0: raise ValueError('Invalid revision')
    if style_key(s.get('style')) not in STYLES or s.get('period') not in ('day','night'): raise ValueError('Unknown style/period')
    if s.get('environment') not in ('city','garden','sea'): raise ValueError('Unknown environment')
    rooms=s.get('rooms',{}); entities=s.get('entities',{})
    if not rooms or not entities: raise ValueError('Empty scene')
    for rid,r in rooms.items():
        if r.get('style') is not None and style_key(r['style']) not in STYLES: raise ValueError('Unknown room style')
        if len(r.get('center',[])) != 2 or len(r.get('size',[])) != 3: raise ValueError('Invalid room geometry')
        for v in r['center']: number(v,-100,100)
        for v in r['size']: number(v,.1,100)
        if 'camera' in r:
            camera=r['camera']
            if not isinstance(camera,dict) or set(camera)!={'position','target'}:raise ValueError('Camera needs position and target')
            for key in ('position','target'):
                if not isinstance(camera[key],list) or len(camera[key])!=3:raise ValueError('Camera coordinates must be XYZ')
                for value in camera[key]:number(value,-1000,1000)
            if camera['position']==camera['target']:raise ValueError('Camera must look toward a different point')
    for eid,e in entities.items():
        if e.get('kind') not in KINDS or e.get('room') not in rooms: raise ValueError(f'Invalid entity {eid}')
        if e.get('id') != eid: raise ValueError('Entity key/id mismatch')
        if len(e.get('position',[])) != 3: raise ValueError('Position must be XYZ')
        for v in e['position']: number(v,-100,100)
        number(e.get('rotation',0),-36000,36000)
        if type(e.get('visible')) is not bool: raise ValueError('visible must be boolean')
        required={'shell':{'w','d','h','edge','opening'},'sofa':{'w','d','h'},'table':{'w','d','h'},'chair':{'w','d','h'},'cabinet':{'w','d','h'},'bed':{'w','d','h'},'island':{'w','d','h'},'art':{'w','h','image'},'window':{'w','h'},'curtain':{'w','h','openness','sheer'},'cove':{'w','power','temperature','enabled'},'plant':{'h'},'rug':{'w','d'},'shower':{'w','d'},'basin':{'w'},'mirror':{'w','h'},'rail':{'w'},'books':{'w'}}
        if not required.get(e['kind'],set()) <= set(e.get('params',{})): raise ValueError(f'Missing required parameters: {eid}')
        if e['kind']=='appliance' and not {'w','d','h','model'}<=set(e.get('params',{})):raise ValueError('Incomplete appliance')
        if e['kind']=='wall':
            p=e['params']
            if not {'w','h','thickness','opening'}<=set(p):raise ValueError('Incomplete wall')
            if p['opening']!='solid' and (not {'gap','offset','sill','head'}<=set(p) or abs(p['offset'])+p['gap']/2>p['w']/2+.001 or p['head']>p['h']):raise ValueError('Opening exceeds wall')
        if e['kind']=='floorplan':
            points=e['params'].get('points')
            if not isinstance(points,list) or not 3<=len(points)<=64:raise ValueError('Invalid floor polygon')
            for pt in points:
                if len(pt)!=2:raise ValueError('Polygon needs XY points')
                for value in pt:number(value,-100,100)
        for key,val in e.get('params',{}).items():
            if key not in PARAMS[e['kind']]: raise ValueError(f'Unsupported {e["kind"]} parameter: {key}')
            bounds=PARAMS[e['kind']][key]
            if bounds: number(val,*bounds)
            elif key in ('glass','shelves','sheer','enabled') and type(val) is not bool: raise ValueError('Expected boolean')
            elif key == 'image' and val not in ('botanical','abstract','coast'): raise ValueError('Unknown artwork')
            elif key == 'edge' and val not in ('N','E','S','W'): raise ValueError('Unknown wall edge')
            elif key == 'opening' and val not in ('door','window','solid'): raise ValueError('Unknown opening')
            elif key == 'model' and val not in ('fridge','cooktop','oven','screen'):raise ValueError('Unknown appliance')
        for role,col in e.get('overrides',{}).items():
            if role not in ROLES:
                raise ValueError('Unknown material role')
            if not isinstance(col,str) or len(col)!=7 or not col.startswith('#'): raise ValueError('Expected #RRGGBB')
            int(col[1:],16)
    return s

def palette(s,e):
    style=style_key(s['rooms'][e['room']].get('style') or s['style'])
    colors={**STYLES[style],'ceramic':'#f0ede5','glass':'#c7dde0','leaf':'#647954','soil':'#52473a','paper':'#ede7d8','screen':'#1d282f','white':'#f9f7ef','light':'#ffe2a6'}
    return {**colors,**e.get('overrides',{})}

def content(s):
    return {k:copy.deepcopy(v) for k,v in s.items() if k not in ('revision','history','redo')}

def effective(s,e):
    result={**e,'palette':palette(s,e),'period':s['period'] if e['kind'] in ('cove','landscape') else None,'environment':s['environment'] if e['kind']=='landscape' else None}
    surfaces={role:profile for role in STYLES['warm'] if (profile:=surface_profile(s,e,role))}
    if surfaces:result['surfaces']=surfaces
    return result

def fingerprints(s): return {eid:digest(effective(s,e)) for eid,e in s['entities'].items()}

def apply(s,patch):
    """Validate the whole candidate before commit; input and source never mutate."""
    validate(s)
    if not isinstance(patch,dict) or set(patch)-{'expected_revision','label','ops','protect'}: raise ValueError('Unsupported patch field')
    if type(patch.get('expected_revision')) is not int or patch.get('expected_revision') != s['revision']: raise ValueError('Revision conflict: reread scene before editing')
    if not isinstance(patch.get('ops'),list) or not 1 <= len(patch['ops']) <= 100: raise ValueError('Expected 1–100 operations')
    protect=patch.get('protect',[])
    if not isinstance(protect,list) or any(not isinstance(eid,str) or eid not in s['entities'] for eid in protect): raise ValueError('protect must list existing entity IDs')
    out=copy.deepcopy(s)
    for op in patch['ops']:
        if not isinstance(op,dict): raise ValueError('Each operation must be an object')
        typ=op.get('op'); target=op.get('target')
        allowed={'set':{'op','target','params','position','rotation','visible'},'material':{'op','target','role','color'},'style':{'op','target','value'},'period':{'op','value'},'environment':{'op','value'}}
        if not isinstance(typ,str) or typ not in allowed or set(op)-allowed[typ]: raise ValueError('Unsupported operation or field')
        required={'set':{'target'},'material':{'target','role','color'},'style':{'target','value'},'period':{'value'},'environment':{'value'}}
        if not required[typ]<=set(op):raise ValueError('Missing operation field')
        if typ in ('set','material','style') and not isinstance(target,str):raise ValueError('Target must be a stable ID')
        if typ=='set':
            if not set(op)&{'params','position','rotation','visible'}:raise ValueError('set requires a changed field')
            if set(op)-{'op','target','params','position','rotation','visible'}: raise ValueError('Unknown set field')
            e=out['entities'].get(target)
            if e is None: raise ValueError(f'Unknown target: {target}')
            if 'params' in op:
                if not isinstance(op['params'],dict):raise ValueError('params must be an object')
                e['params'].update(op['params'])
            for key in ('position','rotation','visible'):
                if key in op:
                    if key=='visible' and type(op[key]) is not bool: raise ValueError('visible must be boolean')
                    e[key]=copy.deepcopy(op[key])
        elif typ=='material':
            e=out['entities'].get(target)
            if e is None: raise ValueError(f'Unknown target: {target}')
            role=op['role']; val=op.get('color')
            if role not in ROLES: raise ValueError('Unknown material role')
            if val is None: e['overrides'].pop(role,None)
            else: e['overrides'][role]=val
        elif typ=='style':
            val=style_key(op.get('value'))
            if target=='all':
                if val not in STYLES: raise ValueError('Unknown style')
                out['style']=val
            elif target in out['rooms']:
                if val is not None and val not in STYLES: raise ValueError('Unknown room style')
                out['rooms'][target]['style']=val
            else: raise ValueError('Unknown room')
        elif typ in ('period','environment'):
            out[typ]=op.get('value')
        else: raise ValueError(f'Unknown operation: {typ}')
    validate(out)
    before=fingerprints(s); after=fingerprints(out)
    changed=[eid for eid in after if after[eid]!=before[eid]]
    if set(protect)&set(changed): raise ValueError('Protected entities would change: '+', '.join(sorted(set(protect)&set(changed))))
    changes={eid:{key:{'before':s['entities'][eid].get(key),'after':out['entities'][eid].get(key)} for key in set(s['entities'][eid])|set(out['entities'][eid]) if s['entities'][eid].get(key)!=out['entities'][eid].get(key)} for eid in changed}
    out['history'].append({'label':str(patch.get('label','Scene edit'))[:300], 'before':content(s), 'after':content(out), 'changed':changed})
    out['history']=out['history'][-40:];out['redo']=[];out['revision']+=1
    return out,{'revision':out['revision'],'changed':changed,'unchanged':len(after)-len(changed),'changes':changes}

def travel(s,redo=False):
    out=copy.deepcopy(s); src='redo' if redo else 'history'; dst='history' if redo else 'redo'
    if not out[src]: raise ValueError('Nothing to redo' if redo else 'Nothing to undo')
    entry=out[src].pop(); snapshot=entry['after' if redo else 'before']
    for k,v in snapshot.items():out[k]=copy.deepcopy(v)
    out[dst].append(entry);out['revision']=s['revision']+1
    validate(out)
    return out,{'revision':out['revision'],'label':entry['label'],'changed':entry['changed']}

def load(path): return validate(json.loads(Path(path).read_text()))

def save(path,s):
    validate(s);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(s,f,ensure_ascii=False,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

@contextmanager
def locked(path):
    # Advisory lock spans read/apply/write for both CLI and local preview server.
    import fcntl
    p=Path(str(path)+'.lock');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)

def transaction(path,patch=None,action=None):
    with locked(path):
        s=load(path)
        out,result=travel(s,action=='redo') if action else apply(s,patch)
        save(path,out)
        return result
