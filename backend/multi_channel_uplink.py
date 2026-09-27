"""
OpenClaw-Inspired Multi-Channel Remote Uplink for MaxIM.
Repository Reference: https://github.com/openclaw/openclaw

Functional Core:
1. "Trusted Gateway, Channel Plugins, Untrusted Execution" Architecture:
   - Central control plane standardizing messages across Discord, Slack, Telegram, and generic Webhooks.
   - Canonical InboundMessage and OutboundMessage abstractions.
2. Channel Adapters:
   - DiscordAdapter: Webhooks & Discord REST API v10 with 2000-character chunking.
   - SlackAdapter: Incoming Webhooks & Slack chat.postMessage API with 4000-character chunking.
   - TelegramAdapter: Async bot API with Markdown parsing and chunking.
   - WebhookAdapter: Inbound & outbound custom JSON webhooks for Home Assistant, Apple Shortcuts, and Termux.
3. Durable Persistence:
   - channel_uplink_configs: SQLite WAL configuration for tokens, URLs, and allowed sender IDs.
   - channel_inbox_logs: Universal unified inbox ledger tracking incoming commands and outgoing receipts.
4. Autonomous Broadcast & Dispatch:
   - Single-channel targeted dispatch or multi-channel simultaneous broadcast.
"""

import os
import json
import sqlite3
import logging
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
from pydantic import BaseModel, Field
import httpx

from config import config

logger = logging.getLogger("maxim.multi_channel_uplink")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOCAL = "local"


class InboundMessage(BaseModel):
    """Canonical normalized incoming message from any external channel."""
    channel: ChannelType
    sender_id: str
    sender_name: str = "Unknown"
    content: str
    session_id: Optional[str] = None
    reply_target: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utc_now_iso)


class OutboundMessage(BaseModel):
    """Canonical outbound message payload dispatched to an external channel."""
    channel: ChannelType
    target: str  # chat_id, webhook_url, or channel_id
    text: str
    title: Optional[str] = None
    status: str = "pending"  # pending, sent, failed
    timestamp: str = Field(default_factory=utc_now_iso)


class ChannelConfig(BaseModel):
    """Configuration record for an active communication channel."""
    channel: str
    enabled: bool = False
    bot_token: Optional[str] = None
    webhook_url: Optional[str] = None
    allowed_ids: List[str] = Field(default_factory=list)
    config_json: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=utc_now_iso)


# =============================================================================
# 1. CHANNEL ADAPTERS
# =============================================================================

