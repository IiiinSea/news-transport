from .base import BasePublisher
from .twitter import TwitterPublisher
from .telegram import TelegramPublisher
from config import PUBLISH_PLATFORMS

# 发布器映射
PUBLISHER_MAP = {
    'twitter': TwitterPublisher,
    'telegram': TelegramPublisher,
    # 可以继续添加其他平台
    # 'facebook': FacebookPublisher,
    # 'linkedin': LinkedInPublisher,
    # 'medium': MediumPublisher,
    # 'reddit': RedditPublisher,
}

def get_publisher(platform_name):
    """获取发布器实例"""
    publisher_cls = PUBLISHER_MAP.get(platform_name)
    if not publisher_cls:
        raise ValueError(f"不支持的发布平台: {platform_name}")
    config = PUBLISH_PLATFORMS.get(platform_name, {})
    return publisher_cls(config)

def get_enabled_publishers():
    """获取所有已启用的发布器实例"""
    publishers = []
    for platform_name, config in PUBLISH_PLATFORMS.items():
        if config.get('enabled', False) and platform_name in PUBLISHER_MAP:
            publisher_cls = PUBLISHER_MAP[platform_name]
            publishers.append(publisher_cls(config))
    return publishers
