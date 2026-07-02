"""
Discord Self-Bot Client.

This is the main client class for interacting with Discord's API using a user token.

WARNING:
--------
Using self-bots (automating user accounts) violates Discord's Terms of Service.
This library is for educational purposes only. Use at your own risk.

Example:
--------
async with Client("your_token") as client:
    user = await client.get_current_user()
    print(f"Logged in as {user}")

    # Send a message
    await client.messages.send("channel_id", "Hello!")

    # Reply to a message
    await client.messages.reply("channel_id", "message_id", "Reply content")
"""
import asyncio
import logging
import warnings
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .http_client import HTTPClient
from .api.messages import MessagesAPI
from .api.users import UsersAPI
from .api.guilds import GuildsAPI
from .api.channels import ChannelsAPI
from .api.reactions import ReactionsAPI
from .api.relationships import RelationshipsAPI
from .api.presence import PresenceAPI
from .api.misc import MiscAPI
from .models.user import User, Member
from .models.message import Message, Embed
from .models.guild import Guild
from .models.channel import Channel
from .exceptions import DisapiException, InvalidToken
from .constants import (
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_RATE_LIMIT_RETRIES,
    ActivityType,
    Status,
)
from .utils import validate_token, setup_logging


__all__ = [
    'Client',
    'ClientOptions',
]


T = TypeVar('T')


