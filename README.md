# 📰 News Transport - 智能新闻搜集分发系统

自动化新闻搜索、汇总、邮件分发工具，支持多平台新闻采集、AI 总结、精美邮件推送。

## ✨ 核心特性

- 🚀 **一键触发**：只需说「查找XX新闻」，自动完成全流程
- 🌐 **多平台采集**：支持百度、新浪、腾讯三大新闻源
- 🧠 **智能去重**：自动去除不同平台重复内容
- 📊 **自动汇总**：生成新闻概览和来源分布统计
- 🎨 **精美邮件**：现代化响应式 HTML 简报，完美适配手机/电脑
- 💾 **本地备份**：自动保存 HTML 版本到本地，方便历史查阅
- ⚡ **异步加速**：多平台并行搜索，速度提升 300%
- 🔧 **高度可配置**：支持自定义新闻源、搜索数量、邮件模板等

## 🚀 快速使用

### 最简单的使用方式
只要说：
```
查找美伊局势最新新闻
```
系统会自动：
1. 从百度、新浪、腾讯搜索相关新闻
2. 去重、汇总、整理
3. 生成精美的 HTML 简报
4. 发送到你的邮箱

### 命令行调用
```bash
# 完整流程：搜索 -> 汇总 -> 发邮件
uv run scripts/fetch_and_send_news.py "美伊局势 最新消息"

# 只搜索不发邮件
uv run scripts/fetch_and_send_news.py "人工智能 发展趋势" --no-email

# 简单搜索，命令行输出
uv run scripts/search_news.py "科技新闻"
```

## ⚙️ 配置说明

### 1. 邮箱配置
编辑 `scripts/fetch_and_send_news.py` 中的 SMTP 配置：
```python
'smtp': {
    'smtp_server': 'smtp.qq.com',      # SMTP 服务器地址
    'smtp_port': 465,                   # SMTP 端口
    'smtp_ssl': True,                   # 是否使用 SSL
    'sender_email': '你的邮箱@qq.com',   # 发件人邮箱
    'sender_password': '你的授权码',     # 邮箱授权码（不是登录密码）
    'receiver_email': '收件邮箱@qq.com', # 收件人邮箱
    'subject_prefix': '【智能新闻简报】'  # 邮件标题前缀
}
```

支持所有主流邮箱：QQ邮箱、163邮箱、Gmail、企业邮箱等。

### 2. 搜索配置
```python
'max_news_per_source': 5,       # 每个新闻源最多返回条数
'total_max_news': 15,            # 总共最多返回条数
'summary_length': 300,           # 新闻摘要最大长度
```

### 3. 新闻源配置
默认支持三大新闻源，可在 `CONFIG['news_sources']` 中添加更多：
- 百度新闻
- 新浪新闻
- 腾讯新闻

## 📁 项目结构

```
news-transport/
├── SKILL.md                # OpenClaw Skill 说明文档
├── pyproject.toml          # Python 项目配置
├── uv.lock                 # 依赖锁定文件
├── .clawhook               # OpenClaw 自动触发钩子
├── README.md               # 本说明文件
├── scripts/                # 快捷调用脚本
│   ├── fetch_and_send_news.py  # 一体化新闻搜集发送脚本（推荐）
│   ├── search_news.py          # 简单新闻搜索脚本
│   └── send_news_email.py      # 预设主题邮件发送脚本
└── news-transport/         # 完整新闻系统源码
    ├── config/             # 配置文件
    ├── spiders/            # 爬虫模块
    ├── processors/         # 数据处理模块（摘要、翻译、审核）
    ├── publishers/         # 发布模块（邮件、Telegram、Twitter等）
    ├── utils/              # 工具函数
    ├── web/                # Web 管理界面
    └── main.py             # 系统入口
```

## 🛠️ 安装部署

### 1. 环境要求
- Python >= 3.12
- uv (Python 包管理器)

### 2. 安装依赖
```bash
uv sync
```

### 3. 配置邮箱
按照上面的说明配置 SMTP 信息。

### 4. 测试运行
```bash
uv run scripts/fetch_and_send_news.py "测试新闻" --no-email
```

## 📧 邮件效果

- ✨ 渐变紫色主题，现代简约设计
- 📱 完全响应式，手机/电脑完美适配
- 📊 汇总概览，显示来源分布和统计信息
- 📰 每条新闻包含标题、时间、来源、平台、摘要、原文链接
- 💡 智能摘要，自动截取核心内容
- 🔗 点击标题或原文链接直接跳转

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
