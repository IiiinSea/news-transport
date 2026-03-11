from .base import BaseSpider
from .sina import SinaSpider
from .netease import NeteaseSpider
from .tencent import TencentSpider
from .thepaper import ThePaperSpider

# 爬虫映射
SPIDER_MAP = {
    'sina': SinaSpider,
    'netease': NeteaseSpider,
    'tencent': TencentSpider,
    'thepaper': ThePaperSpider,
}

def get_spider(source_name):
    """获取爬虫实例"""
    spider_cls = SPIDER_MAP.get(source_name)
    if not spider_cls:
        raise ValueError(f"不支持的新闻来源: {source_name}")
    return spider_cls()

def get_all_spiders():
    """获取所有可用爬虫实例"""
    return [cls() for cls in SPIDER_MAP.values()]
