from abc import ABC, abstractmethod
from loguru import logger
from datetime import datetime
from utils import get_db, PublishRecord

class BasePublisher(ABC):
    """发布器基类"""
    
    def __init__(self, platform_name, config):
        """
        初始化发布器
        :param platform_name: 平台名称
        :param config: 平台配置
        """
        self.platform_name = platform_name
        self.config = config
        self.enabled = config.get('enabled', False)
    
    @abstractmethod
    def publish(self, news_item):
        """
        发布新闻的抽象方法
        :param news_item: 新闻对象
        :return: 发布结果字典，包含success（bool）、post_id、post_url、error_message
        """
        pass
    
    def save_publish_record(self, news_id, publish_result):
        """
        保存发布记录
        :param news_id: 新闻ID
        :param publish_result: 发布结果字典
        """
        db = next(get_db())
        try:
            record = PublishRecord(
                news_id=news_id,
                platform=self.platform_name,
                post_id=publish_result.get('post_id', ''),
                post_url=publish_result.get('post_url', ''),
                status='success' if publish_result.get('success') else 'failed',
                error_message=publish_result.get('error_message', '')
            )
            db.add(record)
            db.commit()
            logger.success(f"发布记录已保存: {self.platform_name} 新闻ID:{news_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"保存发布记录失败: {str(e)}")
        finally:
            db.close()
    
    def update_news_publish_status(self, news_item, publish_result):
        """
        更新新闻的发布状态
        :param news_item: 新闻对象
        :param publish_result: 发布结果字典
        """
        db = next(get_db())
        try:
            if publish_result.get('success'):
                # 添加到已发布平台
                platforms = news_item.published_platforms or ''
                if platforms:
                    platforms += ',' + self.platform_name
                else:
                    platforms = self.platform_name
                news_item.published_platforms = platforms
                news_item.status = 'published'
                news_item.published_time = datetime.now()
                news_item.publish_error = ''
            else:
                # 更新错误信息
                errors = news_item.publish_error or ''
                if errors:
                    errors += f"\n{self.platform_name}: {publish_result.get('error_message', '未知错误')}"
                else:
                    errors = f"{self.platform_name}: {publish_result.get('error_message', '未知错误')}"
                news_item.publish_error = errors
            
            db.add(news_item)
            db.commit()
            logger.success(f"新闻发布状态已更新: {news_item.title[:50]}...")
        except Exception as e:
            db.rollback()
            logger.error(f"更新新闻发布状态失败: {str(e)}")
        finally:
            db.close()
    
    def publish_and_record(self, news_item):
        """
        发布新闻并记录结果
        :param news_item: 新闻对象
        :return: 发布结果
        """
        if not self.enabled:
            logger.info(f"{self.platform_name} 发布未启用，跳过")
            return {'success': False, 'error_message': '平台未启用'}
        
        try:
            logger.info(f"开始发布到 {self.platform_name}: {news_item.title[:50]}...")
            result = self.publish(news_item)
            
            # 保存发布记录
            self.save_publish_record(news_item.id, result)
            
            # 更新新闻状态
            self.update_news_publish_status(news_item, result)
            
            if result.get('success'):
                logger.success(f"发布到 {self.platform_name} 成功: {result.get('post_url', '')}")
            else:
                logger.error(f"发布到 {self.platform_name} 失败: {result.get('error_message', '')}")
            
            return result
            
        except Exception as e:
            error_msg = f"发布异常: {str(e)}"
            logger.error(error_msg)
            result = {'success': False, 'error_message': error_msg}
            self.save_publish_record(news_item.id, result)
            return result
    
    def get_stats(self, days=7):
        """
        获取发布统计数据
        :param days: 统计天数
        :return: 统计数据字典
        """
        from sqlalchemy import func, and_
        from datetime import timedelta
        
        db = next(get_db())
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 总发布数
            total = db.query(PublishRecord).filter(
                and_(
                    PublishRecord.platform == self.platform_name,
                    PublishRecord.publish_time >= start_time,
                    PublishRecord.publish_time <= end_time
                )
            ).count()
            
            # 成功发布数
            success = db.query(PublishRecord).filter(
                and_(
                    PublishRecord.platform == self.platform_name,
                    PublishRecord.status == 'success',
                    PublishRecord.publish_time >= start_time,
                    PublishRecord.publish_time <= end_time
                )
            ).count()
            
            # 总互动量
            stats = db.query(
                func.sum(PublishRecord.views).label('total_views'),
                func.sum(PublishRecord.likes).label('total_likes'),
                func.sum(PublishRecord.shares).label('total_shares'),
                func.sum(PublishRecord.comments).label('total_comments')
            ).filter(
                and_(
                    PublishRecord.platform == self.platform_name,
                    PublishRecord.publish_time >= start_time,
                    PublishRecord.publish_time <= end_time
                )
            ).first()
            
            return {
                'platform': self.platform_name,
                'period_days': days,
                'total_published': total,
                'success_count': success,
                'success_rate': success / total * 100 if total > 0 else 0,
                'total_views': stats.total_views or 0,
                'total_likes': stats.total_likes or 0,
                'total_shares': stats.total_shares or 0,
                'total_comments': stats.total_comments or 0
            }
        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}")
            return {}
        finally:
            db.close()
