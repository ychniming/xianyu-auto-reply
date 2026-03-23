// 卡券管理模块 - 卡券管理相关函数
import { apiBase, authToken } from './utils.js';
import { showToast, toggleLoading } from './api.js';

// 加载卡券列表
export async function loadCards() {
    try {
        const response = await fetch(`${apiBase}/cards`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const cards = await response.json();
            renderCardsList(cards);
            updateCardsStats(cards);
        } else {
            showToast('加载卡券列表失败', 'danger');
        }
    } catch (error) {
        console.error('加载卡券列表失败:', error);
        showToast('加载卡券列表失败', 'danger');
    }
}

// 渲染卡券列表
export function renderCardsList(cards) {
    const tbody = document.getElementById('cardsTableBody');

    if (cards.length === 0) {
        tbody.innerHTML = `
            <tr>
            <td colspan="8" class="text-center py-4 text-muted">
                <i class="bi bi-credit-card fs-1 d-block mb-3"></i>
                <h5>暂无卡券数据</h5>
                <p class="mb-0">点击"添加卡券"开始创建您的第一个卡券</p>
            </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = '';

    cards.forEach(card => {
        const tr = document.createElement('tr');

        // 类型标签
        let typeBadge = '';
        switch(card.type) {
            case 'api':
                typeBadge = '<span class="badge bg-info">API接口</span>';
                break;
            case 'text':
                typeBadge = '<span class="badge bg-success">固定文字</span>';
                break;
            case 'data':
                typeBadge = '<span class="badge bg-warning">批量数据</span>';
                break;
            case 'image':
                typeBadge = '<span class="badge bg-primary">图片</span>';
                break;
        }

        // 状态标签
        const statusBadge = card.enabled ?
            '<span class="badge bg-success">启用</span>' :
            '<span class="badge bg-secondary">禁用</span>';

        // 数据量显示
        let dataCount = '-';
        if (card.type === 'data' && card.data_content) {
            const lines = card.data_content.split('\n').filter(line => line.trim());
            dataCount = lines.length;
        } else if (card.type === 'api') {
            dataCount = '∞';
        } else if (card.type === 'text') {
            dataCount = '1';
        } else if (card.type === 'image') {
            dataCount = '1';
        }

        // 延时时间显示
        const delayDisplay = card.delay_seconds > 0 ?
            `${card.delay_seconds}秒` :
            '<span class="text-muted">立即</span>';

        // 规格信息显示
        let specDisplay = '<span class="text-muted">普通卡券</span>';
        if (card.is_multi_spec && card.spec_name && card.spec_value) {
            specDisplay = `<span class="badge bg-primary">${card.spec_name}: ${card.spec_value}</span>`;
        }

        tr.innerHTML = `
            <td>
            <div class="fw-bold">${card.name}</div>
            ${card.description ? `<small class="text-muted">${card.description}</small>` : ''}
            </td>
            <td>${typeBadge}</td>
            <td>${specDisplay}</td>
            <td>${dataCount}</td>
            <td>${delayDisplay}</td>
            <td>${statusBadge}</td>
            <td>
            <small class="text-muted">${new Date(card.created_at).toLocaleString('zh-CN')}</small>
            </td>
            <td>
            <div class="btn-group" role="group">
                <button class="btn btn-sm btn-outline-primary" onclick="editCard(${card.id})" title="编辑">
                <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-info" onclick="testCard(${card.id})" title="测试">
                <i class="bi bi-play"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteCard(${card.id})" title="删除">
                <i class="bi bi-trash"></i>
                </button>
            </div>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// 更新卡券统计
export function updateCardsStats(cards) {
    const totalCards = cards.length;
    const apiCards = cards.filter(card => card.type === 'api').length;
    const textCards = cards.filter(card => card.type === 'text').length;
    const dataCards = cards.filter(card => card.type === 'data').length;

    document.getElementById('totalCards').textContent = totalCards;
    document.getElementById('apiCards').textContent = apiCards;
    document.getElementById('textCards').textContent = textCards;
    document.getElementById('dataCards').textContent = dataCards;
}

// 显示添加卡券模态框
export function showAddCardModal() {
    document.getElementById('addCardForm').reset();
    toggleCardTypeFields();
    const modal = new bootstrap.Modal(document.getElementById('addCardModal'));
    modal.show();
}

// 切换卡券类型字段显示
export function toggleCardTypeFields() {
    const cardType = document.getElementById('cardType').value;

    document.getElementById('apiFields').style.display = cardType === 'api' ? 'block' : 'none';
    document.getElementById('textFields').style.display = cardType === 'text' ? 'block' : 'none';
    document.getElementById('dataFields').style.display = cardType === 'data' ? 'block' : 'none';
    document.getElementById('imageFields').style.display = cardType === 'image' ? 'block' : 'none';
}

// 切换多规格字段显示
export function toggleMultiSpecFields() {
    const isMultiSpec = document.getElementById('isMultiSpec').checked;
    document.getElementById('multiSpecFields').style.display = isMultiSpec ? 'block' : 'none';
}

// 初始化卡券图片文件选择器
export function initCardImageFileSelector() {
    const fileInput = document.getElementById('cardImageFile');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!file.type.startsWith('image/')) {
                    showToast('❌ 请选择图片文件，当前文件类型：' + file.type, 'warning');
                    e.target.value = '';
                    hideCardImagePreview();
                    return;
                }

                if (file.size > 5 * 1024 * 1024) {
                    showToast('❌ 图片文件大小不能超过 5MB，当前文件大小：' + (file.size / 1024 / 1024).toFixed(1) + 'MB', 'warning');
                    e.target.value = '';
                    hideCardImagePreview();
                    return;
                }

                validateCardImageDimensions(file, e.target);
            } else {
                hideCardImagePreview();
            }
        });
    }
}

