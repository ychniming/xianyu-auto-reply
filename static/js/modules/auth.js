// 认证模块 - 认证相关函数和 Token 管理
import { authToken, updateAuthToken } from './utils.js';

// 检查认证状态
export async function checkAuth() {
    if (!authToken.value) {
        window.location.href = '/';
        return false;
    }

    try {
        // window.API.auth.verify() 返回的已经是 data 部分
        const data = await window.API.auth.verify();

        if (!data || !data.authenticated) {
            localStorage.removeItem('auth_token');
            updateAuthToken(null);
            window.location.href = '/';
            return false;
        }

        // 检查是否为管理员，显示管理员菜单和功能
        if (data.username === 'admin') {
            const adminMenuSection = document.getElementById('adminMenuSection');
            if (adminMenuSection) {
                adminMenuSection.style.display = 'block';
            }

            // 显示备份管理功能
            const backupManagement = document.getElementById('backup-management');
            if (backupManagement) {
                backupManagement.style.display = 'block';
            }
        }

        return true;
    } catch (err) {
        localStorage.removeItem('auth_token');
        updateAuthToken(null);
        window.location.href = '/';
        return false;
    }
}

// 登出功能
export async function logout() {
    try {
        if (authToken.value) {
            await window.API.auth.logout();
        }
        localStorage.removeItem('auth_token');
        updateAuthToken(null);
        window.location.href = '/';
    } catch (err) {
        console.error('登出失败:', err);
        localStorage.removeItem('auth_token');
        updateAuthToken(null);
        window.location.href = '/';
    }
}

// ==================== 扫码登录相关函数 ====================

const MAX_QR_POLL_COUNT = 150;
const QR_POLL_INTERVAL = 2000;

function isValidUrl(urlString) {
    if (!urlString || typeof urlString !== 'string') return false;
    try {
        const url = new URL(urlString);
        return url.protocol === 'https:' && url.hostname.includes('taobao.com') || url.hostname.includes('alibaba.com') || url.hostname.includes('goofish.com');
    } catch {
        return false;
    }
}

let qrCodeCheckInterval = null;
let qrCodeSessionId = null;
let qrPollCount = 0;

// 显示扫码登录模态框
export function showQRCodeLogin() {
    const modal = new bootstrap.Modal(document.getElementById('qrCodeLoginModal'));
    modal.show();

    // 模态框显示后生成二维码
    modal._element.addEventListener('shown.bs.modal', function () {
        generateQRCode();
    });

    // 模态框关闭时清理定时器
    modal._element.addEventListener('hidden.bs.modal', function () {
        clearQRCodeCheck();
    });
}

// 切换手动输入表单显示/隐藏
export function toggleManualInput() {
    const manualForm = document.getElementById('manualInputForm');
    if (manualForm.style.display === 'none') {
        manualForm.style.display = 'block';
        // 清空表单
        document.getElementById('addForm').reset();
    } else {
        manualForm.style.display = 'none';
    }
}

// 刷新二维码（兼容旧函数名）
export async function refreshQRCode() {
    await generateQRCode();
}

// 生成二维码
export async function generateQRCode() {
    try {
        showQRCodeLoading();

        const response = await window.API.qrLogin.generate();

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                qrCodeSessionId = data.session_id;
                showQRCodeImage(data.qr_code_url);
                startQRCodeCheck();
            } else {
                showQRCodeError(data.message || '生成二维码失败');
            }
        } else {
            showQRCodeError('生成二维码失败');
        }
    } catch (error) {
        console.error('生成二维码失败:', error);
        showQRCodeError('网络错误，请重试');
    }
}

// 显示二维码加载状态
export function showQRCodeLoading() {
    document.getElementById('qrCodeContainer').style.display = 'block';
    document.getElementById('qrCodeImage').style.display = 'none';
    document.getElementById('statusText').textContent = '正在生成二维码，请耐心等待...';
    document.getElementById('statusSpinner').style.display = 'none';

    // 隐藏验证容器
    const verificationContainer = document.getElementById('verificationContainer');
    if (verificationContainer) {
        verificationContainer.style.display = 'none';
    }
}

// 显示二维码图片
export function showQRCodeImage(qrCodeUrl) {
    document.getElementById('qrCodeContainer').style.display = 'none';
    document.getElementById('qrCodeImage').style.display = 'block';
    document.getElementById('qrCodeImg').src = qrCodeUrl;
    document.getElementById('statusText').textContent = '等待扫码...';
    document.getElementById('statusSpinner').style.display = 'none';
}

// 显示二维码错误
export function showQRCodeError(message) {
    document.getElementById('qrCodeContainer').innerHTML = `
    <div class="text-danger">
        <i class="bi bi-exclamation-triangle fs-1 mb-3"></i>
        <p>${message}</p>
    </div>
    `;
    document.getElementById('qrCodeImage').style.display = 'none';
    document.getElementById('statusText').textContent = '生成失败';
    document.getElementById('statusSpinner').style.display = 'none';
}

// 开始检查二维码状态
export function startQRCodeCheck() {
    if (qrCodeCheckInterval) {
        clearInterval(qrCodeCheckInterval);
    }

    qrPollCount = 0;

    document.getElementById('statusSpinner').style.display = 'inline-block';
    document.getElementById('statusText').textContent = '等待扫码...';

    qrCodeCheckInterval = setInterval(checkQRCodeStatus, QR_POLL_INTERVAL);
}

