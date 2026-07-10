"""
BEIN Sports Full Dynamic Proxy Server v6.1
"""
import urllib.request, urllib.parse, ssl, json
from http.server import HTTPServer, BaseHTTPRequestHandler

UA = "BuzCup/2.0 (+https://buzcup.net; Flutter; Dart) AppleCoreMedia/1.0"
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def fetch_from_source(url):
    """جلب البيانات من المصدر مع حقن الهيدرز الكاملة لتفادي الـ 404"""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Referer": "https://man1ted.com/"
    })
    try:
        r = urllib.request.urlopen(req, context=ssl_ctx, timeout=15)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 500, {}, str(e).encode()

def rewrite_m3u8(body_bytes, target_url):
    """إعادة توجيه كافة ملفات الفيديو والجودات لتمر عبر سيرفرنا المحلي بشكل إجباري"""
    body = body_bytes.decode("utf-8", errors="replace")
    base_dir = target_url.rsplit("/", 1)[0] if "/" in target_url else target_url
    base_dir = base_dir.split("?")[0]
    
    out = []
    for line in body.split("\n"):
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("<"):
            # إذا كان الرابط نسبي، نقوم بتحويله لرابط كامل أولاً
            if not s.startswith("http"):
                abs_url = f"{base_dir}/{s}"
            else:
                abs_url = s
            # تحويل الرابط ليمر عبر البروكسي المحلي الخاص بنا
            proxied_url = f"/api/proxy?url={urllib.parse.quote(abs_url, safe='')}"
            out.append(proxied_url)
            continue
        out.append(line)
    return "\n".join(out).encode("utf-8")

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path
        print(f"REQ: {repr(p)}")
        
        # 1. نقطة جلب بيانات القناة وتذكرة البث
        if p.startswith('/api/channel?'):
            params = urllib.parse.parse_qs(p.split('?')[1])
            ch = params.get('ch', [''])[0]
            s, h, b = fetch_from_source(f'https://man1ted.com/get.php?ch={ch}')
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b)
            return
        
        # 2. البروكسي الشامل لملفات الـ M3U8 والـ TS لمنع الـ CORS والـ 404
        if p.startswith('/api/proxy?'):
            params = urllib.parse.parse_qs(p.split('?')[1])
            target = params.get('url', [''])[0]
            
            s, h, b = fetch_from_source(target)
            
            # إذا كان الملف ملقم بث (M3U8) نقوم بتعديل روابط الجودات بداخله لكي لا تخرج للمتصفح مباشرة
            if b"EXTM3U" in b or ".m3u8" in target.lower():
                b = rewrite_m3u8(b, target)
                ctype = 'application/vnd.apple.mpegurl'
            else:
                ctype = h.get('Content-Type', 'video/MP2T')
                
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', ctype)
            self.end_headers()
            self.wfile.write(b)
            return

        # 3. تشغيل الصفحة الرئيسية المستهدفة للمباريات
        if p == '/' or p.startswith('/?'):
            try:
                with open('match-site.html', 'rb') as f:
                    html = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"match-site.html not found localy")
            return
            
        # أي طلبات أخرى غير معروفة
        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    print("Server running on http://127.0.0.1:8000")
    HTTPServer(('127.0.0.1', 8000), H).serve_forever()
