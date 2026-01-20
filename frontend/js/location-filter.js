// 地区筛选相关函数

// 提取地区信息
function extractLocationHierarchy(performances) {
    const hierarchy = {};
    const cityPattern = /^([^市县区镇]+[市县区])/;

    performances.forEach(perf => {
        const venue = perf.venue || '';
        if (!venue) return;

        // 提取市级
        const match = venue.match(cityPattern);
        if (match) {
            const city = match[1];
            if (!hierarchy[city]) {
                hierarchy[city] = new Set();
            }

            // 提取县/区/镇
            const remaining = venue.substring(city.length);
            const districtMatch = remaining.match(/^([^镇街道]+[县区镇街道])/);
            if (districtMatch) {
                hierarchy[city].add(districtMatch[1]);
            } else {
                hierarchy[city].add('其他');
            }
        }
    });

    // 转换Set为Array
    const result = {};
    for (const [city, districts] of Object.entries(hierarchy)) {
        result[city] = Array.from(districts).sort();
    }

    return result;
}

// 填充城市下拉框
function populateCitySelect(hierarchy) {
    // 清空现有选项
    citySelect.innerHTML = '<option value="">全部市/县</option>';

    // 按城市名称排序
    const cities = Object.keys(hierarchy).sort();

    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
    });
}

// 处理城市选择变化
function handleCityChange(e) {
    selectedCity = e.target.value;
    selectedDistricts.clear();

    if (selectedCity) {
        // 显示区域筛选
        districtFilter.classList.remove('hidden');
        populateDistrictCheckboxes(selectedCity);
    } else {
        // 隐藏区域筛选
        districtFilter.classList.add('hidden');
    }

    applyFilters();
}

// 填充区域复选框
function populateDistrictCheckboxes(city) {
    districtCheckboxes.innerHTML = '';

    const districts = locationHierarchy[city] || [];

    districts.forEach(district => {
        const item = document.createElement('div');
        item.className = 'district-checkbox-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `district-${district}`;
        checkbox.value = district;
        checkbox.addEventListener('change', handleDistrictChange);

        const label = document.createElement('label');
        label.htmlFor = `district-${district}`;
        label.textContent = district;

        item.appendChild(checkbox);
        item.appendChild(label);
        districtCheckboxes.appendChild(item);
    });
}

// 处理区域复选框变化
function handleDistrictChange(e) {
    const district = e.target.value;

    if (e.target.checked) {
        selectedDistricts.add(district);
    } else {
        selectedDistricts.delete(district);
    }

    applyFilters();
}

// 清除区域选择
function clearDistricts() {
    selectedDistricts.clear();

    // 取消所有复选框
    const checkboxes = districtCheckboxes.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);

    applyFilters();
}

// 应用所有筛选条件
function applyFilters() {
    const keyword = searchInput.value.trim().toLowerCase();

    filteredData = currentData.filter(item => {
        // 1. 地区筛选
        if (selectedCity) {
            const venue = item.venue || '';

            // 检查是否属于选中的城市
            if (!venue.startsWith(selectedCity)) {
                return false;
            }

            // 如果有选中的区域,检查是否匹配
            if (selectedDistricts.size > 0) {
                let matchesDistrict = false;
                for (const district of selectedDistricts) {
                    if (district === '其他') {
                        // 检查是否不包含任何已知区域
                        const allDistricts = locationHierarchy[selectedCity] || [];
                        const hasKnownDistrict = allDistricts.some(d =>
                            d !== '其他' && venue.includes(d)
                        );
                        if (!hasKnownDistrict) {
                            matchesDistrict = true;
                            break;
                        }
                    } else if (venue.includes(district)) {
                        matchesDistrict = true;
                        break;
                    }
                }
                if (!matchesDistrict) {
                    return false;
                }
            }
        }

        // 2. 关键词搜索
        if (keyword) {
            // 搜索剧团
            if (item.troupe && item.troupe.toLowerCase().includes(keyword)) return true;

            // 搜索地点
            if (item.venue && item.venue.toLowerCase().includes(keyword)) return true;

            // 搜索日期
            if (item.date && item.date.includes(keyword)) return true;

            // 搜索剧目
            if (item.shows) {
                for (let show of item.shows) {
                    if (show.info && show.info.toLowerCase().includes(keyword)) return true;
                }
            }

            return false;
        }

        return true;
    });

    renderDataList(filteredData);
    dataCount.textContent = filteredData.length;
}
