"""Original parametric residential kit, shared by browser and Blender backends."""
import math
from core import palette, digest, validate, surface_profile

def kit_demo():
    s={'schema':'room-studio/1','revision':0,'name':'Quiet House / 静居','style':'warm','period':'day','environment':'city','rooms':{},'entities':{},'history':[],'redo':[],
       'provenance':{'origin':'designed_example','scale':'design_dimensions','notes':'Original procedural residence; warm wood/metal/glass language inspired by the existing kitchen study. New rooms are design examples, not reconstruction of private photos.'}}
    specs=[('kitchen','厨房',-6,-2.5),('dining','餐厅',-2,-2.5),('living','客厅',2,-2.5),('balcony','阳台',6,-2.5),('bedroom','卧室',-6,2.5),('study','书房',-2,2.5),('bathroom','卫浴',2,2.5),('entry','玄关',6,2.5)]
    def add(room,name,kind,x,y,z=0,rotation=0,**params):
        cx,cy=s['rooms'][room]['center'];eid=room+'.'+name
        s['entities'][eid]={'id':eid,'label':name.replace('_',' '),'kind':kind,'room':room,'position':[cx+x,cy+y,z],'rotation':rotation,'params':params,'overrides':{},'visible':True,'provenance':{'origin':'designed_example','geometry':'parametric','scale':'design_dimensions'}}
        return eid
    for rid,label,x,y in specs:
        s['rooms'][rid]={'name':label,'center':[x,y],'size':[4,5,2.8],'style':None}
        add(rid,'floor','rug',0,0,-.09,w=3.95,d=4.95)
        s['entities'][rid+'.floor']['surface_role']='floor'
        add(rid,'ceiling','rug',0,0,2.86,w=4,d=5)
        s['entities'][rid+'.ceiling']['surface_role']='wall'
        s['entities'][rid+'.ceiling']['ceiling']=True
        # Each shared boundary is authored once, with actual doorway geometry.
        for edge in ['N','E']+(['S'] if y<0 else [])+(['W'] if x==-6 else []):
            opening='door' if (edge=='N' and y<0) or (edge=='E' and x<6) else 'window'
            if rid=='entry' and edge=='N':opening='door'
            if rid=='balcony' and edge=='S':
                add(rid,'balustrade','rail',0,-2.46,w=3.8);continue
            add(rid,'wall_'+edge,'shell',0,0,w=4,d=5,h=2.8,edge=edge,opening=opening)
        if rid!='balcony':
            outside_y=2.44 if y>0 else -2.44;rot=0 if y>0 else 180
            if rid!='entry':
                add(rid,'window','window',0,outside_y,.65,rotation=rot,w=2.55,h=1.8)
                add(rid,'sheer','curtain',0,outside_y-(.12 if y>0 else -.12),.16,rotation=rot,w=3,h=2.4,openness=.7,sheer=True)
                add(rid,'drape','curtain',0,outside_y-(.2 if y>0 else -.2),.16,rotation=rot,w=3.2,h=2.4,openness=.9,sheer=False)
        add(rid,'outside','landscape',0,3.7 if y>0 else -3.7,0,rotation=0 if y>0 else 180)
        if rid!='balcony':
            add(rid,'cove_back','cove',0,2.46,2.62,w=3.55,power=50,temperature=3000,enabled=True)
            add(rid,'cove_side','cove',-1.96,0,2.58,rotation=90,w=3.4,power=45,temperature=3000,enabled=True)
            add(rid,'skirting_light','cove',0,2.46,.12,w=3.4,power=12,temperature=2700,enabled=True)
    add('kitchen','back_cabinets','cabinet',-.6,1.98,w=2.4,d=.62,h=.9)
    add('kitchen','upper_cabinets','cabinet',-.6,2.1,1.75,w=2.4,d=.38,h=.72)
    add('kitchen','side_shelves','cabinet',-1.65,.7,rotation=90,w=1.6,d=.45,h=2.35,shelves=True)
    add('kitchen','island','island',.2,-.35,w=1,d=2,h=.94)
    add('kitchen','fridge','appliance',-1.6,-1.7,w=.7,d=.65,h=2.2,model='fridge')
    add('kitchen','cooktop','appliance',-.6,1.96,.95,w=.7,d=.46,h=.035,model='cooktop')
    add('kitchen','oven','appliance',-.6,1.64,.25,w=.6,d=.035,h=.48,model='oven')
    add('kitchen','undercabinet_light','cove',0,1.85,1.7,w=3.4,power=22,temperature=3500,enabled=True)
    add('dining','table','table',0,-.1,w=1.05,d=2.35,h=.76,glass=True)
    for i,(x,y) in enumerate([(-.9,-.7),(-.9,.6),(.9,-.7),(.9,.6)]):add('dining',f'chair_{i+1}','chair',x,y,rotation=90 if x<0 else -90,w=.48,d=.52,h=.87)
    add('dining','sideboard','cabinet',-.6,2.05,w=2.4,d=.5,h=.8)
    for i in range(3):add('dining',f'picture_{i+1}','art',-1.3+i*.7,2.41,1.55,w=.54,h=.78,image='botanical')
    add('dining','vase_plant','plant',0,2.02,.83,h=.62)
    add('living','rug','rug',0,-.1,.015,w=2.9,d=3.1)
    add('living','sofa','sofa',-.45,1.45,w=2.4,d=.98,h=.83)
    add('living','coffee_table','table',0,-.15,w=1.25,d=.75,h=.36)
    add('living','media_console','cabinet',1.58,-.2,rotation=-90,w=2.2,d=.4,h=.48)
    add('living','screen','appliance',1.86,-.2,.75,rotation=-90,w=1.55,d=.05,h=.87,model='screen')
    add('living','lounge_chair','chair',-1.25,-.8,rotation=-20,w=.65,d=.65,h=.82)
    add('living','picture','art',-.55,2.41,1.6,w=1.65,h=.78,image='abstract')
    add('living','plant','plant',-1.45,1.9,h=1.45)
    add('bedroom','bed','bed',0,.6,w=1.8,d=2.15,h=.5)
    for i,x in enumerate([-1.38,1.38]):add('bedroom',f'bedside_{i+1}','cabinet',x,1.35,w=.55,d=.5,h=.48)
    add('bedroom','wardrobe','cabinet',-1.65,-.7,rotation=90,w=2.15,d=.58,h=2.45)
    add('bedroom','rug','rug',.25,.1,.015,w=2.8,d=3.1)
    add('bedroom','picture','art',1.9,1.25,1.68,rotation=-90,w=1.25,h=.63,image='coast')
    add('study','desk','table',0,1.05,w=2.1,d=.8,h=.75)
    add('study','chair','chair',0,.1,w=.57,d=.6,h=.9)
    add('study','bookcase','cabinet',-1.65,0,rotation=90,w=2.5,d=.4,h=2.2,shelves=True)
    add('study','books','books',-.4,1.05,.8,w=.55)
    add('study','picture','art',1.9,1.25,1.55,rotation=-90,w=.68,h=.85,image='abstract')
    add('study','plant','plant',1.45,1.9,h=1.1)
    add('bathroom','vanity','basin',-.4,1.65,w=1.5)
    add('bathroom','mirror','mirror',-.4,2.39,1.6,w=1.4,h=.95)
    add('bathroom','shower','shower',1.12,-1.35,w=1.45,d=1.65)
    add('bathroom','toilet','toilet',-1.15,-.6)
    add('bathroom','niche_light','cove',-.4,2.25,2.2,w=1.4,power=24,temperature=3500,enabled=True)
    add('entry','shoe_cabinet','cabinet',-1.6,.1,rotation=90,w=2.5,d=.5,h=2.25)
    add('entry','bench','sofa',-.1,1.4,w=1.4,d=.55,h=.5)
    add('entry','mirror','mirror',-.1,2.4,1.55,w=.65,h=1.2)
    add('entry','rug','rug',.2,-.5,.015,w=1.6,d=2.5)
    add('entry','picture','art',1.88,-.6,1.6,rotation=-90,w=.75,h=.95,image='abstract')
    add('balcony','table','table',0,.2,w=.7,d=.7,h=.55)
    for i,x in enumerate([-1,1]):add('balcony',f'chair_{i+1}','chair',x,.1,rotation=90 if x<0 else -90,w=.6,d=.6,h=.8)
    add('balcony','plant_1','plant',-1.35,1.8,h=1.5)
    add('balcony','plant_2','plant',1.3,-1.7,h=.9)
    return validate(s)

