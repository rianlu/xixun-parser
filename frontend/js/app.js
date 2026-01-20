// 戏讯解析助手 - 前端逻辑

// API配置
const API_BASE_URL = 'http://localhost:5001/api';

// 全局状态
let currentData = [];
let filteredData = [];
let locationHierarchy = {}; // 地区层级数据
let selectedCity = '';
let selectedDistricts = new Set();

// DOM元素
const urlInput = document.getElementById('urlInput');
const parseBtn = document.getElementById('parseBtn');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const resultSection = document.getElementById('resultSection');
const articleTitle = document.getElementById('articleTitle');
const dataCount = document.getElementById('dataCount');
const searchInput = document.getElementById('searchInput');
const dataList = document.getElementById('dataList');
const citySelect = document.getElementById('citySelect');
const districtFilter = document.getElementById('districtFilter');
const districtCheckboxes = document.getElementById('districtCheckboxes');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 绑定事件
    parseBtn.addEventListener('click', handleParse);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleParse();
        }
    });
    searchInput.addEventListener('input', handleSearch);
    citySelect.addEventListener('change', handleCityChange);

    // 测试API连接
    checkAPIHealth();
});

// 检查API健康状态
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('API状态:', data);
    } catch (error) {
        console.warn('API连接失败,请确保后端服务已启动');
    }
}

// 处理解析请求
async function handleParse() {
    const url = urlInput.value.trim();

    // 验证输入
    if (!url) {
        showError('请输入文章链接');
        return;
    }

    if (!url.includes('mp.weixin.qq.com')) {
        showError('请输入有效的微信公众号文章链接');
        return;
    }

    // 显示加载状态
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const result = await response.json();

        if (result.success) {
            // 解析成功
            currentData = result.data.performances || [];
            filteredData = [...currentData];
            displayResults(result.data);
        } else {
            // 解析失败
            showError(result.error || '解析失败,请重试');
        }
    } catch (error) {
        console.error('请求错误:', error);
        showError('网络错误,请确保后端服务已启动');
    }
}

// 显示加载状态
function showLoading() {
    loadingState.classList.remove('hidden');
    errorState.classList.add('hidden');
    resultSection.classList.add('hidden');
}

// 显示错误
function showError(message) {
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
    loadingState.classList.add('hidden');
    resultSection.classList.add('hidden');
}

// 隐藏错误
function hideError() {
    errorState.classList.add('hidden');
}

// 显示结果
function displayResults(data) {
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultSection.classList.remove('hidden');

    // 更新统计信息
    articleTitle.textContent = data.title || '未知标题';
    dataCount.textContent = data.total || 0;

    // 提取地区层级
    locationHierarchy = extractLocationHierarchy(data.performances);

    // 填充城市下拉框
    populateCitySelect(locationHierarchy);

    // 渲染数据列表
    renderDataList(filteredData);
}

// 渲染数据列表
function renderDataList(data) {
    if (!data || data.length === 0) {
        dataList.innerHTML = `
            <div class="data-item">
                <p style="text-align: center; color: var(--text-secondary);">
                    暂无数据
                </p>
            </div>
        `;
        return;
    }

    dataList.innerHTML = data.map((item, index) => {
        // 构建标题
        let title = `${item.troupe || '未知剧团'}`;

        // 构建日期信息
        let dateInfo = '';
        if (item.date) {
            dateInfo = `<div style="color: var(--primary-color); font-size: 0.9rem; margin-bottom: 5px;">
                📅 ${item.date} ${item.lunar_date ? `(${item.lunar_date})` : ''}
            </div>`;
        }

        // 构建地点信息
        let venueInfo = '';
        if (item.venue) {
            venueInfo = `<div style="margin-bottom: 5px;">
                📍 ${item.venue}
                ${item.location_note ? `<span style="color: var(--text-secondary); font-size: 0.85rem;">(定位: ${item.location_note})</span>` : ''}
            </div>`;
        }

        // 构建剧目信息
        let showsInfo = '';
        if (item.shows && item.shows.length > 0) {
            showsInfo = '<div style="margin-top: 10px; padding-left: 10px; border-left: 3px solid var(--primary-color);">';
            item.shows.forEach(show => {
                if (show.date) {
                    // 多日演出格式
                    showsInfo += `<div style="margin-bottom: 5px;">
                        <strong>${show.date}</strong>: ${show.info}
                    </div>`;
                } else {
                    // 当天演出格式
                    showsInfo += `<div style="margin-bottom: 5px;">
                        <strong>${show.time}</strong>: ${show.info}
                    </div>`;
                }
            });
            showsInfo += '</div>';
        }

        // 演出天数信息
        let daysInfo = '';
        if (item.days_info) {
            daysInfo = `<div style="margin-top: 8px; color: var(--text-secondary); font-size: 0.85rem;">
                ${item.days_info}
            </div>`;
        }

        return `
            <div class="data-item" style="animation-delay: ${index * 0.05}s">
                <div class="data-item-header">
                    <div class="data-item-title">
                        🎭 ${title}
                    </div>
                    <div class="data-item-id">#${item.id}</div>
                </div>
                <div class="data-item-content">
                    ${dateInfo}
                    ${venueInfo}
                    ${showsInfo}
                    ${daysInfo}
                </div>
            </div>
        `;
    }).join('');
}

// 格式化数据项内容
function formatItemContent(item) {
    const fields = [];

    if (item.time) fields.push(`⏰ 时间: ${item.time}`);
    if (item.venue) fields.push(`📍 地点: ${item.venue}`);
    if (item.type) fields.push(`🎭 类型: ${item.type}`);
    if (item.actors) fields.push(`👥 演员: ${item.actors}`);
    if (item.price) fields.push(`💰 票价: ${item.price}`);

    if (fields.length === 0 && item.raw_text) {
        return `<p>${item.raw_text}</p>`;
    }

    return fields.join(' | ') || '暂无详细信息';
}

// 处理搜索
function handleSearch(e) {
    const keyword = e.target.value.trim().toLowerCase();

    if (!keyword) {
        filteredData = [...currentData];
    } else {
        filteredData = currentData.filter(item => {
            const searchText = [
                item.name,
                item.venue,
                item.type,
                item.actors,
                item.raw_text
            ].filter(Boolean).join(' ').toLowerCase();

            return searchText.includes(keyword);
        });
    }

    renderDataList(filteredData);
    dataCount.textContent = filteredData.length;
}

// 导出数据
async function exportData(format) {
    if (!currentData || currentData.length === 0) {
        alert('暂无数据可导出');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                format,
                data: filteredData
            })
        });

        const result = await response.json();

        if (result.success) {
            // TODO: 处理文件下载
            alert(`导出${format}格式成功!`);
        } else {
            alert(`导出失败: ${result.error}`);
        }
    } catch (error) {
        console.error('导出错误:', error);
        alert('导出失败,请重试');
    }
}

// 工具函数:格式化日期
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}
