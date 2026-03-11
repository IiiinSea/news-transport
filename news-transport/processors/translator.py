from loguru import logger
from googletrans import Translator as GoogleTranslator
import openai
from config import OPENAI_API_KEY, OPENAI_BASE_URL, TRANSLATION_ENGINE

class NewsTranslator:
    """新闻翻译器"""
    
    def __init__(self, engine=None):
        """
        初始化翻译器
        :param engine: 翻译引擎，支持 'google', 'openai'，默认使用配置文件中的TRANSLATION_ENGINE
        """
        self.engine = engine or TRANSLATION_ENGINE
        
        if self.engine == 'google':
            self.translator = GoogleTranslator()
        elif self.engine == 'openai':
            if not OPENAI_API_KEY:
                logger.warning("未配置OpenAI API Key，将使用Google翻译")
                self.translator = GoogleTranslator()
                self.engine = 'google'
            else:
                self.client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL
                )
        else:
            raise ValueError(f"不支持的翻译引擎: {self.engine}")
    
    def translate(self, text, target_lang='en', source_lang='zh-CN'):
        """
        翻译文本
        :param text: 要翻译的文本
        :param target_lang: 目标语言，默认英文
        :param source_lang: 源语言，默认中文
        :return: 翻译后的文本
        """
        if not text:
            return ""
            
        try:
            if self.engine == 'google':
                return self._translate_with_google(text, target_lang, source_lang)
            elif self.engine == 'openai':
                return self._translate_with_openai(text, target_lang, source_lang)
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            # 失败时返回原文
            return text
    
    def _translate_with_google(self, text, target_lang, source_lang):
        """使用Google翻译"""
        try:
            # 处理长文本，分段翻译
            max_length = 5000
            if len(text) <= max_length:
                result = self.translator.translate(text, dest=target_lang, src=source_lang)
                return result.text
            else:
                # 分段翻译
                segments = []
                for i in range(0, len(text), max_length):
                    segment = text[i:i+max_length]
                    result = self.translator.translate(segment, dest=target_lang, src=source_lang)
                    segments.append(result.text)
                return ' '.join(segments)
        except Exception as e:
            logger.error(f"Google翻译失败: {str(e)}")
            # 降级到OpenAI
            if self.engine != 'openai' and OPENAI_API_KEY:
                logger.info("尝试使用OpenAI翻译")
                return self._translate_with_openai(text, target_lang, source_lang)
            raise
    
    def _translate_with_openai(self, text, target_lang, source_lang):
        """使用OpenAI翻译"""
        try:
            lang_names = {
                'en': '英文',
                'zh-CN': '中文',
                'ja': '日文',
                'ko': '韩文',
                'fr': '法文',
                'de': '德文',
                'es': '西班牙文',
                'ru': '俄文',
                'ar': '阿拉伯文'
            }
            
            target_lang_name = lang_names.get(target_lang, target_lang)
            source_lang_name = lang_names.get(source_lang, source_lang)
            
            prompt = f"""请将以下{source_lang_name}文本准确翻译为{target_lang_name}，保留原文的语气和专业术语，适合新闻发布使用：
            原文：
            {text}
            翻译："""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"你是一个专业的翻译官，擅长{source_lang_name}到{target_lang_name}的新闻翻译，翻译准确自然，符合目标语言的表达习惯。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            translation = response.choices[0].message.content.strip()
            return translation
            
        except Exception as e:
            logger.error(f"OpenAI翻译失败: {str(e)}")
            # 降级到Google翻译
            if self.engine != 'google':
                logger.info("尝试使用Google翻译")
                return self._translate_with_google(text, target_lang, source_lang)
            raise
    
    def translate_news(self, news_item):
        """
        翻译整条新闻
        :param news_item: 新闻对象，包含title和content字段
        :return: 翻译后的新闻对象，新增translated_title和translated_content字段
        """
        try:
            logger.info(f"开始翻译新闻: {news_item.title[:50]}...")
            
            # 翻译标题
            translated_title = self.translate(news_item.title, target_lang='en', source_lang='zh-CN')
            
            # 翻译内容
            translated_content = self.translate(news_item.content, target_lang='en', source_lang='zh-CN')
            
            logger.success(f"新闻翻译完成: {translated_title[:50]}...")
            
            return {
                'translated_title': translated_title,
                'translated_content': translated_content
            }
            
        except Exception as e:
            logger.error(f"翻译新闻失败: {str(e)}")
            return {
                'translated_title': news_item.title,
                'translated_content': news_item.content
            }
