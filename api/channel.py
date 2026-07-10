import urllib.request, urllib.parse, json, ssl

USER_AGENT = "BuzCup/2.0 (+https://buzcup.net; Flutter; Dart) AppleCoreMedia/1.0"
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def app(environ, start_response):
    qs = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    ch = qs.get("ch", [""])[0]
    if not ch:
        start_response("400 Bad Request", [("Content-Type", "application/json")])
        return [json.dumps({"ok": False, "error": "Missing ch param"}).encode()]
    
    url = f"https://man1ted.com/get.php?ch={ch}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Referer": "https://man1ted.com/"
    })
    try:
        resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=15)
        body = resp.read()
        start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, OPTIONS"),
            ("Access-Control-Allow-Headers", "*"),
            ("Cache-Control", "no-cache, no-store, must-revalidate"),
        ])
        return [body]
    except urllib.error.HTTPError as e:
        start_response(f"{e.code} {e.reason}", [("Content-Type", "application/json"), ("Access-Control-Allow-Origin", "*")])
        return [e.read()]
    except Exception as e:
        start_response("500 Internal Server Error", [("Content-Type", "application/json"), ("Access-Control-Allow-Origin", "*")])
        return [json.dumps({"ok": False, "error": str(e)}).encode()]
