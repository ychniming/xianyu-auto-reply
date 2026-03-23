// 商品管理模块 - Items Management
import { apiBase, authToken, escapeHtml, formatDateTime } from './utils.js';
import { showToast } from './api.js';

// ==================== 商品管理功能 ====================

// 切换商品多规格状态
export async function toggleItemMultiSpec(cookieId, itemId, isMultiSpec) {
    try {
        const response = await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}/multi-spec`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                is_multi_spec: isMultiSpec
            })
        });

        if (response.ok) {
            showToast(`${isMultiSpec ? '开启' : '关闭'}多规格成功`, 'success');
            // 刷新商品列表
            await refreshItemsData();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || '操作失败');
        }
    } catch (error) {
        console.error('切换多规格状态失败:', error);
        showToast(`切换多规格状态失败: ${error.message}`, 'danger');
    }
}

// 加载商品列表
export async function loadItems() {
    try {
        // 先加载Cookie列表用于筛选
        await loadCookieFilter();

        // 加载商品列表
        await refreshItemsData();
    } catch (error) {
        console.error('加载商品列表失败:', error);
        showToast('加载商品列表失败', 'danger');
    }
}

// 只刷新商品数据，不重新加载筛选器
export async function refreshItemsData() {
    try {
        const selectedCookie = document.getElementById('itemCookieFilter').value;
        if (selectedCookie) {
            await loadItemsByCookie();
        } else {
            await loadAllItems();
        }
    } catch (error) {
        console.error('刷新商品数据失败:', error);
        showToast('刷新商品数据失败', 'danger');
    }
}

// 加载Cookie筛选选项
export async function loadCookieFilter() {
    try {
        const response = await fetch(`${apiBase}/cookies/details`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const jsonResponse = await response.json();
            const accounts = jsonResponse.data || jsonResponse;
            const select = document.getElementById('itemCookieFilter');

            // 保存当前选择的值
            const currentValue = select.value;

            // 清空现有选项（保留"所有账号"）
            select.innerHTML = '<option value="">所有账号</option>';

            if (accounts.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '❌ 暂无账号';
                option.disabled = true;
                select.appendChild(option);
                return;
            }

            // 分组显示：先显示启用的账号，再显示禁用的账号
            const enabledAccounts = accounts.filter(account => {
                const enabled = account.enabled === undefined ? true : account.enabled;
                return enabled;
            });
            const disabledAccounts = accounts.filter(account => {
                const enabled = account.enabled === undefined ? true : account.enabled;
                return !enabled;
            });

            // 添加启用的账号
            enabledAccounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = `🟢 ${account.id}`;
                select.appendChild(option);
            });

            // 添加禁用的账号
            if (disabledAccounts.length > 0) {
                // 添加分隔线
                if (enabledAccounts.length > 0) {
                    const separator = document.createElement('option');
                    separator.value = '';
                    separator.textContent = '────────────────';
                    separator.disabled = true;
                    select.appendChild(separator);
                }

                disabledAccounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;
                    option.textContent = `🔴 ${account.id} (已禁用)`;
                    select.appendChild(option);
                });
            }

            // 恢复之前选择的值
            if (currentValue) {
                select.value = currentValue;
            }
        }
    } catch (error) {
        console.error('加载Cookie列表失败:', error);
        showToast('加载账号列表失败', 'danger');
    }
}

// 加载所有商品
export async function loadAllItems() {
    try {
        const response = await fetch(`${apiBase}/items`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const jsonResponse = await response.json();
            const itemsData = jsonResponse.data || jsonResponse;
            displayItems(itemsData.items);
        } else {
            throw new Error('获取商品列表失败');
        }
    } catch (error) {
        console.error('加载商品列表失败:', error);
        showToast('加载商品列表失败', 'danger');
    }
}

// 按Cookie加载商品
export async function loadItemsByCookie() {
    const cookieId = document.getElementById('itemCookieFilter').value;

    if (!cookieId) {
        await loadAllItems();
        return;
    }

    try {
        const response = await fetch(`${apiBase}/items/cookie/${encodeURIComponent(cookieId)}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const jsonResponse = await response.json();
            const itemsData = jsonResponse.data || jsonResponse;
            displayItems(itemsData.items);
        } else {
            throw new Error('获取商品列表失败');
        }
    } catch (error) {
        console.error('加载商品列表失败:', error);
        showToast('加载商品列表失败', 'danger');
    }
}

