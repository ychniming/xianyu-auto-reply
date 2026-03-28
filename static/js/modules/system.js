// 系统管理模块 - 系统配置、备份、缓存管理相关函数
import { apiBase, authToken, clearKeywordCache } from './utils.js';
import { toggleLoading, showToast } from './api.js';

// 加载表格数据（支持多种类型）
export async function loadTableData(tableType) {
    toggleLoading(true);

    try {
        switch (tableType) {
            case 'accounts':
                await loadAccountsTable();
                break;
            case 'keywords':
                await loadKeywordsTable();
                break;
            case 'logs':
                await loadLogsTable();
                break;
            case 'ai':
                await loadAITable();
                break;
            case 'delivery':
                await loadDeliveryTable();
                break;
            default:
                console.warn(`Unknown table type: ${tableType}`);
        }
    } catch (error) {
        console.error(`加载 ${tableType} 表格数据失败:`, error);
        showToast(`加载数据失败`, 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 刷新表格数据
export async function refreshTableData(tableType) {
    await loadTableData(tableType);
    showToast(`${getTableName(tableType)}数据已刷新`, 'success');
}

// 获取表格名称
export function getTableName(tableType) {
    const names = {
        'accounts': '账号',
        'keywords': '关键词',
        'logs': '日志',
        'ai': 'AI配置',
        'delivery': '发货规则'
    };
    return names[tableType] || tableType;
}

// 确认删除操作
export function confirmDelete(deleteType, itemId, itemName) {
    if (!confirm(`确定要删除 ${itemName} 吗？此操作不可恢复。`)) {
        return false;
    }
    return true;
}

// 确认删除所有操作
export function confirmDeleteAll(deleteType) {
    const messages = {
        'keywords': '确定要删除所有关键词吗？此操作不可恢复。',
        'cookies': '确定要删除所有Cookie吗？此操作不可恢复。',
        'logs': '确定要清空所有日志吗？此操作不可恢复。'
    };

    const message = messages[deleteType] || `确定要删除所有 ${deleteType} 吗？此操作不可恢复。`;

    if (!confirm(message)) {
        return false;
    }
    return true;
}

// 下载数据库备份
export async function downloadDatabaseBackup() {
    try {
        showToast('正在准备数据库备份...', 'info');

        const response = await fetch(`${apiBase}/admin/backup/download`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (response.ok) {
            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `xianyu_backup_${new Date().toISOString().slice(0, 10)}.db`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match) filename = match[1];
            }

            // 下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            showToast('数据库备份下载成功', 'success');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('下载数据库备份失败:', error);
        showToast('下载数据库备份失败', 'danger');
    }
}

// 上传数据库备份
export async function uploadDatabaseBackup() {
    const fileInput = document.getElementById('backupFileInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast('请选择备份文件', 'warning');
        return false;
    }

    const file = fileInput.files[0];

    // 验证文件类型
    if (!file.name.endsWith('.db') && !file.name.endsWith('.sqlite')) {
        showToast('请选择 .db 或 .sqlite 格式的备份文件', 'warning');
        return false;
    }

    // 确认操作
    if (!confirm('确定要上传备份文件吗？这将覆盖当前数据库。')) {
        return false;
    }

    try {
        showToast('正在上传备份文件...', 'info');

        const formData = new FormData();
        formData.append('backup', file);

        const response = await fetch(`${apiBase}/admin/backup/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showToast('数据库备份上传成功，系统将重新加载...', 'success');
                // 重新加载页面以应用新数据
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
                return true;
            } else {
                showToast(data.message || '上传失败', 'danger');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('上传数据库备份失败:', error);
        showToast('上传数据库备份失败', 'danger');
    }

    return false;
}

// 重新加载系统缓存
export async function reloadSystemCache() {
    try {
        const response = await fetch(`${apiBase}/system/reload-cache`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // 清除本地关键词缓存
                clearKeywordCache();

                showToast('系统缓存已重新加载', 'success');
                return true;
            } else {
                showToast(data.message || '重载失败', 'danger');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('重新加载系统缓存失败:', error);
        showToast('重新加载系统缓存失败', 'danger');
    }

    return false;
}

// 刷新二维码（系统管理中的二维码刷新功能）
export async function refreshQRCode() {
    // 触发 auth 模块中的刷新函数
    const { refreshQRCode: authRefreshQRCode } = await import('./auth.js');
    if (authRefreshQRCode) {
        authRefreshQRCode();
    }
}

// 切换维护模式
export async function toggleMaintenanceMode(enabled) {
    try {
        const response = await fetch(`${apiBase}/api/health`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (response.ok) {
            showToast(`维护模式切换已准备${enabled ? '开启' : '关闭'}（功能开发中）`, 'info');
            return true;
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('切换维护模式失败:', error);
        showToast('切换维护模式失败', 'danger');
    }

    return false;
}

// 获取系统状态
export async function getSystemStatus() {
    try {
        const response = await fetch(`${apiBase}/api/info`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            return {
                version: data.version || '1.0.0',
                uptime: 'N/A',
                last_update: new Date().toLocaleString('zh-CN'),
                cpu_usage: 0,
                memory_usage: 0,
                disk_usage: 0,
                active_accounts: 0,
                websocket_connected: false,
                maintenance_mode: false
            };
        }
    } catch (error) {
        console.error('获取系统状态失败:', error);
    }

    return null;
}

// 显示系统信息
export async function showSystemInfo() {
    const status = await getSystemStatus();
    if (!status) {
        showToast('获取系统信息失败', 'danger');
        return;
    }

    const infoHtml = `
        <div class="row">
            <div class="col-md-6">
                <h6>系统信息</h6>
                <ul class="list-unstyled">
                    <li>版本: <strong>${status.version || '未知'}</strong></li>
                    <li>运行时间: <strong>${status.uptime || '未知'}</strong></li>
                    <li>最后更新: <strong>${status.last_update || '未知'}</strong></li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>资源使用</h6>
                <ul class="list-unstyled">
                    <li>CPU: <strong>${status.cpu_usage || '0'}%</strong></li>
                    <li>内存: <strong>${status.memory_usage || '0'}%</strong></li>
                    <li>磁盘: <strong>${status.disk_usage || '0'}%</strong></li>
                </ul>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <h6>连接状态</h6>
                <ul class="list-unstyled">
                    <li>活跃账号: <strong>${status.active_accounts || 0}</strong></li>
                    <li>WebSocket: <strong>${status.websocket_connected ? '已连接' : '未连接'}</strong></li>
                    <li>维护模式: <strong>${status.maintenance_mode ? '开启' : '关闭'}</strong></li>
                </ul>
            </div>
        </div>
    `;

    // 显示模态框
    const modalHtml = `
        <div class="modal fade" id="systemInfoModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">系统信息</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${infoHtml}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 移除旧的模态框
    const oldModal = document.getElementById('systemInfoModal');
    if (oldModal) oldModal.remove();

    // 添加新的模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('systemInfoModal'));
    modal.show();
}

// 辅助函数：加载账号表格
async function loadAccountsTable() {
    // 触发 cookies 模块的加载函数
    if (typeof loadCookies === 'function') {
        await loadCookies();
    }
}

// 辅助函数：加载关键词表格
async function loadKeywordsTable() {
    // 触发 keywords 模块的加载函数
    if (typeof loadKeywords === 'function') {
        await loadKeywords();
    }
}

// 辅助函数：加载日志表格
async function loadLogsTable() {
    // 触发 dashboard 模块的刷新函数
    if (typeof refreshLogs === 'function') {
        await refreshLogs();
    }
}

// 辅助函数：加载AI配置表格
async function loadAITable() {
    // 触发 ai 模块的加载函数
    if (typeof loadAIReplySettings === 'function') {
        loadAIReplySettings();
    }
}

// 辅助函数：加载发货规则表格
async function loadDeliveryTable() {
    // 触发 cards 模块的加载函数
    if (typeof loadDeliveryRules === 'function') {
        await loadDeliveryRules();
    }
}


