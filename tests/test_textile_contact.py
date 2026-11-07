"""Contact and drape regressions use compiled geometry in support coordinates."""
import collections,math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'skills/room-studio/scripts'))
from catalog import demo,parts

def support_vertices(cloth,mesh,support):
    angle=math.radians(cloth['rotation']);ca,sa=math.cos(angle),math.sin(angle)
    angle=math.radians(-support['rotation']);cb,sb=math.cos(angle),math.sin(angle)
    out=[]
    for x,y,z in mesh['vertices']:
        wx=cloth['position'][0]+ca*x-sa*y-support['position'][0]
        wy=cloth['position'][1]+sa*x+ca*y-support['position'][1]
        out.append((cb*wx-sb*wy,sb*wx+cb*wy,z+cloth['position'][2]-support['position'][2]))
    return out

class TextileContactTests(unittest.TestCase):
    def setUp(self):self.s=demo()
    def cloth(self,eid):
        e=self.s['entities'][eid];p=parts(self.s,e)
        self.assertEqual(len(p),1,'Textile has no rigid fringe/plate primitives')
        mesh=p[0];self.assertEqual(mesh['shape'],'mesh');support=self.s['entities'][e['support_entity']]
        return e,mesh,support,support_vertices(e,mesh,support)
    def assert_closed(self,mesh):
        edges=collections.Counter(tuple(sorted(edge)) for f in mesh['faces'] for edge in zip(f,f[1:]+f[:1]))
        self.assertTrue(all(n==2 for n in edges.values()),set(edges.values()))
    def test_sofa_throw_rests_on_seat_and_falls_clear_of_base(self):
        e,mesh,sofa,verts=self.cloth('living.throw');self.assert_closed(mesh)
        top=verts[:len(verts)//2];d=sofa['params']['d'];front=-.07-(d-.18)/2
        contact=[z-.53 for x,y,z in top if front+.08<y<.10]
        self.assertGreater(len(contact),100);self.assertGreaterEqual(min(contact),.0019);self.assertLessEqual(max(contact),.0061)
        self.assertLess(min(z for x,y,z in top),.32)
        for x,y,z in verts:
            if front+1e-5<y<-.07+(d-.18)/2 and abs(x)<sofa['params']['w']/2-.14:
                self.assertGreaterEqual(z,.5304,'Textile must not penetrate nominal seat envelope, including the bevel')
        hanging=[(y,z) for x,y,z in top if z<.38]
        self.assertTrue(hanging);self.assertTrue(all(y<-d/2 for y,z in hanging),'Drape must clear sofa base front')
        self.assertGreater(max(z for x,y,z in top)-min(z for x,y,z in top),.20)
    def test_all_bed_coverlets_rest_on_duvet_and_drape_both_sides(self):
        for rid in ('bedroom','bedroom2','study'):
            with self.subTest(room=rid):
                e,mesh,bed,verts=self.cloth(rid+'.coverlet');self.assert_closed(mesh)
                bed_parts=parts(self.s,bed)
                self.assertFalse(any(p['id'].endswith('/folded_coverlet') for p in bed_parts))
                band_max_y=max(y for x,y,z in verts)
                for seam in (p for p in bed_parts if '/quilt_seam_' in p['id']):
                    self.assertGreater(seam['position'][1]-seam['size'][1]/2,band_max_y,'Raised stitching must not penetrate the blanket')
                top=verts[:len(verts)//2];w=bed['params']['w'];d=bed['params']['d'];flat=(w+.015)/2-.05
                contact=[z-.67 for x,y,z in top if abs(x)<flat-.01]
                self.assertGreater(len(contact),100);self.assertGreaterEqual(min(contact),.0019);self.assertLessEqual(max(contact),.0061)
                self.assertTrue(all(-d*.48-.001<=y<=d*.22+.001 for x,y,z in top),'Band rests within duvet depth')
                for x,y,z in verts:
                    if abs(x)<(w+.015)/2-1e-5:
                        self.assertGreaterEqual(z,.6704,'Textile must clear the complete nominal duvet envelope at the edge')
                for sign in [-1,1]:
                    hanging=[(x,z) for x,y,z in top if sign*x>w/2 and z<.60]
                    self.assertTrue(hanging);self.assertLess(min(z for x,z in hanging),.48)
                    self.assertGreater(min(z for x,z in hanging),.35,'Fabric clears bed frame top')
    def test_only_target_entities_change_in_compiled_correction(self):
        # All textiles remain independent stable IDs and preserve authored support poses.
        self.assertEqual(self.s['entities']['living.sofa']['position'][2],0)
        self.assertEqual({e['support_entity'] for e in self.s['entities'].values() if e.get('drape_profile')}, {'living.sofa','bedroom.bed','bedroom2.bed','study.bed'})

if __name__=='__main__':unittest.main(verbosity=2)
