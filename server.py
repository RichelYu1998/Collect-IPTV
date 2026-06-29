import os
import re
import sys
import platform
import socket
import subprocess
import hashlib
import time
import tempfile
import shutil
import json
import tarfile
import zipfile
import atexit
import urllib.parse
import urllib.request
import http.server
import functools
import threading
from pathlib import Path

PORT = int(os.environ.get('IPTV_SERVER_PORT', '8000'))
PROXY_PREFIX = '/proxy/'
TRANSCODE_PREFIX = '/transcode/'
TSTREAM_PREFIX = '/tstream/'
MAX_CONTENT_LENGTH = int(os.environ.get('IPTV_MAX_CONTENT_LENGTH', str(50 * 1024 * 1024)))
TRANSCODE_AUDIO_BITRATE = os.environ.get('IPTV_TRANSCODE_AUDIO_BITRATE', '128k')
TRANSCODE_AUDIO_CHANNELS = os.environ.get('IPTV_TRANSCODE_AUDIO_CHANNELS', '2')
TRANSCODE_HLS_TIME = os.environ.get('IPTV_TRANSCODE_HLS_TIME', '4')
TRANSCODE_HLS_LIST_SIZE = os.environ.get('IPTV_TRANSCODE_HLS_LIST_SIZE', '6')
TRANSCODE_SESSION_TIMEOUT = int(os.environ.get('IPTV_TRANSCODE_SESSION_TIMEOUT', '600'))
PROXY_TIMEOUT = int(os.environ.get('IPTV_PROXY_TIMEOUT', '15'))
LAN_IP_DETECT_HOST = os.environ.get('IPTV_LAN_IP_DETECT_HOST', '8.8.8.8')
LAN_IP_DETECT_PORT = int(os.environ.get('IPTV_LAN_IP_DETECT_PORT', '80'))

FFMPEG_PATH = None
TRANSCODE_DIR = None
transcode_sessions = {}
transcode_lock = threading.Lock()
audio_probe_cache = {}
audio_probe_lock = threading.Lock()

PROJECT_ROOT = Path(__file__).parent
FFMPEG_INSTALL_DIR = PROJECT_ROOT / 'ffmpeg'

M3U8_CONTENT_TYPES = (
    'application/vnd.apple.mpegurl',
    'application/x-mpegurl',
    'audio/mpegurl',
    'audio/x-mpegurl',
)


def detect_os():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == 'windows':
        if machine in ['amd64', 'x86_64']:
            return {'os': 'windows', 'arch': 'win64', 'ext': '.exe'}
        elif machine in ['arm64', 'aarch64']:
            return {'os': 'windows', 'arch': 'winarm64', 'ext': '.exe'}
        else:
            return {'os': 'windows', 'arch': 'win32', 'ext': '.exe'}
    elif system == 'darwin':
        if machine in ['arm64', 'aarch64']:
            return {'os': 'mac', 'arch': 'mac_arm64', 'ext': ''}
        else:
            return {'os': 'mac', 'arch': 'mac_x64', 'ext': ''}
    elif system == 'linux':
        if machine in ['arm64', 'aarch64']:
            return {'os': 'linux', 'arch': 'linux_arm64', 'ext': ''}
        elif machine in ['x86_64', 'amd64']:
            return {'os': 'linux', 'arch': 'linux_x64', 'ext': ''}
        else:
            return {'os': 'linux', 'arch': 'linux_32', 'ext': ''}
    else:
        raise Exception(f"Unsupported OS: {system}")


