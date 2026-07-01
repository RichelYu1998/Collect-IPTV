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
import queue
import concurrent.futures
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
PROXY_TIMEOUT = int(os.environ.get('IPTV_PROXY_TIMEOUT', '30'))


FFMPEG_PATH = None
TRANSCODE_DIR = None
transcode_sessions = {}
transcode_lock = threading.Lock()
audio_probe_cache = {}
audio_probe_lock = threading.Lock()

PRELOAD_MAX_ENTRIES = int(os.environ.get('IPTV_PRELOAD_MAX_ENTRIES', '500'))
PRELOAD_MAX_SIZE = int(os.environ.get('IPTV_PRELOAD_MAX_SIZE', str(500 * 1024 * 1024)))
PRELOAD_TTL = int(os.environ.get('IPTV_PRELOAD_TTL', '300'))
PRELOAD_WORKERS = int(os.environ.get('IPTV_PRELOAD_WORKERS', '10'))
PRELOAD_SYNC_FIRST = int(os.environ.get('IPTV_PRELOAD_SYNC_FIRST', '5'))
PRELOAD_SYNC_ALL = os.environ.get('IPTV_PRELOAD_SYNC_ALL', '').lower() in ('1', 'true', 'yes')
preload_cache = {}
preload_order = []
preload_size = 0
preload_lock = threading.Lock()
preload_executor = None
preload_pipelines = {}

PROJECT_ROOT = Path(__file__).parent

def get_ffmpeg_platform_dir():
    """根据操作系统返回对应的 FFmpeg 预编译版本目录"""
    platform_dirs = {
        'windows': 'windows',
        'linux': 'linux',
        'mac': 'macos',
    }
    
    try:
        os_info = detect_os()
        current_os = os_info.get('os', '').lower()
        platform_dir = platform_dirs.get(current_os, current_os)
        
        # 优先使用项目根目录下的预编译版本
        prebuilt_dir = PROJECT_ROOT / 'ffmpeg' / platform_dir / 'bin'
        
        if prebuilt_dir.exists():
            print(f"[*] 使用预编译 FFmpeg: {prebuilt_dir.resolve()}")
            return prebuilt_dir.resolve()  # 规范化路径
        
        # 回退到 .venv 目录（兼容旧版或自动安装）
        fallback_dir = PROJECT_ROOT / '.venv' / 'ffmpeg'
        print(f"[*] 使用 .venv FFmpeg 目录: {fallback_dir}")
        return fallback_dir.resolve()  # 规范化路径
        
    except Exception as e:
        print(f"[!] 检测系统失败，使用默认路径: {e}")
        return PROJECT_ROOT / '.venv' / 'ffmpeg'


# 初始化时使用临时值，稍后在 main() 中会更新
FFMPEG_INSTALL_DIR = PROJECT_ROOT / '.venv' / 'ffmpeg'

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
    # 确保使用正确的平台目录
    global FFMPEG_INSTALL_DIR
    FFMPEG_INSTALL_DIR = get_ffmpeg_platform_dir()
    os_info = detect_os()
    ffmpeg_path = FFMPEG_INSTALL_DIR / 'bin' / f'ffmpeg{os_info["ext"]}'
    ffprobe_path = FFMPEG_INSTALL_DIR / 'bin' / f'ffprobe{os_info["ext"]}'
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
                if ffprobe_path.exists():
                    print(f"[*] FFprobe already installed")
                    print(f"    Location: {ffprobe_path}")
                else:
                    print(f"[!] FFprobe 缺失，需要补充安装")
                    return False
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