// 验证卡券图片尺寸
export function validateCardImageDimensions(file, inputElement) {
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
            hideCardImagePreview();
            return;
        }

        if (totalPixels > maxPixels) {
            showToast(`❌ 图片像素总数过大：${(totalPixels / 1024 / 1024).toFixed(1)}M像素，最大允许：8M像素`, 'warning');
            inputElement.value = '';
            hideCardImagePreview();
            return;
        }

        showCardImagePreview(file);

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
        hideCardImagePreview();
    };

    img.src = url;
}

// 显示卡券图片预览
export function showCardImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewContainer = document.getElementById('cardImagePreview');
        const previewImg = document.getElementById('cardPreviewImg');

        previewImg.src = e.target.result;
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// 隐藏卡券图片预览
export function hideCardImagePreview() {
    const previewContainer = document.getElementById('cardImagePreview');
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
}

// 初始化编辑卡券图片文件选择器
export function initEditCardImageFileSelector() {
    const fileInput = document.getElementById('editCardImageFile');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!file.type.startsWith('image/')) {
                    showToast('❌ 请选择图片文件，当前文件类型：' + file.type, 'warning');
                    e.target.value = '';
                    hideEditCardImagePreview();
                    return;
                }

                if (file.size > 5 * 1024 * 1024) {
                    showToast('❌ 图片文件大小不能超过 5MB，当前文件大小：' + (file.size / 1024 / 1024).toFixed(1) + 'MB', 'warning');
                    e.target.value = '';
                    hideEditCardImagePreview();
                    return;
                }

                validateEditCardImageDimensions(file, e.target);
            } else {
                hideEditCardImagePreview();
            }
        });
    }
}

// 验证编辑卡券图片尺寸
export function validateEditCardImageDimensions(file, inputElement) {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.onload = function() {
        const width = this.naturalWidth;
        const height = this.naturalHeight;

        URL.revokeObjectURL(url);

        if (width > 4096 || height > 4096) {
            showToast(`❌ 图片尺寸过大（${width}x${height}），最大支持 4096x4096 像素`, 'warning');
            inputElement.value = '';
            hideEditCardImagePreview();
            return;
        }

        showEditCardImagePreview(file);

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
        hideEditCardImagePreview();
    };

    img.src = url;
}

// 显示编辑卡券图片预览
export function showEditCardImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImg = document.getElementById('editCardPreviewImg');
        const previewContainer = document.getElementById('editCardImagePreview');

        if (previewImg && previewContainer) {
            previewImg.src = e.target.result;
            previewContainer.style.display = 'block';
        }
    };
    reader.readAsDataURL(file);
}

