"""Local parametric Japanese joinery, garden, roof and furniture families.

These are authored design geometry, separate from the unmodified main runtime.
"""
import math
import random


def parts(scene, e):
    p=e['params'];w=p.get('w',1);d=p.get('d',1);h=p.get('h',1)
    detail=e.get('detail','');out=[]
    rng=random.Random(e['id'])
    def shape(name,loc,size,role='wood',kind='box',**kw):
        out.append({'id':e['id']+'/'+name,'position':list(loc),'size':list(size),'role':role,'shape':kind,**kw})
    def box(n,x,y,z,ww,dd,hh,role='wood',**kw):shape(n,(x,y,z),(ww,dd,hh),role,**kw)
    def mesh(n,vs,fs,role='wood',**kw):shape(n,(0,0,0),(1,1,1),role,'mesh',vertices=vs,faces=fs,**kw)
    def taper(n,x,y,z,bw,bd,tw,td,hh,role='stone'):
        vs=[[x+sx*ww/2,y+sy*dd/2,z+zz] for ww,dd,zz in [(bw,bd,0),(tw,td,hh)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        mesh(n,vs,[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]],role)
    def rod(n,a,b,r,role='wood'):
        delta=[b[i]-a[i] for i in range(3)];ll=math.sqrt(sum(t*t for t in delta));u=[v/ll for v in delta]
        axis=[0,0,1] if abs(u[2])<.95 else [1,0,0]
        v=[u[1]*axis[2]-u[2]*axis[1],u[2]*axis[0]-u[0]*axis[2],u[0]*axis[1]-u[1]*axis[0]];vl=math.sqrt(sum(t*t for t in v));v=[t/vl for t in v]
        q=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        vs=[[point[j]+r*(v[j]*math.cos(i*math.tau/8)+q[j]*math.sin(i*math.tau/8)) for j in range(3)] for point in (a,b) for i in range(8)]
        fs=[]
        for i in range(8):j=(i+1)%8;fs.extend([[i,j,j+8],[i,j+8,i+8]])
        mesh(n,vs,fs,role)
    def leafcloud(n,centers,count=50,color=None):
        vs=[];fs=[]
        for center,spread in centers:
            for _ in range(count):
                xx=center[0]+rng.uniform(-spread,spread);yy=center[1]+rng.uniform(-spread,spread);zz=center[2]+rng.uniform(-spread*.30,spread*.25)
                radius=rng.uniform(.08,.16);angle=rng.random()*math.tau;idx=len(vs);vs.append([xx,yy,zz])
                for j in range(10):
                    rr=radius*(1 if j%2==0 else .39);a=angle+j*math.tau/10
                    vs.append([xx+rr*math.cos(a),yy+rr*math.sin(a),zz+.28*rr*math.sin(a)])
                for j in range(10):fs.append([idx,idx+1+j,idx+1+(j+1)%10])
        mesh(n,vs,fs,'leaf',**({'color':color} if color else {}))
    if e['kind']=='jp_floor':
        if detail=='tatami':
            nx,ny=e.get('grid',[4,2]);cw=w/nx;cd=d/ny
            for i in range(nx):
                for j in range(ny):
                    x=-w/2+(i+.5)*cw;y=-d/2+(j+.5)*cd;tag=f'{i}_{j}'
                    box('mat_'+tag,x,y,h/2,cw-.008,cd-.008,h,'fabric',roundness=.004)
                    for side in [-1,1]:box('heri_'+tag+'_'+str(side),x+side*(cw/2-.022),y,h+.002,.031,cd-.008,.006,'frame')
                    for t in range(12):box('igusa_'+tag+'_'+str(t),x,y-cd/2+(t+.5)*cd/12,h+.003,cw-.075,.008,.004,'accent')
        elif detail=='stone':
            nx=max(1,round(w/.6));ny=max(1,round(d/.6))
            for i in range(nx):
                for j in range(ny):box(f'tile_{i}_{j}',-w/2+(i+.5)*w/nx,-d/2+(j+.5)*d/ny,-h/2,w/nx-.009,d/ny-.009,h,'stone',roundness=.002)
        else:
            count=max(1,round(w/.20))
            for i in range(count):box('board_'+str(i),-w/2+(i+.5)*w/count,0,-h/2,w/count-.004,d,h,'wood',roundness=.001)
    elif e['kind']=='jp_joinery':
        if detail in ('shoji','glazing','fusuma','slats'):
            # All screens share a horizontal axis, with depth along Y.
            if detail=='slats':
                for i in range(max(2,round(w/.14))):
                    n=max(2,round(w/.14));box('slat_'+str(i),-w/2+(i+.5)*w/n,0,h/2,.045,d,h,'wood')
                for z in [.10,h-.10]:box('rail_'+str(z),0,0,z,w,.06,.055)
            else:
                panel_count=max(2,math.ceil(w/1.0));pw=w/panel_count
                openness=p.get('openness',0)
                for side in [-1,1]:box('post_'+str(side),side*w/2,0,h/2,.085,d,h,'wood')
                for z in [.025,h-.025]:box('track_'+str(z),0,0,z,w+.06,d+.03,.05,'wood')
                for i in range(panel_count):
                    # Stack to the two ends; center clears for a walkable opening.
                    half=panel_count//2
                    if i<half:x=-w/2+pw/2+i*pw*(1-openness)
                    else:x=w/2-pw/2-(panel_count-1-i)*pw*(1-openness)
                    # Two leaves overlap on separate tracks; stacking each at
                    # its own end would otherwise leave openness ineffective.
                    if panel_count==2 and i==1:x-=openness*pw
                    yy=(i%3)*.035
                    box('panel_'+str(i),x,yy,h/2,pw-.025,.018,h-.10,'glass' if detail=='glazing' else 'paper')
                    for side in [-1,1]:box(f'frame_{i}_{side}',x+side*(pw/2-.026),yy-.025,h/2,.032,.045,h-.05,'wood')
                    for z in [.065,h-.065]:box(f'cross_{i}_{z}',x,yy-.026,z,pw-.025,.04,.04,'wood')
                    if detail=='shoji':
                        for j in range(1,7):box(f'kumiko_h_{i}_{j}',x,yy-.026,h*j/7,pw-.03,.025,.014,'wood')
                        for j in range(1,4):box(f'kumiko_v_{i}_{j}',x-pw/2+pw*j/4,yy-.026,h/2,.012,.025,h-.1,'wood')
                    if detail=='fusuma':shape('pull_'+str(i),(x+pw*.30,yy-.04,h*.44),(.045,.018,.045),'metal','cylinder')
        elif detail=='boundary':
            box('stone_base',0,0,.18,w,d+.10,.36,'stone')
            box('plaster',0,0,h/2+.15,w,d,h-.30,'wall')
            box('copper_cap',0,0,h,w+.09,d+.12,.07,'metal')
            for side in [-1,1]:box('pier_'+str(side),side*(w/2-.04),0,h/2,.11,d+.05,h,'frame')
        elif detail=='tokonoma':
            box('raised_wood',0,0,.09,w,d,.18,'wood')
            box('plaster_back',0,d/2,h/2,w,.08,h,'wall')
            for side in [-1,1]:box('tokobashira_'+str(side),side*w/2,0,h/2,.09,.09,h,'wood')
            box('hanging_scroll',0,d/2-.05,h*.59,w*.34,.025,h*.48,'paper')
            box('ink_stroke',-.04,d/2-.07,h*.61,.025,.012,h*.26,'frame')
            for z in [h*.35,h*.84]:box('scroll_roller_'+str(z),0,d/2-.073,z,w*.36,.035,.025,'wood')
        elif detail=='beam':box('member',0,0,h/2,w,d,h,'wood',structural=True)
        elif detail=='deck':
            for i in range(max(1,round(w/.15))):
                n=max(1,round(w/.15));box('deck_'+str(i),-w/2+(i+.5)*w/n,0,-h/2,w/n-.006,d,h,'wood')
            box('fascia',0,-d/2,-h/2,w,.06,h,'frame')
        elif detail=='step':box('solid',0,0,h/2,w,d,h,'stone',roundness=.015)
    elif e['kind']=='jp_furniture':
        if detail=='chabudai':
            box('top',0,0,h,w,d,.055,'wood',roundness=.035)
            for i,x in enumerate([-w*.35,w*.35]):
                for j,y in enumerate([-d*.3,d*.3]):box(f'leg_{i}_{j}',x,y,h/2,.08,.08,h,'wood')
        elif detail=='zabuton':
            box('cushion',0,0,h/2,w,d,h,'fabric',roundness=.065)
            box('seam',0,-d/2+.025,h*.5,w-.06,.009,.008,'accent')
        elif detail=='low_bed':
            box('floating_plinth',0,0,.12,w+.22,d+.22,.24,'wood',roundness=.025)
            box('mattress',0,0,.34,w,d,.24,'white',roundness=.07)
            box('linen_duvet',0,-.16,.49,w+.04,d*.75,.12,'fabric',roundness=.06)
            box('head',0,d/2+.06,.43,w+.30,.12,.72,'wood')
            for i in [-1,1]:box('pillow_'+str(i),i*w*.25,d*.32,.53,w*.40,.42,.14,'white',roundness=.05)
            box('linen_fold',0,-d*.27,.57,w+.07,.48,.035,'accent',roundness=.015)
        elif detail=='ofuro':
            box('stone_platform',0,0,.04,w+.20,d+.20,.08,'stone')
            box('water',0,0,h-.13,w-.16,d-.16,.018,'glass')
            box('tub_base',0,0,.09,w,d,.10,'wood')
            for side in [-1,1]:
                box('side_'+str(side),side*(w/2-.055),0,h/2,.11,d,h,'wood')
                box('end_'+str(side),0,side*(d/2-.055),h/2,w,.11,h,'wood')
            for j in range(max(2,round(w/.12))):box('rim_joint_'+str(j),-w/2+(j+.5)*w/max(2,round(w/.12)),-d/2-.005,h-.03,.006,.02,.04,'frame')
            rod('faucet',(-w*.35,d*.62,.03),(-w*.35,d*.62,h+.2),.025,'metal')
        elif detail=='andon':
            box('wood_base',0,0,.04,w,d,.08,'wood')
            box('washi_shade',0,0,h*.52,w*.87,d*.87,h*.85,'paper',emission=1.2,temperature=2700)
            for x in [-w/2,w/2]:
                for y in [-d/2,d/2]:box(f'leg_{x}_{y}',x,y,h/2,.019,.019,h,'frame')
            for z in [h*.13,h*.5,h*.92]:
                for side in [-1,1]:box(f'rail_{z}_{side}',0,side*d/2,z,w,.018,.016,'frame')
            power=12 if scene['period']=='night' else .5
            shape('source',(0,0,h*.6),(1,1,1),'light','light',power=power,temperature=2600,target=[0,0,-1])
        elif detail=='bench':
            box('seat',0,0,h,w,d,.065,'wood')
            for side in [-1,1]:box('leg_'+str(side),side*w*.38,0,h/2,.08,d*.80,h,'frame')
        elif detail=='stone_bowl':
            shape('basin',(0,0,h/2),(w,d,h),'stone','sphere')
            shape('well',(0,0,h*.91),(w*.65,d*.65,.035),'glass','cylinder')
            rod('bamboo_spout',(-w*.65,0,h+.20),(w*.08,0,h+.16),.025,'wood')
    elif e['kind']=='jp_garden':
        if detail=='gravel':
            box('gravel_base',0,0,-.025,w,d,.05,'stone',roundness=.001)
            for i in range(int(w*d*2.2)):
                x=rng.uniform(-w/2,w/2);y=rng.uniform(-d/2,d/2);r=rng.uniform(.025,.065)
                shape('pebble_'+str(i),(x,y,.012),(r,r*.72,.018),'stone','sphere')
        elif detail=='moss':
            shape('island',(0,0,.015),(w,d,.13),'leaf','sphere')
            for i in range(18):
                a=rng.random()*math.tau;r=rng.uniform(.10,.45)
                shape('mound_'+str(i),(math.cos(a)*w*r,math.sin(a)*d*r,.04),(w*.20,d*.18,.11),'leaf','sphere')
        elif detail=='rock':
            vs=[]
            for z,radius in [(0,.42),(h*.30,.55),(h*.76,.43),(h,.15)]:
                for i in range(9):
                    angle=i*math.tau/9;rr=radius*rng.uniform(.83,1.13)
                    vs.append([w*rr*math.cos(angle),d*rr*math.sin(angle),z+rng.uniform(-.025,.025)])
            fs=[]
            for j in range(3):
                for i in range(9):k=j*9+i;l=j*9+(i+1)%9;fs.extend([[k,l,l+9],[k,l+9,k+9]])
            fs.extend([[27,27+i,27+i+1] for i in range(1,8)])
            mesh('weathered_stone',vs,fs,'stone')
        elif detail in ('maple','pine'):
            rod('trunk',(0,0,0),(.06,0,h*.64),.055 if detail=='maple' else .075)
            centers=[]
            for i in range(8):
                a=i*2.4;z=h*(.45+.045*i);rr=w*(.32 if i<5 else .20)
                end=(math.cos(a)*rr,math.sin(a)*rr,z+h*.1)
                rod('branch_'+str(i),(.03,0,z*.8),end,.014 if detail=='maple' else .024)
                centers.append((end,w*.19))
            leafcloud('foliage',centers,38 if detail=='maple' else 48)
        elif detail=='bamboo':
            centers=[]
            for i in range(7):
                x=rng.uniform(-w/2,w/2);y=rng.uniform(-d/2,d/2);hh=h*rng.uniform(.72,1)
                rod('culm_'+str(i),(x,y,0),(x+.08,y,hh),.022,'leaf')
                for j in range(1,7):shape(f'node_{i}_{j}',(x+.08*j/7,y,hh*j/7),(.055,.055,.025),'wood','cylinder')
                centers.append(((x,y,hh*.79),.34))
            leafcloud('leaves',centers,19)
        elif detail=='toro':
            box('base',0,0,.08,w,d,.16,'stone')
            taper('foot',0,0,.15,w*.6,d*.6,w*.35,d*.35,h*.20)
            box('shaft',0,0,h*.42,w*.24,d*.24,h*.30,'stone')
            box('lamp_base',0,0,h*.61,w*.62,d*.62,.07,'stone')
            box('lit_paper',0,0,h*.74,w*.34,d*.34,h*.20,'paper',emission=1 if scene['period']=='night' else .05,temperature=2600)
            for x in [-w*.22,w*.22]:
                for y in [-d*.22,d*.22]:box(f'post_{x}_{y}',x,y,h*.74,w*.08,d*.08,h*.23,'stone')
            taper('roof',0,0,h*.86,w*.94,d*.94,w*.18,d*.18,h*.13)
            shape('finial',(0,0,h*1.04),(w*.18,d*.18,h*.16),'stone','sphere')
        elif detail=='ground':box('earth',0,0,-h/2,w,d,h,'soil')
    elif e['kind']=='jp_roof':
        # Four planar copper/slate roof faces, with a level eave and hip ends.
        half=max(0,(w-d)/2)
        if w>=d:
            vs=[[-w/2,-d/2,0],[w/2,-d/2,0],[w/2,d/2,0],[-w/2,d/2,0],[-half,0,h],[half,0,h]]
        else:
            half=max(0,(d-w)/2);vs=[[-w/2,-d/2,0],[w/2,-d/2,0],[w/2,d/2,0],[-w/2,d/2,0],[0,-half,h],[0,half,h]]
        fs=[[0,1,5],[0,5,4],[1,2,5],[2,3,4],[2,4,5],[3,0,4]] if w>=d else [[0,1,4],[1,2,5],[1,5,4],[2,3,5],[3,0,4],[3,4,5]]
        mesh('hipped_copper',vs,fs,'metal')
        # Thin standing seams follow the actual hip planes; no floating bars.
        seam_vs=[];seam_fs=[]
        def height_at(x,y):return h*max(0,min(1,(w/2-abs(x))/(min(w,d)/2),(d/2-abs(y))/(min(w,d)/2)))
        for i in range(1,max(2,round(w/.40))):
            x=-w/2+i*w/max(2,round(w/.40));start=len(seam_vs)
            for j in range(17):
                y=-d/2+j*d/16
                for dx in [-.008,.008]:seam_vs.append([x+dx,y,height_at(x+dx,y)+.007])
            for j in range(16):a=start+j*2;seam_fs.extend([[a,a+1,a+3],[a,a+3,a+2]])
        mesh('standing_seams',seam_vs,seam_fs,'frame')
        for a,b in [(0,1),(1,2),(2,3),(3,0),(4,5)]:rod('seam_'+str(a)+str(b),vs[a],vs[b],.027,'frame')
        box('soffit',0,0,-.055,w,d,.10,'wood',ceiling=True)
    if not out:raise ValueError('Unsupported Japanese detail: '+e['kind']+'/'+detail)
    return out
