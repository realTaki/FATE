"""Ordinary IDNA and Requests checks without DNS or outbound connections."""
import json
import sys
import unittest

import chardet
import idna
import requests


class IdnaHttpCompatibility(unittest.TestCase):
    def test_patched_idna_requirement(self):
        self.assertGreaterEqual(tuple(int(v) for v in idna.__version__.split('.')),
                                (3, 7))

    def test_ascii_roundtrip(self):
        self.assertEqual(idna.encode('example.com'), b'example.com')
        self.assertEqual(idna.decode(b'example.com'), 'example.com')

    def test_ordinary_unicode_roundtrips(self):
        fixtures = [('bücher.example', b'xn--bcher-kva.example'),
                    ('faß.example', b'xn--fa-hia.example'),
                    ('例子.测试', b'xn--fsqu00a.xn--0zwm56d')]
        for text, encoded in fixtures:
            with self.subTest(text=text):
                self.assertEqual(idna.encode(text), encoded)
                self.assertEqual(idna.decode(encoded), text)

    def test_uts46_case_mapping(self):
        self.assertEqual(idna.encode('BÜCHER.example', uts46=True),
                         b'xn--bcher-kva.example')

    def test_small_invalid_labels(self):
        for text in ('-invalid.example', 'a..example', '😀.example'):
            with self.subTest(text=text):
                with self.assertRaises(idna.IDNAError):
                    idna.encode(text)

    def test_requests_prepares_unicode_host_without_dns(self):
        prepared = requests.Request('GET', 'https://bücher.example/path',
                                    params={'q': '雪'}).prepare()
        self.assertEqual(prepared.url,
                         'https://xn--bcher-kva.example/path?q=%E9%9B%AA')
        self.assertIs(requests.packages.idna, idna)

    def test_requests_prepares_json_without_sending(self):
        payload = {'job_id': 'ordinary-fixture', 'value': '雪', 'enabled': True}
        prepared = requests.Request('POST', 'http://example.test/api',
                                    json=payload).prepare()
        self.assertEqual(json.loads(prepared.body.decode('utf-8')), payload)
        self.assertEqual(prepared.headers['Content-Type'], 'application/json')

    def test_requests_prepares_in_memory_multipart(self):
        prepared = requests.Request('POST', 'http://example.test/upload',
                                    files={'file': ('fixture.txt', b'ordinary bytes')},
                                    data={'job_id': 'ordinary-fixture'}).prepare()
        self.assertIn(b'ordinary bytes', prepared.body)
        self.assertIn(b'name="job_id"', prepared.body)
        self.assertIn('multipart/form-data; boundary=',
                      prepared.headers['Content-Type'])

    def test_existing_chardet_and_response_decoding(self):
        self.assertIs(requests.compat.chardet, chardet)
        self.assertEqual(chardet.__version__, '3.0.4')
        response = requests.Response()
        response.status_code = 200
        response.encoding = 'utf-8'
        response._content = '{"value":"雪"}'.encode('utf-8')
        self.assertEqual(response.json(), {'value': '雪'})
        self.assertEqual(response.text, '{"value":"雪"}')

    def test_documented_nonfinite_json_policy(self):
        request = requests.Request('POST', 'http://example.test/api',
                                   json={'value': float('nan')})
        version = tuple(int(v) for v in requests.__version__.split('.'))
        if version >= (2, 26, 0):
            with self.assertRaises(requests.exceptions.InvalidJSONError):
                request.prepare()
        else:
            self.assertIn(b'NaN', request.prepare().body)


if __name__ == '__main__':
    print('runtime=' + sys.version.replace('\n', ' '), flush=True)
    print('requests=' + requests.__version__ + ' at ' + requests.__file__, flush=True)
    print('idna=' + idna.__version__ + ' at ' + idna.__file__, flush=True)
    unittest.main(verbosity=2)
