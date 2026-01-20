# 戏讯解析助手 - 使用说明

## 问题修复

### ✅ 已修复问题

1. **文件路径错误**: 已修复 `No such file or directory` 错误
   - 自动创建 `backend/data` 目录
   - 使用绝对路径保存文件

2. **HTML内容保存**: 现在会自动保存两份HTML文件
   - `backend/data/temp_content.html` - 每次解析都会覆盖的临时文件
   - `backend/data/content_YYYYMMDD_HHMMSS.html` - 带时间戳的永久文件

## 使用流程

### 1. 启动服务

```bash
cd /Users/lu/AIProjects/戏讯解析助手
./start.sh
```

### 2. 访问网页

打开浏览器: http://localhost:5000

### 3. 解析文章

输入链接并点击"开始解析"

### 4. 查看保存的HTML内容

解析完成后,HTML内容会自动保存到:
```
backend/data/content_YYYYMMDD_HHMMSS.html
backend/data/temp_content.html
```

### 5. 分析HTML结构

使用分析工具查看HTML内容:

```bash
# 方式1: 自动分析最新的HTML文件
python3 analyze_html.py

# 方式2: 指定文件路径
python3 analyze_html.py backend/data/temp_content.html
```

分析工具会输出:
- HTML标签统计
- 段落、表格、section数量
- 前50行文本内容
- 日期、时间模式
- 可能的剧场信息
- 生成纯文本版本 (`*_text.txt`)
- 生成结构分析文件 (`*_structure.txt`)

### 6. 根据分析结果优化解析逻辑

查看分析结果后,可以在 `backend/parser.py` 的 `_extract_performances` 方法中优化数据提取逻辑。

## 文件说明

### 保存的文件

```
backend/data/
├── temp_content.html           # 临时HTML(每次覆盖)
├── content_20260120_003152.html  # 带时间戳的HTML
├── result_20260120_003152.json   # 完整JSON结果
├── content_*_text.txt           # 纯文本版本(分析工具生成)
└── content_*_structure.txt      # 结构分析(分析工具生成)
```

### 核心文件

- `backend/app.py` - Flask API服务
- `backend/parser.py` - Selenium解析器
- `analyze_html.py` - HTML分析工具
- `frontend/index.html` - 网页界面

## 下一步

1. 运行解析器获取HTML内容
2. 使用 `analyze_html.py` 分析数据结构
3. 根据分析结果优化 `parser.py` 中的 `_extract_performances` 方法
4. 提取具体的戏讯字段(名称、时间、地点等)

## 常见问题

### Q: ChromeDriver未安装

```bash
brew install chromedriver
```

### Q: 端口被占用

修改 `backend/app.py` 最后一行的端口号:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 改为5001
```

### Q: 虚拟环境问题

```bash
# 删除并重建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```
