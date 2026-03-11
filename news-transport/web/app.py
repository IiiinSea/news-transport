from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL, SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
from utils import News, PublishRecord, CrawlTask

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 初始化管理员用户
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username=ADMIN_USERNAME).first():
        admin = User(username=ADMIN_USERNAME, is_admin=True)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()

# 路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """仪表盘"""
    # 统计数据
    total_news = News.query.count()
    pending_news = News.query.filter_by(status='pending').count()
    processed_news = News.query.filter_by(status='processed').count()
    published_news = News.query.filter_by(status='published').count()
    failed_news = News.query.filter_by(status='failed').count()
    
    # 最近的新闻
    recent_news = News.query.order_by(News.created_at.desc()).limit(10).all()
    
    # 最近的发布记录
    recent_publishes = PublishRecord.query.order_by(PublishRecord.publish_time.desc()).limit(10).all()
    
    # 最近的爬取任务
    recent_tasks = CrawlTask.query.order_by(CrawlTask.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_news=total_news,
                         pending_news=pending_news,
                         processed_news=processed_news,
                         published_news=published_news,
                         failed_news=failed_news,
                         recent_news=recent_news,
                         recent_publishes=recent_publishes,
                         recent_tasks=recent_tasks)

@app.route('/news')
@login_required
def news_list():
    """新闻列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    source = request.args.get('source', '')
    
    query = News.query
    
    if status:
        query = query.filter_by(status=status)
    if source:
        query = query.filter_by(source=source)
    
    pagination = query.order_by(News.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    news_list = pagination.items
    
    # 获取所有来源
    sources = db.session.query(News.source).distinct().all()
    sources = [s[0] for s in sources]
    
    return render_template('news_list.html',
                         news_list=news_list,
                         pagination=pagination,
                         status=status,
                         source=source,
                         sources=sources)

@app.route('/news/<int:news_id>')
@login_required
def news_detail(news_id):
    """新闻详情"""
    news = News.query.get_or_404(news_id)
    publish_records = PublishRecord.query.filter_by(news_id=news_id).all()
    return render_template('news_detail.html', news=news, publish_records=publish_records)

@app.route('/news/<int:news_id>/audit', methods=['POST'])
@login_required
def audit_news(news_id):
    """审核新闻"""
    news = News.query.get_or_404(news_id)
    action = request.form.get('action')
    comment = request.form.get('comment', '')
    
    if action == 'pass':
        news.audit_result = 'pass'
        news.status = 'processed'
    elif action == 'reject':
        news.audit_result = 'reject'
        news.status = 'failed'
    
    news.audit_comment = comment
    news.audited_time = datetime.now()
    
    db.session.commit()
    flash('审核完成')
    return redirect(url_for('news_detail', news_id=news_id))

@app.route('/news/<int:news_id>/publish', methods=['POST'])
@login_required
def publish_news(news_id):
    """手动发布新闻"""
    news = News.query.get_or_404(news_id)
    platform = request.form.get('platform')
    
    if not platform:
        flash('请选择发布平台')
        return redirect(url_for('news_detail', news_id=news_id))
    
    try:
        from publishers import get_publisher
        publisher = get_publisher(platform)
        result = publisher.publish_and_record(news)
        
        if result.get('success'):
            flash('发布成功')
        else:
            flash(f'发布失败: {result.get("error_message")}')
    except Exception as e:
        flash(f'发布异常: {str(e)}')
    
    return redirect(url_for('news_detail', news_id=news_id))

@app.route('/publishes')
@login_required
def publish_records():
    """发布记录"""
    page = request.args.get('page', 1, type=int)
    platform = request.args.get('platform', '')
    status = request.args.get('status', '')
    
    query = PublishRecord.query
    
    if platform:
        query = query.filter_by(platform=platform)
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(PublishRecord.publish_time.desc()).paginate(page=page, per_page=20, error_out=False)
    records = pagination.items
    
    # 获取所有平台
    platforms = db.session.query(PublishRecord.platform).distinct().all()
    platforms = [p[0] for p in platforms]
    
    return render_template('publish_records.html',
                         records=records,
                         pagination=pagination,
                         platform=platform,
                         status=status,
                         platforms=platforms)

@app.route('/tasks')
@login_required
def crawl_tasks():
    """爬取任务"""
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '')
    status = request.args.get('status', '')
    
    query = CrawlTask.query
    
    if source:
        query = query.filter_by(source=source)
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(CrawlTask.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    tasks = pagination.items
    
    return render_template('crawl_tasks.html',
                         tasks=tasks,
                         pagination=pagination,
                         source=source,
                         status=status)

@app.route('/settings')
@login_required
def settings():
    """系统设置"""
    return render_template('settings.html')

# API接口
@app.route('/api/run_crawl', methods=['POST'])
@login_required
def api_run_crawl():
    """手动触发爬取"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'main.py', 'crawl'], 
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        return jsonify({'success': True, 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/run_process', methods=['POST'])
@login_required
def api_run_process():
    """手动触发处理"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'main.py', 'process'], 
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        return jsonify({'success': True, 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/run_publish', methods=['POST'])
@login_required
def api_run_publish():
    """手动触发发布"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'main.py', 'publish'], 
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        return jsonify({'success': True, 'output': result.stdout + result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system_status')
@login_required
def api_system_status():
    """获取系统状态"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'main.py', 'status'], 
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        return jsonify({'success': True, 'status': result.stdout})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
