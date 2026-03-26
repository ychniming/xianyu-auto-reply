// Cookie管理模块 - 账号/Cookie相关函数
import { clearKeywordCache } from './utils.js';
import { refreshAccountList, loadAccountKeywords, updateAccountBadge } from './keywords.js';

// 加载Cookie列表
export async function loadCookies() {
    try {
        window.App.toggleLoading(true);
        const tbody = document.querySelector('#cookieTable tbody');
        tbody.innerHTML = '';

        const cookieDetails = await window.API.cookies.list();
        const cookiesArray = cookieDetails.data || cookieDetails;

        if (cookiesArray.length === 0) {
            renderEmptyCookiesState(tbody);
            return;
        }

        const accountsWithKeywords = await fetchAccountsWithDetails(cookiesArray);
        renderCookiesTable(tbody, accountsWithKeywords);
        setupCookieClickHandlers();
    } catch (err) {
    } finally {
        window.App.toggleLoading(false);
    }
}

function renderEmptyCookiesState(tbody) {
    tbody.innerHTML = `
    <tr>
        <td colspan="7" class="text-center py-4 text-muted empty-state">
        <i class="bi bi-inbox fs-1 d-block mb-3"></i>
        <h5>暂无账号</h5>
        <p class="mb-0">请添加新的闲鱼账号开始使用</p>
        </td>
    </tr>
    `;
}

async function fetchAccountsWithDetails(cookiesArray) {
    return Promise.all(
        cookiesArray.map(async (cookie) => {
            try {
                const keywordsData = await window.API.keywords.list(cookie.id);
                const keywordCount = Array.isArray(keywordsData) ? keywordsData.length : 0;
                const defaultReply = await getDefaultReply(cookie.id);
                const aiReply = await getAIReplySettings(cookie.id);

                return {
                    ...cookie,
                    keywordCount: keywordCount,
                    defaultReply: defaultReply,
                    aiReply: aiReply
                };
            } catch (error) {
                return {
                    ...cookie,
                    keywordCount: 0,
                    defaultReply: { enabled: false, reply_content: '' },
                    aiReply: { ai_enabled: false, model_name: 'qwen-plus' }
                };
            }
        })
    );
}

async function getDefaultReply(cookieId) {
    try {
        return await window.API.defaultReplies.get(cookieId) || { enabled: false, reply_content: '' };
    } catch (e) {
        console.warn(`获取账号 ${cookieId} 默认回复失败:`, e);
        return { enabled: false, reply_content: '' };
    }
}

async function getAIReplySettings(cookieId) {
    try {
        return await window.API.ai.getSettings(cookieId) || { ai_enabled: false, model_name: 'qwen-plus' };
    } catch (e) {
        console.warn(`获取账号 ${cookieId} AI回复设置失败:`, e);
        return { ai_enabled: false, model_name: 'qwen-plus' };
    }
}

function renderCookiesTable(tbody, accountsWithKeywords) {
    const fragment = document.createDocumentFragment();
    accountsWithKeywords.forEach(cookie => {
        const isEnabled = cookie.enabled === undefined ? true : cookie.enabled;
        const tr = createCookieRow(cookie, isEnabled);
        fragment.appendChild(tr);
    });
    tbody.appendChild(fragment);
}

