#!/usr/bin/env python3
"""Build portable source/skill archives, excluding private references and logs."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent
DOCS=ROOT/'docs'

def sha(data):return hashlib.sha256(data).hexdigest()

def sources():
    files={}
    for name in ('README.md','LICENSE','THIRD_PARTY_NOTICES.md','install_skill.py','build_release.py','package.json','package-lock.json','.gitignore','.gitattributes'):
        p=ROOT/name
        if p.exists():files[name]=p.read_bytes()
    for folder in ('skills','.claude-plugin','.github','web','tests'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    # Ship fresh generated examples rather than silently capturing the user's live edits.
    sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
    from catalog import demo,kit_demo
    from core import apply
    main=demo()
    files['examples/manhattan.scene.json']=json.dumps(main,ensure_ascii=False,indent=2).encode()
    files['examples/kit-grid.scene.json']=json.dumps(kit_demo(),ensure_ascii=False,indent=2).encode()
    night,_=apply(main,{'expected_revision':main['revision'],'label':'Night template','ops':[{'op':'period','value':'night'}]});night['history']=[]
    files['examples/manhattan-night.scene.json']=json.dumps(night,ensure_ascii=False,indent=2).encode()
    industrial,_=apply(main,{'expected_revision':main['revision'],'label':'Industrial Metal template','ops':[{'op':'style','target':'all','value':'industrial'}]});industrial['history']=[]
    files['examples/manhattan-industrial.scene.json']=json.dumps(industrial,ensure_ascii=False,indent=2).encode()
    # Explicit public documentation allowlist; never package generated QA logs.
    for name in ('VALIDATION.md','tools/build_project_guide.py','Room_Studio_Project_Guide_EN.md','Room_Studio_Project_Guide_EN.html','Room_Studio_Project_Guide_EN.pdf'):
        p=DOCS/name
        if p.exists():files['docs/'+name]=p.read_bytes()
    for name in ('images/manhattan-bedroom-day.png','images/manhattan-living-day.png',
                 'images/manhattan-living-night.png','images/manhattan-overview-day.png',
                 'validation/final-native-results.json','validation/final-visual-results.json',
                 'validation/codex-edits.json','validation/claude-edits.json',
                 'validation/publication-checks.json','validation/industrial-native-results.json',
                 'images/industrial-metal-preview.jpg'):
        p=DOCS/name
        if p.exists():files['docs/'+name]=p.read_bytes()
    files['examples/quiet-house.scene.json']=files['examples/kit-grid.scene.json']
    personal_home=Path.home().as_posix().encode()
    for name,data in files.items():
        if name.endswith(('.py','.js','.json','.md','.yaml','.html','.css')) and personal_home in data:
            raise ValueError('Personal absolute path in release member: '+name)
    return files

def archive(path,files,prefix):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for name,data in sorted(files.items()):z.writestr(prefix+'/'+name,data)
        manifest={name:{'bytes':len(data),'sha256':sha(data)} for name,data in sorted(files.items())}
        z.writestr(prefix+'/FILES.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise ValueError('Archive CRC failed')
        recorded=json.loads(z.read(prefix+'/FILES.json'))
        for name,entry in recorded.items():
            data=z.read(prefix+'/'+name)
            if len(data)!=entry['bytes'] or sha(data)!=entry['sha256']:raise ValueError('Archive manifest mismatch: '+name)
    return {'name':path.name,'bytes':path.stat().st_size,'members':len(files)+1,'sha256':sha(path.read_bytes())}

def build():
    dist=ROOT/'dist';dist.mkdir(exist_ok=True);files=sources()
    source=dist/'room-as-code-0.1.0-source.zip';standalone=dist/'room-studio-0.1.0-skill.zip'
    results=[archive(source,files,'room-as-code')]
    skill={name.removeprefix('skills/room-studio/'):data for name,data in files.items() if name.startswith('skills/room-studio/')}
    results.append(archive(standalone,skill,'room-studio'))
    with tempfile.TemporaryDirectory(prefix='room-studio-release-check-') as tmp:
        tmp=Path(tmp)
        with zipfile.ZipFile(source) as z:z.extractall(tmp)
        package=tmp/'room-as-code';project=tmp/'clean-project';project.mkdir()
        subprocess.run([sys.executable,str(package/'install_skill.py'),'--host','codex','--project',str(project)],check=True,capture_output=True)
        helper=project/'.agents/skills/room-studio/scripts/room.py';scene=project/'house.scene.json'
        subprocess.run([sys.executable,str(helper),'init',str(scene)],check=True,capture_output=True)
        compiled=subprocess.run([sys.executable,str(helper),'compile',str(scene)],check=True,capture_output=True,text=True)
        payload=json.loads(compiled.stdout)
        assert payload['parts'] and 'kitchen.island' in payload['scene']['entities']
        assert (project/'.agents/skills/room-studio/assets/viewer/app.js').stat().st_size>100000
        subprocess.run([sys.executable,str(package/'install_skill.py'),'--host','claude','--project',str(project)],check=True,capture_output=True)
        assert (project/'.claude/skills/room-studio/SKILL.md').is_file()
        standalone_check=tmp/'standalone';standalone_check.mkdir()
        with zipfile.ZipFile(standalone) as z:z.extractall(standalone_check)
        subprocess.run([sys.executable,str(standalone_check/'room-studio/scripts/room.py'),'init',str(standalone_check/'test.scene.json')],check=True,capture_output=True)
    report={'status':'PASS','archives':results,'checks':['CRC','per-member SHA256 manifest verification','private-reference/raw-log/dependency exclusions','personal-path check','clean extraction','Codex project install','Claude Code project install','fresh scene initialization and compilation','standalone skill archive initialization','bundled offline viewer assets'],'scope':'Local archive verification; remote publication verified separately'}
    (dist/'release-validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':build()
