---
name: news-transport
description: 新闻爬虫与自动分发系统，支持多源新闻抓取、关键词过滤、自动邮件推送。可定时爬取国际国内新闻，筛选指定主题，生成精美简报并发送到指定邮箱。
author: 用户自定义
version: 1.0.0
homepage: ""
triggers:
  - "搜索新闻"
  - "查找新闻"
  - "发新闻邮件"
  - "新闻简报"
  - "抓取新闻"
  - "美伊新闻"
  - "搜集新闻"
  - "汇总新闻"
  - "发送新闻"
metadata: {"clawdbot":{"emoji":"📰","requires":{"bins":["python3"]}}}
---

# 📰 新闻搬运系统 Skill

自动抓取、筛选和分发新闻的完整系统，支持自定义关键词、定时任务、邮件推送。

## 核心功能
- 🔍 **多源新闻搜索**：支持百度新闻等多个数据源
- 🎯 **关键词过滤**：可自定义关注的主题（如美伊局势、科技新闻等）
- 📊 **数据存储**：SQLite 数据库持久化存储新闻内容
- ✉️ **邮件推送**：自动生成精美的 HTML 格式新闻简报，发送到指定邮箱
- ⏰ **定时任务**：支持定时执行，实现每日/每小时自动推送
- 🌐 **多主题支持**：可扩展抓取不同领域的新闻

## 快速使用

### 1. 智能新闻搜集+汇总+邮件发送（推荐）
```bash
uv run {baseDir}/scripts/fetch_and_send_news.py "<关键词>"
```
自动从百度、新浪、腾讯等多平台搜集新闻，AI汇总总结，生成精美HTML邮件并发送。

示例：`uv run {baseDir}/scripts/fetch_and_send_news.py "美伊局势 最新消息"`

### 2. 只搜索新闻不发邮件
```bash
uv run {baseDir}/scripts/fetch_and_send_news.py "<关键词>" --no-email
```
仅搜索和汇总新闻，保存为本地HTML文件，不发送邮件。

### 3. 简单新闻搜索
```bash
uv run {baseDir}/scripts/search_news.py "<关键词>"
```
快速搜索新闻，在命令行输出结果。

示例：`uv run {baseDir}/scripts/search_news.py "美伊局势 最新消息"`

### 4. 发送预设主题新闻邮件
```bash
uv run {baseDir}/scripts/send_news_email.py
```
自动抓取最新美伊相关新闻，生成简报并发送到配置的邮箱。

### 5. 运行完整新闻采集系统
```bash
cd {baseDir}/news-transport && python main.py
```
启动完整的爬虫流程，定时抓取、处理、存储并分发新闻。

## 配置说明

### 邮件配置
#### 邮箱配置
编辑 `scripts/fetch_and_send_news.py` 中的 CONFIG['smtp'] 部分：
```python
'smtp': {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 465,
    'smtp_ssl': True,
    'sender_email': '你的发件邮箱@qq.com',
    'sender_password': '你的16位授权码',
    'receiver_email': '收件邮箱@example.com',
    'subject_prefix': '【智能新闻简报】'
}
```
支持所有SMTP邮箱：QQ邮箱、163邮箱、Gmail、企业邮箱等。
#### 搜索配置
可配置新闻源、搜索数量、摘要长度等参数：
```python
'max_news_per_source': 5,       # 每个新闻源最多取多少条
'total_max_news': 15,            # 总共最多返回多少条
'summary_length': 300,           # 摘要最大长度
```

### 关键词配置
在 `search_news.py` 或系统配置中修改关注的关键词，支持多个关键词组合。

## 目录结构
```
news-transport/
├── SKILL.md                          # 本说明文件
├── pyproject.toml                    # Python 项目配置
├── scripts/                          # 快捷调用脚本
│   ├── search_news.py               # 新闻搜索脚本
│   └── send_news_email.py           # 邮件发送脚本
└── news-transport/                   # 完整系统源码
    ├── config/                       # 配置文件
    ├── spiders/                      # 爬虫模块
    ├── processors/                   # 数据处理模块
    ├── publishers/                   # 发布模块（邮件、消息等）
    ├── utils/                        # 工具函数
    ├── main.py                       # 系统入口
    └── news.db                       # SQLite 数据库
```

## 依赖安装
```bash
cd {baseDir} && uv sync
```

## 常见问题
1. **邮件发送失败**：检查 SMTP 配置，确认邮箱授权码正确，POP3/SMTP 服务已开启
2. **搜索不到新闻**：检查网络连接，或更换关键词、数据源
3. **数据库报错**：确认 `news.db` 文件存在且有读写权限
