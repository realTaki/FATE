"""Real HTTP-client checks against only two owned loopback test servers."""
import ast
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from pathlib import Path
from socketserver import ThreadingMixIn
import sys
import threading
from types import SimpleNamespace
import unittest

import requests
import urllib3


ROOT = Path(__file__).resolve().parents[2]
source_path = ROOT / "fate_flow/utils/api_utils.py"
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name == "local_api"]
assert len(functions) == 1
settings = ast.parse((ROOT / "fate_flow/settings.py").read_text(encoding="utf-8"))
headers = next(ast.literal_eval(node.value) for node in settings.body
               if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == "HEADERS"
                       for target in node.targets))
module = ast.parse("")
module.body = functions
runtime = SimpleNamespace(JOB_SERVER_HOST=None)
namespace = {"requests": requests, "RuntimeConfig": runtime,
             "HEADERS": headers, "stat_logger": logging.getLogger("http-compatibility")}
exec(compile(module, str(source_path), "exec"), namespace)
local_api = namespace["local_api"]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.respond()

    def respond(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path.startswith("/redirect-"):
            destination = (self.server.self_base if self.path == "/redirect-same"
                           else self.server.peer_base) + "/echo"
            self.send_response(303 if self.path == "/redirect-303" else 302)
            self.send_header("Location", destination)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/bytes":
            data, kind = b"ordinary-test-bytes\n" * 32, "application/octet-stream"
        elif self.path == "/invalid-json":
            data, kind = b"not-json", "text/plain"
        else:
            result = {"method": self.command, "body": body.decode("utf-8"),
                      "content_type": self.headers.get("Content-Type"),
                      "cookie": self.headers.get("Cookie"),
                      "proxy_authorization": self.headers.get("Proxy-Authorization")}
            if body:
                try:
                    result["json"] = json.loads(body.decode("utf-8"))
                except ValueError:
                    pass
            data, kind = json.dumps(result).encode("utf-8"), "application/json"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class OwnedServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class HttpClientCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not requests.utils.should_bypass_proxies("http://127.0.0.1/", no_proxy=None):
            raise RuntimeError("existing proxy does not bypass loopback; no proxy change made")
        cls.servers = [OwnedServer(("127.0.0.1", 0), Handler) for _ in range(2)]
        cls.bases = ["http://127.0.0.1:" + str(server.server_port)
                     for server in cls.servers]
        cls.threads = []
        for index, server in enumerate(cls.servers):
            server.self_base = cls.bases[index]
            server.peer_base = cls.bases[1 - index]
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()
            cls.threads.append(thread)
        runtime.JOB_SERVER_HOST = cls.bases[0].split("://", 1)[1]

    @classmethod
    def tearDownClass(cls):
        for server in cls.servers:
            server.shutdown()
            server.server_close()
        for thread in cls.threads:
            thread.join(timeout=5)

    def setUp(self):
        self.pool = urllib3.PoolManager(timeout=urllib3.Timeout(total=3))

    def tearDown(self):
        self.pool.clear()

    def test_patched_coherent_versions(self):
        self.assertGreaterEqual(tuple(int(v) for v in urllib3.__version__.split(".")),
                                (1, 26, 19))
        self.assertGreaterEqual(tuple(int(v) for v in requests.__version__.split(".")),
                                (2, 25, 0))

    def test_actual_fate_local_api_json_post(self):
        payload = {"job_id": "local-fixture", "value": "雪", "enabled": True}
        result = local_api("POST", "/echo", payload)
        self.assertEqual(result["method"], "POST")
        self.assertEqual(result["json"], payload)
        self.assertEqual(result["content_type"], headers["Content-Type"])

    def test_actual_fate_local_api_json_get(self):
        payload = {"job_id": "local-fixture"}
        result = local_api("GET", "/echo", payload)
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["json"], payload)

    def test_actual_fate_local_api_error_wrapping(self):
        with self.assertRaisesRegex(Exception, "local request error:"):
            local_api("GET", "/invalid-json", {})

    def test_streaming_get_shape(self):
        with requests.get(self.bases[0] + "/bytes", stream=True, timeout=3) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.iter_content(chunk_size=17)),
                             b"ordinary-test-bytes\n" * 32)

    def test_same_origin_redirect_preserves_synthetic_cookie(self):
        response = self.pool.request("GET", self.bases[0] + "/redirect-same",
                                     headers={"Cookie": "demo=local-fixture"})
        result = json.loads(response.data.decode("utf-8"))
        self.assertEqual(result["cookie"], "demo=local-fixture")

    def test_cross_origin_redirect_strips_synthetic_sensitive_headers(self):
        response = self.pool.request("GET", self.bases[0] + "/redirect-cross",
                                     headers={"Cookie": "demo=local-fixture",
                                              "Proxy-Authorization": "fixture-only"})
        result = json.loads(response.data.decode("utf-8"))
        self.assertIsNone(result["cookie"])
        self.assertIsNone(result["proxy_authorization"])

    def test_303_redirect_changes_post_to_bodyless_get(self):
        response = self.pool.request("POST", self.bases[0] + "/redirect-303",
                                     body=b"ordinary-fixture",
                                     headers={"Content-Type": "text/plain"})
        result = json.loads(response.data.decode("utf-8"))
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["body"], "")


if __name__ == "__main__":
    print("runtime=" + sys.version.replace("\n", " "), flush=True)
    print("requests=" + requests.__version__ + " at " + requests.__file__, flush=True)
    print("urllib3=" + urllib3.__version__ + " at " + urllib3.__file__, flush=True)
    unittest.main(verbosity=2)
