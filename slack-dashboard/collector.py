#!/usr/bin/env python3
"""Slack data collector — fetches messages, reactions, and thread replies."""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import yaml
from dotenv import load_dotenv
from slack_sdk import WebClient

from db.schema import init_db
from slack_client.fetcher import SlackFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    with open(
        os.path.join(os.path.dirname(__file__), "config.yaml"), encoding="utf-8"
    ) as f:
        return yaml.safe_load(f)


def upsert_users(conn: sqlite3.Connection, users: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """INSERT INTO users (user_id, display_name, real_name, is_bot, updated_at)
           VALUES (:user_id, :display_name, :real_name, :is_bot, :now)
           ON CONFLICT(user_id) DO UPDATE SET
               display_name=excluded.display_name,
               real_name=excluded.real_name,
               is_bot=excluded.is_bot,
               updated_at=excluded.updated_at""",
        [{**u, "now": now} for u in users],
    )
    conn.commit()


def upsert_channels(conn: sqlite3.Connection, channels: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """INSERT INTO channels (channel_id, channel_name, is_archived, updated_at)
           VALUES (:channel_id, :channel_name, :is_archived, :now)
           ON CONFLICT(channel_id) DO UPDATE SET
               channel_name=excluded.channel_name,
               is_archived=excluded.is_archived,
               updated_at=excluded.updated_at""",
        [{**ch, "now": now} for ch in channels],
    )
    conn.commit()


def get_last_ts(conn: sqlite3.Connection, channel_id: str) -> str:
    row = conn.execute(
        "SELECT last_ts FROM fetch_state WHERE channel_id = ?", (channel_id,)
    ).fetchone()
    return row[0] if row else "0"


def update_last_ts(conn: sqlite3.Connection, channel_id: str, ts: str) -> None:
    conn.execute(
        """INSERT INTO fetch_state (channel_id, last_ts) VALUES (?, ?)
           ON CONFLICT(channel_id) DO UPDATE SET last_ts=excluded.last_ts""",
        (channel_id, ts),
    )
    conn.commit()


def store_messages(conn: sqlite3.Connection, messages: list[dict]) -> None:
    for msg in messages:
        conn.execute(
            """INSERT INTO messages (ts, channel_id, user_id, text, thread_ts,
                                     reply_count, is_reply, posted_at)
               VALUES (:ts, :channel_id, :user_id, :text, :thread_ts,
                        :reply_count, :is_reply, :posted_at)
               ON CONFLICT(channel_id, ts) DO UPDATE SET
                   reply_count=excluded.reply_count,
                   text=excluded.text""",
            msg,
        )
        for rxn in msg.get("reactions", []):
            conn.execute(
                """INSERT OR IGNORE INTO reactions
                   (channel_id, message_ts, message_user_id, reaction, reactor_user_id)
                   VALUES (:channel_id, :message_ts, :message_user_id,
                           :reaction, :reactor_user_id)""",
                rxn,
            )
    conn.commit()


def collect_channel(
    fetcher: SlackFetcher, conn: sqlite3.Connection, channel_id: str, oldest: str
) -> None:
    messages = fetcher.fetch_messages(channel_id, oldest=oldest)
    if not messages:
        logger.info("  No new messages")
        return

    # Fetch thread replies for messages that have replies
    all_messages = list(messages)
    for msg in messages:
        if msg["reply_count"] > 0 and not msg["is_reply"]:
            replies = fetcher.fetch_replies(channel_id, msg["ts"])
            all_messages.extend(replies)

    store_messages(conn, all_messages)

    # Update watermark to newest message ts
    newest_ts = max(m["ts"] for m in messages)
    update_last_ts(conn, channel_id, newest_ts)
    logger.info(
        "  Stored %d messages (%d including replies)",
        len(messages),
        len(all_messages),
    )


def run_collection(config: dict) -> None:
    token = os.environ["SLACK_BOT_TOKEN"]
    client = WebClient(token=token)
    fetcher = SlackFetcher(client)
    conn = init_db()

    # Fetch and store users
    logger.info("Fetching users...")
    users = fetcher.fetch_users()
    upsert_users(conn, users)

    # Fetch and store channels
    logger.info("Fetching channels...")
    all_channels = fetcher.fetch_channels()
    upsert_channels(conn, all_channels)

    # Filter channels — auto-join enabled (channels:join scope required)
    # Exclude log channels (prefixed with "aws")
    exclude_prefixes = config["collection"].get("exclude_prefixes", ["aws"])
    channel_filter = config["collection"].get("channels", "all")
    if channel_filter == "all":
        target_channels = [
            ch for ch in all_channels
            if not ch["is_archived"]
            and not any(ch["channel_name"].startswith(p) for p in exclude_prefixes)
        ]
    else:
        filter_set = set(channel_filter)
        target_channels = [
            ch for ch in all_channels
            if ch["channel_id"] in filter_set
            and not any(ch["channel_name"].startswith(p) for p in exclude_prefixes)
        ]
    logger.info("Target channels (excl. prefixes %s): %d / %d total",
                exclude_prefixes, len(target_channels), len(all_channels))

    # Default oldest for new channels
    history_days = config["collection"].get("initial_history_days", 90)
    default_oldest = str(
        (datetime.now(timezone.utc) - timedelta(days=history_days)).timestamp()
    )

    for ch in target_channels:
        cid = ch["channel_id"]
        cname = ch["channel_name"]
        last_ts = get_last_ts(conn, cid)
        oldest = last_ts if last_ts != "0" else default_oldest
        logger.info("Processing #%s (%s) from ts=%s", cname, cid, oldest)
        try:
            collect_channel(fetcher, conn, cid, oldest)
        except Exception:
            logger.exception("Error processing #%s", cname)

    conn.close()
    logger.info("Collection complete.")


def main() -> None:
    load_dotenv()
    config = load_config()

    parser = argparse.ArgumentParser(description="Slack data collector")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously on a schedule",
    )
    args = parser.parse_args()

    if args.daemon:
        from apscheduler.schedulers.blocking import BlockingScheduler

        interval = config["collection"].get("schedule_interval_minutes", 30)
        scheduler = BlockingScheduler()
        scheduler.add_job(
            run_collection, "interval", minutes=interval, args=[config]
        )
        logger.info("Starting daemon mode (interval=%d min)", interval)
        # Run once immediately, then on schedule
        run_collection(config)
        scheduler.start()
    else:
        run_collection(config)


if __name__ == "__main__":
    main()
