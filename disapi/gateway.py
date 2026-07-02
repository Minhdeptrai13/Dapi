"""
gateway.py — Discord Gateway WebSocket Handler
===============================================

Full-featured WebSocket Gateway client supporting:
  - IDENTIFY & RESUME flow
  - Automatic heartbeat with ACK tracking
  - zlib-stream compression (same as real Discord client)
  - Auto-reconnect with exponential backoff
  - Typed event system (decorator + listener registration)
  - Voice state updates
  - Presence updates
  - Request guild members
  - Lazy guild loading

WARNING:
    Self-bot gateway connections are especially risky. Discord may detect
    and terminate accounts using non-browser gateway clients. Use at your
    own risk.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import zlib
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

try:
    import websockets
    import websockets.legacy.client as ws_legacy
    from websockets.exceptions import ConnectionClosed as WSConnectionClosed
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    ws_legacy = None  # type: ignore[assignment]
    WSConnectionClosed = Exception  # type: ignore[assignment, misc]

from .constants import (
    ActivityType,
    GatewayCloseCode,
    GatewayOpcode,
    Status,
    get_gateway_properties,
    CLIENT_BUILD_NUMBER,
    GATEWAY_URL,
)
from .exceptions import ConnectionClosed, GatewayException


__all__: list[str] = ["Gateway", "GatewayConfig", "EventType"]

logger = logging.getLogger("disapi.gateway")

# Asyncio-compatible callback type
EventCallback = Union[
    Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
    Callable[[Dict[str, Any]], None],
]


# ─── EventType ────────────────────────────────────────────────────────────────

class EventType:
    """Gateway dispatch event name constants.

    Use these to register listeners without typos:

    Example:
        >>> gateway.on(EventType.MESSAGE_CREATE)(my_handler)
    """

    READY                        = "READY"
    RESUMED                      = "RESUMED"
    APPLICATION_COMMAND_PERMISSIONS_UPDATE = "APPLICATION_COMMAND_PERMISSIONS_UPDATE"
    AUTO_MODERATION_RULE_CREATE  = "AUTO_MODERATION_RULE_CREATE"
    AUTO_MODERATION_RULE_UPDATE  = "AUTO_MODERATION_RULE_UPDATE"
    AUTO_MODERATION_RULE_DELETE  = "AUTO_MODERATION_RULE_DELETE"
    AUTO_MODERATION_ACTION_EXECUTION = "AUTO_MODERATION_ACTION_EXECUTION"
    CHANNEL_CREATE               = "CHANNEL_CREATE"
    CHANNEL_UPDATE               = "CHANNEL_UPDATE"
    CHANNEL_DELETE               = "CHANNEL_DELETE"
    CHANNEL_PINS_UPDATE          = "CHANNEL_PINS_UPDATE"
    THREAD_CREATE                = "THREAD_CREATE"
    THREAD_UPDATE                = "THREAD_UPDATE"
    THREAD_DELETE                = "THREAD_DELETE"
    THREAD_LIST_SYNC             = "THREAD_LIST_SYNC"
    THREAD_MEMBER_UPDATE         = "THREAD_MEMBER_UPDATE"
    THREAD_MEMBERS_UPDATE        = "THREAD_MEMBERS_UPDATE"
    GUILD_CREATE                 = "GUILD_CREATE"
    GUILD_UPDATE                 = "GUILD_UPDATE"
    GUILD_DELETE                 = "GUILD_DELETE"
    GUILD_AUDIT_LOG_ENTRY_CREATE = "GUILD_AUDIT_LOG_ENTRY_CREATE"
    GUILD_BAN_ADD                = "GUILD_BAN_ADD"
    GUILD_BAN_REMOVE             = "GUILD_BAN_REMOVE"
    GUILD_EMOJIS_UPDATE          = "GUILD_EMOJIS_UPDATE"
    GUILD_STICKERS_UPDATE        = "GUILD_STICKERS_UPDATE"
    GUILD_INTEGRATIONS_UPDATE    = "GUILD_INTEGRATIONS_UPDATE"
    GUILD_MEMBER_ADD             = "GUILD_MEMBER_ADD"
    GUILD_MEMBER_REMOVE          = "GUILD_MEMBER_REMOVE"
    GUILD_MEMBER_UPDATE          = "GUILD_MEMBER_UPDATE"
    GUILD_MEMBERS_CHUNK          = "GUILD_MEMBERS_CHUNK"
    GUILD_ROLE_CREATE            = "GUILD_ROLE_CREATE"
    GUILD_ROLE_UPDATE            = "GUILD_ROLE_UPDATE"
    GUILD_ROLE_DELETE            = "GUILD_ROLE_DELETE"
    GUILD_SCHEDULED_EVENT_CREATE = "GUILD_SCHEDULED_EVENT_CREATE"
    GUILD_SCHEDULED_EVENT_UPDATE = "GUILD_SCHEDULED_EVENT_UPDATE"
    GUILD_SCHEDULED_EVENT_DELETE = "GUILD_SCHEDULED_EVENT_DELETE"
    GUILD_SCHEDULED_EVENT_USER_ADD    = "GUILD_SCHEDULED_EVENT_USER_ADD"
    GUILD_SCHEDULED_EVENT_USER_REMOVE = "GUILD_SCHEDULED_EVENT_USER_REMOVE"
    INTEGRATION_CREATE           = "INTEGRATION_CREATE"
    INTEGRATION_UPDATE           = "INTEGRATION_UPDATE"
    INTEGRATION_DELETE           = "INTEGRATION_DELETE"
    INTERACTION_CREATE           = "INTERACTION_CREATE"
    INVITE_CREATE                = "INVITE_CREATE"
    INVITE_DELETE                = "INVITE_DELETE"
    MESSAGE_CREATE               = "MESSAGE_CREATE"
    MESSAGE_UPDATE               = "MESSAGE_UPDATE"
    MESSAGE_DELETE               = "MESSAGE_DELETE"
    MESSAGE_DELETE_BULK          = "MESSAGE_DELETE_BULK"
    MESSAGE_REACTION_ADD         = "MESSAGE_REACTION_ADD"
    MESSAGE_REACTION_REMOVE      = "MESSAGE_REACTION_REMOVE"
    MESSAGE_REACTION_REMOVE_ALL  = "MESSAGE_REACTION_REMOVE_ALL"
    MESSAGE_REACTION_REMOVE_EMOJI = "MESSAGE_REACTION_REMOVE_EMOJI"
    PRESENCE_UPDATE              = "PRESENCE_UPDATE"
    TYPING_START                 = "TYPING_START"
    USER_UPDATE                  = "USER_UPDATE"
    VOICE_STATE_UPDATE           = "VOICE_STATE_UPDATE"
    VOICE_SERVER_UPDATE          = "VOICE_SERVER_UPDATE"
    WEBHOOKS_UPDATE              = "WEBHOOKS_UPDATE"
    RELATIONSHIP_ADD             = "RELATIONSHIP_ADD"
    RELATIONSHIP_REMOVE          = "RELATIONSHIP_REMOVE"
    READY_SUPPLEMENTAL           = "READY_SUPPLEMENTAL"
    SESSIONS_REPLACE             = "SESSIONS_REPLACE"


# ─── GatewayConfig ────────────────────────────────────────────────────────────

@dataclass
class GatewayConfig:
    """Configuration for the Gateway connection.

    Attributes:
        token: Discord user token.
        intents: Gateway intents (user accounts typically use 0).
        large_threshold: Guild size threshold to trigger member chunking.
        capabilities: Bitmask of client capabilities (Discord internal).
        compress: Whether to enable zlib-stream transport compression.
        properties: Client identification properties for IDENTIFY.
        initial_presence: Optional presence sent with IDENTIFY.
    """

    token: str
    intents: int = 0
    large_threshold: int = 250
    capabilities: int = 16381
    compress: bool = True
    properties: Dict[str, Any] = field(default_factory=get_gateway_properties)
    initial_presence: Optional[Dict[str, Any]] = None


# ─── Gateway ──────────────────────────────────────────────────────────────────

class Gateway:
    """Discord Gateway WebSocket client.

    Connects to the Discord gateway, handles IDENTIFY/RESUME, sends
    heartbeats, and dispatches incoming events to registered listeners.

    Args:
        token: Discord user token.
        config: Optional ``GatewayConfig`` (auto-created if None).
        auto_reconnect: Whether to automatically reconnect on disconnect.

    Example:
        gateway = Gateway("your_token")

        @gateway.on(EventType.MESSAGE_CREATE)
        async def on_message(data):
            print(data["content"])

        @gateway.on(EventType.READY)
        async def on_ready(data):
            print(f"Connected as {data['user']['username']}")

        await gateway.connect()
    """

    def __init__(
        self,
        token: str,
        config: Optional[GatewayConfig] = None,
        auto_reconnect: bool = True,
    ) -> None:
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "The 'websockets' package is required for Gateway support. "
                "Install it with: pip install disapi[gateway]"
            )

        self.token = token
        self.config = config or GatewayConfig(token=token)
        self.auto_reconnect = auto_reconnect

        # Connection state
        self._ws: Optional[Any] = None
        self._connected: bool = False
        self._session_id: Optional[str] = None
        self._sequence: Optional[int] = None
        self._resume_url: Optional[str] = None
        self._heartbeat_interval: float = 41.25
        self._last_heartbeat_sent: float = 0.0
        self._last_heartbeat_ack: float = 0.0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_delay: float = 1.0

        # zlib decompression
        self._zlib_decompressor = zlib.decompressobj()
        self._buffer = bytearray()
        self._ZLIB_SUFFIX = b"\x00\x00\xff\xff"

        # Event system
        self._listeners: Dict[str, List[EventCallback]] = {}
        self._once_listeners: Dict[str, List[EventCallback]] = {}

        # Ready state
        self._ready: bool = False
        self._user: Optional[Dict[str, Any]] = None

    # ─── Properties ──────────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        """True if the WebSocket connection is active."""
        return self._connected

    @property
    def ready(self) -> bool:
        """True after the READY dispatch is received."""
        return self._ready

    @property
    def session_id(self) -> Optional[str]:
        """Current gateway session ID."""
        return self._session_id

    @property
    def sequence(self) -> Optional[int]:
        """Last received sequence number."""
        return self._sequence

    @property
    def latency(self) -> float:
        """Round-trip heartbeat latency in seconds (0 if no ACK yet)."""
        if self._last_heartbeat_ack and self._last_heartbeat_sent:
            return max(0.0, self._last_heartbeat_ack - self._last_heartbeat_sent)
        return 0.0

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """The authenticated user dict from READY, or None."""
        return self._user

    # ─── Event Registration ──────────────────────────────────────────────────

    def on(self, event: str) -> Callable[[EventCallback], EventCallback]:
        """Register a persistent listener for *event*.

        Args:
            event: Event name (case-insensitive, e.g. ``'message_create'``).

        Returns:
            Decorator that registers the wrapped function.

        Example:
            @gateway.on('message_create')
            async def handler(data): ...
        """

        def decorator(func: EventCallback) -> EventCallback:
            key = event.upper()
            self._listeners.setdefault(key, []).append(func)
            return func

        return decorator

    def once(self, event: str) -> Callable[[EventCallback], EventCallback]:
        """Register a one-shot listener that fires only once.

        Args:
            event: Event name.

        Returns:
            Decorator.
        """

        def decorator(func: EventCallback) -> EventCallback:
            key = event.upper()
            self._once_listeners.setdefault(key, []).append(func)
            return func

        return decorator

    def add_listener(self, event: str, callback: EventCallback) -> None:
        """Programmatically add a persistent listener.

        Args:
            event: Event name.
            callback: Async or sync callable that accepts one dict argument.
        """
        self._listeners.setdefault(event.upper(), []).append(callback)

    def remove_listener(self, event: str, callback: EventCallback) -> None:
        """Remove a specific listener.

        Args:
            event: Event name.
            callback: Previously registered callback.
        """
        key = event.upper()
        if key in self._listeners:
            try:
                self._listeners[key].remove(callback)
            except ValueError:
                pass

    # ─── Connection ───────────────────────────────────────────────────────────

    async def connect(self, url: Optional[str] = None) -> None:
        """Connect to the Discord gateway and start the event loop.

        This coroutine runs until the connection is closed and
        ``auto_reconnect`` is False, or until ``close()`` is called.

        Args:
            url: Override gateway URL (uses ``GATEWAY_URL`` by default).
        """
        gateway_url = url or self._resume_url or GATEWAY_URL
        self._reconnect_delay = 1.0

        while True:
            try:
                await self._run_connection(gateway_url)
            except ConnectionClosed as exc:
                if not exc.can_reconnect or not self.auto_reconnect:
                    raise
                gateway_url = self._resume_url or GATEWAY_URL
            except Exception as exc:
                logger.error("Unexpected gateway error: %s", exc, exc_info=True)
                if not self.auto_reconnect:
                    raise
            else:
                if not self.auto_reconnect:
                    break

            # Wait before reconnecting
            jitter = random.uniform(0, self._reconnect_delay * 0.2)
            delay = self._reconnect_delay + jitter
            logger.info("Reconnecting in %.2fs…", delay)
            await asyncio.sleep(delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, 60.0)

    async def _run_connection(self, url: str) -> None:
        """Run a single WebSocket connection session."""
        logger.info("Connecting to gateway: %s", url)

        extra_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Origin": "https://discord.com",
        }

        async with websockets.connect(  # type: ignore[attr-defined]
            url,
            max_size=None,
            ping_interval=None,  # We handle heartbeats manually
            close_timeout=10,
            additional_headers=extra_headers,
        ) as ws:
            self._ws = ws
            self._connected = True
            # Reset zlib state for new connection
            self._zlib_decompressor = zlib.decompressobj()
            self._buffer = bytearray()
            logger.info("Gateway WebSocket connected")

            try:
                async for message in ws:
                    await self._handle_raw(message)
            except WSConnectionClosed as exc:
                code = getattr(exc, "code", 1000)
                reason = getattr(exc, "reason", "")
                await self._handle_close(code, reason)
            finally:
                self._connected = False
                await self._cancel_tasks()

    # ─── Message Handling ─────────────────────────────────────────────────────

    async def _handle_raw(self, raw: Union[str, bytes]) -> None:
        """Decompress and parse a raw WebSocket message."""
        if isinstance(raw, bytes):
            self._buffer.extend(raw)
            if len(raw) >= 4 and raw[-4:] == self._ZLIB_SUFFIX:
                try:
                    data = self._zlib_decompressor.decompress(self._buffer)
                    self._buffer = bytearray()
                    await self._handle_json(data.decode("utf-8"))
                except zlib.error as exc:
                    logger.warning("zlib decompression failed: %s", exc)
                    self._buffer = bytearray()
            # Otherwise accumulate and wait for ZLIB suffix
        else:
            await self._handle_json(raw)

    async def _handle_json(self, text: str) -> None:
        """Parse JSON payload and dispatch to opcode handler."""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse gateway JSON: %s", exc)
            return

        op: int = payload.get("op", -1)
        d: Any = payload.get("d")
        s: Optional[int] = payload.get("s")
        t: Optional[str] = payload.get("t")

        if s is not None:
            self._sequence = s

        await self._dispatch_opcode(op, d, t)

    async def _dispatch_opcode(
        self, op: int, data: Any, event_name: Optional[str]
    ) -> None:
        """Route gateway opcodes to their handlers."""
        if op == GatewayOpcode.HELLO:
            await self._on_hello(data)

        elif op == GatewayOpcode.DISPATCH:
            await self._on_dispatch(event_name, data)

        elif op == GatewayOpcode.HEARTBEAT:
            # Server requested immediate heartbeat
            await self._send_heartbeat()

        elif op == GatewayOpcode.HEARTBEAT_ACK:
            self._last_heartbeat_ack = time.monotonic()
            logger.debug("Heartbeat ACK received (latency=%.1fms)", self.latency * 1000)

        elif op == GatewayOpcode.RECONNECT:
            logger.info("Server requested RECONNECT")
            await self._ws.close(1000)

        elif op == GatewayOpcode.INVALID_SESSION:
            resumable = bool(data)
            logger.warning("Invalid session — resumable=%s", resumable)
            if not resumable:
                self._session_id = None
                self._sequence = None
            await asyncio.sleep(random.uniform(1.0, 5.0))
            if resumable:
                await self._send_resume()
            else:
                await self._send_identify()

        else:
            logger.debug("Unhandled opcode: %d", op)

    # ─── Opcode Handlers ─────────────────────────────────────────────────────

    async def _on_hello(self, data: Dict[str, Any]) -> None:
        """Handle op 10 HELLO — start heartbeat, then IDENTIFY or RESUME."""
        interval_ms: int = data.get("heartbeat_interval", 41250)
        self._heartbeat_interval = interval_ms / 1000.0
        logger.debug("Hello: heartbeat_interval=%.3fs", self._heartbeat_interval)

        # Start heartbeat (jitter initial delay per spec)
        self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop())

        if self._session_id and self._sequence is not None:
            await self._send_resume()
        else:
            await self._send_identify()

    async def _on_dispatch(self, event: Optional[str], data: Any) -> None:
        """Handle op 0 DISPATCH — update state and emit to listeners."""
        if event is None:
            return

        if event == EventType.READY:
            self._session_id = data.get("session_id")
            self._resume_url = data.get("resume_gateway_url")
            self._user = data.get("user")
            self._ready = True
            self._reconnect_delay = 1.0
            logger.info(
                "READY — session=%s user=%s",
                self._session_id,
                self._user.get("username") if self._user else "?",
            )

        elif event == EventType.RESUMED:
            logger.info("Gateway session RESUMED")

        await self._emit(event, data)

    async def _handle_close(self, code: int, reason: str) -> None:
        """Handle WebSocket close — determine if reconnectable."""
        self._connected = False
        logger.warning("Gateway closed: code=%d reason=%r", code, reason)

        can_reconnect = code not in GatewayCloseCode.FATAL_CODES

        if not can_reconnect:
            raise ConnectionClosed(code=code, reason=reason, can_reconnect=False)

        # For resume-capable codes, preserve session
        if code in (GatewayCloseCode.GOING_AWAY, GatewayCloseCode.UNKNOWN_ERROR,
                    GatewayCloseCode.SESSION_TIMEOUT):
            pass  # Keep session_id and sequence for RESUME
        elif code == GatewayCloseCode.INVALID_SEQ:
            self._sequence = None

    # ─── Heartbeat ────────────────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Send heartbeats at the HELLO-specified interval."""
        # Initial heartbeat jitter (rand(0, interval) per Discord spec)
        await asyncio.sleep(random.uniform(0, self._heartbeat_interval))

        while self._connected:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Heartbeat loop error: %s", exc)
                break

    async def _send_heartbeat(self) -> None:
        """Send a HEARTBEAT payload."""
        self._last_heartbeat_sent = time.monotonic()
        await self._send({"op": GatewayOpcode.HEARTBEAT, "d": self._sequence})
        logger.debug("Heartbeat sent (seq=%s)", self._sequence)

    # ─── Sending ─────────────────────────────────────────────────────────────

    async def _send(self, payload: Dict[str, Any]) -> None:
        """Serialise and send a payload over the WebSocket."""
        if self._ws is None:
            raise GatewayException("Not connected to gateway")
        await self._ws.send(json.dumps(payload))

    async def _send_identify(self) -> None:
        """Send the IDENTIFY payload."""
        presence = self.config.initial_presence or {
            "status": Status.ONLINE,
            "since": 0,
            "activities": [],
            "afk": False,
        }
        payload = {
            "op": GatewayOpcode.IDENTIFY,
            "d": {
                "token": self.token,
                "capabilities": self.config.capabilities,
                "properties": self.config.properties,
                "presence": presence,
                "compress": False,  # We use transport compression, not payload
                "client_state": {
                    "guild_hashes": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1,
                    "private_channels_version": "0",
                    "api_code_version": 0,
                },
            },
        }
        await self._send(payload)
        logger.info("IDENTIFY sent")

    async def _send_resume(self) -> None:
        """Send the RESUME payload."""
        payload = {
            "op": GatewayOpcode.RESUME,
            "d": {
                "token": self.token,
                "session_id": self._session_id,
                "seq": self._sequence,
            },
        }
        await self._send(payload)
        logger.info("RESUME sent (session=%s seq=%s)", self._session_id, self._sequence)

    # ─── Emit ─────────────────────────────────────────────────────────────────

    async def _emit(self, event: str, data: Any) -> None:
        """Dispatch *data* to all listeners registered for *event*."""
        key = event.upper()

        # Persistent listeners
        for cb in list(self._listeners.get(key, [])):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
            except Exception as exc:
                logger.error("Error in listener for %s: %s", event, exc, exc_info=True)

        # One-shot listeners
        once_cbs = self._once_listeners.pop(key, [])
        for cb in once_cbs:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
            except Exception as exc:
                logger.error("Error in once-listener for %s: %s", event, exc, exc_info=True)

    # ─── Gateway Commands ─────────────────────────────────────────────────────

    async def update_presence(
        self,
        status: str = Status.ONLINE,
        activities: Optional[List[Dict[str, Any]]] = None,
        afk: bool = False,
        since: Optional[int] = None,
    ) -> None:
        """Send a PRESENCE_UPDATE payload.

        Args:
            status: Online status string (``'online'``, ``'idle'``, ``'dnd'``, ``'invisible'``).
            activities: List of activity dicts.
            afk: Whether the client is AFK.
            since: Unix ms timestamp when idle began (or 0).
        """
        payload = {
            "op": GatewayOpcode.PRESENCE_UPDATE,
            "d": {
                "status": status,
                "activities": activities or [],
                "afk": afk,
                "since": since if since is not None else (
                    int(time.time() * 1000) if status == Status.IDLE else 0
                ),
            },
        }
        await self._send(payload)

    async def set_status(self, status: str) -> None:
        """Set presence status only.

        Args:
            status: ``'online'``, ``'idle'``, ``'dnd'``, or ``'invisible'``.
        """
        await self.update_presence(status=status)

    async def set_activity(
        self,
        name: str,
        activity_type: int = ActivityType.PLAYING,
        url: Optional[str] = None,
        details: Optional[str] = None,
        state: Optional[str] = None,
        status: str = Status.ONLINE,
    ) -> None:
        """Set a rich presence activity.

        Args:
            name: Activity name.
            activity_type: One of ``ActivityType.*`` constants.
            url: Stream URL (only used for STREAMING type).
            details: Rich presence details line.
            state: Rich presence state line.
            status: Online status to use alongside the activity.
        """
        activity: Dict[str, Any] = {"name": name, "type": activity_type}
        if url:
            activity["url"] = url
        if details:
            activity["details"] = details
        if state:
            activity["state"] = state
        await self.update_presence(status=status, activities=[activity])

    async def set_custom_status(
        self,
        text: str,
        emoji_name: Optional[str] = None,
        emoji_id: Optional[str] = None,
        expires_at: Optional[str] = None,
        status: str = Status.ONLINE,
    ) -> None:
        """Set a custom status (text + optional emoji).

        Args:
            text: Status text (shown in the custom status field).
            emoji_name: Unicode or custom emoji name.
            emoji_id: Custom emoji ID (if using a server emoji).
            expires_at: ISO8601 expiry timestamp.
            status: Online status string.
        """
        activity: Dict[str, Any] = {
            "name": "Custom Status",
            "type": ActivityType.CUSTOM,
            "state": text,
        }
        if emoji_name or emoji_id:
            activity["emoji"] = {"name": emoji_name, "id": emoji_id}
        if expires_at:
            activity["expires_at"] = expires_at

        await self.update_presence(status=status, activities=[activity])

    async def clear_activity(self, status: str = Status.ONLINE) -> None:
        """Clear the current activity.

        Args:
            status: Status to keep after clearing the activity.
        """
        await self.update_presence(status=status, activities=[])

    async def update_voice_state(
        self,
        guild_id: str,
        channel_id: Optional[str] = None,
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
    ) -> None:
        """Send a VOICE_STATE_UPDATE to join, leave, or modify a voice channel.

        Args:
            guild_id: Target guild ID.
            channel_id: Voice channel ID to join, or ``None`` to disconnect.
            self_mute: Mute yourself.
            self_deaf: Deafen yourself.
            self_video: Enable video.
        """
        payload = {
            "op": GatewayOpcode.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "self_mute": self_mute,
                "self_deaf": self_deaf,
                "self_video": self_video,
            },
        }
        await self._send(payload)

    async def request_guild_members(
        self,
        guild_id: str,
        query: str = "",
        limit: int = 0,
        presences: bool = False,
        user_ids: Optional[List[str]] = None,
        nonce: Optional[str] = None,
    ) -> None:
        """Request guild member data from the gateway.

        Args:
            guild_id: Guild to request members from.
            query: Username prefix filter (empty for all).
            limit: Max members to return (0 = unlimited).
            presences: Include presence data.
            user_ids: Request specific user IDs.
            nonce: Correlation nonce returned in GUILD_MEMBERS_CHUNK.
        """
        d: Dict[str, Any] = {
            "guild_id": guild_id,
            "query": query,
            "limit": limit,
            "presences": presences,
        }
        if user_ids:
            d["user_ids"] = user_ids
        if nonce:
            d["nonce"] = nonce

        await self._send({"op": GatewayOpcode.REQUEST_GUILD_MEMBERS, "d": d})

    async def lazy_load_guild(
        self,
        guild_id: str,
        channels: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a lazy guild loading request (op 14).

        Triggers guild data for guilds that were not populated in READY.

        Args:
            guild_id: Guild ID to load.
            channels: Channel ranges dict.
        """
        d: Dict[str, Any] = {"guild_id": guild_id}
        if channels:
            d["channels"] = channels
        await self._send({"op": GatewayOpcode.LAZY_REQUEST, "d": d})

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def close(self, code: int = GatewayCloseCode.NORMAL) -> None:
        """Cleanly close the gateway connection.

        Args:
            code: WebSocket close code.
        """
        self._connected = False
        self.auto_reconnect = False
        await self._cancel_tasks()

        if self._ws is not None:
            try:
                await self._ws.close(code)
            except Exception:
                pass
            self._ws = None

        logger.info("Gateway closed by client (code=%d)", code)

    async def _cancel_tasks(self) -> None:
        """Cancel heartbeat and receive tasks."""
        for task in (self._heartbeat_task, self._receive_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._heartbeat_task = None
        self._receive_task = None

    async def __aenter__(self) -> "Gateway":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return (
            f"<Gateway connected={self._connected} ready={self._ready} "
            f"session={self._session_id!r} latency={self.latency * 1000:.1f}ms>"
        )
