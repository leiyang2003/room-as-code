"""Checks the authored layout, editable families and preserved three-garden scope."""
import copy,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
from core import load,apply,travel,content
from catalog import compile_scene

class JapaneseSceneTests(unittest.TestCase):
 def setUp(self):self.scene=load(ROOT/'examples/japanese-three-gardens.scene.json')
 def test_three_distinct_open_gardens_and_floor_area(self):
  scene=self.scene
  self.assertEqual(set(scene['layout']['garden_rooms']),{'front_garden','courtyard','main_garden'})
  self.assertAlmostEqual(sum(r['area_design_m2'] for r in scene['rooms'].values() if r['zone']!='garden'),221.51,places=3)
  for rid in scene['layout']['garden_rooms']:
   self.assertTrue(scene['rooms'][rid]['open_to_sky'])
   x,y=scene['rooms'][rid]['center']
   for e in scene['entities'].values():
    if e['kind']!='jp_roof':continue
    ex,ey,_=e['position'];self.assertFalse(abs(x-ex)<e['params']['w']/2 and abs(y-ey)<e['params']['d']/2)
 def test_all_indoor_spaces_connect_to_entry(self):
  graph={rid:set() for rid in self.scene['rooms']}
  for p in self.scene['layout']['portals']:
   a,b=p['rooms']
   if a in graph and b in graph:graph[a].add(b);graph[b].add(a)
  seen={'entry'};todo=['entry']
  while todo:
   for rid in graph[todo.pop()]-seen:seen.add(rid);todo.append(rid)
  self.assertTrue({rid for rid,r in self.scene['rooms'].items() if r['zone']!='garden'}<=seen)
 def test_complete_semantic_families_and_stable_meshes(self):
  parts=compile_scene(self.scene)
  self.assertGreater(len(parts),3000)
  self.assertEqual(len(parts),len({p['id'] for p in parts}))
  self.assertTrue(any('kumiko_h' in p['id'] for p in parts))
  self.assertTrue(any('hinoki_tub' in p['entity'] for p in parts))
  self.assertTrue(any('standing_seams' in p['id'] for p in parts))
  for p in parts:
   for v in p['position']+p['size']:self.assertTrue(math.isfinite(v))
   if p['shape']=='mesh':
    self.assertTrue(p['vertices']);self.assertTrue(p['faces'])
    self.assertTrue(all(0<=i<len(p['vertices']) for f in p['faces'] for i in f))
 def test_scoped_move_preserves_courtyards_and_other_objects(self):
  s=self.scene;eid='zashiki.tea_table';xyz=copy.deepcopy(s['entities'][eid]['position']);xyz[0]+=.20
  protected=[i for i,e in s['entities'].items() if e['room'] in s['layout']['garden_rooms']]
  out,report=apply(s,{'expected_revision':s['revision'],'protect':protected,'ops':[{'op':'set','target':eid,'position':xyz}]})
  self.assertEqual(report['changed'],[eid])
  self.assertTrue(all(out['entities'][i]==e for i,e in s['entities'].items() if i!=eid))
  undone,_=travel(out);self.assertEqual(content(undone),content(s))
 def test_style_has_effect_and_preserves_explicit_colors(self):
  s=self.scene;e=s['entities']['engawa.surface_finish']
  before=next(p for p in compile_scene(s) if p['entity']==e['id'])['color']
  out,_=apply(s,{'expected_revision':s['revision'],'ops':[{'op':'style','target':'all','value':'heritage'}]})
  after=next(p for p in compile_scene(out) if p['entity']==e['id'])['color']
  self.assertNotEqual(before,after)
  self.assertEqual(out['entities']['courtyard.maple']['overrides'],s['entities']['courtyard.maple']['overrides'])
 def test_cameras_have_actual_room_context(self):
  for rid,r in self.scene['rooms'].items():
   p=r['camera']['position'];x,y=r['center'];w,d,_=r['size']
   self.assertLessEqual(abs(p[0]-x),w/2+.1,rid);self.assertLessEqual(abs(p[1]-y),d/2+.1,rid)
 def test_two_leaf_fusuma_openness_changes_geometry(self):
  s=self.scene;eid='engawa.screen_12'
  before=[p['position'] for p in compile_scene(s) if p['entity']==eid]
  out,report=apply(s,{'expected_revision':s['revision'],'ops':[{'op':'set','target':eid,'params':{'openness':.25}}]})
  after=[p['position'] for p in compile_scene(out) if p['entity']==eid]
  self.assertNotEqual(before,after);self.assertEqual(report['changed'],[eid])

if __name__=='__main__':unittest.main(verbosity=2)
