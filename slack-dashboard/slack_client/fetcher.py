from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .rate_limiter import rate_limited

logger = logging.getLogger(__name__)


class SlackFetcher:
    def __init__(self, client: WebClient):
        self.client = client

    # ── Channel list ─────────────────────────────────────────────

    @rate_limited(tier=2)
    def _conversations_list(self, cursor: str | None = None) -> dict:
        return self.client.conversations_list(
            types="public_channel",
            limit=200,
            cursor=cursor or "",
        )

    def fetch_channels(self, only_member: bool = False) -> list[dict]:
        channels = []
        cursor = None
        while True:
            resp = self._conversations_list(cursor=cursor)
            for ch in resp["channels"]:
                if only_member and not ch.get("is_member", False):
                    continue
                channels.append(
                    {
                        "channel_id": ch["id"],
                        "channel_name": ch["name"],
                        "is_archived": int(ch.get("is_archived", False)),
                        "is_member": ch.get("is_member", False),
                    }
                )
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        logger.info("Fetched %d channels", len(channels))
        return channels

    # ── User list ────────────────────────────────────────────────

    @rate_limited(tier=2)
    def _users_list(self, cursor: str | None = None) -> dict:
        return self.client.users_list(limit=200, cursor=cursor or "")

    def fetch_users(self) -> list[dict]:
        users = []
        cursor = None
        while True:
            resp = self._users_list(cursor=cursor)
            for u in resp["members"]:
                profile = u.get("profile", {})
                users.append(
                    {
                        "user_id": u["id"],
                        "display_name": profile.get("display_name") or u.get("name", ""),
                        "real_name": profile.get("real_name", ""),
                        "is_bot": int(u.get("is_bot", False)),
                    }
                )
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        logger.info("Fetched %d users", len(users))
        return users

    # ── Channel history ──────────────────────────────────────────

    @rate_limited(tier=3)
    def _conversations_history(
        self, channel_id: str, oldest: str = "0", cursor: str | None = None
    ) -> dict:
        return self.client.conversations_history(
            channel=channel_id,
            oldest=oldest,
            limit=200,
            cursor=cursor or "",
        )

    @rate_limited(tier=3)
    def _conversations_join(self, channel_id: str) -> dict:
        return self.client.conversations_join(channel=channel_id)

    def fetch_messages(self, channel_id: str, oldest: str = "0") -> list[dict]:
        messages = []
        cursor = None
        while True:
            try:
                resp = self._conversations_history(
                    channel_id=channel_id, oldest=oldest, cursor=cursor
                )
            except SlackApiError as e:
                if e.response.get("error") == "not_in_channel":
                    logger.info("Joining channel %s", channel_id)
                    try:
                        self._conversations_join(channel_id)
                    except SlackApiError as join_err:
                        logger.warning("Failed to join %s: %s", channel_id, join_err.response.get("error"))
                        return []
                    time.sleep(2)
                    resp = self._conversations_history(
                        channel_id=channel_id, oldest=oldest, cursor=cursor
                    )
                else:
                    raise
            for msg in resp.get("messages", []):
                if msg.get("subtype") in ("channel_join", "channel_leave"):
                    continue
                messages.append(self._parse_message(channel_id, msg, is_reply=False))
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return messages

    # ── Thread replies ───────────────────────────────────────────

    @rate_limited(tier=3)
    def _conversations_replies(
        self, channel_id: str, thread_ts: str, cursor: str | None = None
    ) -> dict:
        return self.client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=200,
            cursor=cursor or "",
        )

    def fetch_replies(self, channel_id: str, thread_ts: str) -> list[dict]:
        replies = []
        cursor = None
        while True:
            resp = self._conversations_replies(
                channel_id=channel_id, thread_ts=thread_ts, cursor=cursor
            )
            for msg in resp.get("messages", []):
                # Skip the parent message itself
                if msg["ts"] == thread_ts:
                    continue
                replies.append(self._parse_message(channel_id, msg, is_reply=True))
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return replies

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _parse_message(channel_id: str, msg: dict, is_reply: bool) -> dict:
        ts = msg["ts"]
        posted_at = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
        reactions_list = []
        for r in msg.get("reactions", []):
            for uid in r.get("users", []):
                reactions_list.append(
                    {
                        "channel_id": channel_id,
                        "message_ts": ts,
                        "message_user_id": msg.get("user"),
                        "reaction": r["name"],
                        "reactor_user_id": uid,
                    }
                )
        return {
            "ts": ts,
            "channel_id": channel_id,
            "user_id": msg.get("user"),
            "text": msg.get("text", ""),
            "thread_ts": msg.get("thread_ts") if not is_reply else msg.get("thread_ts"),
            "reply_count": msg.get("reply_count", 0),
            "is_reply": int(is_reply),
            "posted_at": posted_at,
            "reactions": reactions_list,
        }
