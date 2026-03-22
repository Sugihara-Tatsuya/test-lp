#!/usr/bin/env python3
"""Generate a static HTML dashboard (spreadsheet-style) for GitHub Pages.

Shows per-user monthly comparison of message counts and reaction counts
with Yellow/Red alerts when activity drops significantly.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

import pandas as pd

from db.schema import init_db
from db.queries import get_all_channels

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs")

# Alert thresholds (drop % from previous month)
YELLOW_THRESHOLD = 0.30  # 30% drop
RED_THRESHOLD = 0.50     # 50% drop


def get_monthly_user_stats(
    conn: sqlite3.Connection,
    months: list[str],
    channel_ids: list[str] | None = None,
) -> pd.DataFrame:
    """Get per-user message count and reaction count for each month.

    Returns DataFrame with columns:
      user_id, display_name, msg_YYYY-MM, rxn_YYYY-MM (for each month)
    """
    placeholders = ""
    params = []
    if channel_ids:
        ph = ", ".join("?" for _ in channel_ids)
        placeholders = f"AND m.channel_id IN ({ph})"
        params.extend(channel_ids)

    # Message counts per user per month
    month_cases_msg = []
    month_cases_rxn = []
    for m in months:
        month_cases_msg.append(
            f"SUM(CASE WHEN strftime('%Y-%m', m.posted_at) = '{m}' THEN 1 ELSE 0 END) AS \"msg_{m}\""
        )

    msg_query = f"""
        SELECT m.user_id,
               COALESCE(u.display_name, m.user_id) AS display_name,
               {', '.join(month_cases_msg)}
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.user_id
        WHERE m.is_reply = 0
          AND m.user_id IS NOT NULL
          {placeholders}
          AND strftime('%Y-%m', m.posted_at) IN ({', '.join('?' for _ in months)})
        GROUP BY m.user_id
    """
    msg_params = list(params) + list(months)
    msg_df = pd.read_sql_query(msg_query, conn, params=msg_params)

    # Reaction counts (received) per user per month
    rxn_cases = []
    for m in months:
        rxn_cases.append(
            f"SUM(CASE WHEN strftime('%Y-%m', m2.posted_at) = '{m}' THEN 1 ELSE 0 END) AS \"rxn_{m}\""
        )

    rxn_query = f"""
        SELECT r.message_user_id AS user_id,
               COALESCE(u.display_name, r.message_user_id) AS display_name,
               {', '.join(rxn_cases)}
        FROM reactions r
        JOIN messages m2 ON r.channel_id = m2.channel_id AND r.message_ts = m2.ts
        LEFT JOIN users u ON r.message_user_id = u.user_id
        WHERE r.message_user_id IS NOT NULL
          {'AND r.channel_id IN (' + ', '.join('?' for _ in channel_ids) + ')' if channel_ids else ''}
          AND strftime('%Y-%m', m2.posted_at) IN ({', '.join('?' for _ in months)})
        GROUP BY r.message_user_id
    """
    rxn_params = (list(channel_ids) if channel_ids else []) + list(months)
    rxn_df = pd.read_sql_query(rxn_query, conn, params=rxn_params)

    # Merge
    if msg_df.empty and rxn_df.empty:
        return pd.DataFrame()

    if msg_df.empty:
        df = rxn_df
    elif rxn_df.empty:
        df = msg_df
    else:
        df = pd.merge(msg_df, rxn_df.drop(columns=["display_name"]),
                       on="user_id", how="outer")
        # Fill display_name from whichever side has it
        df["display_name"] = df["display_name"].fillna(df["user_id"])

    # Fill NaN with 0
    for col in df.columns:
        if col.startswith("msg_") or col.startswith("rxn_"):
            df[col] = df[col].fillna(0).astype(int)

    return df


def compute_alert(current: int, previous: int) -> str:
    """Return alert level based on drop from previous month."""
    if previous == 0:
        return ""
    drop = (previous - current) / previous
    if drop >= RED_THRESHOLD:
        return "Red !"
    if drop >= YELLOW_THRESHOLD:
        return "Yellow !"
    return ""


def get_non_log_channel_ids(conn) -> list:
    """Return channel IDs excluding aws-* log channels."""
    channels_df = get_all_channels(conn)
    filtered = channels_df[~channels_df["channel_name"].str.startswith("aws")]
    return filtered["channel_id"].tolist() if not filtered.empty else None


def build_table_html(df: pd.DataFrame, months: list[str]) -> str:
    """Build the spreadsheet-style HTML table."""
    month_labels = []
    for m in months:
        y, mo = m.split("-")
        month_labels.append(f"{int(mo)}月")

    # Sort by current month message count descending
    current_msg_col = f"msg_{months[-1]}"
    if current_msg_col in df.columns:
        df = df.sort_values(current_msg_col, ascending=False)

    rows = []

    # Build rows
    for _, row in df.iterrows():
        name = row["display_name"]
        cells = f'<td class="name-cell">{name}</td>'

        # Message counts + alert
        msg_vals = []
        for m in months:
            col = f"msg_{m}"
            val = int(row.get(col, 0))
            msg_vals.append(val)
            cells += f'<td class="num">{val:,}</td>'

        # Message alert (current vs previous month)
        if len(msg_vals) >= 2:
            alert = compute_alert(msg_vals[-1], msg_vals[-2])
            cls = "alert-red" if "Red" in alert else ("alert-yellow" if "Yellow" in alert else "")
            cells += f'<td class="alert {cls}">{alert}</td>'
        else:
            cells += '<td class="alert"></td>'

        # Reaction counts + alert
        rxn_vals = []
        for m in months:
            col = f"rxn_{m}"
            val = int(row.get(col, 0))
            rxn_vals.append(val)
            cells += f'<td class="num">{val:,}</td>'

        # Reaction alert
        if len(rxn_vals) >= 2:
            alert = compute_alert(rxn_vals[-1], rxn_vals[-2])
            cls = "alert-red" if "Red" in alert else ("alert-yellow" if "Yellow" in alert else "")
            cells += f'<td class="alert {cls}">{alert}</td>'
        else:
            cells += '<td class="alert"></td>'

        rows.append(f"<tr>{cells}</tr>")

    # Summary row
    summary_cells = '<td class="name-cell summary">合計</td>'
    for m in months:
        col = f"msg_{m}"
        total = int(df[col].sum()) if col in df.columns else 0
        summary_cells += f'<td class="num summary">{total:,}</td>'
    summary_cells += '<td class="alert"></td>'
    for m in months:
        col = f"rxn_{m}"
        total = int(df[col].sum()) if col in df.columns else 0
        summary_cells += f'<td class="num summary">{total:,}</td>'
    summary_cells += '<td class="alert"></td>'

    return f"""
    <div class="table-wrapper">
    <table id="main-table">
      <thead>
        <tr class="header-group">
          <th rowspan="2" class="name-header">ユーザー名</th>
          <th colspan="{len(months) + 1}" class="group-header msg-group">メッセージ数</th>
          <th colspan="{len(months) + 1}" class="group-header rxn-group">リアクション数</th>
        </tr>
        <tr class="header-sub">
          {''.join(f'<th class="num">{ml}</th>' for ml in month_labels)}
          <th>アラート</th>
          {''.join(f'<th class="num">{ml}</th>' for ml in month_labels)}
          <th>アラート</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
      <tfoot>
        <tr>{summary_cells}</tr>
      </tfoot>
    </table>
    </div>
    """


def build_alert_summary(df: pd.DataFrame, months: list[str]) -> str:
    """Build a summary of users with alerts."""
    alerts = []
    current_msg = f"msg_{months[-1]}"
    prev_msg = f"msg_{months[-2]}" if len(months) >= 2 else None
    current_rxn = f"rxn_{months[-1]}"
    prev_rxn = f"rxn_{months[-2]}" if len(months) >= 2 else None

    for _, row in df.iterrows():
        name = row["display_name"]
        reasons = []
        if prev_msg and prev_msg in df.columns and current_msg in df.columns:
            alert = compute_alert(int(row.get(current_msg, 0)), int(row.get(prev_msg, 0)))
            if alert:
                prev_val = int(row.get(prev_msg, 0))
                curr_val = int(row.get(current_msg, 0))
                drop_pct = round((prev_val - curr_val) / prev_val * 100) if prev_val > 0 else 0
                reasons.append(f"メッセージ {alert} ({prev_val} → {curr_val}, -{drop_pct}%)")
        if prev_rxn and prev_rxn in df.columns and current_rxn in df.columns:
            alert = compute_alert(int(row.get(current_rxn, 0)), int(row.get(prev_rxn, 0)))
            if alert:
                prev_val = int(row.get(prev_rxn, 0))
                curr_val = int(row.get(current_rxn, 0))
                drop_pct = round((prev_val - curr_val) / prev_val * 100) if prev_val > 0 else 0
                reasons.append(f"リアクション {alert} ({prev_val} → {curr_val}, -{drop_pct}%)")
        if reasons:
            level = "red" if any("Red" in r for r in reasons) else "yellow"
            alerts.append((name, reasons, level))

    if not alerts:
        return '<div class="alert-summary ok">アラート対象者はいません</div>'

    items = []
    for name, reasons, level in alerts:
        icon = "&#x1F534;" if level == "red" else "&#x1F7E1;"
        reason_html = " / ".join(reasons)
        items.append(f'<li class="alert-item alert-item-{level}">{icon} <strong>{name}</strong>: {reason_html}</li>')

    return f"""
    <div class="alert-summary warning">
      <h3>アラート対象者 ({len(alerts)}名)</h3>
      <ul>{''.join(items)}</ul>
    </div>
    """


def generate_html(table_html: str, alert_html: str, months: list[str], stats: dict) -> str:
    month_labels = [f"{int(m.split('-')[1])}月" for m in months]
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Slack Activity Dashboard</title>
<style>
  :root {{
    --bg: #f5f6fa; --card-bg: #fff; --text: #2d3436;
    --border: #dfe6e9; --accent: #0984e3; --accent2: #6c5ce7;
    --yellow-bg: #ffeaa7; --yellow-text: #d35400;
    --red-bg: #fab1a0; --red-text: #c0392b;
    --green-bg: #55efc4; --green-text: #00b894;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    background: var(--bg); color: var(--text); font-size: 14px;
  }}
  header {{
    background: linear-gradient(135deg, #0984e3, #6c5ce7);
    color: #fff; padding: 1.8rem 2rem 1.4rem;
  }}
  header h1 {{ font-size: 1.6rem; margin-bottom: 0.2rem; }}
  header p {{ opacity: 0.85; font-size: 0.9rem; }}

  .container {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem; }}

  /* KPI cards */
  .kpi-row {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem; margin-bottom: 1.5rem;
  }}
  .kpi {{
    background: var(--card-bg); border-radius: 10px; padding: 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); text-align: center;
  }}
  .kpi .label {{ font-size: 0.8rem; color: #636e72; margin-bottom: 0.3rem; }}
  .kpi .value {{ font-size: 1.8rem; font-weight: 700; color: var(--accent); }}
  .kpi .sub {{ font-size: 0.75rem; color: #b2bec3; margin-top: 0.2rem; }}

  /* Alert summary */
  .alert-summary {{
    background: var(--card-bg); border-radius: 10px; padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .alert-summary.ok {{ border-left: 4px solid var(--green-bg); }}
  .alert-summary.warning {{ border-left: 4px solid var(--yellow-bg); }}
  .alert-summary h3 {{ font-size: 1rem; margin-bottom: 0.8rem; color: var(--yellow-text); }}
  .alert-summary ul {{ list-style: none; }}
  .alert-item {{ padding: 0.4rem 0; font-size: 0.9rem; }}
  .alert-item-red {{ color: var(--red-text); }}
  .alert-item-yellow {{ color: var(--yellow-text); }}

  /* Description */
  .description {{
    background: var(--card-bg); border-radius: 10px; padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border-left: 4px solid var(--accent);
    font-size: 0.88rem; line-height: 1.7; color: #636e72;
  }}

  /* Table */
  .section {{
    background: var(--card-bg); border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  .section h2 {{
    font-size: 1.1rem; margin-bottom: 1rem; color: var(--accent);
    padding-bottom: 0.4rem; border-bottom: 2px solid var(--accent);
  }}
  .table-wrapper {{ overflow-x: auto; }}
  table {{
    width: 100%; border-collapse: collapse; font-size: 0.85rem;
    white-space: nowrap;
  }}
  th, td {{
    padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border);
  }}
  .header-group th {{
    text-align: center; font-weight: 700; font-size: 0.9rem;
    border-bottom: 2px solid var(--border);
  }}
  .msg-group {{ background: #dfe6e9; }}
  .rxn-group {{ background: #ffeaa7; }}
  .header-sub th {{
    text-align: center; font-weight: 600; font-size: 0.8rem;
    background: #f8f9fa; border-bottom: 2px solid var(--border);
  }}
  .name-header {{
    text-align: left !important; background: #f8f9fa !important;
    min-width: 160px; position: sticky; left: 0; z-index: 2;
  }}
  .name-cell {{
    font-weight: 500; position: sticky; left: 0;
    background: #fff; z-index: 1; min-width: 160px;
  }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.alert {{
    text-align: center; font-weight: 700; font-size: 0.8rem;
    min-width: 80px;
  }}
  .alert-yellow {{ background: var(--yellow-bg); color: var(--yellow-text); }}
  .alert-red {{ background: var(--red-bg); color: var(--red-text); }}
  .summary {{ font-weight: 700; background: #f1f3f5 !important; }}
  tbody tr:hover td {{ background: #f0f4ff; }}
  tbody tr:hover .name-cell {{ background: #f0f4ff; }}
  tfoot td {{ border-top: 2px solid var(--border); }}

  /* Search */
  .search-box {{
    margin-bottom: 1rem; display: flex; gap: 0.5rem; align-items: center;
  }}
  .search-box input {{
    padding: 0.5rem 0.8rem; border: 1px solid var(--border);
    border-radius: 6px; font-size: 0.9rem; width: 260px;
  }}
  .search-box input:focus {{ outline: none; border-color: var(--accent); }}

  footer {{
    text-align: center; padding: 2rem; color: #b2bec3; font-size: 0.8rem;
  }}
  @media (max-width: 768px) {{
    header {{ padding: 1.2rem; }}
    .container {{ padding: 0.8rem; }}
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<header>
  <h1>Slack Activity Dashboard</h1>
  <p>月次レポート | {months[0]} 〜 {months[-1]} | 生成日: {date.today().isoformat()}</p>
</header>
<div class="container">

  <div class="description">
    Slackの投稿数とリアクション数を月次で集計し、前月比で30%以上低下した場合に<strong>Yellow</strong>、
    50%以上低下した場合に<strong>Red</strong>アラートを表示します。
    リアクション数が多いチームは雰囲気や生産性が高い傾向にあります。
    早期にフォローすることで、モチベーション低下を防ぎましょう。
  </div>

  <div class="kpi-row">
    <div class="kpi">
      <div class="label">対象ユーザー数</div>
      <div class="value">{stats['total_users']}</div>
    </div>
    <div class="kpi">
      <div class="label">当月メッセージ数</div>
      <div class="value">{stats['current_msg']:,}</div>
      <div class="sub">前月: {stats['prev_msg']:,}</div>
    </div>
    <div class="kpi">
      <div class="label">当月リアクション数</div>
      <div class="value">{stats['current_rxn']:,}</div>
      <div class="sub">前月: {stats['prev_rxn']:,}</div>
    </div>
    <div class="kpi">
      <div class="label">アラート対象者</div>
      <div class="value" style="color: {'var(--red-text)' if stats['alert_count'] > 0 else 'var(--green-text)'}">
        {stats['alert_count']}名
      </div>
    </div>
  </div>

  {alert_html}

  <div class="section">
    <h2>月次アクティビティ一覧</h2>
    <div class="search-box">
      <input type="text" id="search" placeholder="ユーザー名で検索..." oninput="filterTable()">
    </div>
    {table_html}
  </div>

</div>
<footer>
  Generated from Slack workspace data. Updated {date.today().isoformat()}.
</footer>
<script>
function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  const rows = document.querySelectorAll('#main-table tbody tr');
  rows.forEach(row => {{
    const name = row.cells[0].textContent.toLowerCase();
    row.style.display = name.includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""


def main():
    conn = init_db()

    today = date.today()
    # Compute 3 months: 2 months ago, last month, current month
    current_month = today.replace(day=1)
    prev_month = (current_month - timedelta(days=1)).replace(day=1)
    prev_prev_month = (prev_month - timedelta(days=1)).replace(day=1)

    months = [
        prev_prev_month.strftime("%Y-%m"),
        prev_month.strftime("%Y-%m"),
        current_month.strftime("%Y-%m"),
    ]

    print(f"Generating dashboard for months: {months}")

    # Exclude aws-* log channels
    channel_ids = get_non_log_channel_ids(conn)

    # Get stats
    df = get_monthly_user_stats(conn, months, channel_ids)

    if df.empty:
        print("No data found.")
        conn.close()
        return

    # Filter out users with zero activity across all months
    activity_cols = [c for c in df.columns if c.startswith("msg_") or c.startswith("rxn_")]
    df = df[df[activity_cols].sum(axis=1) > 0]

    # Filter out bots
    bot_ids = set(
        row[0] for row in conn.execute(
            "SELECT user_id FROM users WHERE is_bot = 1"
        ).fetchall()
    )
    df = df[~df["user_id"].isin(bot_ids)]

    # Compute stats
    current_msg_col = f"msg_{months[-1]}"
    prev_msg_col = f"msg_{months[-2]}"
    current_rxn_col = f"rxn_{months[-1]}"
    prev_rxn_col = f"rxn_{months[-2]}"

    alert_count = 0
    for _, row in df.iterrows():
        msg_alert = compute_alert(int(row.get(current_msg_col, 0)), int(row.get(prev_msg_col, 0)))
        rxn_alert = compute_alert(int(row.get(current_rxn_col, 0)), int(row.get(prev_rxn_col, 0)))
        if msg_alert or rxn_alert:
            alert_count += 1

    stats = {
        "total_users": len(df),
        "current_msg": int(df[current_msg_col].sum()) if current_msg_col in df.columns else 0,
        "prev_msg": int(df[prev_msg_col].sum()) if prev_msg_col in df.columns else 0,
        "current_rxn": int(df[current_rxn_col].sum()) if current_rxn_col in df.columns else 0,
        "prev_rxn": int(df[prev_rxn_col].sum()) if prev_rxn_col in df.columns else 0,
        "alert_count": alert_count,
    }

    # Build HTML
    table_html = build_table_html(df, months)
    alert_html = build_alert_summary(df, months)
    html = generate_html(table_html, alert_html, months, stats)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    conn.close()
    print(f"Static dashboard written to {out_path}")
    print(f"  Users: {stats['total_users']}, Alerts: {stats['alert_count']}")


if __name__ == "__main__":
    main()
