import os
import logging
import aiohttp
import asyncio
import ssl
import time
import json
import platform
import subprocess
import shutil
import urllib.request
import tarfile
import zipfile
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple, Any

logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)

PROJECT_ROOT = Path(__file__).parent.parent.parent
FFMPEG_DIR = PROJECT_ROOT / 'ffmpeg'
FILE_DIR = PROJECT_ROOT / 'file'
STREAM_CACHE_FILE = FILE_DIR / '.stream_cache.json'
STREAM_CACHE_TTL = 4 * 3600  # 流测试缓存有效期：4小时
SOURCE_CACHE_FILE = FILE_DIR / '.source_cache.json'  # IPTV源文件内容缓存
SOURCE_CACHE_TTL = 2 * 3600  # 源文件缓存有效期：2小时


def _suppress_asyncio_exception(loop, context):
    exception = context.get("exception")
    message = context.get("message", "")
    if exception and isinstance(exception, (OSError, ConnectionError)):
        return
    if "shielded future" in message or "call_connection_lost" in message:
        return
    loop.default_exception_handler(context)

def contains_date(text):
    """
    检测字符串中是否包含日期格式（如 YYYY-MM-DD）
    """
    date_pattern = r"\d{4}-\d{2}-\d{2}"  # 正则表达式匹配 YYYY-MM-DD
    return re.search(date_pattern, text) is not None


def normalize_text_for_match(text: str) -> str:
    """归一化文本用于频道匹配，去掉空格/标点并统一大小写。"""
    normalized = text.translate(CHAR_NORMALIZATION_MAP).strip().upper().replace("＋", "+")
    normalized = re.sub(r"[ \t\r\n\-_|·•:：,，.。/\\()\[\]【】「」'\"`]+", "", normalized)
    return normalized


# 配置
CONFIG = {
    "timeout": int(os.environ.get("IPTV_TIMEOUT", "3")),
    "max_parallel": int(os.environ.get("IPTV_MAX_PARALLEL", "200")),
    "output_file": os.environ.get("IPTV_OUTPUT_FILE", "file/best_sorted.m3u"),
    "connect_timeout": int(os.environ.get("IPTV_CONNECT_TIMEOUT", "2")),
    "dns_cache_ttl": int(os.environ.get("IPTV_DNS_CACHE_TTL", "300")),
    "source_cdn_test_timeout": int(os.environ.get("IPTV_SOURCE_CDN_TEST_TIMEOUT", "2")),
    "cdn_cache_ttl_hours": int(os.environ.get("IPTV_CDN_CACHE_TTL", "6")),
}

CDN_CACHE_FILE = FILE_DIR / '.cdn_cache.json'

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
    ffmpeg_path = FFMPEG_DIR / 'bin' / f'ffmpeg{detect_os()["ext"]}'
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
                print(f"✓ FFmpeg already installed: {version}")
                print(f"  Location: {ffmpeg_path}")
                return True
        except:
            pass
    return False

def get_ffmpeg_sources(os_info):
    sources = []
    if os_info['os'] == 'windows':
        sources = [
            {
                'name': 'Gyan.dev (Official)',
                'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
                'extract_func': extract_zip_generic
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
                'name': 'evermeet.cx (Homebrew)',
                'url': 'https://evermeet.cx/ffmpeg/getrelease/zip',
                'extract_func': extract_zip_mac
            },
            {
                'name': 'Homebrew (Package Manager)',
                'url': None,
                'install_cmd': ['brew', 'install', 'ffmpeg']
            }
        ]
    elif os_info['os'] == 'linux':
        package_managers = []

        if shutil.which('apt-get'):
            package_managers.append({
                'name': 'APT (Ubuntu/Debian)',
                'cmd': ['sudo', 'apt-get', 'update'] + ['&&'] + ['sudo', 'apt-get', 'install', '-y', 'ffmpeg']
            })
        elif shutil.which('dnf'):
            package_managers.append({
                'name': 'DNF (Fedora)',
                'cmd': ['sudo', 'dnf', 'install', '-y', 'ffmpeg']
            })
        elif shutil.which('yum'):
            package_managers.append({
                'name': 'YUM (CentOS/RHEL)',
                'cmd': ['sudo', 'yum', 'install', '-y', 'ffmpeg']
            })
        elif shutil.which('pacman'):
            package_managers.append({
                'name': 'Pacman (Arch Linux)',
                'cmd': ['sudo', '-S', 'pacman', '-S', '--noconfirm', 'ffmpeg']
            })
        elif shutil.which('zypper'):
            package_managers.append({
                'name': 'Zypper (openSUSE)',
                'cmd': ['sudo', 'zypper', 'install', '-y', 'ffmpeg']
            })

        for pm in package_managers:
            sources.append({
                'name': pm['name'],
                'url': None,
                'install_cmd': pm['cmd']
            })

        sources.append({
            'name': 'Static Build (johnvansickle.com)',
            'url': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz',
            'extract_func': extract_tar_xz_linux
        })

    return sources

def extract_zip_generic(filepath, dest):
    with zipfile.ZipFile(filepath, 'r') as z:
        z.extractall(dest)
    return find_ffmpeg_in_dir(dest)

def extract_zip_mac(filepath, dest):
    temp_dir = dest / '_temp'
    temp_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(filepath, 'r') as z:
        z.extractall(temp_dir)

    ffmpeg_bin = FFMPEG_DIR / 'bin'
    ffmpeg_bin.mkdir(parents=True, exist_ok=True)

    for item in temp_dir.iterdir():
        if item.is_file() and item.suffix == '':
            target = ffmpeg_bin / item.name
            shutil.copy2(item, target)
            os.chmod(target, 0o755)

    shutil.rmtree(temp_dir, ignore_errors=True)

    if (ffmpeg_bin / 'ffmpeg').exists():
        return str(FFMPEG_DIR)
    return None

def extract_tar_xz_linux(filepath, dest):
    with tarfile.open(filepath, 'r:xz') as tar:
        tar.extractall(dest)
    return find_ffmpeg_in_dir(dest)

def find_ffmpeg_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        if 'ffmpeg' in files or 'ffmpeg.exe' in files:
            ffmpeg_path = Path(root) / ('ffmpeg.exe' if 'ffmpeg.exe' in files else 'ffmpeg')
            if ffmpeg_path.exists() and not ffmpeg_path.is_dir():
                return str(Path(root).parent) if len(Path(root).parts) > 1 else str(root)
    return None