// 显示商品列表
export function displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');

    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">暂无商品数据</td></tr>';
        // 重置选择状态
        const selectAllCheckbox = document.getElementById('selectAllItems');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        }
        updateBatchDeleteButton();
        return;
    }

    const itemsHtml = items.map(item => {
        // 处理商品标题显示
        let itemTitleDisplay = item.item_title || '未设置';
        if (itemTitleDisplay.length > 30) {
            itemTitleDisplay = itemTitleDisplay.substring(0, 30) + '...';
        }

        // 处理商品详情显示
        let itemDetailDisplay = '未设置';
        if (item.item_detail) {
            try {
                // 尝试解析JSON并提取有用信息
                const detail = JSON.parse(item.item_detail);
                if (detail.content) {
                    itemDetailDisplay = detail.content.substring(0, 50) + (detail.content.length > 50 ? '...' : '');
                } else {
                    // 如果是纯文本或其他格式，直接显示前50个字符
                    itemDetailDisplay = item.item_detail.substring(0, 50) + (item.item_detail.length > 50 ? '...' : '');
                }
            } catch (e) {
                // 如果不是JSON格式，直接显示前50个字符
                itemDetailDisplay = item.item_detail.substring(0, 50) + (item.item_detail.length > 50 ? '...' : '');
            }
        }

        // 多规格状态显示
        const isMultiSpec = item.is_multi_spec;
        const multiSpecDisplay = isMultiSpec ?
            '<span class="badge bg-success">多规格</span>' :
            '<span class="badge bg-secondary">普通</span>';

        return `
            <tr>
            <td>
                <input type="checkbox" name="itemCheckbox"
                        data-cookie-id="${escapeHtml(item.cookie_id)}"
                        data-item-id="${escapeHtml(item.item_id)}"
                        onchange="updateSelectAllState()">
            </td>
            <td>${escapeHtml(item.cookie_id)}</td>
            <td>${escapeHtml(item.item_id)}</td>
            <td title="${escapeHtml(item.item_title || '未设置')}">${escapeHtml(itemTitleDisplay)}</td>
            <td title="${escapeHtml(item.item_detail || '未设置')}">${escapeHtml(itemDetailDisplay)}</td>
            <td>${multiSpecDisplay}</td>
            <td>${formatDateTime(item.updated_at)}</td>
            <td>
                <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-primary" onclick="editItem('${escapeHtml(item.cookie_id)}', '${escapeHtml(item.item_id)}')" title="编辑详情">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteItem('${escapeHtml(item.cookie_id)}', '${escapeHtml(item.item_id)}', '${escapeHtml(item.item_title || item.item_id)}')" title="删除">
                    <i class="bi bi-trash"></i>
                </button>
                <button class="btn btn-sm ${isMultiSpec ? 'btn-warning' : 'btn-success'}" onclick="toggleItemMultiSpec('${escapeHtml(item.cookie_id)}', '${escapeHtml(item.item_id)}', ${!isMultiSpec})" title="${isMultiSpec ? '关闭多规格' : '开启多规格'}">
                    <i class="bi ${isMultiSpec ? 'bi-toggle-on' : 'bi-toggle-off'}"></i>
                </button>
                </div>
            </td>
            </tr>
        `;
    }).join('');

    // 更新表格内容
    tbody.innerHTML = itemsHtml;

    // 重置选择状态
    const selectAllCheckbox = document.getElementById('selectAllItems');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    updateBatchDeleteButton();
}

