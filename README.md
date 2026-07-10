# BEIN Sports Streaming

Free BEIN Sports streaming proxy — watch all 12 BEIN channels (BEIN Sports 1-6 & BEIN Sports MAX 1-6) via a local proxy or Vercel deployment.

## Features

- **12 BEIN channels** — BEIN Sports 1-6 + BEIN Sports MAX 1-6
- **Vercel deployment** — public URL, serverless functions
- **Local proxy** — Python server with BuzCup User-Agent injection
- **Mobile & TV friendly UI** — responsive dark theme
- **VLC playlist** — `.m3u` for desktop playback
- **Multi-source** — man1ted.com API (primary)

## Quick Start

### Option 1: Vercel (recommended)

```bash
vercel deploy
```

Or just visit https://adam-bein.vercel.app

### Option 2: Local Proxy

```bash
python3 bein-server-v6.py
# → http://localhost:8000
```

### Option 3: VLC

Open `bein-sports-vlc.m3u` in VLC.

## API Endpoints

| Endpoint | Description |
|---|---|
| `/` | Main streaming UI |
| `/api/channel?ch=CHANNEL` | Get stream token for channel |
| `/api/proxy?url=URL` | Proxy M3U8/TS segments |

### Channel IDs

- `beee1` — BEIN Sports 1
- `beee2` — BEIN Sports 2
- `beee3` — BEIN Sports 3
- `beee4` — BEIN Sports 4
- `beee5` — BEIN Sports 5
- `beee6` — BEIN Sports 6
- `bemax1` — BEIN Sports MAX 1
- `bemax2` — BEIN Sports MAX 2
- `bemax3` — BEIN Sports MAX 3
- `bemax4` — BEIN Sports MAX 4
- `bemax5` — BEIN Sports MAX 5
- `bemax6` — BEIN Sports MAX 6

## Architecture

```
Browser ──→ Vercel ──→ man1ted.com API ──→ BEIN stream source
               │
          [BuzCup/2.0 User-Agent]
          [Stream proxy + URL rewriting]
```

## Tech Stack

- **Frontend:** HTML/CSS/JS (dark theme, mobile-first)
- **Backend:** Python serverless functions (Vercel)
- **Source:** man1ted.com API with BuzCup credentials
- **Proxy:** HLS segment proxying with playlist rewriting

## Reverse Engineering Guide

See `bein-reverse-engineering-guide.md` for the full technical breakdown of how the streams were extracted from the Buz Cup Android app.

## Notes

- Stream quality is source-limited to ~480p (500 Kbps)
- Quality badges show honest labels
- All traffic routes through Tor for OPSEC

## License

For educational purposes only.
