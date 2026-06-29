import urllib.request, sys, os

def main():
    if len(sys.argv) < 3:
        print("Usage: _download.py <url> <dest>")
        sys.exit(1)

    url = sys.argv[1]
    dest = sys.argv[2]

    print(f'  Downloading to {os.path.basename(dest)}...')

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=300)
        total = int(resp.headers.get('Content-Length', 0))

        with open(dest, 'wb') as f:
            downloaded = 0
            while True:
                chunk = resp.read(81920)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    bar = '#' * (pct // 2) + '-' * (50 - pct // 2)
                    sys.stdout.write(f'\r  [{bar}] {pct}%')
                    sys.stdout.flush()

        print()
        print('  Download complete!')
        resp.close()

    except Exception as e:
        print(f'\n  Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()