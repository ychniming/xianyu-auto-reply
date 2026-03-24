// AI回复模块 - AI回复配置相关函数
import { apiBase, authToken, aiSettings } from './utils.js';
import { saveAIReplyConfigAPI, testAIReplyAPI, saveDefaultReplyAPI, getDefaultRepliesAPI, updateDefaultReplyAPI } from './api.js';

// 切换AI回复设置面板显示
export function toggleAIReplySettings() {
    const settingsPanel = document.getElementById('aiReplySettingsPanel');
    if (!settingsPanel) {
        showToast('AI回复设置面板不存在', 'warning');
        return;
    }

    // 切换显示状态
    if (settingsPanel.style.display === 'none') {
        settingsPanel.style.display = 'block';
        // 加载当前AI回复设置
        loadAIReplySettings();
    } else {
        settingsPanel.style.display = 'none';
    }
}

// 加载AI回复设置
export function loadAIReplySettings() {
    // 从本地存储或默认配置获取设置
    const settings = {
        enabled: aiSettings.enabled || false,
        model: aiSettings.model || 'gpt-4',
        apiKey: aiSettings.apiKey || '',
        customPrompt: aiSettings.customPrompt || '',
        temperature: aiSettings.temperature || 0.7,
        maxTokens: aiSettings.maxTokens || 500,
        intentClassification: aiSettings.intentClassification !== false, // 默认启用
        autoDelivery: aiSettings.autoDelivery !== false // 默认启用
    };

    // 填充表单
    const enabledCheckbox = document.getElementById('aiReplyEnabled');
    if (enabledCheckbox) enabledCheckbox.checked = settings.enabled;

    const modelSelect = document.getElementById('aiModel');
    if (modelSelect) modelSelect.value = settings.model;

    const apiKeyInput = document.getElementById('aiApiKey');
    if (apiKeyInput) apiKeyInput.value = settings.apiKey;

    const customPromptTextarea = document.getElementById('aiCustomPrompt');
    if (customPromptTextarea) customPromptTextarea.value = settings.customPrompt;

    const temperatureInput = document.getElementById('aiTemperature');
    if (temperatureInput) temperatureInput.value = settings.temperature;

    const maxTokensInput = document.getElementById('aiMaxTokens');
    if (maxTokensInput) maxTokensInput.value = settings.maxTokens;

    const intentCheckbox = document.getElementById('intentClassification');
    if (intentCheckbox) intentCheckbox.checked = settings.intentClassification;

    const autoDeliveryCheckbox = document.getElementById('autoDelivery');
    if (autoDeliveryCheckbox) autoDeliveryCheckbox.checked = settings.autoDelivery;

    // 更新自定义模型输入框可见性
    toggleCustomModelInput();
}

// 切换自定义模型输入框显示
export function toggleCustomModelInput() {
    const modelSelect = document.getElementById('aiModel');
    const customModelInput = document.getElementById('customModelInput');

    if (!modelSelect || !customModelInput) return;

    if (modelSelect.value === 'custom') {
        customModelInput.style.display = 'block';
    } else {
        customModelInput.style.display = 'none';
    }
}

// 测试AI回复功能
export async function testAIReply() {
    const testInput = document.getElementById('aiTestInput');
    const testOutput = document.getElementById('aiTestOutput');
    const testButton = document.getElementById('testAIReplyBtn');

    if (!testInput || !testOutput) {
        showToast('测试组件不存在', 'danger');
        return;
    }

    const testMessage = testInput.value.trim();
    if (!testMessage) {
        showToast('请输入测试消息', 'warning');
        return;
    }

    // 获取当前配置
    const config = {
        enabled: true,
        model: document.getElementById('aiModel')?.value || 'gpt-4',
        apiKey: document.getElementById('aiApiKey')?.value || '',
        customPrompt: document.getElementById('aiCustomPrompt')?.value || '',
        temperature: parseFloat(document.getElementById('aiTemperature')?.value || '0.7'),
        maxTokens: parseInt(document.getElementById('aiMaxTokens')?.value || '500')
    };

    // 显示加载状态
    testOutput.value = '正在生成回复...';
    testButton.disabled = true;

    try {
        const response = await testAIReplyAPI(testMessage, config);

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                testOutput.value = data.reply || '收到空回复';
            } else {
                testOutput.value = `测试失败: ${data.message || '未知错误'}`;
            }
        } else {
            testOutput.value = `请求失败: HTTP ${response.status}`;
        }
    } catch (error) {
        console.error('AI测试失败:', error);
        testOutput.value = `测试失败: ${error.message}`;
    } finally {
        testButton.disabled = false;
    }
}