def download_file(url, dest_path):
    print(f"  Downloading from: {url}")

    try:
        urllib.request.urlretrieve(url, dest_path)
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"  ✓ Downloaded: {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def install_via_package_manager(cmd, name):
    print(f"\n[*] Installing via {name}...")
    print(f"  Command: {' '.join(str(c) for c in cmd)}")

    try:
        if isinstance(cmd[0], list):
            for c in cmd:
                subprocess.run(c, check=True)
        else:
            subprocess.run(cmd, check=True)

        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            create_symlink_or_copy(ffmpeg_path)
            return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Installation failed: {e}")
        return False

    return False

def create_symlink_or_copy(system_ffmpeg):
    try:
        FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
        bin_dir = FFMPEG_DIR / 'bin'
        bin_dir.mkdir(exist_ok=True)

        local_ffmpeg = bin_dir / 'ffmpeg'

        if local_ffmpeg.exists() or local_ffmpeg.is_symlink():
            local_ffmpeg.unlink()

        os.symlink(system_ffmpeg, local_ffmpeg)
        print(f"✓ Created symlink: {local_ffmpeg} -> {system_ffmpeg}")

        ffprobe = Path(system_ffmpeg).parent / 'ffprobe'
        local_ffprobe = bin_dir / 'ffprobe'
        if ffprobe.exists():
            os.symlink(str(ffprobe), local_ffprobe)
            print(f"✓ Created symlink: {local_ffprobe} -> {ffprobe}")

        return True
    except OSError:
        shutil.copy2(system_ffmpeg, str(local_ffmpeg))
        print(f"✓ Copied to: {local_ffmpeg}")
        return True

def setup_ffmpeg():
    print("=" * 60)
    print("FFmpeg Setup Tool")
    print("=" * 60)

    os_info = detect_os()
    print(f"\n[*] Detected OS: {os_info['os'].upper()} ({os_info['arch']})")

    if check_ffmpeg_installed():
        print("\nFFmpeg is ready to use!")
        return True

    print(f"\n[*] FFmpeg will be installed to: {FFMPEG_DIR}")

    sources = get_ffmpeg_sources(os_info)
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
                            dst = FFMPEG_DIR
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
        print("✓ FFmpeg installation completed successfully!")
        print("=" * 60)

        if check_ffmpeg_installed():
            return True
    else:
        print("\n" + "=" * 60)
        print("✗ All FFmpeg installation methods failed")
        print("=" * 60)
        print("\nManual installation options:")
        if os_info['os'] == 'windows':
            print("  1. Download from https://www.gyan.dev/ffmpeg/builds/")
            print("  2. Extract to:", FFMPEG_DIR)
        elif os_info['os'] == 'mac':
            print("  1. Install Homebrew: https://brew.sh/")
            print("  2. Run: brew install ffmpeg")
        elif os_info['os'] == 'linux':
            print("  1. Use your package manager:")
            print("     Ubuntu/Debian: sudo apt install ffmpeg")
            print("     Fedora: sudo dnf install ffmpeg")
            print("     Arch: sudo pacman -S ffmpeg")
        return False

CHAR_NORMALIZATION_MAP = str.maketrans({
    "頻": "频",
    "視": "视",
    "臺": "台",
    "綜": "综",
    "聞": "闻",
    "體": "体",
    "藝": "艺",
    "經": "经",
    "濟": "济",
    "娛": "娱",
    "樂": "乐",
    "電": "电",
    "廣": "广",
    "畫": "画",
    "劇": "剧",
    "紀": "纪",
    "錄": "录",
    "網": "网",
    "導": "导",
    "髮": "发",
    "衛": "卫",
    "陰": "阴",
    "陽": "阳",
    "麗": "丽",
    "龍": "龙",
    "鄉": "乡",
    "鎮": "镇",
    "區": "区",
    "縣": "县",
    "灣": "湾",
    "滬": "沪",
    "閩": "闽",
    "贛": "赣",
    "蘇": "苏",
    "浙": "浙",
    "魯": "鲁",
    "豫": "豫",
    "鄂": "鄂",
    "湘": "湘",
    "粵": "粤",
    "瓊": "琼",
    "渝": "渝",
    "遼": "辽",
    "寧": "宁",
    "貴": "贵",
    "雲": "云",
    "藏": "藏",
    "陝": "陕",
    "晉": "晋",
    "冀": "冀",
    "贛": "赣",
    "錫": "锡",
})


PROVINCE_ALIASES = {
    "北京": {"北京台"},
    "上海": {"上海台", "东方明珠", "沪上"},
    "天津": {"天津台"},
    "重庆": {"重庆台"},
    "河北": {"河北台"},
    "山西": {"山西台", "三晋"},
    "辽宁": {"辽宁台", "辽沈"},
    "吉林": {"吉林台"},
    "内蒙": {"内蒙古"},
    "黑龙江": {"龙江", "黑龙江台"},
    "江苏": {"江苏台", "苏南"},
    "浙江": {"浙江台", "之江"},
    "安徽": {"安徽台"},
    "福建": {"福建台", "八闽"},
    "江西": {"江西台"},
    "山东": {"山东台", "齐鲁"},
    "河南": {"河南台", "中原"},
    "湖北": {"湖北台"},
    "湖南": {"湖南台"},
    "广东": {"广东台", "南粤"},
    "广西": {"广西台"},
    "海南": {"海南台"},
    "四川": {"四川台", "巴蜀"},
    "贵州": {"贵州台"},
    "云南": {"云南台", "七彩云南"},
    "西藏": {"西藏台"},
    "陕西": {"陕西台", "三秦"},
    "甘肃": {"甘肃台", "陇原"},
    "青海": {"青海台"},
    "宁夏": {"宁夏台"},
    "新疆": {"新疆台"},
}

COMMON_CHANNEL_SUFFIXES = (
    "新闻综合频道", "新闻综合", "新闻频道",
    "新聞綜合頻道", "新聞綜合", "新聞頻道",
    "社会民生频道", "社会民生",
    "社會民生頻道", "社會民生",
    "影视娱乐频道", "影视娱乐",
    "影視娛樂頻道", "影視娛樂",
    "经济生活频道", "经济生活",
    "經濟生活頻道", "經濟生活",
    "文体旅游频道", "文体旅游",
    "文體旅遊頻道", "文體旅遊",
    "文旅频道", "文旅",
    "文旅頻道",
    "旅游频道", "旅游",
    "旅遊頻道", "旅遊",
    "体育频道", "体育",
    "體育頻道", "體育",
    "教育频道", "教育",
    "教育頻道",
    "少儿频道", "少儿",
    "少兒頻道", "少兒",
    "科教频道", "科教",
    "科教頻道",
    "文化影视", "文化娱乐", "文化生活", "文化频道", "文化",
    "文化影視", "文化娛樂", "文化頻道",
    "都市频道", "都市",
    "都市頻道",
    "民生频道", "民生",
    "民生頻道",
    "资讯频道", "资讯",
    "資訊頻道", "資訊",
    "公共频道", "公共",
    "公共頻道",
    "综合频道", "综合",
    "綜合頻道",
    "娱乐频道", "娱乐",
    "娛樂頻道",
    "影视", "影視", "导视频道", "导视", "導視頻道", "導視",
    "生活频道", "生活頻道", "文艺频道", "文艺", "文藝頻道", "文藝",
    "法治频道", "法治頻道", "军事频道", "軍事頻道",
    "电视台", "電視台", "频道", "頻道", "直播",
    "高清", "超清", "标清",
)

