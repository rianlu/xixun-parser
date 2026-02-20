// 戏讯解析助手 - 前端逻辑

// API配置
const API_BASE_URL = (() => {
    if (window.API_BASE_URL) return window.API_BASE_URL;
    if (window.location.protocol === 'file:') return 'http://localhost:5001/api';
    return '/api';
})();
const REQUEST_TIMEOUT_MS = 30000;

// 全局状态
let currentData = [];
let filteredData = [];
let listenersBound = false;

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
const themeToggleBtn = document.getElementById('themeToggleBtn');
const retryBtn = document.getElementById('retryBtn');
const copyBtn = document.getElementById('copyBtn');
const syncPreviewBtn = document.getElementById('syncPreviewBtn');
const exportButtons = document.querySelectorAll('.export-btn');
const syncModal = document.getElementById('syncModal');
const syncCancelBtn = document.getElementById('syncCancelBtn');
const syncConfirmBtn = document.getElementById('syncConfirmBtn');
const syncModalCloseIconBtn = document.getElementById('syncModalCloseIconBtn');

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function setTextCell(td, value) {
    td.textContent = String(value ?? '');
}

function setMultilineTextCell(td, value) {
    const text = String(value ?? '');
    const lines = text.split(/\r?\n/);
    lines.forEach((line, index) => {
        if (index > 0) td.appendChild(document.createElement('br'));
        td.appendChild(document.createTextNode(line));
    });
}

function setTableEmptyRow(tbody, colSpan, text, large = false) {
    tbody.innerHTML = '';
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = colSpan;
    td.className = `table-empty-cell${large ? ' large' : ''}`;
    td.textContent = text;
    tr.appendChild(td);
    tbody.appendChild(tr);
}

function formatShowLines(item, separator = '\n') {
    if (item.shows && item.shows.length > 0) {
        return item.shows.map(s => {
            const prefix = s.date || s.time || '';
            const info = s.info || '';
            return prefix ? `${prefix} ${info}` : info;
        }).join(separator);
    }
    if (item.content) return String(item.content);
    return item.location_note ? `定位:${item.location_note}` : (item.days_info || '');
}

async function fetchJson(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        if (!response.ok) {
            let detail = '';
            try {
                detail = await response.text();
            } catch (_) {
                detail = '';
            }
            throw new Error(`HTTP ${response.status}${detail ? `: ${detail.slice(0, 200)}` : ''}`);
        }
        return await response.json();
    } finally {
        clearTimeout(timeoutId);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initTheme(); // Initialize Theme

    // 绑定事件
    parseBtn.addEventListener('click', handleParse);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleParse();
        }
    });
    setupFilterListeners();
    if (themeToggleBtn) themeToggleBtn.addEventListener('click', toggleTheme);
    if (retryBtn) retryBtn.addEventListener('click', hideError);
    if (copyBtn) copyBtn.addEventListener('click', copyToClipboard);
    if (syncPreviewBtn) syncPreviewBtn.addEventListener('click', previewSync);
    exportButtons.forEach(btn => {
        btn.addEventListener('click', () => exportData(btn.dataset.format));
    });
    if (syncCancelBtn) syncCancelBtn.addEventListener('click', closeSyncModal);
    if (syncConfirmBtn) syncConfirmBtn.addEventListener('click', confirmSync);
    if (syncModalCloseIconBtn) syncModalCloseIconBtn.addEventListener('click', closeSyncModal);

    // 测试API连接
    checkAPIHealth();
});