function createCookieRow(cookie, isEnabled) {
    const tr = document.createElement('tr');
    tr.className = `account-row ${isEnabled ? 'enabled' : 'disabled'}`;

    const defaultReplyBadge = cookie.defaultReply.enabled ?
        '<span class="badge bg-success">启用</span>' :
        '<span class="badge bg-secondary">禁用</span>';

    const aiReplyBadge = cookie.aiReply.ai_enabled ?
        '<span class="badge bg-primary">AI启用</span>' :
        '<span class="badge bg-secondary">AI禁用</span>';

    const autoConfirm = cookie.auto_confirm === undefined ? true : cookie.auto_confirm;

    tr.innerHTML = `
    <td class="align-middle">
        <div class="cookie-id">
        <strong class="text-primary"></strong>
        </div>
    </td>
    <td class="align-middle">
        <div class="cookie-value" title="点击复制Cookie" style="font-family: monospace; font-size: 0.875rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer;">
        </div>
    </td>
    <td class="align-middle">
        <span class="badge">
        </span>
    </td>
    <td class="align-middle">
        <div class="d-flex align-items-center gap-2">
        <label class="status-toggle" title="${isEnabled ? '点击禁用' : '点击启用'}">
            <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="toggleAccountStatus('${cookie.id}', this.checked)">
            <span class="status-slider"></span>
        </label>
        <span class="status-badge ${isEnabled ? 'enabled' : 'disabled'}" title="${isEnabled ? '账号已启用' : '账号已禁用'}">
            <i class="bi bi-${isEnabled ? 'check-circle-fill' : 'x-circle-fill'}"></i>
        </span>
        </div>
    </td>
    <td class="align-middle">
        ${defaultReplyBadge}
    </td>
    <td class="align-middle">
        ${aiReplyBadge}
    </td>
    <td class="align-middle">
        <div class="d-flex align-items-center gap-2">
        <label class="status-toggle" title="${autoConfirm ? '点击关闭自动确认发货' : '点击开启自动确认发货'}">
            <input type="checkbox" ${autoConfirm ? 'checked' : ''} onchange="toggleAutoConfirm('${cookie.id}', this.checked)">
            <span class="status-slider"></span>
        </label>
        <span class="status-badge ${autoConfirm ? 'enabled' : 'disabled'}" title="${autoConfirm ? '自动确认发货已开启' : '自动确认发货已关闭'}">
            <i class="bi bi-${autoConfirm ? 'truck' : 'truck-flatbed'}"></i>
        </span>
        </div>
    </td>
    <td class="align-middle">
        <div class="btn-group" role="group">
        <button class="btn btn-sm btn-outline-primary" onclick="editCookieInline('${cookie.id}', '${cookie.value}')" title="修改Cookie" ${!isEnabled ? 'disabled' : ''}>
            <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-sm btn-outline-success" onclick="goToAutoReply('${cookie.id}')" title="${isEnabled ? '设置自动回复' : '配置关键词 (账号已禁用)'}">
            <i class="bi bi-arrow-right-circle"></i>
        </button>
        <button class="btn btn-sm btn-outline-warning" onclick="configAIReply('${cookie.id}')" title="配置AI回复" ${!isEnabled ? 'disabled' : ''}>
            <i class="bi bi-robot"></i>
        </button>
        <button class="btn btn-sm btn-outline-info" onclick="copyCookie('${cookie.id}', '${cookie.value}')" title="复制Cookie">
            <i class="bi bi-clipboard"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger" onclick="delCookie('${cookie.id}')" title="删除账号">
            <i class="bi bi-trash"></i>
        </button>
        </div>
    </td>
    `;

    tr.querySelector('.cookie-id strong').textContent = cookie.id;
    const cookieValueDiv = tr.querySelector('.cookie-value');
    cookieValueDiv.textContent = cookie.value || '未设置';
    const keywordBadge = tr.querySelector('.align-middle:nth-child(3) .badge');
    keywordBadge.textContent = `${cookie.keywordCount} 个关键词`;
    keywordBadge.className = `badge ${cookie.keywordCount > 0 ? 'bg-success' : 'bg-secondary'}`;

    return tr;
}

function setupCookieClickHandlers() {
    const tbody = document.querySelector('#cookieTable tbody');
    tbody.addEventListener('click', function(e) {
        const element = e.target.closest('.cookie-value');
        if (element) {
            const cookieValue = element.textContent;
            if (cookieValue && cookieValue !== '未设置') {
                navigator.clipboard.writeText(cookieValue).then(() => {
                    window.App.showToast('Cookie已复制到剪贴板', 'success');
                }).catch(() => {
                    window.App.showToast('复制失败，请手动复制', 'error');
                });
            }
        }
    });
}

// 复制Cookie
export function copyCookie(id, value) {
    if (!value || value === '未设置') {
    window.App.showToast('该账号暂无Cookie值', 'warning');
    return;
    }

    navigator.clipboard.writeText(value).then(() => {
    window.App.showToast(`账号 "${id}" 的Cookie已复制到剪贴板`, 'success');
    }).catch(() => {
    // 降级方案：创建临时文本框
    const textArea = document.createElement('textarea');
    textArea.value = value;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        window.App.showToast(`账号 "${id}" 的Cookie已复制到剪贴板`, 'success');
    } catch (err) {
        window.App.showToast('复制失败，请手动复制', 'error');
    }
    document.body.removeChild(textArea);
    });
}

// 删除Cookie
export async function delCookie(id) {
    if (!confirm(`确定要删除账号 "${id}" 吗？此操作不可恢复。`)) return;

    try {
        await window.API.cookies.delete(id);
        window.App.showToast(`账号 "${id}" 已删除`, 'success');
        loadCookies();
    } catch (err) {
        // 错误已在fetchJSON中处理
    }
}

