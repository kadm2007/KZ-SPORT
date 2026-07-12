"""
BEIN Sports Dynamic Proxy Server v9.4
Optimized for high-performance streaming with rigorous security and standards.
"""

import os
import time
import gzip
import logging
import mimetypes
import threading
import urllib.parse
import shutil
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from collections import OrderedDict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 8000
ROOT = Path(__file__).resolve().parent
UA = "BuzCup/2.0 (+https://buzcup.net; Flutter; Dart) AppleCoreMedia/1.0"
CHUNK_SIZE = 256 * 1024
ALLOWED_DOMAINS = ("man1ted.com")

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ProxyServer")

# --- Optimized Session ---
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.2)
adapter = HTTPAdapter(pool_connections=200, pool_maxsize=200, max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

# --- LRU Cache ---
class LRUCache:
    def __init__(self, capacity=100, ttl=5):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.ttl = ttl
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache: return None
            data, timestamp = self.cache[key]
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None
            return data

    def set(self, key, value):
        with self.lock:
            self.cache[key] = (value, time.time())
            if len(self.cache) > self.capacity: self.cache.popitem(last=False)

channel_cache = LRUCache(capacity=50, ttl=5)
m3u8_cache = LRUCache(capacity=100, ttl=3)

# --- Helpers ---
def is_safe_url(url):
    host = urllib.parse.urlparse(url).hostname or ""
    return host == ALLOWED_DOMAINS or host.endswith("." + ALLOWED_DOMAINS)

def rewrite_m3u8(body_bytes, target_url):
    body = body_bytes.decode("utf-8", errors="replace")
    lines = []
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            url = urllib.parse.urljoin(target_url, s)
            lines.append(f"/api/proxy?url={urllib.parse.quote(url)}")
        else:
            lines.append(line)
    return "\n".join(lines).encode()

class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def write_safe(self, data):
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return False
        return True

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.end_headers()

    def do_HEAD(self): self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == "/api/channel":
            ch = urllib.parse.parse_qs(parsed.query).get("ch", [""])[0]
            data = channel_cache.get(ch)
            if not data:
                try:
                    with session.get(f"https://man1ted.com/get.php?ch={ch}", headers={"User-Agent": UA}, timeout=(3, 20)) as r:
                        r.raise_for_status()
                        data = r.content
                        channel_cache.set(ch, data)
                except Exception as e:
                    logger.warning(f"Channel error: {e}")
                    data = b"{}"
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if not head_only: self.write_safe(data)

        elif path == "/api/proxy":
            target = urllib.parse.parse_qs(parsed.query).get("url", [""])[0]
            if not is_safe_url(target): return self.send_error(403)
            
            headers = {"User-Agent": UA, "Referer": "https://man1ted.com/", "Range": self.headers.get("Range", "")}
            
            if ".m3u8" in target.lower():
                data = m3u8_cache.get(target)
                if not data:
                    try:
                        with session.get(target, headers=headers, timeout=(3, 20)) as r:
                            r.raise_for_status()
                            data = rewrite_m3u8(r.content, target)
                            m3u8_cache.set(target, data)
                    except Exception as e:
                        logger.warning(f"M3U8 error: {e}")
                        return self.send_error(502)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if not head_only: self.write_safe(data)
            else:
                try:
                    with session.get(target, headers=headers, stream=True, timeout=(3, 20)) as r:
                        r.raise_for_status()
                        self.send_response(r.status_code)
                        for h in ["Content-Type", "Content-Length", "Accept-Ranges", "Cache-Control", "ETag", "Expires", "Last-Modified", "Date", "Content-Range"]:
                            if h in r.headers: self.send_header(h, r.headers[h])
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.send_header("Connection", "keep-alive")
                        self.end_headers()
                        if not head_only:
                            for i, chunk in enumerate(r.iter_content(CHUNK_SIZE)):
                                if not self.write_safe(chunk): break
                                if i % 8 == 0: self.wfile.flush()
                except Exception as e:
                    logger.warning(f"Stream error: {e}")

        else:
            file_path = (ROOT / path.lstrip("/")).resolve()
            if not str(file_path).startswith(str(ROOT)): return self.send_error(403)
            if not file_path.exists() or file_path.is_dir(): file_path = ROOT / "index.html"
            
            mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "public, max-age=3600")
            
            accept_enc = self.headers.get("Accept-Encoding", "")
            if "gzip" in accept_enc and mime in ["text/html", "text/css", "application/javascript", "application/json"]:
                self.send_header("Content-Encoding", "gzip")
                data = gzip.compress(file_path.read_bytes())
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if not head_only: self.write_safe(data)
            else:
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.end_headers()
                if not head_only:
                    try:
                        with open(file_path, "rb") as f:
                            shutil.copyfileobj(f, self.wfile, length=CHUNK_SIZE)
                    except (BrokenPipeError, ConnectionResetError): pass

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), ProxyHandler)
    server.daemon_threads = True
    logger.info(f"Server started at http://{HOST}:{PORT}")
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()
