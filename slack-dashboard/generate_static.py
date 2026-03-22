#!/usr/bin/env python3
"""Generate a static HTML dashboard from the SQLite database for GitHub Pages."""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db.schema import init_db
from db.queries import (
    get_message_counts,
    get_reaction_counts,
    get_thread_reply_counts,
    get_hourly_activity,
    get_channel_breakdown,
    get_trend_data,
    get_all_channels,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs")


def build_charts(conn, start: str, end: str, period: str = "weekly", top_n: int = 20, channel_ids: list = None):
    """Build all Plotly figures and return as list of (section_title, fig_html) tuples."""
    sections = []

    # --- Trend ---
    trend_df = get_trend_data(conn, start, end, channel_ids=channel_ids, period=period)
    if not trend_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend_df["period"], y=trend_df["message_count"],
                                 name="メッセージ数", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=trend_df["period"], y=trend_df["active_users"],
                                 name="アクティブユーザー数", mode="lines+markers", yaxis="y2"))
        fig.update_layout(
            title="トレンド推移",
            xaxis_title="期間",
            yaxis=dict(title="メッセージ数"),
            yaxis2=dict(title="アクティブユーザー数", overlaying="y", side="right"),
            height=420, template="plotly_white",
        )
        sections.append(("トレンド推移", fig.to_html(full_html=False, include_plotlyjs=False)))

    # --- Message counts ---
    msg_df = get_message_counts(conn, start, end, channel_ids=channel_ids, period=period)
    if not msg_df.empty:
        msg_total = (msg_df.groupby(["user_id", "display_name"])["message_count"]
                     .sum().reset_index().sort_values("message_count", ascending=False))
        fig = px.bar(msg_total.head(top_n), x="message_count", y="display_name",
                     orientation="h", title="投稿数 Top",
                     labels={"display_name": "ユーザー", "message_count": "件数"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          height=max(400, top_n * 25), template="plotly_white")
        sections.append(("投稿数ランキング", fig.to_html(full_html=False, include_plotlyjs=False)))

        # Table
        table_html = _df_to_table(msg_total.head(top_n), ["display_name", "message_count"],
                                  ["ユーザー", "投稿数"])
        sections.append(("投稿数ランキング（表）", table_html))

    # --- Reaction counts ---
    rxn_df = get_reaction_counts(conn, start, end, channel_ids=channel_ids, period=period)
    if not rxn_df.empty:
        rxn_total = (rxn_df.groupby(["user_id", "display_name"])[["reactions_received", "reactions_given"]]
                     .sum().reset_index())

        # Received
        rxn_recv = rxn_total.sort_values("reactions_received", ascending=False)
        fig = px.bar(rxn_recv.head(top_n), x="reactions_received", y="display_name",
                     orientation="h", title="リアクション受信数 Top",
                     labels={"display_name": "ユーザー", "reactions_received": "件数"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          height=max(400, top_n * 25), template="plotly_white")
        sections.append(("リアクション受信数", fig.to_html(full_html=False, include_plotlyjs=False)))

        # Given
        rxn_given = rxn_total.sort_values("reactions_given", ascending=False)
        fig = px.bar(rxn_given.head(top_n), x="reactions_given", y="display_name",
                     orientation="h", title="リアクション送信数 Top",
                     labels={"display_name": "ユーザー", "reactions_given": "件数"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          height=max(400, top_n * 25), template="plotly_white")
        sections.append(("リアクション送信数", fig.to_html(full_html=False, include_plotlyjs=False)))

        # Table
        table_html = _df_to_table(rxn_recv.head(top_n),
                                  ["display_name", "reactions_received", "reactions_given"],
                                  ["ユーザー", "受信数", "送信数"])
        sections.append(("リアクションランキング（表）", table_html))

    # --- Thread replies ---
    reply_df = get_thread_reply_counts(conn, start, end, channel_ids=channel_ids, period=period)
    if not reply_df.empty:
        reply_total = (reply_df.groupby(["user_id", "display_name"])["reply_count"]
                       .sum().reset_index().sort_values("reply_count", ascending=False))
        fig = px.bar(reply_total.head(top_n), x="reply_count", y="display_name",
                     orientation="h", title="スレッド返信数 Top",
                     labels={"display_name": "ユーザー", "reply_count": "件数"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          height=max(400, top_n * 25), template="plotly_white")
        sections.append(("スレッド返信数", fig.to_html(full_html=False, include_plotlyjs=False)))

    # --- Heatmap ---
    activity_df = get_hourly_activity(conn, start, end, channel_ids=channel_ids, tz_offset_hours=9)
    if not activity_df.empty:
        dow_labels = ["日", "月", "火", "水", "木", "金", "土"]
        pivot = activity_df.pivot_table(index="dow", columns="hour", values="count", fill_value=0)
        pivot = pivot.reindex(index=range(7), columns=range(24), fill_value=0)
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"{h}:00" for h in range(24)],
            y=[dow_labels[d] for d in range(7)],
            colorscale="YlOrRd", hoverongaps=False,
        ))
        fig.update_layout(title="アクティブ時間帯ヒートマップ（JST）",
                          xaxis_title="時間", yaxis_title="曜日",
                          height=350, template="plotly_white")
        sections.append(("アクティブ時間帯", fig.to_html(full_html=False, include_plotlyjs=False)))

    # --- Channel breakdown ---
    ch_df = get_channel_breakdown(conn, start, end, channel_ids=channel_ids)
    if not ch_df.empty:
        fig = px.bar(ch_df.head(30), x="message_count", y="channel_name",
                     orientation="h", title="チャンネル別メッセージ数",
                     labels={"channel_name": "チャンネル", "message_count": "メッセージ数"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          height=max(400, len(ch_df.head(30)) * 22), template="plotly_white")
        sections.append(("チャンネル別メッセージ数", fig.to_html(full_html=False, include_plotlyjs=False)))

    return sections


def _df_to_table(df: pd.DataFrame, cols: list, headers: list) -> str:
    """Convert DataFrame to an HTML table string."""
    rows = []
    rows.append("<table><thead><tr>" +
                "".join(f"<th>{h}</th>" for h in ["#"] + headers) +
                "</tr></thead><tbody>")
    for i, (_, row) in enumerate(df[cols].iterrows(), 1):
        cells = "".join(f"<td>{row[c]}</td>" for c in cols)
        rows.append(f"<tr><td>{i}</td>{cells}</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


def generate_html(sections: list, start: str, end: str, period: str) -> str:
    period_label = "週次" if period == "weekly" else "月次"
    body_parts = []
    for title, html in sections:
        body_parts.append(f'<div class="section"><h2>{title}</h2>{html}</div>')

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Slack Activity Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    --bg: #f8f9fa; --card-bg: #fff; --text: #212529;
    --border: #dee2e6; --accent: #4361ee;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); padding: 0;
  }}
  header {{
    background: linear-gradient(135deg, #4361ee, #3a0ca3);
    color: #fff; padding: 2rem 2rem 1.5rem; margin-bottom: 1.5rem;
  }}
  header h1 {{ font-size: 1.8rem; margin-bottom: 0.3rem; }}
  header p {{ opacity: 0.85; font-size: 0.95rem; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem 3rem; }}
  .section {{
    background: var(--card-bg); border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  .section h2 {{
    font-size: 1.15rem; margin-bottom: 1rem;
    padding-bottom: 0.5rem; border-bottom: 2px solid var(--accent);
    color: var(--accent);
  }}
  table {{
    width: 100%; border-collapse: collapse; font-size: 0.9rem;
  }}
  th, td {{
    padding: 0.6rem 1rem; text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{ background: #f1f3f5; font-weight: 600; position: sticky; top: 0; }}
  tr:hover {{ background: #f8f9fa; }}
  td:last-child, th:last-child {{ text-align: right; }}
  footer {{
    text-align: center; padding: 2rem; color: #868e96; font-size: 0.85rem;
  }}
  @media (max-width: 768px) {{
    header {{ padding: 1.2rem; }}
    .container {{ padding: 0 0.8rem 2rem; }}
    .section {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Slack Activity Dashboard</h1>
  <p>{period_label} | {start} 〜 {end} | 生成日: {date.today().isoformat()}</p>
</header>
<div class="container">
{"".join(body_parts)}
</div>
<footer>
  Generated from Slack workspace data. Updated {date.today().isoformat()}.
</footer>
</body>
</html>"""


def get_non_log_channel_ids(conn) -> list:
    """Return channel IDs excluding aws-* log channels."""
    channels_df = get_all_channels(conn)
    filtered = channels_df[~channels_df["channel_name"].str.startswith("aws")]
    return filtered["channel_id"].tolist() if not filtered.empty else None


def main():
    conn = init_db()

    today = date.today()
    period = "weekly"
    start = (today - timedelta(days=90)).isoformat()
    end = today.isoformat()
    top_n = 20

    # Exclude aws-* log channels from the dashboard
    channel_ids = get_non_log_channel_ids(conn)

    print(f"Generating dashboard: {start} to {end} ({period})")
    sections = build_charts(conn, start, end, period, top_n, channel_ids=channel_ids)
    html = generate_html(sections, start, end, period)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    conn.close()
    print(f"Static dashboard written to {out_path}")
    print(f"  Sections: {len(sections)}")


if __name__ == "__main__":
    main()
