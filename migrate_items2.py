import re

file_path = r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\items.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern-based replacements
patterns = [
    # Simple replacements
    (r"fetch\(`${apiBase}/cookies/details`\)", "window.API.cookies.list()"),
    (r"fetch\(`${apiBase}/items`\)", "window.API.items.list()"),
    (r"fetch\(`${apiBase}/items/cookie/\${encodeURIComponent\(cookieId\)}\)", "window.API.items.getByCookie(cookieId)"),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Simple string replacements (more reliable)
simple_replacements = [
    ("window.App.showToast", "showToast"),
    ("window.App.toggleLoading", "toggleLoading"),
]

for old, new in simple_replacements:
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("items.js pattern migration completed")
