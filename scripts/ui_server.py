#!/usr/bin/env python3
"""Serve the built demo UI and forward its API requests."""
import argparse
import http.client
import http.server
import os
import select
import socket
import ssl
from pathlib import Path
from urllib.parse import urlsplit


def create_server(host, port, root, backend):
    root = root.resolve()
    upstream = urlsplit(backend)
    if upstream.scheme not in ("http", "https") or not upstream.hostname or upstream.path not in ("", "/"):
        raise ValueError("backend must be an HTTP(S) origin")
    proxy_prefixes = (
        "/admin-api",
        "/app-api",
        "/druid",
        "/admin",
        "/doc.html",
        "/swagger-ui",
        "/webjars",
        "/v3/api-docs",
    )

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

        def is_api_path(self):
            path = urlsplit(self.path).path
            return any(path == prefix or path.startswith(prefix + "/") for prefix in proxy_prefixes)

        def proxy(self):
            connection_type = http.client.HTTPSConnection if upstream.scheme == "https" else http.client.HTTPConnection
            conn = connection_type(upstream.hostname, upstream.port, timeout=30)
            response_started = False
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length else None
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in ("host", "connection", "transfer-encoding")}
                conn.request(self.command, self.path, body, headers)
                response = conn.getresponse()
                response_started = True
                self.send_response(response.status, response.reason)
                for key, value in response.getheaders():
                    if key.lower() not in ("connection", "transfer-encoding", "keep-alive"):
                        self.send_header(key, value)
                self.end_headers()
                if self.command != "HEAD":
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (OSError, ValueError, http.client.HTTPException):
                if response_started:
                    self.close_connection = True
                else:
                    try:
                        self.send_error(502, "Backend unavailable")
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                        self.close_connection = True
            finally:
                conn.close()

        def proxy_websocket(self):
            port = upstream.port or (443 if upstream.scheme == "https" else 80)
            backend = socket.create_connection((upstream.hostname, port), timeout=30)
            if upstream.scheme == "https":
                backend = ssl.create_default_context().wrap_socket(
                    backend, server_hostname=upstream.hostname
                )
            try:
                backend.settimeout(30)
                request_headers = []
                for key, value in self.headers.items():
                    if key.lower() == "host":
                        value = upstream.netloc
                    request_headers.append("{}: {}\r\n".format(key, value))
                request = "{} {} HTTP/1.1\r\n{}\r\n".format(
                    self.command, self.path, "".join(request_headers)
                ).encode("latin-1")
                backend.sendall(request)

                response = bytearray()
                while b"\r\n\r\n" not in response:
                    chunk = backend.recv(4096)
                    if not chunk:
                        raise ConnectionError("backend closed before WebSocket handshake")
                    response.extend(chunk)
                header_end = response.index(b"\r\n\r\n") + 4
                self.connection.sendall(response)
                if response[:header_end].split(b"\r\n", 1)[0].find(b" 101 ") < 0:
                    return
                backend.settimeout(None)
                self.connection.settimeout(None)
                sockets = (self.connection, backend)
                while True:
                    readable, _, _ = select.select(sockets, (), (), 60)
                    if not readable:
                        continue
                    for source in readable:
                        data = source.recv(65536)
                        if not data:
                            return
                        destination = backend if source is self.connection else self.connection
                        destination.sendall(data)
            except (OSError, ssl.SSLError, ConnectionError):
                return
            finally:
                backend.close()

        def do_GET(self):
            path = urlsplit(self.path).path
            if self.headers.get("Upgrade", "").lower() == "websocket":
                return self.proxy_websocket()
            if self.is_api_path():
                return self.proxy()
            target = Path(self.translate_path(path))
            if not target.is_file() and not Path(path).suffix:
                self.path = "/index.html"
            return super().do_GET()

        def do_HEAD(self):
            if self.is_api_path():
                return self.proxy()
            return super().do_HEAD()

        def do_POST(self):
            return self.proxy() if self.is_api_path() else self.send_error(404)

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

    return http.server.ThreadingHTTPServer((host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--backend", default="http://127.0.0.1:48080")
    parser.add_argument("--instance", default="")
    args = parser.parse_args()
    if not (args.root / "index.html").is_file():
        parser.error("built UI index.html does not exist")
    server = create_server(args.host, args.port, args.root, args.backend)
    print("UI listening on http://{}:{} (pid {})".format(args.host, args.port, os.getpid()), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