NON_GEO_TOKENS = {
    "新闻", "综合", "公共", "生活", "民生", "都市", "经济", "科教", "教育", "少儿",
    "影视", "娱乐", "体育", "文旅", "旅游", "文化", "资讯", "导视", "频道", "电视",
    "法治", "军事", "党建", "购物", "健康", "养生", "时尚", "美食", "游戏", "电竞",
    "戲曲", "戏曲", "戲劇", "戏剧", "曲艺", "紀錄", "纪录", "綜藝", "综艺",
    "台", "TV", "HD", "SD", "UHD", "FHD", "4K", "8K",
}

# 【修改点 3】扩充智能分类关键字，防止动漫、港澳台频道被错误归类为省份频道
SMART_CATEGORY_KEYWORDS = {
    "港澳台频道": ("翡翠台", "明珠台", "无线新闻", "有线新闻", "HOY", "VIU", "凤凰", "寰宇", "纬来", "东森", "中天", "台视", "华视", "民视", "三立", "非凡", "年代", "TVBS", "八大"),
    "文旅频道": ("古城", "古镇", "景区", "景点", "风景", "风光", "观景", "全景", "大佛", "雪山", "公园", "湿地", "湖景", "山景", "游览", "花布"),
    "新闻频道": ("新闻", "时政", "资讯", "观察", "焦点", "头条"),
    "体育频道": ("体育", "足球", "篮球", "网球", "高尔夫", "搏击", "赛事"),
    "影视频道": ("电影", "影院", "剧场", "电视剧", "影视", "经典剧"),
    "少儿动漫": ("少儿", "卡通", "动漫", "动画", "童话", "小当家", "柯南", "哆啦A梦", "海绵宝宝"),
    "纪录人文": ("纪录", "纪实", "人文", "自然", "地理", "探索"),
    "音乐频道": ("音乐", "MV", "演唱会", "舞曲", "戏曲"),
    "广播频道": ("广播", "电台", "FM", "AM"),
    "戏曲综艺": ("戏曲", "戏剧", "曲艺", "梨园", "相声", "小品", "综艺", "文艺"),
    "法治军事": ("法治", "军事", "国防", "军旅", "警务", "普法"),
    "游戏电竞": ("游戏", "电竞", "电子竞技"),
    "生活购物": ("购物", "导购", "时尚", "美食", "健康", "养生", "家居"),
    "教育党建": ("党建", "党史", "党员", "教育", "教科", "留学", "考试"),
}

SCENIC_SINGLE_CHAR_HINTS = {"山", "湖", "河", "池", "田"}
SCENIC_EXCLUDE_HINTS = {
    "新闻", "综合", "公共", "体育", "足球", "篮球", "电影", "影视", "纪录",
    "动漫", "少儿", "音乐", "广播", "经济", "生活", "教育", "科教", "资讯",
    "法治", "军事", "购物", "党建", "游戏", "电竞"
}