def _install_ffprobe_only(os_info, current_os):
    dest_dir = FFMPEG_INSTALL_DIR / 'bin'
    ffprobe_name = f'ffprobe{os_info["ext"]}'

    sources = FFMPEG_CDNS.get(current_os, [])
    for source in sources:
        ffprobe_url = source.get('ffprobe_url')
        if ffprobe_url:
            print(f"    从 {source['name']} 下载 ffprobe...")
            temp_download = PROJECT_ROOT / '_temp_ffprobe_download'
            temp_extract = PROJECT_ROOT / '_temp_ffprobe_extract'
            try:
                temp_download.mkdir(parents=True, exist_ok=True)
                temp_extract.mkdir(parents=True, exist_ok=True)
                if download_file(ffprobe_url, temp_download / 'ffprobe_archive'):
                    probe_result = extract_zip_mac(temp_download / 'ffprobe_archive', temp_extract)
                    if probe_result:
                        probe_src = Path(probe_result)
                        probe_dst = dest_dir / ffprobe_name
                        shutil.copy2(str(probe_src), str(probe_dst))
                        if os.name != 'nt':
                            os.chmod(str(probe_dst), 0o755)
                        print(f"    已安装: {probe_dst}")
                        return True
                    else:
                        for root, dirs, files in os.walk(str(temp_extract)):
                            for f in files:
                                if f == ffprobe_name:
                                    src_p = Path(root) / f
                                    dst_p = dest_dir / ffprobe_name
                                    shutil.copy2(str(src_p), str(dst_p))
                                    if os.name != 'nt':
                                        os.chmod(str(dst_p), 0o755)
                                    print(f"    已安装: {dst_p}")
                                    return True
            except Exception as e:
                print(f"    ffprobe 下载/解压失败: {e}")
            finally:
                if temp_download.exists():
                    shutil.rmtree(temp_download, ignore_errors=True)
                if temp_extract.exists():
                    shutil.rmtree(temp_extract, ignore_errors=True)

        ffprobe_pkg = source.get('npm_ffprobe_pkg')
        if ffprobe_pkg:
            npm = shutil.which('npm')
            if npm:
                print(f"    通过 npm 淘宝镜像安装 {ffprobe_pkg}...")
                temp_dir = PROJECT_ROOT / '_temp_ffprobe_npm'
                try:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    env = os.environ.copy()
                    subprocess.run([npm, 'init', '-y'], cwd=str(temp_dir), capture_output=True, text=True, timeout=30, env=env)
                    result = subprocess.run(
                        [npm, 'install', ffprobe_pkg, '--registry=https://registry.npmmirror.com'],
                        cwd=str(temp_dir), capture_output=True, text=True, timeout=120, env=env,
                    )
                    if result.returncode == 0:
                        for root, dirs, files in os.walk(str(temp_dir)):
                            for f in files:
                                if f == ffprobe_name:
                                    src_p = os.path.join(root, f)
                                    dst_p = dest_dir / ffprobe_name
                                    shutil.copy2(src_p, str(dst_p))
                                    if os.name != 'nt':
                                        os.chmod(str(dst_p), 0o755)
                                    print(f"    已安装: {dst_p}")
                                    return True
                    else:
                        print(f"    npm 安装 ffprobe 失败: {result.stderr[:200]}")
                except Exception as e:
                    print(f"    npm 安装 ffprobe 异常: {e}")
                finally:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)

    print("    FFprobe 补充安装失败")
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


FFMPEG_CDNS = {
    'windows': [
        {
            'name': 'npm 淘宝镜像 (ffmpeg-static + ffprobe)',
            'npm_pkg': 'ffmpeg-static',
            'npm_bin': 'ffmpeg',
            'npm_ffprobe_pkg': '@ffprobe-installer/ffprobe',
        },
        {
            'name': 'Gyan.dev (官方)',
            'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
        },
        {
            'name': 'BtbN GitHub',
            'url': None,
            'url_tpl': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-{arch}-gpl.zip',
        },
    ],
    'mac': [
        {
            'name': 'npm 淘宝镜像 (ffmpeg-static + ffprobe)',
            'npm_pkg': 'ffmpeg-static',
            'npm_bin': 'ffmpeg',
            'npm_ffprobe_pkg': '@ffprobe-installer/ffprobe',
        },
        {
            'name': 'evermeet.cx (官方)',
            'url': 'https://evermeet.cx/ffmpeg/getrelease/zip',
            'ffprobe_url': 'https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip',
        },
    ],
    'linux': [
        {
            'name': 'npm 淘宝镜像 (ffmpeg-static + ffprobe)',
            'npm_pkg': 'ffmpeg-static',
            'npm_bin': 'ffmpeg',
            'npm_ffprobe_pkg': '@ffprobe-installer/ffprobe',
        },
        {
            'name': 'BtbN GitHub',
            'url': None,
            'url_tpl': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-{arch}-gpl.tar.xz',
        },
    ],
}


