import os
import re
import uuid

directory = r'c:\CFAI_Project\tourist-route-planner\frontend\src'
for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(('.jsx', '.js')):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content
            
            def add_attrs_input(match):
                inner = match.group(1)
                attrs = []
                if 'title=' not in inner: attrs.append('title="Input field"')
                if 'aria-label=' not in inner: attrs.append('aria-label="Input field"')
                if 'id=' not in inner: attrs.append(f'id="inp-{uuid.uuid4().hex[:6]}"')
                return f'<input {" ".join(attrs)}{inner}>'

            def add_attrs_select(match):
                inner = match.group(1)
                attrs = []
                if 'title=' not in inner: attrs.append('title="Select dropdown"')
                if 'aria-label=' not in inner: attrs.append('aria-label="Select dropdown"')
                if 'id=' not in inner: attrs.append(f'id="sel-{uuid.uuid4().hex[:6]}"')
                return f'<select {" ".join(attrs)}{inner}>'

            new_content = re.sub(r'<input([^>]*)>', add_attrs_input, new_content)
            new_content = re.sub(r'<select([^>]*)>', add_attrs_select, new_content)

            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
