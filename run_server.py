#!/usr/bin/env python3
"""Runner script for Nashta 10-Pillars Opportunity Radar & AI Assistant Server."""

import sys
import io
import socket

# Safe UTF-8 stream configuration for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import uvicorn


def find_available_port(preferred_port=8000, max_tries=10):
    for offset in range(max_tries):
        port = preferred_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred_port


if __name__ == "__main__":
    host = "127.0.0.1"
    port = find_available_port(8000)
    print(f"[START] Memulai server Nashta Opportunity Intelligence di http://{host}:{port}")
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)
