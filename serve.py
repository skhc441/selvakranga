#!/usr/bin/env python3
"""Tiny static server for local preview.  Run:  python3 serve.py [port]"""
import functools
import http.server
import os
import socketserver
import sys

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4173


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    handler = functools.partial(Handler, directory=DIRECTORY)
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print("Serving %s at http://127.0.0.1:%d" % (DIRECTORY, PORT), flush=True)
        httpd.serve_forever()