// 检查API健康状态
async function checkAPIHealth() {
    try {
        await fetchJson(`${API_BASE_URL}/health`);
    } catch (error) {
        console.warn('API连接失败,请确保后端服务已启动:', error.message);
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
    parseBtn.disabled = true;

    try {
        const result = await fetchJson(`${API_BASE_URL}/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        if (result.success) {
            // 解析成功
            currentData = result.data.performances || [];
            filteredData = [...currentData];
            // 初始筛选
            filterData();
            displayResults(result.data);

        } else {
            // 解析失败
            showError(result.error || '解析失败,请重试');
        }
    } catch (error) {
        console.error('请求错误:', error);
        showError(error.name === 'AbortError' ? '请求超时，请稍后重试' : '网络错误,请确保后端服务已启动');
    } finally {
        parseBtn.disabled = false;
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
    tableBody.innerHTML = '';

    if (!data || data.length === 0) {
        setTableEmptyRow(tableBody, 5, '暂无数据');
        return;
    }

    data.forEach(item => {
        tableBody.appendChild(createRow(item));
    });
}

function createRow(item) {
    // 使用后端计算的 start_date 和 end_date
    const startDate = item.start_date || item.date || '';
    const endDate = item.end_date || '';
    const troupe = item.troupe || '';
    const address = item.venue || '';
    // 总天数（totalDays）不显示

    const content = formatShowLines(item, '\n');

    const tr = document.createElement('tr');

    const tdTroupe = document.createElement('td');
    tdTroupe.className = 'troupe-cell';
    setTextCell(tdTroupe, troupe);

    const tdAddress = document.createElement('td');
    setTextCell(tdAddress, address);

    const tdStartDate = document.createElement('td');
    tdStartDate.className = 'date-cell';
    setTextCell(tdStartDate, startDate);

    const tdEndDate = document.createElement('td');
    tdEndDate.className = 'date-cell';
    setTextCell(tdEndDate, endDate);

    const tdContent = document.createElement('td');
    tdContent.className = 'content-cell';
    setMultilineTextCell(tdContent, content);

    tr.appendChild(tdTroupe);
    tr.appendChild(tdAddress);
    tr.appendChild(tdStartDate);
    tr.appendChild(tdEndDate);
    tr.appendChild(tdContent);

    return tr;
}

// 处理搜索
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

        const content = formatShowLines(item, ' | ');

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
    if (listenersBound) return;
    listenersBound = true;

    const checkboxes = document.querySelectorAll('#regionCheckboxes input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
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
}

// --- Sync Functions ---
let currentSyncActions = [];

async function previewSync() {
    if (!filteredData || filteredData.length === 0) {
        alert("没有数据可同步，请先解析文章。");
        return;
    }

    const btn = syncPreviewBtn;
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '正在计算...';
        btn.disabled = true;
    }

    try {
        const data = await fetchJson(`${API_BASE_URL}/sync/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data: filteredData })
        });

        if (!data.success) {
            alert('获取同步预览失败: ' + (data.error || '未知错误'));
            return;
        }

        currentSyncActions = data.actions;

        // Show Remote Count Info
        const countInfo = document.getElementById('syncRemoteInfo');
        if (countInfo) {
            const remoteCount = Number(data.remote_count) || 0;
            countInfo.innerHTML = `已连接飞书。远程表格现有数据: <strong>${remoteCount}</strong> 条。`;
            if (remoteCount === 0) {
                countInfo.innerHTML += ` <span class="sync-warning">(⚠️ 注意: 远程表格为空! 请检查 TableID 是否正确)</span>`;
            }
        }

        renderSyncPreview(data.actions);
        openSyncModal();
    } catch (error) {
        console.error('Error:', error);
        alert(error.name === 'AbortError' ? '请求超时，请重试' : '请求失败，请检查网络或后端服务');
    } finally {
        if (btn) {
            btn.innerHTML = '<span>🔄</span> 同步到飞书';
            btn.disabled = false;
        }
    }
}

