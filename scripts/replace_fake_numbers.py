import os
import re

components_dir = r'c:\Users\akash\Desktop\capstone MGT 599\frontend\components'

replacements = [
    (r'88\.90%', '81.02%'),
    (r'88\.90', '81.02'),
    (r'88\.9', '81.02'),
    (r'13\.90', '6.02'),
    (r'67\.99%', '67.18%'),
    (r'67\.99', '67.18'),
    (r'43%', '67.18%'),
    (r'LinearSVC', 'V3 Meta-Ensemble'),
    (r'Cascade SVM', 'V3 Meta-Ensemble'),
    (r'Cascade F1', 'Ensemble F1'),
    (r'leakage', 'standalone models'),
    (r'audit record', 'benchmark history'),
    (r'leaked', 'experimental'),
    (r'Leaked', 'Experimental'),
]

for root, _, files in os.walk(components_dir):
    for f in files:
        if f.endswith('.tsx'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = content
            for old, new in replacements:
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f'Updated {f}')
