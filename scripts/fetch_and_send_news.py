#!/usr/bin/env python3
"""
新闻搜集、汇总、发送一体化脚本 - News Transport Skill
功能：根据用户输入的关键词，自动从多个新闻源搜集新闻，AI汇总总结，发送精美邮件简报
"""
import sys
import os
import asyncio
from datetime import datetime
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 配置
CONFIG = {
    # 新闻源配置
    'news_sources': [
        {
            'name': '百度新闻',
            'url': 'https://www.baidu.com/s?wd={keyword}&tn=news',
            'selector': '.result-op.c-container, .c-result',
            'title_selector': 'h3',
            'summary_selector': '.c-abstract',
            'time_selector': '.c-author, .c-time',
            'source_selector': '.c-source',
            'link_selector': 'a'
        },
        {
            'name': '新浪新闻',
            'url': 'https://search.sina.com.cn/?q={keyword}&c=news&ie=utf-8',
            'selector': '.result',
            'title_selector': 'h2 a',
            'summary_selector': '.content',
            'time_selector': '.fgray_time',
            'source_selector': '.source',
            'link_selector': 'h2 a'
        },
        {
            'name': '腾讯新闻',
            'url': 'https://news.qq.com/search?query={keyword}',
            'selector': '.list li',
            'title_selector': 'h3 a',
            'summary_selector': '.detail',
            'time_selector': '.time',
            'source_selector': '.source',
            'link_selector': 'h3 a'
        }
    ],
    
    # 邮件配置 - 请根据实际情况修改
    'smtp': {
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465,
        'smtp_ssl': True,
        'sender_email': '你的发件邮箱@qq.com',
        'sender_password': '你的16位授权码',
        'receiver_email': '330146530@qq.com',
        'subject_prefix': '【智能新闻简报】'
    },
    
    # 搜索配置
    'max_news_per_source': 5,
    'total_max_news': 15,
    'summary_length': 300
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
}

class NewsItem:
    """新闻条目类"""
    def __init__(self, title: str, summary: str, time: str, source: str, link: str, source_platform: str):
        self.title = title
        self.summary = summary
        self.time = time
        self.source = source
        self.link = link
        self.source_platform = source_platform
        self.timestamp = datetime.now()

async def fetch_news_from_source(source_config: Dict, keyword: str) -> List[NewsItem]:
    """从单个新闻源获取新闻"""
    news_list = []
    source_name = source_config['name']
    url = source_config['url'].format(keyword=urllib.parse.quote(keyword))
    
    print(f"🔍 正在从 {source_name} 搜索 '{keyword}'...")
    
    try:
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        
        items = soup.select(source_config['selector'])
        count = 0
        
        for item in items:
            if count >= CONFIG['max_news_per_source']:
                break
                
            try:
                title_elem = item.select_one(source_config['title_selector'])
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                if not title:
                    continue
                    
                summary_elem = item.select_one(source_config['summary_selector'])
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                time_elem = item.select_one(source_config['time_selector'])
                time = time_elem.get_text(strip=True) if time_elem else ''
                
                source_elem = item.select_one(source_config['source_selector'])
                source = source_elem.get_text(strip=True) if source_elem else source_name
                
                link_elem = item.select_one(source_config['link_selector'])
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
                
                # 清理摘要长度
                if len(summary) > CONFIG['summary_length']:
                    summary = summary[:CONFIG['summary_length']] + '...'
                
                news_item = NewsItem(
                    title=title,
                    summary=summary,
                    time=time,
                    source=source,
                    link=link,
                    source_platform=source_name
                )
                
                news_list.append(news_item)
                count += 1
                
            except Exception as e:
                continue
                
        print(f"✅ {source_name} 找到 {len(news_list)} 条相关新闻")
        return news_list
        
    except Exception as e:
        print(f"❌ {source_name} 搜索失败: {str(e)}")
        return []

async def fetch_all_news(keyword: str) -> List[NewsItem]:
    """从所有新闻源获取新闻"""
    print(f"\n🚀 开始全网搜索新闻，关键词: {keyword}\n")
    
    tasks = []
    for source in CONFIG['news_sources']:
        task = fetch_news_from_source(source, keyword)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # 合并结果并去重
    all_news = []
    seen_titles = set()
    
    for news_list in results:
        for news in news_list:
            if news.title not in seen_titles and len(news.title) > 10:
                seen_titles.add(news.title)
                all_news.append(news)
    
    # 按时间排序（如果有时间信息）
    all_news.sort(key=lambda x: x.time if x.time else '', reverse=True)
    
    # 限制总数量
    all_news = all_news[:CONFIG['total_max_news']]
    
    print(f"\n📊 汇总完成，共找到 {len(all_news)} 条不重复的相关新闻")
    return all_news

