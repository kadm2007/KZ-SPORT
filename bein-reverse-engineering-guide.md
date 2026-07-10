# VacoTV / Buz Cup Reverse Engineering + BEIN Sports Streaming Guide
=============================================================

## Overview
Successfully reverse engineered the VacoTV app (com.buzcup.buz_cup) and
extracted working BEIN Sports streaming URLs through the man1ted.com API.

## Step-by-Step Method

### 1. Obtain the APK
- App: Buz Cup (VacoTV) from Google Play Store
- Package: com.buzcup.buz_cup
- Version: 2.0.0 (APKPure XAPK format)
- Download: Via Play Store or APKPure mirrors

### 2. Extract XAPK
```
unzip Buz+Cup_2.0.0_APKPure.xapk -d /tmp/buzcup-extract/
```
Result: 
- com.buzcup.buz_cup.apk (main APK, Flutter-based)
- config.armeabi_v7a.apk (native ARM libraries)

### 3. Decompile with jadx
```
jadx -d /tmp/buzcup-jadx /tmp/buzcup-extract/com.buzcup.buz_cup.apk
```
- Flutter app → most logic in native libs (libapp.so)
- Searched for streaming URLs in Java code → none found
- Used strings on libapp.so → found everything

### 4. Key Findings from libapp.so (native Dart)
```
strings config.armeabi_v7a/lib/armeabi-v7a/libapp.so | grep ...
```
Found:
- **BuzCup User-Agent**: `BuzCup/2.0 (+https://buzcup.net; Flutter; Dart) AppleCoreMedia/1.0`
- Default IPTV playlist URL
- M3uService, PlaylistUrlValidator functions
- M3U8 URL validation regex
- App stores last_active_playlist_structured locally

### 5. Bypass vitalscop.com Protection
- Stream source: https://vitalscop.com/protect_m3u.php
- Protected with "Access Denied - authorized IPTV applications only"
- **Bypass**: Use BuzCup User-Agent header
- Redirect chain: 22455.xyz → vitalscop.com/protect_m3u.php
- Returns 134KB M3U playlist with all channels

### 6. Extract Real Stream URLs
The M3U playlist contained BEIN Sports with multiple streaming backends:

**Primary (man1ted.com API)**:
- Endpoint: https://man1ted.com/get.php?ch=CHANNEL_ID
- Returns JSON with stream_url (temp token, expires in 600s)
- Channel IDs: beee1..beee9, beemax1..beemax6
- Stream URL: https://man1ted.com/watch/CHANNEL.m3u8?md5=TOKEN&expires=TIMESTAMP
- **Important**: Stream requires BuzCup User-Agent (otherwise 410 Gone)

### 7. Build Proxy Server
Stream requires BuzCup UA which browsers can't set.
Solution: Python proxy server that:
- Serves HTML page at localhost:8000
- Proxies API calls with BuzCup UA
- Proxies HLS streams (M3U8 + TS segments) with BuzCup UA
- Relative URL resolution handled via /stream/ prefix

### 8. Working BEIN Channels
| Channel        | API Param   | Notes         |
|----------------|-------------|---------------|
| BEIN Sports 1  | beee1       | Main channel  |
| BEIN Sports 2  | beee2       |               |
| BEIN Sports 3  | beee3       |               |
| BEIN Sports 4  | beee4       |               |
| BEIN Sports 5  | beee5       |               |
| BEIN Sports 6  | beee6       |               |
| BEIN MAX 1     | beemax1     | Extra content |
| BEIN MAX 2     | beemax2     |               |
| BEIN MAX 3     | beemax3     |               |
| BEIN MAX 4     | beemax4     |               |
| BEIN MAX 5     | beemax5     |               |
| BEIN MAX 6     | beemax6     |               |

### 9. Files Created
- /home/zs/bein-server-v6.py — Streaming proxy server
- /home/zs/match-site.html — Match streaming UI
- /home/zs/vacotv-playlist.m3u — Full original M3U (proprietary format)
- /home/zs/bein-sports-vlc.m3u — VLC-compatible playlist (tokens expire)

### 10. Usage
```
python3 /home/zs/bein-server-v6.py
# Open http://localhost:8000/ in browser
```

## Alternative Sources (from original M3U)
- VACO: https://pub-b6a2e12c8294473a88fb9c317217dbbc.r2.dev/Bein{1-6}.m3u8
  (Cloudflare protected, 403 from browser)
- BUZ: man1ted.com API (working, used in this project)
- YallaHD: https://tv.fan7live.workers.dev/live/beINAR/index.m3u8
  (may work as backup)
