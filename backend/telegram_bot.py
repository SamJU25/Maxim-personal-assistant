"""
MaxIM Remote Uplink - Telegram Bot Daemon
Lightweight, pure async implementation using httpx.
Bridges mobile commands, screen perception, and vault memory to the user's phone.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

from config import config
from memory import memory_store
from engine import AutonomousReActEngine
from dream_engine import BitterbotDreamEngine
from tools.screen_tool import screen_tool

logger = logging.getLogger("maxim.telegram")

class TelegramRemoteUplink:
    def __init__(self, token: Optional[str] = None, allowed_chat_id: Optional[str] = None):
        self.token = token or config.telegram_bot_token
        self.allowed_chat_id = allowed_chat_id or config.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self.is_running = False
        self._polling_task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None
        self.engine = AutonomousReActEngine(memory_store=memory_store)
        self.dream_engine = BitterbotDreamEngine(memory_store=memory_store)

    @property
    def is_configured(self) -> bool:
        return bool(self.token and len(self.token.strip()) > 5)

    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Verify bot credentials with Telegram API."""
        if not self.is_configured:
            return None
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(f"{self.base_url}/getMe")
                if res.status_code == 200:
                    return res.json().get("result")
                logger.warning(f"Telegram getMe failed with status {res.status_code}: {res.text}")
            except Exception as e:
                logger.error(f"Error checking Telegram bot credentials: {e}")
        return None

    async def send_message(self, chat_id: str | int, text: str) -> bool:
        """Send text message, chunking if exceeds 4000 characters."""
        if not self.is_configured:
            return False
        
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
        async with httpx.AsyncClient(timeout=15.0) as client:
            for chunk in chunks:
                try:
                    payload = {
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": "Markdown"
                    }
                    res = await client.post(f"{self.base_url}/sendMessage", json=payload)
                    # If Markdown parsing fails, retry with plain text
                    if res.status_code != 200:
                        payload.pop("parse_mode", None)
                        await client.post(f"{self.base_url}/sendMessage", json=payload)
                except Exception as e:
                    logger.error(f"Failed to send Telegram message: {e}")
                    return False
        return True

    async def send_photo(self, chat_id: str | int, image_bytes: bytes, caption: str = "") -> bool:
        """Send photo with caption to chat."""
        if not self.is_configured:
            return False
        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                files = {"photo": ("screen.jpg", image_bytes, "image/jpeg")}
                data = {"chat_id": str(chat_id), "caption": caption[:1024]}
                res = await client.post(f"{self.base_url}/sendPhoto", data=data, files=files)
                return res.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")
                return False

    async def handle_update(self, update: Dict[str, Any]):
        """Processes a single incoming update/message."""
        msg = update.get("message")
        if not msg:
            return

        chat = msg.get("chat", {})
        chat_id = str(chat.get("id", ""))
        user_text = (msg.get("text") or "").strip()

        # Authorization check if allowed_chat_id is specified
        if self.allowed_chat_id and chat_id != str(self.allowed_chat_id):
            logger.warning(f"Unauthorized Telegram access attempt from chat_id {chat_id}")
            await self.send_message(
                chat_id,
                "⛔ *Access Denied.* I don't answer to random humans. Your chat ID is not authorized."
            )
            return

        if not user_text:
            return

        # Slash Commands
        if user_text == "/start" or user_text == "/help":
            help_msg = (
                "🤖 *MaxIM Autonomous Remote Uplink*\n"
                "I am MaxIM. Grounded in your TELOS, cynical about your procrastination.\n\n"
                "*Available Commands:*\n"
                "• `/status` - Active desktop window, screen state, and provider\n"
                "• `/screen` - Current screenshot of desktop\n"
                "• `/dream` - Trigger an offline reflection cycle\n"
                "• `/morning` - Morning wake-up brief\n"
                "• `/note <text>` - Append note to Obsidian vault\n"
                "• Any plain text - Directly queries the ReAct cognitive loop"
            )
            await self.send_message(chat_id, help_msg)
            return

        if user_text == "/status":
            screen_info = screen_tool.inspect_screen()
            win_title = screen_info.get("active_window", "Desktop")
            status_msg = (
                f"🖥️ *Desktop Status*\n"
                f"• Active Window: `{win_title}`\n"
                f"• Screen Res: `{screen_info.get('resolution', 'Unknown')}`\n"
                f"• Active Provider: `{config.active_provider}`\n"
                f"• Vault: `{config.vault_dir}`"
            )
            await self.send_message(chat_id, status_msg)
            return

        if user_text == "/screen":
            img = screen_tool.capture_screen()
            import io
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            buf.seek(0)
            info = screen_tool.inspect_screen()
            caption = f"Active: {info.get('active_window', 'Desktop')}"
            await self.send_photo(chat_id, buf.getvalue(), caption=caption)
            return

        if user_text == "/dream":
            await self.send_message(chat_id, "🌙 Initiating Bitterbot dream cycle...")
            thought = await self.dream_engine.run_dream_cycle(session_id=f"telegram_{chat_id}")
            await self.send_message(chat_id, f"💭 *Dream Synthesis Complete:*\n\n{thought}")
            return

        if user_text == "/morning":
            greeting = await self.dream_engine.generate_morning_greeting()
            await self.send_message(chat_id, f"☀️ *Morning Wake-Up:*\n\n{greeting}")
            return

        if user_text.startswith("/note "):
            note_content = user_text[6:].strip()
            from tools.vault_tool import vault_synapse
            result = vault_synapse.write_note(
                "01 - Memory/Fleeting Notes.md",
                f"\n\n- [{note_content}] (via Telegram Remote Uplink)",
                append=True
            )
            await self.send_message(chat_id, f"📝 Note recorded to Obsidian vault:\n`{result}`")
            return

        # Normal text message: run autonomous ReAct engine
        await self.send_message(chat_id, "⏳ *MaxIM is thinking...*")
        try:
            response = await self.engine.run(
                prompt=user_text,
                session_id=f"telegram_{chat_id}"
            )
            await self.send_message(chat_id, response)
        except Exception as e:
            logger.error(f"Error in engine run via Telegram: {e}")
            await self.send_message(chat_id, f"💥 Error processing command: `{str(e)}`")

    async def _polling_loop(self):
        """Long polling loop for Telegram updates."""
        offset = 0
        logger.info("Starting Telegram Remote Uplink polling loop...")
        async with httpx.AsyncClient(timeout=35.0) as client:
            while self.is_running:
                try:
                    params = {"offset": offset, "timeout": 20}
                    res = await client.get(f"{self.base_url}/getUpdates", params=params)
                    if res.status_code == 200:
                        data = res.json()
                        updates = data.get("result", [])
                        for update in updates:
                            update_id = update.get("update_id", 0)
                            offset = max(offset, update_id + 1)
                            await self.handle_update(update)
                    else:
                        await asyncio.sleep(5)
                except httpx.RequestError as e:
                    logger.debug(f"Telegram polling timeout or connection issue: {e}")
                    await asyncio.sleep(3)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in Telegram polling: {e}")
                    await asyncio.sleep(5)

    def start(self):
        """Start polling task if configured."""
        if not self.is_configured:
            logger.info("Telegram Bot Token not configured. Remote Uplink idling.")
            return
        if self.is_running:
            return
        self.is_running = True
        self._polling_task = asyncio.create_task(self._polling_loop())

    async def stop(self):
        """Stop polling task."""
        self.is_running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None
        logger.info("Telegram Remote Uplink stopped.")

# Global singleton
telegram_uplink = TelegramRemoteUplink()