// 内联编辑Cookie
export function editCookieInline(id, currentValue) {
    const row = event.target.closest('tr');
    const cookieValueCell = row.querySelector('.cookie-value');
    const originalContent = cookieValueCell.innerHTML;

    // 存储原始数据到全局变量，避免HTML注入问题
    window.editingCookieData = {
    id: id,
    originalContent: originalContent,
    originalValue: currentValue || ''
    };

    // 创建编辑界面容器
    const editContainer = document.createElement('div');
    editContainer.className = 'd-flex gap-2';

    // 创建输入框
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control form-control-sm';
    input.id = `edit-${id}`;
    input.value = currentValue || '';
    input.placeholder = '输入新的Cookie值';

    // 创建保存按钮
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-sm btn-success';
    saveBtn.title = '保存';
    saveBtn.innerHTML = '<i class="bi bi-check"></i>';
    saveBtn.onclick = () => saveCookieInline(id);

    // 创建取消按钮
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-sm btn-secondary';
    cancelBtn.title = '取消';
    cancelBtn.innerHTML = '<i class="bi bi-x"></i>';
    cancelBtn.onclick = () => cancelCookieEdit(id);

    // 组装编辑界面
    editContainer.appendChild(input);
    editContainer.appendChild(saveBtn);
    editContainer.appendChild(cancelBtn);

    // 替换原内容
    cookieValueCell.innerHTML = '';
    cookieValueCell.appendChild(editContainer);

    // 聚焦输入框
    input.focus();
    input.select();

    // 添加键盘事件监听
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
        e.preventDefault();
        saveCookieInline(id);
        } else if (e.key === 'Escape') {
        e.preventDefault();
        cancelCookieEdit(id);
        }
    });

    // 禁用该行的其他按钮
    const actionButtons = row.querySelectorAll('.btn-group button');
    actionButtons.forEach(btn => btn.disabled = true);
}

// 保存内联编辑的Cookie
export async function saveCookieInline(id) {
    const input = document.getElementById(`edit-${id}`);
    const newValue = input.value.trim();

    if (!newValue) {
    window.App.showToast('Cookie值不能为空', 'warning');
    return;
    }

    try {
    window.App.toggleLoading(true);

    await window.API.cookies.update(id, {
        id: id,
        value: newValue
    });

    window.App.showToast(`账号 "${id}" Cookie已更新`, 'success');
    loadCookies(); // 重新加载列表

    } catch (err) {
    console.error('Cookie更新失败:', err);
    window.App.showToast(`Cookie更新失败: ${err.message || '未知错误'}`, 'danger');
    // 恢复原内容
    cancelCookieEdit(id);
    } finally {
    window.App.toggleLoading(false);
    }
}

// 取消Cookie编辑
export function cancelCookieEdit(id) {
    if (!window.editingCookieData || window.editingCookieData.id !== id) {
    console.error('编辑数据不存在');
    return;
    }

    const row = document.querySelector(`#edit-${id}`).closest('tr');
    const cookieValueCell = row.querySelector('.cookie-value');

    // 恢复原内容
    cookieValueCell.innerHTML = window.editingCookieData.originalContent;

    // 恢复按钮状态
    const actionButtons = row.querySelectorAll('.btn-group button');
    actionButtons.forEach(btn => btn.disabled = false);

    // 清理全局数据
    delete window.editingCookieData;
}

// 切换账号启用/禁用状态
export async function toggleAccountStatus(accountId, enabled) {
    try {
        window.App.toggleLoading(true);

        // 这里需要调用后端API来更新账号状态
        // 由于当前后端可能没有enabled字段，我们先在前端模拟
        // 实际项目中需要后端支持

        await window.API.cookies.toggleStatus(accountId, enabled);
        window.App.showToast(`账号 "${accountId}" 已${enabled ? '启用' : '禁用'}`, 'success');

        // 清除相关缓存，确保数据一致性
        clearKeywordCache();

        // 更新界面显示
        updateAccountRowStatus(accountId, enabled);

        // 刷新自动回复页面的账号列表
        refreshAccountList();

        // 如果禁用的账号在自动回复页面被选中，更新显示
        const accountSelect = document.getElementById('accountSelect');
        if (accountSelect && accountSelect.value === accountId) {
            if (!enabled) {
                updateAccountBadge(accountId, false);
                window.App.showToast('账号已禁用，配置的关键词不会参与自动回复', 'warning');
            } else {
                updateAccountBadge(accountId, true);
                window.App.showToast('账号已启用，配置的关键词将参与自动回复', 'success');
            }
        }

    } catch (error) {
        // 如果后端不支持，先在前端模拟
        console.warn('切换账号状态失败，使用前端模拟:', error);
        window.App.showToast(`账号 "${accountId}" 已${enabled ? '启用' : '禁用'} (本地模拟)`, enabled ? 'success' : 'warning');
        updateAccountRowStatus(accountId, enabled);

        // 恢复切换按钮状态
        const toggle = document.querySelector(`input[onchange*="${accountId}"]`);
        if (toggle) {
            toggle.checked = enabled;
        }
    } finally {
        window.App.toggleLoading(false);
    }
}

