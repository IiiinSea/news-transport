import requests
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger
from fake_useragent import UserAgent
from config import USER_AGENT, CRAWL_TIMEOUT
from utils import get_db, News

class BaseSpider(ABC):
    """爬虫基类"""
    
    def __init__(self, source_name, base_url):
        self.source_name = source_name
        self.base_url = base_url
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT or self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get(self, url, **kwargs):
        """发送GET请求"""
        try:
            kwargs.setdefault('timeout', CRAWL_TIMEOUT)
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            time.sleep(random.uniform(1, 3))  # 随机延迟，避免被封
            return response
        except Exception as e:
            logger.error(f"请求失败 {url}: {str(e)}")
            raise
    
    def post(self, url, **kwargs):
        """发送POST请求"""
        try:
            kwargs.setdefault('timeout', CRAWL_TIMEOUT)
            response = self.session.post(url, **kwargs)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            time.sleep(random.uniform(1, 3))
            return response
        except Exception as e:
            logger.error(f"POST请求失败 {url}: {str(e)}")
            raise
    
    def parse_html(self, html):
        """解析HTML"""
        return BeautifulSoup(html, 'lxml')
    
    def save_news(self, news_data):
        """保存新闻到数据库"""
        db = next(get_db())
        try:
            # 检查是否已存在
            existing = db.query(News).filter(News.source_url == news_data['source_url']).first()
            if existing:
                logger.info(f"新闻已存在: {news_data['title']}")
                return existing
            
            news = News(**news_data)
            db.add(news)
            db.commit()
            db.refresh(news)
            logger.success(f"保存新闻成功: {news.title}")
            return news
        except Exception as e:
            db.rollback()
            logger.error(f"保存新闻失败: {str(e)}")
            raise
        finally:
            db.close()
    
    def extract_publish_time(self, time_str):
        """提取发布时间"""
        # 处理各种时间格式
        time_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y年%m月%d日 %H:%M',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%m-%d %H:%M',
            '%m月%d日 %H:%M',
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        # 如果都不匹配，返回当前时间
        logger.warning(f"无法解析时间格式: {time_str}，使用当前时间")
        return datetime.now()
    
    def clean_text(self, text):
        """清理文本内容"""
        if not text:
            return ""
        # 移除多余空白字符
        text = ' '.join(text.split())
        # 移除特殊字符
        text = text.replace('\u3000', ' ').replace('\xa0', ' ')
        return text.strip()
    
    @abstractmethod
    def crawl(self, max_count=20):
        """爬取新闻的抽象方法
        返回爬取到的新闻数量
        """
        pass
