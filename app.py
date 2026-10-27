"""Local-only interface for the Audio Separator worker. Run with Launch.command."""
import argparse
import os
import json
import re
import secrets
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('VOCAL_REMOVER_DATA_DIR', str(ROOT / 'data'))).resolve()
JOBS = DATA / 'jobs'
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
ACTIVE = None
STATE = {}
MODES = {'lead': 'UVR_MDXNET_KARA_2.onnx', 'all': 'UVR-MDX-NET-Inst_HQ_3.onnx'}
MAX_BYTES = 500 * 1024 * 1024

def execute(job_id):
    global ACTIVE
    job = STATE[job_id]
    folder = JOBS / job_id
    try:
        with (folder / 'processing.log').open('w') as log:
            proc = subprocess.Popen([sys.executable, str(ROOT / 'worker.py'), str(folder), MODES[job['mode']]],
                                    stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            result = proc.wait()
        if result or not (folder / 'result.mp3').is_file():
            raise RuntimeError('Processing failed. See processing.log in the job folder for details. '
                               'If a model download failed, check your internet connection and try again.')
        job.update(status='complete', progress=100, message='Your backing track is ready.')
    except Exception as exc:
        job.update(status='error', message=str(exc))
    finally:
        with LOCK:
            ACTIVE = None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {'error': 'Local access only.'})
        parsed = urlparse(self.path)
        if parsed.path == '/':
            body = (ROOT / 'index.html').read_text().replace('__TOKEN__', TOKEN).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Frame-Options', 'DENY')
            self.end_headers()
            self.wfile.write(body)
            return
        match = re.fullmatch(r'/api/jobs/([a-f0-9]{32})(/audio)?', parsed.path)
        if not match or match[1] not in STATE:
            return self.reply(404, {'error': 'Not found.'})
        job_id = match[1]
        job = STATE[job_id]
        if match[2]:
            if job['status'] != 'complete':
                return self.reply(409, {'error': 'The track is not ready yet.'})
            return self.audio(JOBS / job_id / 'result.mp3', job['name'], 'download' in parse_qs(parsed.query))
        if job['status'] == 'processing':
            log_path = JOBS / job_id / 'processing.log'
            log = log_path.read_text(errors='replace') if log_path.exists() else ''
            pairs = re.findall(r'(\d+)/(\d+)\s*\[', log)
            if pairs:
                done, total = map(int, pairs[-1])
                job['progress'] = min(98, round(done / max(total, 1) * 98))
                job['message'] = 'Separating the vocals…' if done < total else 'Exporting your MP3…'
            else:
                job['message'] = 'Loading the model (downloading it if needed)…'
        self.reply(200, dict(job, id=job_id))

    def audio(self, path, name, download):
        size = path.stat().st_size
        start, end = 0, size - 1
        requested = self.headers.get('Range')
        if requested:
            m = re.fullmatch(r'bytes=(\d*)-(\d*)', requested)
            if not m or (not m[1] and not m[2]):
                return self.reply(416, {'error': 'Invalid byte range.'})
            if m[1]:
                start = int(m[1]); end = min(end, int(m[2])) if m[2] else end
            else:
                start = max(0, size - int(m[2]))
            if start > end or start >= size:
                return self.reply(416, {'error': 'Invalid byte range.'})
        self.send_response(206 if requested else 200)
        self.send_header('Content-Type', 'audio/mpeg')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if requested:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        if download:
            safe = re.sub(r'[^A-Za-z0-9._ -]', '_', Path(name).stem)[:100]
            self.send_header('Content-Disposition', f'attachment; filename="{safe}-backing-track.mp3"')
        self.end_headers()
        try:
            with path.open('rb') as stream:
                stream.seek(start)
                remaining = end-start+1
                while remaining:
                    block = stream.read(min(65536, remaining))
                    if not block: break
                    self.wfile.write(block); remaining -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        global ACTIVE
        if not self.valid_host() or self.headers.get('X-Tool-Token') != TOKEN:
            return self.reply(403, {'error': 'Open the tool in its local browser window.'})
        parsed = urlparse(self.path)
        mode = parse_qs(parsed.query).get('mode', ['lead'])[0]
        if parsed.path != '/api/jobs' or mode not in MODES:
            return self.reply(400, {'error': 'Choose a valid separation mode.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            size = 0
        if not 0 < size <= MAX_BYTES:
            return self.reply(413, {'error': 'Choose a file smaller than 500 MB.'})
        name = Path(unquote(self.headers.get('X-Filename', 'song.mp3'))).name
        suffix = Path(name).suffix.lower()
        if suffix not in ('.mp3', '.wav', '.flac', '.m4a', '.ogg'):
            return self.reply(400, {'error': 'Choose an MP3, WAV, FLAC, M4A, or OGG file.'})
        with LOCK:
            if ACTIVE:
                return self.reply(409, {'error': 'Another track is processing. Wait for it to finish.'})
            job_id = uuid.uuid4().hex
            ACTIVE = job_id
        folder = JOBS / job_id
        try:
            folder.mkdir(parents=True)
            with (folder / ('input' + suffix)).open('wb') as f:
                remaining = size
                while remaining:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk: raise ValueError('The file transfer was interrupted. Please retry.')
                    f.write(chunk); remaining -= len(chunk)
            STATE[job_id] = {'name': name, 'mode': mode, 'status': 'processing', 'progress': 0, 'message': 'Preparing your track…'}
            threading.Thread(target=execute, args=(job_id,), daemon=True).start()
            self.reply(202, {'id': job_id})
        except Exception as exc:
            with LOCK: ACTIVE = None
            self.reply(400, {'error': str(exc)})

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--host', default='127.0.0.1', choices=['127.0.0.1', '0.0.0.0'])
    parser.add_argument('--no-browser', action='store_true')
    args=parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    server=ThreadingHTTPServer((args.host, args.port), Handler)
    url=f'http://127.0.0.1:{server.server_port}'
    (DATA / '.server-url').write_text(url)
    print(f'Vocal Remover is ready: {url}\nKeep this window open. Press Control-C to stop.', flush=True)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
