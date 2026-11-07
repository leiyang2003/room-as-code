#!/usr/bin/env python3
"""Open both editable examples from fresh copies in a new runs directory."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    runs=ROOT/'runs';runs.mkdir(exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y-%m-%d_%H%M%S_')+'both-samples_',dir=runs))
    manifest=json.loads((ROOT/'examples/samples.json').read_text())
    for item in manifest['samples']:
        shutil.copyfile(ROOT/'examples'/item['scene'],run/item['scene'])
    registry=run/'samples.json';registry.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print('Editable sample copies: '+str(run),flush=True)
    sys.path.insert(0,str(ROOT/'skills/room-studio/scripts'))
    from server import serve
    serve(run/'japanese-three-gardens.scene.json',args.port,registry)

if __name__=='__main__':main()
