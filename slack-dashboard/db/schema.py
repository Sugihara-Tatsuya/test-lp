from __future__ import annotations

import os
import sqlite3


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = os.environ.get("SLACK_DB_PATH", "./data/slack_activity.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fetch_state (
            channel_id   TEXT PRIMARY KEY,
            last_ts      TEXT NOT NULL DEFAULT '0'
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id      TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            real_name    TEXT,
            is_bot       INTEGER DEFAULT 0,
            updated_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS channels (
            channel_id   TEXT PRIMARY KEY,
            channel_name TEXT NOT NULL,
            is_archived  INTEGER DEFAULT 0,
            updated_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            ts           TEXT NOT NULL,
            channel_id   TEXT NOT NULL,
            user_id      TEXT,
            text         TEXT,
            thread_ts    TEXT,
            reply_count  INTEGER DEFAULT 0,
            is_reply     INTEGER DEFAULT 0,
            posted_at    TEXT NOT NULL,
            PRIMARY KEY (channel_id, ts)
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id       TEXT NOT NULL,
            message_ts       TEXT NOT NULL,
            message_user_id  TEXT,
            reaction         TEXT NOT NULL,
            reactor_user_id  TEXT NOT NULL,
            UNIQUE(channel_id, message_ts, reaction, reactor_user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_messages_posted_at
            ON messages(posted_at);
        CREATE INDEX IF NOT EXISTS idx_messages_user_channel
            ON messages(user_id, channel_id);
        CREATE INDEX IF NOT EXISTS idx_messages_is_reply
            ON messages(is_reply, channel_id);
        CREATE INDEX IF NOT EXISTS idx_reactions_reactor
            ON reactions(reactor_user_id);
        CREATE INDEX IF NOT EXISTS idx_reactions_receiver
            ON reactions(message_user_id);
    """)
