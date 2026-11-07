#!/usr/bin/env python3
"""Room Studio command line. Paths are explicit; all mutations are local."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from core import load, save, transaction
from catalog import demo, compile_scene
from render_state import render_status

def blender_path():
    configured=os.environ.get('BLENDER')
    if configured:
        p=Path(configured).expanduser()
        if p.is_file():return str(p)
        raise ValueError('BLENDER points to a missing executable')
    candidates=[shutil.which('blender'),'/Applications/Blender.app/Contents/MacOS/Blender']
    candidates += [str(p) for p in (Path.home()/'Applications').glob('**/Blender.app/Contents/MacOS/Blender')]
    for p in candidates:
        if p and Path(p).is_file():return p
    raise ValueError('Blender not found. Set BLENDER to its executable; run doctor again.')

def export_paths(scene,out,image=None):
    from render_state import manifest_path
    outputs=[Path(out).resolve(),Path(out).with_suffix('.glb').resolve(),Path(out).with_suffix('.validation.json').resolve()]
    if Path(out).suffix.lower()!='.blend':raise ValueError('Native master must use a .blend filename')
    if image:
        if Path(image).suffix.lower()!='.png':raise ValueError('Render image must use a .png filename')
        outputs.extend([Path(image).resolve(),manifest_path(image).resolve()])
    if Path(scene).resolve() in outputs or len(outputs)!=len(set(outputs)):
        raise ValueError('Scene, master, GLB, validation, image and provenance paths must be distinct')

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    init=sub.add_parser('init');init.add_argument('scene')
    for c in ('inspect','compile','undo','redo'):
        sp=sub.add_parser(c);sp.add_argument('scene')
    sp=sub.add_parser('apply');sp.add_argument('scene');sp.add_argument('patch');sp.add_argument('--dry-run',action='store_true')
    sp=sub.add_parser('serve');sp.add_argument('scene');sp.add_argument('--port',type=int,default=8765)
    sp=sub.add_parser('blender');sp.add_argument('scene');sp.add_argument('--out',required=True);sp.add_argument('--render');sp.add_argument('--room',default='living');sp.add_argument('--samples',type=int,default=32);sp.add_argument('--resolution',type=int,default=1100)
    sp=sub.add_parser('render');sp.add_argument('scene');sp.add_argument('--out',required=True);sp.add_argument('--image',required=True);sp.add_argument('--room',default='living');sp.add_argument('--samples',type=int,default=32);sp.add_argument('--resolution',type=int,default=1100)
    sp=sub.add_parser('render-status');sp.add_argument('scene');sp.add_argument('image')
    args=ap.parse_args()
    try:
        if args.command=='doctor':
            b=blender_path();version=subprocess.run([b,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
            result={'python':sys.version.split()[0],'blender':b,'version':version,'viewer_bundle':(Path(__file__).parent.parent/'assets/viewer/app.js').exists()}
        elif args.command=='init':
            if Path(args.scene).exists():raise ValueError('Scene already exists; choose a new filename')
            s=demo();save(args.scene,s);result={'scene':args.scene,'rooms':len(s['rooms']),'revision':s['revision']}
        elif args.command=='inspect':
            s=load(args.scene);result={k:s[k] for k in ('name','revision','style','period','environment','rooms')}
            result['entities']=[{k:e.get(k) for k in ('id','label','kind','room','params','position','rotation','visible','overrides')} for e in s['entities'].values()]
            for summary,e in zip(result['entities'],s['entities'].values()):
                summary.update({k:e[k] for k in ('detail','semantic_group','provenance') if k in e})
        elif args.command=='compile':
            s=load(args.scene);result={'scene':s,'parts':compile_scene(s)}
        elif args.command=='apply':
            patch=json.loads(Path(args.patch).read_text())
            if args.dry_run:
                from core import apply
                _,result=apply(load(args.scene),patch);result['dry_run']=True
            else:result=transaction(args.scene,patch)
        elif args.command in ('undo','redo'):result=transaction(args.scene,action=args.command)
        elif args.command=='serve':
            from server import serve
            serve(Path(args.scene).resolve(),args.port);return
        elif args.command=='render-status':
            result=render_status(load(args.scene),args.image)
        elif args.command in ('blender','render'):
            render=args.image if args.command=='render' else args.render
            export_paths(args.scene,args.out,render)
            if not 1<=args.samples<=65536 or not 16<=args.resolution<=16384:raise ValueError('Samples must be 1–65536 and resolution 16–16384')
            b=blender_path();script=Path(__file__).with_name('blender_sync.py')
            cmd=[b,'--background','--factory-startup','--python-exit-code','1','--python',str(script),'--','--scene',str(Path(args.scene).resolve()),'--out',str(Path(args.out).resolve()),'--room',args.room,'--samples',str(args.samples),'--resolution',str(args.resolution)]
            if render:
                cmd+=['--render',str(Path(render).resolve())]
            subprocess.run(cmd,check=True);result={'blend':args.out,'glb':str(Path(args.out).with_suffix('.glb'))}
            if render:result.update(image=render,render_status=render_status(load(args.scene),render))
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError,subprocess.CalledProcessError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr);sys.exit(1)

if __name__=='__main__':main()
