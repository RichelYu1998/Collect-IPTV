#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import smtplib
import time
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders
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
                'detail': '首次检测到文件',
                'filepath': str(fpath)
            })
        elif old != current:
            size = os.path.getsize(str(fpath))
            changes.append({
                'file': fname,
                'type': 'updated',
                'detail': f'文件已变更 (大小: {size} 字节)',
                'filepath': str(fpath)
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

    msg = MIMEMultipart('mixed')
    msg['From'] = f"{Header(from_name, 'utf-8').encode()} <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = Header(
        f'【IPTV直播源变更通知】检测到{change_count}个文件变化 - {current_time}',
        'utf-8'
    )

    # 邮件正文
    body_lines = [f'IPTV直播源文件变更通知', '', f'时间: {current_time}', '']
    for c in changes:
        tag = '新增' if c['type'] == 'new' else '变更'
        body_lines.append(f'[{tag}] {c["file"]} - {c["detail"]}')
    
    attachment_files = []
    for c in changes:
        filepath = c.get('filepath', '')
        if filepath and os.path.exists(filepath):
            attachment_files.append(filepath)
    
    body_lines.append('')
    body_lines.append(f'已将变更的文件作为附件发送（共{len(attachment_files)}个文件）:')
    for fpath in attachment_files:
        fname = os.path.basename(fpath)
        body_lines.append(f'  - {fname}')
    
    body_lines.append('')
    body_lines.append('请查收附件中的最新直播源文件。')
    body = '\n'.join(body_lines)

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 添加附件
    for filepath in attachment_files:
        try:
            filename = os.path.basename(filepath)
            
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            
            msg.attach(part)
            print(f'[通知] 已添加附件: {filename}')
            
        except Exception as e:
            print(f'[通知] 添加附件失败 {filepath}: {e}')

    try:
        print('[通知] 正在发送邮件...')
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        server.starttls()
        server.login(smtp_user, smtp_password)
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


def check_and_notify(config):
    """检测变更并发送邮件（含附件）- 首次或变化即发送"""
    watch_files = config.get('watch_files', ['best_sorted.m3u', 'best_sorted.m3u8'])
    old_hashes = load_hashes()
    
    # 检查是否有历史记录（首次运行）
    is_first_run = (not old_hashes or len(old_hashes) == 0)
    
    # 查找存在的文件
    existing_files = []
    for fname in watch_files:
        fpath = PROJECT_ROOT / fname
        if fpath.exists():
            current_hash = file_hash(str(fpath))
            if current_hash:
                existing_files.append({
                    'file': fname,
                    'type': 'new' if is_first_run else 'updated',
                    'detail': '首次生成文件' if is_first_run else '文件已更新',
                    'filepath': str(fpath),
                    'hash': current_hash
                })
                
                # 更新哈希记录
                old_hashes[fname] = current_hash
    
    # 如果没有找到任何文件
    if not existing_files:
        if is_first_run:
            print('[通知] 首次运行，未找到监控文件')
        return False
    
    # 显示检测到的文件
    action_type = "首次运行" if is_first_run else "文件变更"
    print(f'[通知] {action_type} - 检测到 {len(existing_files)} 个文件:')
    for f in existing_files:
        print(f'    [{f["type"]}] {f["file"]} - {f["detail"]}')
    
    # 直接发送邮件（无冷却限制）
    success = send_email(config, existing_files)
    
    if success:
        # 保存最新的哈希记录
        save_hashes(old_hashes)
        print(f'[通知] ✓ 邮件发送成功 ({action_type})')
        return True
    else:
        print('[通知] ✗ 邮件发送失败')
        return False


def main():
    """主函数：持续监控文件变更"""
    config = load_config()
    if not config:
        return

    if not config.get('email_notification_enabled', False):
        print('[通知] 邮件通知未启用，跳过')
        return
    
    interval = int(config.get('watch_interval_seconds', 60))
    
    print('=' * 60)
    print('IPTV 直播源文件监控服务 (带附件)')
    print('=' * 60)
    print(f'[通知] 监控文件: {config.get("watch_files", [])}')
    print(f'[通知] 检查间隔: {interval} 秒')
    print(f'[通知] 发送策略: 首次运行或文件变化时立即发送')
    print(f'[通知] 接收邮箱: {config.get("email_to", "未设置")}')
    print(f'[通知] 附件模式: 开启 (M3U/M3U8文件将作为附件发送)')
    print('=' * 60)
    print('[通知] 开始监控... (按 Ctrl+C 停止)')
    print('')
    
    print('[通知] 执行首次检测...')
    check_and_notify(config)
    
    try:
        while True:
            time.sleep(interval)
            check_and_notify(config)
    except KeyboardInterrupt:
        print('\n[通知] 监控已停止')


if __name__ == '__main__':
    main()


