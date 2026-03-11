import telegram
from loguru import logger
from .base import BasePublisher
from telegram import InputMediaPhoto

class TelegramPublisher(BasePublisher):
    """Telegram频道发布器"""
    
    def __init__(self, config):
        super().__init__('telegram', config)
        self.bot = None
        self.chat_id = config.get('chat_id', '')
        if self.enabled:
            self._init_bot()
    
    def _init_bot(self):
        """初始化Telegram Bot"""
        try:
            self.bot = telegram.Bot(token=self.config['bot_token'])
            logger.info("Telegram Bot 初始化成功")
        except Exception as e:
            logger.error(f"Telegram Bot 初始化失败: {str(e)}")
            self.enabled = False
    
    def publish(self, news_item):
        """发布新闻到Telegram频道"""
        if not self.bot or not self.chat_id:
            return {'success': False, 'error_message': 'Bot未初始化或未配置频道ID'}
        
        try:
            # 构建消息内容
            title = news_item.translated_title or news_item.title
            content = news_item.translated_content or news_item.content
            source = news_item.source
            source_url = news_item.source_url
            
            # 格式化消息（Markdown格式）
            message_text = f"*📰 {title}*\n\n{content[:1000]}...\n\n"
            message_text += f"📌 来源: [{source}]({source_url})\n"
            message_text += f"🕒 发布时间: {news_item.publish_time.strftime('%Y-%m-%d %H:%M')}"
            
            # 发送消息
            if news_item.image_url:
                # 带图片的消息
                try:
                    # 发送带图片的Markdown消息
                    message = self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=news_item.image_url,
                        caption=message_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.warning(f"图片发送失败，将发送纯文本消息: {str(e)}")
                    message = self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
            else:
                # 纯文本消息
                message = self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            
            # 构建返回结果
            post_url = f"https://t.me/{message.chat.username}/{message.message_id}" if message.chat.username else ''
            
            return {
                'success': True,
                'post_id': str(message.message_id),
                'post_url': post_url,
                'error_message': ''
            }
            
        except Exception as e:
            return {'success': False, 'error_message': str(e)}
    
    def delete_post(self, post_id):
        """删除已发布的消息"""
        try:
            self.bot.delete_message(chat_id=self.chat_id, message_id=int(post_id))
            return True
        except Exception as e:
            logger.error(f"删除Telegram消息失败: {str(e)}")
            return False
    
    def send_media_group(self, news_list):
        """批量发送媒体组（适合多条新闻聚合发布）"""
        try:
            media_group = []
            for news in news_list[:10]:  # Telegram限制最多10个媒体
                if news.image_url:
                    caption = f"*📰 {news.translated_title or news.title}*\n\n来源: {news.source}"
                    media_group.append(InputMediaPhoto(
                        media=news.image_url,
                        caption=caption,
                        parse_mode='Markdown'
                    ))
            
            if media_group:
                messages = self.bot.send_media_group(
                    chat_id=self.chat_id,
                    media=media_group
                )
                return [str(msg.message_id) for msg in messages]
            return []
        except Exception as e:
            logger.error(f"发送媒体组失败: {str(e)}")
            return []
