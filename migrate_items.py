import re

file_path = r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\items.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 fetch(`${apiBase}/cookies/details`) -> window.API.cookies.list()
content = content.replace(
    "fetch(`${apiBase}/cookies/details`)",
    "window.API.cookies.list()"
)

# 替换 fetch(`${apiBase}/items`) -> window.API.items.list()
content = content.replace(
    "fetch(`${apiBase}/items`)",
    "window.API.items.list()"
)

# 替换 fetch(`${apiBase}/items/cookie/${encodeURIComponent(cookieId)}`) -> window.API.items.getByCookie(cookieId)
content = content.replace(
    "fetch(`${apiBase}/items/cookie/${encodeURIComponent(cookieId)}`)",
    "window.API.items.getByCookie(cookieId)"
)

# 替换 fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}/multi-spec`) -> window.API.items.toggleMultiSpec(cookieId, itemId, isMultiSpec)
content = content.replace(
    "fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}/multi-spec`)",
    "window.API.items.toggleMultiSpec(cookieId, itemId)"
)

# 替换 fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`) GET -> window.API.items.get(cookieId, itemId)
content = content.replace(
    "fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`)",
    "window.API.items.get(cookieId, itemId)"
)

# 替换 window.App.showToast -> showToast
content = content.replace("window.App.showToast", "showToast")

# 替换 window.App.toggleLoading -> toggleLoading
content = content.replace("window.App.toggleLoading", "toggleLoading")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("items.js migration completed")
