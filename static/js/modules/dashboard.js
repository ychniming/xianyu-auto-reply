// 仪表盘模块 - 仪表盘和日志相关函数
import { apiBase, authToken, dashboardData, clearKeywordCache } from './utils.js';
import { showToast, toggleLoading, fetchJSON, getLogsAPI, clearLogsAPI, getLogStatsAPI } from './api.js';

// 加载仪表盘数据
export async function loadDashboard() {
    try {
        toggleLoading(true);

        // 获取账号列表
        const cookiesResponse = await fetch(`${apiBase}/cookies/details`, {
            headers: {
                'Authorization': `Bearer ${authToken.value}`
            }
        });

        if (cookiesResponse.ok) {
            const cookiesData = await cookiesResponse.json();
            const accounts = cookiesData.data || cookiesData;

            // 为每个账号获取关键词信息
            const accountsWithKeywords = await Promise.all(
                accounts.map(async (account) => {
                    try {
                        const keywordsResponse = await fetch(`${apiBase}/keywords/${account.id}`, {
                            headers: {
                                'Authorization': `Bearer ${authToken.value}`
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
                                keywords: [],
                                keywordCount: 0
                            };
                        }
                    } catch (error) {
                        console.error(`获取账号 ${account.id} 关键词失败:`, error);
                        return {
                            ...account,
                            keywords: [],
                            keywordCount: 0
                        };
                    }
                })
            );

            dashboardData.accounts = accountsWithKeywords;

            // 计算统计数据
            let totalKeywords = 0;
            let activeAccounts = 0;
            let enabledAccounts = 0;

            accountsWithKeywords.forEach(account => {
                const keywordCount = account.keywordCount || 0;
                const isEnabled = account.enabled === undefined ? true : account.enabled;

                if (isEnabled) {
                    enabledAccounts++;
                    totalKeywords += keywordCount;
                    if (keywordCount > 0) {
                        activeAccounts++;
                    }
                }
            });

            dashboardData.totalKeywords = totalKeywords;

            // 更新仪表盘显示
            updateDashboardStats(accountsWithKeywords.length, totalKeywords, enabledAccounts);
            updateDashboardAccountsList(accountsWithKeywords);
        }
    } catch (error) {
        console.error('加载仪表盘数据失败:', error);
        showToast('加载仪表盘数据失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 更新仪表盘统计数据
export function updateDashboardStats(totalAccounts, totalKeywords, enabledAccounts) {
    document.getElementById('totalAccounts').textContent = totalAccounts;
    document.getElementById('totalKeywords').textContent = totalKeywords;
    document.getElementById('activeAccounts').textContent = enabledAccounts;
}

// 更新仪表盘账号列表
export function updateDashboardAccountsList(accounts) {
    const tbody = document.getElementById('dashboardAccountsList');
    tbody.innerHTML = '';

    if (accounts.length === 0) {
        tbody.innerHTML = `
            <tr>
            <td colspan="4" class="text-center text-muted py-4">
                <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                暂无账号数据
            </td>
            </tr>
        `;
        return;
    }

    accounts.forEach(account => {
        const keywordCount = account.keywordCount || 0;
        const isEnabled = account.enabled === undefined ? true : account.enabled;

        let status = '';
        if (!isEnabled) {
            status = '<span class="badge bg-danger">已禁用</span>';
        } else if (keywordCount > 0) {
            status = '<span class="badge bg-success">活跃</span>';
        } else {
            status = '<span class="badge bg-secondary">未配置</span>';
        }

        const row = document.createElement('tr');
        row.className = isEnabled ? '' : 'table-secondary';
        row.innerHTML = `
            <td>
            <strong class="text-primary ${!isEnabled ? 'text-muted' : ''}">${account.id}</strong>
            ${!isEnabled ? '<i class="bi bi-pause-circle-fill text-danger ms-1" title="已禁用"></i>' : ''}
            </td>
            <td>
            <span class="badge ${isEnabled ? 'bg-primary' : 'bg-secondary'}">${keywordCount} 个关键词</span>
            </td>
            <td>${status}</td>
            <td>
            <small class="text-muted">${new Date().toLocaleString()}</small>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ==================== 日志管理功能 ====================

// 刷新日志
export async function refreshLogs() {
    try {
        const lines = document.getElementById('logLines').value;

        const response = await getLogsAPI(lines);

        window.allLogs = response.logs || [];
        window.filteredLogs = window.allLogs;
        displayLogs();
        updateLogStats();
        showToast('日志已刷新', 'success');
    } catch (error) {
        console.error('刷新日志失败:', error);
        showToast('刷新日志失败', 'danger');
    }
}

// 显示日志
export function displayLogs() {
    const container = document.getElementById('logContainer');

    if (window.filteredLogs.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4 text-muted">
            <i class="bi bi-file-text fs-1"></i>
            <p class="mt-2">暂无日志数据</p>
            </div>
        `;
        return;
    }

    const logsHtml = window.filteredLogs.map(log => {
        const timestamp = formatLogTimestamp(log.timestamp);
        const levelClass = log.level || 'INFO';

        return `
            <div class="log-entry ${levelClass}">
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level">[${log.level}]</span>
            <span class="log-source">${log.source}:</span>
            <span class="log-message">${escapeHtml(log.message)}</span>
            </div>
        `;
    }).join('');

    container.innerHTML = logsHtml;

    // 滚动到底部
    container.scrollTop = container.scrollHeight;
}

// 格式化日志时间戳
export function formatLogTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
    });
}

// 更新日志统计信息
export function updateLogStats() {
    document.getElementById('logCount').textContent = `${window.filteredLogs.length} 条日志`;
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString('zh-CN');
}

// 清空日志显示
export function clearLogsDisplay() {
    window.allLogs = [];
    window.filteredLogs = [];
    document.getElementById('logContainer').innerHTML = `
        <div class="text-center p-4 text-muted">
        <i class="bi bi-file-text fs-1"></i>
        <p class="mt-2">日志显示已清空</p>
        </div>
    `;
    updateLogStats();
    showToast('日志显示已清空', 'info');
}

// 切换自动刷新
export function toggleAutoRefresh() {
    const button = document.querySelector('#autoRefreshText');
    const icon = button.previousElementSibling;

    if (window.autoRefreshInterval) {
        // 停止自动刷新
        clearInterval(window.autoRefreshInterval);
        window.autoRefreshInterval = null;
        button.textContent = '开启自动刷新';
        icon.className = 'bi bi-play-circle me-1';
        showToast('自动刷新已停止', 'info');
    } else {
        // 开启自动刷新
        window.autoRefreshInterval = setInterval(refreshLogs, 5000); // 每5秒刷新一次
        button.textContent = '停止自动刷新';
        icon.className = 'bi bi-pause-circle me-1';
        showToast('自动刷新已开启（每5秒）', 'success');

        // 立即刷新一次
        refreshLogs();
    }
}

// 清空服务器日志
export async function clearLogsServer() {
    if (!confirm('确定要清空服务器端的所有日志吗？此操作不可恢复！')) {
        return;
    }

    try {
        const response = await clearLogsAPI();

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                window.allLogs = [];
                window.filteredLogs = [];
                displayLogs();
                updateLogStats();
                showToast('服务器日志已清空', 'success');
            } else {
                showToast(data.message || '清空失败', 'danger');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('清空服务器日志失败:', error);
        showToast('清空服务器日志失败', 'danger');
    }
}

// 显示日志统计信息
export async function showLogStats() {
    try {
        const response = await getLogStatsAPI();

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const stats = data.stats;

                let statsHtml = `
                    <div class="row">
                    <div class="col-md-6">
                        <h6>总体统计</h6>
                        <ul class="list-unstyled">
                        <li>总日志数: <strong>${stats.total_logs}</strong></li>
                        <li>最大容量: <strong>${stats.max_capacity}</strong></li>
                        <li>使用率: <strong>${((stats.total_logs / stats.max_capacity) * 100).toFixed(1)}%</strong></li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>级别分布</h6>
                        <ul class="list-unstyled">
                `;

                for (const [level, count] of Object.entries(stats.level_counts || {})) {
                    const percentage = ((count / stats.total_logs) * 100).toFixed(1);
                    statsHtml += `<li>${level}: <strong>${count}</strong> (${percentage}%)</li>`;
                }

                statsHtml += `
                        </ul>
                    </div>
                    </div>
                    <div class="row mt-3">
                    <div class="col-12">
                        <h6>来源分布</h6>
                        <div class="row">
                `;

                const sources = Object.entries(stats.source_counts || {});
                sources.forEach(([source, count], index) => {
                    if (index % 2 === 0) statsHtml += '<div class="col-md-6"><ul class="list-unstyled">';
                    const percentage = ((count / stats.total_logs) * 100).toFixed(1);
                    statsHtml += `<li>${source}: <strong>${count}</strong> (${percentage}%)</li>`;
                    if (index % 2 === 1 || index === sources.length - 1) statsHtml += '</ul></div>';
                });

                statsHtml += `
                        </div>
                    </div>
                    </div>
                `;

                // 显示模态框
                const modalHtml = `
                    <div class="modal fade" id="logStatsModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">日志统计信息</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${statsHtml}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                        </div>
                    </div>
                    </div>
                `;

                // 移除旧的模态框
                const oldModal = document.getElementById('logStatsModal');
                if (oldModal) oldModal.remove();

                // 添加新的模态框
                document.body.insertAdjacentHTML('beforeend', modalHtml);

                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('logStatsModal'));
                modal.show();

            } else {
                showToast(data.message || '获取统计信息失败', 'danger');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('获取日志统计失败:', error);
        showToast('获取日志统计失败', 'danger');
    }
}

// HTML转义函数
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
