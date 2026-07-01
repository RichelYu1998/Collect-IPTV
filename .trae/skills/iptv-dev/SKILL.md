---
name: "iptv-dev"
description: "Collect-IPTV project development guide. Invoke when modifying server.py, index.html, notify.py, iptv_tool.bat/sh, or working on FFmpeg/hls.js/mpegts.js/email notification features."
---

# Collect-IPTV Development Skill

## Project Overview

IPTV live stream collection tool with auto-collection, deduplication, quality selection, web player, audio transcoding, and email notification.

## Architecture

```
server.py          → Web server (aiohttp), CORS proxy, FFmpeg transcoding, preload cache, audio probe
output/index.html  → Frontend with dual-engine player (hls.js + mpegts.js)
script/notify.py   → Email notification (MD5 hash change detection)
script/iptv_tool.bat/sh → Startup scripts (env detection → collection → notify → web server)
.github/workflows/iptv.py → Collection script
config/notify.json → Email config
```

## Key Conventions

### Player - Dual Engine (hls.js + mpegts.js)

**mpegts.js does NOT support HLS/m3u8** — it only handles raw MPEG-TS and FLV streams.
All IPTV sources are HLS (m3u8), so hls.js is the primary player.

#### URL Type Detection

```javascript
const isHlsUrl = proxiedUrl.includes('.m3u8') || proxiedUrl.includes('.m3u') || proxiedUrl.includes('/hls/') || proxiedUrl.includes('/tstream/');
```

#### HLS Player (hls.js) — for m3u8 URLs

- Use `new Hls(config)` for initialization
- Load: `loadSource(url)` then `attachMedia(video)`
- Event: `Hls.Events.MANIFEST_PARSED` (stream ready)
- Error: `Hls.Events.ERROR` with `Hls.ErrorTypes.NETWORK_ERROR` / `MEDIA_ERROR`
- Recover NETWORK: `startLoad()` (retry from last position)
- Recover MEDIA: `recoverMediaError()` (rebuild MSE)
- Destroy: `hls.destroy()`
- Variable: `currentPlayer` (shared between hls.js and mpegts.js)

#### hls.js Live Config

```javascript
{
    enableWorker: true,
    lowLatencyMode: false,
    backBufferLength: 10,
    maxBufferLength: 10,
    maxMaxBufferLength: 30,
    maxBufferSize: 30 * 1000 * 1000,
    maxBufferHole: 0.5,
    liveSyncDurationCount: 3,
    liveMaxLatencyDurationCount: 6,
    liveDurationInfinity: true,
    progressive: true,
    highBufferWatchdogPeriod: 2,
    abrEwmaDefaultEstimate: 800000,
    abrEwmaFastEstimate: 1500000,
    abrBandWidthFactor: 0.7,
    abrBandWidthUpFactor: 1.5,
    startLevel: -1,
    fragLoadingTimeOut: 10000,
    fragLoadingMaxRetry: 3,
    fragLoadingMaxRetryTimeout: 4000,
    manifestLoadingTimeOut: 10000,
    manifestLoadingMaxRetry: 3,
    levelLoadingTimeOut: 10000,
    levelLoadingMaxRetry: 3,
}
```

#### mpegts.js Player — for raw TS/FLV URLs only

- Use `mpegts.createPlayer({type:'mpegts', isLive:true, url}, config)` (NOT 'mse')
- Attach: `attachMediaElement(video)` then `load()`
- Ready events: `MEDIA_INFO` (primary), `METADATA_ARRIVED`, `loadeddata`, `canplay` (fallback)
- Error: `mpegts.Events.ERROR` with `mpegts.ErrorTypes.NETWORK_ERROR` / `MEDIA_ERROR`
- Destroy: `unload()` → `detachMediaElement()` → `destroy()`
- Recover: `unload()` → `load()` → `play()`

#### mpegts.js Live Config

```javascript
{
    enableWorker: true,
    enableStashBuffer: true,
    stashInitialSize: 1024,
    lazyLoad: false,
    autoCleanupSourceBuffer: true,
    autoCleanupMaxBackwardDuration: 30,
    autoCleanupMinBackwardDuration: 10,
    liveBufferLatencyChasing: true,
    liveBufferLatencyMaxLatency: 10,
    liveBufferLatencyMinRemain: 2,
}
```

