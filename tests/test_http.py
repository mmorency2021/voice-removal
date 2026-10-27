"""Fast HTTP checks; no model downloads or ML dependencies are required."""
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vocal_app',ROOT/'app.py')
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        app.JOBS=Path(cls.tmp.name)
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()

    def test_homepage_has_both_modes(self):
        html=urlopen(self.url).read().decode()
        self.assertIn('value="lead"',html)
        self.assertIn('value="all"',html)
        self.assertNotIn('__TOKEN__',html)

    def test_rejects_cross_site_post(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url+'/api/jobs',data=b'abc'))
        self.assertEqual(error.exception.code,403)

    def test_rejects_bad_host(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url,headers={'Host':'example.com'}))
        self.assertEqual(error.exception.code,403)

    def test_rejects_unsupported_file(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url+'/api/jobs',data=b'abc',headers={'X-Tool-Token':app.TOKEN,'X-Filename':'bad.txt'}))
        self.assertEqual(error.exception.code,400)
        self.assertIsNone(app.ACTIVE)

    def test_playback_ranges_and_download(self):
        jobid='a'*32
        folder=app.JOBS/jobid;folder.mkdir(exist_ok=True)
        data=b'ID3'+bytes(range(256))*8
        (folder/'result.mp3').write_bytes(data)
        app.STATE[jobid]={'name':'My Song.mp3','status':'complete'}
        response=urlopen(Request(self.url+f'/api/jobs/{jobid}/audio',headers={'Range':'bytes=10-99'}))
        self.assertEqual(response.status,206)
        self.assertEqual(response.read(),data[10:100])
        response=urlopen(self.url+f'/api/jobs/{jobid}/audio?download=1')
        self.assertIn('attachment;',response.headers['Content-Disposition'])
        self.assertEqual(response.read(),data)

if __name__=='__main__':unittest.main()