// 保存AI回复配置
export async function saveAIReplyConfig() {
    const enabled = document.getElementById('aiReplyEnabled')?.checked || false;
    const model = document.getElementById('aiModel')?.value || 'gpt-4';
    const apiKey = document.getElementById('aiApiKey')?.value || '';
    const customPrompt = document.getElementById('aiCustomPrompt')?.value || '';
    const temperature = parseFloat(document.getElementById('aiTemperature')?.value || '0.7');
    const maxTokens = parseInt(document.getElementById('aiMaxTokens')?.value || '500');
    const intentClassification = document.getElementById('intentClassification')?.checked || false;
    const autoDelivery = document.getElementById('autoDelivery')?.checked || false;

    // 验证API Key
    if (enabled && !apiKey) {
        showToast('请输入API Key', 'warning');
        return false;
    }

    const config = {
        enabled,
        model,
        apiKey,
        customPrompt,
        temperature,
        maxTokens,
        intentClassification,
        autoDelivery
    };

    try {
        const response = await saveAIReplyConfigAPI(config);

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // 更新本地配置
                aiSettings.enabled = enabled;
                aiSettings.model = model;
                aiSettings.apiKey = apiKey;
                aiSettings.customPrompt = customPrompt;
                aiSettings.temperature = temperature;
                aiSettings.maxTokens = maxTokens;
                aiSettings.intentClassification = intentClassification;
                aiSettings.autoDelivery = autoDelivery;

                // 保存到本地存储
                localStorage.setItem('ai_settings', JSON.stringify(aiSettings));

                showToast('AI回复配置已保存', 'success');
                return true;
            } else {
                showToast(data.message || '保存失败', 'danger');
            }
        } else {
            showToast(`保存失败: HTTP ${response.status}`, 'danger');
        }
    } catch (error) {
        console.error('保存AI配置失败:', error);
        showToast('保存AI配置失败', 'danger');
    }

    return false;
}

// 切换回复内容可见性
export function toggleReplyContentVisibility(contentId, toggleBtn) {
    const content = document.getElementById(contentId);
    if (!content) return;

    if (content.type === 'password') {
        content.type = 'text';
        if (toggleBtn) toggleBtn.textContent = '隐藏';
    } else {
        content.type = 'password';
        if (toggleBtn) toggleBtn.textContent = '显示';
    }
}

// 打开默认回复管理器
export async function openDefaultReplyManager() {
    try {
        const response = await fetch(`${apiBase}/default-replies`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                renderDefaultRepliesTable(data.replies || {});
                const modal = new bootstrap.Modal(document.getElementById('defaultReplyManagerModal'));
                modal.show();
            } else {
                showToast(data.message || '加载失败', 'danger');
            }
        } else {
            showToast(`加载失败: HTTP ${response.status}`, 'danger');
        }
    } catch (error) {
        console.error('打开默认回复管理器失败:', error);
        showToast('打开默认回复管理器失败', 'danger');
    }
}

