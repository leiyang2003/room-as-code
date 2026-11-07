#!/usr/bin/env python3
"""Install the same skill into a project for Codex or Claude Code."""
import argparse,json,shutil
from pathlib import Path

def install(host,project,link=False):
    if host not in ('codex','claude'):raise ValueError('Unknown host')
    source=Path(__file__).resolve().parent/'skills/room-studio'
    target=Path(project).resolve()/('.agents' if host=='codex' else '.claude')/'skills/room-studio'
    if target.is_symlink() and target.resolve()==source:return target
    if target.exists() or target.is_symlink():raise ValueError(f'Target already exists; kept unchanged: {target}')
    target.parent.mkdir(parents=True,exist_ok=True)
    if link:target.symlink_to(source,target_is_directory=True)
    else:shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    return target

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--host',choices=['codex','claude'],required=True);ap.add_argument('--project',required=True);ap.add_argument('--link',action='store_true');a=ap.parse_args()
    try:print(json.dumps({'installed':str(install(a.host,a.project,a.link)),'host':a.host}))
    except (ValueError,OSError) as e:ap.exit(1,str(e)+'\n')
