// 自动发货模块 - Delivery Rules Management
import { apiBase, authToken } from './utils.js';
import { } from './api.js';

// ==================== 自动发货功能 ====================

// 加载发货规则列表
export async function loadDeliveryRules() {
    try {
        const response = await fetch(`${apiBase}/delivery-rules`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const rules = await response.json();
            renderDeliveryRulesList(rules);
            updateDeliveryStats(rules);

            // 同时加载卡券列表用于下拉选择
            loadCardsForSelect();
        } else {
            showToast('加载发货规则失败', 'danger');
        }
    } catch (error) {
        console.error('加载发货规则失败:', error);
        showToast('加载发货规则失败', 'danger');
    }
}

// 渲染发货规则列表
export function renderDeliveryRulesList(rules) {
    const tbody = document.getElementById('deliveryRulesTableBody');

    if (rules.length === 0) {
        tbody.innerHTML = `
            <tr>
            <td colspan="7" class="text-center py-4 text-muted">
                <i class="bi bi-truck fs-1 d-block mb-3"></i>
                <h5>暂无发货规则</h5>
                <p class="mb-0">点击"添加规则"开始配置自动发货规则</p>
            </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = '';

    rules.forEach(rule => {
        const tr = document.createElement('tr');

        // 状态标签
        const statusBadge = rule.enabled ?
            '<span class="badge bg-success">启用</span>' :
            '<span class="badge bg-secondary">禁用</span>';

        // 卡券类型标签
        let cardTypeBadge = '<span class="badge bg-secondary">未知</span>';
        if (rule.card_type) {
            switch(rule.card_type) {
                case 'api':
                    cardTypeBadge = '<span class="badge bg-info">API接口</span>';
                    break;
                case 'text':
                    cardTypeBadge = '<span class="badge bg-success">固定文字</span>';
                    break;
                case 'data':
                    cardTypeBadge = '<span class="badge bg-warning">批量数据</span>';
                    break;
                case 'image':
                    cardTypeBadge = '<span class="badge bg-primary">图片</span>';
                    break;
            }
        }

        tr.innerHTML = `
            <td>
            <div class="fw-bold">${rule.keyword}</div>
            ${rule.description ? `<small class="text-muted">${rule.description}</small>` : ''}
            </td>
            <td>
            <div>
                <span class="badge bg-primary">${rule.card_name || '未知卡券'}</span>
                ${rule.is_multi_spec && rule.spec_name && rule.spec_value ?
                `<br><small class="text-muted mt-1 d-block"><i class="bi bi-tags"></i> ${rule.spec_name}: ${rule.spec_value}</small>` :
                ''}
            </div>
            </td>
            <td>${cardTypeBadge}</td>
            <td>
            <span class="badge bg-info">${rule.delivery_count || 1}</span>
            </td>
            <td>${statusBadge}</td>
            <td>
            <span class="badge bg-warning">${rule.delivery_times || 0}</span>
            </td>
            <td>
            <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-primary" onclick="editDeliveryRule(${rule.id})" title="编辑">
                <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-info" onclick="testDeliveryRule(${rule.id})" title="测试">
                <i class="bi bi-play"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteDeliveryRule(${rule.id})" title="删除">
                <i class="bi bi-trash"></i>
                </button>
            </div>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// 更新发货统计
export function updateDeliveryStats(rules) {
    const totalRules = rules.length;
    const activeRules = rules.filter(rule => rule.enabled).length;
    const todayDeliveries = 0; // 需要从后端获取今日发货统计
    const totalDeliveries = rules.reduce((sum, rule) => sum + (rule.delivery_times || 0), 0);

    document.getElementById('totalRules').textContent = totalRules;
    document.getElementById('activeRules').textContent = activeRules;
    document.getElementById('todayDeliveries').textContent = todayDeliveries;
    document.getElementById('totalDeliveries').textContent = totalDeliveries;
}

// 显示添加发货规则模态框
export function showAddDeliveryRuleModal() {
    document.getElementById('addDeliveryRuleForm').reset();
    loadCardsForSelect(); // 加载卡券选项
    const modal = new bootstrap.Modal(document.getElementById('addDeliveryRuleModal'));
    modal.show();
}

// 加载卡券列表用于下拉选择
export async function loadCardsForSelect() {
    try {
        const response = await fetch(`${apiBase}/cards`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const cards = await response.json();
            const select = document.getElementById('selectedCard');

            // 清空现有选项
            select.innerHTML = '<option value="">请选择卡券</option>';

            cards.forEach(card => {
                if (card.enabled) { // 只显示启用的卡券
                    const option = document.createElement('option');
                    option.value = card.id;

                    // 构建显示文本
                    let displayText = card.name;

                    // 添加类型信息
                    let typeText;
                    switch(card.type) {
                        case 'api':
                            typeText = 'API';
                            break;
                        case 'text':
                            typeText = '固定文字';
                            break;
                        case 'data':
                            typeText = '批量数据';
                            break;
                        case 'image':
                            typeText = '图片';
                            break;
                        default:
                            typeText = '未知类型';
                    }
                    displayText += ` (${typeText})`;

                    // 添加规格信息
                    if (card.is_multi_spec && card.spec_name && card.spec_value) {
                        displayText += ` [${card.spec_name}:${card.spec_value}]`;
                    }

                    option.textContent = displayText;
                    select.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('加载卡券选项失败:', error);
    }
}

// 保存发货规则
export async function saveDeliveryRule() {
    try {
        const keyword = document.getElementById('productKeyword').value;
        const cardId = document.getElementById('selectedCard').value;
        const deliveryCount = document.getElementById('deliveryCount').value;
        const enabled = document.getElementById('ruleEnabled').checked;
        const description = document.getElementById('ruleDescription').value;

        if (!keyword || !cardId) {
            showToast('请填写必填字段', 'warning');
            return;
        }

        const ruleData = {
            keyword: keyword,
            card_id: parseInt(cardId),
            delivery_count: parseInt(deliveryCount),
            enabled: enabled,
            description: description
        };

        const response = await fetch(`${apiBase}/delivery-rules`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });

        if (response.ok) {
            showToast('发货规则保存成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addDeliveryRuleModal')).hide();
            loadDeliveryRules();
        } else {
            const error = await response.text();
            showToast(`保存失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('保存发货规则失败:', error);
        showToast('保存发货规则失败', 'danger');
    }
}

// 编辑发货规则
export async function editDeliveryRule(ruleId) {
    try {
        // 获取发货规则详情
        const response = await fetch(`${apiBase}/delivery-rules/${ruleId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const rule = await response.json();

            // 填充编辑表单
            document.getElementById('editRuleId').value = rule.id;
            document.getElementById('editProductKeyword').value = rule.keyword;
            document.getElementById('editDeliveryCount').value = rule.delivery_count || 1;
            document.getElementById('editRuleEnabled').checked = rule.enabled;
            document.getElementById('editRuleDescription').value = rule.description || '';

            // 加载卡券选项并设置当前选中的卡券
            await loadCardsForEditSelect();
            document.getElementById('editSelectedCard').value = rule.card_id;

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('editDeliveryRuleModal'));
            modal.show();
        } else {
            showToast('获取发货规则详情失败', 'danger');
        }
    } catch (error) {
        console.error('获取发货规则详情失败:', error);
        showToast('获取发货规则详情失败', 'danger');
    }
}

// 加载卡券列表用于编辑时的下拉选择
export async function loadCardsForEditSelect() {
    try {
        const response = await fetch(`${apiBase}/cards`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const cards = await response.json();
            const select = document.getElementById('editSelectedCard');

            // 清空现有选项
            select.innerHTML = '<option value="">请选择卡券</option>';

            cards.forEach(card => {
                if (card.enabled) { // 只显示启用的卡券
                    const option = document.createElement('option');
                    option.value = card.id;

                    // 构建显示文本
                    let displayText = card.name;

                    // 添加类型信息
                    let typeText;
                    switch(card.type) {
                        case 'api':
                            typeText = 'API';
                            break;
                        case 'text':
                            typeText = '固定文字';
                            break;
                        case 'data':
                            typeText = '批量数据';
                            break;
                        case 'image':
                            typeText = '图片';
                            break;
                        default:
                            typeText = '未知类型';
                    }
                    displayText += ` (${typeText})`;

                    // 添加规格信息
                    if (card.is_multi_spec && card.spec_name && card.spec_value) {
                        displayText += ` [${card.spec_name}:${card.spec_value}]`;
                    }

                    option.textContent = displayText;
                    select.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('加载卡券选项失败:', error);
    }
}

// 更新发货规则
export async function updateDeliveryRule() {
    try {
        const ruleId = document.getElementById('editRuleId').value;
        const keyword = document.getElementById('editProductKeyword').value;
        const cardId = document.getElementById('editSelectedCard').value;
        const deliveryCount = document.getElementById('editDeliveryCount').value;
        const enabled = document.getElementById('editRuleEnabled').checked;
        const description = document.getElementById('editRuleDescription').value;

        if (!keyword || !cardId) {
            showToast('请填写必填字段', 'warning');
            return;
        }

        const ruleData = {
            keyword: keyword,
            card_id: parseInt(cardId),
            delivery_count: parseInt(deliveryCount),
            enabled: enabled,
            description: description
        };

        const response = await fetch(`${apiBase}/delivery-rules/${ruleId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });

        if (response.ok) {
            showToast('发货规则更新成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editDeliveryRuleModal')).hide();
            loadDeliveryRules();
        } else {
            const error = await response.text();
            showToast(`更新失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('更新发货规则失败:', error);
        showToast('更新发货规则失败', 'danger');
    }
}

// 测试发货规则（占位函数）
export function testDeliveryRule(ruleId) {
    showToast('测试功能开发中...', 'info');
}

// 删除发货规则
export async function deleteDeliveryRule(ruleId) {
    if (confirm('确定要删除这个发货规则吗？删除后无法恢复！')) {
        try {
            const response = await fetch(`${apiBase}/delivery-rules/${ruleId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });

            if (response.ok) {
                showToast('发货规则删除成功', 'success');
                loadDeliveryRules();
            } else {
                const error = await response.text();
                showToast(`删除失败: ${error}`, 'danger');
            }
        } catch (error) {
            console.error('删除发货规则失败:', error);
            showToast('删除发货规则失败', 'danger');
        }
    }
}


