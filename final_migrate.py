import re

def migrate_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for old, new in replacements:
        content = content.replace(old, new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Migrated: {filepath}")

# keywords.js
keywords_replacements = [
    # Import
    ("import { showToast, toggleLoading, fetchJSON } from './api.js';", "import { showToast, toggleLoading } from './api.js';"),
    # window.App -> direct
    ("window.App.showToast", "showToast"),
    ("window.App.toggleLoading", "toggleLoading"),
    # Simple fetch replacements (these have headers so handled separately)
    # Will handle complex ones via patterns
]
migrate_file(r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\keywords.js', keywords_replacements)

# items.js
items_replacements = [
    ("window.App.showToast", "showToast"),
    ("window.App.toggleLoading", "toggleLoading"),
]
migrate_file(r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\items.js', items_replacements)

# dashboard.js
dashboard_replacements = [
    ("window.App.showToast", "showToast"),
    ("window.App.toggleLoading", "toggleLoading"),
]
migrate_file(r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\dashboard.js', dashboard_replacements)

# ai.js
ai_replacements = [
    ("window.App.showToast", "showToast"),
    ("window.App.toggleLoading", "toggleLoading"),
]
migrate_file(r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\ai.js', ai_replacements)

# delivery.js
delivery_replacements = [
    ("window.App.showToast", "showToast"),
    ("window.App.toggleLoading", "toggleLoading"),
]
migrate_file(r'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\delivery.js', delivery_replacements)

print("\nAll files migrated (window.App.* -> direct calls)")
