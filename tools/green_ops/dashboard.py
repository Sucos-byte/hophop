# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Local read-only Green Ops dashboard. No backend execution endpoints."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlsplit,parse_qs
from dashboard_artifacts import ArtifactStore, ASSETS, safe_read

STATIC={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}


def make_server(port=8765,store=None):
    snapshots={route:(safe_read(ASSETS,name),mime) for route,(name,mime) in STATIC.items()}
    store=store if store is not None else ArtifactStore()
    class Handler(BaseHTTPRequestHandler):
        server_version='GreenOpsLocal/1'
        def log_message(self,*args):pass
        def send(self,status,raw,mime='application/json; charset=utf-8'):
            self.send_response(status);self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            if self.command!='HEAD':self.wfile.write(raw)
        def json(self,status,value):self.send(status,json.dumps(value,allow_nan=False,separators=(',',':')).encode())
        def do_HEAD(self):self.do_GET()
        def do_GET(self):
            allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            if self.headers.get('Host') not in allowed:
                return self.json(403,{'error':'Local Host header required'})
            origin=self.headers.get('Origin')
            if origin is not None and origin not in {'http://'+h for h in allowed}:
                return self.json(403,{'error':'Cross-origin requests denied'})
            if len(self.path)>2048:return self.json(400,{'error':'Request too long'})
            url=urlsplit(self.path)
            if url.scheme or url.netloc or '%' in url.path or '..' in url.path or '\\' in url.path:
                return self.json(404,{'error':'Not allowlisted'})
            try:
                params=parse_qs(url.query,keep_blank_values=True,max_num_fields=10,strict_parsing=bool(url.query))
                if any(len(v)!=1 for v in params.values()):raise ValueError('Repeated parameters denied')
                query={k:v[0] for k,v in params.items()}
                if url.path in STATIC and not query:
                    raw,mime=snapshots[url.path];return self.send(200,raw,mime)
                if url.path=='/api/summary' and not query:return self.json(200,store.summary())
                if url.path in ('/api/experiments','/api/predictions'):
                    return self.json(200,store.page(url.path.rsplit('/',1)[1],query))
                if url.path.startswith('/resource/') and not query:
                    key=url.path[len('/resource/'):]
                    if key not in store.resources:return self.json(404,{'error':'Not allowlisted'})
                    if key not in store.snapshots:return self.json(409,{'error':'Missing or incompatible artifact'})
                    # Always text/plain; untrusted artifact/document text never executes.
                    return self.send(200,store.raw(key),'text/plain; charset=utf-8')
                return self.json(404,{'error':'Not allowlisted'})
            except (ValueError,KeyError,OverflowError):return self.json(400,{'error':'Invalid query or incompatible data'})
        def readonly(self):self.json(405,{'error':'Read-only dashboard; GET/HEAD only'})
        do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=readonly
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    return server


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('port must be1..65535')
    with make_server(args.port) as server:
        print(f'Green Ops read-only dashboard: http://127.0.0.1:{server.server_port} (Ctrl+C stops)',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