def check_ffmpeg_installed():
    os_info = detect_os()
    ffmpeg_path = FFMPEG_INSTALL_DIR / 'bin' / f'ffmpeg{os_info["ext"]}'
    if ffmpeg_path.exists():
        try:
            result = subprocess.run(
                [str(ffmpeg_path), '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"[*] FFmpeg already installed: {version}")
                print(f"    Location: {ffmpeg_path}")
                return True
        except:
            pass
    return False


def download_file(url, dest_path):
    print(f"    Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, str(dest_path))
        file_size = os.path.getsize(dest_path)
        print(f"    Downloaded: {file_size / 1024 / 1024:.1f} MB")
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def extract_zip_generic(filepath, dest):
    try:
        with zipfile.ZipFile(str(filepath), 'r') as zip_ref:
            zip_ref.extractall(str(dest))
        for root, dirs, files in os.walk(str(dest)):
            for f in files:
                if f == 'ffmpeg.exe' or f == 'ffmpeg':
                    return os.path.join(root, f)
        return None
    except Exception as e:
        print(f"    Extraction failed: {e}")
        return None


def extract_zip_windows(filepath, dest):
    return extract_zip_generic(filepath, dest)


def extract_zip_mac(filepath, dest):
    try:
        with zipfile.ZipFile(str(filepath), 'r') as zip_ref:
            zip_ref.extractall(str(dest))
        ffmpeg_bin = dest / 'ffmpeg'
        if ffmpeg_bin.exists():
            return str(ffmpeg_bin)
        return None
    except Exception as e:
        print(f"    Extraction failed: {e}")
        return None


def install_via_package_manager(cmd, name):
    print(f"    Installing via {name}...")
    try:
        full_cmd = ' '.join(cmd) if isinstance(cmd, list) else cmd
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"    Installation successful!")
            return True
        else:
            print(f"    Installation failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("    Installation timeout (5 minutes)")
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


def setup_ffmpeg():
    print("=" * 60)
    print("FFmpeg Setup Tool")
    print("=" * 60)

    os_info = detect_os()
    print(f"\n[*] Detected OS: {os_info['os'].upper()} ({os_info['arch']})")

    if check_ffmpeg_installed():
        print("\nFFmpeg is ready to use!")
        return True

    print(f"\n[*] FFmpeg will be installed to: {FFMPEG_INSTALL_DIR}")

    sources = []

    if os_info['os'] == 'windows':
        sources = [
            {
                'name': 'Gyan.dev (Official)',
                'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
                'extract_func': extract_zip_windows
            },
            {
                'name': 'BtbN (GitHub)',
                'url': f'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-{os_info["arch"]}-gpl.zip',
                'extract_func': extract_zip_generic
            }
        ]
    elif os_info['os'] == 'mac':
        sources = [
            {
                'name': 'evermeet.cx',
                'url': 'https://evermeet.cx/ffmpeg/getrelease/zip',
                'extract_func': extract_zip_mac
            },
            {
                'name': 'Homebrew',
                'url': None,
                'install_cmd': ['brew', 'install', 'ffmpeg']
            }
        ]
    elif os_info['os'] == 'linux':
        if shutil.which('apt-get'):
            sources.append({
                'name': 'APT (Ubuntu/Debian)',
                'url': None,
                'install_cmd': ['sudo', 'apt-get', 'update', '&&', 'sudo', 'apt-get', 'install', '-y', 'ffmpeg']
            })
        elif shutil.which('dnf'):
            sources.append({
                'name': 'DNF (Fedora)',
                'url': None,
                'install_cmd': ['sudo', 'dnf', 'install', '-y', 'ffmpeg']
            })
        elif shutil.which('yum'):
            sources.append({
                'name': 'YUM (CentOS/RHEL)',
                'url': None,
                'install_cmd': ['sudo', 'yum', 'install', '-y', 'ffmpeg']
            })
        elif shutil.which('pacman'):
            sources.append({
                'name': 'Pacman (Arch)',
                'url': None,
                'install_cmd': ['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg']
            })

    success = False

    for i, source in enumerate(sources, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(sources)}] Trying: {source['name']}")
        print('=' * 60)

        if source.get('install_cmd'):
            if install_via_package_manager(source['install_cmd'], source['name']):
                success = True
                break
            continue

        if not source.get('url'):
            continue

        temp_download = PROJECT_ROOT / '_temp_ffmpeg.zip'
        temp_extract = PROJECT_ROOT / '_temp_ffmpeg_extract'

        if os.path.exists(temp_extract):
            shutil.rmtree(temp_extract, ignore_errors=True)

        if download_file(source['url'], temp_download):
            extract_func = source.get('extract_func')
            if extract_func and callable(extract_func):
                try:
                    result = extract_func(temp_download, temp_extract)
                    if result:
                        if os_info['os'] != 'mac':
                            src = Path(result)
                            dst = FFMPEG_INSTALL_DIR
                            if dst.exists():
                                shutil.rmtree(dst)
                            shutil.move(src, dst)
                        success = True
                        break
                except Exception as e:
                    print(f"  ✗ Extraction failed: {e}")

        if temp_download.exists():
            os.remove(temp_download)

    if os.path.exists(PROJECT_ROOT / '_temp_ffmpeg_extract'):
        shutil.rmtree(PROJECT_ROOT / '_temp_ffmpeg_extract', ignore_errors=True)

    if success:
        print("\n" + "=" * 60)
        print("[*] FFmpeg installation completed successfully!")
        print("=" * 60)
        return check_ffmpeg_installed()
    else:
        print("\n" + "=" * 60)
        print("[!] All installation methods failed")
        print("=" * 60)
        print("\nManual installation options:")
        if os_info['os'] == 'windows':
            print("  1. Download from https://www.gyan.dev/ffmpeg/builds/")
            print(f"  2. Extract to: {FFMPEG_INSTALL_DIR}")
        elif os_info['os'] == 'mac':
            print("  1. Install Homebrew: https://brew.sh/")
            print("  2. Run: brew install ffmpeg")
        elif os_info['os'] == 'linux':
            print("  1. Use your package manager:")
            print("     Ubuntu/Debian: sudo apt install ffmpeg")
            print("     Fedora: sudo dnf install ffmpeg")
            print("     Arch: sudo pacman -S ffmpeg")
        return False


def find_ffmpeg():
    path = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    if path:
        return path
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext = '.exe' if os.name == 'nt' else ''
    
    project_ffmpeg = os.path.join(base_dir, 'ffmpeg', 'bin', f'ffmpeg{ext}')
    if os.path.isfile(project_ffmpeg):
        return project_ffmpeg

    if os.name == 'nt':
        venv_ffmpeg = os.path.join(base_dir, '.venv', 'ffmpeg', 'bin', f'ffmpeg{ext}')
        if os.path.isfile(venv_ffmpeg):
            return venv_ffmpeg
        for env_var in ['ProgramFiles', 'ProgramFiles(x86)', 'LOCALAPPDATA']:
            base = os.environ.get(env_var, '')
            if base:
                for sub in [['FFmpeg', 'bin', f'ffmpeg{ext}'], ['ffmpeg', 'bin', f'ffmpeg{ext}']]:
                    candidate = os.path.join(base, *sub)
                    if os.path.isfile(candidate):
                        return candidate
        choco = shutil.which('choco')
        if choco:
            candidate = os.path.join(os.path.dirname(os.path.dirname(choco)), 'bin', f'ffmpeg{ext}')
            if os.path.isfile(candidate):
                return candidate
    else:
        venv_ffmpeg = os.path.join(base_dir, '.venv', 'ffmpeg', 'bin', 'ffmpeg')
        if os.path.isfile(venv_ffmpeg):
            return venv_ffmpeg
        
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/usr/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            '/snap/bin/ffmpeg',
            '/flatpak/ bin/ffmpeg',
        ]
        
        for fp in common_paths:
            if os.path.isfile(fp):
                return fp
                
        try:
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
            
        try:
            result = subprocess.run(['whereis', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.split()[1:]
                for fp in paths:
                    if os.path.isfile(fp):
                        return fp
        except Exception:
            pass
            
    return None


def find_ffprobe():
    if not FFMPEG_PATH:
        return None
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    ffmpeg_name = os.path.basename(FFMPEG_PATH)
    ffprobe_name = ffmpeg_name.replace('ffmpeg', 'ffprobe')
    candidate = os.path.join(ffmpeg_dir, ffprobe_name)
    if os.path.isfile(candidate):
        return candidate
    path = shutil.which('ffprobe') or shutil.which('ffprobe.exe')
    if path:
        return path
    return None


def probe_audio_info(url):
    ffprobe_path = find_ffprobe()
    if not ffprobe_path:
        return {'has_audio': None, 'error': 'no_ffprobe'}

    cmd = [
        ffprobe_path,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        '-select_streams', 'a',
        '-analyzeduration', '5000000',
        '-probesize', '5000000',
        '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        url,
    ]

    try:
        kwargs = {
            'capture_output': True,
            'text': True,
            'timeout': 15,
        }
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(cmd, **kwargs)
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        if not streams:
            return {'has_audio': False, 'codecs': [], 'unsupported': []}
        codecs = []
        unsupported = []
        for s in streams:
            codec = s.get('codec_name', 'unknown')
            codecs.append(codec)
            if codec in ('ac3', 'eac3', 'dts', 'dtshd', 'truehd', 'mlp'):
                unsupported.append(codec)
        return {'has_audio': True, 'codecs': codecs, 'unsupported': unsupported}
    except subprocess.TimeoutExpired:
        return {'has_audio': None, 'error': 'timeout'}
    except json.JSONDecodeError:
        return {'has_audio': None, 'error': 'parse_error'}
    except Exception as e:
        return {'has_audio': None, 'error': str(e)}


def probe_audio_cached(url):
    with audio_probe_lock:
        cached = audio_probe_cache.get(url)
        if cached is not None:
            age = time.time() - cached['time']
            if age < 300:
                return cached['result']

    result = probe_audio_info(url)

    with audio_probe_lock:
        audio_probe_cache[url] = {'time': time.time(), 'result': result}

        if len(audio_probe_cache) > 500:
            sorted_items = sorted(audio_probe_cache.items(), key=lambda x: x[1]['time'])
            for k, _ in sorted_items[:200]:
                del audio_probe_cache[k]

    return result


def needs_transcode(url):
    if not FFMPEG_PATH:
        return False
    info = probe_audio_cached(url)
    if info.get('has_audio') and info.get('unsupported'):
        return True
    return False


def start_transcode_session(url):
    with transcode_lock:
        session_id = hashlib.md5(url.encode()).hexdigest()[:12]

        if session_id in transcode_sessions:
            session = transcode_sessions[session_id]
            session['last_access'] = time.time()
            if session['process'].poll() is None:
                return session_id
            try:
                shutil.rmtree(session['dir'], ignore_errors=True)
            except Exception:
                pass
            del transcode_sessions[session_id]

        output_dir = os.path.join(TRANSCODE_DIR, session_id)
        os.makedirs(output_dir, exist_ok=True)

        for f in os.listdir(output_dir):
            try:
                os.remove(os.path.join(output_dir, f))
            except Exception:
                pass

        cmd = [
            FFMPEG_PATH,
            '-i', url,
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', TRANSCODE_AUDIO_BITRATE, '-ac', TRANSCODE_AUDIO_CHANNELS,
            '-f', 'hls',
            '-hls_time', TRANSCODE_HLS_TIME,
            '-hls_list_size', TRANSCODE_HLS_LIST_SIZE,
            '-hls_flags', 'delete_segments+append_list',
            '-hls_segment_filename', os.path.join(output_dir, 'seg_%03d.ts'),
            os.path.join(output_dir, 'index.m3u8'),
            '-y',
            '-loglevel', 'error',
        ]

        kwargs = {
            'stdout': subprocess.DEVNULL,
            'stderr': subprocess.PIPE,
        }
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(cmd, **kwargs)

        transcode_sessions[session_id] = {
            'process': process,
            'dir': output_dir,
            'last_access': time.time(),
            'url': url,
        }

        return session_id


def stop_transcode_session(session_id):
    with transcode_lock:
        if session_id not in transcode_sessions:
            return
        session = transcode_sessions[session_id]
        try:
            session['process'].terminate()
            session['process'].wait(timeout=5)
        except Exception:
            try:
                session['process'].kill()
            except Exception:
                pass
        try:
            shutil.rmtree(session['dir'], ignore_errors=True)
        except Exception:
            pass
        del transcode_sessions[session_id]


def cleanup_all_transcodes():
    with transcode_lock:
        for sid in list(transcode_sessions.keys()):
            session = transcode_sessions[sid]
            try:
                session['process'].terminate()
                session['process'].wait(timeout=3)
            except Exception:
                try:
                    session['process'].kill()
                except Exception:
                    pass
            try:
                shutil.rmtree(session['dir'], ignore_errors=True)
            except Exception:
                pass
        transcode_sessions.clear()
    if TRANSCODE_DIR and os.path.isdir(TRANSCODE_DIR):
        try:
            shutil.rmtree(TRANSCODE_DIR, ignore_errors=True)
        except Exception:
            pass


def cleanup_old_sessions():
    now = time.time()
    with transcode_lock:
        for sid in list(transcode_sessions.keys()):
            session = transcode_sessions[sid]
            if now - session['last_access'] > TRANSCODE_SESSION_TIMEOUT:
                try:
                    session['process'].terminate()
                    session['process'].wait(timeout=3)
                except Exception:
                    try:
                        session['process'].kill()
                    except Exception:
                        pass
                try:
                    shutil.rmtree(session['dir'], ignore_errors=True)
                except Exception:
                    pass
                del transcode_sessions[sid]


class CORSProxyHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith(PROXY_PREFIX):
            self._handle_proxy()
        elif self.path.startswith(TRANSCODE_PREFIX):
            self._handle_transcode()
        elif self.path.startswith(TSTREAM_PREFIX):
            self._handle_tstream()
        else:
            super().do_GET()

    def _proxy_wrap(self, target_url):
        host = self.headers.get('Host', f'localhost:{self.server.server_port}')
        base = f'http://{host}'
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

            with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
                content_type = resp.headers.get('Content-Type', 'application/octet-stream').lower()
                data = resp.read(MAX_CONTENT_LENGTH)

                is_m3u8 = any(ct in content_type for ct in M3U8_CONTENT_TYPES)
                if not is_m3u8:
                    is_m3u8 = target_url.endswith('.m3u8') or target_url.endswith('.m3u')

                if is_m3u8 and needs_transcode(target_url):
                    session_id = start_transcode_session(target_url)
                    tstream_url = f'/tstream/{session_id}/index.m3u8'
                    self.send_response(302)
                    self.send_header('Location', tstream_url)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    return

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

    def _handle_transcode(self):
        path_part = self.path[len(TRANSCODE_PREFIX):]

        if path_part.startswith('start/'):
            encoded_url = path_part[6:]
            target_url = urllib.parse.unquote(encoded_url)
            if not target_url.startswith(('http://', 'https://')):
                self._send_json_error(400, 'Invalid URL')
                return
            if not FFMPEG_PATH:
                self._send_json_error(503, 'FFmpeg not installed')
                return
            try:
                session_id = start_transcode_session(target_url)
                self._send_json_response({'session_id': session_id, 'url': target_url})
            except Exception as e:
                self._send_json_error(500, str(e))
            return

        if path_part.startswith('status/'):
            session_id = path_part[7:].split('/')[0].split('?')[0]
            with transcode_lock:
                session = transcode_sessions.get(session_id)
            if not session:
                self._send_json_response({'session_id': session_id, 'ready': False, 'alive': False})
                return
            m3u8_path = os.path.join(session['dir'], 'index.m3u8')
            ready = os.path.isfile(m3u8_path) and os.path.getsize(m3u8_path) > 100
            alive = session['process'].poll() is None
            self._send_json_response({
                'session_id': session_id,
                'ready': ready,
                'alive': alive,
            })
            return

        if path_part.startswith('stop/'):
            session_id = path_part[5:].split('/')[0].split('?')[0]
            stop_transcode_session(session_id)
            self._send_json_response({'ok': True})
            return

        if path_part.startswith('probe/'):
            encoded_url = path_part[6:]
            target_url = urllib.parse.unquote(encoded_url)
            if not target_url.startswith(('http://', 'https://')):
                self._send_json_error(400, 'Invalid URL')
                return
            result = probe_audio_info(target_url)
            self._send_json_response(result)
            return

        if path_part.startswith('check/'):
            self._send_json_response({'ffmpeg': FFMPEG_PATH is not None})
            return

        self._send_json_error(400, 'Unknown transcode action')

    def _handle_tstream(self):
        path_part = self.path[len(TSTREAM_PREFIX):]
        parts = path_part.split('/', 1)
        if len(parts) != 2:
            self._send_proxy_error(400, 'Invalid tstream path')
            return

        session_id, filename = parts[0], parts[1]

        with transcode_lock:
            session = transcode_sessions.get(session_id)
        if not session:
            self._send_proxy_error(404, 'Session not found')
            return

        session['last_access'] = time.time()
        filepath = os.path.join(session['dir'], filename)

        if not os.path.isfile(filepath):
            self._send_proxy_error(404, 'File not found yet')
            return

        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except Exception:
            self._send_proxy_error(500, 'Read error')
            return

        if filename.endswith('.m3u8'):
            try:
                text = data.decode('utf-8')
                rewritten = []
                for line in text.split('\n'):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        rewritten.append(stripped)
                    elif stripped.endswith('.ts') or stripped.endswith('.m3u8'):
                        rewritten.append(f'{TSTREAM_PREFIX}{session_id}/{stripped}')
                    else:
                        rewritten.append(stripped)
                data = '\n'.join(rewritten).encode('utf-8')
            except Exception:
                pass
            content_type = 'application/vnd.apple.mpegurl'
        elif filename.endswith('.ts'):
            content_type = 'video/mp2t'
        else:
            content_type = 'application/octet-stream'

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(data)

    def _send_json_response(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def _send_json_error(self, code, message):
        data = json.dumps({'error': message}, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def end_headers(self):
        if not self.path.startswith(PROXY_PREFIX) and not self.path.startswith(TSTREAM_PREFIX):
            self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        msg = format % args
        if '.ts' in msg and ('/proxy/' in msg or '/tstream/' in msg):
            return
        super().log_message(format, *args)


class ThreadedHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((LAN_IP_DETECT_HOST, LAN_IP_DETECT_PORT))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def main():
    global FFMPEG_PATH, TRANSCODE_DIR

    FFMPEG_PATH = find_ffmpeg()
    TRANSCODE_DIR = tempfile.mkdtemp(prefix='iptv_tc_')
    atexit.register(cleanup_all_transcodes)

    port = int(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else PORT
    serve_dir = str(PROJECT_ROOT / '.github' / 'workflows')
    handler = functools.partial(CORSProxyHandler, directory=serve_dir)

    with ThreadedHTTPServer(('', port), handler) as httpd:
        print(f'  访问地址: http://127.0.0.1:{port}')
        lan_ip = get_lan_ip()
        if lan_ip:
            print(f'  局域网地址: http://{lan_ip}:{port}')
        print(f'  Serving: {serve_dir}')
        print(f'  CORS proxy: /proxy/<encoded_url>')
        if FFMPEG_PATH:
            print(f'  音频转码: 已启用 (FFmpeg: {FFMPEG_PATH})')
        else:
            print(f'  音频转码: 未启用 (未找到FFmpeg，AC3/EAC3音频将无声音)')
        print('  Press Ctrl+C to stop')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped.')
            cleanup_all_transcodes()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--setup-ffmpeg':
        success = setup_ffmpeg()
        sys.exit(0 if success else 1)
    else:
        main()