def setup_ffmpeg():
    print("=" * 60)
    print("FFmpeg 安装工具")
    print("=" * 60)

    os_info = detect_os()
    current_os = os_info['os']
    print(f"\n[*] 检测到系统: {current_os.upper()} ({os_info['arch']})")

    # 更新 FFmpeg 安装目录为平台对应的预编译版本目录
    global FFMPEG_INSTALL_DIR
    FFMPEG_INSTALL_DIR = get_ffmpeg_platform_dir()

    if check_ffmpeg_installed():
        print("\nFFmpeg 已就绪！")
        return True

    ffmpeg_bin = FFMPEG_INSTALL_DIR / 'bin' / f'ffmpeg{os_info["ext"]}'
    ffprobe_bin = FFMPEG_INSTALL_DIR / 'bin' / f'ffprobe{os_info["ext"]}'
    if ffmpeg_bin.exists() and not ffprobe_bin.exists():
        print(f"\n[*] FFmpeg 已安装但 FFprobe 缺失，尝试补充安装 FFprobe...")
        if _install_ffprobe_only(os_info, current_os):
            return check_ffmpeg_installed()

    print(f"\n[*] FFmpeg 将安装到: {FFMPEG_INSTALL_DIR}")

    sources = FFMPEG_CDNS.get(current_os, [])

    pkg_managers = []
    if current_os == 'mac':
        if shutil.which('brew'):
            pkg_managers.append({'name': 'Homebrew', 'cmd': ['brew', 'install', 'ffmpeg']})
    elif current_os == 'linux':
        if shutil.which('apt-get'):
            pkg_managers.append({'name': 'APT (Ubuntu/Debian)', 'cmd': ['sudo', 'apt-get', 'update', '&&', 'sudo', 'apt-get', 'install', '-y', 'ffmpeg']})
        if shutil.which('dnf'):
            pkg_managers.append({'name': 'DNF (Fedora)', 'cmd': ['sudo', 'dnf', 'install', '-y', 'ffmpeg']})
        if shutil.which('yum'):
            pkg_managers.append({'name': 'YUM (CentOS/RHEL)', 'cmd': ['sudo', 'yum', 'install', '-y', 'ffmpeg']})
        if shutil.which('pacman'):
            pkg_managers.append({'name': 'Pacman (Arch)', 'cmd': ['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg']})
        if shutil.which('apk'):
            pkg_managers.append({'name': 'APK (Alpine)', 'cmd': ['sudo', 'apk', 'add', 'ffmpeg']})

    success = False
    total = len(sources) + len(pkg_managers)
    step = 0

    for source in sources:
        step += 1
        print(f"\n{'=' * 60}")
        print(f"[{step}/{total}] 尝试: {source['name']}")
        print('=' * 60)

        if source.get('npm_pkg'):
            if _install_ffmpeg_via_npm(source):
                success = True
                break
            continue

        url = source.get('url')
        if not url and source.get('url_tpl'):
            arch_map = {
                'win64': 'win64-gpl',
                'winarm64': 'winarm64-gpl',
                'win32': 'win32-gpl',
                'linux_x64': 'linux64-gpl',
                'linux_arm64': 'linuxarm64-gpl',
                'mac_arm64': 'macos64-arm64-gpl',
                'mac_x64': 'macos64-gpl',
            }
            mapped = arch_map.get(os_info['arch'], os_info['arch'])
            url = source['url_tpl'].format(arch=mapped)

        if not url:
            continue

        temp_download = PROJECT_ROOT / '_temp_ffmpeg_download'
        temp_extract = PROJECT_ROOT / '_temp_ffmpeg_extract'
        if temp_extract.exists():
            shutil.rmtree(temp_extract, ignore_errors=True)
        temp_download.mkdir(parents=True, exist_ok=True)

        if download_file(url, temp_download / 'ffmpeg_archive'):
            extract_func = extract_zip_generic
            if url.endswith('.tar.xz') or url.endswith('.tar.gz'):
                extract_func = extract_tar
            elif current_os == 'mac':
                extract_func = extract_zip_mac

            try:
                result = extract_func(temp_download / 'ffmpeg_archive', temp_extract)
                if result:
                    _move_ffmpeg_to_install_dir(result, temp_extract, os_info)

                    ffprobe_url = source.get('ffprobe_url')
                    if ffprobe_url and not (FFMPEG_INSTALL_DIR / 'bin' / f'ffprobe{os_info["ext"]}').exists():
                        print(f"\n    正在下载 ffprobe...")
                        temp_extract_ffprobe = PROJECT_ROOT / '_temp_ffmpeg_extract_ffprobe'
                        if temp_extract_ffprobe.exists():
                            shutil.rmtree(temp_extract_ffprobe, ignore_errors=True)
                        temp_extract_ffprobe.mkdir(parents=True, exist_ok=True)
                        if download_file(ffprobe_url, temp_download / 'ffprobe_archive'):
                            try:
                                probe_result = extract_zip_mac(temp_download / 'ffprobe_archive', temp_extract_ffprobe)
                                if probe_result:
                                    probe_src = Path(probe_result)
                                    probe_dst = FFMPEG_INSTALL_DIR / 'bin' / f'ffprobe{os_info["ext"]}'
                                    shutil.copy2(str(probe_src), str(probe_dst))
                                    if os.name != 'nt':
                                        os.chmod(str(probe_dst), 0o755)
                                    print(f"    已安装: {probe_dst}")
                                else:
                                    for root, dirs, files in os.walk(str(temp_extract_ffprobe)):
                                        for f in files:
                                            if f == f'ffprobe{os_info["ext"]}':
                                                src_p = Path(root) / f
                                                dst_p = FFMPEG_INSTALL_DIR / 'bin' / f
                                                shutil.copy2(str(src_p), str(dst_p))
                                                if os.name != 'nt':
                                                    os.chmod(str(dst_p), 0o755)
                                                print(f"    已安装: {dst_p}")
                                                break
                            except Exception as e:
                                print(f"    ffprobe 解压失败: {e}")
                            finally:
                                if temp_extract_ffprobe.exists():
                                    shutil.rmtree(temp_extract_ffprobe, ignore_errors=True)

                    success = True
                    break
            except Exception as e:
                print(f"    解压失败: {e}")

        if temp_download.exists():
            shutil.rmtree(temp_download, ignore_errors=True)

    if not success:
        for pm in pkg_managers:
            step += 1
            print(f"\n{'=' * 60}")
            print(f"[{step}/{total}] 尝试: {pm['name']}")
            print('=' * 60)
            if install_via_package_manager(pm['cmd'], pm['name']):
                if shutil.which('ffmpeg'):
                    success = True
                    break

    if PROJECT_ROOT.exists() and (PROJECT_ROOT / '_temp_ffmpeg_extract').exists():
        shutil.rmtree(PROJECT_ROOT / '_temp_ffmpeg_extract', ignore_errors=True)
    if PROJECT_ROOT.exists() and (PROJECT_ROOT / '_temp_ffmpeg_download').exists():
        shutil.rmtree(PROJECT_ROOT / '_temp_ffmpeg_download', ignore_errors=True)

    if success:
        print("\n" + "=" * 60)
        print("[*] FFmpeg 安装成功！")
        print("=" * 60)
        return check_ffmpeg_installed()
    else:
        print("\n" + "=" * 60)
        print("[!] 所有安装方式均失败")
        print("=" * 60)
        print("\n手动安装方式:")
        if current_os == 'windows':
            print("  1. 下载: https://www.gyan.dev/ffmpeg/builds/")
            print(f"  2. 解压到: {FFMPEG_INSTALL_DIR}")
        elif current_os == 'mac':
            print("  1. 安装 Homebrew: https://brew.sh/")
            print("  2. 运行: brew install ffmpeg")
        elif current_os == 'linux':
            print("  1. 使用包管理器:")
            print("     Ubuntu/Debian: sudo apt install ffmpeg")
            print("     Fedora: sudo dnf install ffmpeg")
            print("     Arch: sudo pacman -S ffmpeg")
        return False


