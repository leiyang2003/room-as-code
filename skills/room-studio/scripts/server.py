"""Loopback-only preview; same transactions as the CLI. No remote API or model."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
from core import load, transaction
from catalog import compile_scene

def serve(path,port):
    assets=Path(__file__).parent.parent/'assets/viewer'
    class Handler(BaseHTTPRequestHandler):
        def send(self,status,body,typ='application/json'):
            self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path.split('?')[0]=='/api/scene':
                try:
                    s=load(path);self.send(200,json.dumps({'scene':s,'parts':compile_scene(s)},ensure_ascii=False).encode())
                except Exception as e:self.send(500,json.dumps({'error':str(e)}).encode())
                return
            name=self.path.split('?')[0].lstrip('/') or 'index.html'
            if name not in ('index.html','app.js','app.css'):self.send(404,b'Not found','text/plain');return
            file=assets/name
            if not file.exists():self.send(404,b'Build viewer first','text/plain');return
            self.send(200,file.read_bytes(),{'html':'text/html; charset=utf-8','js':'text/javascript','css':'text/css'}[file.suffix[1:]])
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
                if self.path=='/api/patch':result=transaction(path,body)
                elif self.path in ('/api/undo','/api/redo'):result=transaction(path,action=self.path[5:])
                else:self.send(404,b'{}');return
                self.send(200,json.dumps(result,ensure_ascii=False).encode())
            except (ValueError,KeyError,TypeError) as e:self.send(400,json.dumps({'error':str(e)}).encode())
        def log_message(self,*args):pass
    print(f'Room Studio preview: http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
