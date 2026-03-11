#!/usr/bin/env python3
import os
import sys
import click
from loguru import logger
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 初始化数据库
from utils import init_db
init_db()

from spiders import get_all_spiders, get_spider
# 暂时注释，先测试爬虫功能
# from processors import NewsSummarizer, NewsTranslator, NewsAuditor
# from publishers import get_enabled_publishers, get_publisher
from utils import get_db, News, CrawlTask

# 配置日志
logger.add(
    "logs/news_transport.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
)

@click.group()
def cli():
    """新闻搬运系统 - 自动汇总国内热点新闻，智能处理后发布到海外平台"""
    # 创建必要的目录
    os.makedirs('logs', exist_ok=True)
    pass

@cli.command()
@click.option('--source', '-s', help='指定爬取的新闻来源，如：sina, netease, tencent, thepaper。默认爬取所有来源')
@click.option('--max-count', '-m', type=int, default=20, help='每个来源最大爬取数量，默认20')
def crawl(source, max_count):
    """爬取新闻"""
    logger.info("开始爬取新闻任务")
    
    if source:
        try:
            spiders = [get_spider(source)]
        except ValueError as e:
            logger.error(str(e))
            return
    else:
        spiders = get_all_spiders()
    
    total_count = 0
    for spider in spiders:
        try:
            # 创建爬取任务记录
            db = next(get_db())
            task = CrawlTask(source=spider.source_name, status='running', start_time=datetime.now())
            db.add(task)
            db.commit()
            
            # 执行爬取
            count = spider.crawl(max_count)
            total_count += count
            
            # 更新任务状态
            task.status = 'success'
            task.end_time = datetime.now()
            task.news_count = count
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"爬取 {spider.source_name} 失败: {str(e)}")
            # 更新任务状态为失败
            db.rollback()
            task.status = 'failed'
            task.end_time = datetime.now()
            task.error_message = str(e)
            db.commit()
            db.close()
            continue
    
    logger.success(f"爬取任务完成，共爬取 {total_count} 条新闻")

@cli.command()
@click.option('--news-id', '-i', type=int, help='指定处理的新闻ID，默认处理所有待处理的新闻')
def process(news_id):
    """处理新闻（摘要、翻译、审核）"""
    logger.info("处理功能暂时不可用，需要安装额外依赖")

@cli.command()
@click.option('--news-id', '-i', type=int, help='指定发布的新闻ID，默认发布所有已审核通过的新闻')
@click.option('--platform', '-p', help='指定发布平台，默认发布到所有已启用的平台')
def publish(news_id, platform):
    """发布新闻到海外平台"""
    logger.info("发布功能暂时不可用，需要安装额外依赖")

@cli.command()
def run():
    """运行完整流程：爬取 -> 处理 -> 发布"""
    logger.info("开始完整流程运行")
    
    # 爬取
    from click.testing import CliRunner
    runner = CliRunner()
    runner.invoke(crawl)
    
    # 处理
    runner.invoke(process)
    
    # 发布
    runner.invoke(publish)
    
    logger.success("完整流程运行完成")

@cli.command()
@click.option('--crawl-interval', type=int, default=3600, help='爬取间隔（秒），默认3600秒（1小时）')
@click.option('--process-interval', type=int, default=1800, help='处理间隔（秒），默认1800秒（30分钟）')
@click.option('--publish-interval', type=int, default=1800, help='发布间隔（秒），默认1800秒（30分钟）')
def schedule(crawl_interval, process_interval, publish_interval):
    """启动定时任务调度器"""
    logger.info("启动定时任务调度器")
    logger.info(f"爬取间隔: {crawl_interval}秒")
    logger.info(f"处理间隔: {process_interval}秒")
    logger.info(f"发布间隔: {publish_interval}秒")
    
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    
    # 添加爬取任务
    scheduler.add_job(
        run,
        trigger=IntervalTrigger(seconds=crawl_interval),
        id='crawl_job',
        name='定时爬取新闻',
        replace_existing=True
    )
    
    # 添加处理任务
    scheduler.add_job(
        process,
        trigger=IntervalTrigger(seconds=process_interval),
        id='process_job',
        name='定时处理新闻',
        replace_existing=True
    )
    
    # 添加发布任务
    scheduler.add_job(
        publish,
        trigger=IntervalTrigger(seconds=publish_interval),
        id='publish_job',
        name='定时发布新闻',
        replace_existing=True
    )
    
    try:
        logger.info("调度器启动成功，按Ctrl+C停止")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器已停止")
        scheduler.shutdown()

@cli.command()
def web():
    """启动Web管理后台"""
    logger.info("启动Web管理后台")
    from web.app import app
    from config import WEB_HOST, WEB_PORT
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)

@cli.command()
def status():
    """查看系统状态"""
    db = next(get_db())
    try:
        # 统计数据
        total_news = db.query(News).count()
        pending_news = db.query(News).filter(News.status == 'pending').count()
        processed_news = db.query(News).filter(News.status == 'processed').count()
        published_news = db.query(News).filter(News.status == 'published').count()
        failed_news = db.query(News).filter(News.status == 'failed').count()
        
        # 最近爬取任务
        latest_tasks = db.query(CrawlTask).order_by(CrawlTask.created_at.desc()).limit(5).all()
        
        click.echo("=" * 60)
        click.echo("📊 新闻搬运系统状态")
        click.echo("=" * 60)
        click.echo(f"总新闻数: {total_news}")
        click.echo(f"待处理: {pending_news}")
        click.echo(f"已处理: {processed_news}")
        click.echo(f"已发布: {published_news}")
        click.echo(f"失败: {failed_news}")
        click.echo("\n最近爬取任务:")
        for task in latest_tasks:
            status_icon = "✅" if task.status == 'success' else "⏳" if task.status == 'running' else "❌"
            click.echo(f"  {status_icon} {task.source} - {task.news_count}条 - {task.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        # 发布平台状态
        click.echo("\n发布平台状态:")
        click.echo("  🚀 发布功能需要配置平台API密钥后启用")
        
        click.echo("=" * 60)
        
    finally:
        db.close()

if __name__ == '__main__':
    cli()
