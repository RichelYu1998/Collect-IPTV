---
name: "iptv-dev"
description: "Collect-IPTV project development guide. Invoke when modifying server.py, index.html, notify.py, iptv_tool.bat/sh, or working on FFmpeg/mpegts.js/email notification features."
---

# Collect-IPTV Development Skill

## Project Overview

IPTV live stream collection tool with auto-collection, deduplication, quality selection, web player, audio transcoding, and email notification.

## Architecture

```
server.py          → Web server (aiohttp), CORS proxy, FFmpeg transcoding, preload cache
output/index.html  → Frontend with mpegts.js player
script/notify.py   → Email notification (MD5 hash change detection)
script/iptv_tool.bat/sh → Startup scripts (env detection → collection → notify → web server)
.github/workflows/iptv.py → Collection script
config/notify.json → Email config
```

## Key Conventions

### Player (mpegts.js)

- Use `mpegts.createPlayer({type:'mse', isLive:true, url}, config)` for initialization
- Attach: `attachMediaElement(video)` then `load()`
- Event: `mpegts.Events.METADATA_ARRIVED` (not MANIFEST_PARSED)
- Error: `mpegts.Events.ERROR` with `mpegts.ErrorTypes.NETWORK_ERROR` / `MEDIA_ERROR`
- Destroy: `unload()` → `detachMediaElement()` → `destroy()`
- Recover: `unload()` → `load()` → `play()`
- Variable: `currentPlayer` (not currentHls)
- Function: `destroyPlayer()` (not destroyHls), `checkAudioTracksFromPlayer()`

### mpegts.js Live Config

```javascript
{
    enableWorker: true,
    enableStashBuffer: false,
    stashInitialSize: 128,
    lazyLoad: false,
    autoCleanupSourceBuffer: true,
    autoCleanupMaxBackwardDuration: 30,
    autoCleanupMinBackwardDuration: 10,
    liveBufferLatencyChasing: true,
    liveBufferLatencyMaxLatency: 6,
    liveBufferLatencyMinRemain: 0.5,
    liveSync: true,
    liveSyncMaxLatency: 6,
}
```

### FFmpeg Transcode Parameters

```python
cmd = [
    FFMPEG_PATH,
    '-nostdin', '-re',
    '-fflags', '+genpts+discardcorrupt',
    '-analyzeduration', '5000000',
    '-probesize', '5000000',
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