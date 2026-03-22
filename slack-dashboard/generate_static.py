#!/usr/bin/env python3
"""Generate a static HTML dashboard (spreadsheet-style) for GitHub Pages.

Two tabs:
  1. 30-day comparison (current 30 days vs previous 30 days)
  2. 3-month comparison (current month, last month, 2 months ago)

Includes sort, filter, and alert functionality via JavaScript.
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

YELLOW_THRESHOLD = 0.30
RED_THRESHOLD = 0.50


def get_period_user_stats(
    conn: sqlite3.Connection,
    period_start: str,
    period_end: str,
    label: str,
    channel_ids: list[str] | None = None,
) -> pd.DataFrame:
    ch_filter_msg = ""
    ch_filter_rxn = ""
    msg_params = [period_start, period_end]
    rxn_params = []

    if channel_ids:
        ph = ", ".join("?" for _ in channel_ids)
        ch_filter_msg = f"AND m.channel_id IN ({ph})"
        ch_filter_rxn = f"AND r.channel_id IN ({ph})"
        msg_params.extend(channel_ids)
        rxn_params.extend(channel_ids)

    rxn_params.extend([period_start, period_end])

    msg_query = f"""
        SELECT m.user_id,
               COALESCE(u.display_name, m.user_id) AS display_name,
               COUNT(*) AS "msg_{label}"
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.user_id
        WHERE m.is_reply = 0 AND m.user_id IS NOT NULL
          AND m.posted_at >= ? AND m.posted_at < ?
          {ch_filter_msg}
        GROUP BY m.user_id
    """
    msg_df = pd.read_sql_query(msg_query, conn, params=msg_params)

    rxn_query = f"""
        SELECT r.message_user_id AS user_id,
               COALESCE(u.display_name, r.message_user_id) AS display_name,
               COUNT(*) AS "rxn_{label}"
        FROM reactions r
        JOIN messages m2 ON r.channel_id = m2.channel_id AND r.message_ts = m2.ts
        LEFT JOIN users u ON r.message_user_id = u.user_id
        WHERE r.message_user_id IS NOT NULL
          {ch_filter_rxn}
          AND m2.posted_at >= ? AND m2.posted_at < ?
        GROUP BY r.message_user_id
    """
    rxn_df = pd.read_sql_query(rxn_query, conn, params=rxn_params)

    if msg_df.empty and rxn_df.empty:
        return pd.DataFrame()
    if msg_df.empty:
        return rxn_df
    if rxn_df.empty:
        return msg_df

    df = pd.merge(msg_df, rxn_df.drop(columns=["display_name"]),
                   on="user_id", how="outer")
    df["display_name"] = df["display_name"].fillna(df["user_id"])
    return df


def compute_alert(current: int, previous: int) -> str:
    if previous == 0:
        return ""
    drop = (previous - current) / previous
    if drop >= RED_THRESHOLD:
        return "Red !"
    if drop >= YELLOW_THRESHOLD:
        return "Yellow !"
    return ""


def alert_class(alert: str) -> str:
    if "Red" in alert:
        return "alert-red"
    if "Yellow" in alert:
        return "alert-yellow"
    return ""


def row_alert_level(msg_alert: str, rxn_alert: str) -> str:
    if "Red" in msg_alert or "Red" in rxn_alert:
        return "red"
    if "Yellow" in msg_alert or "Yellow" in rxn_alert:
        return "yellow"
    return "none"


def get_non_log_channel_ids(conn) -> list:
    channels_df = get_all_channels(conn)
    filtered = channels_df[
        ~channels_df["channel_name"].str.startswith("aws")
        & ~channels_df["channel_name"].str.startswith("xo_order")
    ]
    return filtered["channel_id"].tolist() if not filtered.empty else None


def filter_df(df: pd.DataFrame, conn: sqlite3.Connection, cols: list) -> pd.DataFrame:
    """Remove bots and zero-activity users."""
    for col in cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0).astype(int)
    df = df[df[cols].sum(axis=1) > 0]
    bot_ids = set(r[0] for r in conn.execute("SELECT user_id FROM users WHERE is_bot = 1").fetchall())
    return df[~df["user_id"].isin(bot_ids)]


# ── 30-day tab ──────────────────────────────────────────────────

def build_30day_rows(df: pd.DataFrame) -> str:
    rows = []
    for _, row in df.iterrows():
        mp, mc = int(row.get("msg_prev", 0)), int(row.get("msg_curr", 0))
        rp, rc = int(row.get("rxn_prev", 0)), int(row.get("rxn_curr", 0))
        ma, ra = compute_alert(mc, mp), compute_alert(rc, rp)
        rl = row_alert_level(ma, ra)
        rows.append(
            f'<tr data-alert="{rl}" data-msg-curr="{mc}" data-msg-prev="{mp}" '
            f'data-rxn-curr="{rc}" data-rxn-prev="{rp}">'
            f'<td class="name-cell">{row["display_name"]}</td>'
            f'<td class="num">{mp:,}</td><td class="num">{mc:,}</td>'
            f'<td class="alert {alert_class(ma)}">{ma}</td>'
            f'<td class="num">{rp:,}</td><td class="num">{rc:,}</td>'
            f'<td class="alert {alert_class(ra)}">{ra}</td></tr>'
        )
    return "\n".join(rows)


# ── 3-month tab ─────────────────────────────────────────────────

def build_3month_rows(df: pd.DataFrame, months: list) -> str:
    rows = []
    for _, row in df.iterrows():
        m0 = int(row.get(f"msg_{months[0]}", 0))
        m1 = int(row.get(f"msg_{months[1]}", 0))
        m2 = int(row.get(f"msg_{months[2]}", 0))
        r0 = int(row.get(f"rxn_{months[0]}", 0))
        r1 = int(row.get(f"rxn_{months[1]}", 0))
        r2 = int(row.get(f"rxn_{months[2]}", 0))
        ma = compute_alert(m2, m1)
        ra = compute_alert(r2, r1)
        rl = row_alert_level(ma, ra)
        rows.append(
            f'<tr data-alert="{rl}" data-m0="{m0}" data-m1="{m1}" data-m2="{m2}" '
            f'data-r0="{r0}" data-r1="{r1}" data-r2="{r2}">'
            f'<td class="name-cell">{row["display_name"]}</td>'
            f'<td class="num">{m0:,}</td><td class="num">{m1:,}</td><td class="num">{m2:,}</td>'
            f'<td class="alert {alert_class(ma)}">{ma}</td>'
            f'<td class="num">{r0:,}</td><td class="num">{r1:,}</td><td class="num">{r2:,}</td>'
            f'<td class="alert {alert_class(ra)}">{ra}</td></tr>'
        )
    return "\n".join(rows)


def build_alert_summary(items_list: list) -> str:
    if not items_list:
        return '<div class="alert-summary ok">アラート対象者はいません</div>'
    items = []
    for name, reasons, level in items_list:
        icon = "&#x1F534;" if level == "red" else "&#x1F7E1;"
        reason_html = " / ".join(reasons)
        items.append(f'<li class="alert-item alert-item-{level}">{icon} <strong>{name}</strong>: {reason_html}</li>')
    return f"""<div class="alert-summary warning">
      <h3>アラート対象者 ({len(items_list)}名)</h3>
      <ul>{''.join(items)}</ul></div>"""


def collect_alerts(df, msg_curr_col, msg_prev_col, rxn_curr_col, rxn_prev_col):
    alerts = []
    for _, row in df.iterrows():
        reasons = []
        mc, mp = int(row.get(msg_curr_col, 0)), int(row.get(msg_prev_col, 0))
        rc, rp = int(row.get(rxn_curr_col, 0)), int(row.get(rxn_prev_col, 0))
        ma = compute_alert(mc, mp)
        if ma:
            dp = round((mp - mc) / mp * 100) if mp > 0 else 0
            reasons.append(f"メッセージ {ma} ({mp} → {mc}, -{dp}%)")
        ra = compute_alert(rc, rp)
        if ra:
            dp = round((rp - rc) / rp * 100) if rp > 0 else 0
            reasons.append(f"リアクション {ra} ({rp} → {rc}, -{dp}%)")
        if reasons:
            level = "red" if any("Red" in r for r in reasons) else "yellow"
            alerts.append((row["display_name"], reasons, level))
    return alerts


def generate_html(
    tab30_rows, tab30_alert, tab30_stats, prev_label, curr_label,
    tab3m_rows, tab3m_alert, tab3m_stats, month_labels, months,
) -> str:
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

  /* Tabs */
  .tab-bar {{
    display: flex; gap: 0; margin-bottom: 1.5rem;
    border-bottom: 2px solid var(--border);
  }}
  .tab-btn {{
    padding: 0.8rem 1.5rem; border: none; background: none;
    font-size: 0.95rem; font-weight: 600; cursor: pointer;
    color: #636e72; border-bottom: 3px solid transparent;
    transition: all 0.2s;
  }}
  .tab-btn:hover {{ color: var(--accent); }}
  .tab-btn.active {{
    color: var(--accent); border-bottom-color: var(--accent);
  }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}

  .description {{
    background: var(--card-bg); border-radius: 10px; padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border-left: 4px solid var(--accent);
    font-size: 0.88rem; line-height: 1.7; color: #636e72;
  }}
  .kpi-row {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem; margin-bottom: 1.5rem;
  }}
  .kpi {{
    background: var(--card-bg); border-radius: 10px; padding: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); text-align: center;
  }}
  .kpi .label {{ font-size: 0.78rem; color: #636e72; margin-bottom: 0.2rem; }}
  .kpi .value {{ font-size: 1.6rem; font-weight: 700; color: var(--accent); }}
  .kpi .sub {{ font-size: 0.72rem; color: #b2bec3; margin-top: 0.15rem; }}
  .alert-summary {{
    background: var(--card-bg); border-radius: 10px; padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .alert-summary.ok {{ border-left: 4px solid var(--green-bg); }}
  .alert-summary.warning {{ border-left: 4px solid var(--yellow-bg); }}
  .alert-summary h3 {{ font-size: 1rem; margin-bottom: 0.8rem; color: var(--yellow-text); }}
  .alert-summary ul {{ list-style: none; }}
  .alert-item {{ padding: 0.3rem 0; font-size: 0.88rem; }}
  .alert-item-red {{ color: var(--red-text); }}
  .alert-item-yellow {{ color: var(--yellow-text); }}
  .section {{
    background: var(--card-bg); border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  .section h2 {{
    font-size: 1.1rem; margin-bottom: 1rem; color: var(--accent);
    padding-bottom: 0.4rem; border-bottom: 2px solid var(--accent);
  }}
  .toolbar {{
    display: flex; flex-wrap: wrap; gap: 0.8rem; margin-bottom: 1rem; align-items: center;
  }}
  .toolbar input {{
    padding: 0.5rem 0.8rem; border: 1px solid var(--border);
    border-radius: 6px; font-size: 0.9rem; width: 220px;
  }}
  .toolbar input:focus {{ outline: none; border-color: var(--accent); }}
  .toolbar select {{
    padding: 0.5rem 0.8rem; border: 1px solid var(--border);
    border-radius: 6px; font-size: 0.85rem; background: #fff; cursor: pointer;
  }}
  .toolbar label {{ font-size: 0.85rem; color: #636e72; }}
  .table-wrapper {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; white-space: nowrap; }}
  th, td {{ padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border); }}
  .header-group th {{
    text-align: center; font-weight: 700; font-size: 0.9rem;
    border-bottom: 2px solid var(--border);
  }}
  .msg-group {{ background: #dfe6e9; }}
  .rxn-group {{ background: #ffeaa7; }}
  .header-sub th {{
    text-align: center; font-weight: 600; font-size: 0.8rem;
    background: #f8f9fa; border-bottom: 2px solid var(--border);
    cursor: pointer; user-select: none;
  }}
  .header-sub th:hover {{ background: #e9ecef; }}
  .header-sub th.sort-asc::after {{ content: " ▲"; font-size: 0.7rem; }}
  .header-sub th.sort-desc::after {{ content: " ▼"; font-size: 0.7rem; }}
  .name-header {{
    text-align: left !important; background: #f8f9fa !important;
    min-width: 160px; position: sticky; left: 0; z-index: 2; cursor: pointer;
  }}
  .name-cell {{
    font-weight: 500; position: sticky; left: 0;
    background: #fff; z-index: 1; min-width: 160px;
  }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.alert {{ text-align: center; font-weight: 700; font-size: 0.8rem; min-width: 80px; }}
  .alert-yellow {{ background: var(--yellow-bg); color: var(--yellow-text); }}
  .alert-red {{ background: var(--red-bg); color: var(--red-text); }}
  .summary {{ font-weight: 700; background: #f1f3f5 !important; }}
  tbody tr:hover td {{ background: #f0f4ff; }}
  tbody tr:hover .name-cell {{ background: #f0f4ff; }}
  tfoot td {{ border-top: 2px solid var(--border); }}
  footer {{ text-align: center; padding: 2rem; color: #b2bec3; font-size: 0.8rem; }}
  @media (max-width: 768px) {{
    header {{ padding: 1.2rem; }}
    .container {{ padding: 0.8rem; }}
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .toolbar {{ flex-direction: column; }}
    .toolbar input {{ width: 100%; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Slack Activity Dashboard</h1>
  <p>生成日: {date.today().isoformat()}</p>
</header>
<div class="container">

  <div class="description">
    投稿数・リアクション数を期間比較し、前期間比で<strong>30%以上低下→Yellow</strong>、
    <strong>50%以上低下→Red</strong>アラートを表示。
    リアクションが多いチームは雰囲気・生産性が高い傾向にあります。早期フォローでモチベーション低下を防ぎましょう。
  </div>

  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab('tab30')">30日間比較</button>
    <button class="tab-btn" onclick="switchTab('tab3m')">直近3ヶ月</button>
  </div>

  <!-- ===== 30-day tab ===== -->
  <div id="tab30" class="tab-content active">
    <div class="kpi-row">
      <div class="kpi"><div class="label">対象ユーザー</div><div class="value">{tab30_stats['total_users']}</div></div>
      <div class="kpi"><div class="label">当期間メッセージ</div><div class="value">{tab30_stats['current_msg']:,}</div><div class="sub">前期間: {tab30_stats['prev_msg']:,}</div></div>
      <div class="kpi"><div class="label">当期間リアクション</div><div class="value">{tab30_stats['current_rxn']:,}</div><div class="sub">前期間: {tab30_stats['prev_rxn']:,}</div></div>
      <div class="kpi"><div class="label">アラート対象</div><div class="value" style="color:{'var(--red-text)' if tab30_stats['alert_count']>0 else 'var(--green-text)'}">{tab30_stats['alert_count']}名</div></div>
    </div>
    {tab30_alert}
    <div class="section">
      <h2>30日間比較（{prev_label} vs {curr_label}）</h2>
      <div class="toolbar">
        <input type="text" id="search30" placeholder="ユーザー名で検索..." oninput="applyFilters('tab30')">
        <label>絞り込み:</label>
        <select id="filter30" onchange="applyFilters('tab30')">
          <option value="all">全員</option><option value="alert">アラートのみ</option>
          <option value="red">Red ! のみ</option><option value="yellow">Yellow ! のみ</option>
          <option value="none">アラートなし</option>
        </select>
      </div>
      <div class="table-wrapper">
      <table id="table30">
        <thead>
          <tr class="header-group">
            <th rowspan="2" class="name-header" onclick="sortTable('table30','name')">ユーザー名</th>
            <th colspan="3" class="group-header msg-group">メッセージ数</th>
            <th colspan="3" class="group-header rxn-group">リアクション数</th>
          </tr>
          <tr class="header-sub">
            <th class="num" data-col="msg-prev" onclick="sortTable('table30','msg-prev')">前30日</th>
            <th class="num sort-desc" data-col="msg-curr" onclick="sortTable('table30','msg-curr')">直近30日</th>
            <th data-col="msg-alert" onclick="sortTable('table30','msg-alert')">アラート</th>
            <th class="num" data-col="rxn-prev" onclick="sortTable('table30','rxn-prev')">前30日</th>
            <th class="num" data-col="rxn-curr" onclick="sortTable('table30','rxn-curr')">直近30日</th>
            <th data-col="rxn-alert" onclick="sortTable('table30','rxn-alert')">アラート</th>
          </tr>
        </thead>
        <tbody>{tab30_rows}</tbody>
        <tfoot><tr>
          <td class="name-cell summary">合計</td>
          <td class="num summary">{tab30_stats['prev_msg']:,}</td>
          <td class="num summary">{tab30_stats['current_msg']:,}</td>
          <td class="alert"></td>
          <td class="num summary">{tab30_stats['prev_rxn']:,}</td>
          <td class="num summary">{tab30_stats['current_rxn']:,}</td>
          <td class="alert"></td>
        </tr></tfoot>
      </table>
      </div>
    </div>
  </div>

  <!-- ===== 3-month tab ===== -->
  <div id="tab3m" class="tab-content">
    <div class="kpi-row">
      <div class="kpi"><div class="label">対象ユーザー</div><div class="value">{tab3m_stats['total_users']}</div></div>
      <div class="kpi"><div class="label">{month_labels[2]}メッセージ</div><div class="value">{tab3m_stats['current_msg']:,}</div><div class="sub">{month_labels[1]}: {tab3m_stats['prev_msg']:,}</div></div>
      <div class="kpi"><div class="label">{month_labels[2]}リアクション</div><div class="value">{tab3m_stats['current_rxn']:,}</div><div class="sub">{month_labels[1]}: {tab3m_stats['prev_rxn']:,}</div></div>
      <div class="kpi"><div class="label">アラート対象</div><div class="value" style="color:{'var(--red-text)' if tab3m_stats['alert_count']>0 else 'var(--green-text)'}">{tab3m_stats['alert_count']}名</div></div>
    </div>
    {tab3m_alert}
    <div class="section">
      <h2>月次比較（{month_labels[0]}〜{month_labels[2]}）</h2>
      <div class="toolbar">
        <input type="text" id="search3m" placeholder="ユーザー名で検索..." oninput="applyFilters('tab3m')">
        <label>絞り込み:</label>
        <select id="filter3m" onchange="applyFilters('tab3m')">
          <option value="all">全員</option><option value="alert">アラートのみ</option>
          <option value="red">Red ! のみ</option><option value="yellow">Yellow ! のみ</option>
          <option value="none">アラートなし</option>
        </select>
      </div>
      <div class="table-wrapper">
      <table id="table3m">
        <thead>
          <tr class="header-group">
            <th rowspan="2" class="name-header" onclick="sortTable('table3m','name')">ユーザー名</th>
            <th colspan="4" class="group-header msg-group">メッセージ数</th>
            <th colspan="4" class="group-header rxn-group">リアクション数</th>
          </tr>
          <tr class="header-sub">
            <th class="num" data-col="m0" onclick="sortTable('table3m','m0')">{month_labels[0]}</th>
            <th class="num" data-col="m1" onclick="sortTable('table3m','m1')">{month_labels[1]}</th>
            <th class="num sort-desc" data-col="m2" onclick="sortTable('table3m','m2')">{month_labels[2]}</th>
            <th data-col="msg-alert" onclick="sortTable('table3m','msg-alert')">アラート</th>
            <th class="num" data-col="r0" onclick="sortTable('table3m','r0')">{month_labels[0]}</th>
            <th class="num" data-col="r1" onclick="sortTable('table3m','r1')">{month_labels[1]}</th>
            <th class="num" data-col="r2" onclick="sortTable('table3m','r2')">{month_labels[2]}</th>
            <th data-col="rxn-alert" onclick="sortTable('table3m','rxn-alert')">アラート</th>
          </tr>
        </thead>
        <tbody>{tab3m_rows}</tbody>
        <tfoot><tr>
          <td class="name-cell summary">合計</td>
          <td class="num summary">{tab3m_stats['m0_msg']:,}</td>
          <td class="num summary">{tab3m_stats['prev_msg']:,}</td>
          <td class="num summary">{tab3m_stats['current_msg']:,}</td>
          <td class="alert"></td>
          <td class="num summary">{tab3m_stats['m0_rxn']:,}</td>
          <td class="num summary">{tab3m_stats['prev_rxn']:,}</td>
          <td class="num summary">{tab3m_stats['current_rxn']:,}</td>
          <td class="alert"></td>
        </tr></tfoot>
      </table>
      </div>
    </div>
  </div>

</div>
<footer>Generated from Slack workspace data. Updated {date.today().isoformat()}.</footer>
<script>
const sortState = {{}};

function switchTab(tabId) {{
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  event.target.classList.add('active');
}}

function sortTable(tableId, col) {{
  const table = document.getElementById(tableId);
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  if (!sortState[tableId]) sortState[tableId] = {{ col: col, dir: 'desc' }};
  const st = sortState[tableId];
  st.dir = st.col === col ? (st.dir === 'asc' ? 'desc' : 'asc') : 'desc';
  st.col = col;

  table.querySelectorAll('.header-sub th, .name-header').forEach(th => {{
    th.classList.remove('sort-asc', 'sort-desc');
  }});
  const hdr = col === 'name'
    ? table.querySelector('.name-header')
    : table.querySelector(`th[data-col="${{col}}"]`);
  if (hdr) hdr.classList.add(st.dir === 'asc' ? 'sort-asc' : 'sort-desc');

  rows.sort((a, b) => {{
    let va, vb;
    if (col === 'name') {{
      va = a.cells[0].textContent.toLowerCase();
      vb = b.cells[0].textContent.toLowerCase();
      return st.dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
    }}
    if (col === 'msg-alert' || col === 'rxn-alert') {{
      const ci = col === 'msg-alert'
        ? (tableId === 'table30' ? 3 : 4)
        : (tableId === 'table30' ? 6 : 8);
      va = alertRank(a.cells[ci].textContent.trim());
      vb = alertRank(b.cells[ci].textContent.trim());
    }} else {{
      const key = col.replace('-','');
      va = parseInt(a.dataset[key]) || 0;
      vb = parseInt(b.dataset[key]) || 0;
    }}
    return st.dir === 'asc' ? va - vb : vb - va;
  }});
  rows.forEach(r => tbody.appendChild(r));
}}

function alertRank(t) {{ return t.includes('Red') ? 2 : t.includes('Yellow') ? 1 : 0; }}

function applyFilters(tabId) {{
  const sfx = tabId === 'tab30' ? '30' : '3m';
  const q = document.getElementById('search' + sfx).value.toLowerCase();
  const f = document.getElementById('filter' + sfx).value;
  const tableId = tabId === 'tab30' ? 'table30' : 'table3m';
  document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {{
    const name = row.cells[0].textContent.toLowerCase();
    const alert = row.dataset.alert;
    let am = true;
    if (f === 'alert') am = alert !== 'none';
    else if (f === 'red') am = alert === 'red';
    else if (f === 'yellow') am = alert === 'yellow';
    else if (f === 'none') am = alert === 'none';
    row.style.display = (name.includes(q) && am) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""


def get_monthly_user_stats(conn, months, channel_ids):
    """Get per-user msg/rxn for each of 3 months."""
    ch_filter_msg = ""
    ch_filter_rxn = ""
    msg_params = []
    rxn_params = []
    if channel_ids:
        ph = ", ".join("?" for _ in channel_ids)
        ch_filter_msg = f"AND m.channel_id IN ({ph})"
        ch_filter_rxn = f"AND r.channel_id IN ({ph})"
        msg_params.extend(channel_ids)
        rxn_params.extend(channel_ids)

    msg_cases = ", ".join(
        f"SUM(CASE WHEN strftime('%Y-%m', m.posted_at)='{m}' THEN 1 ELSE 0 END) AS \"msg_{m}\""
        for m in months
    )
    msg_query = f"""
        SELECT m.user_id, COALESCE(u.display_name, m.user_id) AS display_name, {msg_cases}
        FROM messages m LEFT JOIN users u ON m.user_id = u.user_id
        WHERE m.is_reply = 0 AND m.user_id IS NOT NULL {ch_filter_msg}
          AND strftime('%Y-%m', m.posted_at) IN ({','.join('?' for _ in months)})
        GROUP BY m.user_id
    """
    msg_df = pd.read_sql_query(msg_query, conn, params=msg_params + list(months))

    rxn_cases = ", ".join(
        f"SUM(CASE WHEN strftime('%Y-%m', m2.posted_at)='{m}' THEN 1 ELSE 0 END) AS \"rxn_{m}\""
        for m in months
    )
    rxn_query = f"""
        SELECT r.message_user_id AS user_id, COALESCE(u.display_name, r.message_user_id) AS display_name, {rxn_cases}
        FROM reactions r
        JOIN messages m2 ON r.channel_id = m2.channel_id AND r.message_ts = m2.ts
        LEFT JOIN users u ON r.message_user_id = u.user_id
        WHERE r.message_user_id IS NOT NULL {ch_filter_rxn}
          AND strftime('%Y-%m', m2.posted_at) IN ({','.join('?' for _ in months)})
        GROUP BY r.message_user_id
    """
    rxn_df = pd.read_sql_query(rxn_query, conn, params=rxn_params + list(months))

    if msg_df.empty and rxn_df.empty:
        return pd.DataFrame()
    if msg_df.empty:
        return rxn_df
    if rxn_df.empty:
        return msg_df
    df = pd.merge(msg_df, rxn_df.drop(columns=["display_name"]), on="user_id", how="outer")
    df["display_name"] = df["display_name"].fillna(df["user_id"])
    return df


def main():
    conn = init_db()
    today = date.today()
    channel_ids = get_non_log_channel_ids(conn)

    # ── 30-day comparison ──
    curr_end = today
    curr_start = today - timedelta(days=30)
    prev_end = curr_start
    prev_start = curr_start - timedelta(days=30)

    df_prev = get_period_user_stats(conn, prev_start.isoformat(), prev_end.isoformat(), "prev", channel_ids)
    df_curr = get_period_user_stats(conn, curr_start.isoformat(), curr_end.isoformat(), "curr", channel_ids)

    if df_prev.empty and df_curr.empty:
        df30 = pd.DataFrame(columns=["user_id", "display_name", "msg_prev", "msg_curr", "rxn_prev", "rxn_curr"])
    elif df_prev.empty:
        df30 = df_curr
    elif df_curr.empty:
        df30 = df_prev
    else:
        df30 = pd.merge(df_prev, df_curr.drop(columns=["display_name"]), on="user_id", how="outer")
        df30["display_name"] = df30["display_name"].fillna(df30["user_id"])

    df30 = filter_df(df30, conn, ["msg_prev", "msg_curr", "rxn_prev", "rxn_curr"])
    df30 = df30.sort_values("msg_curr", ascending=False)

    alerts30 = collect_alerts(df30, "msg_curr", "msg_prev", "rxn_curr", "rxn_prev")
    tab30_stats = {
        "total_users": len(df30),
        "current_msg": int(df30["msg_curr"].sum()),
        "prev_msg": int(df30["msg_prev"].sum()),
        "current_rxn": int(df30["rxn_curr"].sum()),
        "prev_rxn": int(df30["rxn_prev"].sum()),
        "alert_count": len(alerts30),
    }

    # ── 3-month comparison ──
    cm = today.replace(day=1)
    pm = (cm - timedelta(days=1)).replace(day=1)
    ppm = (pm - timedelta(days=1)).replace(day=1)
    months = [ppm.strftime("%Y-%m"), pm.strftime("%Y-%m"), cm.strftime("%Y-%m")]
    month_labels = [f"{int(m.split('-')[1])}月" for m in months]

    df3m = get_monthly_user_stats(conn, months, channel_ids)
    cols3m = [f"msg_{m}" for m in months] + [f"rxn_{m}" for m in months]
    if not df3m.empty:
        df3m = filter_df(df3m, conn, cols3m)
        df3m = df3m.sort_values(f"msg_{months[-1]}", ascending=False)
    else:
        df3m = pd.DataFrame(columns=["user_id", "display_name"] + cols3m)

    alerts3m = collect_alerts(df3m, f"msg_{months[-1]}", f"msg_{months[-2]}",
                              f"rxn_{months[-1]}", f"rxn_{months[-2]}")
    tab3m_stats = {
        "total_users": len(df3m),
        "current_msg": int(df3m[f"msg_{months[-1]}"].sum()),
        "prev_msg": int(df3m[f"msg_{months[-2]}"].sum()),
        "m0_msg": int(df3m[f"msg_{months[0]}"].sum()),
        "current_rxn": int(df3m[f"rxn_{months[-1]}"].sum()),
        "prev_rxn": int(df3m[f"rxn_{months[-2]}"].sum()),
        "m0_rxn": int(df3m[f"rxn_{months[0]}"].sum()),
        "alert_count": len(alerts3m),
    }

    # ── Generate HTML ──
    html = generate_html(
        tab30_rows=build_30day_rows(df30),
        tab30_alert=build_alert_summary(alerts30),
        tab30_stats=tab30_stats,
        prev_label=f"{prev_start.isoformat()} 〜 {prev_end.isoformat()}",
        curr_label=f"{curr_start.isoformat()} 〜 {curr_end.isoformat()}",
        tab3m_rows=build_3month_rows(df3m, months),
        tab3m_alert=build_alert_summary(alerts3m),
        tab3m_stats=tab3m_stats,
        month_labels=month_labels,
        months=months,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    conn.close()
    print(f"Dashboard written to {out_path}")
    print(f"  30-day: {tab30_stats['total_users']} users, {tab30_stats['alert_count']} alerts")
    print(f"  3-month: {tab3m_stats['total_users']} users, {tab3m_stats['alert_count']} alerts")


if __name__ == "__main__":
    main()
