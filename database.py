"""
PostgreSQL database for tracking user downloads, bans, and admin broadcast.
Uses DATABASE_URL environment variable (automatically set by Replit/Railway).
"""

import os
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

# Thread-safe connection pool: min 2, max 10 simultaneous connections.
# This prevents both idle-connection waste and connection exhaustion.
_pool: pool.ThreadedConnectionPool | None = None


def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL environment variable is not set.")
        _pool = pool.ThreadedConnectionPool(2, 10, DATABASE_URL)
        logger.info("PostgreSQL connection pool created (min=2, max=10)")
    return _pool


@contextmanager
def _get_conn():
    """Context manager that borrows a connection from the pool and always returns it."""
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def init_db():
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id        BIGINT PRIMARY KEY,
                    username       TEXT,
                    first_name     TEXT,
                    download_count INTEGER DEFAULT 0,
                    first_used     TIMESTAMP DEFAULT NOW(),
                    last_used      TIMESTAMP DEFAULT NOW()
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS download_history (
                    id            SERIAL PRIMARY KEY,
                    user_id       BIGINT NOT NULL,
                    url           TEXT NOT NULL,
                    platform      TEXT,
                    downloaded_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id   BIGINT PRIMARY KEY,
                    banned_at TIMESTAMP DEFAULT NOW()
                )
            ''')
        logger.info("PostgreSQL database initialised.")
    except Exception as e:
        logger.error("DB init_db error: %s", e)
        raise


def register_user(user_id: int, username: str, first_name: str):
    """Register a user without incrementing their download counter."""
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (user_id, username, first_name, download_count)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (user_id) DO UPDATE SET
                    username   = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_used  = NOW()
            ''', (user_id, username or '', first_name or ''))
    except Exception as e:
        logger.error("DB register_user error: %s", e)


def record_download(user_id: int, username: str, first_name: str, url: str = '', platform: str = ''):
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (user_id, username, first_name, download_count)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    download_count = users.download_count + 1,
                    last_used      = NOW(),
                    username       = EXCLUDED.username,
                    first_name     = EXCLUDED.first_name
            ''', (user_id, username or '', first_name or ''))
            if url:
                c.execute('''
                    INSERT INTO download_history (user_id, url, platform)
                    VALUES (%s, %s, %s)
                ''', (user_id, url, platform or ''))
    except Exception as e:
        logger.error("DB record_download error: %s", e)


def get_user_stats(user_id: int):
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT download_count, first_used FROM users WHERE user_id = %s', (user_id,))
            return c.fetchone()
    except Exception as e:
        logger.error("DB get_user_stats error: %s", e)
        return None


def get_global_stats():
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT COUNT(*), COALESCE(SUM(download_count), 0) FROM users')
            return c.fetchone() or (0, 0)
    except Exception as e:
        logger.error("DB get_global_stats error: %s", e)
        return (0, 0)


def get_all_user_ids():
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT user_id FROM users')
            return [r[0] for r in c.fetchall()]
    except Exception as e:
        logger.error("DB get_all_user_ids error: %s", e)
        return []


def get_all_users():
    """Returns all users sorted by download count descending."""
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute(
                'SELECT user_id, first_name, username, download_count, last_used '
                'FROM users ORDER BY download_count DESC'
            )
            return c.fetchall()
    except Exception as e:
        logger.error("DB get_all_users error: %s", e)
        return []


def get_download_history(user_id: int, limit: int = 10):
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute(
                'SELECT url, platform, downloaded_at FROM download_history '
                'WHERE user_id = %s ORDER BY downloaded_at DESC LIMIT %s',
                (user_id, limit)
            )
            return c.fetchall()
    except Exception as e:
        logger.error("DB get_download_history error: %s", e)
        return []


def ban_user(user_id: int) -> bool:
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('INSERT INTO banned_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING', (user_id,))
            return c.rowcount > 0
    except Exception as e:
        logger.error("DB ban_user error: %s", e)
        return False


def unban_user(user_id: int) -> bool:
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM banned_users WHERE user_id = %s', (user_id,))
            return c.rowcount > 0
    except Exception as e:
        logger.error("DB unban_user error: %s", e)
        return False


def is_banned(user_id: int) -> bool:
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT 1 FROM banned_users WHERE user_id = %s', (user_id,))
            return c.fetchone() is not None
    except Exception as e:
        logger.error("DB is_banned error: %s", e)
        return False


def get_user_info(user_id: int):
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute(
                'SELECT user_id, username, first_name, download_count, first_used, last_used '
                'FROM users WHERE user_id = %s',
                (user_id,)
            )
            return c.fetchone()
    except Exception as e:
        logger.error("DB get_user_info error: %s", e)
        return None


def get_user_info_by_username(username: str):
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            clean = username.lstrip('@').lower()
            c.execute(
                'SELECT user_id, username, first_name, download_count, first_used, last_used '
                'FROM users WHERE LOWER(username) = %s',
                (clean,)
            )
            return c.fetchone()
    except Exception as e:
        logger.error("DB get_user_info_by_username error: %s", e)
        return None


def get_daily_stats():
    """Returns (downloads_last_24h, new_users_last_24h, top_3_users)."""
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            since = datetime.utcnow() - timedelta(days=1)
            c.execute('SELECT COUNT(*) FROM download_history WHERE downloaded_at >= %s', (since,))
            downloads = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM users WHERE first_used >= %s', (since,))
            new_users = c.fetchone()[0]
            c.execute(
                'SELECT first_name, username, download_count FROM users '
                'ORDER BY download_count DESC LIMIT 3'
            )
            top_users = c.fetchall()
            return downloads, new_users, top_users
    except Exception as e:
        logger.error("DB get_daily_stats error: %s", e)
        return 0, 0, []
