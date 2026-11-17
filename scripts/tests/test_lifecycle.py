import http.server
import importlib.util
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import subprocess
import shutil
import socket
import base64
import hashlib
import os
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ui_server", ROOT / "scripts" / "ui_server.py")
ui_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui_server)


class Backend(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(self.path.encode())

    def log_message(self, *args):
        pass


class UiServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        Path(self.directory.name, "index.html").write_text("demo index")
        self.backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Backend)
        self.server = ui_server.create_server("127.0.0.1", 0, Path(self.directory.name), "http://127.0.0.1:" + str(self.backend.server_port))
        for server in (self.backend, self.server):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    def tearDown(self):
        for server in (self.server, self.backend):
            server.shutdown()
            server.server_close()
        self.directory.cleanup()

    def test_spa_route_and_api_proxy(self):
        base = "http://127.0.0.1:" + str(self.server.server_port)
        self.assertEqual(urllib.request.urlopen(base + "/member/list").read(), b"demo index")
        self.assertEqual(urllib.request.urlopen(base + "/admin-api/example?x=1").read(), b"/admin-api/example?x=1")
        self.assertEqual(urllib.request.urlopen(base + "/app-api/example?x=1").read(), b"/app-api/example?x=1")

    def test_monitoring_pages_are_proxied_to_backend(self):
        base = "http://127.0.0.1:" + str(self.server.server_port)
        self.assertEqual(urllib.request.urlopen(base + "/druid/index.html").read(), b"/druid/index.html")
        self.assertEqual(urllib.request.urlopen(base + "/admin/applications").read(), b"/admin/applications")

    def test_api_documentation_is_proxied_to_backend(self):
        base = "http://127.0.0.1:" + str(self.server.server_port)
        for path in (
            "/doc.html",
            "/swagger-ui/index.html",
            "/swagger-ui/swagger-ui.css",
            "/webjars/swagger-ui/5.32.2/swagger-ui.css",
            "/v3/api-docs/swagger-config",
            "/v3/api-docs/all",
        ):
            with self.subTest(path=path):
                self.assertEqual(urllib.request.urlopen(base + path).read(), path.encode())

    def test_missing_asset_is_not_spa_fallback(self):
        with self.assertRaises(urllib.error.HTTPError) as result:
            urllib.request.urlopen("http://127.0.0.1:" + str(self.server.server_port) + "/assets/missing.js")
        self.assertEqual(result.exception.code, 404)

    def test_favicon_is_served_from_ui_root(self):
        favicon = Path(self.directory.name, "favicon.ico")
        favicon.write_bytes(b"ico")
        response = urllib.request.urlopen("http://127.0.0.1:" + str(self.server.server_port) + "/favicon.ico")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b"ico")

    def test_static_assets_allow_crossorigin_module_stylesheets(self):
        asset = Path(self.directory.name, "assets")
        asset.mkdir()
        (asset / "login.css").write_text(".login { display: block }")
        request = urllib.request.Request(
            "http://127.0.0.1:" + str(self.server.server_port) + "/assets/login.css",
            headers={"Origin": "http://127.0.0.1:5178"},
        )
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.read(), b".login { display: block }")
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")

    def test_client_disconnect_does_not_report_backend_failure(self):
        requested = threading.Event()
        release = threading.Event()
        finished = threading.Event()
        errors = []
        messages = []

        class DelayedBackend(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                requested.set()
                release.wait(5)
                self.send_response(200)
                self.send_header("Content-Length", str(1024 * 1024))
                self.end_headers()
                try:
                    self.wfile.write(b"x" * (1024 * 1024))
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), DelayedBackend)
        proxy = ui_server.create_server("127.0.0.1", 0, Path(self.directory.name),
                                        f"http://127.0.0.1:{backend.server_port}")

        def handle_error(request, address):
            errors.append((request, address))

        proxy.handle_error = handle_error

        class RecordingHandler(proxy.RequestHandlerClass):
            def finish(self):
                try:
                    super().finish()
                finally:
                    finished.set()

            def send_error(self, code, message=None, explain=None):
                messages.append((code, message))
                return super().send_error(code, message, explain)

        proxy.RequestHandlerClass = RecordingHandler

        for server in (backend, proxy):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(backend.server_close)
        self.addCleanup(proxy.server_close)
        self.addCleanup(backend.shutdown)
        self.addCleanup(proxy.shutdown)
        client = socket.create_connection(("127.0.0.1", proxy.server_port), timeout=2)
        client.sendall(b"GET /admin-api/slow HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        self.assertTrue(requested.wait(2))
        client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        client.close()
        release.set()
        self.assertTrue(finished.wait(5))
        self.assertEqual(errors, [])
        self.assertEqual(messages, [])

    def test_backend_unavailable_returns_502(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        listener.close()
        unavailable = ui_server.create_server("127.0.0.1", 0, Path(self.directory.name),
                                              f"http://127.0.0.1:{port}")
        threading.Thread(target=unavailable.serve_forever, daemon=True).start()
        self.addCleanup(unavailable.server_close)
        self.addCleanup(unavailable.shutdown)
        with self.assertRaises(urllib.error.HTTPError) as result:
            urllib.request.urlopen(f"http://127.0.0.1:{unavailable.server_port}/admin-api/offline")
        self.assertEqual(result.exception.code, 502)

    def test_websocket_upgrade_is_tunneled_and_frames_flow_both_ways(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        upstream_port = listener.getsockname()[1]

        def websocket_peer():
            connection, _ = listener.accept()
            request = bytearray()
            while not request.endswith(b"\r\n\r\n"):
                request.extend(connection.recv(4096))
            headers = {}
            for line in request.decode("ascii").split("\r\n")[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.lower()] = value.strip()
            accept = base64.b64encode(hashlib.sha1(
                (headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
            ).digest())
            connection.sendall(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + accept + b"\r\n\r\n"
            )
            frame = connection.recv(128)
            connection.sendall(frame)
            connection.close()

        peer = threading.Thread(target=websocket_peer, daemon=True)
        peer.start()
        self.addCleanup(listener.close)
        proxy = ui_server.create_server(
            "127.0.0.1", 0, Path(self.directory.name), f"http://127.0.0.1:{upstream_port}"
        )
        threading.Thread(target=proxy.serve_forever, daemon=True).start()
        self.addCleanup(proxy.server_close)
        self.addCleanup(proxy.shutdown)

        client = socket.create_connection(("127.0.0.1", proxy.server_port), timeout=2)
        client.settimeout(2)
        key = base64.b64encode(os.urandom(16))
        client.sendall(
            b"GET /infra/ws?token=test-token HTTP/1.1\r\n"
            b"Host: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            b"Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: " + key + b"\r\n\r\n"
        )
        response = bytearray()
        while b"\r\n\r\n" not in response:
            chunk = client.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
        self.assertIn(b"101 Switching Protocols", response)
        frame = b"\x81\x82\x01\x02\x03\x04\x69\x6b"
        client.sendall(frame)
        echoed = bytearray()
        while len(echoed) < len(frame):
            echoed.extend(client.recv(len(frame) - len(echoed)))
        self.assertEqual(echoed, frame)
        client.close()
        peer.join(timeout=2)


class ProcessSafetyTests(unittest.TestCase):
    def test_stop_does_not_kill_unrelated_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            runtime = root / "logs" / "lifecycle"
            runtime.mkdir(parents=True)
            shutil.copy(ROOT / "scripts" / "stop.sh", root / "scripts" / "stop.sh")
            process = subprocess.Popen(["sleep", "30"])
            try:
                started = subprocess.check_output(["ps", "-p", str(process.pid), "-o", "lstart="], text=True).strip()
                (runtime / "backend.pid").write_text(f"{process.pid}|{started}|yuheng-backend-1-2\n")
                result = subprocess.run(["bash", str(root / "scripts" / "stop.sh")], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(process.poll())
            finally:
                process.terminate()
                process.wait()


if __name__ == "__main__":
    unittest.main()
