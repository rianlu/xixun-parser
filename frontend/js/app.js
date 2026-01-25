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
    const endDate = item.end_date || '';
    const troupe = item.troupe || '';
    const address = item.venue || '';
    // 总天数（totalDays）不显示

    // 合并内容详情
    let content = '';
    if (item.shows && item.shows.length > 0) {
        // 将所有场次组合在一起
        content = item.shows.map(s => {
            const prefix = s.date || s.time || '';
            const info = s.info || '';
            return prefix ? `${prefix} ${info}` : info;
        }).join('<br>');
    } else if (item.content) {
        // Fallback if item.content already exists (from backend sync preference)
        content = item.content.replace(/\n/g, '<br>');
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
            // 复制时使用 " | " 分隔不同场次 (避免换行破坏TSV格式)
            content = item.shows.map(s => {
                const prefix = s.date || s.time || '';
                const info = s.info || '';
                return prefix ? `${prefix} ${info}` : info;
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

// --- Sync Functions ---
let currentSyncActions = [];

function previewSync() {
    if (!filteredData || filteredData.length === 0) {
        alert("没有数据可同步，请先解析文章。");
        return;
    }

    const btn = document.querySelector('.action-btn.sync-btn') || document.querySelector('button[onclick="previewSync()"]');
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '正在计算...';
        btn.disabled = true;
    }

    fetch(`${API_BASE_URL}/sync/preview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: filteredData })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentSyncActions = data.actions;

                // 🔍 调试: 打印读取到的数据到控制台
                console.log('=== 同步预览数据 ===');
                console.log('远程记录数:', data.remote_count);
                console.log('操作列表:', data.actions);
                console.log('详细操作:');
                data.actions.forEach((action, index) => {
                    console.log(`[${index + 1}] ${action.type}:`, {
                        剧团: action.troupe,
                        地址: action.venue,
                        开始日期: action.date,
                        结束日期: action.end_date,
                        内容: action.content
                    });
                });
                console.log('==================');

                // Show Remote Count Info
                const countInfo = document.getElementById('syncRemoteInfo');
                if (countInfo) {
                    countInfo.innerHTML = `已连接飞书。远程表格现有数据: <strong>${data.remote_count}</strong> 条。`;
                    if (data.remote_count === 0) {
                        countInfo.innerHTML += ` <span style="color:red; font-weight:bold;">(⚠️ 注意: 远程表格为空! 请检查 TableID 是否正确)</span>`;
                    }
                }

                renderSyncPreview(data.actions);
                document.getElementById('syncModal').style.display = 'block';
            } else {
                alert('获取同步预览失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('请求失败，请检查网络或后端服务');
        })
        .finally(() => {
            if (btn) {
                btn.innerHTML = '<span>🔄</span> 同步到飞书';
                btn.disabled = false;
            }
        });
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
        let summaryHtml = `<div style="display: flex; gap: 20px; flex-wrap: wrap;">`;

        // 1. Update/Add Count
        const changeCount = createCount + updateCount;
        summaryHtml += `<div style="padding: 10px; background: #e6fffa; border-radius: 4px; color: #008000;">
            <strong>本次更新:</strong> <span style="font-size: 1.2em;">${changeCount}</span> 条数据 
            <span style="font-size: 0.9em; color: #666;">(新增 ${createCount}, 更新 ${updateCount})</span>
        </div>`;

        // 2. Unchanged Count
        summaryHtml += `<div style="padding: 10px; background: #f0f7ff; border-radius: 4px; color: #0052cc;">
            <strong>云端保留(未修改):</strong> <span style="font-size: 1.2em;">${skipCount}</span> 条数据
        </div>`;

        // 3. Deletion Count (Hidden details but maybe show simplified count if needed, or hide as requested? 
        // User said "不考虑删除的数据", better to just mention it briefly or ignore. 
        // Let's hide it from the main view but maybe show a small note if > 0 just for safety?)
        // If user wants to ignore completely, we can skip showing it or show it in gray.
        // Let's add it in light gray
        if (deleteCount > 0) {
            summaryHtml += `<div style="padding: 10px; background: #fff5f5; border-radius: 4px; color: #cc0000; opacity: 0.6;">
                <strong>将被移除(已隐藏):</strong> ${deleteCount} 条
            </div>`;
        }

        summaryHtml += `</div>`;
        countInfo.innerHTML = summaryHtml;
    }

    if (actions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">数据已是最新，无需同步。</td></tr>';
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
        let color = '#333';
        let label = action.type;
        let bgColor = '';
        let troupeDisplay = action.troupe || '-';
        let venueDisplay = action.venue || '-';
        let endDateDisplay = action.end_date || '-';

        // Format content for display (replace newlines with <br>)
        let contentDisplay = (action.content || '').replace(/\n/g, '<br>');

        if (action.type === 'CREATE') {
            color = 'green'; label = '新增'; bgColor = '#e6fffa';
        }
        else if (action.type === 'UPDATE') {
            color = 'orange'; label = '更新'; bgColor = '#fffaf0';

            // Diff Helper
            const diffHtml = (oldVal, newVal) => {
                if (oldVal && oldVal !== newVal) {
                    return `<div style="font-size:0.9em;color:#999;text-decoration:line-through;margin-bottom:2px;">${oldVal}</div>
                             <div style="color:#e65100;font-weight:600;">${newVal || '(空)'}</div>`;
                }
                return newVal;
            };

            troupeDisplay = diffHtml(action.old_troupe, action.troupe);
            venueDisplay = diffHtml(action.old_venue, action.venue);
            endDateDisplay = diffHtml(action.old_end_date, action.end_date);

            // Content Diff
            if (action.old_content && action.old_content !== action.content) {
                const oldC = (action.old_content || '').replace(/\n/g, '<br>');
                const newC = (action.content || '').replace(/\n/g, '<br>');
                contentDisplay = `<div style="font-size:0.9em;color:#999;text-decoration:line-through;margin-bottom:6px;border-bottom:1px dashed #ddd;padding-bottom:4px;">${oldC}</div>
                                  <div style="color:#e65100;">${newC}</div>`;
            }
        }
        else if (action.type === 'SKIP') {
            color = '#666'; label = '保留'; bgColor = '#f8f9fa';
        }

        tr.style.backgroundColor = bgColor;

        tr.innerHTML = `
            <td style="color: ${color}; font-weight: bold;">${label}</td>
            <td>${troupeDisplay}</td>
            <td>${venueDisplay}</td>
            <td>${action.date || '-'}</td>
            <td>${endDateDisplay}</td>
            <td style="font-size: 13px; color: #555; white-space: nowrap;">${contentDisplay}</td>
        `;
        tbody.appendChild(tr);
    });

    if (tbody.children.length === 0) {
        if (deleteCount > 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">仅有删除操作（已隐藏），请点击确认同步执行清理。</td></tr>';
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">无可见变更</td></tr>';
        }
    }
}

function closeSyncModal() {
    document.getElementById('syncModal').style.display = 'none';
}

function confirmSync() {
    if (!currentSyncActions || currentSyncActions.length === 0) return;

    const btn = document.querySelector('#syncModal button[onclick="confirmSync()"]');
    const originalText = btn.innerText;
    btn.innerText = '同步中...';
    btn.disabled = true;

    fetch(`${API_BASE_URL}/sync/execute`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ actions: currentSyncActions })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                alert(`同步完成!\n新增: ${stats.create}\n更新: ${stats.update}\n删除: ${stats.delete}\n跳过: ${stats.skip}\n错误: ${stats.error}`);
                closeSyncModal();
            } else {
                alert('同步执行失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('请求失败');
        })
        .finally(() => {
            btn.innerText = originalText;
            btn.disabled = false;
        });
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('syncModal');
    if (event.target == modal) {
        closeSyncModal();
    }
}
