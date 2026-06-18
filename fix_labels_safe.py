import os
import re

def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        label_open = match.group(1)
        inner = match.group(2)
        label_close = match.group(3)
        
        if '<input' in inner or '<select' in inner:
            return match.group(0)
            
        div_open = label_open.replace('<label', '<div', 1)
        return f"{div_open}{inner}</div>"

    new_content = re.sub(r'(<label[^>]*>)(.*?)(</label>)', replacer, content, flags=re.DOTALL)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

directory = r'c:\CFAI_Project\tourist-route-planner\frontend\src'
for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(('.jsx', '.js')):
            process_file(os.path.join(root, file))