class ClientOptions:
    """Client configuration options.

    Attributes:
        proxy: Proxy URL (e.g., 'http://127.0.0.1:8080').
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts for rate limits.
        debug: Enable debug logging.
        log_level: Logging level.
        suppress_warnings: Suppress self-bot warnings.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_RATE_LIMIT_RETRIES,
        debug: bool = False,
        log_level: int = logging.INFO,
        suppress_warnings: bool = False,
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug
        self.log_level = log_level
        self.suppress_warnings = suppress_warnings


class Client:
    """Discord Self-Bot Client.

    This is the main class for interacting with Discord's API using a user token.

    WARNING:
    --------
    Using self-bots violates Discord's Terms of Service and may result in
    account termination. Use responsibly and at your own risk.

    Example:
    --------
    async with Client("your_token") as client:
        user = await client.get_current_user()
        print(f"Logged in as {user}")

        await client.messages.send("123456789", "Hello world!")

    Attributes:
        token: Discord user token.
        http: HTTP client instance.
        messages: Messages API.
        users: Users API.
        guilds: Guilds API.
        channels: Channels API.
        reactions: Reactions API.
        relationships: Relationships API.
        presence: Presence API.
        misc: Miscellaneous API.
        _user: Current user.
        _closed: Whether client is closed.
    """

    __slots__ = (
        'token',
        'http',
        '_user',
        '_closed',
        '_options',
        'messages',
        'users',
        'guilds',
        'channels',
        'reactions',
        'relationships',
        'presence',
        'misc',
    )

    def __init__(
        self,
        token: str,
        proxy: Optional[str] = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_RATE_LIMIT_RETRIES,
        debug: bool = False,
        suppress_warnings: bool = False,
    ):
        """Initialize the Discord client.

        Args:
            token: Discord user token.
            proxy: Proxy URL (optional).
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            debug: Enable debug logging.
            suppress_warnings: Suppress self-bot warnings.
        """
        # Validate token format
        if not token or not isinstance(token, str):
            raise InvalidToken("Token must be a non-empty string")

        if not validate_token(token):
            warnings.warn(
                "Token format appears invalid. Proceed with caution.",
                UserWarning
            )

        self.token = token
        self._closed = False
        self._user: Optional[User] = None

        # Setup logging
        if debug:
            setup_logging(level=logging.DEBUG)
        else:
            setup_logging(level=logging.INFO)

        # Show warning
        if not suppress_warnings:
            warnings.warn(
                "\n"
                "╔═══════════════════════════════════════════════════════════╗\n"
                "║               SELF-BOT WARNING                           ║\n"
                "║                                                           ║\n"
                "║  Using self-bots violates Discord's Terms of Service.     ║\n"
                "║  This may result in account termination.                  ║\n"
                "║  Use responsibly and at your own risk.                   ║\n"
                "║                                                           ║\n"
                "║  This library is for educational purposes only.          ║\n"
                "╚═══════════════════════════════════════════════════════════╝",
                UserWarning
            )

        # Initialize HTTP client
        self.http = HTTPClient(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            proxy=proxy,
        )

        # Initialize API modules
        self.messages = MessagesAPI(self.http)
        self.users = UsersAPI(self.http)
        self.guilds = GuildsAPI(self.http)
        self.channels = ChannelsAPI(self.http)
        self.reactions = ReactionsAPI(self.http)
        self.relationships = RelationshipsAPI(self.http)
        self.presence = PresenceAPI(self.http)
        self.misc = MiscAPI(self.http)

    # ========== Context Manager ==========

    async def __aenter__(self) -> 'Client':
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        await self.close()

    # ========== Properties ==========

    @property
    def user(self) -> Optional[User]:
        """Get current user (requires fetching first)."""
        return self._user

    @property
    def closed(self) -> bool:
        """Check if client is closed."""
        return self._closed

    # ========== Connection Methods ==========

    async def login(self) -> User:
        """Login and get current user.

        Returns:
            Current User object.
        """
        if self._user:
            return self._user

        self._user = await self.users.get_current()
        return self._user

    async def close(self) -> None:
        """Close the client and release resources."""
        if self._closed:
            return

        self._closed = True
        await self.http.close()

    # ========== Convenience Methods ==========

    async def get_current_user(self) -> User:
        """Get current user information.

        Returns:
            Current User.
        """
        return await self.users.get_current()

    async def get_user(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: User ID.

        Returns:
            User object.
        """
        return await self.users.get_user(user_id)

    async def send_message(
        self,
        channel_id: str,
        content: str,
        embed: Optional[Union[Dict, Embed]] = None,
        **kwargs
    ) -> Message:
        """Send a message to a channel.

        Args:
            channel_id: Channel ID.
            content: Message content.
            embed: Optional embed.
            **kwargs: Additional arguments.

        Returns:
            Created Message.
        """
        return await self.messages.send(
            channel_id,
            content=content,
            embed=embed,
            **kwargs
        )

    async def reply(
        self,
        channel_id: str,
        message_id: str,
        content: str,
        **kwargs
    ) -> Message:
        """Reply to a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID to reply to.
            content: Reply content.
            **kwargs: Additional arguments.

        Returns:
            Created Message.
        """
        return await self.messages.reply(
            channel_id,
            message_id,
            content=content,
            **kwargs
        )

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        **kwargs
    ) -> Message:
        """Edit a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            content: New content.
            **kwargs: Additional arguments.

        Returns:
            Edited Message.
        """
        return await self.messages.edit(
            channel_id,
            message_id,
            content=content,
            **kwargs
        )

    async def delete_message(
        self,
        channel_id: str,
        message_id: str
    ) -> None:
        """Delete a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
        """
        await self.messages.delete(channel_id, message_id)

    async def get_channel(self, channel_id: str) -> Channel:
        """Get channel by ID.

        Args:
            channel_id: Channel ID.

        Returns:
            Channel object.
        """
        return await self.channels.get(channel_id)

    async def get_guild(self, guild_id: str) -> Guild:
        """Get guild by ID.

        Args:
            guild_id: Guild ID.

        Returns:
            Guild object.
        """
        return await self.guilds.get(guild_id)

    async def get_guild_member(
        self,
        guild_id: str,
        user_id: str
    ) -> Member:
        """Get guild member.

        Args:
            guild_id: Guild ID.
            user_id: User ID.

        Returns:
            Member object.
        """
        return await self.guilds.get_member(guild_id, user_id)

    async def create_dm(self, user_id: str) -> Channel:
        """Create DM channel with a user.

        Args:
            user_id: User ID.

        Returns:
            DM Channel.
        """
        data = await self.users.create_dm(user_id)
        return Channel.from_dict(data)

    async def set_status(
        self,
        status: str = Status.ONLINE
    ) -> None:
        """Set online status.

        Args:
            status: Status (online, idle, dnd, invisible).
        """
        await self.presence.set_status(status)

    async def set_activity(
        self,
        name: str,
        activity_type: int = ActivityType.PLAYING
    ) -> None:
        """Set activity/status.

        Args:
            name: Activity name.
            activity_type: Activity type.

        Example:
            # Playing
            await client.set_activity("Visual Studio Code")

            # Streaming
            await client.set_activity("Twitch", activity_type=1)
        """
        await self.presence.set_activity(name, activity_type)

    async def set_custom_status(
        self,
        text: str,
        emoji_name: Optional[str] = None
    ) -> None:
        """Set custom status.

        Args:
            text: Status text.
            emoji_name: Optional emoji.
        """
        await self.presence.set_custom_status(text=text, emoji_name=emoji_name)

    async def trigger_typing(self, channel_id: str) -> None:
        """Start typing indicator in a channel.

        Args:
            channel_id: Channel ID.
        """
        await self.messages.trigger_typing(channel_id)

    async def add_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> None:
        """Add reaction to a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            emoji: Emoji string.
        """
        await self.reactions.add(channel_id, message_id, emoji)

    async def remove_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str
    ) -> None:
        """Remove reaction from a message.

        Args:
            channel_id: Channel ID.
            message_id: Message ID.
            emoji: Emoji string.
        """
        await self.reactions.remove(channel_id, message_id, emoji)

    async def join_guild(self, invite_code: str) -> Guild:
        """Join a guild via invite.

        Args:
            invite_code: Invite code.

        Returns:
            Guild object.
        """
        data = await self.users.join_guild(invite_code)
        return Guild.from_dict(data)

    async def leave_guild(self, guild_id: str) -> None:
        """Leave a guild.

        Args:
            guild_id: Guild ID.
        """
        await self.guilds.leave(guild_id)

    async def send_friend_request(
        self,
        username: str,
        discriminator: Optional[str] = None
    ) -> None:
        """Send friend request.

        Args:
            username: Username (with or without discriminator).
            discriminator: Discriminator (optional).
        """
        await self.relationships.send_friend_request(username, discriminator)

    def __repr__(self) -> str:
        return f"<Client user={self._user} closed={self._closed}>"

    def __str__(self) -> str:
        if self._user:
            return f"Client as {self._user}"
        return "Client (not logged in)"


