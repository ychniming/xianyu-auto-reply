// 关键词管理模块 - 关键词管理相关函数
import { apiBase, authToken, keywordsData, currentCookieId, clearKeywordCache } from './utils.js';
import { showToast, toggleLoading, fetchJSON } from './api.js';

// XSS防护：HTML转义函数
function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const str = String(text);
    const htmlEntities = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    };
    return str.replace(/[&<>"'/]/g, char => htmlEntities[char]);
}

// 获取账号关键词数量（带缓存）
export async function getAccountKeywordCount(accountId) {
    const now = Date.now();

    // 检查缓存
    if (window.accountKeywordCache && window.accountKeywordCache[accountId] && (now - window.cacheTimestamp) < window.CACHE_DURATION) {
        return window.accountKeywordCache[accountId];
    }

    try {
        const response = await fetch(`${apiBase}/keywords/${accountId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const keywordsData = await response.json();
            const count = keywordsData.length;

            // 更新缓存
            if (!window.accountKeywordCache) {
                window.accountKeywordCache = {};
            }
            window.accountKeywordCache[accountId] = count;
            window.cacheTimestamp = now;

            return count;
        } else {
            return 0;
        }
    } catch (error) {
        console.error(`获取账号 ${accountId} 关键词失败:`, error);
        return 0;
    }
}

// 刷新账号列表（用于自动回复页面）
export async function refreshAccountList() {
    try {
        toggleLoading(true);

        // 获取账号列表
        const response = await fetch(`${apiBase}/cookies/details`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const accounts = await response.json();
            const select = document.getElementById('accountSelect');
            select.innerHTML = '<option value="">🔍 请选择一个账号开始配置...</option>';

            // 为每个账号获取关键词数量
            const accountsWithKeywords = await Promise.all(
                accounts.map(async (account) => {
                    try {
                        const keywordsResponse = await fetch(`${apiBase}/keywords/${account.id}`, {
                            headers: {
                                'Authorization': `Bearer ${authToken}`
                            }
                        });

                        if (keywordsResponse.ok) {
                            const keywordsData = await keywordsResponse.json();
                            return {
                                ...account,
                                keywords: keywordsData,
                                keywordCount: keywordsData.length
                            };
                        } else {
                            return {
                                ...account,
                                keywordCount: 0
                            };
                        }
                    } catch (error) {
                        console.error(`获取账号 ${account.id} 关键词失败:`, error);
                        return {
                            ...account,
                            keywordCount: 0
                        };
                    }
                })
            );

            // 渲染账号选项（显示所有账号，但标识禁用状态）
            if (accountsWithKeywords.length === 0) {
                select.innerHTML = '<option value="">❌ 暂无账号，请先添加账号</option>';
                return;
            }

            // 分组显示：先显示启用的账号，再显示禁用的账号
            const enabledAccounts = accountsWithKeywords.filter(account => {
                const enabled = account.enabled === undefined ? true : account.enabled;
                return enabled;
            });
            const disabledAccounts = accountsWithKeywords.filter(account => {
                const enabled = account.enabled === undefined ? true : account.enabled;
                return !enabled;
            });

            // 渲染启用的账号
            enabledAccounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;

                // 根据关键词数量显示不同的图标和样式
                let icon = '📝';
                let status = '';
                if (account.keywordCount === 0) {
                    icon = '⚪';
                    status = ' (未配置)';
                } else if (account.keywordCount >= 5) {
                    icon = '🟢';
                    status = ` (${account.keywordCount} 个关键词)`;
                } else {
                    icon = '🟡';
                    status = ` (${account.keywordCount} 个关键词)`;
                }

                option.textContent = `${icon} ${account.id}${status}`;
                select.appendChild(option);
            });

            // 如果有禁用的账号，添加分隔线和禁用账号
            if (disabledAccounts.length > 0) {
                const separatorOption = document.createElement('option');
                separatorOption.disabled = true;
                separatorOption.textContent = `--- 禁用账号 (${disabledAccounts.length} 个) ---`;
                select.appendChild(separatorOption);

                // 渲染禁用的账号
                disabledAccounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;

                    let icon = '🔴';
                    let status = '';
                    if (account.keywordCount === 0) {
                        status = ' (未配置) [已禁用]';
                    } else {
                        status = ` (${account.keywordCount} 个关键词) [已禁用]`;
                    }

                    option.textContent = `${icon} ${account.id}${status}`;
                    option.style.color = '#6b7280';
                    option.style.fontStyle = 'italic';
                    select.appendChild(option);
                });
            }
        } else {
            showToast('获取账号列表失败', 'danger');
        }
    } catch (error) {
        console.error('刷新账号列表失败:', error);
        showToast('刷新账号列表失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 加载账号关键词
export async function loadAccountKeywords() {
    const accountId = document.getElementById('accountSelect').value;
    const keywordManagement = document.getElementById('keywordManagement');

    if (!accountId) {
        keywordManagement.style.display = 'none';
        return;
    }

    try {
        toggleLoading(true);
        currentCookieId = accountId;

        // 获取账号详情以检查状态
        const accountResponse = await fetch(`${apiBase}/cookies/details`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        let accountStatus = true;
        if (accountResponse.ok) {
            const accounts = await accountResponse.json();
            const currentAccount = accounts.find(acc => acc.id === accountId);
            accountStatus = currentAccount ? (currentAccount.enabled === undefined ? true : currentAccount.enabled) : true;
        }

        const response = await fetch(`${apiBase}/keywords-with-item-id/${accountId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const formattedData = data;
            keywordsData[accountId] = formattedData;
            renderKeywordsList(formattedData);

            // 加载商品列表
            await loadItemsList(accountId);

            // 更新账号徽章显示
            updateAccountBadge(accountId, accountStatus);

            keywordManagement.style.display = 'block';
        } else {
            showToast('加载关键词失败', 'danger');
        }
    } catch (error) {
        console.error('加载关键词失败:', error);
        showToast('加载关键词失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 加载商品列表
export async function loadItemsList(accountId) {
    try {
        const response = await fetch(`${apiBase}/items/${accountId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const items = data.items || [];

            // 更新商品选择下拉框
            const selectElement = document.getElementById('newItemIdSelect');
            if (selectElement) {
                selectElement.innerHTML = '<option value="">选择商品或留空表示通用关键词</option>';

                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.item_id;
                    option.textContent = `${item.item_id} - ${item.item_title}`;
                    selectElement.appendChild(option);
                });
            }
        } else {
            console.warn('加载商品列表失败:', response.status);
        }
    } catch (error) {
        console.error('加载商品列表时发生错误:', error);
    }
}

// 更新账号徽章显示
export function updateAccountBadge(accountId, isEnabled) {
    const badge = document.getElementById('currentAccountBadge');
    if (!badge) return;

    const statusIcon = isEnabled ? '🟢' : '🔴';
    const statusText = isEnabled ? '启用' : '禁用';
    const statusClass = isEnabled ? 'bg-success' : 'bg-warning';

    badge.innerHTML = `
        <span class="badge ${statusClass} me-2">
            ${statusIcon} ${accountId}
        </span>
        <small class="text-muted">
            状态: ${statusText}
            ${!isEnabled ? ' (配置的关键词不会参与自动回复)' : ''}
        </small>
    `;
}

// 显示添加关键词表单
export function showAddKeywordForm() {
    const form = document.getElementById('addKeywordForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';

    if (form.style.display === 'block') {
        document.getElementById('newKeyword').focus();
    }
}

// 匹配类型中文映射
const MATCH_TYPE_NAMES = {
    'contains': '包含匹配',
    'exact': '精确匹配',
    'prefix': '前缀匹配',
    'suffix': '后缀匹配',
    'regex': '正则表达式',
    'fuzzy': '模糊匹配'
};

// 回复模式中文映射
const REPLY_MODE_NAMES = {
    'single': '单条回复',
    'random': '随机回复',
    'sequence': '顺序回复'
};

// 切换多回复字段显示
export function toggleMultiReplyField() {
    const replyMode = document.getElementById('newReplyMode').value;
    const multiReplyField = document.getElementById('multiReplyField');
    const replyInput = document.getElementById('newReply');
    
    if (replyMode === 'random' || replyMode === 'sequence') {
        multiReplyField.style.display = 'block';
        replyInput.placeholder = '单条回复内容（如使用多回复，请填写下方文本框）';
    } else {
        multiReplyField.style.display = 'none';
        replyInput.placeholder = '例如：您好，欢迎咨询！有什么可以帮助您的吗？';
    }
}

// 切换高级条件面板展开/折叠
export function toggleAdvancedConditions() {
    const body = document.getElementById('advancedConditionsBody');
    const icon = document.getElementById('advancedConditionsIcon');
    
    if (body.style.display === 'none') {
        body.style.display = 'block';
        icon.classList.remove('bi-chevron-down');
        icon.classList.add('bi-chevron-up');
    } else {
        body.style.display = 'none';
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
    }
}

// 收集高级条件数据
export function collectAdvancedConditions() {
    const timeStartHour = document.getElementById('timeStartHour').value.trim();
    const timeEndHour = document.getElementById('timeEndHour').value.trim();
    const excludeKeywords = document.getElementById('excludeKeywords').value.trim();
    const maxTriggerCount = document.getElementById('maxTriggerCount').value.trim();
    const userType = document.getElementById('userType').value;
    
    const conditions = [];
    
    // 时间范围条件
    if (timeStartHour !== '' && timeEndHour !== '') {
        const start = parseInt(timeStartHour);
        const end = parseInt(timeEndHour);
        if (start >= 0 && start <= 23 && end >= 0 && end <= 23) {
            conditions.push({
                type: 'time',
                field: 'hour',
                operator: 'between',
                value: [start, end]
            });
        }
    }
    
    // 排除关键词条件
    if (excludeKeywords) {
        const keywords = excludeKeywords.split(',').map(k => k.trim()).filter(k => k);
        if (keywords.length > 0) {
            conditions.push({
                type: 'keyword',
                field: 'exclude',
                operator: 'contains',
                value: keywords
            });
        }
    }
    
    // 触发次数限制
    if (maxTriggerCount !== '') {
        const count = parseInt(maxTriggerCount);
        if (count > 0) {
            conditions.push({
                type: 'trigger',
                field: 'count',
                operator: 'lte',
                value: count
            });
        }
    }
    
    // 用户类型条件
    if (userType !== 'all') {
        conditions.push({
            type: 'user',
            field: 'is_new',
            operator: 'eq',
            value: userType === 'new'
        });
    }
    
    // 如果有条件,返回完整的conditions对象
    if (conditions.length > 0) {
        return {
            logic: 'and',
            conditions: conditions
        };
    }
    
    return null;
}

// 清空高级条件输入
export function clearAdvancedConditions() {
    document.getElementById('timeStartHour').value = '';
    document.getElementById('timeEndHour').value = '';
    document.getElementById('excludeKeywords').value = '';
    document.getElementById('maxTriggerCount').value = '';
    document.getElementById('userType').value = 'all';
}

// 回显高级条件数据
export function fillAdvancedConditions(conditionsData) {
    if (!conditionsData || !conditionsData.conditions) {
        return;
    }
    
    conditionsData.conditions.forEach(condition => {
        switch (condition.type) {
            case 'time':
                if (condition.field === 'hour' && condition.operator === 'between') {
                    document.getElementById('timeStartHour').value = condition.value[0];
                    document.getElementById('timeEndHour').value = condition.value[1];
                }
                break;
            case 'keyword':
                if (condition.field === 'exclude' && condition.operator === 'contains') {
                    document.getElementById('excludeKeywords').value = condition.value.join(', ');
                }
                break;
            case 'trigger':
                if (condition.field === 'count' && condition.operator === 'lte') {
                    document.getElementById('maxTriggerCount').value = condition.value;
                }
                break;
            case 'user':
                if (condition.field === 'is_new' && condition.operator === 'eq') {
                    document.getElementById('userType').value = condition.value ? 'new' : 'old';
                }
                break;
        }
    });
    
    // 展开高级条件面板
    const body = document.getElementById('advancedConditionsBody');
    const icon = document.getElementById('advancedConditionsIcon');
    body.style.display = 'block';
    icon.classList.remove('bi-chevron-down');
    icon.classList.add('bi-chevron-up');
}

// 添加或更新关键词
export async function addKeyword() {
    const keyword = document.getElementById('newKeyword').value.trim();
    const reply = document.getElementById('newReply').value.trim();
    const itemId = document.getElementById('newItemIdSelect').value.trim();
    const matchType = document.getElementById('newMatchType').value;
    const priority = parseInt(document.getElementById('newPriority').value) || 50;
    const replyMode = document.getElementById('newReplyMode').value;
    const multiReplies = document.getElementById('newMultiReplies').value.trim();

    if (!keyword) {
        showToast('请填写关键词', 'warning');
        return;
    }

    // 验证回复内容
    let replies = [];
    if (replyMode === 'single') {
        if (!reply) {
            showToast('请填写回复内容', 'warning');
            return;
        }
        replies = [reply];
    } else {
        // 多回复模式
        if (!multiReplies) {
            showToast('请填写多回复配置（每行一条）', 'warning');
            return;
        }
        replies = multiReplies.split('\n').map(r => r.trim()).filter(r => r);
        if (replies.length === 0) {
            showToast('请至少填写一条回复内容', 'warning');
            return;
        }
    }

    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    // 验证优先级范围
    if (priority < 0 || priority > 100) {
        showToast('优先级必须在 0-100 之间', 'warning');
        return;
    }

    // 检查是否为编辑模式
    const isEditMode = typeof window.editingIndex !== 'undefined';
    const actionText = isEditMode ? '更新' : '添加';

    try {
        toggleLoading(true);

        // 获取当前关键词列表
        let currentKeywords = [...(keywordsData[currentCookieId] || [])];

        // 准备要保存的关键词列表
        let keywordsToSave = [...currentKeywords];

        // 如果是编辑模式，先移除原关键词
        if (isEditMode && typeof window.editingIndex !== 'undefined') {
            keywordsToSave.splice(window.editingIndex, 1);
        }

        // 检查关键词是否已存在（考虑商品ID）
        const existingKeyword = keywordsToSave.find(item =>
            item.keyword === keyword &&
            (item.item_id || '') === (itemId || '')
        );
        if (existingKeyword) {
            const itemIdText = itemId ? `（商品ID: ${itemId}）` : '（通用关键词）';
            showToast(`关键词 "${keyword}" ${itemIdText} 已存在，请使用其他关键词或商品ID`, 'warning');
            toggleLoading(false);
            return;
        }

        // 收集高级条件数据
        const advancedConditions = collectAdvancedConditions();
        
        // 添加新关键词或更新的关键词
        const newKeyword = {
            keyword: keyword,
            reply: replyMode === 'single' ? reply : replies[0],
            item_id: itemId || '',
            match_type: matchType,
            priority: priority,
            reply_mode: replyMode,
            // 将 replies 数组转换为 JSON 字符串，与后端格式匹配
            replies: (replyMode !== 'single' && replies.length > 1) ? JSON.stringify(replies) : null,
            // 添加高级条件
            conditions: advancedConditions
        };
        keywordsToSave.push(newKeyword);

        const response = await fetch(`${apiBase}/keywords-with-item-id/${currentCookieId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                keywords: keywordsToSave
            })
        });

        if (response.ok) {
            showToast(`✨ 关键词 "${keyword}" ${actionText}成功！`, 'success');

            // 清空输入框并重置样式
            const keywordInput = document.getElementById('newKeyword');
            const replyInput = document.getElementById('newReply');
            const selectElement = document.getElementById('newItemIdSelect');
            const matchTypeSelect = document.getElementById('newMatchType');
            const priorityInput = document.getElementById('newPriority');
            const replyModeSelect = document.getElementById('newReplyMode');
            const multiRepliesInput = document.getElementById('newMultiReplies');
            const addBtn = document.querySelector('.add-btn');

            keywordInput.value = '';
            replyInput.value = '';
            if (selectElement) selectElement.value = '';
            if (matchTypeSelect) matchTypeSelect.value = 'contains';
            if (priorityInput) priorityInput.value = '50';
            if (replyModeSelect) replyModeSelect.value = 'single';
            if (multiRepliesInput) multiRepliesInput.value = '';
            
            // 隐藏多回复字段
            document.getElementById('multiReplyField').style.display = 'none';
            
            // 清空高级条件
            clearAdvancedConditions();
            
            keywordInput.style.borderColor = '#e5e7eb';
            replyInput.style.borderColor = '#e5e7eb';
            addBtn.style.opacity = '0.7';
            addBtn.style.transform = 'scale(0.95)';

            // 如果是编辑模式，重置编辑状态
            if (isEditMode) {
                delete window.editingIndex;
                delete window.originalKeyword;

                // 恢复添加按钮
                addBtn.innerHTML = '<i class="bi bi-plus-lg"></i>添加';
                addBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';

                // 移除取消按钮
                const cancelBtn = document.getElementById('cancelEditBtn');
                if (cancelBtn) {
                    cancelBtn.remove();
                }
            }

            // 聚焦到关键词输入框，方便连续添加
            setTimeout(() => {
                keywordInput.focus();
            }, 100);

            loadAccountKeywords(); // 重新加载关键词列表
            clearKeywordCache(); // 清除缓存
        } else {
            const errorText = await response.text();
            console.error('关键词添加失败:', errorText);
            showToast('关键词添加失败', 'danger');
        }
    } catch (error) {
        console.error('添加关键词失败:', error);
        showToast('添加关键词失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 渲染现代化关键词列表
export function renderKeywordsList(keywords) {
    const container = document.getElementById('keywordsList');

    if (!container) {
        return;
    }

    container.innerHTML = '';

    if (!keywords || keywords.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
            <i class="bi bi-chat-dots"></i>
            <h3>还没有关键词</h3>
            <p>添加第一个关键词，让您的闲鱼店铺自动回复客户消息</p>
            <button class="quick-add-btn" onclick="focusKeywordInput()">
                <i class="bi bi-plus-lg me-2"></i>立即添加
            </button>
            </div>
        `;
        return;
    }

    keywords.forEach((item, index) => {
        const keywordItem = document.createElement('div');
        keywordItem.className = 'keyword-item';

        // 判断关键词类型
        const keywordType = item.type || 'text';
        const isImageType = keywordType === 'image';

        // 类型标识
        const typeBadge = isImageType ?
            '<span class="keyword-type-badge keyword-type-image"><i class="bi bi-image"></i> 图片</span>' :
            '<span class="keyword-type-badge keyword-type-text"><i class="bi bi-chat-text"></i> 文本</span>';

        // 匹配类型标签
        const matchType = item.match_type || 'contains';
        const matchTypeName = MATCH_TYPE_NAMES[matchType] || '包含匹配';
        const matchTypeBadge = `<span class="keyword-match-type-badge match-type-${escapeHtml(matchType)}">${escapeHtml(matchTypeName)}</span>`;

        // 优先级标签
        const priority = item.priority !== undefined ? item.priority : 50;
        const priorityClass = priority >= 80 ? 'priority-high' : (priority >= 50 ? 'priority-medium' : 'priority-low');
        const priorityBadge = `<span class="keyword-priority-badge ${priorityClass}">优先级: ${escapeHtml(priority)}</span>`;

        // 回复模式标签
        const replyMode = item.reply_mode || 'single';
        const replyModeName = REPLY_MODE_NAMES[replyMode] || '单条回复';
        const replyModeBadge = replyMode !== 'single' ? 
            `<span class="keyword-reply-mode-badge reply-mode-${escapeHtml(replyMode)}">${escapeHtml(replyModeName)}</span>` : '';

        // 触发次数
        const triggerCount = item.trigger_count || 0;
        const triggerCountBadge = triggerCount > 0 ? 
            `<span class="keyword-trigger-badge"><i class="bi bi-lightning"></i> ${escapeHtml(triggerCount)}次</span>` : '';

        // 高级条件显示
        let conditionsDisplay = '';
        if (item.conditions && item.conditions.conditions && item.conditions.conditions.length > 0) {
            const conditionBadges = [];
            item.conditions.conditions.forEach(condition => {
                switch (condition.type) {
                    case 'time':
                        if (condition.field === 'hour' && condition.operator === 'between') {
                            conditionBadges.push(`<span class="condition-badge condition-time"><i class="bi bi-clock"></i> ${escapeHtml(condition.value[0])}:00-${escapeHtml(condition.value[1])}:00</span>`);
                        }
                        break;
                    case 'keyword':
                        if (condition.field === 'exclude' && condition.operator === 'contains') {
                            const excludeText = condition.value.slice(0, 2).join(', ') + (condition.value.length > 2 ? '...' : '');
                            conditionBadges.push(`<span class="condition-badge condition-exclude"><i class="bi bi-x-circle"></i> 排除: ${escapeHtml(excludeText)}</span>`);
                        }
                        break;
                    case 'trigger':
                        if (condition.field === 'count' && condition.operator === 'lte') {
                            conditionBadges.push(`<span class="condition-badge condition-limit"><i class="bi bi-hash"></i> 最多${escapeHtml(condition.value)}次</span>`);
                        }
                        break;
                    case 'user':
                        if (condition.field === 'is_new' && condition.operator === 'eq') {
                            const userTypeText = condition.value ? '仅新用户' : '仅老用户';
                            conditionBadges.push(`<span class="condition-badge condition-user"><i class="bi bi-people"></i> ${escapeHtml(userTypeText)}</span>`);
                        }
                        break;
                }
            });
            if (conditionBadges.length > 0) {
                conditionsDisplay = `<div class="keyword-conditions">${conditionBadges.join('')}</div>`;
            }
        }

        // 商品ID显示（转义）
        const itemIdDisplay = item.item_id ?
            `<small class="text-muted d-block"><i class="bi bi-box"></i> 商品ID: ${escapeHtml(item.item_id)}</small>` :
            '<small class="text-muted d-block"><i class="bi bi-globe"></i> 通用关键词</small>';

        // 内容显示
        let contentDisplay = '';
        if (isImageType) {
            const imageUrl = item.reply || item.image_url || '';
            contentDisplay = imageUrl ?
                `<div class="d-flex align-items-center gap-3">
                    <img src="${escapeHtml(imageUrl)}" alt="关键词图片" class="keyword-image-preview" onclick="showImageModal('${escapeHtml(imageUrl)}')">
                    <div class="flex-grow-1">
                        <p class="reply-text mb-0">用户发送关键词时将回复此图片</p>
                        <small class="text-muted">点击图片查看大图</small>
                    </div>
                </div>` :
                '<p class="reply-text text-muted">图片加载失败</p>';
        } else {
            // 多回复显示（转义每条回复）
            const replies = item.replies || [item.reply];
            if (replyMode !== 'single' && replies.length > 1) {
                contentDisplay = `
                    <div class="multi-replies-container">
                        <div class="multi-replies-header">
                            <i class="bi bi-chat-square-text"></i>
                            <span>共 ${escapeHtml(replies.length)} 条回复（${escapeHtml(replyModeName)}）</span>
                        </div>
                        <div class="multi-replies-list">
                            ${replies.map((r, i) => `<div class="multi-reply-item"><span class="reply-index">${escapeHtml(i + 1)}</span>${escapeHtml(r)}</div>`).join('')}
                        </div>
                    </div>
                `;
            } else {
                contentDisplay = `<p class="reply-text">${escapeHtml(item.reply || '')}</p>`;
            }
        }

        keywordItem.innerHTML = `
            <div class="keyword-item-header">
            <div class="keyword-tag">
                <i class="bi bi-tag-fill"></i>
                ${escapeHtml(item.keyword)}
                ${typeBadge}
            </div>
            <div class="keyword-actions">
                <button class="action-btn edit-btn ${isImageType ? 'edit-btn-disabled' : ''}" onclick="${isImageType ? 'editImageKeyword' : 'editKeyword'}(${escapeHtml(index)})" title="${isImageType ? '图片关键词不支持编辑' : '编辑'}">
                <i class="bi bi-pencil"></i>
                </button>
                <button class="action-btn delete-btn" onclick="deleteKeyword('${escapeHtml(currentCookieId)}', ${escapeHtml(index)})" title="删除">
                <i class="bi bi-trash"></i>
                </button>
            </div>
            </div>
            <div class="keyword-meta-info">
                ${itemIdDisplay}
                <div class="keyword-badges">
                    ${matchTypeBadge}
                    ${priorityBadge}
                    ${replyModeBadge}
                    ${triggerCountBadge}
                </div>
                ${conditionsDisplay}
            </div>
            <div class="keyword-content">
            ${contentDisplay}
            </div>
        `;
        container.appendChild(keywordItem);
    });
}

// 聚焦到关键词输入框
export function focusKeywordInput() {
    document.getElementById('newKeyword').focus();
}

// 编辑关键词
export function editKeyword(index) {
    const keywords = keywordsData[currentCookieId] || [];
    const keyword = keywords[index];

    if (!keyword) {
        showToast('关键词不存在', 'warning');
        return;
    }

    // 将关键词信息填入输入框
    document.getElementById('newKeyword').value = keyword.keyword;
    document.getElementById('newReply').value = keyword.reply || '';
    
    // 设置商品ID选择框
    const selectElement = document.getElementById('newItemIdSelect');
    if (selectElement) {
        selectElement.value = keyword.item_id || '';
    }
    
    // 设置匹配类型
    const matchTypeSelect = document.getElementById('newMatchType');
    if (matchTypeSelect) {
        matchTypeSelect.value = keyword.match_type || 'contains';
    }
    
    // 设置优先级
    const priorityInput = document.getElementById('newPriority');
    if (priorityInput) {
        priorityInput.value = keyword.priority !== undefined ? keyword.priority : 50;
    }
    
    // 设置回复模式
    const replyModeSelect = document.getElementById('newReplyMode');
    if (replyModeSelect) {
        replyModeSelect.value = keyword.reply_mode || 'single';
    }
    
    // 设置多回复内容
    const multiRepliesInput = document.getElementById('newMultiReplies');
    if (multiRepliesInput && keyword.replies && keyword.replies.length > 1) {
        multiRepliesInput.value = keyword.replies.join('\n');
    }
    
    // 触发多回复字段显示切换
    toggleMultiReplyField();
    
    // 回显高级条件数据
    if (keyword.conditions) {
        fillAdvancedConditions(keyword.conditions);
    }

    // 设置编辑模式标识
    window.editingIndex = index;
    window.originalKeyword = keyword.keyword;
    window.originalItemId = keyword.item_id || '';

    // 更新按钮文本和样式
    const addBtn = document.querySelector('.add-btn');
    addBtn.innerHTML = '<i class="bi bi-check-lg"></i>更新';
    addBtn.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';

    // 显示取消按钮
    showCancelEditButton();

    // 聚焦到关键词输入框并选中文本
    setTimeout(() => {
        const keywordInput = document.getElementById('newKeyword');
        keywordInput.focus();
        keywordInput.select();
    }, 100);

    showToast('📝 编辑模式：修改后点击"更新"按钮保存', 'info');
}

// 显示取消编辑按钮
export function showCancelEditButton() {
    // 检查是否已存在取消按钮
    if (document.getElementById('cancelEditBtn')) {
        return;
    }

    const addBtn = document.querySelector('.add-btn');
    const cancelBtn = document.createElement('button');
    cancelBtn.id = 'cancelEditBtn';
    cancelBtn.className = 'btn btn-outline-secondary';
    cancelBtn.style.marginLeft = '0.5rem';
    cancelBtn.innerHTML = '<i class="bi bi-x-lg"></i>取消';
    cancelBtn.onclick = cancelEdit;

    addBtn.parentNode.appendChild(cancelBtn);
}

// 取消编辑
export function cancelEdit() {
    // 清空输入框
    document.getElementById('newKeyword').value = '';
    document.getElementById('newReply').value = '';

    // 清空商品ID选择框
    const selectElement = document.getElementById('newItemIdSelect');
    if (selectElement) {
        selectElement.value = '';
    }
    
    // 重置匹配类型
    const matchTypeSelect = document.getElementById('newMatchType');
    if (matchTypeSelect) {
        matchTypeSelect.value = 'contains';
    }
    
    // 重置优先级
    const priorityInput = document.getElementById('newPriority');
    if (priorityInput) {
        priorityInput.value = '50';
    }
    
    // 重置回复模式
    const replyModeSelect = document.getElementById('newReplyMode');
    if (replyModeSelect) {
        replyModeSelect.value = 'single';
    }
    
    // 清空多回复内容
    const multiRepliesInput = document.getElementById('newMultiReplies');
    if (multiRepliesInput) {
        multiRepliesInput.value = '';
    }
    
    // 隐藏多回复字段
    document.getElementById('multiReplyField').style.display = 'none';

    // 清空高级条件
    clearAdvancedConditions();

    // 重置编辑状态
    delete window.editingIndex;
    delete window.originalKeyword;
    delete window.originalItemId;

    // 恢复添加按钮
    const addBtn = document.querySelector('.add-btn');
    addBtn.innerHTML = '<i class="bi bi-plus-lg"></i>添加';
    addBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';

    // 移除取消按钮
    const cancelBtn = document.getElementById('cancelEditBtn');
    if (cancelBtn) {
        cancelBtn.remove();
    }

    showToast('已取消编辑', 'info');
}

// 删除关键词
export async function deleteKeyword(cookieId, index) {
    if (!confirm('确定要删除这个关键词吗？')) {
        return;
    }

    try {
        toggleLoading(true);

        // 使用新的删除API
        const response = await fetch(`${apiBase}/keywords/${cookieId}/${index}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            showToast('关键词删除成功', 'success');
            // 重新加载关键词列表
            loadAccountKeywords();
            clearKeywordCache(); // 清除缓存
        } else {
            const errorText = await response.text();
            console.error('关键词删除失败:', errorText);
            showToast('关键词删除失败', 'danger');
        }
    } catch (error) {
        console.error('删除关键词失败:', error);
        showToast('关键词删除失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// ==================== 图片关键词管理 ====================

// 验证图片尺寸
export function validateImageDimensions(file, inputElement) {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.onload = function() {
        const width = this.naturalWidth;
        const height = this.naturalHeight;

        URL.revokeObjectURL(url);

        const maxDimension = 4096;
        const maxPixels = 8 * 1024 * 1024;
        const totalPixels = width * height;

        if (width > maxDimension || height > maxDimension) {
            showToast(`❌ 图片尺寸过大：${width}x${height}，最大允许：${maxDimension}x${maxDimension}像素`, 'warning');
            inputElement.value = '';
            hideImagePreview();
            return;
        }

        if (totalPixels > maxPixels) {
            showToast(`❌ 图片像素总数过大：${(totalPixels / 1024 / 1024).toFixed(1)}M像素，最大允许：8M像素`, 'warning');
            inputElement.value = '';
            hideImagePreview();
            return;
        }

        showImagePreview(file);

        if (width > 2048 || height > 2048) {
            showToast(`ℹ️ 图片尺寸较大（${width}x${height}），上传时将自动压缩以优化性能`, 'info');
        } else {
            showToast(`✅ 图片尺寸合适（${width}x${height}），可以上传`, 'success');
        }
    };

    img.onerror = function() {
        URL.revokeObjectURL(url);
        showToast('❌ 无法读取图片文件，请选择有效的图片', 'warning');
        inputElement.value = '';
        hideImagePreview();
    };

    img.src = url;
}

// 显示图片预览
export function showImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewContainer = document.getElementById('imagePreview');
        const previewImg = document.getElementById('previewImg');

        previewImg.src = e.target.result;
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// 隐藏图片预览
export function hideImagePreview() {
    const previewContainer = document.getElementById('imagePreview');
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
}

// 显示图片模态框
export function showImageModal(imageUrl) {
    const modalHtml = `
        <div class="modal fade" id="imageViewModal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">图片预览</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <img src="${imageUrl}" alt="关键词图片" style="max-width: 100%; max-height: 70vh; border-radius: 8px;">
                    </div>
                </div>
            </div>
        </div>
    `;

    const existingModal = document.getElementById('imageViewModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const modal = new bootstrap.Modal(document.getElementById('imageViewModal'));
    modal.show();

    document.getElementById('imageViewModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// 初始化图片关键词事件监听器
export function initImageKeywordEventListeners() {
    const imageFileInput = document.getElementById('imageFile');
    if (imageFileInput && !imageFileInput.hasEventListener) {
        imageFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!file.type.startsWith('image/')) {
                    showToast('请选择图片文件', 'warning');
                    e.target.value = '';
                    hideImagePreview();
                    return;
                }

                if (file.size > 5 * 1024 * 1024) {
                    showToast('❌ 图片文件大小不能超过 5MB，当前文件大小：' + (file.size / 1024 / 1024).toFixed(1) + 'MB', 'warning');
                    e.target.value = '';
                    hideImagePreview();
                    return;
                }

                validateImageDimensions(file, e.target);
            } else {
                hideImagePreview();
            }
        });
        imageFileInput.hasEventListener = true;
    }
}

// 显示添加图片关键词模态框
export function showAddImageKeywordModal() {
    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    loadItemsListForImageKeyword();

    const modal = new bootstrap.Modal(document.getElementById('addImageKeywordModal'));
    modal.show();

    document.getElementById('imageKeyword').value = '';
    document.getElementById('imageItemIdSelect').value = '';
    document.getElementById('imageFile').value = '';
    hideImagePreview();
}

// 为图片关键词模态框加载商品列表
export async function loadItemsListForImageKeyword() {
    try {
        const response = await fetch(`${apiBase}/items/${currentCookieId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const items = data.items || [];

            const selectElement = document.getElementById('imageItemIdSelect');
            if (selectElement) {
                selectElement.innerHTML = '<option value="">选择商品或留空表示通用关键词</option>';

                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.item_id;
                    option.textContent = `${item.item_id} - ${item.item_title}`;
                    selectElement.appendChild(option);
                });
            }
        } else {
            console.warn('加载商品列表失败:', response.status);
        }
    } catch (error) {
        console.error('加载商品列表时发生错误:', error);
    }
}

// 添加图片关键词
export async function addImageKeyword() {
    const keyword = document.getElementById('imageKeyword').value.trim();
    const itemId = document.getElementById('imageItemIdSelect').value.trim();
    const fileInput = document.getElementById('imageFile');
    const file = fileInput.files[0];

    if (!keyword) {
        showToast('请填写关键词', 'warning');
        return;
    }

    if (!file) {
        showToast('请选择图片文件', 'warning');
        return;
    }

    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    try {
        toggleLoading(true);

        const formData = new FormData();
        formData.append('keyword', keyword);
        formData.append('item_id', itemId || '');
        formData.append('image', file);

        const response = await fetch(`${apiBase}/keywords/${currentCookieId}/image`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        if (response.ok) {
            showToast(`✨ 图片关键词 "${keyword}" 添加成功！`, 'success');

            const modal = bootstrap.Modal.getInstance(document.getElementById('addImageKeywordModal'));
            modal.hide();

            loadAccountKeywords();
            clearKeywordCache();
        } else {
            try {
                const errorData = await response.json();
                let errorMessage = errorData.detail || '图片关键词添加失败';

                if (errorMessage.includes('图片尺寸过大')) {
                    errorMessage = '❌ 图片尺寸过大，请选择尺寸较小的图片（建议不超过4096x4096像素）';
                } else if (errorMessage.includes('图片像素总数过大')) {
                    errorMessage = '❌ 图片像素总数过大，请选择分辨率较低的图片';
                } else if (errorMessage.includes('图片数据验证失败')) {
                    errorMessage = '❌ 图片格式不支持或文件损坏，请选择JPG、PNG、GIF格式的图片';
                } else if (errorMessage.includes('图片保存失败')) {
                    errorMessage = '❌ 图片保存失败，请检查图片格式和大小后重试';
                } else if (errorMessage.includes('文件大小超过限制')) {
                    errorMessage = '❌ 图片文件过大，请选择小于5MB的图片';
                } else if (errorMessage.includes('不支持的图片格式')) {
                    errorMessage = '❌ 不支持的图片格式，请选择JPG、PNG、GIF格式的图片';
                } else if (response.status === 413) {
                    errorMessage = '❌ 图片文件过大，请选择小于5MB的图片';
                } else if (response.status === 400) {
                    errorMessage = `❌ 请求参数错误：${errorMessage}`;
                } else if (response.status === 500) {
                    errorMessage = '❌ 服务器内部错误，请稍后重试';
                }

                console.error('图片关键词添加失败:', errorMessage);
                showToast(errorMessage, 'danger');
            } catch (e) {
                const errorText = await response.text();
                console.error('图片关键词添加失败:', errorText);

                let friendlyMessage = '图片关键词添加失败';
                if (response.status === 413) {
                    friendlyMessage = '❌ 图片文件过大，请选择小于5MB的图片';
                } else if (response.status === 400) {
                    friendlyMessage = '❌ 图片格式不正确或参数错误，请检查后重试';
                } else if (response.status === 500) {
                    friendlyMessage = '❌ 服务器内部错误，请稍后重试';
                }

                showToast(friendlyMessage, 'danger');
            }
        }
    } catch (error) {
        console.error('添加图片关键词失败:', error);
        showToast('添加图片关键词失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 编辑图片关键词（不允许修改）
export function editImageKeyword(index) {
    showToast('图片关键词不允许修改，请删除后重新添加', 'warning');
}

// 跳转到自动回复页面并选择指定账号
export function goToAutoReply(accountId) {
    showSection('auto-reply');

    setTimeout(() => {
        const accountSelect = document.getElementById('accountSelect');
        if (accountSelect) {
            accountSelect.value = accountId;
            loadAccountKeywords();
        }
    }, 100);

    showToast(`已切换到自动回复页面，账号 "${accountId}" 已选中`, 'info');
}

// 导出关键词
export async function exportKeywords() {
    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    try {
        toggleLoading(true);

        const response = await fetch(`${apiBase}/keywords-export/${currentCookieId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const blob = await response.blob();

            const contentDisposition = response.headers.get('Content-Disposition');
            let fileName = `关键词数据_${currentCookieId}_${new Date().toISOString().slice(0, 10)}.xlsx`;

            if (contentDisposition) {
                const fileNameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/);
                if (fileNameMatch) {
                    fileName = decodeURIComponent(fileNameMatch[1]);
                }
            }

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showToast('✅ 关键词导出成功', 'success');
        } else {
            const errorText = await response.text();
            console.error('导出关键词失败:', errorText);
            showToast('导出关键词失败', 'danger');
        }
    } catch (error) {
        console.error('导出关键词失败:', error);
        showToast('导出关键词失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 显示导入模态框
export function showImportModal() {
    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    const modal = new bootstrap.Modal(document.getElementById('importKeywordsModal'));
    modal.show();
}

// 导入关键词
export async function importKeywords() {
    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    const fileInput = document.getElementById('importFileInput');
    const file = fileInput.files[0];

    if (!file) {
        showToast('请选择要导入的Excel文件', 'warning');
        return;
    }

    try {
        const progressDiv = document.getElementById('importProgress');
        const progressBar = progressDiv.querySelector('.progress-bar');
        progressDiv.style.display = 'block';
        progressBar.style.width = '30%';

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${apiBase}/keywords-import/${currentCookieId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        progressBar.style.width = '70%';

        if (response.ok) {
            const result = await response.json();
            progressBar.style.width = '100%';

            setTimeout(() => {
                progressDiv.style.display = 'none';
                progressBar.style.width = '0%';

                const modal = bootstrap.Modal.getInstance(document.getElementById('importKeywordsModal'));
                modal.hide();

                fileInput.value = '';

                loadAccountKeywords(currentCookieId);

                showToast(`导入成功！新增: ${result.added}, 更新: ${result.updated}`, 'success');
            }, 500);
        } else {
            const error = await response.json();
            progressDiv.style.display = 'none';
            progressBar.style.width = '0%';
            showToast(`导入失败: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('导入关键词失败:', error);
        document.getElementById('importProgress').style.display = 'none';
        document.querySelector('#importProgress .progress-bar').style.width = '0%';
        showToast('导入关键词失败', 'error');
    }
}

// ==================== 关键词测试功能 ====================

// 测试关键词匹配
export async function testKeywordMatch() {
    const message = document.getElementById('testMessage').value.trim();
    const itemId = document.getElementById('testItemId').value.trim() || null;

    if (!message) {
        showToast('请输入测试消息', 'warning');
        return;
    }

    if (!currentCookieId) {
        showToast('请先选择账号', 'warning');
        return;
    }

    try {
        const response = await fetch(`${apiBase}/keywords/test/${currentCookieId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                message: message,
                item_id: itemId,
                user_name: '测试用户',
                user_id: 'test_user'
            })
        });

        const result = await response.json();
        const resultDiv = document.getElementById('testResult');
        const alertDiv = document.getElementById('testResultAlert');

        resultDiv.style.display = 'block';

        if (result.matched) {
            alertDiv.className = 'alert alert-success';
            document.getElementById('testResultTitle').innerHTML = '<i class="bi bi-check-circle"></i> 匹配成功！';

            document.getElementById('testResultKeyword').innerHTML =
                `<strong>匹配关键词：</strong>${escapeHtml(result.keyword || '')}`;
            document.getElementById('testResultMatchType').innerHTML =
                `<strong>匹配类型：</strong>${escapeHtml(result.match_type || '')}`;
            document.getElementById('testResultItemId').innerHTML =
                `<strong>商品ID：</strong>${escapeHtml(result.item_id || '通用')} ${!result.item_id ? '(通用关键词)' : ''}`;
            document.getElementById('testResultPosition').innerHTML =
                `<strong>匹配位置：</strong>${result.position ? `${result.position[0]}-${result.position[1]}` : 'N/A'}`;
            document.getElementById('testResultReplyMode').innerHTML =
                `<strong>回复模式：</strong>${escapeHtml(result.reply_mode || 'single')}`;
            document.getElementById('testResultReplyIndex').innerHTML =
                result.reply_index !== undefined ? `<strong>顺序索引：</strong>${result.reply_index}` : '';

            const replyDiv = document.getElementById('testResultReply');
            replyDiv.innerHTML = `<strong>回复内容：</strong><div class="mt-1 p-2 bg-white border rounded">${escapeHtml(result.reply || '').replace(/\n/g, '<br>')}</div>`;
        } else {
            alertDiv.className = 'alert alert-warning';
            document.getElementById('testResultTitle').innerHTML = '<i class="bi bi-exclamation-triangle"></i> 未匹配到关键词';

            document.getElementById('testResultKeyword').innerHTML = '';
            document.getElementById('testResultMatchType').innerHTML = '';
            document.getElementById('testResultItemId').innerHTML = '';
            document.getElementById('testResultPosition').innerHTML = '';
            document.getElementById('testResultReplyMode').innerHTML = '';
            document.getElementById('testResultReplyIndex').innerHTML = '';
            document.getElementById('testResultReply').innerHTML = '<div class="text-muted">没有关键词匹配当前消息内容</div>';
        }
    } catch (error) {
        console.error('关键词测试失败:', error);
        showToast('关键词测试失败: ' + error.message, 'danger');

        const resultDiv = document.getElementById('testResult');
        resultDiv.style.display = 'block';
        const alertDiv = document.getElementById('testResultAlert');
        alertDiv.className = 'alert alert-danger';
        document.getElementById('testResultTitle').innerHTML = '<i class="bi bi-x-circle"></i> 测试出错';
        document.getElementById('testResultReply').innerHTML = `<div class="text-danger">${escapeHtml(error.message)}</div>`;
    }
}