def generate_summary(news_list: List[NewsItem], keyword: str) -> str:
    """生成新闻汇总摘要"""
    if not news_list:
        return "暂未找到相关新闻。"
    
    # 简单的汇总逻辑 - 可以接入LLM进行更智能的总结
    total_sources = len(set(news.source_platform for news in news_list))
    
    summary = f"本次共搜集到来自 {total_sources} 个平台的 {len(news_list)} 条关于 '{keyword}' 的最新新闻。"
    summary += " 以下是最新动态汇总：\n\n"
    
    # 分类统计来源
    source_stats = {}
    for news in news_list:
        if news.source_platform in source_stats:
            source_stats[news.source_platform] += 1
        else:
            source_stats[news.source_platform] = 1
    
    summary += "📰 来源分布：\n"
    for source, count in source_stats.items():
        summary += f"  • {source}: {count} 条\n"
    
    return summary

def generate_html_email(news_list: List[NewsItem], keyword: str, summary: str) -> str:
    """生成HTML格式的邮件内容"""
    date_str = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>新闻简报 - {keyword}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
                line-height: 1.8;
                background-color: #f5f7fa;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .header .date {{
                margin-top: 10px;
                font-size: 16px;
                opacity: 0.9;
            }}
            .header .keyword {{
                margin-top: 5px;
                font-size: 20px;
                font-weight: bold;
                background: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 20px;
                display: inline-block;
            }}
            .summary-section {{
                background: white;
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                border-left: 4px solid #667eea;
            }}
            .summary-section h2 {{
                font-size: 20px;
                color: #667eea;
                margin-bottom: 15px;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 10px;
            }}
            .summary-content {{
                font-size: 16px;
                color: #555;
                white-space: pre-line;
            }}
            .news-list {{
                display: grid;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .news-item {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                transition: transform 0.2s, box-shadow 0.2s;
                border-left: 4px solid #667eea;
            }}
            .news-item:hover {{
                transform: translateY(-3px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.12);
            }}
            .news-title {{
                font-size: 18px;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 12px;
                line-height: 1.5;
            }}
            .news-title a {{
                color: #2c3e50;
                text-decoration: none;
                transition: color 0.2s;
            }}
            .news-title a:hover {{
                color: #667eea;
            }}
            .news-meta {{
                display: flex;
                gap: 20px;
                margin-bottom: 12px;
                font-size: 14px;
                color: #7f8c8d;
            }}
            .news-meta span {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            .news-source {{
                background: #e8f4fd;
                color: #3498db;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            .news-platform {{
                background: #fceef5;
                color: #e84393;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            .news-summary {{
                font-size: 15px;
                color: #555;
                line-height: 1.7;
                margin-bottom: 10px;
            }}
            .news-link {{
                font-size: 14px;
            }}
            .news-link a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }}
            .news-link a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                text-align: center;
                padding: 25px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                color: #95a5a6;
                font-size: 14px;
            }}
            .footer a {{
                color: #667eea;
                text-decoration: none;
            }}
            .no-news {{
                text-align: center;
                padding: 50px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                color: #95a5a6;
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 智能新闻简报</h1>
            <div class="date">{date_str}</div>
            <div class="keyword">关键词：{keyword}</div>
        </div>
        
        <div class="summary-section">
            <h2>📊 汇总概览</h2>
            <div class="summary-content">{summary}</div>
        </div>
    """
    
    if not news_list:
        html += """
        <div class="no-news">
            <p>😔 暂时没有找到相关新闻，请稍后再试或更换关键词。</p>
        </div>
        """
    else:
        html += '<div class="news-list">'
        
        for i, news in enumerate(news_list, 1):
            html += f"""
            <div class="news-item">
                <div class="news-title">
                    <a href="{news.link}" target="_blank">{i}. {news.title}</a>
                </div>
                <div class="news-meta">
                    <span>⏰ {news.time if news.time else '未知时间'}</span>
                    <span class="news-source">{news.source}</span>
                    <span class="news-platform">{news.source_platform}</span>
                </div>
                <div class="news-summary">
                    {news.summary if news.summary else '暂无摘要'}
                </div>
                <div class="news-link">
                    🔗 <a href="{news.link}" target="_blank">查看原文</a>
                </div>
            </div>
            """
        
        html += '</div>'
    
    html += """
        <div class="footer">
            <p>由 <a href="https://github.com/IiiinSea/news-transport">News Transport</a> 智能新闻系统自动生成</p>
            <p>📧 如有问题或建议，请联系管理员</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(html_content: str, keyword: str) -> bool:
    """发送邮件"""
    smtp_config = CONFIG['smtp']
    date_str = datetime.now().strftime('%Y-%m-%d')
    subject = f"{smtp_config['subject_prefix']} {keyword} - {date_str}"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = Header(f"新闻简报系统 <{smtp_config['sender_email']}>", 'utf-8')
        msg['To'] = Header(smtp_config['receiver_email'], 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        if smtp_config['smtp_ssl']:
            server = smtplib.SMTP_SSL(smtp_config['smtp_server'], smtp_config['smtp_port'])
        else:
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
        
        server.login(smtp_config['sender_email'], smtp_config['sender_password'])
        server.sendmail(smtp_config['sender_email'], smtp_config['receiver_email'], msg.as_string())
        server.quit()
        
        print(f"\n✅ 邮件发送成功！已发送到 {smtp_config['receiver_email']}")
        return True
        
    except Exception as e:
        print(f"\n❌ 邮件发送失败: {str(e)}")
        return False

def print_help():
    """打印帮助信息"""
    print("""
📰 智能新闻搜集发送工具

用法: python fetch_and_send_news.py <关键词> [选项]

选项:
    --no-email      只搜索新闻不发送邮件
    --help, -h      显示帮助信息

示例:
    python fetch_and_send_news.py "美伊局势 最新消息"
    python fetch_and_send_news.py "人工智能 发展趋势" --no-email

配置说明:
    请先修改脚本中的 CONFIG['smtp'] 部分配置你的邮箱信息。
    支持的邮箱: QQ邮箱、163邮箱、Gmail等所有支持SMTP的邮箱。
    """)

async def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print_help()
        return
    
    keyword = sys.argv[1]
    send_email_flag = '--no-email' not in sys.argv
    
    print("=" * 80)
    print(f"🚀 开始执行新闻搜索流程，关键词: {keyword}")
    print("=" * 80)
    
    # Step 1: 多平台并行搜索新闻
    print("\n📊 Step 1/7: 正在从多个平台搜集新闻...")
    news_list = await fetch_all_news(keyword)
    
    if not news_list:
        print("\n❌ 没有找到任何相关新闻，请更换关键词后重试。")
        return
    
    # Step 2: 数据清洗与去重
    print("\n🧹 Step 2/7: 正在进行数据清洗与去重...")
    # 去重逻辑已经在fetch_all_news中实现
    print(f"✅ 数据清洗完成，共获得 {len(news_list)} 条有效不重复新闻")
    
    # Step 3: 生成汇总报告
    print("\n📝 Step 3/7: 正在生成新闻汇总报告...")
    summary = generate_summary(news_list, keyword)
    print("\n" + summary)
    
    # Step 4: 生成HTML邮件内容
    print("\n🎨 Step 4/7: 正在生成HTML邮件内容...")
    html_content = generate_html_email(news_list, keyword, summary)
    
    # Step 5: 保存本地副本
    print("\n💾 Step 5/7: 正在保存本地副本...")
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"news_{keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ 本地副本已保存到: {output_file}")
    
    # Step 6: 发送邮件（强制发送，无需询问）
    if send_email_flag:
        print("\n📤 Step 6/6: 正在发送邮件...")
        success = send_email(html_content, keyword)
        if success:
            print("\n✅ Step 6/6: 邮件发送成功！")
            print(f"📧 已发送到: {CONFIG['smtp']['receiver_email']}")
        else:
            print("\n❌ Step 6/6: 邮件发送失败")
            print("🔄 正在自动重试发送...")
            # 自动重试2次
            retry_count = 0
            max_retries = 2
            while retry_count < max_retries and not success:
                retry_count += 1
                print(f"   重试 {retry_count}/{max_retries}...")
                success = send_email(html_content, keyword)
                if success:
                    print("✅ 重试发送成功！")
                    break
            
            if not success:
                print("❌ 多次重试失败，请检查SMTP配置")
                print("⚠️  新闻文件已保存到本地，可手动查看")
    else:
        print("\n✅ Step 6/6: 已跳过邮件发送（--no-email 参数）")
    
    print("\n🎉 所有操作完成！")
    
    print("\n" + "=" * 80)
    print("🎉 流程执行结束")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
