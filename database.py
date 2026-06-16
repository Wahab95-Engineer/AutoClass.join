import sqlite3

DB = "bot.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT, password TEXT, provider TEXT, imap_host TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, link TEXT, platform TEXT,
        scheduled_time TEXT, status TEXT DEFAULT 'pending', source TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT, level TEXT DEFAULT 'info',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def add_account(email, password, provider, imap_host):
    conn = get_conn()
    conn.execute("INSERT INTO accounts VALUES (NULL,?,?,?,?)", (email, password, provider, imap_host))
    conn.commit(); conn.close()

def get_accounts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_account(aid):
    conn = get_conn()
    conn.execute("DELETE FROM accounts WHERE id=?", (aid,))
    conn.commit(); conn.close()

def add_meeting(title, link, platform, scheduled_time, source="manual"):
    conn = get_conn()
    ex = conn.execute("SELECT id FROM meetings WHERE link=? AND scheduled_time=?", (link, scheduled_time)).fetchone()
    if ex:
        conn.close()
        return ex["id"]
    cur = conn.execute("INSERT INTO meetings VALUES (NULL,?,?,?,?,?,?)",
                       (title, link, platform, scheduled_time, "pending", source))
    mid = cur.lastrowid
    conn.commit(); conn.close()
    return mid

def get_meetings(status=None):
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM meetings WHERE status=? ORDER BY scheduled_time", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM meetings ORDER BY scheduled_time DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_status(mid, status):
    conn = get_conn()
    conn.execute("UPDATE meetings SET status=? WHERE id=?", (status, mid))
    conn.commit(); conn.close()

def delete_meeting(mid):
    conn = get_conn()
    conn.execute("DELETE FROM meetings WHERE id=?", (mid,))
    conn.commit(); conn.close()

def add_log(msg, level="info"):
    conn = get_conn()
    conn.execute("INSERT INTO logs (message, level) VALUES (?,?)", (msg, level))
    conn.commit(); conn.close()

def get_logs(limit=50):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]