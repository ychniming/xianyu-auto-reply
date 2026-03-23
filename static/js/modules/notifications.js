// 通知渠道管理模块 - 通知渠道和消息通知相关函数
import { apiBase, authToken } from './utils.js';
import { showToast, toggleLoading } from './api.js';

// 通知渠道类型配置
export const channelTypeConfigs = {
    qq: {
        title: 'QQ机器人通知',
        description: '使用QQ开放平台机器人发送通知（沙箱环境，无发送限制）。<a href="https://q.qq.com/" target="_blank">QQ开放平台</a> | <a href="https://bot.qq.com/wiki/" target="_blank">开发文档</a>',
        icon: 'bi-robot',
        color: 'primary',
        fields: [
            {
                id: 'app_id',
                label: '机器人 AppID',
                type: 'text',
                placeholder: '例如: 102891558',
                required: true,
                help: '在 QQ 开放平台后台获取'
            },
            {
                id: 'bot_secret',
                label: '机器人密钥 (BotSecret)',
                type: 'password',
                placeholder: '输入 BotSecret',
                required: true,
                help: '在 QQ 开放平台 → 开发设置 中获取'
            },
            {
                id: 'user_openid',
                label: '接收用户 OpenID',
                type: 'text',
                placeholder: '点击下方按钮自动获取',
                required: true,
                help: '点击"获取 OpenID"按钮，然后给机器人发送消息',
                readonly: false
            }
        ],
        customActions: [
            {
                id: 'get_openid',
                label: '获取 OpenID',
                icon: 'bi-key',
                color: 'success',
                help: '输入 AppID 和密钥后，点击此按钮，然后给机器人发送消息获取 OpenID'
            },
            {
                id: 'test_reply',
                label: '测试回复',
                icon: 'bi-send',
                color: 'primary',
                help: '填写完整配置后，点击此按钮发送测试消息'
            }
        ]
    },
    dingtalk: {
        title: '钉钉通知',
        description: '请设置钉钉机器人Webhook URL，支持自定义机器人和群机器人',
        icon: 'bi-bell-fill',
        color: 'info',
        fields: [
            {
                id: 'webhook_url',
                label: '钉钉机器人Webhook URL',
                type: 'url',
                placeholder: 'https://oapi.dingtalk.com/robot/send?access_token=...',
                required: true,
                help: '钉钉机器人的Webhook地址'
            },
            {
                id: 'secret',
                label: '加签密钥（可选）',
                type: 'text',
                placeholder: '输入加签密钥',
                required: false,
                help: '如果机器人开启了加签验证，请填写密钥'
            }
        ]
    },
    email: {
        title: '邮件通知',
        description: '通过SMTP服务器发送邮件通知，支持各种邮箱服务商',
        icon: 'bi-envelope-fill',
        color: 'success',
        fields: [
            {
                id: 'smtp_server',
                label: 'SMTP服务器',
                type: 'text',
                placeholder: 'smtp.gmail.com',
                required: true,
                help: '邮箱服务商的SMTP服务器地址'
            },
            {
                id: 'smtp_port',
                label: 'SMTP端口',
                type: 'number',
                placeholder: '587',
                required: true,
                help: '通常为587（TLS）或465（SSL）'
            },
            {
                id: 'email_user',
                label: '发送邮箱',
                type: 'email',
                placeholder: 'your-email@gmail.com',
                required: true,
                help: '用于发送通知的邮箱地址'
            },
            {
                id: 'email_password',
                label: '邮箱密码/授权码',
                type: 'password',
                placeholder: '输入密码或授权码',
                required: true,
                help: '邮箱密码或应用专用密码'
            },
            {
                id: 'recipient_email',
                label: '接收邮箱',
                type: 'email',
                placeholder: 'recipient@example.com',
                required: true,
                help: '用于接收通知的邮箱地址'
            }
        ]
    },
    webhook: {
        title: 'Webhook通知',
        description: '通过HTTP POST请求发送通知到自定义的Webhook地址',
        icon: 'bi-link-45deg',
        color: 'warning',
        fields: [
            {
                id: 'webhook_url',
                label: 'Webhook URL',
                type: 'url',
                placeholder: 'https://your-server.com/webhook',
                required: true,
                help: '接收通知的Webhook地址'
            },
            {
                id: 'http_method',
                label: 'HTTP方法',
                type: 'select',
                options: [
                    { value: 'POST', text: 'POST' },
                    { value: 'PUT', text: 'PUT' }
                ],
                required: true,
                help: '发送请求使用的HTTP方法'
            },
            {
                id: 'headers',
                label: '自定义请求头（可选）',
                type: 'textarea',
                placeholder: '{"Authorization": "Bearer token", "Content-Type": "application/json"}',
                required: false,
                help: 'JSON格式的自定义请求头'
            }
        ]
    },
    wechat: {
        title: '微信通知',
        description: '通过企业微信机器人发送通知消息',
        icon: 'bi-wechat',
        color: 'success',
        fields: [
            {
                id: 'webhook_url',
                label: '企业微信机器人Webhook URL',
                type: 'url',
                placeholder: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...',
                required: true,
                help: '企业微信群机器人的Webhook地址'
            }
        ]
    },
    telegram: {
        title: 'Telegram通知',
        description: '通过Telegram机器人发送通知消息',
        icon: 'bi-telegram',
        color: 'primary',
        fields: [
            {
                id: 'bot_token',
                label: 'Bot Token',
                type: 'text',
                placeholder: '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
                required: true,
                help: '从@BotFather获取的机器人Token'
            },
            {
                id: 'chat_id',
                label: 'Chat ID',
                type: 'text',
                placeholder: '123456789 或 @channel_name',
                required: true,
                help: '接收消息的用户ID或频道名'
            }
        ]
    }
};

