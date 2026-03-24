$file = 'd:\我的\创业\xianyu-auto-reply-main\static\js\modules\keywords.js'
$content = Get-Content $file -Raw

# 替换 import 语句
$content = $content -replace "import \{ showToast, toggleLoading, fetchJSON \} from './api.js';", "import { showToast, toggleLoading } from './api.js';"

# 替换 fetchJSON(apiBase + '/cookies/details') -> window.API.cookies.list()
$content = $content -replace "fetchJSON\(apiBase \+ '/cookies/details'\)", "window.API.cookies.list()"

# 替换 fetch(`${apiBase}/cookies/details`) -> window.API.cookies.list()
$content = $content -replace "fetch\(`\$\{apiBase\}/cookies/details`", "window.API.cookies.list()"

# 替换 fetch(`${apiBase}/keywords/${accountId}`) -> window.API.keywords.list(accountId)
$content = $content -replace "fetch\(`\$\{apiBase\}/keywords/\$\{accountId\}`", "window.API.keywords.list(accountId)"

# 替换 fetch(`${apiBase}/keywords/${account.id}`) -> window.API.keywords.list(account.id)
$content = $content -replace "fetch\(`\$\{apiBase\}/keywords/\$\{account\.id\}`", "window.API.keywords.list(account.id)"

# 替换 fetch(`${apiBase}/keywords-with-item-id/${accountId}`) -> window.API.keywords.listWithItemId(accountId)
$content = $content -replace "fetch\(`\$\{apiBase\}/keywords-with-item-id/\$\{accountId\}`", "window.API.keywords.listWithItemId(accountId)"

# 替换 fetch(`${apiBase}/keywords-with-item-id/${currentCookieId}`) POST -> window.API.keywords.create(...)
$content = $content -replace "fetch\(`\$\{apiBase\}/keywords-with-item-id/\$\{currentCookieId\}`,\s*\{\s*method:\s*'POST'", "window.API.keywords.create(currentCookieId"

# 替换 fetch(`${apiBase}/keywords/${cookieId}/${index}`) DELETE -> window.API.keywords.delete(cookieId, index)
$content = $content -replace "fetch\(`\$\{apiBase\}/keywords/\$\{cookieId\}/\$\{index\}`,\s*\{\s*method:\s*'DELETE'", "window.API.keywords.delete(cookieId, index)"

# 替换 fetch(`${apiBase}/items/${accountId}`) -> window.API.items.getByCookie(accountId)
$content = $content -replace "fetch\(`\$\{apiBase\}/items/\$\{accountId\}`", "window.API.items.getByCookie(accountId)"

# 替换 fetch(`${apiBase}/items/${currentCookieId}`) -> window.API.items.getByCookie(currentCookieId)
$content = $content -replace "fetch\(`\$\{apiBase\}/items/\$\{currentCookieId\}`", "window.API.items.getByCookie(currentCookieId)"

# 替换 fetch(`${apiBase}/keywords/${currentCookieId}/image`) -> window.API.keywords.addImage(currentCookieId, formData)
$content = $content -replace "fetch\(`\$\{apiBase\}/keywords/\$\{currentCookieId\}/image\`),\s*\{", "window.API.keywords.addImage(currentCookieId, formData)"

# 替换 window.App.showToast -> showToast
$content = $content -replace "window\.App\.showToast", "showToast"

# 替换 window.App.toggleLoading -> toggleLoading
$content = $content -replace "window\.App\.toggleLoading", "toggleLoading"

Set-Content -Path $file -Value $content -Force
Write-Host "keywords.js migration completed"