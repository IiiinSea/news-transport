# 系统配置
import os
from dotenv import load_dotenv

load_dotenv()

# 基础配置
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
TIMEZONE = 'Asia/Shanghai'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///news.db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# 爬虫配置
CRAWL_INTERVAL = int(os.getenv('CRAWL_INTERVAL', 3600))  # 爬取间隔，单位秒
MAX_NEWS_PER_SOURCE = int(os.getenv('MAX_NEWS_PER_SOURCE', 20))  # 每个来源最多爬取新闻数
CRAWL_TIMEOUT = int(os.getenv('CRAWL_TIMEOUT', 30))  # 爬虫超时时间

# 新闻来源配置
NEWS_SOURCES = {
    'sina': {
        'name': '新浪新闻',
        'url': 'https://news.sina.com.cn/',
        'enabled': True
    },
    'netease': {
        'name': '网易新闻',
        'url': 'https://news.163.com/',
        'enabled': True
    },
    'tencent': {
        'name': '腾讯新闻',
        'url': 'https://news.qq.com/',
        'enabled': True
    },
    'thepaper': {
        'name': '澎湃新闻',
        'url': 'https://www.thepaper.cn/',
        'enabled': True
    },
    'xinhua': {
        'name': '新华网',
        'url': 'http://www.xinhuanet.com/',
        'enabled': True
    }
}

# AI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
SUMMARY_LENGTH = int(os.getenv('SUMMARY_LENGTH', 200))  # 摘要长度
TRANSLATION_ENGINE = os.getenv('TRANSLATION_ENGINE', 'google')  # google / openai

# 审核配置
AUTO_AUDIT = os.getenv('AUTO_AUDIT', 'False').lower() == 'true'  # 是否自动审核
AUTO_AUDIT_THRESHOLD = float(os.getenv('AUTO_AUDIT_THRESHOLD', 0.8))  # 自动审核阈值

# 发布平台配置
PUBLISH_PLATFORMS = {
    'twitter': {
        'enabled': os.getenv('TWITTER_ENABLED', 'False').lower() == 'true',
        'api_key': os.getenv('TWITTER_API_KEY', ''),
        'api_secret': os.getenv('TWITTER_API_SECRET', ''),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
        'access_secret': os.getenv('TWITTER_ACCESS_SECRET', '')
    },
    'facebook': {
        'enabled': os.getenv('FACEBOOK_ENABLED', 'False').lower() == 'true',
        'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN', ''),
        'page_id': os.getenv('FACEBOOK_PAGE_ID', '')
    },
    'linkedin': {
        'enabled': os.getenv('LINKEDIN_ENABLED', 'False').lower() == 'true',
        'client_id': os.getenv('LINKEDIN_CLIENT_ID', ''),
        'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET', ''),
        'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    },
    'medium': {
        'enabled': os.getenv('MEDIUM_ENABLED', 'False').lower() == 'true',
        'token': os.getenv('MEDIUM_TOKEN', ''),
        'user_id': os.getenv('MEDIUM_USER_ID', '')
    },
    'telegram': {
        'enabled': os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true',
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID', '')
    }
}

# 发布配置
PUBLISH_INTERVAL = int(os.getenv('PUBLISH_INTERVAL', 1800))  # 发布间隔，单位秒
MAX_PUBLISH_PER_TIME = int(os.getenv('MAX_PUBLISH_PER_TIME', 5))  # 每次最多发布条数
PUBLISH_TIME_WINDOW = (8, 22)  # 发布时间窗口，只在这个时间段内发布

# Web管理后台配置
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', 5000))
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
