import os
import re
import sys
import urllib.parse
import urllib.request
import http.server
import functools
import threading

PORT = 8000
PROXY_PREFIX = '/proxy/'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024

M3U8_CONTENT_TYPES = (
    'application/vnd.apple.mpegurl',
    'application/x-mpegurl',
    'audio/mpegurl',
    'audio/x-mpegurl',
)


class CORSProxyHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith(PROXY_PREFIX):
            self._handle_proxy()
        else:
            super().do_GET()

    def _proxy_wrap(self, target_url):
        base = f'http://localhost:{self.server.server_port}'
        return base + PROXY_PREFIX + urllib.parse.quote(target_url, safe='')

    def _rewrite_m3u8(self, content, base_url):
        lines = content.split('\n')
        rewritten = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                if 'URI="' in stripped:
                    def replace_uri(m):
                        uri = m.group(1)
                        if uri.startswith('http://') or uri.startswith('https://'):
                            return 'URI="' + self._proxy_wrap(uri) + '"'
                        abs_uri = urllib.parse.urljoin(base_url, uri)
                        return 'URI="' + self._proxy_wrap(abs_uri) + '"'
                    stripped = re.sub(r'URI="([^"]+)"', replace_uri, stripped)
                rewritten.append(stripped)
                continue

            if stripped.startswith('http://') or stripped.startswith('https://'):
                rewritten.append(self._proxy_wrap(stripped))
            else:
                abs_url = urllib.parse.urljoin(base_url, stripped)
                rewritten.append(self._proxy_wrap(abs_url))

        return '\n'.join(rewritten)

    def _send_proxy_error(self, code, message):
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            body = f'{code} {message}'.encode('utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def _handle_proxy(self):
        encoded_url = self.path[len(PROXY_PREFIX):]
        target_url = urllib.parse.unquote(encoded_url)

        if not target_url.startswith(('http://', 'https://')):
            self._send_proxy_error(400, 'Invalid proxy target URL')
            return

        try:
            req = urllib.request.Request(target_url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept', '*/*')

            with urllib.request.urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get('Content-Type', 'application/octet-stream').lower()
                data = resp.read(MAX_CONTENT_LENGTH)

                is_m3u8 = any(ct in content_type for ct in M3U8_CONTENT_TYPES)
                if not is_m3u8:
                    is_m3u8 = target_url.endswith('.m3u8') or target_url.endswith('.m3u')

                if is_m3u8:
                    try:
                        text = data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            text = data.decode('latin-1')
                        except Exception:
                            text = data.decode('utf-8', errors='replace')
                    text = self._rewrite_m3u8(text, target_url)
                    data = text.encode('utf-8')
                    content_type = 'application/vnd.apple.mpegurl'

                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            self._send_proxy_error(e.code, e.reason)
        except Exception as e:
            self._send_proxy_error(502, f'Proxy error: {str(e)}')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def end_headers(self):
        if not self.path.startswith(PROXY_PREFIX):
            self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        msg = format % args
        if '/proxy/' in msg and '.ts' in msg:
            return
        super().log_message(format, *args)


class ThreadedHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    base_dir = os.path.dirname(os.path.abspath(__file__))
    serve_dir = os.path.join(base_dir, '.github', 'workflows')
    handler = functools.partial(CORSProxyHandler, directory=serve_dir)

    with ThreadedHTTPServer(('', port), handler) as httpd:
        print(f'Server started at http://localhost:{port}')
        print(f'Serving: {serve_dir}')
        print(f'CORS proxy: http://localhost:{port}/proxy/<encoded_url>')
        print('Press Ctrl+C to stop')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped.')


if __name__ == '__main__':
    main()