from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session
import sqlite3
from pathlib import Path
import os
from werkzeug.utils import secure_filename


app = Flask(__name__, template_folder='templates')
app.secret_key = 'change-me-in-production'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'
PROSECUTOR_USERNAME = 'proc'
PROSECUTOR_PASSWORD = 'proc123'

DB_PATH = Path(__file__).with_name('data.db')
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS slider_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            image TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nick_ds TEXT, nick_roblox TEXT,
            char_name TEXT, real_age INTEGER, char_birth TEXT, date_now TEXT,
            char_age INTEGER, char_nationality TEXT, char_job TEXT,
            char_education TEXT, about TEXT, what_is_prosecutor TEXT,
            literacy_test TEXT, has_convictions TEXT, has_experience TEXT,
            term_upk TEXT, term_uk TEXT, term_koap TEXT, term_tk TEXT,
            desired_login TEXT, desired_password TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            contact TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            title TEXT NOT NULL,
            url TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leaders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            name TEXT,
            message TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            value TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
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
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_by TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending' -- pending, approved, rejected
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'employee', -- employee, prosecutor, admin
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_from_application INTEGER, -- job application ID
            FOREIGN KEY (created_from_application) REFERENCES job_applications(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS organs_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            url TEXT
        )
        """
    )
    # Миграция: добавляем колонку description в documents, если её нет
    cur.execute("PRAGMA table_info(documents)")
    cols = [r[1] for r in cur.fetchall()]
    if 'description' not in cols:
        cur.execute('ALTER TABLE documents ADD COLUMN description TEXT')
    
    # Миграция: добавляем колонки claimed_by и claimed_at в complaints, если их нет
    cur.execute("PRAGMA table_info(complaints)")
    complaint_cols = [r[1] for r in cur.fetchall()]
    if 'claimed_by' not in complaint_cols:
        cur.execute('ALTER TABLE complaints ADD COLUMN claimed_by TEXT')
    if 'claimed_at' not in complaint_cols:
        cur.execute('ALTER TABLE complaints ADD COLUMN claimed_at TEXT')
    
    # Миграция: добавляем колонки в job_applications, если их нет
    cur.execute("PRAGMA table_info(job_applications)")
    job_cols = [r[1] for r in cur.fetchall()]
    if 'desired_login' not in job_cols:
        cur.execute('ALTER TABLE job_applications ADD COLUMN desired_login TEXT')
    if 'desired_password' not in job_cols:
        cur.execute('ALTER TABLE job_applications ADD COLUMN desired_password TEXT')
    if 'status' not in job_cols:
        cur.execute('ALTER TABLE job_applications ADD COLUMN status TEXT DEFAULT "pending"')

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
    conn.close()
    feed_grouped = group_news_by_date(rows)

    return render_template(
        'base.html',
        page=page,
        total_pages=total,
        news=current_news,
        feed_groups=feed_grouped,
        feed_page=feed_page,
        feed_pages=feed_pages,
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
        return render_template('submitted.html', title='Заявка отправлена', message='Спасибо! Ваша заявка принята.')
    return render_template('jobs.html')


# ------------------ Admin ------------------
def is_admin() -> bool:
    return bool(session.get('is_admin'))


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


def admin_fetch_lists():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT date, title, description, image FROM slider_news ORDER BY id DESC LIMIT 50')
    slider = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, time, title, description, url FROM feed_news ORDER BY id DESC LIMIT 50')
    feed = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT name, position, contact FROM employees ORDER BY id DESC LIMIT 200')
    employees = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, title, description, url FROM documents ORDER BY id DESC LIMIT 200')
    documents = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, name, message FROM leaders ORDER BY id DESC LIMIT 50')
    leaders = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, created_at, char_name, char_age, char_nationality, char_job, desired_login, status FROM job_applications ORDER BY id DESC LIMIT 200')
    job_apps = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT id, created_at, fio, nick_ds, violator_ds, violator_roblox, details, image, claimed_by, claimed_at FROM complaints ORDER BY id DESC LIMIT 200')
    complaints = [dict(r) for r in cur.fetchall()]
    conn.close()
    return slider, feed, employees, documents, leaders, job_apps, complaints


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
    return render_template('admin/important.html', slider_news=slider)


@app.route('/admin/ordinary')
def admin_ordinary():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    return render_template('admin/ordinary.html', feed=feed)


@app.route('/admin/employees')
def admin_employees():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    return render_template('admin/employees.html', employees=employees)


@app.route('/admin/jobs')
def admin_jobs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    return render_template('admin/jobs.html', job_apps=job_apps)


@app.route('/admin/docs')
def admin_docs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    return render_template('admin/documents.html', documents=documents)


@app.route('/admin/leader')
def admin_leader():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps, complaints = admin_fetch_lists()
    return render_template('admin/leader.html', leaders=leaders)


@app.route('/admin/complaints')
def admin_complaints():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, created_at, fio, nick_ds, violator_ds, violator_roblox, details, image, claimed_by, claimed_at FROM complaints ORDER BY id DESC LIMIT 300')
    complaints = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('admin/complaints.html', complaints=complaints)


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
    conn.execute('INSERT INTO leaders(date, name, message) VALUES(?,?,?)', (
        request.form.get('date'), request.form.get('name','').strip(), request.form.get('message','').strip()
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_leader'))


@app.route('/about')
def about():
    return render_template('about-the-proc.html')


@app.route('/activity')
def activity():
    return render_template('activity.html')



@app.route('/internet-reception')
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


@app.route('/admin/contacts')
def admin_contacts():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, label, value FROM contacts ORDER BY id ASC')
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('admin/contacts.html', contacts=items)


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
        return redirect(url_for('admin_jobs'))  # Username already exists
    
    # Create user account
    try:
        cur.execute('INSERT INTO user_accounts(username, password, full_name, role, created_from_application) VALUES(?,?,?,?,?)',
                    (desired_login, desired_password, char_name, 'employee', app_id))
        # Also create employee directory record
        safe_position = (char_job or 'Сотрудник').strip() or 'Сотрудник'
        safe_contact = (nick_ds or '').strip()
        cur.execute('INSERT INTO employees(name, position, contact) VALUES(?,?,?)', (char_name, safe_position, safe_contact))
    except Exception as e:
        conn.close()
        return redirect(url_for('admin_jobs'))
    
    # Update application status
    cur.execute('UPDATE job_applications SET status="approved" WHERE id=?', (app_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('admin_jobs'))


@app.route('/admin/jobs/reject/<int:app_id>', methods=['POST'])
def admin_reject_job(app_id: int):
    if not is_admin():
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    conn.execute('UPDATE job_applications SET status="rejected" WHERE id=?', (app_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_jobs'))


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
    return render_template('prosecutor/panel.html', complaints=complaints, drafts=drafts, proc_name=session.get('proc_name','Прокурор'))


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
    app.run(host='127.0.0.1', port=8080, debug=True)