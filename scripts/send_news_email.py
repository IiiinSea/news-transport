#!/usr/bin/env python3
"""
新闻邮件发送脚本 - News Transport Skill
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
import sys
import os

# 添加新闻系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'news-transport'))

from utils import get_db, News

# 邮件配置
SMTP_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 465,
    'smtp_ssl': True,
    'sender_email': '你的发件邮箱@qq.com',  # 请配置你的发件邮箱
    'sender_password': '你的16位授权码',      # 请配置你的邮箱授权码
    'receiver_email': '330146530@qq.com',    # 收件邮箱
    'subject_prefix': '【国际新闻简报】'
}

def send_news_email(keywords=['美', '伊', '冲突', '袭击', '伊拉克', '霍尔木兹', '中东', '伊朗', '美国'], limit=5):
    """发送新闻邮件"""
    
    # 获取最新的新闻
    db = next(get_db())
    news_list = db.query(News).order_by(News.created_at.desc()).limit(20).all()
    
    if not news_list:
        print("❌ 没有找到新闻")
        return False
    
    # 筛选相关新闻
    related_news = []
    for news in news_list:
        if any(k in news.title for k in keywords):
            related_news.append(news)
            if len(related_news) >= limit:
                break
    
    if not related_news:
        print("❌ 没有找到相关新闻")
        return False
    
    print(f"✅ 找到 {len(related_news)} 条相关新闻，正在生成邮件...")
    
    # 构建HTML邮件内容
    date_str = datetime.now().strftime('%Y年%m月%d日')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>最新新闻简报 {date_str}</title>
        <style>
            body {{
                font-family: "Microsoft YaHei", Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
                line-height: 1.6;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .date {{
                margin-top: 10px;
                font-size: 16px;
                opacity: 0.9;
            }}
            .news-item {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                border-left: 4px solid #667eea;
            }}
            .news-title {{
                font-size: 18px;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 10px;
            }}
            .news-title a {{
                color: #667eea;
                text-decoration: none;
            }}
            .news-meta {{
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
            }}
            .news-content {{
                font-size: 16px;
                color: #444;
                margin-bottom: 10px;
            }}
            .source {{
                color: #999;
                font-size: 14px;
            }}
            .source a {{
                color: #667eea;
                text-decoration: none;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 最新新闻动态</h1>
            <div class="date">{date_str}</div>
        </div>
    """
    
    for i, news in enumerate(related_news, 1):
        title = news.title
        content = news.content[:500] + "..." if len(news.content) > 500 else news.content
        source = news.source
        source_url = news.source_url
        publish_time = news.publish_time.strftime('%Y-%m-%d %H:%M') if news.publish_time else '未知'
        
        html += f"""
        <div class="news-item">
            <div class="news-title">
                <a href="{source_url}" target="_blank">{i}. {title}</a>
            </div>
            <div class="news-meta">
                🕒 {publish_time} | 📰 来源: {source}
            </div>
            <div class="news-content">
                {content}
            </div>
            <div class="source">
                🔗 查看原文: <a href="{source_url}" target="_blank">点击跳转</a>
            </div>
        </div>
        """
    
    html += """
        <div class="footer">
            <p>由新闻搬运系统自动发送 | 订阅请联系管理员</p>
        </div>
    </body>
    </html>
    """
    
    # 发送邮件
    try:
        msg = MIMEMultipart()
        msg['From'] = Header(f"新闻简报 <{SMTP_CONFIG['sender_email']}>", 'utf-8')
        msg['To'] = Header(SMTP_CONFIG['receiver_email'], 'utf-8')
        subject = f"{SMTP_CONFIG['subject_prefix']} {date_str} 最新消息"
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 添加HTML正文
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        
        # 连接SMTP服务器
        if SMTP_CONFIG['smtp_ssl']:
            server = smtplib.SMTP_SSL(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port'])
        else:
            server = smtplib.SMTP(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port'])
        
        server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['sender_password'])
        server.sendmail(SMTP_CONFIG['sender_email'], SMTP_CONFIG['receiver_email'], msg.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功！已发送到 {SMTP_CONFIG['receiver_email']}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

def main():
    # 支持自定义关键词
    keywords = sys.argv[1:] if len(sys.argv) > 1 else ['美', '伊', '冲突', '袭击', '伊拉克', '霍尔木兹', '中东', '伊朗', '美国']
    send_news_email(keywords)

if __name__ == "__main__":
    main()