def _install_ffmpeg_via_npm(source):
    npm = shutil.which('npm')
    if not npm:
        print("    npm 未安装，跳过此方式")
        return False

    npm_pkg = source['npm_pkg']
    npm_bin_name = source.get('npm_bin', 'ffmpeg')

    temp_dir = PROJECT_ROOT / '_temp_ffmpeg_npm'
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"    通过 npm 淘宝镜像安装 {npm_pkg}...")
        env = os.environ.copy()
        if npm_pkg == 'ffmpeg-static':
            env['FFMPEG_BINARIES_URL'] = 'https://cdn.npmmirror.com/binaries/ffmpeg-static'

        result = subprocess.run(
            [npm, 'init', '-y'],
            cwd=str(temp_dir),
            capture_output=True, text=True, timeout=30,
            env=env,
        )

        result = subprocess.run(
            [npm, 'install', npm_pkg, '--registry=https://registry.npmmirror.com'],
            cwd=str(temp_dir),
            capture_output=True, text=True, timeout=120,
            env=env,
        )

        if result.returncode != 0:
            print(f"    npm 安装失败: {result.stderr[:200]}")
            return False

        ffmpeg_found = None
        for root, dirs, files in os.walk(str(temp_dir)):
            for f in files:
                if f == npm_bin_name or f == npm_bin_name + '.exe':
                    candidate = os.path.join(root, f)
                    try:
                        test = subprocess.run(
                            [candidate, '-version'],
                            capture_output=True, text=True, timeout=5,
                        )
                        if test.returncode == 0:
                            ffmpeg_found = candidate
                            break
                    except Exception:
                        pass
            if ffmpeg_found:
                break

        if not ffmpeg_found:
            print("    npm 安装完成但未找到可执行的 ffmpeg")
            return False

        dest_dir = FFMPEG_INSTALL_DIR / 'bin'
        dest_dir.mkdir(parents=True, exist_ok=True)
        os_info = detect_os()
        dest_file = dest_dir / f'ffmpeg{os_info["ext"]}'
        shutil.copy2(ffmpeg_found, str(dest_file))
        if os.name != 'nt':
            os.chmod(str(dest_file), 0o755)

        print(f"    已复制: {dest_file}")

        ffprobe_name = 'ffprobe' + os_info['ext']
        for root, dirs, files in os.walk(str(temp_dir)):
            for f in files:
                if f == ffprobe_name:
                    src = os.path.join(root, f)
                    dst = dest_dir / ffprobe_name
                    shutil.copy2(src, str(dst))
                    if os.name != 'nt':
                        os.chmod(str(dst), 0o755)
                    print(f"    已复制: {dst}")
                    break

        ffprobe_pkg = source.get('npm_ffprobe_pkg')
        if ffprobe_pkg and not (dest_dir / ffprobe_name).exists():
            print(f"    通过 npm 淘宝镜像安装 {ffprobe_pkg}...")
            result = subprocess.run(
                [npm, 'install', ffprobe_pkg, '--registry=https://registry.npmmirror.com'],
                cwd=str(temp_dir),
                capture_output=True, text=True, timeout=120,
                env=env,
            )
            if result.returncode == 0:
                for root, dirs, files in os.walk(str(temp_dir)):
                    for f in files:
                        if f == ffprobe_name:
                            src = os.path.join(root, f)
                            dst = dest_dir / ffprobe_name
                            shutil.copy2(src, str(dst))
                            if os.name != 'nt':
                                os.chmod(str(dst), 0o755)
                            print(f"    已复制: {dst}")
                            break
                    if (dest_dir / ffprobe_name).exists():
                        break
            else:
                print(f"    ffprobe npm 安装失败: {result.stderr[:200]}")

        return True

    except subprocess.TimeoutExpired:
        print("    npm 安装超时")
        return False
    except Exception as e:
        print(f"    npm 安装异常: {e}")
        return False
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def extract_tar(filepath, dest):
    filepath = Path(filepath)
    try:
        if str(filepath).endswith('.tar.xz'):
            import lzma
            with lzma.open(str(filepath), 'rb') as f:
                with tarfile.open(fileobj=f) as tar:
                    tar.extractall(path=str(dest))
        elif str(filepath).endswith('.tar.gz'):
            with tarfile.open(str(filepath), 'r:gz') as tar:
                tar.extractall(path=str(dest))
        else:
            with tarfile.open(str(filepath), 'r') as tar:
                tar.extractall(path=str(dest))
        for root, dirs, files in os.walk(str(dest)):
            for f in files:
                if f == 'ffmpeg' or f == 'ffmpeg.exe':
                    return os.path.join(root, f)
        return None
    except Exception as e:
        print(f"    解压失败: {e}")
        return None


