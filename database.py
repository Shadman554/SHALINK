"""
SQLite database for tracking user download stats, history, bans, and admin broadcast.
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_data.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            first_name     TEXT,
            download_count INTEGER DEFAULT 0,
            first_used     TEXT DEFAULT (datetime('now')),
            last_used      TEXT DEFAULT (datetime('now'))
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS download_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            url           TEXT NOT NULL,
            platform      TEXT,
            downloaded_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id   INTEGER PRIMARY KEY,
            banned_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


def record_download(user_id: int, username: str, first_name: str, url: str = '', platform: str = ''):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (user_id, username, first_name, download_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                download_count = download_count + 1,
                last_used      = datetime('now'),
                username       = excluded.username,
                first_name     = excluded.first_name
        ''', (user_id, username or '', first_name or ''))
        if url:
            c.execute('''
                INSERT INTO download_history (user_id, url, platform)
                VALUES (?, ?, ?)
            ''', (user_id, url, platform or ''))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("DB record_download error: %s", e)


def get_user_stats(user_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT download_count, first_used FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row
    except Exception as e:
        logger.error("DB get_user_stats error: %s", e)
        return None


def get_global_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*), COALESCE(SUM(download_count), 0) FROM users')
        row = c.fetchone()
        conn.close()
        return row or (0, 0)
    except Exception as e:
        logger.error("DB get_global_stats error: %s", e)
        return (0, 0)


def get_all_user_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id FROM users')
        rows = [r[0] for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error("DB get_all_user_ids error: %s", e)
        return []


def get_download_history(user_id: int, limit: int = 10):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'SELECT url, platform, downloaded_at FROM download_history WHERE user_id = ? ORDER BY downloaded_at DESC LIMIT ?',
            (user_id, limit)
        )
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error("DB get_download_history error: %s", e)
        return []


def ban_user(user_id: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error("DB ban_user error: %s", e)
        return False


def unban_user(user_id: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error("DB unban_user error: %s", e)
        return False


def is_banned(user_id: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        logger.error("DB is_banned error: %s", e)
        return False


def get_user_info(user_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'SELECT user_id, username, first_name, download_count, first_used, last_used FROM users WHERE user_id = ?',
            (user_id,)
        )
        row = c.fetchone()
        conn.close()
        return row
    except Exception as e:
        logger.error("DB get_user_info error: %s", e)
        return None


def get_daily_stats():
    """Returns (downloads_last_24h, new_users_last_24h, top_3_users)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute('SELECT COUNT(*) FROM download_history WHERE downloaded_at >= ?', (since,))
        downloads = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM users WHERE first_used >= ?', (since,))
        new_users = c.fetchone()[0]
        c.execute('SELECT first_name, username, download_count FROM users ORDER BY download_count DESC LIMIT 3')
        top_users = c.fetchall()
        conn.close()
        return downloads, new_users, top_users
    except Exception as e:
        logger.error("DB get_daily_stats error: %s", e)
        return 0, 0, []
