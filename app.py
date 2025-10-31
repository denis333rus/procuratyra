from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session, flash, jsonify
import sqlite3
from pathlib import Path
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates')

# Configuration from environment variables
app.secret_key = os.getenv('SECRET_KEY', 'change-me-in-production')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
PROSECUTOR_USERNAME = os.getenv('PROSECUTOR_USERNAME', 'proc')
PROSECUTOR_PASSWORD = os.getenv('PROSECUTOR_PASSWORD', 'proc123')

# Production security settings
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'"
        return response

# Database configuration for Railway
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Use PostgreSQL for production (Railway)
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_TYPE = 'postgresql'
else:
    # Use SQLite for development
    DB_PATH = Path(__file__).with_name('data.db')
    DB_TYPE = 'sqlite'

# Upload folder configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Set max content length for uploads
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default


def get_db():
    if DB_TYPE == 'postgresql':
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Define table schemas for both databases
    tables = {
        'slider_news': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS slider_news (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    image TEXT
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS slider_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    image TEXT
                )
            """
        },
        'feed_news': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS feed_news (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS feed_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL
                )
            """
        },
        'job_applications': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS job_applications (
                    id SERIAL PRIMARY KEY,
                    nick_ds TEXT, nick_roblox TEXT,
                    char_name TEXT, real_age INTEGER, char_birth TEXT, date_now TEXT,
                    char_age INTEGER, char_nationality TEXT, char_job TEXT,
                    char_education TEXT, about TEXT, what_is_prosecutor TEXT,
                    literacy_test TEXT, has_convictions TEXT, has_experience TEXT,
                    term_upk TEXT, term_uk TEXT, term_koap TEXT, term_tk TEXT,
                    desired_login TEXT, desired_password TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS job_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nick_ds TEXT, nick_roblox TEXT,
                    char_name TEXT, real_age INTEGER, char_birth TEXT, date_now TEXT,
                    char_age INTEGER, char_nationality TEXT, char_job TEXT,
                    char_education TEXT, about TEXT, what_is_prosecutor TEXT,
                    literacy_test TEXT, has_convictions TEXT, has_experience TEXT,
                    term_upk TEXT, term_uk TEXT, term_koap TEXT, term_tk TEXT,
                    desired_login TEXT, desired_password TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
        },
        'employees': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    contact TEXT
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    contact TEXT
                )
            """
        },
        'documents': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    date TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL
                )
            """
        },
        'leaders': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS leaders (
                    id SERIAL PRIMARY KEY,
                    date TEXT,
                    name TEXT,
                    message TEXT NOT NULL,
                    photo TEXT
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS leaders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    name TEXT,
                    message TEXT NOT NULL,
                    photo TEXT
                )
            """
        },
        'notifications': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT NOT NULL,
                    recipient_role TEXT NOT NULL,
                    recipient_id INTEGER,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT NOT NULL,
                    recipient_role TEXT NOT NULL,
                    recipient_id INTEGER,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT
                )
            """
        },
        'contacts': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    label TEXT NOT NULL,
                    value TEXT NOT NULL
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    value TEXT NOT NULL
                )
            """
        },
        'complaints': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS complaints (
                    id SERIAL PRIMARY KEY,
                    fio TEXT NOT NULL,
                    nick_ds TEXT NOT NULL,
                    violator_ds TEXT,
                    violator_roblox TEXT NOT NULL,
                    details TEXT NOT NULL,
                    image TEXT,
                    claimed_by TEXT,
                    claimed_at TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fio TEXT NOT NULL,
                    nick_ds TEXT NOT NULL,
                    violator_ds TEXT,
                    violator_roblox TEXT NOT NULL,
                    details TEXT NOT NULL,
                    image TEXT,
                    claimed_by TEXT,
                    claimed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
        },
        'documents_drafts': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS documents_drafts (
                    id SERIAL PRIMARY KEY,
                    created_by TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS documents_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_by TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            """
        },
        'user_accounts': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT DEFAULT 'employee',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_from_application INTEGER
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT DEFAULT 'employee',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_from_application INTEGER,
                    FOREIGN KEY (created_from_application) REFERENCES job_applications(id)
                )
            """
        },
        'organs_units': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS organs_units (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    url TEXT
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS organs_units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    url TEXT
                )
            """
        },
        'app_settings': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """
        },
        'hotline_appeals': {
            'postgresql': """
                CREATE TABLE IF NOT EXISTS hotline_appeals (
                    id SERIAL PRIMARY KEY,
                    fio TEXT NOT NULL,
                    organization TEXT,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'sqlite': """
                CREATE TABLE IF NOT EXISTS hotline_appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fio TEXT NOT NULL,
                    organization TEXT,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
    }
    
    # Create all tables
    for table_name, schemas in tables.items():
        cur.execute(schemas[DB_TYPE])
    
    # Handle migrations for SQLite only
    if DB_TYPE == 'sqlite':
        # Add photo column if it doesn't exist
        try:
            cur.execute("ALTER TABLE leaders ADD COLUMN photo TEXT")
        except:
            pass
        
        # Add description column to documents if it doesn't exist
        try:
            cur.execute("ALTER TABLE documents ADD COLUMN description TEXT")
        except:
            pass
        
        # Add claimed_by and claimed_at columns to complaints if they don't exist
        try:
            cur.execute("ALTER TABLE complaints ADD COLUMN claimed_by TEXT")
        except:
            pass
        try:
            cur.execute("ALTER TABLE complaints ADD COLUMN claimed_at TEXT")
        except:
            pass
        
        # Add columns to job_applications if they don't exist
        try:
            cur.execute('ALTER TABLE job_applications ADD COLUMN desired_login TEXT')
        except:
            pass
        try:
            cur.execute('ALTER TABLE job_applications ADD COLUMN desired_password TEXT')
        except:
            pass
        try:
            cur.execute('ALTER TABLE job_applications ADD COLUMN status TEXT DEFAULT "pending"')
        except:
            pass

    conn.commit()
    conn.close()


init_db()


# База данных создается без демо-данных


def group_news_by_date(items):
    grouped = {}
    for it in items:
        grouped.setdefault(it['date'], []).append(it)
    # сортировка дат по убыванию
    ordered = []
    for d in sorted(grouped.keys(), reverse=True):
        # сортировка времени по убыванию
        ordered.append((d, sorted(grouped[d], key=lambda x: x['time'], reverse=True)))
    return ordered


@app.route('/')
def index():
    page = request.args.get('page', default=1, type=int)
    q = request.args.get('q', default='', type=str).strip()
    tab = request.args.get('tab', default='feed', type=str)
    # slider news from DB
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM slider_news')
    total = cur.fetchone()[0]
    current_news = None
    if total > 0:
        if page < 1:
            page = 1
        if page > total:
            page = total
        offset = page - 1
        cur.execute('SELECT date, title, description, image FROM slider_news ORDER BY id DESC LIMIT 1 OFFSET ?', (offset,))
        row = cur.fetchone()
        if row:
            current_news = { 'date': row['date'], 'title': row['title'], 'description': row['description'], 'image': row['image'] }
    # Если активен поиск, не пагинируем ленту, а фильтруем по запросу
    search_results = []
    feed_grouped = []
    if q:
        like = f"%{q}%"
        cur.execute('''
            SELECT date, time, title, description, url
            FROM feed_news
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY id DESC
            LIMIT 100
        ''', (like, like))
        search_results = [dict(r) for r in cur.fetchall()]
        # сгруппуем найденное по дате для единообразного отображения
        feed_grouped = group_news_by_date(search_results)
        feed_page = 1
        feed_pages = 1
    else:
        # Пагинация ленты (по датам не режем; просто первые N записей)
        per_page = 7
        cur.execute('SELECT COUNT(*) FROM feed_news')
        feed_total = cur.fetchone()[0]
        feed_page = request.args.get('feed_page', default=1, type=int)
        if feed_page < 1:
            feed_page = 1
        feed_pages = max(1, (feed_total + per_page - 1) // per_page)
        if feed_page > feed_pages:
            feed_page = feed_pages
        start = (feed_page - 1) * per_page
        cur.execute('SELECT date, time, title, description, url FROM feed_news ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, start))
        rows = [dict(r) for r in cur.fetchall()]
        feed_grouped = group_news_by_date(rows)
    conn.close()

    return render_template(
        'base.html',
        page=page,
        total_pages=total,
        news=current_news,
        feed_groups=feed_grouped,
        feed_page=feed_page,
        feed_pages=feed_pages,
        q=q,
        tab=('search' if q or tab == 'search' else 'feed'),
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Check admin credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_home'))
        
        # Check prosecutor credentials
        if username == PROSECUTOR_USERNAME and password == PROSECUTOR_PASSWORD:
            session['is_prosecutor'] = True
            session['proc_name'] = 'Прокурор'
            return redirect(url_for('prosecutor_panel'))
        
        # Check user accounts
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, username, password, full_name, role FROM user_accounts WHERE username=? AND password=?', (username, password))
        user = cur.fetchone()
        conn.close()
        
        if user:
            user_id, username, password, full_name, role = user
            session['user_id'] = user_id
            session['username'] = username
            session['full_name'] = full_name
            session['user_role'] = role
            
            if role == 'prosecutor':
                session['is_prosecutor'] = True
                session['proc_name'] = full_name
                return redirect(url_for('prosecutor_panel'))
            else:
                return render_template('submitted.html', title='Вход', message=f'Здравствуйте, {full_name}!')
        
        # обычное сообщение, если не найдено
        if username:
            return render_template('submitted.html', title='Вход', message=f'Здравствуйте, {username}!')
        return render_template('login.html', error='Укажите логин и пароль')
    return render_template('login.html')


@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'POST':
        # Сохранение заявки в БД
        desired_login = request.form.get('login', '').strip()
        desired_password = request.form.get('password', '').strip()
        
        conn = get_db()
        conn.execute(
            'INSERT INTO job_applications(nick_ds, nick_roblox, char_name, real_age, char_birth, date_now, char_age, char_nationality, char_job, char_education, about, what_is_prosecutor, literacy_test, has_convictions, has_experience, term_upk, term_uk, term_koap, term_tk, desired_login, desired_password) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (
                request.form.get('nick_ds'),
                request.form.get('nick_roblox'),
                request.form.get('char_name'),
                request.form.get('real_age'),
                request.form.get('char_birth'),
                request.form.get('date_now'),
                request.form.get('char_age'),
                request.form.get('char_nationality'),
                request.form.get('char_job'),
                request.form.get('char_education'),
                request.form.get('about'),
                request.form.get('what_is_prosecutor'),
                request.form.get('literacy_test'),
                request.form.get('has_convictions'),
                request.form.get('has_experience'),
                request.form.get('term_upk'),
                request.form.get('term_uk'),
                request.form.get('term_koap'),
                request.form.get('term_tk'),
                desired_login,
                desired_password,
            ),
        )
        conn.commit()
        conn.close()
        
        # Создать уведомление для админов о новой заявке
        create_notification(
            title="Новая заявка на работу",
            message=f"Поступила заявка от {request.form.get('char_name', 'Неизвестно')}",
            notification_type="job_application",
            recipient_role="admin"
        )
        
        return render_template('submitted.html', title='Заявка отправлена', message='Спасибо! Ваша заявка принята.')
    return render_template('jobs.html')


# ------------------ Admin ------------------
def is_admin() -> bool:
    is_admin_status = bool(session.get('is_admin'))
    print(f"DEBUG: is_admin() = {is_admin_status}, session = {dict(session)}")
    return is_admin_status


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Используем общий экран входа
    if request.method == 'POST':
        return redirect(url_for('login'))
    return redirect(url_for('login'))


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))


def is_prosecutor() -> bool:
    return bool(session.get('is_prosecutor'))


@app.route('/admin', methods=['GET'])
def admin_home():
    if not is_admin():
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin_important'))


def create_notification(title, message, notification_type, recipient_role, recipient_id=None, data=None):
    """Создать новое уведомление"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO notifications (title, message, type, recipient_role, recipient_id, data) 
                   VALUES (?, ?, ?, ?, ?, ?)''', 
                (title, message, notification_type, recipient_role, recipient_id, data))
    conn.commit()
    conn.close()

def get_notifications(recipient_role, recipient_id=None, limit=50):
    """Получить уведомления для пользователя"""
    conn = get_db()
    cur = conn.cursor()
    
    if recipient_id:
        cur.execute('''SELECT id, title, message, type, is_read, created_at, data 
                       FROM notifications 
                       WHERE recipient_role = ? AND (recipient_id = ? OR recipient_id IS NULL)
                       ORDER BY created_at DESC LIMIT ?''', 
                    (recipient_role, recipient_id, limit))
    else:
        cur.execute('''SELECT id, title, message, type, is_read, created_at, data 
                       FROM notifications 
                       WHERE recipient_role = ? AND recipient_id IS NULL
                       ORDER BY created_at DESC LIMIT ?''', 
                    (recipient_role, limit))
    
    notifications = [dict(r) for r in cur.fetchall()]
    conn.close()
    return notifications

def mark_notification_read(notification_id):
    """Отметить уведомление как прочитанное"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE notifications SET is_read = TRUE WHERE id = ?', (notification_id,))
    conn.commit()
    conn.close()

def get_unread_count(recipient_role, recipient_id=None):
    """Получить количество непрочитанных уведомлений"""
    conn = get_db()
    cur = conn.cursor()
    
    if recipient_id:
        cur.execute('''SELECT COUNT(*) FROM notifications 
                       WHERE recipient_role = ? AND (recipient_id = ? OR recipient_id IS NULL) 
                       AND is_read = FALSE''', 
                    (recipient_role, recipient_id))
    else:
        cur.execute('''SELECT COUNT(*) FROM notifications 
                       WHERE recipient_role = ? AND recipient_id IS NULL 
                       AND is_read = FALSE''', 
                    (recipient_role,))
    
    count = cur.fetchone()[0]
    conn.close()
    return count

def admin_fetch_lists():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT date, title, description, image FROM slider_news ORDER BY id DESC LIMIT 50')
    slider = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, time, title, description, url FROM feed_news ORDER BY id DESC LIMIT 50')
    feed = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, name, position, contact FROM employees ORDER BY id DESC LIMIT 200')
    employees = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, title, description, url FROM documents ORDER BY id DESC LIMIT 200')
    documents = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, date, name, message, photo FROM leaders ORDER BY id DESC LIMIT 50')
    leaders = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, created_at, char_name, char_age, char_nationality, char_job, nick_ds, desired_login, status FROM job_applications ORDER BY id DESC LIMIT 200')
    job_apps = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, created_at, fio, nick_ds, violator_ds, violator_roblox, details, image, claimed_by, claimed_at FROM complaints ORDER BY id DESC LIMIT 200')
    complaints = [dict(r) for r in cur.fetchall()]
    conn.close()
    return slider, feed, employees, documents, leaders, job_apps, complaints

def admin_fetch_with_notifications():
    """Получить данные для админки с уведомлениями"""
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    notifications = get_notifications('admin')
    unread_count = get_unread_count('admin')
    return slider, feed, employees, documents, leaders, job_apps, complaints, notifications, unread_count


@app.route('/admin/organs')
def admin_organs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, url FROM organs_units ORDER BY id DESC')
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('admin/organs.html', items=items)


@app.route('/admin/organs/add', methods=['POST'])
def admin_add_organ():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('INSERT INTO organs_units(name, description, url) VALUES(?,?,?)', (
        request.form.get('name','').strip(),
        request.form.get('description','').strip(),
        (request.form.get('url','').strip() or None),
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_organs'))


@app.route('/admin/organs/delete/<int:item_id>', methods=['POST'])
def admin_delete_organ(item_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('DELETE FROM organs_units WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_organs'))


@app.route('/admin/important')
def admin_important():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    unread_count = get_unread_count('admin')
    return render_template('admin/important.html', slider_news=slider, unread_count=unread_count)


@app.route('/admin/ordinary')
def admin_ordinary():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    unread_count = get_unread_count('admin')
    return render_template('admin/ordinary.html', feed=feed, unread_count=unread_count)


@app.route('/admin/employees')
def admin_employees():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    unread_count = get_unread_count('admin')
    return render_template('admin/employees.html', employees=employees, unread_count=unread_count)


@app.route('/admin/jobs')
def admin_jobs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    unread_count = get_unread_count('admin')
    return render_template('admin/jobs.html', job_apps=job_apps, unread_count=unread_count)


@app.route('/admin/docs')
def admin_docs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    unread_count = get_unread_count('admin')
    return render_template('admin/documents.html', documents=documents, unread_count=unread_count)


@app.route('/admin/leader')
def admin_leader():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints, notifications, unread_count = admin_fetch_with_notifications()
    return render_template('admin/leader.html', leaders=leaders, notifications=notifications, unread_count=unread_count)


@app.route('/admin/complaints')
def admin_complaints():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, created_at, fio, nick_ds, violator_ds, violator_roblox, details, image, claimed_by, claimed_at FROM complaints ORDER BY id DESC LIMIT 300')
    complaints = [dict(r) for r in cur.fetchall()]
    conn.close()
    unread_count = get_unread_count('admin')
    return render_template('admin/complaints.html', complaints=complaints, unread_count=unread_count)


@app.route('/admin/hotline')
def admin_hotline():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, created_at, fio, organization, subject, message FROM hotline_appeals ORDER BY id DESC LIMIT 300')
    appeals = [dict(r) for r in cur.fetchall()]
    conn.close()
    unread_count = get_unread_count('admin')
    return render_template('admin/hotline_appeals.html', appeals=appeals, unread_count=unread_count)


@app.route('/admin/news/add', methods=['POST'])
def admin_add_slider_news():
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    # Обработка загрузки файла
    image_path = '/logo/logo.png'  # По умолчанию
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Добавляем timestamp для уникальности
            import time
            timestamp = str(int(time.time()))
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            filepath = UPLOAD_FOLDER / filename
            file.save(filepath)
            image_path = f'/uploads/{filename}'
    
    conn = get_db()
    conn.execute(
        'INSERT INTO slider_news(date, title, description, image) VALUES(?,?,?,?)',
        (
            request.form.get('date', '').strip(),
            request.form.get('title', '').strip(),
            request.form.get('description', '').strip(),
            image_path,
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_important'))


@app.route('/admin/feed/add', methods=['POST'])
def admin_add_feed_news():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute(
        'INSERT INTO feed_news(date, time, title, description, url) VALUES(?,?,?,?,?)',
        (
            request.form.get('date', '').strip(),
            request.form.get('time', '').strip(),
            request.form.get('title', '').strip(),
            request.form.get('description', '').strip(),
            (request.form.get('url', '#').strip() or '#'),
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_ordinary'))


@app.route('/admin/employees/add', methods=['POST'])
def admin_add_employee():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('INSERT INTO employees(name, position, contact) VALUES(?,?,?)', (
        request.form.get('name','').strip(), request.form.get('position','').strip(), request.form.get('contact','').strip()
    ))
    conn.commit()
    conn.close()
    flash('Сотрудник добавлен', 'success')
    return redirect(url_for('admin_employees'))


@app.route('/admin/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
def admin_edit_employee(emp_id: int):
    if not is_admin():
        flash('Необходимо войти как администратор', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        position = request.form.get('position', '').strip()
        contact = request.form.get('contact', '').strip()
        
        cur.execute('UPDATE employees SET name=?, position=?, contact=? WHERE id=?', 
                   (name, position, contact, emp_id))
        conn.commit()
        conn.close()
        flash('Сотрудник обновлен', 'success')
        return redirect(url_for('admin_employees'))
    
    # GET request - show edit form
    cur.execute('SELECT name, position, contact FROM employees WHERE id=?', (emp_id,))
    employee = cur.fetchone()
    conn.close()
    
    if not employee:
        flash('Сотрудник не найден', 'error')
        return redirect(url_for('admin_employees'))
    
    return render_template('admin/edit_employee.html', employee={'id': emp_id, 'name': employee[0], 'position': employee[1], 'contact': employee[2]})


@app.route('/admin/employees/delete/<int:emp_id>', methods=['POST'])
def admin_delete_employee(emp_id: int):
    if not is_admin():
        flash('Необходимо войти как администратор', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get employee info before deletion
    cur.execute('SELECT name FROM employees WHERE id=?', (emp_id,))
    employee = cur.fetchone()
    
    if employee:
        # Delete employee
        cur.execute('DELETE FROM employees WHERE id=?', (emp_id,))
        conn.commit()
        flash(f'Сотрудник {employee[0]} удален', 'success')
    else:
        flash('Сотрудник не найден', 'error')
    
    conn.close()
    return redirect(url_for('admin_employees'))


@app.route('/admin/docs/add', methods=['POST'])
def admin_add_document():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('INSERT INTO documents(date, title, url) VALUES(?,?,?)', (
        request.form.get('date'), request.form.get('title','').strip(), request.form.get('url','').strip()
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_docs'))


@app.route('/admin/leader/add', methods=['POST'])
def admin_add_leader():
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Handle photo upload
    photo_filename = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo and photo.filename:
            # Generate secure filename
            import os
            import uuid
            from werkzeug.utils import secure_filename
            
            filename = secure_filename(photo.filename)
            if filename:
                # Create unique filename
                file_ext = os.path.splitext(filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                
                # Save file
                photo_path = os.path.join('static', 'uploads', 'leaders')
                os.makedirs(photo_path, exist_ok=True)
                photo.save(os.path.join(photo_path, unique_filename))
                photo_filename = f"uploads/leaders/{unique_filename}"
    
    cur.execute('INSERT INTO leaders(date, name, message, photo) VALUES(?,?,?,?)', (
        request.form.get('date'), 
        request.form.get('name','').strip(), 
        request.form.get('message','').strip(),
        photo_filename
    ))
    conn.commit()
    conn.close()
    flash('Лидер добавлен', 'success')
    return redirect(url_for('admin_leader'))


@app.route('/admin/leader/edit/<int:leader_id>', methods=['GET', 'POST'])
def admin_edit_leader(leader_id: int):
    if not is_admin():
        flash('Необходимо войти как администратор', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        date = request.form.get('date', '').strip()
        name = request.form.get('name', '').strip()
        message = request.form.get('message', '').strip()
        
        # Handle photo upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename:
                # Generate secure filename
                import os
                import uuid
                from werkzeug.utils import secure_filename
                
                filename = secure_filename(photo.filename)
                if filename:
                    # Create unique filename
                    file_ext = os.path.splitext(filename)[1]
                    unique_filename = f"{uuid.uuid4()}{file_ext}"
                    
                    # Save file
                    photo_path = os.path.join('static', 'uploads', 'leaders')
                    os.makedirs(photo_path, exist_ok=True)
                    photo.save(os.path.join(photo_path, unique_filename))
                    photo_filename = f"uploads/leaders/{unique_filename}"
        
        # Update leader with or without new photo
        if photo_filename:
            cur.execute('UPDATE leaders SET date=?, name=?, message=?, photo=? WHERE id=?', 
                       (date, name, message, photo_filename, leader_id))
        else:
            cur.execute('UPDATE leaders SET date=?, name=?, message=? WHERE id=?', 
                       (date, name, message, leader_id))
        
        conn.commit()
        conn.close()
        flash('Лидер обновлен', 'success')
        return redirect(url_for('admin_leader'))
    
    # GET request - show edit form
    cur.execute('SELECT date, name, message, photo FROM leaders WHERE id=?', (leader_id,))
    leader = cur.fetchone()
    conn.close()
    
    if not leader:
        flash('Лидер не найден', 'error')
        return redirect(url_for('admin_leader'))
    
    return render_template('admin/edit_leader.html', leader={'id': leader_id, 'date': leader[0], 'name': leader[1], 'message': leader[2], 'photo': leader[3]})


@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_notification_read_route(notification_id):
    """Отметить уведомление как прочитанное"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    mark_notification_read(notification_id)
    return jsonify({'success': True})

@app.route('/notifications/get_unread_count')
def get_unread_count_route():
    """Получить количество непрочитанных уведомлений"""
    if not session.get('user_id'):
        return jsonify({'count': 0})
    
    user_role = session.get('user_role')
    user_id = session.get('user_id')
    count = get_unread_count(user_role, user_id)
    return jsonify({'count': count})

@app.route('/notifications/get_all')
def get_all_notifications_route():
    """Получить все уведомления пользователя"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    user_role = session.get('user_role')
    user_id = session.get('user_id')
    notifications = get_notifications(user_role, user_id)
    return jsonify({'notifications': notifications})


@app.route('/about')
def about():
    return render_template('about-the-proc.html')


@app.route('/activity')
def activity():
    return render_template('activity.html')



@app.route('/internet-reception', methods=['GET', 'POST'])
def internet_reception():
    if request.method == 'POST':
        # Сохранение жалобы в БД + опциональная картинка
        fio = request.form.get('fio','').strip()
        nick_ds = request.form.get('nick_ds','').strip()
        violator_ds = request.form.get('violator_ds','').strip()
        violator_roblox = request.form.get('violator_roblox','').strip()
        details = request.form.get('what_happened','').strip()

        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                filename = f"complaint_{name}_{timestamp}{ext}"
                filepath = UPLOAD_FOLDER / filename
                file.save(filepath)
                image_path = f'/uploads/{filename}'

        conn = get_db()
        conn.execute(
            'INSERT INTO complaints(fio, nick_ds, violator_ds, violator_roblox, details, image) VALUES(?,?,?,?,?,?)',
            (fio, nick_ds, violator_ds, violator_roblox, details, image_path)
        )
        conn.commit()
        conn.close()
        
        # Создать уведомления для админов и прокуроров
        create_notification(
            title="Новая жалоба получена",
            message=f"Поступила жалоба от {fio}",
            notification_type="complaint",
            recipient_role="admin"
        )
        create_notification(
            title="Новая жалоба получена", 
            message=f"Поступила жалоба от {fio}",
            notification_type="complaint",
            recipient_role="prosecutor"
        )
        return render_template('submitted.html', title='Жалоба отправлена', message='Спасибо! Обращение получено.')
    return render_template('internet-reception.html')


@app.route('/documents')
def documents():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT date, title, description, url FROM documents ORDER BY id DESC')
    docs = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('documents.html', documents=docs)


# Страница "Органы и организации прокуратуры"
@app.route('/organs')
def organs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, url FROM organs_units ORDER BY id DESC')
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('organs.html', items=items)


# Статика для логотипа и других файлов из папки logo
@app.route('/logo/<path:filename>')
def logo_files(filename: str):
    return send_from_directory('logo', filename)


# Статика для загруженных файлов
@app.route('/uploads/<path:filename>')
def uploaded_files(filename: str):
    return send_from_directory('uploads', filename)


# Статика для PDF файлов
@app.route('/pdf/<path:filename>')
def pdf_files(filename: str):
    return send_from_directory('pdf', filename)


# Пример маршрута контактов (страница пока не создана)
@app.route('/contacts')
def contacts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, label, value FROM contacts ORDER BY id ASC')
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('contacts.html', contacts=items)


@app.route('/erknm')
def erknm():
    conn = get_db()
    cur = conn.cursor()
    
    # Считаем количество сотрудников
    cur.execute('SELECT COUNT(*) FROM employees')
    employees_count = cur.fetchone()[0]
    
    # Считаем количество жалоб
    cur.execute('SELECT COUNT(*) FROM complaints')
    complaints_processed = cur.fetchone()[0]
    
    # Считаем количество заявок на работу
    cur.execute('SELECT COUNT(*) FROM job_applications')
    job_applications = cur.fetchone()[0]
    
    # Считаем количество одобренных заявок
    cur.execute('SELECT COUNT(*) FROM job_applications WHERE status="approved"')
    approved_applications = cur.fetchone()[0]
    
    # Считаем количество пользователей
    cur.execute('SELECT COUNT(*) FROM user_accounts')
    user_accounts = cur.fetchone()[0]
    
    # Политиков снято (берем из настроек app_settings)
    cur.execute('SELECT value FROM app_settings WHERE key=?', ('politicians_removed',))
    row = cur.fetchone()
    try:
        politicians_removed = int(row[0]) if row and row[0] is not None else 0
    except Exception:
        politicians_removed = 0
    
    conn.close()
    
    return render_template('erknm.html', 
                         employees_count=employees_count,
                         complaints_processed=complaints_processed,
                         politicians_removed=politicians_removed,
                         job_applications=job_applications,
                         approved_applications=approved_applications,
                         user_accounts=user_accounts)


@app.route('/admin/stats', methods=['GET', 'POST'])
def admin_stats():
    if not is_admin():
        flash('Необходимо войти как администратор', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        value = request.form.get('politicians_removed', '0').strip()
        # upsert настройку
        cur.execute("INSERT INTO app_settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (
            'politicians_removed', value
        ))
        conn.commit()
        conn.close()
        flash('Статистика обновлена', 'success')
        return redirect(url_for('admin_stats'))
    # GET
    cur.execute('SELECT value FROM app_settings WHERE key=?', ('politicians_removed',))
    row = cur.fetchone()
    current_value = row[0] if row and row[0] is not None else '0'
    conn.close()
    unread_count = get_unread_count('admin')
    return render_template('admin/stats.html', politicians_removed=current_value, unread_count=unread_count)


@app.route('/anticorruption')
def anticorruption():
    return render_template('anticorruption.html')


@app.route('/leadership')
def leadership():
    conn = get_db()
    cur = conn.cursor()
    
    # Get leaders with priority for deputies
    cur.execute('SELECT date, name, message, photo FROM leaders ORDER BY id DESC')
    all_leaders = cur.fetchall()
    
    # Separate deputies from other leaders
    deputies = []
    other_leaders = []
    
    for leader in all_leaders:
        position = leader[0] or ''  # date field contains position
        if any(keyword in position.lower() for keyword in ['зам', 'заместитель', 'первый зам']):
            deputies.append(leader)
        else:
            other_leaders.append(leader)
    
    # Combine: deputies first, then others
    leaders_data = deputies + other_leaders
    
    conn.close()
    return render_template('leadership.html', leaders=leaders_data)


@app.route('/hotline', methods=['GET', 'POST'])
def hotline():
    if request.method == 'POST':
        # Получаем данные формы
        fio = request.form.get('name', '').strip()
        organization = request.form.get('organization', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Сохраняем обращение в БД
        conn = get_db()
        conn.execute(
            'INSERT INTO hotline_appeals(fio, organization, subject, message) VALUES(?,?,?,?)',
            (fio, organization, subject, message)
        )
        conn.commit()
        conn.close()
        
        # Создать уведомление для админов
        create_notification(
            title="Новое обращение на горячую линию",
            message=f"Поступило обращение от {fio} на тему: {subject}",
            notification_type="hotline_appeal",
            recipient_role="admin"
        )
        
        return render_template('submitted.html', title='Обращение отправлено', message='Спасибо! Ваше обращение принято.')
    
    return render_template('hotline.html')


@app.route('/admin/contacts')
def admin_contacts():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, label, value FROM contacts ORDER BY id ASC')
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    unread_count = get_unread_count('admin')
    return render_template('admin/contacts.html', contacts=items, unread_count=unread_count)


@app.route('/admin/contacts/add', methods=['POST'])
def admin_contacts_add():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('INSERT INTO contacts(label, value) VALUES(?,?)', (
        request.form.get('label','').strip(), request.form.get('value','').strip()
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_contacts'))


@app.route('/admin/contacts/delete/<int:item_id>', methods=['POST'])
def admin_contacts_delete(item_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('DELETE FROM contacts WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_contacts'))


@app.route('/admin/jobs/approve/<int:app_id>', methods=['POST'])
def admin_approve_job(app_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get application details
    cur.execute('SELECT char_name, desired_login, desired_password, char_job, nick_ds FROM job_applications WHERE id=?', (app_id,))
    app_data = cur.fetchone()
    
    if not app_data:
        conn.close()
        return redirect(url_for('admin_jobs'))
    
    char_name, desired_login, desired_password, char_job, nick_ds = app_data
    
    # Check if username already exists
    cur.execute('SELECT id FROM user_accounts WHERE username=?', (desired_login,))
    if cur.fetchone():
        conn.close()
        flash(f'Ошибка: Логин "{desired_login}" уже существует!', 'error')
        return redirect(url_for('admin_jobs'))
    
    # Create user account
    try:
        cur.execute('INSERT INTO user_accounts(username, password, full_name, role, created_from_application) VALUES(?,?,?,?,?)',
                    (desired_login, desired_password, char_name, 'employee', app_id))
        # Also create employee directory record
        safe_position = (char_job or 'Сотрудник').strip() or 'Сотрудник'
        safe_contact = (nick_ds or '').strip()
        cur.execute('INSERT INTO employees(name, position, contact) VALUES(?,?,?)', (char_name, safe_position, safe_contact))
        
        # Update application status
        cur.execute('UPDATE job_applications SET status="approved" WHERE id=?', (app_id,))
        
        conn.commit()
        conn.close()
        flash(f'Заявка одобрена! Создан аккаунт для {char_name}', 'success')
        return redirect(url_for('admin_jobs'))
    except Exception as e:
        print(f"Error approving job application: {e}")
        conn.rollback()
        conn.close()
        flash(f'Ошибка при одобрении заявки: {str(e)}', 'error')
        return redirect(url_for('admin_jobs'))


@app.route('/admin/jobs/reject/<int:app_id>', methods=['POST'])
def admin_reject_job(app_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    conn.execute('UPDATE job_applications SET status="rejected" WHERE id=?', (app_id,))
    conn.commit()
    conn.close()
    flash('Заявка отклонена', 'info')
    return redirect(url_for('admin_jobs'))


@app.route('/admin/jobs/details/<int:app_id>')
def admin_job_details(app_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM job_applications WHERE id=?', (app_id,))
    app_data = cur.fetchone()
    conn.close()
    
    if not app_data:
        return jsonify({'error': 'Заявка не найдена'})
    
    # Convert to dict for easier access
    app_dict = dict(app_data)
    
    # Generate HTML for the modal
    html = f"""
    <h2 style="color: #2d3748; margin-bottom: 20px;">Детали заявки #{app_dict['id']}</h2>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
        <div>
            <h3 style="color: #4a5568; margin-bottom: 10px;">Основная информация</h3>
            <p><strong>ФИО персонажа:</strong> {app_dict['char_name'] or 'Не указано'}</p>
            <p><strong>Возраст персонажа:</strong> {app_dict['char_age'] or 'Не указано'}</p>
            <p><strong>Национальность:</strong> {app_dict['char_nationality'] or 'Не указано'}</p>
            <p><strong>Работа персонажа:</strong> {app_dict['char_job'] or 'Не указано'}</p>
            <p><strong>Образование:</strong> {app_dict['char_education'] or 'Не указано'}</p>
        </div>
        
        <div>
            <h3 style="color: #4a5568; margin-bottom: 10px;">Контактная информация</h3>
            <p><strong>Ник в ДС:</strong> {app_dict['nick_ds'] or 'Не указано'}</p>
            <p><strong>Ник в Roblox:</strong> {app_dict['nick_roblox'] or 'Не указано'}</p>
            <p><strong>Реальный возраст:</strong> {app_dict['real_age'] or 'Не указано'}</p>
            <p><strong>Дата рождения персонажа:</strong> {app_dict['char_birth'] or 'Не указано'}</p>
            <p><strong>Дата подачи:</strong> {app_dict['date_now'] or 'Не указано'}</p>
        </div>
    </div>
    
    <div style="margin-bottom: 20px;">
        <h3 style="color: #4a5568; margin-bottom: 10px;">О себе</h3>
        <div style="background: #f7fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
            {app_dict['about'] or 'Не указано'}
        </div>
    </div>
    
    <div style="margin-bottom: 20px;">
        <h3 style="color: #4a5568; margin-bottom: 10px;">Что такое прокуратура</h3>
        <div style="background: #f7fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
            {app_dict['what_is_prosecutor'] or 'Не указано'}
        </div>
    </div>
    
    <div style="margin-bottom: 20px;">
        <h3 style="color: #4a5568; margin-bottom: 10px;">Проверка грамотности</h3>
        <div style="background: #f7fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
            {app_dict['literacy_test'] or 'Не указано'}
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
        <div>
            <h3 style="color: #4a5568; margin-bottom: 10px;">Дополнительная информация</h3>
            <p><strong>Судимости:</strong> {'Да' if app_dict['has_convictions'] == 'yes' else 'Нет' if app_dict['has_convictions'] == 'no' else 'Не указано'}</p>
            <p><strong>Опыт:</strong> {'Да' if app_dict['has_experience'] == 'yes' else 'Нет' if app_dict['has_experience'] == 'no' else 'Не указано'}</p>
        </div>
        
        <div>
            <h3 style="color: #4a5568; margin-bottom: 10px;">Желаемые данные для входа</h3>
            <p><strong>Логин:</strong> {app_dict['desired_login'] or 'Не указано'}</p>
            <p><strong>Пароль:</strong> {'***' if app_dict['desired_password'] else 'Не указано'}</p>
        </div>
    </div>
    
    <div style="margin-bottom: 20px;">
        <h3 style="color: #4a5568; margin-bottom: 10px;">Расшифровка терминов</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <p><strong>УПК:</strong> {app_dict['term_upk'] or 'Не указано'}</p>
            <p><strong>УК:</strong> {app_dict['term_uk'] or 'Не указано'}</p>
            <p><strong>КоАП:</strong> {app_dict['term_koap'] or 'Не указано'}</p>
            <p><strong>ТК:</strong> {app_dict['term_tk'] or 'Не указано'}</p>
        </div>
    </div>
    
    <div style="background: #e6fffa; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
        <p><strong>Статус:</strong> 
            <span style="color: {'#f59e0b' if app_dict['status'] == 'pending' else '#10b981' if app_dict['status'] == 'approved' else '#ef4444' if app_dict['status'] == 'rejected' else '#6b7280'}; font-weight: 600;">
                {'Ожидает' if app_dict['status'] == 'pending' else 'Одобрено' if app_dict['status'] == 'approved' else 'Отклонено' if app_dict['status'] == 'rejected' else app_dict['status']}
            </span>
        </p>
        <p><strong>Дата создания:</strong> {app_dict['created_at'] or 'Не указано'}</p>
    </div>
    """
    
    return jsonify({'html': html})


@app.route('/admin/users')
def admin_users():
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, full_name, role, created_at FROM user_accounts ORDER BY created_at DESC')
    users = cur.fetchall()
    conn.close()
    unread_count = get_unread_count('admin')
    return render_template('admin/users.html', users=users, unread_count=unread_count)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'employee').strip()
        
        # Check if username already exists (excluding current user)
        cur.execute('SELECT id FROM user_accounts WHERE username=? AND id!=?', (username, user_id))
        if cur.fetchone():
            conn.close()
            flash(f'Ошибка: Логин "{username}" уже существует!', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))
        
        # Update user
        cur.execute('UPDATE user_accounts SET username=?, full_name=?, role=? WHERE id=?', 
                   (username, full_name, role, user_id))
        conn.commit()
        conn.close()
        flash('Пользователь обновлен', 'success')
        return redirect(url_for('admin_users'))
    
    # GET request - show edit form
    cur.execute('SELECT username, full_name, role FROM user_accounts WHERE id=?', (user_id,))
    user = cur.fetchone()
    conn.close()
    
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user={'id': user_id, 'username': user[0], 'full_name': user[1], 'role': user[2]})


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get user info before deletion
    cur.execute('SELECT username, full_name FROM user_accounts WHERE id=?', (user_id,))
    user = cur.fetchone()
    
    if user:
        # Delete user
        cur.execute('DELETE FROM user_accounts WHERE id=?', (user_id,))
        conn.commit()
        flash(f'Пользователь {user[1]} ({user[0]}) удален', 'success')
    else:
        flash('Пользователь не найден', 'error')
    
    conn.close()
    return redirect(url_for('admin_users'))


# ------------------ Prosecutor Panel ------------------
@app.route('/prosecutor')
def prosecutor_panel():
    if not is_prosecutor():
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, created_at, fio, nick_ds, violator_ds, violator_roblox, details, image, claimed_by, claimed_at FROM complaints ORDER BY id DESC LIMIT 200')
    complaints = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, created_by, title, description, url, status, created_at FROM documents_drafts ORDER BY id DESC LIMIT 100')
    drafts = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    # Get notifications for prosecutor
    notifications = get_notifications('prosecutor')
    unread_count = get_unread_count('prosecutor')
    
    return render_template('prosecutor/panel.html', complaints=complaints, drafts=drafts, proc_name=session.get('proc_name','Прокурор'), notifications=notifications, unread_count=unread_count)


@app.route('/prosecutor/claim/<int:cid>', methods=['POST'])
def prosecutor_claim(cid: int):
    if not is_prosecutor():
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('UPDATE complaints SET claimed_by=?, claimed_at=CURRENT_TIMESTAMP WHERE id=? AND claimed_by IS NULL', (
        session.get('proc_name','Прокурор'), cid
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('prosecutor_panel'))


@app.route('/prosecutor/draft/add', methods=['POST'])
def prosecutor_add_draft():
    if not is_prosecutor():
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('INSERT INTO documents_drafts(created_by, title, description, url) VALUES(?,?,?,?)', (
        session.get('proc_name','Прокурор'),
        request.form.get('title','').strip(),
        request.form.get('description','').strip(),
        request.form.get('url','').strip(),
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('prosecutor_panel'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)