// 刷新商品列表
export async function refreshItems() {
    await refreshItemsData();
    showToast('商品列表已刷新', 'success');
}

// 获取商品信息（按页获取）
export async function getAllItemsFromAccount() {
    const cookieSelect = document.getElementById('itemCookieFilter');
    const selectedCookieId = cookieSelect.value;
    const pageNumber = parseInt(document.getElementById('pageNumber').value) || 1;

    if (!selectedCookieId) {
        showToast('请先选择一个账号', 'warning');
        return;
    }

    if (pageNumber < 1) {
        showToast('页码必须大于0', 'warning');
        return;
    }

    // 显示加载状态
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>获取中...';
    button.disabled = true;

    try {
        const response = await fetch(`${apiBase}/items/get-by-page`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                cookie_id: selectedCookieId,
                page_number: pageNumber,
                page_size: 20
            })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showToast(`成功获取第${pageNumber}页 ${data.current_count} 个商品，请查看控制台日志`, 'success');
                // 刷新商品列表（保持筛选器选择）
                await refreshItemsData();
            } else {
                showToast(data.message || '获取商品信息失败', 'danger');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('获取商品信息失败:', error);
        showToast('获取商品信息失败', 'danger');
    } finally {
        // 恢复按钮状态
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// 获取所有页商品信息
export async function getAllItemsFromAccountAll() {
    const cookieSelect = document.getElementById('itemCookieFilter');
    const selectedCookieId = cookieSelect.value;

    if (!selectedCookieId) {
        showToast('请先选择一个账号', 'warning');
        return;
    }

    // 显示加载状态
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>获取中...';
    button.disabled = true;

    try {
        const response = await fetch(`${apiBase}/items/get-all-from-account`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                cookie_id: selectedCookieId
            })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const message = data.total_pages ?
                    `成功获取 ${data.total_count} 个商品（共${data.total_pages}页），请查看控制台日志` :
                    `成功获取商品信息，请查看控制台日志`;
                showToast(message, 'success');
                // 刷新商品列表（保持筛选器选择）
                await refreshItemsData();
            } else {
                showToast(data.message || '获取商品信息失败', 'danger');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('获取商品信息失败:', error);
        showToast('获取商品信息失败', 'danger');
    } finally {
        // 恢复按钮状态
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// 编辑商品详情
export async function editItem(cookieId, itemId) {
    try {
        const response = await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const item = data.item;

            // 填充表单
            document.getElementById('editItemCookieId').value = item.cookie_id;
            document.getElementById('editItemId').value = item.item_id;
            document.getElementById('editItemCookieIdDisplay').value = item.cookie_id;
            document.getElementById('editItemIdDisplay').value = item.item_id;
            document.getElementById('editItemDetail').value = item.item_detail || '';

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
            modal.show();
        } else {
            throw new Error('获取商品详情失败');
        }
    } catch (error) {
        console.error('获取商品详情失败:', error);
        showToast('获取商品详情失败', 'danger');
    }
}

// 保存商品详情
export async function saveItemDetail() {
    const cookieId = document.getElementById('editItemCookieId').value;
    const itemId = document.getElementById('editItemId').value;
    const itemDetail = document.getElementById('editItemDetail').value.trim();

    if (!itemDetail) {
        showToast('请输入商品详情', 'warning');
        return;
    }

    try {
        const response = await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                item_detail: itemDetail
            })
        });

        if (response.ok) {
            showToast('商品详情更新成功', 'success');

            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('editItemModal'));
            modal.hide();

            // 刷新列表（保持筛选器选择）
            await refreshItemsData();
        } else {
            const error = await response.text();
            showToast(`更新失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('更新商品详情失败:', error);
        showToast('更新商品详情失败', 'danger');
    }
}

// 删除商品信息
export async function deleteItem(cookieId, itemId, itemTitle) {
    try {
        // 确认删除
        const confirmed = confirm(`确定要删除商品信息吗？\n\n商品ID: ${itemId}\n商品标题: ${itemTitle || '未设置'}\n\n此操作不可撤销！`);
        if (!confirmed) {
            return;
        }

        const response = await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            showToast('商品信息删除成功', 'success');
            // 刷新列表（保持筛选器选择）
            await refreshItemsData();
        } else {
            const error = await response.text();
            showToast(`删除失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('删除商品信息失败:', error);
        showToast('删除商品信息失败', 'danger');
    }
}

