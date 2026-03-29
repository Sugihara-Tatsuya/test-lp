"""Dashboard read queries — all functions return pandas DataFrames."""

from __future__ import annotations

import sqlite3

import pandas as pd


def get_message_counts(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    channel_ids: list[str] | None = None,
    period: str = "weekly",
) -> pd.DataFrame:
    """Per-user message counts grouped by period."""
    group_expr = _period_expr(period)
    params: list = [start_date, end_date]
    channel_filter = _channel_filter(channel_ids, params)

    query = f"""
        SELECT m.user_id,
               COALESCE(u.display_name, m.user_id) AS display_name,
               {group_expr} AS period,
               COUNT(*) AS message_count
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.user_id
        WHERE m.posted_at >= ? AND m.posted_at < ?
          AND m.is_reply = 0
          {channel_filter}
        GROUP BY m.user_id, period
        ORDER BY message_count DESC
    """
    return pd.read_sql_query(query, conn, params=params)


def get_reaction_counts(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    channel_ids: list[str] | None = None,
    period: str = "weekly",
) -> pd.DataFrame:
    """Reactions received and given per user, grouped by period."""
    group_expr = _period_expr(period, table="m")
    params_recv: list = [start_date, end_date]
    channel_filter_recv = _channel_filter(channel_ids, params_recv, table="r")

    received_query = f"""
        SELECT r.message_user_id AS user_id,
               COALESCE(u.display_name, r.message_user_id) AS display_name,
               {group_expr} AS period,
               COUNT(*) AS reactions_received
        FROM reactions r
        JOIN messages m ON r.channel_id = m.channel_id AND r.message_ts = m.ts
        LEFT JOIN users u ON r.message_user_id = u.user_id
        WHERE m.posted_at >= ? AND m.posted_at < ?
          {channel_filter_recv}
        GROUP BY r.message_user_id, period
    """
    df_recv = pd.read_sql_query(received_query, conn, params=params_recv)

    params_given: list = [start_date, end_date]
    channel_filter_given = _channel_filter(channel_ids, params_given, table="r")

    given_query = f"""
        SELECT r.reactor_user_id AS user_id,
               COALESCE(u.display_name, r.reactor_user_id) AS display_name,
               {group_expr} AS period,
               COUNT(*) AS reactions_given
        FROM reactions r
        JOIN messages m ON r.channel_id = m.channel_id AND r.message_ts = m.ts
        LEFT JOIN users u ON r.reactor_user_id = u.user_id
        WHERE m.posted_at >= ? AND m.posted_at < ?
          {channel_filter_given}
        GROUP BY r.reactor_user_id, period
    """
    df_given = pd.read_sql_query(given_query, conn, params=params_given)

    if df_recv.empty and df_given.empty:
        return pd.DataFrame(
            columns=["user_id", "display_name", "period", "reactions_received", "reactions_given"]
        )
    df = pd.merge(
        df_recv, df_given, on=["user_id", "display_name", "period"], how="outer"
    ).fillna(0)
    df["reactions_received"] = df["reactions_received"].astype(int)
    df["reactions_given"] = df["reactions_given"].astype(int)
    return df


def get_thread_reply_counts(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    channel_ids: list[str] | None = None,
    period: str = "weekly",
) -> pd.DataFrame:
    """Per-user thread reply counts grouped by period."""
    group_expr = _period_expr(period)
    params: list = [start_date, end_date]
    channel_filter = _channel_filter(channel_ids, params)

    query = f"""
        SELECT m.user_id,
               COALESCE(u.display_name, m.user_id) AS display_name,
               {group_expr} AS period,
               COUNT(*) AS reply_count
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.user_id
        WHERE m.posted_at >= ? AND m.posted_at < ?
          AND m.is_reply = 1
          {channel_filter}
        GROUP BY m.user_id, period
        ORDER BY reply_count DESC
    """
    return pd.read_sql_query(query, conn, params=params)


def get_hourly_activity(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    channel_ids: list[str] | None = None,
    tz_offset_hours: int = 9,
) -> pd.DataFrame:
    """Activity count by hour-of-day and day-of-week (for heatmap)."""
    params: list = [start_date, end_date]
    channel_filter = _channel_filter(channel_ids, params)

    query = f"""
        SELECT
            CAST(strftime('%w', datetime(m.posted_at, '+{tz_offset_hours} hours')) AS INTEGER) AS dow,
            CAST(strftime('%H', datetime(m.posted_at, '+{tz_offset_hours} hours')) AS INTEGER) AS hour,
            COUNT(*) AS count
        FROM messages m
        WHERE m.posted_at >= ? AND m.posted_at < ?
          {channel_filter}
        GROUP BY dow, hour
    """
    return pd.read_sql_query(query, conn, params=params)


def get_channel_breakdown(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    channel_ids: list[str] | None = None,
) -> pd.DataFrame:
    """Message count per channel."""
    params: list = [start_date, end_date]
    channel_filter = _channel_filter(channel_ids, params)

    query = f"""
        SELECT m.channel_id,
               COALESCE(c.channel_name, m.channel_id) AS channel_name,
               COUNT(*) AS message_count
        FROM messages m
        LEFT JOIN channels c ON m.channel_id = c.channel_id
        WHERE m.posted_at >= ? AND m.posted_at < ?
          {channel_filter}
        GROUP BY m.channel_id
        ORDER BY message_count DESC
    """
    return pd.read_sql_query(query, conn, params=params)


def get_trend_data(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    channel_ids: list[str] | None = None,
    period: str = "weekly",
) -> pd.DataFrame:
    """Total message count per period (for trend line)."""
    group_expr = _period_expr(period)
    params: list = [start_date, end_date]
    channel_filter = _channel_filter(channel_ids, params)

    query = f"""
        SELECT {group_expr} AS period,
               COUNT(*) AS message_count,
               COUNT(DISTINCT m.user_id) AS active_users
        FROM messages m
        WHERE m.posted_at >= ? AND m.posted_at < ?
          {channel_filter}
        GROUP BY period
        ORDER BY period
    """
    return pd.read_sql_query(query, conn, params=params)


def get_all_channels(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT channel_id, channel_name FROM channels WHERE is_archived = 0 ORDER BY channel_name",
        conn,
    )


# ── Helpers ──────────────────────────────────────────────────────


def _period_expr(period: str, table: str = "m") -> str:
    if period == "monthly":
        return f"strftime('%Y-%m', {table}.posted_at)"
    # weekly: ISO week start (Monday)
    return f"strftime('%Y-W%W', {table}.posted_at)"


def _channel_filter(
    channel_ids: list[str] | None, params: list, table: str = "m"
) -> str:
    if not channel_ids:
        return ""
    placeholders = ", ".join("?" for _ in channel_ids)
    params.extend(channel_ids)
    return f"AND {table}.channel_id IN ({placeholders})"