def parts(s,e):
    """Return local-space editable primitive descriptors with stable member IDs."""
    if e['kind'].startswith('jp_'):
        from japanese_parts import parts as japanese_parts
        return japanese_parts(s,e)
    p=e['params'];k=e['kind'];a=[]
    def shape(name,loc,size,role='wood',kind='box',**extra):
        a.append({'id':e['id']+'/'+name,'position':list(loc),'size':list(size),'role':role,'shape':kind,**extra})
    def box(n,x,y,z,w,d,h,role='wood',**kw):shape(n,(x,y,z),(w,d,h),role,**kw)
    w=p.get('w',1);d=p.get('d',1);h=p.get('h',1)
    detail=e.get('detail')
    def vessel(name,x,y,z,width,height,role='ceramic'):
        # Revolved, hollow vessel with an actual rim and interior surface.
        profile=[(0,0),(.30,.015),(.43,.08),(.50,.35),(.42,.70),(.24,.90),(.24,1),(.20,1),(.20,.91),(.36,.69),(.43,.35),(.35,.10),(0,.08)]
        verts=[[x+width*r*math.cos(i*math.tau/32),y+width*r*math.sin(i*math.tau/32),z+height*hh] for r,hh in profile for i in range(32)]
        faces=[]
        for j in range(len(profile)-1):
            for i in range(32):
                a=j*32+i;b=j*32+(i+1)%32;c=b+32;dd=a+32;faces.extend([[a,b,c],[a,c,dd]])
        shape(name,(0,0,0),(1,1,1),role,'mesh',vertices=verts,faces=faces)
    if detail in ('table_setting','ceramic_vessel','toiletries','tea_service','key_tray') and k=='art':
        if detail=='ceramic_vessel':vessel('ceramic_vessel',0,0,0,w,h)
        elif detail=='table_setting':
            shape('dinner_plate',(0,0,.014),(w,w,.025),'ceramic','cylinder')
            shape('plate_well',(0,0,.028),(w*.76,w*.76,.012),'white','cylinder')
            box('linen_napkin',0,0,.045,w*.40,w*.65,.022,'fabric',roundness=.012)
            for side in [-1,1]:
                box('cutlery_'+str(side),side*w*.68,0,.016,.012,w*.70,.012,'metal',roundness=.005)
                if side<0:
                    for j in range(3):box('fork_tine_'+str(j),side*w*.68+(j-1)*.006,w*.37,.016,.003,.045,.008,'metal')
            vessel('water_glass',w*.57,w*.65,.01,w*.26,h*.75,'glass')
        elif detail=='toiletries':
            box('stone_tray',0,0,.015,w,.18,.03,'stone',roundness=.018)
            for i in range(3):
                x=(i-1)*w*.27;hh=h*(.65+i*.14)
                shape('bottle_'+str(i),(x,0,hh/2+.04),(w*.19,w*.19,hh),'glass' if i==1 else 'ceramic','cylinder')
                box('label_'+str(i),x,-w*.10,hh*.55,.04,.005,.05,'paper')
                shape('cap_'+str(i),(x,0,hh+.04),(w*.12,w*.12,.03),'metal','cylinder')
        elif detail=='key_tray':
            shape('dish',(0,0,.015),(w,w*.65,.03),'stone','cylinder')
            box('leather_fob',0,0,.045,w*.21,w*.32,.018,'accent',roundness=.015)
            for i in range(3):box('key_'+str(i),w*.1+i*.023,.015,.05,.016,w*.27,.008,'metal')
        else:
            box('tray',0,0,.02,w,w*.6,.04,'wood',roundness=.025)
            vessel('tea_pot',-.12,0,.045,w*.34,h*.7)
            for i in [-1,1]:vessel('tea_cup_'+str(i),w*.25,i*w*.15,.045,w*.18,h*.35)
        return a
    if k=='books' and detail=='stack':
        for i in range(4):
            box('cover_'+str(i),(i%2)*.025,0,.025+i*.035,w*(1-i*.035),w*.65,.031,'accent' if i%2 else 'frame',roundness=.004)
            box('pages_'+str(i),(i%2)*.025,-.002,.025+i*.035,w*(1-i*.035)-.012,w*.65-.01,.023,'paper')
        return a
    if k=='cabinet' and detail=='wall_panel':
        box('backing',0,0,h/2,w,d,h,'wood',roundness=.003)
        count=max(2,round(w/.60))
        for i in range(count+1):box('reveal_'+str(i),-w/2+i*w/count,-d/2-.003,h/2,.008,.006,h-.02,'frame')
        box('shadow_base',0,-d/2-.005,.045,w,.009,.075,'metal')
        box('top_cap',0,-d/2-.004,h-.01,w,.012,.025,'frame')
        return a
    if k=='cabinet' and detail=='basket':
        box('base',0,0,.03,w,d,.055,'fabric',roundness=.02)
        for x in [-w/2,w/2]:box('side_'+str(x),x,0,h/2,.025,d,h,'fabric',roundness=.012)
        for y in [-d/2,d/2]:
            box('panel_'+str(y),0,y,h/2,w,.025,h,'fabric',roundness=.012)
            for j in range(7):box('woven_'+str(y)+'_'+str(j),0,y-.016,.05+j*(h-.09)/6,w-.02,.008,.008,'wood')
        return a
    if k=='rug' and detail in ('folded_towels','throw'):
        if detail=='throw':
            # Material coordinates fold around the support edge; excess cloth falls
            # vertically instead of continuing as a rigid plane in free space.
            profile=e.get('drape_profile',{});axis=profile.get('axis','y')
            radius=profile.get('radius',.065);lo=profile.get('flat_min',-d/2);hi=profile.get('flat_max',d/2)
            along=w if axis=='x' else d;across=d if axis=='x' else w
            coords={-along/2+i*along/40 for i in range(41)}
            for edge,sign in [(lo,-1),(hi,1)]:
                for i in range(13):
                    u=edge+sign*radius*math.pi/2*i/12
                    if -along/2<=u<=along/2:coords.add(u)
            coords=sorted(coords);cols=25;verts=[]
            for u in coords:
                for j in range(cols):
                    v=(-.5+j/(cols-1))*across;uu=u;drop=0;hanging=0
                    if u<lo or u>hi:
                        edge,sign=(lo,-1) if u<lo else (hi,1);distance=abs(u-edge)
                        angle=min(math.pi/2,distance/radius)
                        uu=edge+sign*radius*math.sin(angle)
                        drop=radius*(1-math.cos(angle))+max(0,distance-radius*math.pi/2)
                        hanging=min(1,drop/.1)
                        uu+=sign*.006*math.sin(v*26)*hanging
                    # 2–6 mm of soft folds rest on the nominal cushion/duvet top.
                    zz=.002+.004*(.5+.5*math.sin(v*23+u*8))-drop
                    verts.append([uu,v,zz] if axis=='x' else [v,uu,zz])
            rows=len(coords);count=len(verts);top_faces=[]
            for i in range(rows-1):
                for j in range(cols-1):
                    t=i*cols+j
                    tri=[[t,t+1,t+cols+1],[t,t+cols+1,t+cols]]
                    top_faces.extend([list(reversed(f)) for f in tri] if axis=='x' else tri)
            # A closed 1.5 mm textile shell gives native export real edge thickness.
            normals=[[0.,0.,0.] for _ in verts]
            for f in top_faces:
                aa,bb,cc=[verts[k] for k in f];ab=[bb[k]-aa[k] for k in range(3)];ac=[cc[k]-aa[k] for k in range(3)]
                nn=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
                for index in f:
                    for k in range(3):normals[index][k]+=nn[k]
            for index in range(count):
                nn=normals[index];length=math.sqrt(sum(x*x for x in nn)) or 1
                verts.append([verts[index][k]-.0015*nn[k]/length for k in range(3)])
            faces=top_faces+[[c+count,b+count,a+count] for a,b,c in top_faces]
            boundary=list(range(cols))+[i*cols+cols-1 for i in range(1,rows)]+list(range((rows-1)*cols+cols-2,(rows-1)*cols-1,-1))+[i*cols for i in range(rows-2,0,-1)]
            for ia,ib in zip(boundary,boundary[1:]+boundary[:1]):faces.extend([[ia,ib,ib+count],[ia,ib+count,ia+count]])
            shape('woven_cloth',(0,0,0),(1,1,1),profile.get('role','fabric'),'mesh',vertices=verts,faces=faces,textile=True)
            return a
        layers=3
        for i in range(layers):box('fold_'+str(i),i*.006,0,.025+i*.035,w,d,.04,'white' if i%2 else 'fabric',roundness=.015)
        for i in range(7):box('woven_edge_'+str(i),-w/2+.03+i*(w-.06)/6,-d/2+.025,.048+(layers-1)*.035,.012,.04,.005,'accent')
        return a
    if k=='shell':
        edge=p['edge'];length=w if edge in ('N','S') else d;opening=p['opening']
        def wall(n,u,z,ln,hh):
            loc=(u,d/2 if edge=='N' else -d/2,z) if edge in ('N','S') else (w/2 if edge=='E' else -w/2,u,z)
            size=(ln,.12,hh) if edge in ('N','S') else (.12,ln,hh)
            shape(n,loc,size,'wall',structural=True)
        gap=1.05 if opening=='door' else 2.65
        if opening=='solid':wall('solid',0,h/2,length,h)
        else:
            offset=1.35 if opening=='door' and edge in ('N','S') else 0
            left=length/2+offset-gap/2;right=length/2-offset-gap/2
            wall('pier_-1',-length/2+left/2,h/2,left,h)
            wall('pier_1',length/2-right/2,h/2,right,h)
            top=2.18 if opening=='door' else 2.5
            wall('lintel',offset,(top+h)/2,gap,h-top)
            if opening=='window':wall('sill',0,.3,gap,.6)
    elif k=='wall':
        thick=p['thickness'];opening=p['opening']
        def wall(n,x,z,width,height):
            if width>.001 and height>.001:
                box(n,x,0,z,width,thick,height,'wall',structural=True)
                if z-height/2<.001:
                    for side in [-1,1]:box(n+'_skirting_'+str(side),x,side*(thick/2+.009),.055,width,.018,.11,'wood',structural=True)
        if opening=='solid':wall('solid',0,h/2,w,h)
        else:
            gap=p['gap'];off=p['offset'];left=w/2+off-gap/2;right=w/2-off-gap/2
            wall('pier_left',-w/2+left/2,h/2,left,h);wall('pier_right',w/2-right/2,h/2,right,h)
            wall('lintel',off,(h+p['head'])/2,gap,h-p['head'])
            wall('sill',off,p['sill']/2,gap,p['sill'])
            if opening=='door':
                for side in [-1,1]:box('jamb_'+str(side),off+side*(gap/2+.014),0,p['head']/2,.028,thick+.035,p['head'],'frame',structural=True)
                box('door_head_trim',off,0,p['head']+.016,gap+.055,thick+.035,.032,'frame',structural=True)
    elif k=='floorplan':
        pts=p['points'];th=p.get('thickness',.1);n=len(pts);tri=triangulate(pts)
        verts=[[x,y,z] for z in [-th,0] for x,y in pts]
        faces=[[a+n,b+n,c+n] for a,b,c in tri]+[[c,b,a] for a,b,c in tri]
        for i in range(n):
            j=(i+1)%n;faces.extend([[i,j,j+n],[i,j+n,i+n]])
        shape('surface',(0,0,0),(1,1,1),e.get('surface_role','floor'),'mesh',vertices=verts,faces=faces,structural=bool(e.get('ceiling')),ceiling=bool(e.get('ceiling')))
    elif k=='rug':
        box('surface',0,0,0,w,d,.06 if e.get('ceiling') else .035,e.get('surface_role','fabric'),structural=bool(e.get('ceiling')),ceiling=bool(e.get('ceiling')))
        if not e.get('ceiling') and 'surface_role' not in e:
            for side in [-1,1]:
                box('bound_long_'+str(side),side*(w/2-.055),0,.02,.045,d-.04,.006,'accent')
                box('bound_short_'+str(side),0,side*(d/2-.055),.02,w-.08,.045,.006,'accent')
            for i in range(30):box('weave_'+str(i),0,-d/2+.11+(d-.22)*i/29,.02,w-.19,.008,.003,'fabric')
    elif k in ('table','chair','sofa','bed','cabinet'):
        if k=='table':
            box('top',0,0,h,w,d,.055,'glass' if p.get('glass') else 'wood')
            for i,x in enumerate([-w*.36,w*.36]):
                for j,y in enumerate([-d*.35,d*.35]):box(f'leg_{i}_{j}',x,y,h/2,.065,.065,h,'wood')
        elif k=='chair' and detail=='lounge':
            box('plinth',0,0,.17,w*.72,d*.72,.16,'wood',roundness=.06)
            box('seat',0,-.05,.40,w-.08,d-.10,.22,'fabric',roundness=.095)
            box('back',0,d*.33,.66,w,.22,h*.55,'fabric',roundness=.10)
            for i,x in enumerate([-w/2+.08,w/2-.08]):box('arm_'+str(i),x,0,.53,.16,d,.36,'fabric',roundness=.07)
            box('lumbar',0,d*.13,.59,w*.62,.19,.23,'accent',roundness=.08)
        elif k=='chair':
            box('seat',0,0,.45,w,d,.12,'fabric',roundness=.05)
            box('back',0,d*.42,.68,w,.085,max(.15,h-.45),'wood',roundness=.025)
            for i,x in enumerate([-w*.36,w*.36]):
                for j,y in enumerate([-d*.32,d*.32]):box(f'leg_{i}_{j}',x,y,.22,.038,.038,.44,'metal')
        elif k=='sofa':
            box('base',0,0,.24,w,d,.28,'wood',roundness=.04)
            count=max(2,round(w/.95))
            for i in range(count):
                xx=-w/2+.14+(i+.5)*(w-.28)/count
                box('seat_'+str(i),xx,-.07,.43,(w-.28)/count-.018,d-.18,.2,'fabric',roundness=.07)
                box('back_cushion_'+str(i),xx,d*.25,h*.72,(w-.28)/count-.025,.23,.36,'fabric',roundness=.075)
            for i,x in enumerate([-w*.38,w*.38]):
                for j,y in enumerate([-d*.3,d*.3]):box('foot_'+str(i)+'_'+str(j),x,y,.065,.055,.055,.13,'metal')
            box('back',0,d*.37,h*.72,w,.2,max(.15,h*.5),'fabric',roundness=.06)
            for i,x in enumerate([-w/2+.09,w/2-.09]):box(f'arm_{i}',x,0,h*.62,.18,d,max(.2,h*.42),'fabric',roundness=.05)
            for i,x in enumerate([-w*.28,w*.28]):box(f'pillow_{i}',x,d*.21,h*.76,w*.21,.22,.28,'accent',roundness=.065)
        elif k=='bed':
            box('frame',0,0,.2,w+.1,d+.1,.3)
            box('mattress',0,-.02,.45,w,d,.26,'white',roundness=.08)
            box('duvet',0,-d*.13,.61,w+.015,d*.7,.12,'fabric',roundness=.05)
            box('headboard',0,d*.5,.65,w+.2,.12,1.1,'wood',roundness=.035)
            for i in range(5):box('headboard_pad_'+str(i),-w/2+(i+.5)*w/5,d*.5-.076,.79,w/5-.018,.055,.72,'fabric',roundness=.022)
            if detail!='tailored_bed':box('folded_coverlet',0,-d*.28,.69,w+.03,d*.22,.065,'accent',roundness=.03)
            for i in range(13):box('quilt_seam_'+str(i),-w/2+.035+i*(w-.07)/12,d*.04 if detail=='tailored_bed' else -d*.15,.676,.006,d*(.34 if detail=='tailored_bed' else .62),.008,'white')
            for i,x in enumerate([-w*.25,w*.25]):
                box(f'pillow_{i}',x,d*.3,.67,w*.4,.45,.18,'white',roundness=.07)
                box(f'cushion_{i}',x,d*.15,.72,w*.31,.32,.13,'fabric',roundness=.06)
        else:
            if p.get('shelves'):
                box('back',0,d*.44,h/2,w,.05,h)
                for i,x in enumerate([-w/2+.025,w/2-.025]):box(f'side_{i}',x,0,h/2,.05,d,h)
                for i in range(6):box(f'shelf_{i}',0,0,.04+i*(h-.08)/5,w,d,.035)
                for i in range(4):
                    for j in range(4):box(f'book_{i}_{j}',-w*.32+j*.09,0,.15+i*h/5,.06,d*.65,h*.12,'accent' if j%2 else 'paper')
            else:
                box('body',0,0,h/2,w,d,h)
                box('top',0,0,h+.015,w+.03,d+.03,.035,'stone')
                n=max(1,round(w/.6))
                for i in range(n):
                    x=-w/2+(i+.5)*w/n
                    box(f'door_{i}',x,-d/2-.015,h/2,w/n-.012,.025,h-.07)
                    box(f'pull_{i}',x,-d/2-.033,h*.78,w/n*.4,.018,.013,'metal')
                box('plinth',0,-d*.46,.045,w*.94,.025,.09,'metal')
                for x in [-w/2+.02,w/2-.02]:box('end_trim_'+str(x),x,-d/2-.025,h/2,.018,.03,h-.06,'frame')
                if detail=='towel_shelf':
                    for j in range(3):box('folded_towel_'+str(j),-.1,0,h+.055+j*.045,w*.62,d*.72,.055,'white' if j%2 else 'fabric',roundness=.02)
    elif k=='island':
        box('body',0,0,h*.46,w,d,h*.92)
        # Counter opening is represented by four solids around a real recessed basin.
        sw=min(.46,w*.5);sd=.52;sy=d*.21;z=h
        box('counter_left',-(w+sw)/4,0,z,(w-sw)/2,d+.06,.05,'metal')
        box('counter_right',(w+sw)/4,0,z,(w-sw)/2,d+.06,.05,'metal')
        front=(d/2+sy-sd/2);back=d/2-sy-sd/2
        box('counter_front',0,-d/2+front/2,z,sw,front,.05,'metal')
        box('counter_back',0,d/2-back/2,z,sw,back,.05,'metal')
        # Recess starts above body; no false measurement claim.
        box('basin_inner',0,sy,h-.07,sw*.94,sd*.94,.018,'metal')
        for i,x in enumerate([-sw/2,sw/2]):box(f'basin_side_{i}',x,sy,h-.025,.014,sd,.09,'metal')
        for i,y in enumerate([sy-sd/2,sy+sd/2]):box(f'basin_end_{i}',0,y,h-.025,sw,.014,.09,'metal')
        box('basin_lip',0,sy+sd/2,h+.03,sw,.018,.035,'metal')
        shape('tap_stem',(sw*.32,sy+sd*.7,h+.17),(.025,.025,.34),'metal','cylinder')
        box('tap_spout',sw*.32,sy+sd*.52,h+.33,.025,.23,.025,'metal')
        for i in range(3):box(f'front_panel_{i}',-w/2+(i+.5)*w/3,-d/2-.018,h*.46,w/3-.012,.025,h*.86)
    elif k=='appliance':
        model=p['model'];box('body',0,0,h/2,w,d,h,'metal')
        if detail=='laundry_appliance':
            box('front',0,-d/2-.012,h/2,w-.02,.024,h-.02,'white')
            # Drum on the front: mesh ring lies in XZ, sharing both backends.
            verts=[];faces=[]
            for rr in [.23,.18]:
                for i in range(48):verts.append([rr*math.cos(i*math.tau/48),-d/2-.035,h*.43+rr*math.sin(i*math.tau/48)])
            for i in range(48):j=(i+1)%48;faces.extend([[i,j,j+48],[i,j+48,i+48]])
            shape('drum_ring',(0,0,0),(1,1,1),'metal','mesh',vertices=verts,faces=faces)
            box('drum_glass',0,-d/2-.03,h*.43,.33,.018,.33,'screen',roundness=.13)
            box('controls',0,-d/2-.03,h*.86,w*.8,.018,.07,'metal')
        elif model=='fridge':
            box('door',0,-d/2-.015,h/2,w-.025,.025,h-.025,'screen')
            box('split',0,-d/2-.032,h*.36,w,.012,.012,'metal')
            box('handle',w*.35,-d/2-.05,h*.65,.025,.045,.45,'metal')
        elif model=='cooktop':
            box('glass',0,0,h+.004,w,d,.008,'screen')
            for i,x in enumerate([-w*.26,w*.26]):
                for j,y in enumerate([-d*.25,d*.25]):shape(f'burner_{i}_{j}',(x,y,h+.012),(.15,.15,.008),'metal','cylinder')
        else:
            box('screen',0,-d/2-.006,h/2,w-.035,.012,h-.035,'screen')
            if model=='oven':box('handle',0,-d/2-.028,h*.8,w*.7,.035,.018,'metal')
    elif k=='window':
        for i,x in enumerate([-w/2,0,w/2]):box(f'mullion_{i}',x,0,h/2,.04,.065,h,'metal')
        for i,z in enumerate([0,h]):box(f'frame_{i}',0,0,z,w,.065,.045,'metal')
        box('glass',0,0,h/2,w,.014,h,'glass')
    elif k=='curtain':
        op=p['openness'];panel=w*(.5-.4*op);sheer=p.get('sheer',False)
        for side in [-1,1]:
            verts=[];faces=[];steps=48
            center=side*(w/2-panel/2)
            for i in range(steps+1):
                x=center-panel/2+panel*i/steps;y=.055*math.cos(i/steps*math.pi*16)
                verts.extend([[x,y,0],[x,y,h]])
            for i in range(steps):faces.extend([[i*2,i*2+1,i*2+3],[i*2,i*2+3,i*2+2]])
            shape('panel_'+str(side),(0,0,0),(1,1,1),'white' if sheer else 'fabric','mesh',vertices=verts,faces=faces,sheer=sheer)
        box('hidden_track',0,0,h+.025,w+.05,.06,.045,'metal')
    elif k=='art':
        box('back',0,0,0,w,.04,h,'frame')
        box('paper',0,-.026,0,w-.065,.012,h-.065,'paper')
        design=p.get('image','abstract')
        for i in range(5):
            x=(i%3-1)*w*.2;z=(i/4-.5)*h*.6
            if design=='botanical':
                box(f'stem_{i}',x,-.038,z,.008,.008,h*.3,'leaf')
                shape(f'leaf_{i}',(x+.035,-.045,z+h*.06),(w*.13,.012,h*.09),'leaf','sphere')
            elif design=='coast':box(f'sea_{i}',0,-.04-i*.002,(i-2)*h*.13,w*.8,.012,h*.12,'accent' if i<3 else 'white')
            else:shape(f'motif_{i}',(x,-.044-i*.003,z),(w*.27,.012,h*.2),'accent' if i%2 else 'wood','sphere')
    elif k=='cove':
        power=p.get('power',45) if p.get('enabled',True) else 0
        if s['period']=='day':power*=.13
        box('recess',0,.02,0,w,.065,.035,'wall',structural=True)
        box('diffuser',0,-.018,-.012,w-.04,.025,.01,'light',emission=power/12,temperature=p.get('temperature',3000))
        shape('source',(0,-.09,-.06),(w,.35,1),'light','light',power=power,temperature=p.get('temperature',3000),target=[0,-.6,-1])
    elif k=='plant' and detail=='flowers':
        vessel('vase',0,0,0,h*.32,h*.46)
        for i in range(7):
            angle=i*2.4;x=h*.18*math.cos(angle);y=h*.18*math.sin(angle);z=h*(.75+(i%3)*.09)
            shape('stem_'+str(i),(x*.45,y*.45,z*.6),(.012,.012,z*.8),'leaf','cylinder')
            shape('flower_'+str(i),(x,y,z),(h*.16,h*.16,h*.13),'white' if i%2 else 'accent','sphere')
        return a
    elif k=='plant':
        shape('pot',(0,0,h*.15),(h*.29,h*.29,h*.3),'stone','cylinder')
        shape('stem',(0,0,h*.55),(.022,.022,h*.7),'wood','cylinder')
        for i in range(7):
            angle=i*2.4;r=h*.18
            shape(f'leaf_{i}',(r*math.cos(angle),r*math.sin(angle),h*(.45+i*.07)),(h*.22,h*.13,h*.17),'leaf','sphere')
    elif k=='basin':
        box('cabinet',0,0,.4,w,.52,.7)
        box('counter',0,0,.79,w+.04,.57,.07,'stone')
        shape('bowl',(0,0,.86),(.48,.34,.13),'ceramic','sphere')
        shape('tap',(0,.19,1),(.025,.025,.35),'metal','cylinder')
        box('tap_spout',0,.12,1.17,.03,.18,.025,'metal')
    elif k=='mirror':box('frame',0,0,0,w+.05,.05,h+.05,'frame');box('mirror',0,-.03,0,w,.015,h,'mirror')
    elif k=='toilet':
        shape('pedestal',(0,0,.2),(.3,.4,.4),'ceramic','sphere')
        shape('bowl',(0,-.08,.42),(.44,.63,.25),'ceramic','sphere')
        box('tank',0,.24,.63,.42,.22,.6,'ceramic',roundness=.06)
        box('lid',0,-.08,.55,.39,.5,.035,'white',roundness=.07)
    elif k=='shower':
        box('tray',0,0,.04,w,d,.08,'stone')
        box('glass',-w/2,0,1.05,.018,d,2.1,'glass')
        box('back',0,d/2,1.15,w,.08,2.3,'stone')
        box('head',0,d*.3,2.15,.3,.3,.025,'metal')
        shape('pipe',(0,d*.44,1.5),(.025,.025,1.3),'metal','cylinder')
    elif k=='rail':
        box('glass',0,0,.55,w,.025,1.1,'glass')
        box('top',0,0,1.1,w,.055,.045,'metal')
        for i,x in enumerate([-w/2,w/2]):box(f'post_{i}',x,0,.55,.04,.04,1.1,'metal')
    elif k=='books':
        for i in range(7):box(f'book_{i}',-w/2+i*w/7,0,.12,w/8,.22,.22+(i%3)*.025,'accent' if i%2 else 'paper')
    elif k=='landscape':
        env=s['environment'];night=s['period']=='night'
        if env=='city' and p.get('w',6)>=20:
            span=p.get('w',6)
            # Two grounded layers; the view remains an original, non-geographic city.
            box('distant_ground',0,14,-16,span*2,38,.6,'skyline')
            for row in range(2):
                for i in range(12):
                    hh=12+(i*7%13)+row*3;xx=(i-5.5)*span/10;yy=4+row*8;ww=1.15+(i%3)*.32
                    box(f'tower_{row}_{i}',xx,yy,hh/2-15,ww,2+row,hh,'skyline')
                    box(f'roof_{row}_{i}',xx,yy,hh-14.8,ww*.7,1.6,.4,'metal')
                    for j in range(12):
                        for col in [-1,1]:box(f'lit_window_{row}_{i}_{j}_{col}',xx+col*ww*.24,yy-(2+row)/2-.012,-13+j*(hh-2)/12,ww*.18,.018,.33,'light' if (i+j)%3 else 'glass',emission=.7 if night and (i+j)%3 else 0)
        elif env=='city':
            for i in range(10):
                span=p.get('w',6);hh=1.4+(i*7%9)*.3;x=(i-4.5)*span/10
                box(f'tower_{i}',x,1.5,hh/2,.48,.6,hh,'skyline')
                for j in range(4):box(f'lit_window_{i}_{j}',x,1.19,.5+j*.48,.13,.015,.18,'light',emission=2 if night else 0)
        elif env=='garden':
            box('lawn',0,1,0,7,6,.05,'leaf')
            for i in range(5):shape(f'tree_{i}',((i-2)*1.2,1+(i%2),1.4),(.9,.8,1.5),'leaf','sphere')
        else:
            box('sea',0,2,-.1,8,9,.04,'sea')
            for i in range(7):box(f'wave_{i}',0,.1+i*.7,-.065,7,.035,.012,'white')
    return a

