"""267 m² design envelope inspired by Residence 02, not a measured reconstruction.

Coordinates are a deliberately simplified reading of the public plan. Rooms tile one
polygon; shared walls are authored once and doors carry an explicit adjacency graph.
"""
import copy
import math
from core import validate


def area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2


def residence(kit):
    outline=[[-11,0],[1,0],[1,-5],[3,-5],[3,-3],[5,-3],[5,0],[12,0],[11.2,4],[11,5],[8.5,11],[-11,11]]
    scale=math.sqrt(267/area(outline))
    def rect(x0,y0,x1,y1):return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
    specs=[
        ('entry','入户门厅',rect(1,-5,3,-3),'arrival'),
        ('gallery','长画廊',rect(1,-3,3,6.5),'circulation'),
        ('living','转角大客厅',[[3,4],[11.2,4],[11,5],[8.5,11],[3,11]],'public'),
        ('kitchen','开放厨房',rect(3,0,7.2,4),'public'),
        ('dining','家庭餐厅',[[7.2,0],[12,0],[11.2,4],[7.2,4]],'public'),
        ('bedroom','主卧',rect(-11,6.5,-6,11),'private'),
        ('bedroom2','次卧',rect(-6,6.5,-1.5,11),'private'),
        ('study','第三卧室 / 书房',rect(-1.5,6.5,3,11),'private'),
        ('private_hall','卧室走廊',rect(-7,5,1,6.5),'circulation'),
        ('service_hall','服务走廊',[[-7,1.6],[1,1.6],[1,3.2],[-6,3.2],[-6,5],[-7,5]],'circulation'),
        ('bathroom','主卫',rect(-11,0,-7,3.2),'service'),
        ('dressing','步入衣帽间',rect(-11,3.2,-7,6.5),'private'),
        ('bathroom2','次卫',rect(-6,3.2,-3.2,5),'service'),
        ('bathroom3','第三卫浴',rect(-3.2,3.2,-.4,5),'service'),
        ('linen','布草柜',rect(-.4,3.2,1,5),'service'),
        ('laundry','洗衣间',rect(-7,0,-4.4,1.6),'service'),
        ('storage','储物间',rect(-4.4,0,-1.8,1.6),'service'),
        ('utility','设备间',rect(-1.8,0,1,1.6),'service'),
        ('powder','客卫',rect(3,-3,5,0),'service'),
    ]
    s={k:copy.deepcopy(v) for k,v in kit.items() if k not in ('rooms','entities')}
    s.update(name='Manhattan / 曼哈顿大公寓',rooms={},entities={},history=[],redo=[],revision=0)
    s['provenance']={'origin':'reference_layout_design_adaptation','scale':'design_dimensions',
        'reference':'35 Hudson Yards Residence 02, floors 75–82; public developer floor plan',
        'notes':'Space organization adapted from the public plan. 267 m² is this model’s design envelope, not measured net usable area, survey, exact sales-plan reproduction or BIM. Three bedrooms, three full bathrooms, powder room; no balcony. Procedural scenery is not the actual view.'}
    def xy(pt):return [round(v*scale,6) for v in pt]
    for rid,label,poly,zone in specs:
        pts=[xy(pt) for pt in poly];xs,ys=zip(*pts);center=[(min(xs)+max(xs))/2,(min(ys)+max(ys))/2]
        s['rooms'][rid]={'name':label,'center':center,'size':[max(xs)-min(xs),max(ys)-min(ys),3.05],
            'style':None,'polygon':pts,'zone':zone,'area_design_m2':round(area(pts),3)}
    def add(rid,name,kind,x,y,z=0,rotation=0,**params):
        eid=rid+'.'+name
        for key in ('w','d'): 
            if key in params:params[key]=round(params[key]*scale,6)
        e={'id':eid,'label':name.replace('_',' '),'kind':kind,'room':rid,'position':xy([x,y])+[z],
            'rotation':rotation,'params':params,'overrides':{},'visible':True,'provenance':{'origin':'reference_layout_design_adaptation','scale':'design_dimensions','geometry':'parametric'}}
        s['entities'][eid]=e
        return e
    for rid,_,poly,_ in specs:
        for name,z,role in [('floor',0,'floor'),('ceiling',3.05,'wall')]:
            e=add(rid,name,'floorplan',0,0,z,points=[xy(pt) for pt in poly],thickness=.12)
            e['surface_role']='stone' if name=='floor' and rid in ('bathroom','bathroom2','bathroom3','powder','laundry') else role
            if name=='ceiling':e['ceiling']=True
    # All shared edges are split at room vertices and emitted once.
    vertices={tuple(p) for _,_,poly,_ in specs for p in poly};edges={}
    for rid,_,poly,_ in specs:
        for a,b in zip(poly,poly[1:]+poly[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1];ll=dx*dx+dy*dy
            cuts=sorted((( ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/ll,p) for p in vertices
                if abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)<1e-7 and -1e-7<=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/ll<=1+1e-7))
            for (_,p),(_,q) in zip(cuts,cuts[1:]):
                if math.dist(p,q)<.001:continue
                key=tuple(sorted((p,q)));edges.setdefault(key,[]).append(rid)
    open_pairs={frozenset(pair) for pair in [('entry','gallery'),('gallery','private_hall'),('gallery','service_hall'),('private_hall','service_hall'),('living','kitchen'),('living','dining'),('kitchen','dining')]}
    # Pairs define actual doors, with centers chosen clear of furniture and art.
    doors={frozenset(pair):(width,at) for pair,width,at in [
        (('gallery','living'),1.45,5.4),(('gallery','kitchen'),1.8,2.5),
        (('gallery','powder'),.9,-1.2),(('private_hall','bedroom'),.9,-6.5),
        (('private_hall','bedroom2'),.95,-4.9),(('private_hall','study'),.95,.3),
        (('private_hall','bathroom2'),.8,-4.7),(('private_hall','bathroom3'),.8,-2.4),
        (('service_hall','linen'),.8,.3),(('service_hall','dressing'),.9,4.1),
        (('dressing','bathroom'),.9,-7.7),(('service_hall','laundry'),.9,-5.8),
        (('service_hall','storage'),.85,-3.1),(('service_hall','utility'),.85,-.35)]}
    portals=[];wall_index=0;window_index={}
    for (a,b),owners in sorted(edges.items()):
        pair=frozenset(owners);dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);rot=math.degrees(math.atan2(dy,dx));mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
        if len(owners)==2 and pair in open_pairs:
            portals.append({'rooms':owners,'center':xy([mx,my]),'width':length*scale,'kind':'open','axis':rot});continue
        opening='solid';gap=off=0;head=2.45;sill=0
        if pair in doors:
            gap,at=doors[pair];opening='door';off=(at-(mx if abs(dx)>abs(dy) else my))*(1 if (dx if abs(dx)>abs(dy) else dy)>0 else -1)
        if len(owners)==1 and owners[0]=='entry' and a[0]==b[0]==1:
            opening='door';gap=1;off=0
        # North facade and sloping east facade; no invented balcony.
        window=len(owners)==1 and (a[1]==b[1]==11 or (a[0]>=8.5 and b[0]>=8.5 and a[1]!=b[1])) and length>1
        if window:opening='window';gap=min(length-.5,4.55);off=0;head=2.85;sill=.35
        rid=owners[0];name=f'wall_{wall_index:02}';wall_index+=1
        params=dict(w=length,h=3.05,thickness=.14,opening=opening)
        if opening!='solid':params.update(gap=gap*scale,offset=off*scale,sill=sill,head=head)
        e=add(rid,name,'wall',mx,my,rotation=rot,**params);e['adjacent_rooms']=owners
        if opening=='door':
            cx,cy=mx+off*dx/length,my+off*dy/length
            portals.append({'rooms':owners if len(owners)==2 else [rid,'outside'],'center':xy([cx,cy]),'width':gap*scale,'kind':'door','wall':e['id'],'axis':rot})
        if window:
            n=window_index.get(rid,0);window_index[rid]=n+1;suffix='' if n==0 else '_'+str(n+1)
            # Determine inward-facing normal from room centroid.
            cc=s['rooms'][rid]['center'];nx,ny=-dy/length,dx/length
            if (cc[0]/scale-mx)*nx+(cc[1]/scale-my)*ny<0:nx,ny=-nx,-ny
            facing=rot if (nx,ny)==(-dy/length,dx/length) else rot+180
            add(rid,'window'+suffix,'window',mx,my,.35,rotation=facing,w=gap,h=2.5)
            add(rid,'sheer'+suffix,'curtain',mx+nx*.18,my+ny*.18,.12,rotation=facing,w=gap+.22,h=2.82,openness=.7,sheer=True)
            add(rid,'drape'+suffix,'curtain',mx+nx*.29,my+ny*.29,.12,rotation=facing,w=gap+.30,h=2.82,openness=.9,sheer=False)
    s['rooms']['service_hall']['label_center']=xy([-3,2.4])
    s['layout']={'design_envelope_m2':267,'outline':[xy(p) for p in outline],'portals':portals,'bedroom_rooms':['bedroom','bedroom2','study'],
        'full_bathrooms':['bathroom','bathroom2','bathroom3'],'powder_room':'powder','scale_factor':scale,'units':'m','north':'+Y'}
    # Furnishing: positions are absolute plan coordinates; major semantic IDs stay stable.
    add('kitchen','back_cabinets','cabinet',4.85,.38,w=2.6,d=.6,h=.9,rotation=180)
    add('kitchen','upper_cabinets','cabinet',4.85,.29,1.8,w=2.6,d=.38,h=.85,rotation=180)
    add('kitchen','island','island',5.15,2.35,w=1,d=2,h=.94,rotation=90)
    add('kitchen','fridge','appliance',6.7,.5,w=.7,d=.65,h=2.2,rotation=180,model='fridge')
    add('kitchen','cooktop','appliance',4.4,.4,.95,w=.7,d=.46,h=.035,model='cooktop')
    add('kitchen','oven','appliance',4.4,.7,.25,w=.6,d=.035,h=.48,model='oven')
    add('kitchen','undercabinet_light','cove',4.85,.6,1.72,w=2.45,power=30,temperature=3500,enabled=True,rotation=180)
    add('dining','table','table',9.35,2.45,w=1.05,d=2.15,h=.76,glass=True,rotation=90)
    for i,(x,y,rot) in enumerate([(8.7,1.38,180),(9.9,1.38,180),(8.7,3.52,0),(9.9,3.52,0),(7.75,2.45,90),(10.95,2.45,-90)]):
        add('dining',f'chair_{i+1}','chair',x,y,rotation=rot,w=.48,d=.52,h=.87)
    add('dining','sideboard','cabinet',9.25,.36,w=2.4,d=.48,h=.8,rotation=180)
    for i in range(3):add('dining',f'picture_{i+1}','art',8.5+i*.72,.10,1.7,w=.54,h=.78,image='botanical',rotation=180)
    add('living','rug','rug',6.35,7.6,.025,w=4.4,d=4.5)
    add('living','sofa','sofa',4.45,7.9,rotation=90,w=3.15,d=1,h=.83)
    add('living','coffee_table','table',6.3,7.7,w=1.35,d=.85,h=.36)
    add('living','media_console','cabinet',8.55,5.15,rotation=180,w=2.5,d=.42,h=.48)
    add('living','screen','appliance',8.55,4.95,.72,rotation=180,w=1.65,d=.05,h=.92,model='screen')
    for i,(x,y,rot) in enumerate([(5.6,9.85,0),(7.6,9.5,-25)]):add('living','lounge_chair' if i==0 else 'lounge_chair_2','chair',x,y,rotation=rot,w=.7,d=.7,h=.86)
    add('living','picture','art',3.10,8,1.7,rotation=90,w=1.8,h=.95,image='abstract')
    add('living','plant','plant',10,5.15,h=1.45)
    for rid,x,w in [('bedroom',-8.5,1.95),('bedroom2',-3.75,1.65),('study',.25,1.5)]:
        add(rid,'bed','bed',x,8.45,w=w,d=2.15,h=.5,rotation=180)
        for i,xx in enumerate([x-w/2-.4,x+w/2+.4]):add(rid,f'bedside_{i+1}','cabinet',xx,7.6,w=.55,d=.48,h=.48)
        add(rid,'rug','rug',x,8.45,.02,w=3.3,d=3.2)
        # Headboards face a solid interior wall, well clear of facade curtains.
        # Beds turned toward windows; back rests on the south room wall.
    add('bedroom','picture','art',-10.90,8,1.7,rotation=90,w=1.3,h=.8,image='coast')
    add('bedroom2','wardrobe','cabinet',-5.55,8.3,rotation=90,w=2.1,d=.55,h=2.5)
    add('study','desk','table',2.4,8.3,rotation=90,w=1.8,d=.65,h=.75)
    add('study','chair','chair',1.65,8.3,rotation=90,w=.52,d=.56,h=.86)
    add('study','books','books',2.4,8.3,.8,w=.5)
    add('study','picture','art',2.9,8.3,1.7,rotation=-90,w=1.2,h=.72,image='abstract')
    add('study','bookcase','cabinet',-1.18,9.5,rotation=90,w=1.5,d=.4,h=2.2,shelves=True)
    add('dressing','wardrobe','cabinet',-10.55,4.8,rotation=90,w=2.6,d=.6,h=2.6)
    add('dressing','wardrobe_2','cabinet',-8.85,6.12,w=2.5,d=.58,h=2.6)
    add('dressing','bench','sofa',-8.7,4.6,w=1.3,d=.55,h=.5)
    add('bathroom','vanity','basin',-10.55,1.5,rotation=90,w=1.65)
    add('bathroom','mirror','mirror',-10.88,1.5,1.7,rotation=90,w=1.55,h=.95)
    add('bathroom','shower','shower',-8.2,.85,w=1.5,d=1.5)
    add('bathroom','toilet','toilet',-8.7,2.65,rotation=0)
    for rid,x in [('bathroom2',-6),('bathroom3',-3.2)]:
        add(rid,'shower','shower',x+.58,3.83,w=.95,d=1.0,rotation=180)
        add(rid,'vanity','basin',x+2.4,4.1,rotation=-90,w=.8)
        add(rid,'mirror','mirror',x+2.68,4.1,1.7,rotation=-90,w=.75,h=.85)
        add(rid,'toilet','toilet',x+1.62,3.62,rotation=180)
    add('powder','vanity','basin',4.6,-2.05,rotation=-90,w=.8)
    add('powder','mirror','mirror',4.87,-2.05,1.65,rotation=-90,w=.75,h=.9)
    add('powder','toilet','toilet',4.1,-.55)
    add('laundry','washer','appliance',-6.25,.48,w=.65,d=.65,h=.85,rotation=180,model='oven')
    add('laundry','dryer','appliance',-5.4,.48,w=.65,d=.65,h=.85,rotation=180,model='oven')
    for rid,x,w in [('storage',-3.1,2.15),('utility',-.4,2.2),('linen',.3,.85)]:add(rid,'storage','cabinet',x,.35 if rid!='linen' else 4.68,w=w,d=.45,h=2.5,rotation=0 if rid=='linen' else 180)
    add('entry','shoe_cabinet','cabinet',2.72,-4.05,rotation=-90,w=1.35,d=.32,h=.95)
    add('entry','mirror','mirror',2.48,-4.05,1.6,rotation=-90,w=.6,h=1.1)
    add('entry','rug','rug',1.9,-4,.02,w=1.25,d=1.5)
    for i,y in enumerate([-2,-.6,.8]):add('gallery',f'picture_{i+1}','art',1.1,y,1.7,rotation=90,w=.85,h=1.15,image='abstract' if i%2 else 'coast')
    # Linear concealed lighting only; no exposed ceiling fixtures.
    for rid,_,poly,_ in specs:
        r=s['rooms'][rid];cx,cy=[v/scale for v in r['center']]
        width=min(5.5,r['size'][0]/scale-.35)
        if rid=='gallery':cx,cy=1.12,1.5;width=5.5;rot=90
        else:cy=min(p[1] for p in poly)+.16;rot=180
        add(rid,'cove_back','cove',cx,cy,2.88,rotation=rot,w=width,power=55,temperature=3000,enabled=True)
    add('living','cove_side','cove',3.16,8.4,2.88,rotation=90,w=4.2,power=50,temperature=3000,enabled=True)
    add('gallery','skirting_light','cove',1.11,.5,.14,rotation=90,w=5.5,power=14,temperature=2700,enabled=True)
    # One distant skyline, never distributed through the interior of adjacent rooms.
    add('living','outside','landscape',0,22,w=36)
    # Purpose-authored realtime cameras; native adapter can adopt these later.
    camera_specs={'living':([9,5.8,1.72],[5.4,8.5,1.1]),'kitchen':([3.7,3.4,1.72],[5.3,.65,1.15]),
        'dining':([8,3.5,1.72],[9.8,1.6,1.05]),'entry':([1.5,-4.6,1.7],[2.05,-2.7,1.2]),
        'gallery':([2,-2.6,1.72],[2,5,1.25]),'bathroom':([-7.7,2.8,1.72],[-10,.9,1.05]),'bathroom2':([-4.7,4.78,1.72],[-4.4,3.8,1]),'bathroom3':([-1.9,4.78,1.72],[-1.6,3.8,1]),'powder':([3.3,-1.1,1.7],[4.4,-1.8,1]),'service_hall':([-6.5,3.7,1.72],[-6.5,4.9,1.1]),'bedroom':([-6.6,7.1,1.72],[-8.8,9.2,1]),
        'bedroom2':([-4.9,7,1.72],[-3.5,9,1]),'study':([1.9,7,1.72],[.1,9,1])}
    for rid,(pos,target) in camera_specs.items():
        s['rooms'][rid]['camera']={'position':xy(pos[:2])+[pos[2]],'target':xy(target[:2])+[target[2]]}
    # A2 keeps the architectural contract frozen; all accessories have independent IDs.
    def detail(e,preset,group,label):
        e.update(detail=preset,semantic_group=group,label=label)
        return e
    detail(add('living','oak_wall_panel','cabinet',3.17,8.3,rotation=90,w=3.6,d=.16,h=2.70),'wall_panel','joinery','客厅木饰面壁板')
    s['entities']['living.picture']['position'][0]=3.31*scale
    for name in ('lounge_chair','lounge_chair_2'):
        e=s['entities']['living.'+name];e['params'].update(w=.88*scale,d=.90*scale,h=.92);detail(e,'lounge','seating','软包休闲椅')
    detail(add('living','reading_books','books',6.05,7.65,.42,w=.48),'stack','books','茶几阅读书籍')
    detail(add('living','tea_service','art',6.72,7.7,.42,w=.5,h=.25,image='abstract'),'tea_service','tableware','茶盘与杯壶')
    throw=detail(add('living','throw','rug',4.75,8.55,.53,rotation=90,w=.78,d=.86),'throw','textiles','沙发搭毯')
    seat_depth=s['entities']['living.sofa']['params']['d']-.18
    throw['support_entity']='living.sofa'
    throw['drape_profile']={'axis':'y','flat_min':-.07-seat_depth/2+.30*scale,'flat_max':1,'radius':.035,'role':'accent'}
    add('living','side_table','table',4.48,5.8,w=.56,d=.56,h=.52)
    detail(add('living','vase','plant',4.48,5.8,.56,h=.54),'flowers','botanical','边几花器与枝花')
    for i,(x,y,rot) in enumerate([(8.7,2.10,0),(9.9,2.10,0),(8.7,2.80,180),(9.9,2.80,180),(8.45,2.45,-90),(10.25,2.45,90)]):
        detail(add('dining',f'place_setting_{i+1}','art',x,y,.80,rotation=rot,w=.265,h=.23,image='abstract'),'table_setting','tableware','餐位 '+str(i+1)+' / 盘杯餐巾与餐具')
    detail(add('dining','centerpiece','plant',9.35,2.45,.80,h=.46),'flowers','botanical','餐桌低花器')
    detail(add('dining','ceramic_vase','art',9.8,.38,.85,w=.22,h=.36,image='abstract'),'ceramic_vessel','ceramics','餐边柜陶瓶')
    detail(add('dining','sideboard_books','books',8.6,.38,.85,w=.52),'stack','books','餐边柜艺术书')
    detail(add('kitchen','herbs','plant',3.78,.4,.96,h=.38),'flowers','botanical','料理台香草花器')
    detail(add('kitchen','canisters','art',5.65,.4,.96,w=.42,h=.24,image='abstract'),'toiletries','counter_storage','料理台收纳瓶罐')
    for rid,x in [('bedroom',-8.5),('bedroom2',-3.75),('study',.25)]:
        bed=s['entities'][rid+'.bed'];bed['detail']='tailored_bed'
        cover=detail(add(rid,'coverlet','rug',x,9.08,.67,rotation=180,w=bed['params']['w']/scale+.48,d=.60),'throw','textiles','床尾织物搭毯')
        edge=(bed['params']['w']+.015)/2
        cover['support_entity']=bed['id']
        cover['drape_profile']={'axis':'x','flat_min':-edge,'flat_max':edge,'radius':.025,'role':'accent'}
        detail(add(rid,'bedside_books','books',x-1.37 if rid=='bedroom' else x-1.23 if rid=='bedroom2' else x-1.15,7.6,.52,w=.30),'stack','books','床头阅读书籍')
    detail(add('study','desk_vessel','art',2.4,8.9,.80,w=.16,h=.19,image='abstract'),'ceramic_vessel','ceramics','书桌笔器')
    detail(add('entry','key_tray','art',2.72,-4.05,1.00,rotation=90,w=.30,h=.16,image='abstract'),'key_tray','arrival','入户钥匙托盘')
    detail(add('gallery','end_plant','plant',2.55,3.95,h=1.15),'flowers','botanical','画廊转角枝花')
    for rid,x,y,rot in [('bathroom',-10.55,1.9,90),('bathroom2',-3.6,4.1,-90),('bathroom3',-.8,4.1,-90),('powder',4.6,-2.05,-90)]:
        detail(add(rid,'towels','rug',x,y,.91,rotation=rot,w=.36,d=.30),'folded_towels','bath_linen','叠放手巾')
        # On a side shelf, separate from the basin bowl and faucet.
        xx,yy=(x,y-.85) if rid=='bathroom' else (x,y+.37)
        detail(add(rid,'care_set','art',xx,yy,1.28,rotation=rot,w=.34,h=.23,image='abstract'),'toiletries','bath_accessories','洗护瓶组')
        e=add(rid,'care_shelf','cabinet',xx,yy,1.02,rotation=rot,w=.48,d=.23,h=.2);e['label']='洗护壁龛搁板'
    detail(add('dressing','folded_linen','rug',-8.7,4.6,.60,w=.65,d=.34),'folded_towels','textiles','衣帽间换洗织物')
    detail(add('laundry','basket','cabinet',-4.78,.5,w=.48,d=.45,h=.48),'basket','laundry','洗衣篮')
    for eid in ('laundry.washer','laundry.dryer'):detail(s['entities'][eid],'laundry_appliance','laundry','洗衣机' if eid.endswith('washer') else '烘干机')
    s['provenance']['finish_notes']='A2: editable functional arrangements, upholstered seating, tailored bed linen, layered rugs, flowers/books/tableware/bath storage; procedural city is not a geographic Manhattan view.'
    return validate(s)