class DiscordAdapter:
    """Dispatches messages to Discord via Webhooks or Bot REST API."""

    @staticmethod
    async def send_message(
        target: str,
        text: str,
        bot_token: Optional[str] = None,
        title: Optional[str] = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        if not target:
            return {"status": "failed", "error": "Missing Discord target (webhook URL or channel ID)"}

        # Discord message limit is 2000 chars
        chunks = [text[i:i + 1950] for i in range(0, len(text), 1950)] or [""]

        # Check if target is a Webhook URL
        is_webhook = target.startswith("http://") or target.startswith("https://")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                for idx, chunk in enumerate(chunks):
                    prefix = f"**{title}**\n" if (title and idx == 0) else ""
                    formatted = f"{prefix}{chunk}"

                    if is_webhook:
                        payload = {"content": formatted, "username": "MaxIM AI"}
                        res = await client.post(target, json=payload)
                    else:
                        token = bot_token or config.get_nested("discord.bot_token", None)
                        if not token:
                            return {"status": "failed", "error": "Bot token required for Discord channel ID target"}
                        headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
                        api_url = f"https://discord.com/api/v10/channels/{target}/messages"
                        res = await client.post(api_url, headers=headers, json={"content": formatted})

                    if res.status_code not in [200, 201, 204]:
                        return {"status": "failed", "status_code": res.status_code, "error": res.text}

                return {"status": "sent", "channel": "discord", "chunks": len(chunks)}
            except Exception as e:
                logger.error(f"Discord dispatch error: {e}")
                return {"status": "failed", "error": str(e)}


class SlackAdapter:
    """Dispatches messages to Slack via Incoming Webhooks or Web API."""

    @staticmethod
    async def send_message(
        target: str,
        text: str,
        bot_token: Optional[str] = None,
        title: Optional[str] = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        if not target:
            return {"status": "failed", "error": "Missing Slack target (webhook URL or channel ID)"}

        # Slack message limit is ~4000 chars per block
        chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or [""]
        is_webhook = target.startswith("http://") or target.startswith("https://")

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                for idx, chunk in enumerate(chunks):
                    prefix = f"*{title}*\n" if (title and idx == 0) else ""
                    formatted = f"{prefix}{chunk}"

                    if is_webhook:
                        payload = {"text": formatted, "username": "MaxIM AI"}
                        res = await client.post(target, json=payload)
                    else:
                        token = bot_token or config.get_nested("slack.bot_token", None)
                        if not token:
                            return {"status": "failed", "error": "Bot token required for Slack channel ID target"}
                        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                        api_url = "https://slack.com/api/chat.postMessage"
                        res = await client.post(api_url, headers=headers, json={"channel": target, "text": formatted})

                    if res.status_code != 200:
                        return {"status": "failed", "status_code": res.status_code, "error": res.text}

                return {"status": "sent", "channel": "slack", "chunks": len(chunks)}
            except Exception as e:
                logger.error(f"Slack dispatch error: {e}")
                return {"status": "failed", "error": str(e)}


class TelegramAdapter:
    """Dispatches messages to Telegram via Bot API."""

    @staticmethod
    async def send_message(
        target: str,
        text: str,
        bot_token: Optional[str] = None,
        title: Optional[str] = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        token = bot_token or config.telegram_bot_token
        if not token:
            return {"status": "failed", "error": "Telegram bot token not configured"}

        # Telegram message limit is 4096 chars
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or [""]
        base_url = f"https://api.telegram.org/bot{token}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                for idx, chunk in enumerate(chunks):
                    prefix = f"*{title}*\n" if (title and idx == 0) else ""
                    formatted = f"{prefix}{chunk}"
                    payload = {"chat_id": target, "text": formatted, "parse_mode": "Markdown"}

                    res = await client.post(f"{base_url}/sendMessage", json=payload)
                    # If Markdown fails, retry with plain text
                    if res.status_code != 200:
                        payload.pop("parse_mode", None)
                        res = await client.post(f"{base_url}/sendMessage", json=payload)

                    if res.status_code != 200:
                        return {"status": "failed", "status_code": res.status_code, "error": res.text}

                return {"status": "sent", "channel": "telegram", "chunks": len(chunks)}
            except Exception as e:
                logger.error(f"Telegram dispatch error: {e}")
                return {"status": "failed", "error": str(e)}


class WebhookAdapter:
    """Dispatches outbound HTTP POST webhooks to custom services."""

    @staticmethod
    async def send_message(
        target_url: str,
        text: str,
        title: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        if not target_url or not (target_url.startswith("http://") or target_url.startswith("https://")):
            return {"status": "failed", "error": "Invalid or missing webhook URL"}

        payload = {
            "source": "MaxIM_v2_Uplink",
            "title": title or "MaxIM AI Notification",
            "content": text,
            "timestamp": utc_now_iso(),
            **(extra_data or {})
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                res = await client.post(target_url, json=payload)
                if res.status_code in [200, 201, 202, 204]:
                    return {"status": "sent", "channel": "webhook", "status_code": res.status_code}
                return {"status": "failed", "status_code": res.status_code, "error": res.text}
            except Exception as e:
                logger.error(f"Webhook dispatch error: {e}")
                return {"status": "failed", "error": str(e)}


# =============================================================================
# 2. MULTI-CHANNEL UPLINK MANAGER
# =============================================================================

class MultiChannelUplinkManager:
    """Central gateway and router for all external communication channels."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes SQLite WAL tables for channel configs and unified inbox."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_uplink_configs (
                    channel TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    bot_token TEXT,
                    webhook_url TEXT,
                    allowed_ids TEXT,
                    config_json TEXT,
                    updated_at TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_inbox_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    direction TEXT NOT NULL,  -- inbound, outbound
                    sender_id TEXT NOT NULL,
                    sender_name TEXT,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'delivered',
                    timestamp TEXT NOT NULL
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inbox_channel ON channel_inbox_logs(channel);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inbox_timestamp ON channel_inbox_logs(timestamp);")
            conn.commit()

        # Seed Telegram config from config.py if present
        if config.telegram_bot_token:
            self.configure_channel(
                channel=ChannelType.TELEGRAM.value,
                enabled=True,
                bot_token=config.telegram_bot_token,
                allowed_ids=[str(config.telegram_chat_id)] if config.telegram_chat_id else [],
            )

    # =========================================================================
    # CONFIGURATION & REPOSITORY METHODS
    # =========================================================================

    def configure_channel(
        self,
        channel: str,
        enabled: bool = True,
        bot_token: Optional[str] = None,
        webhook_url: Optional[str] = None,
        allowed_ids: Optional[List[str]] = None,
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> ChannelConfig:
        """Stores or updates credentials and status for a communication channel."""
        clean_ch = channel.lower().strip()
        now = utc_now_iso()
        ids_json = json.dumps(allowed_ids or [])
        cfg_json = json.dumps(extra_config or {})

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO channel_uplink_configs (
                    channel, enabled, bot_token, webhook_url, allowed_ids, config_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(channel) DO UPDATE SET
                    enabled = excluded.enabled,
                    bot_token = COALESCE(excluded.bot_token, channel_uplink_configs.bot_token),
                    webhook_url = COALESCE(excluded.webhook_url, channel_uplink_configs.webhook_url),
                    allowed_ids = excluded.allowed_ids,
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at
            """, (clean_ch, 1 if enabled else 0, bot_token, webhook_url, ids_json, cfg_json, now))
            conn.commit()

        return self.get_channel_config(clean_ch) or ChannelConfig(
            channel=clean_ch,
            enabled=enabled,
            bot_token=bot_token,
            webhook_url=webhook_url,
            allowed_ids=allowed_ids or [],
            config_json=extra_config or {},
            updated_at=now,
        )

    def get_channel_config(self, channel: str) -> Optional[ChannelConfig]:
        """Retrieves configuration for a specific channel."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channel_uplink_configs WHERE channel = ?", (channel.lower().strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return ChannelConfig(
                channel=row["channel"],
                enabled=bool(row["enabled"]),
                bot_token=row["bot_token"],
                webhook_url=row["webhook_url"],
                allowed_ids=json.loads(row["allowed_ids"] or "[]"),
                config_json=json.loads(row["config_json"] or "{}"),
                updated_at=row["updated_at"],
            )

    def get_all_channel_configs(self) -> List[ChannelConfig]:
        """Returns all configured channel profiles."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channel_uplink_configs ORDER BY channel ASC")
            rows = cursor.fetchall()
            return [
                ChannelConfig(
                    channel=r["channel"],
                    enabled=bool(r["enabled"]),
                    bot_token=r["bot_token"],
                    webhook_url=r["webhook_url"],
                    allowed_ids=json.loads(r["allowed_ids"] or "[]"),
                    config_json=json.loads(r["config_json"] or "{}"),
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def log_message(
        self,
        channel: str,
        direction: str,
        sender_id: str,
        sender_name: str,
        content: str,
        status: str = "delivered",
    ) -> int:
        """Records an incoming or outgoing message in the unified inbox ledger."""
        now = utc_now_iso()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO channel_inbox_logs (
                    channel, direction, sender_id, sender_name, content, status, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (channel.lower(), direction, str(sender_id), sender_name, content, status, now))
            conn.commit()
            return cursor.lastrowid

    def get_inbox(self, limit: int = 50, channel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent unified inbox logs across channels."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if channel:
                cursor.execute("""
                    SELECT * FROM channel_inbox_logs
                    WHERE channel = ?
                    ORDER BY id DESC LIMIT ?
                """, (channel.lower(), limit))
            else:
                cursor.execute("""
                    SELECT * FROM channel_inbox_logs
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # =========================================================================
    # INBOUND PROCESSING & REAC T ENGINE ROUTING
    # =========================================================================

    async def process_inbound(self, msg: InboundMessage, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Receives an inbound message from any channel, verifies sender permission,
        logs the message, and executes an agent turn via MaxIMAgentEngine.
        """
        ch_name = msg.channel.value if isinstance(msg.channel, ChannelType) else str(msg.channel).lower()
        cfg = self.get_channel_config(ch_name)

        # 1. Authorization check
        if cfg and cfg.allowed_ids and len(cfg.allowed_ids) > 0:
            if str(msg.sender_id) not in cfg.allowed_ids:
                logger.warning(f"Unauthorized sender {msg.sender_id} on channel {ch_name}")
                self.log_message(ch_name, "inbound", msg.sender_id, msg.sender_name, msg.content, status="blocked_unauthorized")
                return {
                    "status": "rejected",
                    "reason": "unauthorized_sender",
                    "channel": ch_name,
                    "sender_id": msg.sender_id,
                }

        # 2. Record in unified inbox
        self.log_message(ch_name, "inbound", msg.sender_id, msg.sender_name, msg.content, status="received")

        # 3. Derive session ID: guarantee remote prefix to enforce AgentShield Tier 4 OS lockdown
        raw_sess = session_id or msg.session_id
        if raw_sess:
            derived_session = raw_sess if (raw_sess.startswith("channel_") or raw_sess.startswith("webhook_")) else f"channel_{ch_name}_{raw_sess}"
        else:
            derived_session = f"channel_{ch_name}_{msg.sender_id}"

        # 4. Execute ReAct turn via Engine
        try:
            from engine import agent_engine
            agent_res = await agent_engine.run_turn(
                user_message=msg.content,
                session_id=derived_session,
            )
            response_text = agent_res.get("response", "")
        except Exception as e:
            logger.error(f"Error executing agent turn for {ch_name} message: {e}")
            response_text = f"MaxIM Error processing request: {e}"

        # 5. Log outbound response
        self.log_message(ch_name, "outbound", "maxim_ai", "MaxIM Core", response_text, status="dispatched")

        # 6. Auto-reply if a reply_target is supplied
        reply_res = None
        if msg.reply_target:
            reply_res = await self.send_remote(
                channel=ch_name,
                target=msg.reply_target,
                text=response_text,
            )

        return {
            "status": "processed",
            "channel": ch_name,
            "session_id": derived_session,
            "response": response_text,
            "reply_dispatched": reply_res,
        }

    # =========================================================================
    # OUTBOUND DISPATCH & BROADCAST
    # =========================================================================

    async def send_remote(
        self,
        channel: Union[ChannelType, str],
        target: str,
        text: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatches an outbound notification or response through the designated channel adapter."""
        ch_name = channel.value if isinstance(channel, ChannelType) else str(channel).lower().strip()
        cfg = self.get_channel_config(ch_name)
        token = cfg.bot_token if cfg else None

        if ch_name == ChannelType.DISCORD.value:
            res = await DiscordAdapter.send_message(target=target, text=text, bot_token=token, title=title)
        elif ch_name == ChannelType.SLACK.value:
            res = await SlackAdapter.send_message(target=target, text=text, bot_token=token, title=title)
        elif ch_name == ChannelType.TELEGRAM.value:
            res = await TelegramAdapter.send_message(target=target, text=text, bot_token=token, title=title)
        elif ch_name == ChannelType.WEBHOOK.value:
            res = await WebhookAdapter.send_message(target_url=target, text=text, title=title)
        else:
            return {"status": "failed", "error": f"Unsupported channel type: {ch_name}"}

        # Log outbound dispatch
        self.log_message(
            channel=ch_name,
            direction="outbound",
            sender_id="maxim_ai",
            sender_name="MaxIM Core",
            content=text[:500],
            status="delivered" if res.get("status") == "sent" else "failed",
        )
        return res

    async def broadcast(
        self,
        text: str,
        title: Optional[str] = None,
        channels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Broadcasts an alert, shift summary, or briefing across all enabled channels."""
        all_cfgs = self.get_all_channel_configs()
        target_cfgs = [
            c for c in all_cfgs
            if c.enabled and (not channels or c.channel in channels)
        ]

        results: Dict[str, Any] = {}
        for c in target_cfgs:
            # Determine target from config
            target = c.webhook_url or (c.allowed_ids[0] if c.allowed_ids else None)
            if not target:
                results[c.channel] = {"status": "skipped", "reason": "No target webhook or chat_id configured"}
                continue

            res = await self.send_remote(channel=c.channel, target=target, text=text, title=title)
            results[c.channel] = res

        return {
            "status": "broadcast_complete",
            "channels_contacted": len(results),
            "results": results,
        }

    def get_channel_status(self) -> Dict[str, Any]:
        """Returns overall health, configuration metrics, and traffic statistics for all channels."""
        configs = self.get_all_channel_configs()
        inbox = self.get_inbox(limit=100)

        inbound_count = sum(1 for m in inbox if m["direction"] == "inbound")
        outbound_count = sum(1 for m in inbox if m["direction"] == "outbound")

        channels_data = {}
        for c in configs:
            ch_inbound = sum(1 for m in inbox if m["channel"] == c.channel and m["direction"] == "inbound")
            ch_outbound = sum(1 for m in inbox if m["channel"] == c.channel and m["direction"] == "outbound")
            channels_data[c.channel] = {
                "enabled": c.enabled,
                "has_token": bool(c.bot_token),
                "has_webhook": bool(c.webhook_url),
                "allowed_ids_count": len(c.allowed_ids),
                "inbound_messages": ch_inbound,
                "outbound_messages": ch_outbound,
                "updated_at": c.updated_at,
            }

        return {
            "status": "active",
            "total_channels_configured": len(configs),
            "total_traffic": {
                "inbound": inbound_count,
                "outbound": outbound_count,
            },
            "channels": channels_data,
        }


# Singleton instance
multi_channel_uplink = MultiChannelUplinkManager()