// 隐藏编辑卡券图片预览
export function hideEditCardImagePreview() {
    const previewContainer = document.getElementById('editCardImagePreview');
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
}

// 切换编辑多规格字段显示
export function toggleEditMultiSpecFields() {
    const checkbox = document.getElementById('editIsMultiSpec');
    const fieldsDiv = document.getElementById('editMultiSpecFields');

    if (!checkbox || !fieldsDiv) {
        console.error('编辑多规格开关元素未找到');
        return;
    }

    const isMultiSpec = checkbox.checked;
    fieldsDiv.style.display = isMultiSpec ? 'block' : 'none';
}

// 清空添加卡券表单
export function clearAddCardForm() {
    try {
        const setElementValue = (id, value) => {
            const element = document.getElementById(id);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = value;
                } else {
                    element.value = value;
                }
            }
        };

        const setElementDisplay = (id, display) => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = display;
            }
        };

        setElementValue('cardName', '');
        setElementValue('cardType', 'text');
        setElementValue('cardDescription', '');
        setElementValue('cardDelaySeconds', '0');
        setElementValue('isMultiSpec', false);
        setElementValue('specName', '');
        setElementValue('specValue', '');

        setElementDisplay('multiSpecFields', 'none');
        setElementValue('textContent', '');
        setElementValue('dataContent', '');
        setElementValue('apiUrl', '');
        setElementValue('apiMethod', 'GET');
        setElementValue('apiHeaders', '');
        setElementValue('apiParams', '');
        setElementValue('apiTimeout', '10');

        toggleCardTypeFields();
    } catch (error) {
        console.error('清空表单时出错:', error);
    }
}

// 保存卡券
export async function saveCard() {
    try {
        const cardType = document.getElementById('cardType').value;
        const cardName = document.getElementById('cardName').value;

        if (!cardType || !cardName) {
            showToast('请填写必填字段', 'warning');
            return;
        }

        const isMultiSpec = document.getElementById('isMultiSpec').checked;
        const specName = document.getElementById('specName').value;
        const specValue = document.getElementById('specValue').value;

        if (isMultiSpec && (!specName || !specValue)) {
            showToast('多规格卡券必须填写规格名称和规格值', 'warning');
            return;
        }

        const cardData = {
            name: cardName,
            type: cardType,
            description: document.getElementById('cardDescription').value,
            delay_seconds: parseInt(document.getElementById('cardDelaySeconds').value) || 0,
            enabled: true,
            is_multi_spec: isMultiSpec,
            spec_name: isMultiSpec ? specName : null,
            spec_value: isMultiSpec ? specValue : null
        };

        switch(cardType) {
            case 'api':
                let headers = '{}';
                let params = '{}';

                try {
                    const headersInput = document.getElementById('apiHeaders').value.trim();
                    if (headersInput) {
                        JSON.parse(headersInput);
                        headers = headersInput;
                    }
                } catch (e) {
                    showToast('请求头格式错误，请输入有效的JSON', 'warning');
                    return;
                }

                try {
                    const paramsInput = document.getElementById('apiParams').value.trim();
                    if (paramsInput) {
                        JSON.parse(paramsInput);
                        params = paramsInput;
                    }
                } catch (e) {
                    showToast('请求参数格式错误，请输入有效的JSON', 'warning');
                    return;
                }

                cardData.api_config = {
                    url: document.getElementById('apiUrl').value,
                    method: document.getElementById('apiMethod').value,
                    timeout: parseInt(document.getElementById('apiTimeout').value),
                    headers: headers,
                    params: params
                };
                break;
            case 'text':
                cardData.text_content = document.getElementById('textContent').value;
                break;
            case 'data':
                cardData.data_content = document.getElementById('dataContent').value;
                break;
            case 'image':
                const imageFile = document.getElementById('cardImageFile').files[0];
                if (!imageFile) {
                    showToast('请选择图片文件', 'warning');
                    return;
                }

                const formData = new FormData();
                formData.append('image', imageFile);

                const uploadResponse = await fetch(`${apiBase}/upload-image`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: formData
                });

                if (!uploadResponse.ok) {
                    const errorData = await uploadResponse.json();
                    showToast(`图片上传失败: ${errorData.detail || '未知错误'}`, 'danger');
                    return;
                }

                const uploadResult = await uploadResponse.json();
                cardData.image_url = uploadResult.image_url;
                break;
        }

        const response = await fetch(`${apiBase}/cards`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cardData)
        });

        if (response.ok) {
            showToast('卡券保存成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addCardModal')).hide();
            clearAddCardForm();
            loadCards();
        } else {
            let errorMessage = '保存失败';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorData.detail || errorMessage;
            } catch (e) {
                try {
                    const errorText = await response.text();
                    errorMessage = errorText || errorMessage;
                } catch (e2) {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
            }
            showToast(`保存失败: ${errorMessage}`, 'danger');
        }
    } catch (error) {
        console.error('保存卡券失败:', error);
        showToast(`网络错误: ${error.message}`, 'danger');
    }
}