# ========== Sync Wrapper ==========

class SyncClient:
    """Synchronous wrapper for Client.

    Provides a synchronous interface for the async Client.

    Example:
        with SyncClient("your_token") as client:
            user = client.get_current_user()
            print(f"Logged in as {user}")
            client.send_message("channel_id", "Hello!")
    """

    def __init__(self, token: str, **kwargs):
        """Initialize sync client.

        Args:
            token: Discord token.
            **kwargs: Additional Client arguments.
        """
        self._client = Client(token, **kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        return self._loop

    def _run(self, coro):
        """Run coroutine synchronously."""
        loop = self._get_loop()
        if loop.is_running():
            # Create task if loop is already running
            task = asyncio.create_task(coro)
            return asyncio.ensure_future(task)
        return loop.run_until_complete(coro)

    def login(self) -> User:
        """Login and get user."""
        return self._run(self._client.login())

    def close(self) -> None:
        """Close client."""
        return self._run(self._client.close())

    def __enter__(self) -> 'SyncClient':
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        self._run(self._client.close())

    # Delegate to async client methods
    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._client, name)

        if callable(attr):
            async_method = getattr(self._client, name)

            def wrapper(*args, **kwargs):
                return self._run(async_method(*args, **kwargs))

            return wrapper

        return attr
