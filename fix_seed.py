import re

with open('frontend/src/mocks/seed.ts', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
new_lines = []

in_project_block = False
current_block = []

for line in lines:
    if 'id: "p' in line:
        in_project_block = True
    
    if in_project_block:
        current_block.append(line)
        if line.strip() in ['},', '}']:
            in_project_block = False
            
            keys_seen = {}
            to_remove = set()
            
            for i, bline in enumerate(current_block):
                match = re.match(r'\s*([a-zA-Z0-9_]+):', bline)
                if match:
                    key = match.group(1)
                    if key in keys_seen:
                        to_remove.add(keys_seen[key])
                    keys_seen[key] = i
                    
            for i, bline in enumerate(current_block):
                if i not in to_remove:
                    new_lines.append(bline)
                    
            current_block = []
    else:
        if not current_block:
            new_lines.append(line)

with open('frontend/src/mocks/seed.ts', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