// 检查二维码状态
export async function checkQRCodeStatus() {
    if (!qrCodeSessionId) return;

    qrPollCount++;

    if (qrPollCount >= MAX_QR_POLL_COUNT) {
        clearQRCodeCheck();
        showQRCodeError('登录超时，请刷新页面重试');
        return;
    }

    try {
        const response = await window.API.qrLogin.checkStatus(qrCodeSessionId);

        if (response.ok) {
            const data = await response.json();

            switch (data.status) {
                case 'waiting':
                    document.getElementById('statusText').textContent = '等待扫码...';
                    break;
                case 'scanned':
                    document.getElementById('statusText').textContent = '已扫码，请在手机上确认...';
                    break;
                case 'success':
                    document.getElementById('statusText').textContent = '登录成功！';
                    document.getElementById('statusSpinner').style.display = 'none';
                    clearQRCodeCheck();
                    handleQRCodeSuccess(data);
                    break;
                case 'expired':
                    document.getElementById('statusText').textContent = '二维码已过期';
                    document.getElementById('statusSpinner').style.display = 'none';
                    clearQRCodeCheck();
                    showQRCodeError('二维码已过期，请刷新重试');
                    break;
                case 'cancelled':
                    document.getElementById('statusText').textContent = '用户取消登录';
                    document.getElementById('statusSpinner').style.display = 'none';
                    clearQRCodeCheck();
                    break;
                case 'verification_required':
                    document.getElementById('statusText').textContent = '需要手机验证';
                    document.getElementById('statusSpinner').style.display = 'inline-block';
                    showVerificationRequired(data);
                    break;
            }
        } else {
            console.warn(`检查状态请求失败: HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('检查二维码状态失败:', error);
        if (qrPollCount >= Math.floor(MAX_QR_POLL_COUNT / 3)) {
            clearQRCodeCheck();
            showQRCodeError('网络错误，请检查网络连接后刷新重试');
        }
    }
}

// 显示需要验证的提示
export function showVerificationRequired(data) {
    if (!data.verification_url) {
        showQRCodeError('验证信息无效，请刷新重试');
        return;
    }

    if (!isValidUrl(data.verification_url)) {
        showQRCodeError('验证链接无效，请刷新重试');
        return;
    }

    // 隐藏二维码区域
    document.getElementById('qrCodeContainer').style.display = 'none';
    document.getElementById('qrCodeImage').style.display = 'none';

    const safeUrl = data.verification_url;

    // 显示验证提示
    const verificationHtml = `
        <div class="text-center">
        <div class="mb-4">
            <i class="bi bi-shield-exclamation text-warning" style="font-size: 4rem;"></i>
        </div>
        <h5 class="text-warning mb-3">账号需要手机验证</h5>
        <div class="alert alert-warning border-0 mb-4">
            <i class="bi bi-info-circle me-2"></i>
            <strong>检测到账号存在风控，需要进行手机验证才能完成登录</strong>
        </div>
        <div class="mb-4">
            <p class="text-muted mb-3">请点击下方按钮，在新窗口中完成手机验证：</p>
            <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-warning btn-lg">
            <i class="bi bi-phone me-2"></i>
            打开手机验证页面
            </a>
        </div>
        <div class="alert alert-info border-0">
            <i class="bi bi-lightbulb me-2"></i>
            <small>
            <strong>验证步骤：</strong><br>
            1. 点击上方按钮打开验证页面<br>
            2. 按照页面提示完成手机验证<br>
            3. 验证完成后，点击下方按钮继续登录
            </small>
        </div>
        <div class="mt-3">
            <button onclick="continueAfterVerification()" class="btn btn-success">
            <i class="bi bi-check-circle me-2"></i>
            验证完成，继续登录
            </button>
        </div>
        </div>
    `;

    // 创建验证提示容器
    let verificationContainer = document.getElementById('verificationContainer');
    if (!verificationContainer) {
        verificationContainer = document.createElement('div');
        verificationContainer.id = 'verificationContainer';
        document.querySelector('#qrCodeLoginModal .modal-body').appendChild(verificationContainer);
    }

    verificationContainer.innerHTML = verificationHtml;
    verificationContainer.style.display = 'block';

        // 显示Toast提示
        window.App.showToast('账号需要手机验证，请按照提示完成验证', 'warning');
    }
}

// 验证完成后继续登录
export function continueAfterVerification() {
    // 隐藏验证容器
    const verificationContainer = document.getElementById('verificationContainer');
    if (verificationContainer) {
        verificationContainer.style.display = 'none';
    }

    // 显示检查状态
    document.getElementById('statusText').textContent = '正在检查登录状态...';
    document.getElementById('statusSpinner').style.display = 'inline-block';

    // 继续轮询检查状态
    startQRCodeCheck();

    window.App.showToast('正在检查登录状态...', 'info');
}

// 处理扫码成功
export function handleQRCodeSuccess(data) {
    if (data.account_info) {
        const { account_id, is_new_account } = data.account_info;

        if (is_new_account) {
            window.App.showToast(`新账号添加成功！账号ID: ${account_id}`, 'success');
        } else {
            window.App.showToast(`账号Cookie已更新！账号ID: ${account_id}`, 'success');
        }

        // 关闭模态框
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('qrCodeLoginModal'));
            modal.hide();

            // 刷新账号列表
            if (typeof loadCookies === 'function') {
                loadCookies();
            }
        }, 2000);
    }
}

// 清理二维码检查
export function clearQRCodeCheck() {
    if (qrCodeCheckInterval) {
        clearInterval(qrCodeCheckInterval);
        qrCodeCheckInterval = null;
    }
    qrCodeSessionId = null;
}

