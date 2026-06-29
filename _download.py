import urllib.request, sys, os, time

CDN_URLS = [
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "https://hub.gitmirror.com/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "https://ghfast.top/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
]

SLOW_THRESHOLD = 30
SLOW_TIMEOUT = 30

def download_one(url, dest):
    print(f'  Trying: {url.split("/")[2]}...')

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=30)
        total = int(resp.headers.get('Content-Length', 0))

        if total > 0:
            print(f'  Size: {total // 1024 // 1024}MB')
        else:
            print(f'  Size: unknown')

        with open(dest, 'wb') as f:
            downloaded = 0
            last_time = time.time()
            last_bytes = 0
            slow_start = None

            while True:
                chunk = resp.read(81920)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                now = time.time()
                elapsed = now - last_time

                if total > 0:
                    pct = downloaded * 100 // total
                    bar = '#' * (pct // 2) + '-' * (50 - pct // 2)
                    speed = len(chunk) / max(elapsed, 0.001) / 1024
                    sys.stdout.write(f'\r  [{bar}] {pct}% ({speed:.0f}KB/s)')
                    sys.stdout.flush()

                    speed_kbps = (downloaded - last_bytes) / max(elapsed, 0.001) / 1024
                    if speed_kbps < SLOW_THRESHOLD:
                        if slow_start is None:
                            slow_start = now
                        elif now - slow_start > SLOW_TIMEOUT:
                            print(f'\n  Too slow ({speed_kbps:.0f}KB/s < {SLOW_THRESHOLD}KB/s for {SLOW_TIMEOUT}s), trying next...')
                            resp.close()
                            return False
                    else:
                        slow_start = None

                    last_time = now
                    last_bytes = downloaded

        print()
        print('  Download complete!')
        resp.close()
        return True

    except Exception as e:
        print(f'\n  Failed: {e}')
        if os.path.exists(dest):
            os.remove(dest)
        return False


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get('TEMP', ''), 'ffmpeg-release-essentials.zip')

    urls = []
    for arg in sys.argv[1:]:
        if arg.startswith('http'):
            urls.append(arg)

    if not urls:
        urls = CDN_URLS

    for i, url in enumerate(urls):
        print(f'  Source {i+1}/{len(urls)}')
        if download_one(url, dest):
            sys.exit(0)

    print('\n  All sources failed!')
    sys.exit(1)


if __name__ == '__main__':
    main()