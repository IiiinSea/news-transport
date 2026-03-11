import tweepy
from loguru import logger
from .base import BasePublisher

class TwitterPublisher(BasePublisher):
    """Twitter发布器"""
    
    def __init__(self, config):
        super().__init__('twitter', config)
        self.api = None
        if self.enabled:
            self._init_api()
    
    def _init_api(self):
        """初始化Twitter API"""
        try:
            auth = tweepy.OAuthHandler(
                self.config['api_key'],
                self.config['api_secret']
            )
            auth.set_access_token(
                self.config['access_token'],
                self.config['access_secret']
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            # 验证凭证
            self.api.verify_credentials()
            logger.info("Twitter API 初始化成功")
        except Exception as e:
            logger.error(f"Twitter API 初始化失败: {str(e)}")
            self.enabled = False
    
    def publish(self, news_item):
        """发布新闻到Twitter"""
        if not self.api:
            return {'success': False, 'error_message': 'API未初始化'}
        
        try:
            # 构建推文内容
            title = news_item.translated_title or news_item.title
            summary = news_item.summary or news_item.content[:200] + "..."
            
            # Twitter限制280字符，需要控制长度
            tweet_text = f"📰 {title}\n\n{summary}\n\nSource: {news_item.source_url}"
            
            # 截断超长内容
            if len(tweet_text) > 270:
                summary = summary[:270 - len(title) - len(news_item.source_url) - 20] + "..."
                tweet_text = f"📰 {title}\n\n{summary}\n\nSource: {news_item.source_url}"
            
            # 发布推文
            if news_item.image_url:
                # 有图片的情况
                try:
                    # 下载图片
                    import requests
                    from io import BytesIO
                    
                    response = requests.get(news_item.image_url, timeout=10)
                    response.raise_for_status()
                    
                    # 上传图片
                    media = self.api.media_upload(filename="news.jpg", file=BytesIO(response.content))
                    
                    # 发布带图片的推文
                    status = self.api.update_status(
                        status=tweet_text,
                        media_ids=[media.media_id]
                    )
                except Exception as e:
                    logger.warning(f"图片上传失败，将发布纯文本推文: {str(e)}")
                    status = self.api.update_status(status=tweet_text)
            else:
                # 纯文本推文
                status = self.api.update_status(status=tweet_text)
            
            # 构建返回结果
            post_url = f"https://twitter.com/{status.user.screen_name}/status/{status.id}"
            
            return {
                'success': True,
                'post_id': str(status.id),
                'post_url': post_url,
                'error_message': ''
            }
            
        except Exception as e:
            return {'success': False, 'error_message': str(e)}
    
    def delete_post(self, post_id):
        """删除已发布的推文"""
        try:
            self.api.destroy_status(post_id)
            return True
        except Exception as e:
            logger.error(f"删除推文失败: {str(e)}")
            return False
    
    def get_post_stats(self, post_id):
        """获取推文的统计数据"""
        try:
            status = self.api.get_status(post_id)
            return {
                'views': getattr(status, 'view_count', 0),
                'likes': status.favorite_count,
                'retweets': status.retweet_count,
                'comments': status.reply_count
            }
        except Exception as e:
            logger.error(f"获取推文统计失败: {str(e)}")
            return {}