function renderSyncPreview(actions) {
    const tbody = document.querySelector('#syncPreviewTable tbody');
    tbody.innerHTML = '';

    // Calculate stats
    let createCount = 0;
    let updateCount = 0;
    let deleteCount = 0;
    let skipCount = 0;

    actions.forEach(a => {
        if (a.type === 'CREATE') createCount++;
        else if (a.type === 'UPDATE') updateCount++;
        else if (a.type === 'DELETE') deleteCount++;
        else if (a.type === 'SKIP') skipCount++;
    });

    // Update Summary Logic
    // "我只需要显示本次同步更新多少条数据。以及云端有哪些数据是不会被修改的"
    const countInfo = document.getElementById('syncRemoteInfo');
    if (countInfo) {
        // Build summary string
        let summaryHtml = `<div class="sync-summary">`;

        // 1. Update/Add Count
        const changeCount = createCount + updateCount;
        summaryHtml += `<div class="sync-summary-item create">
            <strong>本次更新:</strong> <span class="sync-count">${changeCount}</span> 条数据 
            <span class="sync-subtext">(新增 ${createCount}, 更新 ${updateCount})</span>
        </div>`;

        // 2. Unchanged Count
        summaryHtml += `<div class="sync-summary-item skip">
            <strong>云端保留(未修改):</strong> <span class="sync-count">${skipCount}</span> 条数据
        </div>`;

        // 3. Deletion Count (Hidden details but maybe show simplified count if needed, or hide as requested? 
        // User said "不考虑删除的数据", better to just mention it briefly or ignore. 
        // Let's hide it from the main view but maybe show a small note if > 0 just for safety?)
        // If user wants to ignore completely, we can skip showing it or show it in gray.
        // Let's add it in light gray
        if (deleteCount > 0) {
            summaryHtml += `<div class="sync-summary-item delete">
                <strong>将被移除(已隐藏):</strong> ${deleteCount} 条
            </div>`;
        }

        summaryHtml += `</div>`;
        countInfo.innerHTML = summaryHtml;
    }

    if (actions.length === 0) {
        setTableEmptyRow(tbody, 6, '数据已是最新，无需同步。');
        return;
    }

    // Sort: CREATE/UPDATE first, then SKIP. Hide DELETE.
    // We can filter out DELETE
    const displayActions = actions.filter(a => a.type !== 'DELETE');

    // Sort logic: Chronological first, then by Type priority
    displayActions.sort((a, b) => {
        // Helper to parse date string to timestamp
        const getTs = (d) => {
            if (!d) return 0;
            // Handle "2026年1月25日" -> "2026/1/25" for parsing
            let s = d.replace(/年|月/g, '/').replace(/日/g, '');
            // Handle "2026-01-25" -> "2026/01/25" (already works)
            return new Date(s).getTime();
        };

        const dateA = getTs(a.date);
        const dateB = getTs(b.date);

        if (dateA !== dateB) {
            return dateA - dateB;
        }

        // Tie-breaker: Type Priority (Update > Create > Skip)
        const priority = { 'UPDATE': 1, 'CREATE': 2, 'SKIP': 3 };
        return (priority[a.type] || 99) - (priority[b.type] || 99);
    });

    displayActions.forEach(action => {
        const tr = document.createElement('tr');
        let rowClass = '';
        let labelClass = '';
        let label = action.type;
        let troupeDisplay = escapeHtml(action.troupe || '-');
        let venueDisplay = escapeHtml(action.venue || '-');
        let endDateDisplay = escapeHtml(action.end_date || '-');

        // Format content for display (replace newlines with <br>)
        let contentDisplay = escapeHtml(action.content || '').replace(/\n/g, '<br>');

        if (action.type === 'CREATE') {
            label = '新增';
            rowClass = 'sync-op-create';
            labelClass = 'create';
        }
        else if (action.type === 'UPDATE') {
            label = '更新';
            rowClass = 'sync-op-update';
            labelClass = 'update';

            // Diff Helper
            const diffHtml = (oldVal, newVal) => {
                if (oldVal && oldVal !== newVal) {
                    return `<div class="sync-diff-old">${escapeHtml(oldVal)}</div>
                             <div class="sync-diff-new">${escapeHtml(newVal || '(空)')}</div>`;
                }
                return escapeHtml(newVal || '');
            };

            troupeDisplay = diffHtml(action.old_troupe, action.troupe);
            venueDisplay = diffHtml(action.old_venue, action.venue);
            endDateDisplay = diffHtml(action.old_end_date, action.end_date);

            // Content Diff
            if (action.old_content && action.old_content !== action.content) {
                const oldC = action.old_content || '';
                const newC = action.content || '';
                contentDisplay = `<div class="sync-diff-old">${escapeHtml(oldC).replace(/\n/g, '<br>')}</div>
                                  <div class="sync-diff-new">${escapeHtml(newC).replace(/\n/g, '<br>')}</div>`;
            }
        }
        else if (action.type === 'SKIP') {
            label = '保留';
            rowClass = 'sync-op-skip';
            labelClass = 'skip';
        }

        if (rowClass) tr.classList.add(rowClass);

        tr.innerHTML = `
            <td><span class="sync-op-label ${escapeHtml(labelClass)}">${escapeHtml(label)}</span></td>
            <td>${troupeDisplay}</td>
            <td>${venueDisplay}</td>
            <td>${escapeHtml(action.date || '-')}</td>
            <td>${endDateDisplay}</td>
            <td class="sync-content-cell">${contentDisplay}</td>
        `;
        tbody.appendChild(tr);
    });

    if (tbody.children.length === 0) {
        if (deleteCount > 0) {
            setTableEmptyRow(tbody, 6, '仅有删除操作（已隐藏），请点击确认同步执行清理。');
        } else {
            setTableEmptyRow(tbody, 6, '无可见变更');
        }
    }
}

// --- Theme Handling ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcon(true);
    } else {
        document.documentElement.removeAttribute('data-theme');
        updateThemeIcon(false);
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const isDark = current === 'dark';

    if (isDark) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        updateThemeIcon(false);
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        updateThemeIcon(true);
    }
}

function updateThemeIcon(isDark) {
    const btn = document.querySelector('.theme-toggle .icon');
    if (btn) btn.textContent = isDark ? '🌙' : '☀️';
}

async function confirmSync() {
    if (!currentSyncActions || currentSyncActions.length === 0) return;

    const btn = syncConfirmBtn;
    const originalText = btn.innerText;
    btn.innerText = '同步中...';
    btn.disabled = true;

    try {
        const data = await fetchJson(`${API_BASE_URL}/sync/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ actions: currentSyncActions })
        });

        if (data.success) {
            const stats = data.stats;
            alert(`同步完成!\n新增: ${stats.create}\n更新: ${stats.update}\n删除: ${stats.delete}\n跳过: ${stats.skip}\n错误: ${stats.error}`);
            closeSyncModal();
        } else {
            alert('同步执行失败: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.name === 'AbortError' ? '请求超时，请重试' : '请求失败');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    if (event.target === syncModal) {
        closeSyncModal();
    }
});

function openSyncModal() {
    syncModal.classList.remove('hidden');
}

function closeSyncModal() {
    syncModal.classList.add('hidden');
}
