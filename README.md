# 戏讯解析助手

微信公众号戏讯数据智能解析工具

## 功能特性

- 🎭 **智能解析**: 自动解析微信公众号戏讯文章
- 📊 **数据展示**: 现代化界面展示戏讯数据
- 🔍 **搜索筛选**: 支持关键词搜索和数据筛选
- 💾 **多格式导出**: 支持Excel、CSV、JSON格式导出
- 🎨 **精美UI**: 渐变色设计,流畅动画效果

## 技术栈

### 前端
- HTML5 + CSS3 + JavaScript
- 现代化渐变设计
- 响应式布局

### 后端
- Python 3.8+
- Flask Web框架
- Selenium浏览器自动化
- BeautifulSoup HTML解析

## 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
cd backend
pip install -r requirements.txt
```

### 2. 安装ChromeDriver

macOS:
```bash
brew install chromedriver
```

或手动下载: https://chromedriver.chromium.org/

### 3. 启动服务

```bash
# 启动后端服务
cd backend
python app.py
```

服务将在 http://localhost:5000 启动

### 4. 访问应用

在浏览器中打开: http://localhost:5000

## 使用说明

1. 在输入框中粘贴微信公众号文章链接
2. 点击"开始解析"按钮
3. 等待解析完成,查看数据列表
4. 使用搜索框筛选数据
5. 点击导出按钮下载数据

## 项目结构

```
戏讯解析助手/
├── backend/                 # 后端服务
│   ├── app.py              # Flask应用
│   ├── parser.py           # 解析器
│   ├── requirements.txt    # Python依赖
│   └── data/              # 数据存储
├── frontend/               # 前端页面
│   ├── index.html         # 主页面
│   ├── css/
│   │   └── style.css      # 样式
│   └── js/
│       └── app.js         # 前端逻辑
└── README.md
```

## API文档

### POST /api/parse
解析微信公众号文章

**请求体**:
```json
{
  "url": "https://mp.weixin.qq.com/s/..."
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "title": "文章标题",
    "performances": [...],
    "total": 10
  }
}
```

### POST /api/export
导出数据

**请求体**:
```json
{
  "format": "excel|csv|json",
  "data": [...]
}
```

## 开发计划

- [x] 基础框架搭建
- [x] Selenium数据提取
- [x] 前端界面设计
- [ ] 数据解析优化
- [ ] 导出功能完善
- [ ] 飞书多维表格对接

## 注意事项

- 需要安装Chrome浏览器和ChromeDriver
- 首次运行可能需要较长时间加载
- 建议使用Chrome或Edge浏览器访问

## License

MIT
# -
