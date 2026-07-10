import urllib.request, urllib.parse, ssl

USER_AGENT = "BuzCup/2.0 (+https://buzcup.net; Flutter; Dart) AppleCoreMedia/1.0"
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def rewrite_playlist(body_bytes, target_url):
    """إعادة كتابة مسارات ملفات الـ TS النسبية لكي تمر عبر البروكسي"""
    body = body_bytes.decode("utf-8", errors="replace")
    base_dir = target_url.rsplit("/", 1)[0] if "/" in target_url else target_url
    base_dir = base_dir.split("?")[0]
    
    out = []
    lines = body.split("\n")
    
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("<") and not s.startswith("http"):
            if ".ts" in s or s.count(".") > 0:
                abs_url = f"{base_dir}/{s}"
                proxy = f"/api/proxy?url={urllib.parse.quote(abs_url, safe='')}"
                out.append(proxy)
                continue
        out.append(line)
        
    return "\n".join(out).encode("utf-8")

def app(environ, start_response):
    qs = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    target = qs.get("url", [""])[0]
    
    if not target:
        start_response("400 Bad Request", [("Content-Type", "text/plain")])
        return [b"Missing url parameter"]
    
    # الـ Headers الكاملة لتخطي حظر الـ 404 من السيرفر الرئيسي
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Origin": "https://man1ted.com",
        "Referer": "https://man1ted.com/"
    }
    
    req = urllib.request.Request(target, headers=headers)
    try:
        resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=15)
        body = resp.read()
        
        ctype = resp.headers.get("Content-Type", "application/octet-stream")
        if b"EXTM3U" in body:
            body = rewrite_playlist(body, target)
            ctype = "application/vnd.apple.mpegurl"
        
        start_response("200 OK", [
            ("Content-Type", ctype),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "*"),
            ("Cache-Control", "no-cache, no-store, must-revalidate"),
            ("Content-Length", str(len(body))),
        ])
        return [body]
    except urllib.error.HTTPError as e:
        body = e.read()
        start_response(f"{e.code} {e.reason}", [
            ("Content-Type", "text/plain"),
            ("Access-Control-Allow-Origin", "*"),
        ])
        return [body]
    except Exception as e:
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Access-Control-Allow-Origin", "*"),
        ])
        return [str(e).encode()]
