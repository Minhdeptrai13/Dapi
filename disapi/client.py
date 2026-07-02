"""
disapi/client.py — Main Discord Client (Async & Sync)
====================================================

Async-first client with sync wrapper for Discord user/selfbot API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from .http_client import HTTPClient
from .rate_limiter import RateLimiter
from .api.messages import MessagesAPI
from .api.users import UsersAPI
from .api.guilds import GuildsAPI
from .api.channels import ChannelsAPI
from .api.reactions import ReactionsAPI
from .api.relationships import RelationshipsAPI
from .api.presence import PresenceAPI
from .api.misc import MiscAPI
from .models.user import User
from .models.message import Message
from .models.guild import Guild
from .models.channel import Channel
from .exceptions import (
    DisapiException,
    InvalidToken,
    LoginFailure,
)
from .constants import DEFAULT_REQUEST_TIMEOUT, DEFAULT_RATE_LIMIT_RETRIES
from .utils import validate_token, setup_logging

__all__ = ["Client", "SyncClient", "ClientOptions"]

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ClientOptions:
    """Client configuration options.
    
    Attributes:
        proxy: HTTP proxy URL (e.g., 'http://127.0.0.1:8080').
        timeout: Request timeout in seconds.
        max_retries: Max retry attempts for rate limits/5xx.
        debug: Enable debug logging.
        log_level: Logging level.
        suppress_warnings: Suppress TOS warning on import.
        enable_gateway: Enable WebSocket gateway.
        gateway_intents: Intents bitmask.
        auto_reconnect: Auto-reconnect on disconnect.
        heartbeat_interval: Heartbeat interval (0 = auto).
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_RATE_LIMIT_RETRIES,
        debug: bool = False,
        log_level: int = logging.INFO,
        suppress_warnings: bool = False,
        enable_gateway: bool = True,
        gateway_intents: int = 33281,
        auto_reconnect: bool = True,
        heartbeat_interval: int = 0,
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug
        self.log_level = log_level
        self.suppress_warnings = suppress_warnings
        self.enable_gateway = enable_gateway
        self.gateway_intents = gateway_intents
        self.auto_reconnect = auto_reconnect
        self.heartbeat_interval = heartbeat_interval