def triangulate(points):
    """Ear clipping for simple concave floor polygons, normalized to CCW."""
    area=sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
    ids=list(range(len(points))) if area>0 else list(reversed(range(len(points))))
    def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    triangles=[]
    while len(ids)>3:
        for i,b in enumerate(ids):
            a=ids[i-1];c=ids[(i+1)%len(ids)]
            if turn(points[a],points[b],points[c])<=1e-9:continue
            if any(turn(points[a],points[b],points[j])>=-1e-9 and turn(points[b],points[c],points[j])>=-1e-9 and turn(points[c],points[a],points[j])>=-1e-9 for j in ids if j not in (a,b,c)):continue
            triangles.append((a,b,c));ids.pop(i);break
        else:raise ValueError('Floor polygon is self-intersecting or degenerate')
    triangles.append(tuple(ids));return triangles

def demo():
    from manhattan import residence
    return residence(kit_demo())

def compile_scene(s):
    out=[]
    for e in s['entities'].values():
        colors=palette(s,e)
        colors.update({'mirror':'#cbd5d5','skyline':'#536478' if s['period']=='day' else '#18283b','sea':'#53878d' if s['period']=='day' else '#152c44'})
        for m in parts(s,e):
            m.update({'entity':e['id'],'room':e['room'],'parent_position':e['position'],'parent_rotation':e['rotation'],'visible':e.get('visible',True),'color':e.get('overrides',{}).get(m['role'],m.get('color',colors[m['role']])),'outside':e['kind']=='landscape'})
            m['rooms']=e.get('adjacent_rooms',[e['room']])
            m['architecture']=e['kind']=='wall' or e.get('architecture',False)
            m['roof']=e['kind']=='jp_roof'
            if m['roof']:m['structural']=True
            m['facade']=e['kind'] in ('window','curtain') or e.get('facade',False)
            surface=surface_profile(s,e,m['role'])
            if surface:m['surface']=surface
            if e['kind']=='shell':
                cx,cy=s['rooms'][e['room']]['center'];w,d,_=s['rooms'][e['room']]['size'];edge=e['params']['edge']
                nx,ny=cx+({'E':w,'W':-w}.get(edge,0)),cy+({'N':d,'S':-d}.get(edge,0))
                m['rooms'] += [rid for rid,r in s['rooms'].items() if abs(r['center'][0]-nx)<.01 and abs(r['center'][1]-ny)<.01]
            m['fingerprint']=digest(m);out.append(m)
    return out
