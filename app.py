from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session
import sqlite3
from pathlib import Path


app = Flask(__name__, template_folder='templates')
app.secret_key = 'change-me-in-production'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

DB_PATH = Path(__file__).with_name('data.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS slider_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            image TEXT NOT NULL
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
    conn.commit()
    conn.close()


init_db()


# При первом запуске добавим демо-данные, если таблицы пустые
def ensure_seed_data():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM slider_news')
    if c.fetchone()[0] == 0:
        c.executemany(
            'INSERT INTO slider_news(date, title, image) VALUES(?,?,?)',
            [
                ('09 Октября 2025, 14:52', 'Под председательством состоялось заседание коллегии, посвященное практике прокурорского надзора...', '/logo/logo.png'),
                ('08 Октября 2025, 10:20', 'Прокуратура разъяснила порядок обращений граждан и меры поддержки', '/logo/logo.png'),
                ('07 Октября 2025, 09:00', 'Обновлены методические рекомендации по противодействию коррупции', '/logo/logo.png'),
            ],
        )
    c.execute('SELECT COUNT(*) FROM feed_news')
    if c.fetchone()[0] == 0:
        c.executemany(
            'INSERT INTO feed_news(date, time, title, url) VALUES(?,?,?,?)',
            [
                ('2025-10-17', '15:26', 'В суд направлены уголовные дела в отношении двух наемников из Колумбии...', '#'),
                ('2025-10-17', '11:52', 'Военная прокуратура помогла матери погибшего участника СВО получить страховые выплаты', '#'),
                ('2025-10-17', '09:29', 'Вынесен приговор участникам батальона «Айдар» по делу о террористической деятельности', '#'),
                ('2025-10-16', '14:26', 'После вмешательства военной прокуратуры родители погибшего участника СВО получили выплаты', '#'),
                ('2025-10-16', '12:25', 'Военная прокуратура помогла родителям погибшего участника СВО получить выплаты', '#'),
                ('2025-10-16', '11:08', 'Предотвращен возможный вывод имущества аэропорта Домодедово', '#'),
                ('2025-10-15', '13:51', 'Состоялся приговор в отношении боевика ВСУ за тяжкие преступления', '#'),
            ],
        )
    conn.commit()
    conn.close()


ensure_seed_data()

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
        cur.execute('SELECT date, title, image FROM slider_news ORDER BY id DESC LIMIT 1 OFFSET ?', (offset,))
        row = cur.fetchone()
        if row:
            current_news = { 'date': row['date'], 'title': row['title'], 'image': row['image'] }
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
    cur.execute('SELECT date, time, title, url FROM feed_news ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, start))
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
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_home'))
        # обычное сообщение, если не админ
        if username:
            return render_template('submitted.html', title='Вход', message=f'Здравствуйте, {username}!')
        return render_template('login.html', error='Укажите логин и пароль')
    return render_template('login.html')


@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'POST':
        # Сохранение заявки в БД
        conn = get_db()
        conn.execute(
            'INSERT INTO job_applications(nick_ds, nick_roblox, char_name, real_age, char_birth, date_now, char_age, char_nationality, char_job, char_education, about, what_is_prosecutor, literacy_test, has_convictions, has_experience, term_upk, term_uk, term_koap, term_tk) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
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


@app.route('/admin', methods=['GET'])
def admin_home():
    if not is_admin():
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin_important'))


def admin_fetch_lists():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT date, title FROM slider_news ORDER BY id DESC LIMIT 50')
    slider = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, time, title, url FROM feed_news ORDER BY id DESC LIMIT 50')
    feed = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT name, position, contact FROM employees ORDER BY id DESC LIMIT 200')
    employees = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, title, url FROM documents ORDER BY id DESC LIMIT 200')
    documents = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT date, name, message FROM leaders ORDER BY id DESC LIMIT 50')
    leaders = [dict(r) for r in cur.fetchall()]
    cur.execute('SELECT created_at, char_name, char_age, char_nationality, char_job FROM job_applications ORDER BY id DESC LIMIT 200')
    job_apps = [dict(r) for r in cur.fetchall()]
    conn.close()
    return slider, feed, employees, documents, leaders, job_apps


@app.route('/admin/important')
def admin_important():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps = admin_fetch_lists()
    return render_template('admin/important.html', slider_news=slider)


@app.route('/admin/ordinary')
def admin_ordinary():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps = admin_fetch_lists()
    return render_template('admin/ordinary.html', feed=feed)


@app.route('/admin/employees')
def admin_employees():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps = admin_fetch_lists()
    return render_template('admin/employees.html', employees=employees)


@app.route('/admin/jobs')
def admin_jobs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps = admin_fetch_lists()
    return render_template('admin/jobs.html', job_apps=job_apps)


@app.route('/admin/docs')
def admin_docs():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps = admin_fetch_lists()
    return render_template('admin/documents.html', documents=documents)


@app.route('/admin/leader')
def admin_leader():
    if not is_admin():
        return redirect(url_for('admin_login'))
    slider, feed, employees, documents, leaders, job_apps = admin_fetch_lists()
    return render_template('admin/leader.html', leaders=leaders)


@app.route('/admin/news/add', methods=['POST'])
def admin_add_slider_news():
    if not is_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute(
        'INSERT INTO slider_news(date, title, image) VALUES(?,?,?)',
        (
            request.form.get('date', '').strip(),
            request.form.get('title', '').strip(),
            (request.form.get('image', '/logo/logo.png').strip() or '/logo/logo.png'),
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
        'INSERT INTO feed_news(date, time, title, url) VALUES(?,?,?,?)',
        (
            request.form.get('date', '').strip(),
            request.form.get('time', '').strip(),
            request.form.get('title', '').strip(),
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
    return render_template('internet-reception.html')


@app.route('/documents')
def documents():
    return render_template('documents.html')


# Статика для логотипа и других файлов из папки logo
@app.route('/logo/<path:filename>')
def logo_files(filename: str):
    return send_from_directory('logo', filename)


# Пример маршрута контактов (страница пока не создана)
@app.route('/contacts')
def contacts():
    # Верните существующий шаблон или временный текст
    return '<h1 style="font-family:Segoe UI, Arial, sans-serif;">Контакты — страница в разработке</h1>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)


