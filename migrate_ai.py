import re

file_path = r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\ai.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 fetch(`${apiBase}/default-replies`) -> window.API.defaultReplies.list()
content = content.replace(
    "fetch(`${apiBase}/default-replies`)",
    "window.API.defaultReplies.list()"
)

# 替换 fetch(`${apiBase}/default-replies/${cookieId}`) -> window.API.defaultReplies.get(cookieId)
content = content.replace(
    "fetch(`${apiBase}/default-replies/${cookieId}`)",
    "window.API.defaultReplies.get(cookieId)"
)

# 替换 fetch(`${apiBase}/ai-reply-settings/${accountId}`) GET -> window.API.ai.getSettings(accountId)
content = content.replace(
    "fetch(`${apiBase}/ai-reply-settings/${accountId}`)",
    "window.API.ai.getSettings(accountId)"
)

# 替换 window.App.showToast -> showToast
content = content.replace("window.App.showToast", "showToast")

# 替换 window.App.toggleLoading -> toggleLoading
content = content.replace("window.App.toggleLoading", "toggleLoading")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("ai.js migration completed")
