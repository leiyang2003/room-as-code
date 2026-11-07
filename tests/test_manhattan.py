"""Layout-specific geometry and editing checks."""
import math,sys,unittest,json,hashlib,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'skills/room-studio/scripts'))
from catalog import demo,compile_scene,triangulate
from core import save,load
from manhattan import area

def inside(p,poly):
    x,y=p;v=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        cross=(x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if abs(cross)<1e-6 and min(a[0],b[0])-1e-6<=x<=max(a[0],b[0])+1e-6 and min(a[1],b[1])-1e-6<=y<=max(a[1],b[1])+1e-6:return True
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:v=not v
    return v

def footprint(e,padding=0):
    p=e['params'];w=p.get('w',.5)+padding*2;d=p.get('d',.7)+padding*2
    if e['kind']=='bed':w+=.2;d+=.2
    if e['kind']=='basin':d=.6
    if e['kind']=='toilet':w=.5;d=.8
    c,s=math.cos(math.radians(e['rotation'])),math.sin(math.radians(e['rotation']));x,y=e['position'][:2]
    return [(x+xx*c-yy*s,y+xx*s+yy*c) for xx,yy in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]

class ManhattanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s=demo()
    def test_design_envelope_and_room_tiling(self):
        s=self.s;self.assertAlmostEqual(area(s['layout']['outline']),267,places=4)
        self.assertAlmostEqual(sum(area(r['polygon']) for r in s['rooms'].values()),267,places=4)
        # Dense independent sampling detects overlap and gaps, rather than just matching totals.
        outline=s['layout']['outline']
        for i in range(119):
            for j in range(87):
                p=(-11.5+i*.205,-5.2+j*.205)
                n=sum(inside(p,r['polygon']) for r in s['rooms'].values())
                self.assertEqual(n,1 if inside(p,outline) else 0,(p,n))
    def test_three_beds_three_full_baths_and_no_balcony(self):
        s=self.s
        for rid in s['layout']['bedroom_rooms']:self.assertIn(rid+'.bed',s['entities'])
        for rid in s['layout']['full_bathrooms']:
            for name in ('vanity','toilet','shower'):self.assertIn(rid+'.'+name,s['entities'])
        self.assertIn('powder.toilet',s['entities']);self.assertNotIn('balcony',s['rooms'])
    def test_all_rooms_have_real_portal_path_from_entry(self):
        s=self.s;reached={'entry'}
        while True:
            nxt=reached|{r for p in s['layout']['portals'] if reached.intersection(p['rooms']) for r in p['rooms']}
            if nxt==reached:break
            reached=nxt
        self.assertTrue(set(s['rooms'])<=reached,set(s['rooms'])-reached)
        for p in s['layout']['portals']:
            self.assertGreaterEqual(p['width'],.8)
            for rid in p['rooms']:
                if rid!='outside':self.assertTrue(inside(p['center'],s['rooms'][rid]['polygon']),(rid,p))
    def test_furniture_inside_assigned_room(self):
        for e in self.s['entities'].values():
            if e['kind'] not in {'bed','sofa','table','chair','cabinet','island','basin','toilet','shower','appliance'}:continue
            if e['position'][2]>.1:continue
            for pt in footprint(e):self.assertTrue(inside(pt,self.s['rooms'][e['room']]['polygon']),(e['id'],pt))
    def test_doors_not_blocked_by_floor_furniture(self):
        for p in self.s['layout']['portals']:
            if p['kind']!='door':continue
            c,s=math.cos(math.radians(p['axis'])),math.sin(math.radians(p['axis']))
            for e in self.s['entities'].values():
                if e['room'] not in p['rooms'] or e['position'][2]>.1 or e['kind'] not in {'bed','sofa','table','chair','cabinet','island','basin','toilet','shower','appliance'}:continue
                # Door aperture plus a 60 cm approach on each side.
                pts=footprint(e);u=[(pt[0]-p['center'][0])*c+(pt[1]-p['center'][1])*s for pt in pts];v=[-(pt[0]-p['center'][0])*s+(pt[1]-p['center'][1])*c for pt in pts]
                overlap=min(u)<p['width']/2-.03 and max(u)>-p['width']/2+.03 and min(v)<.60 and max(v)>-.60
                self.assertFalse(overlap,(p,e['id']))
    def test_wall_art_does_not_cross_door(self):
        for e in self.s['entities'].values():
            if e['kind'] not in ('art','mirror'):continue
            for p in self.s['layout']['portals']:
                if e['room'] not in p['rooms']:continue
                c,s=math.cos(math.radians(p['axis'])),math.sin(math.radians(p['axis']));dx=e['position'][0]-p['center'][0];dy=e['position'][1]-p['center'][1]
                if abs(-dx*s+dy*c)<.21:
                    self.assertGreaterEqual(abs(dx*c+dy*s),p['width']/2+e['params']['w']/2-.01,(e['id'],p))
    def test_A2_preserves_A1_walls_and_portals(self):
        contract=json.loads((Path(__file__).parent/'fixtures/manhattan-A1-contract.json').read_text())
        walls={k:e for k,e in self.s['entities'].items() if e['kind']=='wall'}
        self.assertEqual(hashlib.sha256(json.dumps(walls,sort_keys=True).encode()).hexdigest(),contract['walls_sha256'])
        self.assertEqual(self.s['layout'],contract['layout'])
    def test_floor_furniture_do_not_overlap(self):
        ents=[e for e in self.s['entities'].values() if e['kind'] in {'bed','sofa','table','chair','cabinet','island','basin','toilet','shower','appliance'} and e['position'][2]<.1]
        def overlap(a,b):
            for polygon in (a,b):
                for u,v in zip(polygon,polygon[1:]+polygon[:1]):
                    n=(v[1]-u[1],u[0]-v[0]);x=[i[0]*n[0]+i[1]*n[1] for i in a];y=[i[0]*n[0]+i[1]*n[1] for i in b]
                    if min(max(x),max(y))-max(min(x),min(y))<.01:return False
            return True
        for a,b in itertools.combinations(ents,2):
            if a['room']==b['room']:self.assertFalse(overlap(footprint(a),footprint(b)),(a['id'],b['id']))
    def test_A2_decor_edit_keeps_unrelated_entities(self):
        from core import apply
        s=self.s;eid='dining.place_setting_1';e=s['entities'][eid];pos=e['position'].copy();pos[0]+=.04
        out,result=apply(s,{'expected_revision':0,'ops':[{'op':'set','target':eid,'position':pos}]})
        self.assertEqual(result['changed'],[eid]);self.assertEqual(s['entities']['living.sofa'],out['entities']['living.sofa'])
        self.assertEqual(len([e for e in s['entities'].values() if e.get('detail')=='table_setting']),6)
        self.assertEqual(s['entities']['living.lounge_chair']['detail'],'lounge')
        self.assertIn('bathroom.towels',s['entities'])
    def test_meshes_stable_ids_and_compilation(self):
        parts=compile_scene(self.s);self.assertEqual(len(parts),len({p['id'] for p in parts}))
        for eid in ('kitchen.island','dining.table','living.sofa','living.picture','living.sheer'):self.assertIn(eid,self.s['entities'])
        for e in self.s['entities'].values():
            if e['kind']!='floorplan':continue
            pts=e['params']['points'];tri=triangulate(pts)
            self.assertEqual(len(tri),len(pts)-2)
            self.assertAlmostEqual(sum(area([pts[i] for i in t]) for t in tri),area(pts),places=5)
        self.assertFalse(any(e['kind'] in ('pendant','ceiling_lamp') for e in self.s['entities'].values()))

if __name__=='__main__':unittest.main(verbosity=2)
