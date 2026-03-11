#!/usr/bin/env python3
"""
新闻搜索脚本 - News Transport Skill
"""
import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.baidu.com/',
}

def search_news(keyword, count=10):
    """搜索新闻并返回结果"""
    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(keyword)}&tn=news"
    
    print(f"🔍 正在搜索: {keyword}")
    print("=" * 80)

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        
        news_items = soup.select('.result-op.c-container')
        if not news_items:
            news_items = soup.select('.c-result')
        
        results = []
        for item in news_items[:count]:
            try:
                title = item.select_one('h3').get_text(strip=True) if item.select_one('h3') else ''
                summary = item.select_one('.c-abstract').get_text(strip=True) if item.select_one('.c-abstract') else ''
                time_info = item.select_one('.c-author, .c-time').get_text(strip=True) if item.select_one('.c-author, .c-time') else ''
                link = item.select_one('a')['href'] if item.select_one('a') else ''
                source = item.select_one('.c-source').get_text(strip=True) if item.select_one('.c-source') else '未知来源'
                
                if title:
                    results.append({
                        'title': title,
                        'summary': summary,
                        'time': time_info,
                        'source': source,
                        'link': link
                    })
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")
        return []

def main():
    if len(sys.argv) < 2:
        print("用法: python search_news.py <关键词> [数量]")
        print("示例: python search_news.py '美伊局势 最新消息' 10")
        sys.exit(1)
    
    keyword = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    results = search_news(keyword, count)
    
    if not results:
        print("\n❌ 暂时没有找到相关的最新新闻。")
        return
    
    for i, news in enumerate(results, 1):
        print(f"\n{i}. {news['title']}")
        if news['time']:
            print(f"   🕒 时间: {news['time']}")
        if news['source']:
            print(f"   📰 来源: {news['source']}")
        if news['summary']:
            print(f"   📝 摘要: {news['summary'][:200]}..." if len(news['summary']) > 200 else f"   📝 摘要: {news['summary']}")
        if news['link']:
            print(f"   🔗 链接: {news['link']}")
        print("-" * 80)
    
    print(f"\n✅ 共找到 {len(results)} 条相关新闻。")

if __name__ == "__main__":
    main()
