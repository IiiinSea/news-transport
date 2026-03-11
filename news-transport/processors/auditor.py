from loguru import logger
from config import AUTO_AUDIT, AUTO_AUDIT_THRESHOLD

class NewsAuditor:
    """新闻内容审核器"""
    
    def __init__(self, auto_audit=AUTO_AUDIT):
        """
        初始化审核器
        :param auto_audit: 是否开启自动审核
        """
        self.auto_audit = auto_audit
        self.threshold = AUTO_AUDIT_THRESHOLD
        
        # 敏感词列表（可扩展）
        self.sensitive_words = {
            # 政治敏感词
            '敏感词1', '敏感词2',
            # 暴力色情
            '暴力', '色情',
            # 其他违规内容
            '赌博', '诈骗'
        }
    
    def audit(self, news_item):
        """
        审核新闻内容
        :param news_item: 新闻对象
        :return: 审核结果字典，包含audit_result（pass/reject）、audit_score、audit_comment
        """
        if not self.auto_audit:
            logger.info("自动审核已关闭，需要人工审核")
            return {
                'audit_result': 'pending',
                'audit_score': 0.0,
                'audit_comment': '等待人工审核'
            }
            
        try:
            logger.info(f"开始审核新闻: {news_item.title[:50]}...")
            
            total_score = 1.0
            issues = []
            
            # 1. 敏感词检测
            sensitive_score, sensitive_issues = self._check_sensitive_words(news_item)
            total_score *= sensitive_score
            issues.extend(sensitive_issues)
            
            # 2. 内容质量检测
            quality_score, quality_issues = self._check_content_quality(news_item)
            total_score *= quality_score
            issues.extend(quality_issues)
            
            # 3. 来源可靠性检测
            source_score, source_issues = self._check_source_reliability(news_item)
            total_score *= source_score
            issues.extend(source_issues)
            
            # 4. 重复内容检测
            duplicate_score, duplicate_issues = self._check_duplicate(news_item)
            total_score *= duplicate_score
            issues.extend(duplicate_issues)
            
            # 确定审核结果
            if total_score >= self.threshold:
                result = 'pass'
                comment = '自动审核通过'
                if issues:
                    comment += f"，注意：{'; '.join(issues)}"
            else:
                result = 'reject'
                comment = '自动审核不通过：' + '；'.join(issues) if issues else '内容不符合发布要求'
            
            logger.info(f"新闻审核完成，得分: {total_score:.2f}, 结果: {result}")
            
            return {
                'audit_result': result,
                'audit_score': total_score,
                'audit_comment': comment
            }
            
        except Exception as e:
            logger.error(f"审核新闻失败: {str(e)}")
            return {
                'audit_result': 'pending',
                'audit_score': 0.0,
                'audit_comment': f'审核出错：{str(e)}，等待人工审核'
            }
    
    def _check_sensitive_words(self, news_item):
        """检测敏感词"""
        score = 1.0
        issues = []
        
        content = (news_item.title + ' ' + news_item.content).lower()
        
        for word in self.sensitive_words:
            if word.lower() in content:
                score *= 0.3
                issues.append(f"包含敏感词：{word}")
        
        return score, issues
    
    def _check_content_quality(self, news_item):
        """检测内容质量"""
        score = 1.0
        issues = []
        
        # 内容长度检测
        if len(news_item.content) < 100:
            score *= 0.5
            issues.append("内容过短")
        
        # 标题内容匹配度
        title_words = set(news_item.title.replace('，', ' ').replace('。', ' ').split())
        content_words = set(news_item.content.replace('，', ' ').replace('。', ' ').split())
        if title_words and content_words:
            overlap = len(title_words & content_words) / len(title_words)
            if overlap < 0.2:
                score *= 0.7
                issues.append("标题与内容相关性低")
        
        # 特殊字符占比
        special_chars = sum(1 for c in news_item.content if not '\u4e00' <= c <= '\u9fff' and not c.isalnum() and c not in '，。、；：？！“”‘’（）【】《》,.;:?!""''()[]<> ')
        if len(news_item.content) > 0 and special_chars / len(news_item.content) > 0.3:
            score *= 0.6
            issues.append("特殊字符过多")
        
        return score, issues
    
    def _check_source_reliability(self, news_item):
        """检测来源可靠性"""
        score = 1.0
        issues = []
        
        # 可靠来源列表
        reliable_sources = {'xinhua', 'people', 'thepaper', 'sina', 'netease', 'tencent'}
        
        if news_item.source not in reliable_sources:
            score *= 0.8
            issues.append(f"来源{news_item.source}可靠性较低")
        
        return score, issues
    
    def _check_duplicate(self, news_item):
        """检测重复内容"""
        score = 1.0
        issues = []
        
        # 这里可以实现去重逻辑，比如查询数据库中是否有相似标题或内容
        # 简单实现：检查标题是否已存在
        from utils import get_db, News
        db = next(get_db())
        try:
            existing = db.query(News).filter(News.title == news_item.title).first()
            if existing and existing.id != news_item.id:
                score = 0.0
                issues.append("内容重复")
        finally:
            db.close()
        
        return score, issues
    
    def batch_audit(self, news_list):
        """批量审核新闻"""
        results = []
        for news in news_list:
            result = self.audit(news)
            results.append((news, result))
        return results