def load_cdn_cache():
    try:
        if os.path.exists(CDN_CACHE_FILE):
            with open(CDN_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                cache_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
                if (datetime.now() - cache_time).total_seconds() < CONFIG['cdn_cache_ttl_hours'] * 3600:
                    return cache.get('results', {})
    except Exception:
        pass
    return {}

def save_cdn_cache(results):
    try:
        cache = {
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        with open(CDN_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

# 【修改点 1】去掉 pcas-code 里的 s（街道/乡镇），只使用省、市、区级别的 pca-code.json
ONLINE_GEO_DATA_URLS = [
    "https://cdn.jsdelivr.net/gh/modood/Administrative-divisions-of-China/dist/pca-code.json",
    "https://fastly.jsdelivr.net/gh/modood/Administrative-divisions-of-China/dist/pca-code.json",
    "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/pca-code.json",
    "https://gh-proxy.com/raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/pca-code.json",
]

PROVINCE_SUFFIXES = (
    "特别行政区", "维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "省", "市"
)

AREA_SUFFIXES = (
    "自治县", "自治州", "自治区", "特别行政区", "新区", "开发区", "高新区",
    "地区", "林区", "矿区", "县", "市", "区", "州", "盟", "旗", "镇", "乡", "街道"
)

IGNORED_GEO_NAMES = {
    "市辖区", "城区", "郊区", "新区", "开发区", "高新区", "矿区", "城区街道",
    "其他", "直辖", "省直辖县级行政区划", "自治区直辖县级行政区划",
    "市辖县", "县级市", "直辖县级", "工业园区", "示范区", "合作区", "管理区"
}

COMMON_CHANNEL_SUFFIXES_NORMALIZED = tuple(
    sorted({normalize_text_for_match(s) for s in COMMON_CHANNEL_SUFFIXES}, key=len, reverse=True)
)

NON_GEO_TOKENS_NORMALIZED = {
    normalize_text_for_match(token) for token in NON_GEO_TOKENS
}

SMART_CATEGORY_KEYWORDS_NORMALIZED = {
    category: tuple(sorted({normalize_text_for_match(k) for k in keywords}, key=len, reverse=True))
    for category, keywords in SMART_CATEGORY_KEYWORDS.items()
}

SCENIC_EXCLUDE_HINTS_NORMALIZED = {
    normalize_text_for_match(token) for token in SCENIC_EXCLUDE_HINTS
}

IGNORED_GEO_NAMES_NORMALIZED = {
    normalize_text_for_match(name) for name in IGNORED_GEO_NAMES
}


# 读取 CCTV 频道列表
def load_cctv_channels(file_path=".github/workflows/IPTV/CCTV.txt"):
    """从文件加载 CCTV 频道列表"""
    cctv_channels = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # Ignore empty lines
                    cctv_channels.add(line)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    return cctv_channels


# 正规化 CCTV 频道名称
def normalize_cctv_name(channel_name):
    """将 CCTV 频道名称进行正规化，例如 CCTV-1 -> CCTV1"""
    return re.sub(r'(?i)CCTV[\s-]?(\d+\+?)', r'CCTV\1', channel_name).replace("＋", "+")


def is_cctv_channel(
    channel_name: str,
    normalized_channel: str,
    normalized_cctv_channels: Set[str]
) -> bool:
    """判断频道是否属于 CCTV/CGTN/CHC 等央视频道。"""
    cctv_number_match = re.search(r'(?i)CCTV[\s-]?(\d+\+?)', channel_name)
    if cctv_number_match:
        channel_id = f"CCTV{cctv_number_match.group(1).upper()}"
        if channel_id in normalized_cctv_channels:
            return True

    if normalized_channel in normalized_cctv_channels:
        return True

    # 处理 CCTV少儿/CGTN纪录/CHC电影 等存在后缀的场景
    for token in normalized_cctv_channels:
        if len(token) >= 4 and token in normalized_channel:
            return True

    return False


def resolve_province_aliases(province_name: str) -> Set[str]:
    aliases = {province_name}
    aliases.update(PROVINCE_ALIASES.get(province_name, set()))
    return aliases


def simplify_channel_name(channel_name: str) -> str:
    """移除常见分辨率/备注标记，便于提取地名与关键词。"""
    simplified = re.sub(r"[（(【\[][^\])）】]{0,24}[)）】\]]", "", channel_name)
    simplified = re.sub(r"\b(?:IPV6|HEVC|H\.?265|H\.?264|HDR|UHD|FHD|HD|SD|\d{3,4}P|4K|8K)\b", "", simplified, flags=re.IGNORECASE)
    return simplified.strip()


def strip_common_channel_suffixes(token: str) -> str:
    """去除频道通用后缀，尽量保留地名主干词。"""
    value = token
    value = re.sub(r"(?:TV|BTV|NBTV|CETV)\d+$", "", value)
    value = re.sub(r"[0-9一二三四五六七八九十]+套?$", "", value)
    value = re.sub(r"(?:IPV6|HEVC|H265|H264|HDR|UHD|FHD|HD|SD|4K|8K)$", "", value)

    changed = True
    while changed and value:
        changed = False
        for suffix in COMMON_CHANNEL_SUFFIXES_NORMALIZED:
            if value.endswith(suffix) and len(value) > len(suffix) + 1:
                value = value[:-len(suffix)]
                changed = True
                break

    return value


def extract_geo_tokens(channel_name: str, normalized_aliases: Set[str]) -> Set[str]:
    """从频道名中自动提取可用于省份匹配的地名词。"""
    tokens: Set[str] = set()
    simplified = simplify_channel_name(channel_name)

    candidates = [simplified]
    candidates.extend(part for part in re.split(r"[|｜/\\\-_·•\s]+", simplified) if part)

    for candidate in candidates:
        normalized = normalize_text_for_match(candidate)
        if not normalized:
            continue

        trimmed = normalized
        for alias in sorted(normalized_aliases, key=len, reverse=True):
            if trimmed.startswith(alias) and len(trimmed) > len(alias) + 1:
                trimmed = trimmed[len(alias):]
                break

        trimmed = strip_common_channel_suffixes(trimmed).strip()
        if 2 <= len(trimmed) <= 8 and trimmed not in NON_GEO_TOKENS_NORMALIZED:
            tokens.add(trimmed)

    return tokens


def strip_suffix_once(name: str, suffixes: Iterable[str]) -> str:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            return name[:-len(suffix)]
    return name


def normalize_province_name(name: str) -> str:
    return strip_suffix_once(re.sub(r"\s+", "", name), PROVINCE_SUFFIXES)


def geo_name_variants(name: str) -> Set[str]:
    cleaned = re.sub(r"\s+", "", name)
    if not cleaned:
        return set()

    variants = {cleaned}
    stripped = strip_suffix_once(cleaned, AREA_SUFFIXES)
    if stripped and stripped != cleaned:
        variants.add(stripped)

    return {
        variant
        for variant in variants
        if len(variant) >= 2 and normalize_text_for_match(variant) not in IGNORED_GEO_NAMES_NORMALIZED
    }


def iter_named_items(payload) -> Iterable[str]:
    if isinstance(payload, list):
        for item in payload:
            yield from iter_named_items(item)
    elif isinstance(payload, dict):
        name = payload.get("name")
        if isinstance(name, str) and name.strip():
            yield name.strip()

        has_known_children = False
        for key in ("children", "cities", "districts", "items", "list", "data"):
            child = payload.get(key)
            if child is not None:
                has_known_children = True
                yield from iter_named_items(child)

        if not has_known_children and "name" not in payload:
            for key, value in payload.items():
                if isinstance(key, str) and key.strip():
                    yield key.strip()
                if isinstance(value, (list, dict)):
                    yield from iter_named_items(value)


def build_province_lookup(province_channels: Dict[str, Set[str]]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for province_key in province_channels:
        province_base = province_key.replace("频道", "")
        candidates = set(resolve_province_aliases(province_base))
        candidates.add(normalize_province_name(province_base))
        for candidate in candidates:
            normalized = normalize_text_for_match(normalize_province_name(candidate))
            if len(normalized) >= 2 and normalized not in lookup:
                lookup[normalized] = province_key
    return lookup


def collect_online_geo_tokens(geo_payload, province_channels: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    province_lookup = build_province_lookup(province_channels)
    added_tokens: Dict[str, Set[str]] = defaultdict(set)

    if isinstance(geo_payload, list):
        province_nodes = geo_payload
    elif isinstance(geo_payload, dict):
        if isinstance(geo_payload.get("children"), list):
            province_nodes = geo_payload["children"]
        else:
            province_nodes = [
                {"name": key, "children": value}
                for key, value in geo_payload.items()
                if isinstance(value, (list, dict))
            ]
    else:
        return added_tokens

    for node in province_nodes:
        if not isinstance(node, dict):
            continue

        province_name = node.get("name")
        if not isinstance(province_name, str) or not province_name.strip():
            continue

        province_normalized = normalize_text_for_match(normalize_province_name(province_name))
        province_key = province_lookup.get(province_normalized)
        if not province_key:
            for key, matched_province in province_lookup.items():
                if key and (key in province_normalized or province_normalized in key):
                    province_key = matched_province
                    break
        if not province_key:
            continue

        for raw_name in iter_named_items(node.get("children", [])):
            for variant in geo_name_variants(raw_name):
                normalized_variant = normalize_text_for_match(variant)
                if len(normalized_variant) >= 2 and normalized_variant not in IGNORED_GEO_NAMES_NORMALIZED:
                    added_tokens[province_key].add(variant)

    return added_tokens


async def load_online_geo_tokens(
    session: aiohttp.ClientSession,
    province_channels: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    cdn_cache = load_cdn_cache()
    cache_key = 'geo_data'

    if cache_key in cdn_cache:
        cached_url = cdn_cache[cache_key].get('url')
        if cached_url:
            print(f"Using cached fastest geo CDN: {cached_url}")
            try:
                async with session.get(cached_url, timeout=CONFIG["timeout"]) as response:
                    if response.status == 200:
                        raw_text = await response.text(errors="ignore")
                        payload = json.loads(raw_text)
                        tokens = collect_online_geo_tokens(payload, province_channels)
                        if tokens:
                            total = sum(len(items) for items in tokens.values())
                            print(f"Loaded {total} online geo tokens from cache: {cached_url}")
                        return tokens
            except Exception:
                pass

    cdn_timeout = aiohttp.ClientTimeout(total=CONFIG["source_cdn_test_timeout"], connect=1.5)
    print("Testing geo data CDN sources (parallel)...")

    async def _test_geo_cdn(url):
        try:
            start = time.time()
            async with session.head(url, timeout=cdn_timeout, allow_redirects=True) as resp:
                if resp.status < 400:
                    return url, time.time() - start
                return url, None
        except Exception:
            return url, None

    tasks = [_test_geo_cdn(url) for url in ONLINE_GEO_DATA_URLS]
    results = await asyncio.gather(*tasks)

    best_url = None
    best_latency = float('inf')
    for url, latency in results:
        if latency is not None:
            print(f"  {url}: {latency:.3f}s")
            if latency < best_latency:
                best_latency = latency
                best_url = url
        else:
            print(f"  {url}: failed")

    if not best_url:
        print("  All geo CDN sources failed, skipping online geo tokens.")
        return {}

    print(f"  Fastest: {best_url} ({best_latency:.3f}s)")

    cdn_cache[cache_key] = {'url': best_url, 'latency': best_latency}
    save_cdn_cache(cdn_cache)
    try:
        async with session.get(best_url, timeout=CONFIG["timeout"]) as response:
            if response.status != 200:
                return {}
            raw_text = await response.text(errors="ignore")
            payload = json.loads(raw_text)
            tokens = collect_online_geo_tokens(payload, province_channels)
            if tokens:
                total = sum(len(items) for items in tokens.values())
                print(f"Loaded {total} online geo tokens from: {best_url}")
            return tokens
    except Exception:
        return {}


def build_province_matchers(province_channels: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """构建省份频道匹配词，优先精确词，其次省份关键词兜底。"""
    province_matchers: Dict[str, List[str]] = {}

    for province, channels in province_channels.items():
        patterns = set()
        province_base = province.replace("频道", "")
        aliases = resolve_province_aliases(province_base)
        normalized_aliases = {normalize_text_for_match(alias) for alias in aliases}

        for ch in channels:
            normalized = normalize_text_for_match(ch)
            
            # 【修改点 2】不再将整个频道的全名强行当成合法匹配词，避免脏数据污染。
            # 仅信任通过规则提取出的真正 geo_token
            for geo_token in extract_geo_tokens(ch, normalized_aliases):
                patterns.add(geo_token)

        for alias in aliases:
            normalized_alias = normalize_text_for_match(alias)
            if len(normalized_alias) >= 2:
                patterns.add(normalized_alias)

        province_matchers[province] = sorted(patterns, key=len, reverse=True)

    return province_matchers


def match_province(normalized_channel: str, province_matchers: Dict[str, List[str]]) -> Optional[str]:
    """按最长匹配词命中省份，避免短词误判。"""
    best_match_province = None
    best_score = 0

    for province, patterns in province_matchers.items():
        for pattern in patterns:
            if pattern in normalized_channel:
                score = len(pattern)
                if score > best_score:
                    best_score = score
                    best_match_province = province
                break

    return best_match_province


def match_smart_category(normalized_channel: str) -> Optional[str]:
    """为无法命中省份的频道提供主题兜底分类。"""
    for category, keywords in SMART_CATEGORY_KEYWORDS_NORMALIZED.items():
        for keyword in keywords:
            if keyword and keyword in normalized_channel:
                return category
    if any(ch in normalized_channel for ch in SCENIC_SINGLE_CHAR_HINTS):
        if not any(token in normalized_channel for token in SCENIC_EXCLUDE_HINTS_NORMALIZED):
            return "文旅频道"
    return None


def natural_sort_key(text: str) -> Tuple[Any, ...]:
    parts = re.split(r"(\d+)", text)
    key: List[Any] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return tuple(key)


def cctv_sort_key(channel_name: str) -> Tuple[Any, ...]:
    """
    央视频道排序：
    - CCTV 数字频道按数字升序（CCTV-1, CCTV-2 ... CCTV-16）
    - 同号里普通版优先于 + 版
    - 其余（CHC/CGTN/CCTV专题）按自然排序放后面
    """
    match = re.search(r"(?i)CCTV[\s-]?(\d+)(\+?)", channel_name)
    if match:
        num = int(match.group(1))
        is_plus = 1 if match.group(2) == "+" else 0
        return (0, num, is_plus, natural_sort_key(channel_name))
    return (1, natural_sort_key(channel_name))


def channel_identity_key(channel: str) -> str:
    """频道唯一键（用于去重与选优）。"""
    return normalize_text_for_match(normalize_cctv_name(channel))


def parse_group_title_from_extinf(extinf_line: str) -> Optional[str]:
    patterns = [
        r'group-title\s*=\s*"([^"]+)"',
        r"group-title\s*=\s*'([^']+)'",
        r"group-title\s*=\s*([^,\s]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, extinf_line, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def infer_group_from_upstream_title(
    source_group_title: Optional[str],
    province_matchers: Dict[str, List[str]]
) -> Optional[str]:
    """将上游 group-title 作为分类先验信号。"""
    if not source_group_title:
        return None

    raw_title = source_group_title.strip()
    normalized = normalize_text_for_match(raw_title)
    if not normalized:
        return None

    if any(token in normalized for token in ("CCTV", "CGTN", "CHC")) or "央视" in raw_title:
        return "央视频道"
    if "卫视" in raw_title:
        return "卫视频道"

    province = match_province(normalized, province_matchers)
    if province:
        return province

    smart_category = match_smart_category(normalized)
    if smart_category:
        return smart_category

    return None


def deduplicate_candidate_entries(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduplicated: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()

    for entry in entries:
        channel = str(entry.get("channel", "")).strip()
        url = str(entry.get("url", "")).strip()
        if not channel or not url.startswith(("http://", "https://")):
            continue

        key = (channel_identity_key(channel), url)
        if key in seen:
            continue
        seen.add(key)

        normalized_entry = dict(entry)
        normalized_entry["channel"] = channel
        normalized_entry["url"] = url
        deduplicated.append(normalized_entry)

    return deduplicated


def choose_better_entry(current_best: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    best_latency = current_best.get("latency")
    cand_latency = candidate.get("latency")
    best_score = (
        best_latency if isinstance(best_latency, (int, float)) else float("inf"),
        0 if str(current_best.get("url", "")).startswith("https://") else 1,
        len(str(current_best.get("url", ""))),
    )
    cand_score = (
        cand_latency if isinstance(cand_latency, (int, float)) else float("inf"),
        0 if str(candidate.get("url", "")).startswith("https://") else 1,
        len(str(candidate.get("url", ""))),
    )
    return candidate if cand_score < best_score else current_best


def select_best_streams(valid_entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    去重并选优：
    1) 同频道同 URL 去重
    2) 同频道保留最低延迟（并优先 https）的最佳 URL
    """
    best_by_channel: Dict[str, Dict[str, Any]] = {}

    for entry in valid_entries:
        channel = str(entry.get("channel", "")).strip()
        url = str(entry.get("url", "")).strip()
        if not channel or not url:
            continue

        key = channel_identity_key(channel)
        current = best_by_channel.get(key)
        if current is None:
            best_by_channel[key] = dict(entry)
        else:
            best_by_channel[key] = choose_better_entry(current, entry)

    selected = list(best_by_channel.values())
    selected.sort(key=lambda x: natural_sort_key(str(x.get("channel", ""))))
    return selected


# 从 TXT 文件中提取 IPTV 链接
def extract_urls_from_txt(content):
    """从 TXT 文件中提取 IPTV 链接"""
    urls: List[Dict[str, Any]] = []
    for line in content.splitlines():
        line = line.strip()
        if line and ',' in line:  # 格式应该是: <频道名>,<URL>
            channel, url = line.split(',', 1)
            urls.append({
                "channel": channel.strip(),
                "url": url.strip(),
                "source_group_title": None,
            })
    return urls


# 从 M3U 文件中提取 IPTV 链接
def extract_urls_from_m3u(content):
    """从 M3U 文件中提取 IPTV 链接"""
    urls: List[Dict[str, Any]] = []
    lines = content.splitlines()
    channel = "Unknown"
    source_group_title = None

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # 从 EXTINF 标签中提取频道名
            parts = line.split(',', 1)
            channel = parts[1] if len(parts) > 1 else "Unknown"
            source_group_title = parse_group_title_from_extinf(line)
        elif line.startswith(('http://', 'https://')):
            urls.append({
                "channel": channel.strip(),
                "url": line.strip(),
                "source_group_title": source_group_title,
            })
    return urls


def load_stream_cache():
    """加载流测试结果缓存"""
    if STREAM_CACHE_FILE.exists():
        try:
            cache_age = time.time() - STREAM_CACHE_FILE.stat().st_mtime
            if cache_age < STREAM_CACHE_TTL:
                with open(STREAM_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Loaded stream cache: {len(data)} entries (age: {cache_age/60:.0f}min)")
                return data
            else:
                print(f"Stream cache expired (age: {cache_age/3600:.1f}h > {STREAM_CACHE_TTL/3600}h)")
        except Exception as e:
            print(f"Failed to load stream cache: {e}")
    else:
        print("No stream cache found")
    return {}


def save_stream_cache(cache_data):
    """保存流测试结果缓存"""
    try:
        FILE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STREAM_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f)
        print(f"Saved stream cache: {len(cache_data)} entries to file/{STREAM_CACHE_FILE.name}")
    except Exception as e:
        print(f"Failed to save stream cache: {e}")


def load_source_cache():
    """加载IPTV源文件内容缓存"""
    if SOURCE_CACHE_FILE.exists():
        try:
            cache_age = time.time() - SOURCE_CACHE_FILE.stat().st_mtime
            if cache_age < SOURCE_CACHE_TTL:
                with open(SOURCE_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Loaded source cache: {len(data)} files (age: {cache_age/60:.0f}min)")
                return data
            else:
                print(f"Source cache expired (age: {cache_age/3600:.1f}h > {SOURCE_CACHE_TTL/3600}h)")
        except Exception as e:
            print(f"Failed to load source cache: {e}")
    else:
        print("No source cache found")
    return {}


def save_source_cache(cache_data):
    """保存IPTV源文件内容缓存"""
    try:
        FILE_DIR.mkdir(parents=True, exist_ok=True)
        with open(SOURCE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f)
        print(f"Saved source cache: {len(cache_data)} files")
    except Exception as e:
        print(f"Failed to save source cache: {e}")


# 测试 IPTV 链接的可用性和速度（带缓存）
async def test_stream(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, url: str, stream_cache=None):
    """测试 IPTV 链接的可用性和速度 - 使用 GET 请求读取少量数据快速检测，支持结果缓存"""
    if stream_cache is not None and url in stream_cache:
        cached_result = stream_cache[url]
        if cached_result["valid"]:
            return True, cached_result.get("latency", 0.01)
        else:
            return False, None

    async with semaphore:
        start_time = time.time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"], connect=CONFIG["connect_timeout"]), allow_redirects=True) as response:
                if response.status < 400:
                    try:
                        await response.content.read(1024)
                    except Exception:
                        pass
                    elapsed_time = time.time() - start_time
                    if stream_cache is not None:
                        stream_cache[url] = {"valid": True, "latency": elapsed_time, "timestamp": time.time()}
                    return True, elapsed_time
                else:
                    if stream_cache is not None:
                        stream_cache[url] = {"valid": False, "latency": None, "timestamp": time.time()}
                    return False, None
        except (asyncio.TimeoutError, Exception) as e:
            if stream_cache is not None:
                stream_cache[url] = {"valid": False, "latency": None, "timestamp": time.time(), "error": str(type(e).__name__)}
            return False, None


# 测试多个 IPTV 链接
async def test_multiple_streams(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    entries: Iterable[Dict[str, Any]],
    stream_cache=None
):
    """测试多个 IPTV 链接"""
    tasks = [test_stream(session, semaphore, str(entry.get("url", "")).strip(), stream_cache) for entry in entries]
    results = await asyncio.gather(*tasks)
    return results


# 读取文件并提取 URL（支持 M3U 或 TXT 格式）
async def read_and_test_file(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    file_path: str,
    is_m3u: bool = False,
    stream_cache=None,
    source_cache=None
):
    """读取文件并提取 URL 进行测试 - 支持源文件内容和流测试双重缓存"""
    content = None
    cache_hit = False

    if source_cache is not None and file_path in source_cache:
        cached = source_cache[file_path]
        if cached.get("content"):
            content = cached["content"]
            cache_hit = True
            print(f"  Source cache hit: {file_path[:50]}... ({len(content)} chars)")

    if content is None:
        try:
            async with session.get(file_path, timeout=CONFIG["timeout"]) as response:
                if response.status != 200:
                    return []
                content = await response.text(errors="ignore")

            if source_cache is not None:
                source_cache[file_path] = {
                    "content": content,
                    "timestamp": time.time(),
                    "size": len(content)
                }
                print(f"  Downloaded & cached: {file_path[:50]}... ({len(content)} chars)")

        except Exception:
            return []

    if is_m3u:
        entries = extract_urls_from_m3u(content)
    else:
        entries = extract_urls_from_txt(content)
    entries = deduplicate_candidate_entries(entries)

    if not cache_hit:
        print(f"  Extracted {len(entries)} URLs from {file_path[:30]}...")

    valid_entries: List[Dict[str, Any]] = []
    results = await test_multiple_streams(session, semaphore, entries, stream_cache)
    for (is_valid, latency), entry in zip(results, entries):
        if is_valid:
            valid_entries.append({
                "channel": entry["channel"],
                "url": entry["url"],
                "source_group_title": entry.get("source_group_title"),
                "latency": latency,
            })

    return valid_entries


# 生成排序后的 M3U 和 M3U8 文件
def generate_sorted_m3u(valid_entries, cctv_channels, province_channels, filename):
    """生成排序后的 M3U 和 M3U8 文件"""
    cctv_channels_list = []
    province_channels_list = defaultdict(list)
    satellite_channels = []
    smart_category_channels = defaultdict(list)
    other_channels = []
    normalized_cctv_channels = {
        normalize_text_for_match(normalize_cctv_name(name)) for name in cctv_channels
    }
    province_matchers = build_province_matchers(province_channels)

    for entry in valid_entries:
        channel = str(entry.get("channel", "")).strip()
        url = str(entry.get("url", "")).strip()
        source_group_title = entry.get("source_group_title")
        if not channel or not url:
            continue

        if contains_date(channel) or contains_date(url):
            continue  # 过滤掉包含日期格式的频道

        normalized_channel = normalize_text_for_match(normalize_cctv_name(channel))
        upstream_group = infer_group_from_upstream_title(source_group_title, province_matchers)

        # 根据频道名判断属于哪个分组
        if is_cctv_channel(channel, normalized_channel, normalized_cctv_channels) or upstream_group == "央视频道":
            cctv_channels_list.append({
                "channel": channel,
                "url": url,
                "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                "group_title": "央视频道"
            })
        elif "卫视" in channel or upstream_group == "卫视频道":  # 卫视频道
            satellite_channels.append({
                "channel": channel,
                "url": url,
                "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                "group_title": "卫视频道"
            })
        else:
            province = match_province(normalized_channel, province_matchers)
            if province:
                province_channels_list[province].append({
                    "channel": channel,
                    "url": url,
                    "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                    "group_title": f"{province}"
                })
            else:
                smart_category = upstream_group if upstream_group in SMART_CATEGORY_KEYWORDS else match_smart_category(normalized_channel)
                if smart_category and smart_category in SMART_CATEGORY_KEYWORDS:
                    smart_category_channels[smart_category].append({
                        "channel": channel,
                        "url": url,
                        "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                        "group_title": smart_category
                    })
                else:
                    other_channels.append({
                        "channel": channel,
                        "url": url,
                        "logo": f"https://live.fanmingming.cn/tv/{channel}.png",
                        "group_title": "其他频道"
                    })

    # 排序：省份频道、主题频道、卫视频道、其他频道
    cctv_channels_list.sort(key=lambda x: cctv_sort_key(x["channel"]))

    for province in province_channels_list:
        province_channels_list[province].sort(key=lambda x: natural_sort_key(x["channel"]))
    for smart_category in smart_category_channels:
        smart_category_channels[smart_category].sort(key=lambda x: natural_sort_key(x["channel"]))

    satellite_channels.sort(key=lambda x: natural_sort_key(x["channel"]))
    other_channels.sort(key=lambda x: natural_sort_key(x["channel"]))

    # 合并所有频道：CCTV -> 卫视频道 -> 省份频道 -> 主题频道 -> 其他
    all_channels = cctv_channels_list + satellite_channels + \
                   [channel for province in sorted(province_channels_list) for channel in
                    province_channels_list[province]] + \
                   [channel for smart_category in SMART_CATEGORY_KEYWORDS for channel in
                    smart_category_channels.get(smart_category, [])] + \
                   other_channels

    # 生成 m3u8 的文件名 (将后缀 .m3u 替换为 .m3u8)
    m3u8_filename = filename.replace('.m3u', '.m3u8')
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
    
    # 写入 M3U 和 M3U8 文件
    for fname in [filename, m3u8_filename]:
        with open(fname, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Generated-Time: {generated_at}\n")
            f.write(f"# Channel-Count: {len(all_channels)}\n")
            for channel_info in all_channels:
                f.write(
                    f"#EXTINF:-1 tvg-name=\"{channel_info['channel']}\" tvg-logo=\"{channel_info['logo']}\" group-title=\"{channel_info['group_title']}\",{channel_info['channel']}\n")
                f.write(f"{channel_info['url']}\n")

def load_province_channels(files):
    """加载多个省份的频道列表"""
    province_channels = defaultdict(set)

    for file_path in files:
        province_name = os.path.basename(file_path).replace(".txt", "")  # 使用文件名作为省份名称

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:  # 忽略空行
                        province_channels[province_name].add(line)
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")

    return province_channels


async def _select_fastest_source_cdns(source_groups):
    """对每个 IPTV 源的多个 CDN 镜像并行测速，选最快的 URL（带缓存）。"""
    cdn_cache = load_cdn_cache()

    cached_results = {}
    groups_to_test = []

    for idx, group in enumerate(source_groups):
        cache_key = f'source_{idx}'
        if cache_key in cdn_cache and cdn_cache[cache_key].get('url') in group['urls']:
            cached_results[idx] = cdn_cache[cache_key]
            print(f"Using cached CDN: {group['name']} -> {cdn_cache[cache_key]['url']}")
        else:
            groups_to_test.append((idx, group))

    if groups_to_test:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        cdn_timeout = aiohttp.ClientTimeout(total=CONFIG["source_cdn_test_timeout"], connect=1.5)
        connector = aiohttp.TCPConnector(limit=30, ttl_dns_cache=CONFIG["dns_cache_ttl"],
                                         ssl=ssl_context, force_close=True, enable_cleanup_closed=True)

        async def _test_one_cdn(session, url):
            try:
                start = time.time()
                async with session.head(url, timeout=cdn_timeout, allow_redirects=True) as resp:
                    if resp.status < 400:
                        return url, time.time() - start
                    return url, None
            except Exception:
                return url, None

        all_tasks = []
        task_to_group = []
        print(f"Testing {len(groups_to_test)} IPTV source groups (fully parallel)...")

        async with aiohttp.ClientSession(timeout=cdn_timeout, connector=connector) as session:
            for idx, group in groups_to_test:
                for url in group["urls"]:
                    task = asyncio.create_task(_test_one_cdn(session, url))
                    all_tasks.append(task)
                    task_to_group.append((idx, group["name"], url))

            results = await asyncio.gather(*all_tasks)

            group_results = {}
            for i, (url, latency) in enumerate(results):
                gidx, name, original_url = task_to_group[i]
                if gidx not in group_results:
                    group_results[gidx] = {'name': name, 'urls': []}
                if latency is not None:
                    print(f"  {name} | {url}: {latency:.3f}s")
                    group_results[gidx]['urls'].append((url, latency))
                else:
                    print(f"  {name} | {url}: failed")

            for gidx, data in group_results.items():
                if data['urls']:
                    best_url, best_latency = min(data['urls'], key=lambda x: x[1])
                    cached_results[gidx] = {'url': best_url, 'latency': best_latency}
                    print(f"  -> Selected: {best_url} ({best_latency:.3f}s)")
                else:
                    group = next(g for i, g in groups_to_test if i == gidx)
                    fallback_url = group["urls"][-1]
                    cached_results[gidx] = {'url': fallback_url, 'latency': float('inf')}
                    print(f"  -> Fallback: {fallback_url}")

        for cache_key, result in ((f'source_{k}', v) for k, v in cached_results.items() if k >= len(cached_results) - len(groups_to_test)):
            pass

        save_cdn_cache({**cdn_cache, **{f'source_{k}': v for k, v in cached_results.items()}})

    selected_urls = [cached_results[i]['url'] for i in range(len(source_groups))]
    print(f"Selected {len(selected_urls)} source URLs via CDN speed test.")
    return selected_urls


# 主函数：处理多个文件并生成 M3U 输出
async def main(file_urls, cctv_channel_file, province_channel_files):
    """主函数处理多个文件"""
    asyncio.get_event_loop().set_exception_handler(_suppress_asyncio_exception)

    cctv_channels = load_cctv_channels(cctv_channel_file)
    province_channels = load_province_channels(province_channel_files)

    all_valid_entries: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(CONFIG["max_parallel"])

    timeout = aiohttp.ClientTimeout(total=CONFIG["timeout"], connect=CONFIG["connect_timeout"])
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(limit=CONFIG["max_parallel"] * 2, ttl_dns_cache=CONFIG["dns_cache_ttl"], ssl=ssl_context,
                                     force_close=True, enable_cleanup_closed=True)
    async with aiohttp.ClientSession(cookie_jar=None, timeout=timeout, connector=connector) as session:
        online_geo_tokens = await load_online_geo_tokens(session, province_channels)
        if online_geo_tokens:
            for province, tokens in online_geo_tokens.items():
                province_channels[province].update(tokens)
            print("Online geo classification tokens merged.")
        else:
            print("Online geo tokens unavailable, fallback to local province txt only.")

        stream_cache = load_stream_cache()
        source_cache = load_source_cache()
        tasks = []
        for file_url in file_urls:
            is_m3u = file_url.endswith(('.m3u', '.m3u8'))
            tasks.append(read_and_test_file(session, semaphore, file_url, is_m3u=is_m3u, stream_cache=stream_cache, source_cache=source_cache))

        results = await asyncio.gather(*tasks)
        for valid_entries in results:
            all_valid_entries.extend(valid_entries)

    save_stream_cache(stream_cache)
    save_source_cache(source_cache)

    deduplicated_entries = deduplicate_candidate_entries(all_valid_entries)
    best_entries = select_best_streams(deduplicated_entries)
    print(f"Valid streams: {len(all_valid_entries)}, deduplicated: {len(deduplicated_entries)}, best-per-channel: {len(best_entries)}")

    # 生成排序后的 M3U 文件
    generate_sorted_m3u(best_entries, cctv_channels, province_channels, CONFIG["output_file"])
    print(f"Generated sorted M3U file: {CONFIG['output_file']}")


if __name__ == "__main__":
    IPTV_SOURCE_CDNS = [
        {
            "name": "Guovin/iptv-api (jsdelivr)",
            "urls": [
                "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt",
                "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.txt",
            ],
        },
        {
            "name": "vbskycn/iptv (gh-proxy)",
            "urls": [
                "https://gh-proxy.com/raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.m3u",
                "https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.m3u",
            ],
        },
        {
            "name": "suxuang/myIPTV (jsdelivr)",
            "urls": [
                "https://cdn.jsdelivr.net/gh/suxuang/myIPTV@main/ipv4.m3u",
                "https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv4.m3u",
            ],
        },
        {
            "name": "Guovin/iptv-api ipv4 (jsdelivr)",
            "urls": [
                "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/ipv4/result.m3u",
                "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/ipv4/result.m3u",
            ],
        },
        {
            "name": "hujingguang/ChinaIPTV (gh-proxy)",
            "urls": [
                "https://gh-proxy.com/raw.githubusercontent.com/hujingguang/ChinaIPTV/main/cnTV_AutoUpdate.m3u8",
                "https://raw.githubusercontent.com/hujingguang/ChinaIPTV/main/cnTV_AutoUpdate.m3u8",
            ],
        },
    ]

    cctv_channel_file = ".github/workflows/IPTV/CCTV.txt"

    province_channel_files = []
    iptv_dir = ".github/workflows/IPTV"
    if os.path.isdir(iptv_dir):
        for fname in sorted(os.listdir(iptv_dir)):
            if fname.endswith("频道.txt"):
                province_channel_files.append(os.path.join(iptv_dir, fname))

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    if os.path.isdir(os.path.join(project_root, '.github')):
        os.chdir(project_root)

    total_start = time.time()

    cdn_start = time.time()
    file_urls = asyncio.run(_select_fastest_source_cdns(IPTV_SOURCE_CDNS))
    cdn_elapsed = time.time() - cdn_start
    print(f"CDN speed test took: {cdn_elapsed:.1f}s")

    collect_start = time.time()
    asyncio.run(main(file_urls, cctv_channel_file, province_channel_files))
    collect_elapsed = time.time() - collect_start
    if collect_elapsed >= 60:
        print(f"Stream collection took: {int(collect_elapsed//60)}m {int(collect_elapsed%60)}s")
    else:
        print(f"Stream collection took: {collect_elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    if total_elapsed >= 60:
        print(f"Total iptv.py took: {int(total_elapsed//60)}m {int(total_elapsed%60)}s")
    else:
        print(f"Total iptv.py took: {total_elapsed:.1f}s")