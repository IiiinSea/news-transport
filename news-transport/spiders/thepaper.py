from datetime import datetime
from loguru import logger
from .base import BaseSpider

class ThePaperSpider(BaseSpider):
    """澎湃新闻爬虫"""
    
    def __init__(self):
        super().__init__('thepaper', 'https://www.thepaper.cn/')
    
    def crawl(self, max_count=20):
        """爬取澎湃新闻"""
        logger.info(f"开始爬取澎湃新闻，最大数量: {max_count}")
        news_count = 0
        
        try:
            response = self.get(self.base_url)
            soup = self.parse_html(response.text)
            
            # 提取热点新闻列表
            news_items = soup.select('.news_li a, .hot_list li a, .list_title a, .news_tit a')
            
            for item in news_items[:max_count]:
                try:
                    title = self.clean_text(item.get_text())
                    url = item.get('href', '')
                    
                    if not url or not title:
                        continue
                    
                    # 处理相对路径
                    if not url.startswith('http'):
                        url = 'https://www.thepaper.cn/' + url.lstrip('/')
                    
                    # 只爬取新闻详情页
                    if 'thepaper.cn/newsDetail' not in url:
                        continue
                    
                    news_detail = self.crawl_detail(url, title)
                    if news_detail:
                        self.save_news(news_detail)
                        news_count += 1
                        
                except Exception as e:
                    logger.error(f"处理新闻条目失败: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"爬取澎湃新闻失败: {str(e)}")
            raise
            
        logger.success(f"澎湃新闻爬取完成，共爬取 {news_count} 条新闻")
        return news_count
    
    def crawl_detail(self, url, title):
        """爬取新闻详情页"""
        try:
            response = self.get(url)
            soup = self.parse_html(response.text)
            
            # 提取内容
            content_selector = '.news_txt, .article-content, #ctext, .content'
            content_elements = soup.select(content_selector)
            
            if not content_elements:
                logger.warning(f"未找到内容元素: {url}")
                return None
                
            content = '\n'.join([p.get_text().strip() for p in content_elements[0].select('p') if p.get_text().strip()])
            content = self.clean_text(content)
            
            if len(content) < 100:
                logger.warning(f"内容过短: {title}")
                return None
            
            # 提取发布时间
            time_selector = '.pubtime, .time, .article-time, .news_time'
            time_element = soup.select_one(time_selector)
            publish_time = datetime.now()
            if time_element:
                time_str = time_element.get_text().strip()
                publish_time = self.extract_publish_time(time_str)
            
            # 提取作者
            author_selector = '.source, .author, .origin, .news_origin'
            author_element = soup.select_one(author_selector)
            author = author_element.get_text().strip() if author_element else '澎湃新闻'
            
            # 提取封面图
            img_selector = '.news_txt img, .article-content img, #ctext img'
            img_element = soup.select_one(img_selector)
            image_url = img_element.get('src', '') if img_element else ''
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            
            # 提取分类
            category = '热点'
            
            return {
                'title': title,
                'content': content,
                'source': 'thepaper',
                'source_url': url,
                'publish_time': publish_time,
                'category': category,
                'image_url': image_url,
                'author': author,
                'tags': ''
            }
            
        except Exception as e:
            logger.error(f"爬取详情页失败 {url}: {str(e)}")
            return None
