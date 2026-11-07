import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'skills/room-studio/scripts'))
from core import apply,travel,content,save,load,transaction,fingerprints,validate
from catalog import demo,compile_scene

class SceneTests(unittest.TestCase):
    def setUp(self):self.s=demo()
    def edit(self,ops,s=None):
        s=s or self.s
        return apply(s,{'expected_revision':s['revision'],'label':'test','ops':ops})
    def test_complete_residence_and_recessed_lights(self):
        self.assertGreaterEqual(len(self.s['rooms']),8)
        p=compile_scene(self.s);self.assertEqual(len(p),len({m['id'] for m in p}))
        self.assertTrue(any(m['shape']=='light' and m['power']>0 for m in p))
        self.assertFalse(any(e['kind'] in ('pendant','ceiling_lamp') for e in self.s['entities'].values()))
    def test_island_width_changes_only_entity_and_keeps_sink_centered(self):
        before=copy.deepcopy(self.s)
        out,r=self.edit([{'op':'set','target':'kitchen.island','params':{'w':1.2}}])
        self.assertEqual(r['changed'],['kitchen.island']);self.assertEqual(self.s,before)
        self.assertEqual(out['entities']['dining.table'],self.s['entities']['dining.table'])
        a={p['id']:p for p in compile_scene(out)}
        self.assertEqual(a['kitchen.island/basin_inner']['position'][0],0)
        self.assertGreater(a['kitchen.island/counter_right']['position'][0],.35)
    def test_material_and_room_overrides_survive_global_style(self):
        out,_=self.edit([{'op':'material','target':'dining.table','role':'wood','color':'#334455'},{'op':'style','target':'bedroom','value':'warm'}])
        out,_=self.edit([{'op':'style','target':'all','value':'mono'}],out)
        from core import palette
        self.assertEqual(palette(out,out['entities']['dining.table'])['wood'],'#334455')
        self.assertEqual(out['rooms']['bedroom']['style'],'warm')
        self.assertEqual(out['entities']['living.sofa']['position'],self.s['entities']['living.sofa']['position'])
    def test_invalid_patch_is_atomic(self):
        before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.edit([{'op':'style','target':'all','value':'mono'},{'op':'set','target':'missing','params':{'w':1}}])
        self.assertEqual(self.s,before)
    def test_bad_values_and_unknown_parameters(self):
        for value in (-1,float('nan'),float('inf'),True,1000):
            with self.assertRaises(ValueError):self.edit([{'op':'set','target':'kitchen.island','params':{'w':value}}])
        with self.assertRaises(ValueError):self.edit([{'op':'set','target':'kitchen.island','params':{'width_typo':1.2}}])
    def test_revision_conflict(self):
        with self.assertRaises(ValueError):apply(self.s,{'expected_revision':-1,'ops':[{'op':'period','value':'night'}]})
        with self.assertRaises(ValueError):apply(self.s,{'expected_revision':False,'ops':[{'op':'period','value':'night'}]})
    def test_unknown_fields_and_incomplete_entities_rejected(self):
        with self.assertRaises(ValueError):self.edit([{'op':'period','value':'night','typo':True}])
        with self.assertRaises(ValueError):self.edit([{'op':'material','target':'living.sofa','role':'unknown','color':None}])
        broken=copy.deepcopy(self.s);del broken['entities']['kitchen.island']['params']['w']
        with self.assertRaises(ValueError):validate(broken)
    def test_undo_redo_and_new_edit_clears_redo(self):
        out,_=self.edit([{'op':'period','value':'night'}]);undone,_=travel(out)
        self.assertEqual(content(undone),content(self.s));self.assertEqual(undone['revision'],2)
        redone,_=travel(undone,True);self.assertEqual(content(redone),content(out));self.assertEqual(redone['revision'],3)
        fresh,_=self.edit([{'op':'style','target':'all','value':'mono'}],undone);self.assertEqual(fresh['redo'],[])
    def test_curtain_geometry_and_picture_are_independent(self):
        out,r=self.edit([{'op':'set','target':'living.sheer','params':{'openness':.1}}])
        before={p['id']:p for p in compile_scene(self.s)};after={p['id']:p for p in compile_scene(out)}
        self.assertNotEqual(before['living.sheer/panel_-1']['vertices'],after['living.sheer/panel_-1']['vertices'])
        self.assertEqual(before['living.window/glass'],after['living.window/glass'])
        out,r=self.edit([{'op':'set','target':'living.picture','params':{'image':'coast'}}])
        self.assertEqual(r['changed'],['living.picture'])
    def test_environment_does_not_change_light_or_curtain(self):
        out,r=self.edit([{'op':'environment','value':'sea'}])
        self.assertTrue(all(self.s['entities'][eid]['kind']=='landscape' for eid in r['changed']))
        self.assertEqual(out['period'],self.s['period'])
    def test_day_night_controls_real_light_energy(self):
        out,_=self.edit([{'op':'period','value':'night'}]);day=compile_scene(self.s);night=compile_scene(out)
        get=lambda a:next(p['power'] for p in a if p['id']=='living.cove_back/source')
        self.assertGreater(get(night),get(day))
        dark,_=self.edit([{'op':'set','target':'living.cove_back','params':{'enabled':False}}],out)
        self.assertEqual(get(compile_scene(dark)),0)
    def test_roundtrip_persist_and_transaction(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'scene.json';save(p,self.s)
            transaction(p,{'expected_revision':0,'ops':[{'op':'period','value':'night'}]})
            restored=load(p);self.assertEqual(restored['period'],'night');self.assertEqual(restored['revision'],1)
            transaction(p,action='undo');self.assertEqual(content(load(p)),content(self.s))
    def test_all_theme_period_environment_combinations_compile(self):
        for style in ('warm','mono','heritage'):
            for period in ('day','night'):
                for env in ('city','garden','sea'):
                    out,_=self.edit([{'op':'style','target':'all','value':style},{'op':'period','value':period},{'op':'environment','value':env}])
                    self.assertTrue(compile_scene(out))

if __name__=='__main__':unittest.main(verbosity=2)