// 渲染默认回复表格
export function renderDefaultRepliesTable(replies) {
    const tbody = document.getElementById('defaultReplyTableBody');
    if (!tbody) {
        console.error('找不到 defaultReplyTableBody 元素');
        return;
    }

    tbody.innerHTML = '';

    for (const [cookieId, replyData] of Object.entries(replies)) {
        const enabled = replyData.enabled || false;
        const content = replyData.reply_content || '';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${escapeHtml(cookieId)}</code></td>
            <td>
                <span class="badge ${enabled ? 'bg-success' : 'bg-secondary'}">
                    ${enabled ? '已启用' : '已禁用'}
                </span>
            </td>
            <td>
                <div class="text-truncate" style="max-width: 400px;" title="${escapeHtml(content)}">
                    ${escapeHtml(content) || '<span class="text-muted">未设置</span>'}
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editDefaultReply('${escapeHtml(cookieId)}')">
                    <i class="bi bi-pencil"></i> 编辑
                </button>
            </td>
        `;
        tbody.appendChild(row);
    }

    if (Object.keys(replies).length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无数据</td></tr>';
    }
}

// 编辑默认回复
export async function editDefaultReply(cookieId) {
    try {
        const response = await fetch(`${apiBase}/default-replies/${cookieId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const replyData = data || { enabled: false, reply_content: '' };

            document.getElementById('editAccountId').value = cookieId;
            document.getElementById('editAccountIdDisplay').value = cookieId;
            document.getElementById('editDefaultReplyEnabled').checked = replyData.enabled || false;
            document.getElementById('editReplyContent').value = replyData.reply_content || '';

            toggleReplyContentVisibility();

            const modal = new bootstrap.Modal(document.getElementById('editDefaultReplyModal'));
            modal.show();
        } else {
            showToast(`加载失败: HTTP ${response.status}`, 'danger');
        }
    } catch (error) {
        console.error('加载默认回复失败:', error);
        showToast('加载默认回复失败', 'danger');
    }
}

// 保存默认回复
export async function saveDefaultReply() {
    const cookieId = document.getElementById('editAccountId').value;
    const enabled = document.getElementById('editDefaultReplyEnabled').checked;
    const content = document.getElementById('editReplyContent').value.trim();

    if (!cookieId) {
        showToast('账号ID不能为空', 'warning');
        return false;
    }

    try {
        const response = await fetch(`${apiBase}/default-replies/${cookieId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ enabled, reply_content: content })
        });

        if (response.ok) {
            showToast('默认回复已保存', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editDefaultReplyModal')).hide();
            openDefaultReplyManager();
            return true;
        } else {
            showToast(`保存失败: HTTP ${response.status}`, 'danger');
        }
    } catch (error) {
        console.error('保存默认回复失败:', error);
        showToast('保存默认回复失败', 'danger');
    }

    return false;
}

// 获取所有默认回复
export async function getDefaultReplies() {
    try {
        const response = await getDefaultRepliesAPI();

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                return data.replies || {};
            }
        }
    } catch (error) {
        console.error('获取默认回复失败:', error);
    }

    return {};
}

// 获取单个默认回复
export async function getDefaultReply(type) {
    try {
        const response = await getDefaultRepliesAPI();

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const replies = data.replies || {};
                return replies[type] || '';
            }
        }
    } catch (error) {
        console.error('获取默认回复失败:', error);
    }

    return '';
}

// 更新单个默认回复
export async function updateDefaultReply(type, content) {
    try {
        const response = await updateDefaultReplyAPI(type, content);

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showToast(`${type}默认回复已更新`, 'success');
                return true;
            } else {
                showToast(data.message || '更新失败', 'danger');
            }
        }
    } catch (error) {
        console.error('更新默认回复失败:', error);
        showToast('更新默认回复失败', 'danger');
    }

    return false;
}

// 跳转到AI回复配置页面并选中指定账号
export function configAIReply(accountId) {
    showSection('ai-reply');

    setTimeout(() => {
        const accountSelect = document.getElementById('aiAccountSelect');
        if (accountSelect) {
            accountSelect.value = accountId;
        }
    }, 100);

    showToast(`已切换到AI回复配置页面，账号 "${accountId}" 已选中`, 'info');
}