#### Shared Functions

- `destroyPlayer()` — checks `instanceof Hls` for hls.js, else mpegts.js destroy flow
- `checkAudioTracksFromPlayer(info)` — handles both hls.js and mpegts.js track info formats
- `currentPlayer` — shared variable, can be either Hls or mpegts player instance

### Audio Probe (server.py)

#### Fast Probe: `_probe_audio_fast(url)`

Python-native TS stream parser — no ffprobe/ffmpeg needed for non-encrypted streams:

1. Download m3u8 → parse first TS segment URL
2. Download 256KB TS data
3. Parse TS packets (188 bytes each): sync byte 0x47, PID, PUSI flag
4. Handle adaptation field and pointer byte (PUSI packets)
5. Identify PES stream_id: 0xC0-0xDF = MPEG audio, 0xBD = private stream
6. Detect codec: mp2/mp3 (MPEG audio), ac3/eac3/dts (private stream sub_id)
7. Encrypted stream detection: pointer byte > 183 → switch to ffmpeg probe

#### Fallback Chain

`_probe_audio_fast()` → `ffprobe` → `ffmpeg -i` → return error

- Non-encrypted streams: ~1-2 seconds (fast probe)
- Encrypted streams: ~8-12 seconds (ffmpeg probe with larger probesize)
- ffprobe: analyzeduration/probesize 2M, timeout 10s
- ffmpeg encrypted: probesize 1M, timeout 12s
- ffmpeg non-encrypted: probesize 500K, timeout 8s

### FFmpeg Transcode Parameters

```python
cmd = [
    FFMPEG_PATH,
    '-nostdin',
    '-fflags', '+genpts+discardcorrupt+fastseek',
    '-analyzeduration', '3000000',
    '-probesize', '3000000',
    '-i', url,
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', TRANSCODE_AUDIO_BITRATE, '-ac', TRANSCODE_AUDIO_CHANNELS,
    '-sn',
    '-max_delay', '0',
    '-threads', '0',
    '-f', 'hls',
    '-hls_time', TRANSCODE_HLS_TIME,
    '-hls_list_size', TRANSCODE_HLS_LIST_SIZE,
    '-hls_flags', 'delete_segments+append_list+independent_segments',
    '-hls_segment_filename', os.path.join(output_dir, 'seg_%03d.ts'),
    os.path.join(output_dir, 'index.m3u8'),
    '-y',
    '-loglevel', 'error',
]
```

Key changes from v2.9:
- Removed `-re` flag (was limiting output rate, causing delay accumulation)
- analyzeduration/probesize: 5M → 3M (faster startup)
- Added `+fastseek` to fflags

### Proxy Optimization

- TS segments: **streaming transfer** (read 64KB → write → flush), not download-then-forward
- Preload wait: 200ms (was 500ms)
- TS caching: cache while forwarding, don't block transfer

### Email Notification (notify.py)

- Watch files: `file/best_sorted.m3u`, `file/best_sorted.m3u8`
- Hash storage: `config/.notify_hashes.json`
- First run: send email (mark as "new")
- File changed (hash differs): send email (mark as "updated")
- No change: skip sending
- Scripts call: `notify.py --once` after collection
- Config: `config/notify.json`

### Shell Scripts

- bat/sh both call `notify.py --once` after IPTV collection
- bat: `%PYTHON_CMD% "%~dp0notify.py" --once`
- sh: `$PYTHON_CMD "$WORK_DIR/script/notify.py" --once`
- Working dir: bat uses `cd /d "%~dp0.."`, sh uses `cd "$WORK_DIR"`

### Python Style

- Encoding: always specify `encoding='utf-8'`
- Paths: use `pathlib.Path`
- Async: `aiohttp` + `asyncio`
- Config: environment variables with `os.environ.get()` and defaults
- Version: single source in `README.md`, format `### v1.2.3 (YYYY-MM-DD)`

### File Locations

- M3U/M3U8 output: `file/best_sorted.m3u`, `file/best_sorted.m3u8`
- Web static: `output/` directory
- FFmpeg binaries: `ffmpeg/{windows,linux,macos}/bin/`
- Cache files: `file/.cdn_cache.json`, `file/.stream_cache.json`, `file/.source_cache.json`