// 批量删除商品信息
export async function batchDeleteItems() {
    try {
        // 获取所有选中的复选框
        const checkboxes = document.querySelectorAll('input[name="itemCheckbox"]:checked');
        if (checkboxes.length === 0) {
            showToast('请选择要删除的商品', 'warning');
            return;
        }

        // 确认删除
        const confirmed = confirm(`确定要删除选中的 ${checkboxes.length} 个商品信息吗？\n\n此操作不可撤销！`);
        if (!confirmed) {
            return;
        }

        // 构造删除列表
        const itemsToDelete = Array.from(checkboxes).map(checkbox => {
            const row = checkbox.closest('tr');
            return {
                cookie_id: checkbox.dataset.cookieId,
                item_id: checkbox.dataset.itemId
            };
        });

        const response = await fetch(`${apiBase}/items/batch`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ items: itemsToDelete })
        });

        if (response.ok) {
            const result = await response.json();
            showToast(`批量删除完成: 成功 ${result.success_count} 个，失败 ${result.failed_count} 个`, 'success');
            // 刷新列表（保持筛选器选择）
            await refreshItemsData();
        } else {
            const error = await response.text();
            showToast(`批量删除失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('批量删除商品信息失败:', error);
        showToast('批量删除商品信息失败', 'danger');
    }
}

// 全选/取消全选
export function toggleSelectAll(selectAllCheckbox) {
    const checkboxes = document.querySelectorAll('input[name="itemCheckbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    updateBatchDeleteButton();
}

// 更新全选状态
export function updateSelectAllState() {
    const checkboxes = document.querySelectorAll('input[name="itemCheckbox"]');
    const checkedCheckboxes = document.querySelectorAll('input[name="itemCheckbox"]:checked');
    const selectAllCheckbox = document.getElementById('selectAllItems');

    if (checkboxes.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCheckboxes.length === checkboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCheckboxes.length > 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }

    updateBatchDeleteButton();
}

// 更新批量删除按钮状态
export function updateBatchDeleteButton() {
    const checkedCheckboxes = document.querySelectorAll('input[name="itemCheckbox"]:checked');
    const batchDeleteBtn = document.getElementById('batchDeleteBtn');

    if (checkedCheckboxes.length > 0) {
        batchDeleteBtn.disabled = false;
        batchDeleteBtn.innerHTML = `<i class="bi bi-trash"></i> 批量删除 (${checkedCheckboxes.length})`;
    } else {
        batchDeleteBtn.disabled = true;
        batchDeleteBtn.innerHTML = '<i class="bi bi-trash"></i> 批量删除';
    }
}

// 加载商品列表（用于自动回复页面的商品选择下拉框）
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
                // 清空现有选项（保留第一个默认选项）
                selectElement.innerHTML = '<option value="">选择商品或留空表示通用关键词</option>';

                // 添加商品选项
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

// 加载商品列表（用于图片关键词选择商品）
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

            // 更新商品选择下拉框
            const selectElement = document.getElementById('imageKeywordItemSelect');
            if (selectElement) {
                // 清空现有选项
                selectElement.innerHTML = '<option value="">选择商品或留空表示通用图片关键词</option>';

                // 添加商品选项
                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.item_id;
                    option.textContent = `${item.item_id} - ${item.item_title}`;
                    selectElement.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载商品列表时发生错误:', error);
    }
}