// 更新账号行的状态显示
export function updateAccountRowStatus(accountId, enabled) {
    const toggle = document.querySelector(`input[onchange*="${accountId}"]`);
    if (!toggle) return;

    const row = toggle.closest('tr');
    const statusBadge = row.querySelector('.status-badge');
    const actionButtons = row.querySelectorAll('.btn-group .btn:not(.btn-outline-info):not(.btn-outline-danger)');

    // 更新行样式
    row.className = `account-row ${enabled ? 'enabled' : 'disabled'}`;

    // 更新状态徽章
    statusBadge.className = `status-badge ${enabled ? 'enabled' : 'disabled'}`;
    statusBadge.title = enabled ? '账号已启用' : '账号已禁用';
    statusBadge.innerHTML = `
    <i class="bi bi-${enabled ? 'check-circle-fill' : 'x-circle-fill'}"></i>
    `;

    // 更新按钮状态（只禁用编辑Cookie按钮，其他按钮保持可用）
    actionButtons.forEach(btn => {
    if (btn.onclick && btn.onclick.toString().includes('editCookieInline')) {
        btn.disabled = !enabled;
    }
    // 设置自动回复按钮始终可用，但更新提示文本
    if (btn.onclick && btn.onclick.toString().includes('goToAutoReply')) {
        btn.title = enabled ? '设置自动回复' : '配置关键词 (账号已禁用)';
    }
    });

    // 更新切换按钮的提示
    const label = toggle.closest('.status-toggle');
    label.title = enabled ? '点击禁用' : '点击启用';
}

// 切换自动确认发货状态
export async function toggleAutoConfirm(accountId, enabled) {
    try {
        window.App.toggleLoading(true);

        const result = await window.API.cookies.toggleAutoConfirm(accountId, enabled);
        window.App.showToast(result.message || `账号 "${accountId}" 自动确认发货已${enabled ? '开启' : '关闭'}`, 'success');

        // 更新界面显示
        updateAutoConfirmRowStatus(accountId, enabled);

    } catch (error) {
        console.error('切换自动确认发货状态失败:', error);
        window.App.showToast('更新自动确认发货设置失败', 'error');

        // 恢复切换按钮状态
        const toggle = document.querySelector(`input[onchange*="toggleAutoConfirm('${accountId}'"]`);
        if (toggle) {
            toggle.checked = !enabled;
        }
    } finally {
        window.App.toggleLoading(false);
    }
}

// 更新自动确认发货行状态
export function updateAutoConfirmRowStatus(accountId, enabled) {
    const row = document.querySelector(`tr:has(input[onchange*="toggleAutoConfirm('${accountId}'"])`);
    if (!row) return;

    const statusBadge = row.querySelector('.status-badge:has(i.bi-truck, i.bi-truck-flatbed)');
    const toggle = row.querySelector(`input[onchange*="toggleAutoConfirm('${accountId}'"]`);

    if (statusBadge && toggle) {
    // 更新状态徽章
    statusBadge.className = `status-badge ${enabled ? 'enabled' : 'disabled'}`;
    statusBadge.title = enabled ? '自动确认发货已开启' : '自动确认发货已关闭';
    statusBadge.innerHTML = `
        <i class="bi bi-${enabled ? 'truck' : 'truck-flatbed'}"></i>
    `;

    // 更新切换按钮的提示
    const label = toggle.closest('.status-toggle');
    label.title = enabled ? '点击关闭自动确认发货' : '点击开启自动确认发货';
    }
}

// 跳转到自动回复页面并选择指定账号
export function goToAutoReply(accountId) {
    // 切换到自动回复页面
    showSection('auto-reply');

    // 设置账号选择器的值
    setTimeout(() => {
    const accountSelect = document.getElementById('accountSelect');
    if (accountSelect) {
        accountSelect.value = accountId;
        // 触发change事件来加载关键词
        loadAccountKeywords();
    }
    }, 100);

    window.App.showToast(`已切换到自动回复页面，账号 "${accountId}" 已选中`, 'info');
}

