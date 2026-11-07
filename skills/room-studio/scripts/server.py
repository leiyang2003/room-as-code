"""Loopback-only preview; same transactions as the CLI. No remote API or model."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import re
from urllib.parse import urlsplit, parse_qs
from core import load, transaction
from catalog import compile_scene

def sample_registry(path, manifest=None):
    """Resolve an explicit local allowlist; never accept paths from HTTP clients."""
    if manifest is None:
        return 'default', {'default': {'label': load(path)['name'], 'path': Path(path)}}
    manifest=Path(manifest).resolve();config=json.loads(manifest.read_text());samples={}
    for item in config['samples']:
        key=item['id']
        if not isinstance(key,str) or not re.fullmatch(r'[a-z0-9-]{1,64}',key) or key in samples:
            raise ValueError('Invalid or duplicate sample ID')
        scene=(manifest.parent/item['scene']).resolve();load(scene)
        samples[key]={'label':item['label'],'path':scene}
    default=config['default']
    if default not in samples:raise ValueError('Default sample is missing')
    return default,samples

def serve(path,port,manifest=None):
    default,samples=sample_registry(path,manifest)
    assets=Path(__file__).parent.parent/'assets/viewer'
    class Handler(BaseHTTPRequestHandler):
        def send(self,status,body,typ='application/json'):
            self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if urlsplit(self.path).path=='/api/samples':
                self.send(200,json.dumps({'default':default,'samples':[{'id':key,'label':value['label']} for key,value in samples.items()]},ensure_ascii=False).encode());return
            if self.path.split('?')[0]=='/api/scene':
                try:
                    key=self.sample_key();s=load(samples[key]['path']);self.send(200,json.dumps({'sample':key,'scene':s,'parts':compile_scene(s)},ensure_ascii=False).encode())
                except (ValueError,KeyError) as e:self.send(400,json.dumps({'error':str(e)}).encode())
                return
            name=self.path.split('?')[0].lstrip('/') or 'index.html'
            if name not in ('index.html','app.js','app.css'):self.send(404,b'Not found','text/plain');return
            file=assets/name
            if not file.exists():self.send(404,b'Build viewer first','text/plain');return
            self.send(200,file.read_bytes(),{'html':'text/html; charset=utf-8','js':'text/javascript','css':'text/css'}[file.suffix[1:]])
        def sample_key(self):
            key=parse_qs(urlsplit(self.path).query).get('sample',[default])[0]
            if key not in samples:raise ValueError('Unknown sample')
            return key
        def do_POST(self):
            # Do not accept cross-origin writes; browser fetches supply matching Origin.
            origin=self.headers.get('Origin');host=self.headers.get('Host')
            if host not in (f'127.0.0.1:{port}',f'localhost:{port}') or origin not in (None,f'http://{host}'):
                self.send(403,b'{"error":"Origin rejected"}');return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send(415,b'{}');return
            try:
                size=int(self.headers.get('Content-Length',0))
                if not 0<size<100000:raise ValueError('Invalid request size')
                body=json.loads(self.rfile.read(size))
                scene=samples[self.sample_key()]['path'];route=urlsplit(self.path).path
                if route=='/api/patch':result=transaction(scene,body)
                elif route in ('/api/undo','/api/redo'):result=transaction(scene,action=route[5:])
                else:self.send(404,b'{}');return
                self.send(200,json.dumps(result,ensure_ascii=False).encode())
            except (ValueError,KeyError,TypeError) as e:self.send(400,json.dumps({'error':str(e)}).encode())
        def log_message(self,*args):pass
    print(f'Room Studio preview: http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
