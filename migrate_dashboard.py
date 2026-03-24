import re

file_path = r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\dashboard.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 fetch(`${apiBase}/cookies/details`) -> window.API.cookies.list()
content = content.replace(
    "fetch(`${apiBase}/cookies/details`)",
    "window.API.cookies.list()"
)

# 替换 fetch(`${apiBase}/keywords/${account.id}`) -> window.API.keywords.list(account.id)
content = content.replace(
    "fetch(`${apiBase}/keywords/${account.id}`)",
    "window.API.keywords.list(account.id)"
)

# 替换 window.App.showToast -> showToast
content = content.replace("window.App.showToast", "showToast")

# 替换 window.App.toggleLoading -> toggleLoading
content = content.replace("window.App.toggleLoading", "toggleLoading")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("dashboard.js migration completed")
