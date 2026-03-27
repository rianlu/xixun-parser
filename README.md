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

## 自动化部署

当前推荐的自动化链路如下:

```text
Telegram Bot -> Cloudflare Worker -> GitHub Actions -> Python 解析同步 -> Telegram 回执
```

### 1. GitHub 仓库要求

- 默认分支使用 `main`
- 保留 workflow 文件 `.github/workflows/sync.yml`
- GitHub Actions Secrets 至少配置:
  - `TELEGRAM_BOT_TOKEN`

### 2. Cloudflare Worker 连接 GitHub

- Git repository: `rianlu/xixun-parser`
- Root directory: `cloudflare_worker`
- Deploy command: `npx wrangler deploy`
- Production branch: `main`
- Version command: 留空

Worker 代码入口:

- `cloudflare_worker/worker.mjs`
- `cloudflare_worker/wrangler.toml`

### 3. Cloudflare Variables / Secrets

在 Cloudflare Worker 的生产环境中配置:

- `TELEGRAM_BOT_TOKEN`: Telegram BotFather 生成的 bot token
- `TELEGRAM_SECRET_TOKEN`: 自定义 webhook 校验口令，例如 `xixun_telegram_webhook_20260327`
- `GITHUB_TOKEN`: 可调用 GitHub Actions workflow dispatch API 的 token

可选变量:

- `GITHUB_REF`: 默认 `main`
- `GITHUB_WORKFLOW_FILE`: 默认 `sync.yml`

说明:

- 当前 Worker 已写死 GitHub 仓库目标为 `rianlu/xixun-parser`
- 不再要求配置 `GITHUB_OWNER` 和 `GITHUB_REPO`

### 4. Telegram 设置 webhook

部署 Worker 后，将 Telegram webhook 指向 Worker 根地址，不是 `/health`。

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<YOUR_WORKER_SUBDOMAIN>.workers.dev" \
  -d "secret_token=<YOUR_TELEGRAM_SECRET_TOKEN>"
```

检查 webhook 是否生效:

```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

健康检查:

```bash
curl "https://<YOUR_WORKER_SUBDOMAIN>.workers.dev/health"
```

### 5. 触发方式

- 直接给 Telegram Bot 发送一条“纯微信公众号链接”
- 当前 Worker 只接受整条消息就是链接的格式，例如:

```text
https://mp.weixin.qq.com/s/xxxxxx
```

不会触发的格式:

```text
帮我解析这个链接：https://mp.weixin.qq.com/s/xxxxxx
```

### 6. 正常回执顺序

用户发送链接后，预期消息顺序:

1. Telegram 立即收到: `⌛ 已接收链接，正在解析同步中`
2. GitHub Actions 触发并执行解析
3. Telegram 收到最终结果:
   - 成功: `✅ 戏讯解析同步完成`
   - 失败: `❌ 戏讯解析同步失败，请查看 GitHub Actions 日志`

### 7. 常见排查

- `getWebhookInfo` 显示 `500 Internal Server Error`:
  - 查看 Cloudflare Worker 日志
- Telegram 发 `hello` 没回复:
  - 检查 Worker 是否已部署到最新 GitHub commit
  - 检查 Cloudflare 中 `TELEGRAM_BOT_TOKEN` 是否为当前有效 token
  - 检查 `TELEGRAM_SECRET_TOKEN` 是否与 `setWebhook` 使用值一致
- Telegram 发链接无反应:
  - 检查消息是否为“纯链接”
- GitHub Actions 未触发:
  - 检查 Cloudflare 中 `GITHUB_TOKEN` 权限

### 8. 安全注意事项

- 不要把 `TELEGRAM_BOT_TOKEN`、`GITHUB_TOKEN`、`TELEGRAM_SECRET_TOKEN` 提交到仓库
- 如果 token 在聊天、截图或日志中泄露，应立即旋转并同步更新 Cloudflare 与 GitHub Secrets
- Cloudflare 中敏感配置优先使用 Secrets，而不是普通 Variables

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