// 显示添加渠道模态框
export function showAddChannelModal(type) {
    const config = channelTypeConfigs[type];
    if (!config) {
        showToast('不支持的通知渠道类型', 'danger');
        return;
    }

    document.getElementById('addChannelModalTitle').textContent = `添加${config.title}`;
    document.getElementById('channelTypeDescription').innerHTML = config.description;
    document.getElementById('channelType').value = type;

    const fieldsContainer = document.getElementById('channelConfigFields');
    fieldsContainer.innerHTML = '';

    config.fields.forEach(field => {
        const fieldHtml = generateFieldHtml(field, '');
        fieldsContainer.insertAdjacentHTML('beforeend', fieldHtml);
    });

    // 添加自定义按钮
    if (config.customActions && config.customActions.length > 0) {
        const actionsHtml = config.customActions.map(action => `
            <div class="mb-3">
                <button type="button" class="btn btn-${action.color}" id="btn_${action.id}" onclick="handleCustomAction('${action.id}')">
                    <i class="bi ${action.icon}"></i> ${action.label}
                </button>
                ${action.help ? `<small class="form-text text-muted d-block mt-1">${action.help}</small>` : ''}
                <div id="${action.id}_status" class="mt-2"></div>
            </div>
        `).join('');
        fieldsContainer.insertAdjacentHTML('beforeend', actionsHtml);
    }

    const modal = new bootstrap.Modal(document.getElementById('addChannelModal'));
    modal.show();
}

// 生成表单字段HTML
export function generateFieldHtml(field, prefix) {
    const fieldId = prefix + field.id;
    let inputHtml = '';

    switch (field.type) {
        case 'select':
            inputHtml = `<select class="form-select" id="${fieldId}" ${field.required ? 'required' : ''}>`;
            if (field.options) {
                field.options.forEach(option => {
                    inputHtml += `<option value="${option.value}">${option.text}</option>`;
                });
            }
            inputHtml += '</select>';
            break;
        case 'textarea':
            inputHtml = `<textarea class="form-control" id="${fieldId}" placeholder="${field.placeholder}" rows="3" ${field.required ? 'required' : ''}></textarea>`;
            break;
        case 'checkbox':
            return `
                <div class="mb-3 form-check">
                    <input type="checkbox" class="form-check-input" id="${fieldId}" ${field.required ? 'required' : ''}>
                    <label class="form-check-label" for="${fieldId}">${field.label}</label>
                    ${field.help ? `<small class="form-text text-muted d-block mt-1">${field.help}</small>` : ''}
                </div>
            `;
        default:
            inputHtml = `<input type="${field.type}" class="form-control" id="${fieldId}" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''}>`;
    }

    return `
        <div class="mb-3">
            <label for="${fieldId}" class="form-label">
            ${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}
            </label>
            ${inputHtml}
            ${field.help ? `<small class="form-text text-muted">${field.help}</small>` : ''}
        </div>
    `;
}

