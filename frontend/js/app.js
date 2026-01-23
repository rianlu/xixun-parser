// 戏讯解析助手 - 前端逻辑

// API配置
const API_BASE_URL = 'http://localhost:5001/api';

// 全局状态
let currentData = [];
let filteredData = [];

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
const tableBody = document.getElementById('tableBody');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 绑定事件
    parseBtn.addEventListener('click', handleParse);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleParse();
        }
    });
    // searchInput.addEventListener('input', handleSearch);

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
            // 初始筛选
            filterData();
            displayResults(result.data);

            // 添加筛选监听器
            setupFilterListeners();
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
    dataCount.textContent = filteredData.length || 0;

    // 渲染数据表格
    renderTable(filteredData);
}

// 渲染数据表格
function renderTable(data) {
    if (!data || data.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 30px;">
                    暂无数据
                </td>
            </tr>
        `;
        return;
    }

    const rows = data.map(item => createRow(item));
    tableBody.innerHTML = rows.join('');
}

function createRow(item) {
    // 使用后端计算的 start_date 和 end_date
    const startDate = item.start_date || item.date || '';
    const endDate = item.end_date || item.date || '';
    const troupe = item.troupe || '';
    const address = item.venue || '';
    // 总天数（totalDays）不显示

    // 合并内容详情
    let content = '';
    if (item.shows && item.shows.length > 0) {
        // 将所有场次组合在一起
        content = item.shows.map(s => {
            const time = s.time || '';
            const info = s.info || '';
            return time ? `${time} ${info}` : info;
        }).join('<br>');
    } else {
        content = item.location_note ? `定位:${item.location_note}` : (item.days_info || '');
    }

    return `
        <tr>
            <td class="troupe-cell">${troupe}</td>
            <td>${address}</td>
            <td class="date-cell">${startDate}</td>
            <td class="date-cell">${endDate}</td>
            <td class="content-cell">${content}</td>
        </tr>
    `;
}

// 处理搜索
function handleSearch(e) {
    const keyword = e.target.value.trim().toLowerCase();

    if (!keyword) {
        filteredData = [...currentData];
    } else {
        filteredData = currentData.filter(item => {
            const searchText = [
                item.troupe,
                item.venue,
                item.date,
                item.start_date,
                item.actors,
                item.raw_text
            ].filter(Boolean).join(' ').toLowerCase();

            return searchText.includes(keyword);
        });
    }

    renderTable(filteredData);
    dataCount.textContent = filteredData.length;
}

// 复制到剪贴板 (Tab-separated values for Excel/Feishu)
function copyToClipboard() {
    if (!filteredData || filteredData.length === 0) {
        alert('暂无数据可复制');
        return;
    }

    // Build Header matching Feishu Fields (Troupe, Address, Start, End, Content)
    // 剧团或词师名称	地址	开始日期	结束日期	内容详情
    let tsvContent = "剧团或词师名称\t地址\t开始日期\t结束日期\t内容详情\n";

    filteredData.forEach(item => {
        const startDate = item.start_date || item.date || '';
        const endDate = item.end_date || item.date || '';
        const troupe = item.troupe || '';
        const address = item.venue || '';
        // totalDays ignored

        let content = '';
        if (item.shows && item.shows.length > 0) {
            // 复制时使用 " | " 分隔不同场次
            content = item.shows.map(s => {
                const time = s.time || '';
                const info = s.info || '';
                return time ? `${time} ${info}` : info;
            }).join(' | ');
        } else {
            content = item.location_note ? `定位:${item.location_note}` : (item.days_info || '');
        }

        // 清理潜在的制表符或换行符
        const cleanContent = content.replace(/\t/g, ' ').replace(/\n/g, ' ');

        const row = [troupe, address, startDate, endDate, cleanContent].join('\t');
        tsvContent += row + "\n";
    });

    navigator.clipboard.writeText(tsvContent).then(() => {
        alert('已复制到剪贴板! (顺序: 剧团, 地址, 开始, 结束, 内容)');
    }).catch(err => {
        console.error('复制失败:', err);
        alert('复制失败，请手动复制。');
    });
}

// 导出数据 (保留原有接口，暂不重点维护)
async function exportData(format) {
    alert("请使用'复制为表格格式'功能直接粘贴到飞书，更方便！");
}

// 设置筛选监听器
function setupFilterListeners() {
    console.log('Setting up filter listeners');
    const checkboxes = document.querySelectorAll('#regionCheckboxes input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            console.log('Region checkbox changed');
            filterData();
            // 更新显示
            // articleTitle.textContent = document.getElementById('articleTitle').textContent; 
            dataCount.textContent = filteredData.length;
            renderTable(filteredData);
        });
    });

    // 搜索框也触发筛选
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            console.log('Search input changed');
            filterData();
            dataCount.textContent = filteredData.length;
            renderTable(filteredData);
        });
    }
}

// 筛选数据
function filterData() {
    if (!currentData) return;

    // 获取选中的地区
    const selectedRegions = Array.from(document.querySelectorAll('#regionCheckboxes input[type="checkbox"]:checked'))
        .map(cb => cb.value);

    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : '';

    filteredData = currentData.filter(item => {
        // 1. 地区筛选
        // 默认全选时如果一个没选可能意味着全不选? 
        // 按照用户需求，默认选中了几个。如果用户全部取消勾选，应该显示为空还是显示所有?
        // 通常 checkbox 筛选是 OR 关系。如果未选中任何地区，逻辑上应该是不显示任何数据。
        if (selectedRegions.length > 0) {
            const address = item.venue || '';
            const regionMatch = selectedRegions.some(region => address.includes(region));
            if (!regionMatch) return false;
        }

        // 2. 搜索筛选
        if (searchTerm) {
            const rawText = (item.raw_text || '').toLowerCase();
            const troupe = (item.troupe || '').toLowerCase();
            const venue = (item.venue || '').toLowerCase();
            const showsContent = (item.shows || []).map(s => (s.info || '') + (s.time || '')).join(' ').toLowerCase();

            return rawText.includes(searchTerm) ||
                troupe.includes(searchTerm) ||
                venue.includes(searchTerm) ||
                showsContent.includes(searchTerm);
        }

        return true;
    });
    console.log('Filtered data count:', filteredData.length);
}
