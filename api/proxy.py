import urllib.request, urllib.parse, ssl

USER_AGENT = "BuzCup/2.0 (+https://buzcup.net; Flutter; Dart) AppleCoreMedia/1.0"
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def proxify_url(url):
    return f"/api/proxy?url={urllib.parse.quote(url, safe='')}"

def rewrite_playlist(body_bytes, target_url):
    """Rewrite HLS variant and segment URLs so every request keeps using this proxy."""
    body = body_bytes.decode("utf-8", errors="replace")
    out = []

    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("<"):
            out.append(proxify_url(urllib.parse.urljoin(target_url, s)))
            continue
        out.append(line)

    return "\n".join(out).encode("utf-8")

def app(environ, start_response):
    qs = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    target = qs.get("url", [""])[0]

    if not target:
        start_response("400 Bad Request", [("Content-Type", "text/plain")])
        return [b"Missing url parameter"]

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