// 保存通知渠道
export async function saveNotificationChannel() {
    const type = document.getElementById('channelType').value;
    const name = document.getElementById('channelName').value;
    const enabled = document.getElementById('channelEnabled').checked;

    if (!name.trim()) {
        showToast('请输入渠道名称', 'warning');
        return;
    }

    const config = channelTypeConfigs[type];
    if (!config) {
        showToast('无效的渠道类型', 'danger');
        return;
    }

    const configData = {};
    let hasError = false;

    config.fields.forEach(field => {
        const element = document.getElementById(field.id);
        let value;
        
        if (field.type === 'checkbox') {
            value = element.checked;
        } else {
            value = element.value.trim();
        }

        if (field.required && !value && field.type !== 'checkbox') {
            showToast(`请填写${field.label}`, 'warning');
            hasError = true;
            return;
        }

        configData[field.id] = value;
    });

    if (hasError) return;

    try {
        const response = await fetch(`${apiBase}/notification-channels`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken.value}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                type: type,
                config: JSON.stringify(configData),
                enabled: enabled
            })
        });

        if (response.ok) {
            showToast('通知渠道添加成功', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addChannelModal'));
            modal.hide();
            loadNotificationChannels();
        } else {
            const error = await response.text();
            showToast(`添加失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('添加通知渠道失败:', error);
        showToast('添加通知渠道失败', 'danger');
    }
}

// 加载通知渠道列表
export async function loadNotificationChannels() {
    try {
        const response = await fetch(`${apiBase}/notification-channels`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (!response.ok) {
            throw new Error('获取通知渠道失败');
        }

        const channels = await response.json();
        renderNotificationChannels(channels);
    } catch (error) {
        console.error('加载通知渠道失败:', error);
        showToast('加载通知渠道失败', 'danger');
    }
}

// 渲染通知渠道列表
export function renderNotificationChannels(channels) {
    const tbody = document.getElementById('channelsTableBody');
    tbody.innerHTML = '';

    if (channels.length === 0) {
        tbody.innerHTML = `
            <tr>
            <td colspan="6" class="text-center py-4 text-muted">
                <i class="bi bi-bell fs-1 d-block mb-3"></i>
                <h5>暂无通知渠道</h5>
                <p class="mb-0">点击上方按钮添加通知渠道</p>
            </td>
            </tr>
        `;
        return;
    }

    channels.forEach(channel => {
        const tr = document.createElement('tr');

        const statusBadge = channel.enabled ?
            '<span class="badge bg-success">启用</span>' :
            '<span class="badge bg-secondary">禁用</span>';

        let channelType = channel.type;
        if (channelType === 'ding_talk') {
            channelType = 'dingtalk';
        }
        const typeConfig = channelTypeConfigs[channelType];
        const typeDisplay = typeConfig ? typeConfig.title : channel.type;
        const typeColor = typeConfig ? typeConfig.color : 'secondary';

        let configDisplay = '';
        try {
            const configData = JSON.parse(channel.config || '{}');
            const configEntries = Object.entries(configData);

            if (configEntries.length > 0) {
                configDisplay = configEntries.map(([key, value]) => {
                    if (key.includes('password') || key.includes('token') || key.includes('secret')) {
                        return `${key}: ****`;
                    }
                    const displayValue = value.length > 30 ? value.substring(0, 30) + '...' : value;
                    return `${key}: ${displayValue}`;
                }).join('<br>');
            } else {
                configDisplay = channel.config || '无配置';
            }
        } catch (e) {
            configDisplay = channel.config || '无配置';
            if (configDisplay.length > 30) {
                configDisplay = configDisplay.substring(0, 30) + '...';
            }
        }

        tr.innerHTML = `
            <td><strong class="text-primary">${channel.id}</strong></td>
            <td>
            <div class="d-flex align-items-center">
                <i class="bi ${typeConfig ? typeConfig.icon : 'bi-bell'} me-2 text-${typeColor}"></i>
                ${channel.name}
            </div>
            </td>
            <td><span class="badge bg-${typeColor}">${typeDisplay}</span></td>
            <td><small class="text-muted">${configDisplay}</small></td>
            <td>${statusBadge}</td>
            <td>
            <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-primary" onclick="editNotificationChannel(${channel.id})" title="编辑">
                <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteNotificationChannel(${channel.id})" title="删除">
                <i class="bi bi-trash"></i>
                </button>
            </div>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// 删除通知渠道
export async function deleteNotificationChannel(channelId) {
    if (!confirm('确定要删除这个通知渠道吗？')) {
        return;
    }

    try {
        const response = await fetch(`${apiBase}/notification-channels/${channelId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (response.ok) {
            showToast('通知渠道删除成功', 'success');
            loadNotificationChannels();
        } else {
            const error = await response.text();
            showToast(`删除失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('删除通知渠道失败:', error);
        showToast('删除通知渠道失败', 'danger');
    }
}

// 编辑通知渠道
export async function editNotificationChannel(channelId) {
    try {
        const response = await fetch(`${apiBase}/notification-channels`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (!response.ok) {
            throw new Error('获取通知渠道失败');
        }

        const channels = await response.json();
        const channel = channels.find(c => c.id === channelId);

        if (!channel) {
            showToast('通知渠道不存在', 'danger');
            return;
        }

        let channelType = channel.type;
        if (channelType === 'ding_talk') {
            channelType = 'dingtalk';
        }

        const config = channelTypeConfigs[channelType];
        if (!config) {
            showToast('不支持的渠道类型', 'danger');
            return;
        }

        document.getElementById('editChannelId').value = channel.id;
        document.getElementById('editChannelType').value = channelType;
        document.getElementById('editChannelName').value = channel.name;
        document.getElementById('editChannelEnabled').checked = channel.enabled;

        let configData = {};
        try {
            configData = JSON.parse(channel.config || '{}');
        } catch (e) {
            if (channel.type === 'qq') {
                configData = { qq_number: channel.config };
            } else if (channel.type === 'dingtalk' || channel.type === 'ding_talk') {
                configData = { webhook_url: channel.config };
            } else {
                configData = { config: channel.config };
            }
        }

        const fieldsContainer = document.getElementById('editChannelConfigFields');
        fieldsContainer.innerHTML = '';

        config.fields.forEach(field => {
            const fieldHtml = generateFieldHtml(field, 'edit_');
            fieldsContainer.insertAdjacentHTML('beforeend', fieldHtml);

            const element = document.getElementById('edit_' + field.id);
            if (element && configData[field.id] !== undefined) {
                if (field.type === 'checkbox') {
                    element.checked = configData[field.id];
                } else {
                    element.value = configData[field.id];
                }
            }
        });

        const modal = new bootstrap.Modal(document.getElementById('editChannelModal'));
        modal.show();
    } catch (error) {
        console.error('编辑通知渠道失败:', error);
        showToast('编辑通知渠道失败', 'danger');
    }
}

// 更新通知渠道
export async function updateNotificationChannel() {
    const channelId = document.getElementById('editChannelId').value;
    const type = document.getElementById('editChannelType').value;
    const name = document.getElementById('editChannelName').value;
    const enabled = document.getElementById('editChannelEnabled').checked;

    if (!name.trim()) {
        showToast('请输入渠道名称', 'warning');
        return;
    }

    const config = channelTypeConfigs[type];
    if (!config) {
        showToast('无效的渠道类型', 'danger');
        return;
    }

    const configData = {};
    let hasError = false;

    config.fields.forEach(field => {
        const element = document.getElementById('edit_' + field.id);
        let value;
        
        if (field.type === 'checkbox') {
            value = element.checked;
        } else {
            value = element.value.trim();
        }

        if (field.required && !value && field.type !== 'checkbox') {
            showToast(`请填写${field.label}`, 'warning');
            hasError = true;
            return;
        }

        configData[field.id] = value;
    });

    if (hasError) return;

    try {
        const response = await fetch(`${apiBase}/notification-channels/${channelId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken.value}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                config: JSON.stringify(configData),
                enabled: enabled
            })
        });

        if (response.ok) {
            showToast('通知渠道更新成功', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editChannelModal'));
            modal.hide();
            loadNotificationChannels();
        } else {
            const error = await response.text();
            showToast(`更新失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('更新通知渠道失败:', error);
        showToast('更新通知渠道失败', 'danger');
    }
}

// ==================== 消息通知配置功能 ====================

// 加载消息通知配置
export async function loadMessageNotifications() {
    try {
        const accountsResponse = await fetch(`${apiBase}/cookies`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (!accountsResponse.ok) {
            throw new Error('获取账号列表失败');
        }

        const accounts = await accountsResponse.json();

        const notificationsResponse = await fetch(`${apiBase}/message-notifications`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        let notifications = {};
        if (notificationsResponse.ok) {
            notifications = await notificationsResponse.json();
        }

        renderMessageNotifications(accounts, notifications);
    } catch (error) {
        console.error('加载消息通知配置失败:', error);
        showToast('加载消息通知配置失败', 'danger');
    }
}

// 渲染消息通知配置
export function renderMessageNotifications(accounts, notifications) {
    const tbody = document.getElementById('notificationsTableBody');
    tbody.innerHTML = '';

    if (accounts.length === 0) {
        tbody.innerHTML = `
            <tr>
            <td colspan="4" class="text-center py-4 text-muted">
                <i class="bi bi-chat-dots fs-1 d-block mb-3"></i>
                <h5>暂无账号数据</h5>
                <p class="mb-0">请先添加账号</p>
            </td>
            </tr>
        `;
        return;
    }

    accounts.forEach(accountId => {
        const accountNotifications = notifications[accountId] || [];
        const tr = document.createElement('tr');

        let channelsList = '';
        if (accountNotifications.length > 0) {
            channelsList = accountNotifications.map(n =>
                `<span class="badge bg-${n.enabled ? 'success' : 'secondary'} me-1">${n.channel_name}</span>`
            ).join('');
        } else {
            channelsList = '<span class="text-muted">未配置</span>';
        }

        const status = accountNotifications.some(n => n.enabled) ?
            '<span class="badge bg-success">启用</span>' :
            '<span class="badge bg-secondary">禁用</span>';

        tr.innerHTML = `
            <td><strong class="text-primary">${accountId}</strong></td>
            <td>${channelsList}</td>
            <td>${status}</td>
            <td>
            <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-primary" onclick="configAccountNotification('${accountId}')" title="配置">
                <i class="bi bi-gear"></i> 配置
                </button>
                ${accountNotifications.length > 0 ? `
                <button class="btn btn-sm btn-outline-danger" onclick="deleteAccountNotification('${accountId}')" title="删除配置">
                <i class="bi bi-trash"></i>
                </button>
                ` : ''}
            </div>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// 配置账号通知
export async function configAccountNotification(accountId) {
    try {
        const channelsResponse = await fetch(`${apiBase}/notification-channels`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (!channelsResponse.ok) {
            throw new Error('获取通知渠道失败');
        }

        const channels = await channelsResponse.json();

        if (channels.length === 0) {
            showToast('请先添加通知渠道', 'warning');
            return;
        }

        const notificationResponse = await fetch(`${apiBase}/message-notifications/${accountId}`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        let currentNotifications = [];
        if (notificationResponse.ok) {
            currentNotifications = await notificationResponse.json();
        }

        document.getElementById('configAccountId').value = accountId;
        document.getElementById('displayAccountId').value = accountId;

        const channelSelect = document.getElementById('notificationChannel');
        channelSelect.innerHTML = '<option value="">请选择通知渠道</option>';

        const currentNotification = currentNotifications.length > 0 ? currentNotifications[0] : null;

        channels.forEach(channel => {
            if (channel.enabled) {
                const option = document.createElement('option');
                option.value = channel.id;
                option.textContent = `${channel.name} (${channel.config})`;
                if (currentNotification && currentNotification.channel_id === channel.id) {
                    option.selected = true;
                }
                channelSelect.appendChild(option);
            }
        });

        document.getElementById('notificationEnabled').checked =
            currentNotification ? currentNotification.enabled : true;

        const modal = new bootstrap.Modal(document.getElementById('configNotificationModal'));
        modal.show();
    } catch (error) {
        console.error('配置账号通知失败:', error);
        showToast('配置账号通知失败', 'danger');
    }
}

// 删除账号通知配置
export async function deleteAccountNotification(accountId) {
    if (!confirm(`确定要删除账号 ${accountId} 的通知配置吗？`)) {
        return;
    }

    try {
        const response = await fetch(`${apiBase}/message-notifications/account/${accountId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (response.ok) {
            showToast('通知配置删除成功', 'success');
            loadMessageNotifications();
        } else {
            const error = await response.text();
            showToast(`删除失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('删除通知配置失败:', error);
        showToast('删除通知配置失败', 'danger');
    }
}

// 保存账号通知配置
export async function saveAccountNotification() {
    const accountId = document.getElementById('configAccountId').value;
    const channelId = document.getElementById('notificationChannel').value;
    const enabled = document.getElementById('notificationEnabled').checked;

    if (!channelId) {
        showToast('请选择通知渠道', 'warning');
        return;
    }

    try {
        const response = await fetch(`${apiBase}/message-notifications/${accountId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken.value}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                channel_id: parseInt(channelId),
                enabled: enabled
            })
        });

        if (response.ok) {
            showToast('通知配置保存成功', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('configNotificationModal'));
            modal.hide();
            loadMessageNotifications();
        } else {
            const error = await response.text();
            showToast(`保存失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('保存通知配置失败:', error);
        showToast('保存通知配置失败', 'danger');
    }
}

// ==================== 自定义操作处理 ====================

let openidPollingTimer = null;

window.handleCustomAction = async function(actionId) {
    if (actionId === 'get_openid') {
        await handleGetOpenID();
    } else if (actionId === 'test_reply') {
        await handleTestReply();
    }
};

async function handleGetOpenID() {
    const appIdInput = document.getElementById('app_id');
    const botSecretInput = document.getElementById('bot_secret');
    const openidInput = document.getElementById('user_openid');
    const statusDiv = document.getElementById('get_openid_status');
    
    if (!appIdInput || !botSecretInput) {
        showToast('找不到输入框', 'danger');
        return;
    }
    
    const appId = appIdInput.value.trim();
    const botSecret = botSecretInput.value.trim();
    
    if (!appId) {
        showToast('请先输入机器人 AppID', 'warning');
        appIdInput.focus();
        return;
    }
    
    if (!botSecret) {
        showToast('请先输入机器人密钥', 'warning');
        botSecretInput.focus();
        return;
    }
    
    const btn = document.getElementById('btn_get_openid');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>启动中...';
    }
    
    if (statusDiv) {
        statusDiv.innerHTML = '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>正在启动监听器...</div>';
    }
    
    try {
        const response = await fetch(`${apiBase}/qq/start-openid-listener`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken.value}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                app_id: appId,
                bot_secret: botSecret
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        const result = await response.json();
        const sessionId = result.session_id;
        
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="alert alert-warning mb-0">
                    <i class="bi bi-clock me-2"></i>
                    <span id="openid_status_text">监听器已启动，请给机器人发送消息...</span>
                </div>
            `;
        }
        
        startOpenIDPolling(sessionId, openidInput, statusDiv, btn);
        
    } catch (error) {
        console.error('启动监听器失败:', error);
        if (statusDiv) {
            statusDiv.innerHTML = `<div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle me-2"></i>启动失败: ${error.message}</div>`;
        }
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-key"></i> 获取 OpenID';
        }
    }
}

function startOpenIDPolling(sessionId, openidInput, statusDiv, btn) {
    let pollCount = 0;
    const maxPolls = 48;
    
    if (openidPollingTimer) {
        clearInterval(openidPollingTimer);
    }
    
    openidPollingTimer = setInterval(async () => {
        pollCount++;
        
        if (pollCount > maxPolls) {
            clearInterval(openidPollingTimer);
            openidPollingTimer = null;
            if (statusDiv) {
                statusDiv.innerHTML = '<div class="alert alert-secondary mb-0"><i class="bi bi-clock me-2"></i>监听超时，请重试</div>';
            }
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-key"></i> 获取 OpenID';
            }
            return;
        }
        
        try {
            const response = await fetch(`${apiBase}/qq/check-openid/${sessionId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken.value}`
                }
            });
            
            if (!response.ok) {
                clearInterval(openidPollingTimer);
                openidPollingTimer = null;
                if (statusDiv) {
                    statusDiv.innerHTML = '<div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle me-2"></i>查询失败</div>';
                }
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-key"></i> 获取 OpenID';
                }
                return;
            }
            
            const result = await response.json();
            
            if (result.status === 'success' && result.openid) {
                clearInterval(openidPollingTimer);
                openidPollingTimer = null;
                
                if (openidInput) {
                    openidInput.value = result.openid;
                }
                
                if (statusDiv) {
                    statusDiv.innerHTML = `
                        <div class="alert alert-success mb-0">
                            <i class="bi bi-check-circle me-2"></i>
                            <strong>成功获取 OpenID!</strong><br>
                            <code class="user-select-all">${result.openid}</code>
                        </div>
                    `;
                }
                
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-key"></i> 获取 OpenID';
                }
                
                showToast('OpenID 获取成功！', 'success');
                
            } else if (result.status === 'error' || result.status === 'timeout') {
                clearInterval(openidPollingTimer);
                openidPollingTimer = null;
                
                if (statusDiv) {
                    statusDiv.innerHTML = `<div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle me-2"></i>${result.error || '获取失败'}</div>`;
                }
                
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-key"></i> 获取 OpenID';
                }
                
            } else {
                const statusText = document.getElementById('openid_status_text');
                if (statusText && result.message) {
                    statusText.textContent = result.message;
                }
            }
            
        } catch (error) {
            console.error('轮询状态失败:', error);
        }
        
    }, 2500);
}

async function handleTestReply() {
    const appIdInput = document.getElementById('app_id');
    const botSecretInput = document.getElementById('bot_secret');
    const openidInput = document.getElementById('user_openid');
    const statusDiv = document.getElementById('test_reply_status');
    
    if (!appIdInput || !botSecretInput || !openidInput) {
        showToast('找不到输入框', 'danger');
        return;
    }
    
    const appId = appIdInput.value.trim();
    const botSecret = botSecretInput.value.trim();
    const userOpenid = openidInput.value.trim();
    
    if (!appId) {
        showToast('请先输入机器人 AppID', 'warning');
        appIdInput.focus();
        return;
    }
    
    if (!botSecret) {
        showToast('请先输入机器人密钥', 'warning');
        botSecretInput.focus();
        return;
    }
    
    if (!userOpenid) {
        showToast('请先获取或输入接收用户 OpenID', 'warning');
        openidInput.focus();
        return;
    }
    
    const btn = document.getElementById('btn_test_reply');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>发送中...';
    }
    
    if (statusDiv) {
        statusDiv.innerHTML = '<div class="alert alert-info mb-0"><i class="bi bi-send me-2"></i>正在发送测试消息...</div>';
    }
    
    try {
        const response = await fetch(`${apiBase}/qq/send-test-message`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken.value}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                app_id: appId,
                bot_secret: botSecret,
                user_openid: userOpenid
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        const result = await response.json();
        
        if (result.success) {
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="alert alert-success mb-0">
                        <i class="bi bi-check-circle me-2"></i>
                        <strong>发送成功！</strong><br>
                        ${result.message || '请检查 QQ 是否收到测试消息'}
                    </div>
                `;
            }
            showToast('测试消息发送成功！', 'success');
        } else {
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="alert alert-danger mb-0">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        <strong>发送失败</strong><br>
                        ${result.error || '未知错误'}
                    </div>
                `;
            }
            showToast(`发送失败: ${result.error || '未知错误'}`, 'danger');
        }
        
    } catch (error) {
        console.error('发送测试消息失败:', error);
        if (statusDiv) {
            statusDiv.innerHTML = `<div class="alert alert-danger mb-0"><i class="bi bi-exclamation-triangle me-2"></i>发送失败: ${error.message}</div>`;
        }
        showToast(`发送失败: ${error.message}`, 'danger');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-send"></i> 测试回复';
        }
    }
}