def _move_ffmpeg_to_install_dir(extracted_path, temp_extract, os_info):
    src = Path(extracted_path)
    dest_dir = FFMPEG_INSTALL_DIR / 'bin'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f'ffmpeg{os_info["ext"]}'
    shutil.copy2(str(src), str(dest))
    if os.name != 'nt':
        os.chmod(str(dest), 0o755)
    print(f"    已安装: {dest}")

    for root, dirs, files in os.walk(str(temp_extract)):
        for f in files:
            if f == f'ffprobe{os_info["ext"]}':
                src_probe = Path(root) / f
                dst_probe = dest_dir / f
                shutil.copy2(str(src_probe), str(dst_probe))
                if os.name != 'nt':
                    os.chmod(str(dst_probe), 0o755)
                print(f"    已安装: {dst_probe}")
                break


def find_ffmpeg():
    path = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    if path:
        return path

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext = '.exe' if os.name == 'nt' else ''


    # 优先使用项目根目录下的预编译版本
    try:
        prebuilt_ffmpeg = get_ffmpeg_platform_dir() / f'ffmpeg{ext}'
        if prebuilt_ffmpeg.exists():
            print(f"[*] 找到预编译 FFmpeg: {prebuilt_ffmpeg.resolve()}")
            return str(prebuilt_ffmpeg.resolve())  # 规范化路径，消除 ..
    except Exception as e:
        print(f"[!] 检测预编译 FFmpeg 失败: {e}")

    # 回退到虚拟环境中的旧版路径（兼容）
    venv_ffmpeg = os.path.join(base_dir, '.venv', 'ffmpeg', 'bin', f'ffmpeg{ext}')
    if os.path.isfile(venv_ffmpeg):
        return venv_ffmpeg

    if os.name == 'nt':
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
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/usr/bin/ffmpeg',
            '/snap/bin/ffmpeg',
            '/flatpak/bin/ffmpeg',
        ]

        homebrew_prefix = os.environ.get('HOMEBREW_PREFIX', '')
        if homebrew_prefix and os.path.isdir(homebrew_prefix):
            homebrew_bin = os.path.join(homebrew_prefix, 'bin', 'ffmpeg')
            if homebrew_bin not in common_paths:
                common_paths.insert(3, homebrew_bin)
        elif os.path.isdir('/opt/homebrew'):
            common_paths.append('/opt/homebrew/bin/ffmpeg')

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

    if ffprobe_path:
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
            pass
        except Exception:
            pass

    if FFMPEG_PATH:
        cmd = [
            FFMPEG_PATH,
            '-i', url,
            '-hide_banner',
            '-t', '0',
            '-f', 'null',
            '-',
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
            stderr = result.stderr
            codecs = []
            unsupported = []
            has_audio = False

            audio_section = False
            for line in stderr.split('\n'):
                if 'Audio:' in line:
                    has_audio = True
                    audio_section = True
                    parts = line.split('Audio:')[1].strip()
                    codec_part = parts.split(',')[0].strip().split(' ')[0]
                    codecs.append(codec_part)
                    if codec_part in ('ac3', 'eac3', 'dts', 'dtshd', 'truehd', 'mlp'):
                        unsupported.append(codec_part)

            if has_audio:
                return {'has_audio': True, 'codecs': codecs, 'unsupported': unsupported}
            elif 'Stream #' in stderr and 'Video:' in stderr:
                return {'has_audio': False, 'codecs': [], 'unsupported': []}
            else:
                return {'has_audio': None, 'error': 'probe_failed'}
        except subprocess.TimeoutExpired:
            return {'has_audio': None, 'error': 'timeout'}
        except Exception as e:
            return {'has_audio': None, 'error': str(e)}

    return {'has_audio': None, 'error': 'no_ffprobe'}


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


def _preload_evict():
    global preload_size
    now = time.time()
    expired = [k for k, v in preload_cache.items() if now - v['ts'] > PRELOAD_TTL]
    for k in expired:
        preload_size -= len(preload_cache[k]['data'])
        del preload_cache[k]
        if k in preload_order:
            preload_order.remove(k)
    while (preload_order and
           (len(preload_cache) > PRELOAD_MAX_ENTRIES or preload_size > PRELOAD_MAX_SIZE)):
        oldest = preload_order.pop(0)
        if oldest in preload_cache:
            preload_size -= len(preload_cache[oldest]['data'])
            del preload_cache[oldest]


def _preload_fetch(url):
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', '*/*')
        req.add_header('Connection', 'keep-alive')
        with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
            content_type = resp.headers.get('Content-Type', 'application/octet-stream').lower()
            data = resp.read(MAX_CONTENT_LENGTH)
        with preload_lock:
            _preload_evict()
            preload_cache[url] = {'data': data, 'ct': content_type, 'ts': time.time()}
            preload_order.append(url)
            preload_size += len(data)
    except Exception:
        pass


def preload_segments(urls):
    global preload_executor
    if preload_executor is None:
        preload_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=PRELOAD_WORKERS, thread_name_prefix='preload')
    pending = []
    for url in urls:
        with preload_lock:
            if url in preload_cache:
                continue
        pending.append(url)
    if not pending:
        return
    sync_count = len(pending) if PRELOAD_SYNC_ALL else min(PRELOAD_SYNC_FIRST, len(pending))
    futures = []
    for url in pending:
        futures.append(preload_executor.submit(_preload_fetch, url))
    for f in futures[:sync_count]:
        try:
            f.result(timeout=PROXY_TIMEOUT)
        except Exception:
            pass


PRELOAD_PIPELINE_INTERVAL = int(os.environ.get('IPTV_PRELOAD_PIPELINE_INTERVAL', '2'))
PRELOAD_PIPELINE_MAX_AGE = int(os.environ.get('IPTV_PRELOAD_PIPELINE_MAX_AGE', '300'))


def _preload_pipeline(m3u8_url):
    try:
        while True:
            req = urllib.request.Request(m3u8_url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
                data = resp.read(MAX_CONTENT_LENGTH)
            text = data.decode('utf-8', errors='replace')
            seg_urls = []
            for line in text.split('\n'):
                s = line.strip()
                if s and not s.startswith('#'):
                    if s.startswith('http://') or s.startswith('https://'):
                        seg_urls.append(s)
                    else:
                        seg_urls.append(urllib.parse.urljoin(m3u8_url, s))
            if seg_urls:
                preload_segments(seg_urls)
            time.sleep(PRELOAD_PIPELINE_INTERVAL)
    except Exception:
        pass
    finally:
        with preload_lock:
            preload_pipelines.pop(m3u8_url, None)


def start_preload_pipeline(m3u8_url):
    with preload_lock:
        if m3u8_url in preload_pipelines:
            return
        preload_pipelines[m3u8_url] = True
    t = threading.Thread(target=_preload_pipeline, args=(m3u8_url,), daemon=True, name=f'pipeline-{hashlib.md5(m3u8_url.encode()).hexdigest()[:8]}')
    t.start()


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

    def _stream_proxy_body(self, resp, content_length):
        first_chunk_size = 32768
        chunk_size = 262144
        buf = queue.Queue(maxsize=16)
        reader_error = [None]

        def _reader():
            total = 0
            try:
                first = True
                while True:
                    sz = first_chunk_size if first else chunk_size
                    first = False
                    chunk = resp.read(sz)
                    if not chunk:
                        buf.put(None)
                        break
                    total += len(chunk)
                    if total > MAX_CONTENT_LENGTH:
                        buf.put(None)
                        break
                    buf.put(chunk)
            except Exception as e:
                reader_error[0] = e
                buf.put(None)

        t = threading.Thread(target=_reader, daemon=True)
        t.start()

        while True:
            chunk = buf.get()
            if chunk is None:
                break
            if content_length:
                self.wfile.write(chunk)
                self.wfile.flush()
            else:
                self.wfile.write(f'{len(chunk):x}\r\n'.encode())
                self.wfile.write(chunk)
                self.wfile.write(b'\r\n')
                self.wfile.flush()

        if not content_length:
            self.wfile.write(b'0\r\n\r\n')

        t.join(timeout=5)
        if reader_error[0]:
            raise reader_error[0]

    def _handle_proxy(self):
        encoded_url = self.path[len(PROXY_PREFIX):]
        target_url = urllib.parse.unquote(encoded_url)

        if not target_url.startswith(('http://', 'https://')):
            self._send_proxy_error(400, 'Invalid proxy target URL')
            return

        with preload_lock:
            cached = preload_cache.get(target_url)
            if cached and time.time() - cached['ts'] <= PRELOAD_TTL:
                self.send_response(200)
                self.send_header('Content-Type', cached['ct'])
                self.send_header('Content-Length', str(len(cached['data'])))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                self.send_header('X-Preload-Hit', '1')
                self.end_headers()
                data = cached['data']
                off = 0
                while off < len(data):
                    chunk = data[off:off + 65536]
                    self.wfile.write(chunk)
                    self.wfile.flush()
                    off += len(chunk)
                return

        try:
            req = urllib.request.Request(target_url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept', '*/*')

            with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
                content_type = resp.headers.get('Content-Type', 'application/octet-stream').lower()

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
                    data = resp.read(MAX_CONTENT_LENGTH)
                    try:
                        text = data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            text = data.decode('latin-1')
                        except Exception:
                            text = data.decode('utf-8', errors='replace')

                    seg_urls = []
                    for line in text.split('\n'):
                        s = line.strip()
                        if s and not s.startswith('#'):
                            if s.startswith('http://') or s.startswith('https://'):
                                seg_urls.append(s)
                            else:
                                seg_urls.append(urllib.parse.urljoin(target_url, s))

                    if seg_urls:
                        preload_segments(seg_urls)

                    start_preload_pipeline(target_url)

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
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', '*')
                    self.send_header('Cache-Control', 'no-cache')
                    content_length = resp.headers.get('Content-Length')
                    if content_length:
                        self.send_header('Content-Length', content_length)
                    else:
                        self.send_header('Transfer-Encoding', 'chunked')
                    self.end_headers()

                    self._stream_proxy_body(resp, content_length)

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





def main():
    global FFMPEG_PATH, TRANSCODE_DIR

    FFMPEG_PATH = find_ffmpeg()
    TRANSCODE_DIR = tempfile.mkdtemp(prefix='iptv_tc_')
    atexit.register(cleanup_all_transcodes)

    port = int(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else PORT
    serve_dir = str((PROJECT_ROOT / "output").resolve())  # 输出目录
    handler = functools.partial(CORSProxyHandler, directory=serve_dir)

    with ThreadedHTTPServer(('', port), handler) as httpd:
        print(f'  访问地址: http://127.0.0.1:{port}')
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