class Client:
    """Async Discord User API Client.
    
    Async-first client for Discord user/selfbot API.
    Supports HTTP REST and WebSocket Gateway.
    
    Example:
        async with Client("token") as client:
            user = await client.login()
            msg = await client.messages.send("channel_id", "Hello!")
    """

    def __init__(self, token: str, options: Optional[ClientOptions] = None) -> None:
        """Initialize client.
        
        Args:
            token: Discord user token.
            options: ClientOptions for configuration.
            
        Raises:
            InvalidToken: If token format is invalid.
        """
        if not token or not isinstance(token, str):
            raise InvalidToken("Token must be a non-empty string")
        
        self._token = token
        self._options = options or ClientOptions()
        self._closed = True
        self.user: Optional[User] = None
        
        # Initialize HTTP
        self._rate_limiter = RateLimiter()
        self._http = HTTPClient(
            token=token,
            proxy=self._options.proxy,
            timeout=self._options.timeout,
            max_retries=self._options.max_retries,
            debug=self._options.debug,
            rate_limiter=self._rate_limiter,
        )
        
        # Initialize API modules
        self.messages = MessagesAPI(self._http)
        self.users = UsersAPI(self._http)
        self.guilds = GuildsAPI(self._http)
        self.channels = ChannelsAPI(self._http)
        self.reactions = ReactionsAPI(self._http)
        self.relationships = RelationshipsAPI(self._http)
        self.presence = PresenceAPI(self._http)
        self.misc = MiscAPI(self._http)
        
        setup_logging(self._options.log_level, self._options.debug)

    async def __aenter__(self) -> Client:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize client (create HTTP session)."""
        if not self._closed:
            logger.warning("Client already connected")
            return
        
        await self._http.connect()
        self._closed = False
        logger.info("Client connected")

    async def login(self) -> User:
        """Login and get current user.
        
        Returns:
            Current User object.
            
        Raises:
            InvalidToken: If token is invalid.
            LoginFailure: If login fails.
        """
        if self._closed:
            raise DisapiException("Client not connected. Call .connect() first.")
        
        try:
            logger.debug("Authenticating...")
            user_data = await self._http.request("GET", "/users/@me")
            self.user = User(user_data)
            logger.info(f"Logged in as {self.user}")
            return self.user
        except Exception as e:
            if "401" in str(e):
                raise InvalidToken("Invalid token") from e
            raise LoginFailure(f"Login failed: {e}") from e

    async def close(self) -> None:
        """Close client and all connections."""
        if self._closed:
            return
        
        logger.info("Closing client...")
        try:
            await self._http.close()
        except Exception as e:
            logger.error(f"Error closing HTTP: {e}")
        
        self._closed = True
        logger.info("Client closed")

    async def get_current_user(self) -> User:
        """Get current user."""
        if not self.user:
            return await self.login()
        return self.user

    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        data = await self._http.request("GET", f"/users/{user_id}")
        return User(data)

    async def get_channel(self, channel_id: str) -> Channel:
        """Get channel by ID."""
        data = await self._http.request("GET", f"/channels/{channel_id}")
        return Channel(data)

    async def get_guild(self, guild_id: str) -> Guild:
        """Get guild by ID."""
        data = await self._http.request("GET", f"/guilds/{guild_id}")
        return Guild(data)

    async def get_message(self, channel_id: str, message_id: str) -> Message:
        """Get message by ID."""
        data = await self._http.request("GET", f"/channels/{channel_id}/messages/{message_id}")
        return Message(data)

    @property
    def http(self) -> HTTPClient:
        """Get HTTP client."""
        return self._http

    @property
    def is_closed(self) -> bool:
        """Check if client is closed."""
        return self._closed


class SyncClient:
    """Synchronous wrapper around async Client.
    
    Provides sync interface for users who don't want async/await.
    All methods are blocking.
    
    Example:
        with SyncClient("token") as client:
            user = client.login()
            msg = client.messages.send("channel_id", "Hello!")
    """

    def __init__(self, token: str, options: Optional[ClientOptions] = None) -> None:
        """Initialize sync client."""
        if options:
            options.enable_gateway = False
        else:
            options = ClientOptions(enable_gateway=False)
        
        self._client = Client(token, options)

    def __enter__(self) -> SyncClient:
        """Context manager entry."""
        asyncio.run(self._client.connect())
        asyncio.run(self._client.login())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        asyncio.run(self._client.close())

    def __repr__(self) -> str:
        return f"<SyncClient {self._client.user}>"

    def _run_sync(self, coro: Awaitable[T]) -> T:
        """Run async code synchronously."""
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot use SyncClient from async context")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    def login(self) -> User:
        """Login (blocking)."""
        return self._run_sync(self._client.login())

    def close(self) -> None:
        """Close (blocking)."""
        self._run_sync(self._client.close())

    def get_current_user(self) -> User:
        """Get current user (blocking)."""
        return self._run_sync(self._client.get_current_user())

    def get_user(self, user_id: str) -> User:
        """Get user by ID (blocking)."""
        return self._run_sync(self._client.get_user(user_id))

    def get_channel(self, channel_id: str) -> Channel:
        """Get channel by ID (blocking)."""
        return self._run_sync(self._client.get_channel(channel_id))

    def get_guild(self, guild_id: str) -> Guild:
        """Get guild by ID (blocking)."""
        return self._run_sync(self._client.get_guild(guild_id))

    def get_message(self, channel_id: str, message_id: str) -> Message:
        """Get message by ID (blocking)."""
        return self._run_sync(self._client.get_message(channel_id, message_id))

    @property
    def user(self) -> Optional[User]:
        """Get current user."""
        return self._client.user

    @property
    def messages(self) -> MessagesAPI:
        """Access messages API."""
        return self._client.messages

    @property
    def users(self) -> UsersAPI:
        """Access users API."""
        return self._client.users

    @property
    def guilds(self) -> GuildsAPI:
        """Access guilds API."""
        return self._client.guilds

    @property
    def channels(self) -> ChannelsAPI:
        """Access channels API."""
        return self._client.channels

    @property
    def reactions(self) -> ReactionsAPI:
        """Access reactions API."""
        return self._client.reactions

    @property
    def relationships(self) -> RelationshipsAPI:
        """Access relationships API."""
        return self._client.relationships

    @property
    def presence(self) -> PresenceAPI:
        """Access presence API."""
        return self._client.presence

    @property
    def misc(self) -> MiscAPI:
        """Access misc API."""
        return self._client.misc

    @property
    def http(self) -> HTTPClient:
        """Get HTTP client."""
        return self._client.http

    @property
    def is_closed(self) -> bool:
        """Check if client is closed."""
        return self._client.is_closed
