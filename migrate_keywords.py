import re

file_path = r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\keywords.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 import 语句
content = content.replace(
    "import { showToast, toggleLoading, fetchJSON } from './api.js';",
    "import { showToast, toggleLoading } from './api.js';"
)

# 替换 fetchJSON(apiBase + '/cookies/details')
content = content.replace(
    "fetchJSON(apiBase + '/cookies/details')",
    "window.API.cookies.list()"
)

# 替换 fetch(`${apiBase}/cookies/details`)
content = content.replace(
    "fetch(`${apiBase}/cookies/details`)",
    "window.API.cookies.list()"
)

# 替换 fetch(`${apiBase}/keywords/${accountId}`)
content = content.replace(
    "fetch(`${apiBase}/keywords/${accountId}`)",
    "window.API.keywords.list(accountId)"
)

# 替换 fetch(`${apiBase}/keywords/${account.id}`)
content = content.replace(
    "fetch(`${apiBase}/keywords/${account.id}`)",
    "window.API.keywords.list(account.id)"
)

# 替换 fetch(`${apiBase}/keywords-with-item-id/${accountId}`)
content = content.replace(
    "fetch(`${apiBase}/keywords-with-item-id/${accountId}`)",
    "window.API.keywords.listWithItemId(accountId)"
)

# 替换 fetch(`${apiBase}/items/${accountId}`)
content = content.replace(
    "fetch(`${apiBase}/items/${accountId}`)",
    "window.API.items.getByCookie(accountId)"
)

# 替换 fetch(`${apiBase}/items/${currentCookieId}`)
content = content.replace(
    "fetch(`${apiBase}/items/${currentCookieId}`)",
    "window.API.items.getByCookie(currentCookieId)"
)

# 替换 window.App.showToast -> showToast
content = content.replace("window.App.showToast", "showToast")

# 替换 window.App.toggleLoading -> toggleLoading
content = content.replace("window.App.toggleLoading", "toggleLoading")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("keywords.js migration completed")
