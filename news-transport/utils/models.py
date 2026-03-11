from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class News(Base):
    """新闻数据模型"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True, comment="新闻标题")
    content = Column(Text, comment="新闻内容")
    summary = Column(Text, comment="新闻摘要")
    translated_title = Column(String(500), comment="翻译后的标题")
    translated_content = Column(Text, comment="翻译后的内容")
    source = Column(String(100), index=True, comment="新闻来源")
    source_url = Column(String(500), unique=True, comment="原文链接")
    publish_time = Column(DateTime, comment="原发布时间")
    crawl_time = Column(DateTime, default=datetime.now, comment="爬取时间")
    category = Column(String(100), index=True, comment="新闻分类")
    tags = Column(String(500), comment="新闻标签，逗号分隔")
    image_url = Column(String(500), comment="新闻封面图")
    author = Column(String(200), comment="作者")
    
    # 处理状态
    status = Column(String(50), default="pending", comment="状态：pending/processed/audited/published/failed")
    audit_result = Column(String(50), comment="审核结果：pass/reject")
    audit_score = Column(Float, comment="审核分数")
    audit_comment = Column(Text, comment="审核意见")
    processed_time = Column(DateTime, comment="处理完成时间")
    audited_time = Column(DateTime, comment="审核完成时间")
    published_time = Column(DateTime, comment="发布完成时间")
    
    # 发布状态
    published_platforms = Column(String(500), comment="已发布的平台，逗号分隔")
    publish_error = Column(Text, comment="发布错误信息")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<News {self.title[:50]}...>"

class PublishRecord(Base):
    """发布记录模型"""
    __tablename__ = "publish_records"
    
    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, index=True, comment="关联新闻ID")
    platform = Column(String(100), index=True, comment="发布平台")
    post_id = Column(String(200), comment="平台返回的帖子ID")
    post_url = Column(String(500), comment="帖子链接")
    status = Column(String(50), comment="发布状态：success/failed")
    error_message = Column(Text, comment="错误信息")
    publish_time = Column(DateTime, default=datetime.now, comment="发布时间")
    
    # 统计数据
    views = Column(Integer, default=0, comment="浏览量")
    likes = Column(Integer, default=0, comment="点赞数")
    shares = Column(Integer, default=0, comment="分享数")
    comments = Column(Integer, default=0, comment="评论数")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<PublishRecord {self.platform} {self.news_id}>"

class CrawlTask(Base):
    """爬虫任务模型"""
    __tablename__ = "crawl_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), index=True, comment="爬虫来源")
    status = Column(String(50), default="pending", comment="任务状态：pending/running/success/failed")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    news_count = Column(Integer, default=0, comment="爬取到的新闻数量")
    error_message = Column(Text, comment="错误信息")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<CrawlTask {self.source} {self.status}>"

# 创建数据库表
def init_db():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
