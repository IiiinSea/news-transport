# 新闻搬运系统

自动汇总国内热点新闻，智能处理后发布到海外平台。

## 功能特性

- 🕷️ **多平台爬虫**：支持新浪、网易、腾讯、澎湃等主流新闻平台
- 📝 **智能摘要**：使用AI提取新闻核心内容
- 🌐 **自动翻译**：支持中英文互译，保留新闻原意
- ✅ **审核机制**：后台管理界面支持内容审核
- 🚀 **多平台发布**：支持Twitter/X、Facebook、LinkedIn、Medium等平台
- ⏰ **定时任务**：可配置的爬取和发布频率
- 📊 **数据统计**：发布效果统计和分析

## 架构设计

```
news-transport/
├── spiders/          # 新闻爬虫模块
├── processors/       # 内容处理模块（摘要、翻译、分类）
├── publishers/       # 海外平台发布模块
├── utils/            # 工具函数
├── config/           # 配置文件
├── web/              # 后台管理界面
└── main.py           # 主程序入口
```

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置平台密钥：
编辑 `config/settings.py`，添加各平台的API密钥。

3. 运行爬虫：
```bash
python main.py crawl
```

4. 启动后台管理：
```bash
python main.py web
```

## 支持的平台

### 新闻来源
- 新浪新闻
- 网易新闻
- 腾讯新闻
- 澎湃新闻
- 新华网
- 人民网

### 发布平台
- Twitter/X
- Facebook
- LinkedIn
- Medium
- Telegram Channel
- Reddit

## 配置说明

参见 `config/settings.example.py` 详细配置说明。
