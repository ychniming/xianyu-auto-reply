import re

file_path = r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\delivery.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 fetch(`${apiBase}/delivery-rules`) -> window.API.delivery.list()
content = content.replace(
    "fetch(`${apiBase}/delivery-rules`)",
    "window.API.delivery.list()"
)

# 替换 fetch(`${apiBase}/delivery-rules/${ruleId}`) -> window.API.delivery.get(ruleId)
content = content.replace(
    "fetch(`${apiBase}/delivery-rules/${ruleId}`)",
    "window.API.delivery.get(ruleId)"
)

# 替换 fetch(`${apiBase}/cards`) -> window.API.cards.list()
content = content.replace(
    "fetch(`${apiBase}/cards`)",
    "window.API.cards.list()"
)

# 替换 window.App.showToast -> showToast
content = content.replace("window.App.showToast", "showToast")

# 替换 window.App.toggleLoading -> toggleLoading
content = content.replace("window.App.toggleLoading", "toggleLoading")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("delivery.js migration completed")
