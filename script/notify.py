#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import smtplib
import time
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / 'config'
CONFIG_FILE = CONFIG_DIR / 'notify.json'
HASH_FILE = CONFIG_DIR / '.notify_hashes.json'


def load_config():
    if not CONFIG_FILE.exists():
        example = CONFIG_DIR / 'notify.json.example'
        if example.exists():
            import shutil
            shutil.copy2(str(example), str(CONFIG_FILE))
            print(f'[通知] 已从模板创建配置文件: {CONFIG_FILE}')
            print('[通知] 请编辑 config/notify.json 填写邮件信息后重试')
        else:
            print('[通知] 配置文件不存在，跳过通知')
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'[通知] 读取配置失败: {e}')
        return None


def load_hashes():
    if HASH_FILE.exists():
        try:
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_hashes(hashes):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(HASH_FILE, 'w', encoding='utf-8') as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def detect_changes(config):
    watch_files = config.get('watch_files', ['best_sorted.m3u', 'best_sorted.m3u8'])
    old_hashes = load_hashes()
    new_hashes = {}
    changes = []

    for fname in watch_files:
        fpath = PROJECT_ROOT / fname
        current = file_hash(str(fpath))
        new_hashes[fname] = current

        if current is None:
            continue

        old = old_hashes.get(fname)
        if old is None:
            changes.append({
                'file': fname,
                'type': 'new',
                'detail': '首次检测到文件'
            })
        elif old != current:
            size = os.path.getsize(str(fpath))
            changes.append({
                'file': fname,
                'type': 'updated',
                'detail': f'文件已变更 (大小: {size} 字节)'
            })

    save_hashes(new_hashes)
    return changes


def send_email(config, changes):
    smtp_host = config.get('email_smtp_host', 'smtp.qq.com')
    smtp_port = int(config.get('email_smtp_port', 587))
    smtp_user = config.get('email_smtp_user', '')
    smtp_password = config.get('email_smtp_password', '')
    from_name = config.get('email_from_name', 'IPTV直播源监控')
    to_email = config.get('email_to', '')

    if not smtp_user or not smtp_password or not to_email:
        print('[通知] 邮件配置不完整，跳过发送')
        return False

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    change_count = len(changes)

    msg = MIMEMultipart('alternative')
    msg['From'] = f"{Header(from_name, 'utf-8').encode()} <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = Header(
        f'【IPTV直播源变更通知】检测到{change_count}个文件变化 - {current_time}',
        'utf-8'
    )

    body_lines = [f'IPTV直播源文件变更通知', '', f'时间: {current_time}', '']
    for c in changes:
        tag = '新增' if c['type'] == 'new' else '变更'
        body_lines.append(f'[{tag}] {c["file"]} - {c["detail"]}')
    body_lines.append('')
    body_lines.append('请及时查看更新后的直播源文件。')
    body = '\n'.join(body_lines)

    html_rows = ''
    for c in changes:
        tag = '🆕 新增' if c['type'] == 'new' else '🔄 变更'
        color = '#28a745' if c['type'] == 'new' else '#fd7e14'
        html_rows += f'<tr><td style="color:{color};font-weight:bold;">{tag}</td><td>{c["file"]}</td><td>{c["detail"]}</td></tr>'

    html_body = f"""
<html>
<body>
<h2 style="color:#333;">IPTV直播源文件变更通知</h2>
<table style="border-collapse:collapse;width:100%;max-width:600px;">
<tr style="background:#f5f5f5;"><th style="padding:8px;border:1px solid #ddd;">类型</th><th style="padding:8px;border:1px solid #ddd;">文件</th><th style="padding:8px;border:1px solid #ddd;">详情</th></tr>
{html_rows}
</table>
<p style="color:#666;margin-top:16px;">检测时间: {current_time}</p>
<p style="color:#999;">此邮件由 IPTV 直播源采集工具自动发送</p>
</body>
</html>
"""

    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        print(f'[通知] 正在连接 SMTP 服务器: {smtp_host}:{smtp_port}')
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.starttls()

        print('[通知] 正在登录 SMTP 服务器...')
        server.login(smtp_user, smtp_password)

        print('[通知] 正在发送邮件...')
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()

        print(f'[通知] 邮件已成功发送至 {to_email}')
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f'[通知] SMTP 认证失败: {e}，请检查邮箱账号和授权码')
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f'[通知] SMTP 连接断开: {e}，请检查网络连接')
        return False
    except smtplib.SMTPException as e:
        print(f'[通知] SMTP 错误: {e}')
        return False
    except Exception as e:
        print(f'[通知] 发送邮件失败: {e}')
        return False


def main():
    config = load_config()
    if not config:
        return

    if not config.get('email_notification_enabled', False):
        print('[通知] 邮件通知未启用，跳过')
        return

    changes = detect_changes(config)
    if not changes:
        print('[通知] 未检测到文件变更')
        return

    print(f'[通知] 检测到 {len(changes)} 个文件变更:')
    for c in changes:
        print(f'    [{c["type"]}] {c["file"]} - {c["detail"]}')

    cooldown = int(config.get('email_cooldown_seconds', 300))
    hash_data = load_hashes()
    last_sent = hash_data.get('_last_email_sent', 0)
    now = time.time()

    if now - last_sent < cooldown:
        remaining = int(cooldown - (now - last_sent))
        print(f'[通知] 邮件冷却中，剩余 {remaining} 秒')
        return

    success = send_email(config, changes)

    if success:
        hash_data = load_hashes()
        hash_data['_last_email_sent'] = now
        save_hashes(hash_data)
    else:
        hash_data = load_hashes()
        fail_count = hash_data.get('_email_fail_count', 0) + 1
        max_fail = int(config.get('email_max_fail_count', 3))
        fail_cooldown = int(config.get('email_fail_cooldown_seconds', 1800))

        if fail_count >= max_fail:
            hash_data['_email_fail_count'] = 0
            hash_data['_last_email_sent'] = now + fail_cooldown - cooldown
            print(f'[通知] 连续发送失败 {fail_count} 次，暂停 {fail_cooldown} 秒')
        else:
            hash_data['_email_fail_count'] = fail_count

        save_hashes(hash_data)


if __name__ == '__main__':
    main()