// 编辑卡券
export async function editCard(cardId) {
    try {
        const response = await fetch(`${apiBase}/cards/${cardId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const card = await response.json();

            document.getElementById('editCardId').value = card.id;
            document.getElementById('editCardName').value = card.name;
            document.getElementById('editCardType').value = card.type;
            document.getElementById('editCardDescription').value = card.description || '';
            document.getElementById('editCardDelaySeconds').value = card.delay_seconds || 0;
            document.getElementById('editCardEnabled').checked = card.enabled;

            const isMultiSpec = card.is_multi_spec || false;
            document.getElementById('editIsMultiSpec').checked = isMultiSpec;
            document.getElementById('editSpecName').value = card.spec_name || '';
            document.getElementById('editSpecValue').value = card.spec_value || '';

            if (card.type === 'api' && card.api_config) {
                document.getElementById('editApiUrl').value = card.api_config.url || '';
                document.getElementById('editApiMethod').value = card.api_config.method || 'GET';
                document.getElementById('editApiTimeout').value = card.api_config.timeout || 10;
                document.getElementById('editApiHeaders').value = card.api_config.headers || '{}';
                document.getElementById('editApiParams').value = card.api_config.params || '{}';
            } else if (card.type === 'text') {
                document.getElementById('editTextContent').value = card.text_content || '';
            } else if (card.type === 'data') {
                document.getElementById('editDataContent').value = card.data_content || '';
            } else if (card.type === 'image') {
                const currentImagePreview = document.getElementById('editCurrentImagePreview');
                const currentImg = document.getElementById('editCurrentImg');
                const noImageText = document.getElementById('editNoImageText');

                if (card.image_url) {
                    currentImg.src = card.image_url;
                    currentImagePreview.style.display = 'block';
                    noImageText.style.display = 'none';
                } else {
                    currentImagePreview.style.display = 'none';
                    noImageText.style.display = 'block';
                }

                document.getElementById('editCardImageFile').value = '';
                document.getElementById('editCardImagePreview').style.display = 'none';
            }

            toggleEditCardTypeFields();

            setTimeout(() => {
                toggleEditMultiSpecFields();
            }, 100);

            const modal = new bootstrap.Modal(document.getElementById('editCardModal'));
            modal.show();
        } else {
            showToast('获取卡券详情失败', 'danger');
        }
    } catch (error) {
        console.error('获取卡券详情失败:', error);
        showToast('获取卡券详情失败', 'danger');
    }
}

// 切换编辑卡券类型字段显示
export function toggleEditCardTypeFields() {
    const cardType = document.getElementById('editCardType').value;

    document.getElementById('editApiFields').style.display = cardType === 'api' ? 'block' : 'none';
    document.getElementById('editTextFields').style.display = cardType === 'text' ? 'block' : 'none';
    document.getElementById('editDataFields').style.display = cardType === 'data' ? 'block' : 'none';
    document.getElementById('editImageFields').style.display = cardType === 'image' ? 'block' : 'none';
}

// 更新卡券
export async function updateCard() {
    try {
        const cardId = document.getElementById('editCardId').value;
        const cardType = document.getElementById('editCardType').value;
        const cardName = document.getElementById('editCardName').value;

        if (!cardType || !cardName) {
            showToast('请填写必填字段', 'warning');
            return;
        }

        const isMultiSpec = document.getElementById('editIsMultiSpec').checked;
        const specName = document.getElementById('editSpecName').value;
        const specValue = document.getElementById('editSpecValue').value;

        if (isMultiSpec && (!specName || !specValue)) {
            showToast('多规格卡券必须填写规格名称和规格值', 'warning');
            return;
        }

        const cardData = {
            name: cardName,
            type: cardType,
            description: document.getElementById('editCardDescription').value,
            delay_seconds: parseInt(document.getElementById('editCardDelaySeconds').value) || 0,
            enabled: document.getElementById('editCardEnabled').checked,
            is_multi_spec: isMultiSpec,
            spec_name: isMultiSpec ? specName : null,
            spec_value: isMultiSpec ? specValue : null
        };

        switch(cardType) {
            case 'api':
                let headers = '{}';
                let params = '{}';

                try {
                    const headersInput = document.getElementById('editApiHeaders').value.trim();
                    if (headersInput) {
                        JSON.parse(headersInput);
                        headers = headersInput;
                    }
                } catch (e) {
                    showToast('请求头格式错误，请输入有效的JSON', 'warning');
                    return;
                }

                try {
                    const paramsInput = document.getElementById('editApiParams').value.trim();
                    if (paramsInput) {
                        JSON.parse(paramsInput);
                        params = paramsInput;
                    }
                } catch (e) {
                    showToast('请求参数格式错误，请输入有效的JSON', 'warning');
                    return;
                }

                cardData.api_config = {
                    url: document.getElementById('editApiUrl').value,
                    method: document.getElementById('editApiMethod').value,
                    timeout: parseInt(document.getElementById('editApiTimeout').value),
                    headers: headers,
                    params: params
                };
                break;
            case 'text':
                cardData.text_content = document.getElementById('editTextContent').value;
                break;
            case 'data':
                cardData.data_content = document.getElementById('editDataContent').value;
                break;
            case 'image':
                const imageFile = document.getElementById('editCardImageFile').files[0];
                if (imageFile) {
                    await updateCardWithImage(cardId, cardData, imageFile);
                    return;
                }
                break;
        }

        const response = await fetch(`${apiBase}/cards/${cardId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cardData)
        });

        if (response.ok) {
            showToast('卡券更新成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editCardModal')).hide();
            loadCards();
        } else {
            const error = await response.text();
            showToast(`更新失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('更新卡券失败:', error);
        showToast('更新卡券失败', 'danger');
    }
}

// 更新带图片的卡券
export async function updateCardWithImage(cardId, cardData, imageFile) {
    try {
        const formData = new FormData();
        formData.append('image', imageFile);

        Object.keys(cardData).forEach(key => {
            if (cardData[key] !== null && cardData[key] !== undefined) {
                if (typeof cardData[key] === 'object') {
                    formData.append(key, JSON.stringify(cardData[key]));
                } else {
                    formData.append(key, cardData[key]);
                }
            }
        });

        const response = await fetch(`${apiBase}/cards/${cardId}/image`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        if (response.ok) {
            showToast('卡券更新成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editCardModal')).hide();
            loadCards();
        } else {
            const error = await response.text();
            showToast(`更新失败: ${error}`, 'danger');
        }
    } catch (error) {
        console.error('更新带图片的卡券失败:', error);
        showToast('更新卡券失败', 'danger');
    }
}

// 测试卡券
export function testCard(cardId) {
    showToast('测试功能开发中...', 'info');
}

// 删除卡券
export async function deleteCard(cardId) {
    if (confirm('确定要删除这个卡券吗？删除后无法恢复！')) {
        try {
            const response = await fetch(`${apiBase}/cards/${cardId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });

            if (response.ok) {
                showToast('卡券删除成功', 'success');
                loadCards();
            } else {
                const error = await response.text();
                showToast(`删除失败: ${error}`, 'danger');
            }
        } catch (error) {
            console.error('删除卡券失败:', error);
            showToast('删除卡券失败', 'danger');
        }
    }
}

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

// 测试发货规则
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
