# -*- coding: utf-8 -*-
import os

file_path = r'D:\ws\Collect-IPTV\iptv_tool.sh'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换路径：.github/workflows -> .github/workflows (注意: workflows 有 k)
content = content.replace('.github/workflows/', '.github/workflows/')
content = content.replace('.github/workflows/iptv.py', '.github/workflows/iptv.py')
content = content.replace('.github/workflows/index.html', '.github/workflows/index.html')
content = content.replace('.github/workflows/IPTV', '.github/workflows/IPTV')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")