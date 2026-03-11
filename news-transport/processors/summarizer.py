import jieba
from loguru import logger
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import openai
from config import OPENAI_API_KEY, OPENAI_BASE_URL, SUMMARY_LENGTH

class NewsSummarizer:
    """新闻摘要生成器"""
    
    def __init__(self, method='textrank'):
        """
        初始化摘要生成器
        :param method: 摘要方法，支持 'textrank', 'lsa', 'openai'
        """
        self.method = method
        self.language = 'chinese'
        self.stemmer = Stemmer(self.language)
        
        if method == 'textrank':
            self.summarizer = TextRankSummarizer(self.stemmer)
        elif method == 'lsa':
            self.summarizer = LsaSummarizer(self.stemmer)
        elif method == 'openai':
            if not OPENAI_API_KEY:
                logger.warning("未配置OpenAI API Key，将使用TextRank方法")
                self.summarizer = TextRankSummarizer(self.stemmer)
                self.method = 'textrank'
            else:
                self.client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL
                )
        else:
            raise ValueError(f"不支持的摘要方法: {method}")
        
        # 加载中文停用词
        self.stop_words = get_stop_words(self.language)
    
    def summarize(self, content, title='', max_length=SUMMARY_LENGTH):
        """
        生成新闻摘要
        :param content: 新闻正文
        :param title: 新闻标题（可选，用于提升摘要质量）
        :param max_length: 摘要最大长度
        :return: 摘要文本
        """
        if not content:
            return ""
            
        # 内容过短直接返回
        if len(content) <= max_length:
            return content
            
        try:
            if self.method == 'openai':
                return self._summarize_with_openai(content, title, max_length)
            else:
                return self._summarize_with_sumy(content, max_length)
        except Exception as e:
            logger.error(f"生成摘要失败: {str(e)}")
            # 失败时返回前max_length个字符
            return content[:max_length] + "..."
    
    def _summarize_with_sumy(self, content, max_length):
        """使用sumy库生成摘要"""
        # 计算需要的句子数量（平均每句约30字）
        sentences_count = max(3, min(10, max_length // 30))
        
        parser = PlaintextParser.from_string(content, Tokenizer(self.language))
        self.summarizer.stop_words = self.stop_words
        
        summary_sentences = self.summarizer(parser.document, sentences_count)
        summary = ''.join([str(sentence) for sentence in summary_sentences])
        
        # 如果摘要过长，截断
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
            
        return summary
    
    def _summarize_with_openai(self, content, title, max_length):
        """使用OpenAI生成摘要"""
        try:
            prompt = f"""请为以下新闻生成一个不超过{max_length}字的中文摘要，要求准确概括核心内容，突出重要信息：
            标题：{title}
            正文：{content[:3000]}  # 限制输入长度
            摘要："""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻编辑，擅长生成准确简洁的新闻摘要。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_length // 2  # 中文每个字约占2个token
            )
            
            summary = response.choices[0].message.content.strip()
            return summary[:max_length]
            
        except Exception as e:
            logger.error(f"OpenAI摘要生成失败: {str(e)}")
            # 降级到TextRank
            return self._summarize_with_sumy(content, max_length)
    
    def extract_keywords(self, content, top_n=5):
        """
        提取新闻关键词
        :param content: 新闻内容
        :param top_n: 返回关键词数量
        :return: 关键词列表
        """
        if not content:
            return []
            
        try:
            # 使用jieba分词
            words = jieba.cut(content)
            # 过滤停用词和短词
            words = [word for word in words if word not in self.stop_words and len(word) > 1]
            # 统计词频
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            # 排序取前N个
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:top_n]]
            return keywords
        except Exception as e:
            logger.error(f"提取关键词失败: {str(e)}")
            return []
