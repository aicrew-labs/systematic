import re

html=open('c:/Personal/Projects/systematic/systematic/erp_data/edit_4305.html', encoding='utf-8').read()
scripts = re.findall(r'<script[^>]*src=[\'\"]([^\'\"]+)[\'\"]', html)
print(scripts)
