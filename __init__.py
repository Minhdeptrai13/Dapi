"""
disapi - Production-Grade Discord User API Wrapper
===================================================

An async-first, modular Python library for interacting with Discord's
user/selfbot API. Supports HTTP REST + Gateway WebSocket with full
rate limiting, realistic fingerprinting, and comprehensive event handling.

╔══════════════════════════════════════════════════════════════╗
║                    ⚠  TOS WARNING  ⚠                        ║
║                                                              ║
║  Using selfbots (automating user accounts) violates          ║
║  Discord's Terms of Service (TOS) and Community Guidelines.  ║
║  Your account may be permanently terminated without notice.  ║
║                                                              ║
║  This library is provided FOR EDUCATIONAL AND RESEARCH       ║
║  PURPOSES ONLY. The authors accept no responsibility for     ║
║  any account bans, data loss, or consequences arising from   ║
║  the use of this software. Use entirely at your own risk.    ║
╚══════════════════════════════════════════════════════════════╝

Quick Start:
    import asyncio
    from disapi import Client

    async def main():
        async with Client("your_token_here") as client:
            me = await client.login()
            print(f"Logged in as {me}")

            # Modular API access
            msg = await client.messages.send("channel_id", "Hello, World!")
            await client.presence.set_custom_status("Powered by disapi ⚡")
            await client.guilds.kick("guild_id", "user_id", reason="Testing")

    asyncio.run(main())

Sync Usage:
    from disapi import SyncClient

    with SyncClient("your_token_here") as client:
        me = client.login()
        client.messages.send("channel_id", "Hello sync!")

Package Layout:
    disapi/
    ├── __init__.py       — Package entry point (this file)
    ├── client.py         — Main Client + SyncClient
    ├── http_client.py    — Async HTTP layer (httpx)
    ├── gateway.py        — WebSocket Gateway (IDENTIFY/RESUME/HEARTBEAT)
    ├── rate_limiter.py   — Smart rate limiter (global + per-bucket)
    ├── constants.py      — API constants, enums, fingerprinting
    ├── exceptions.py     — Custom exception hierarchy
    ├── types.py          — TypedDicts and type aliases
    ├── utils.py          — Utility functions and helpers
    ├── api/              — Modular API endpoints
    │   ├── messages.py
    │   ├── guilds.py
    │   ├── channels.py
    │   ├── users.py
    │   ├── reactions.py
    │   ├── relationships.py
    │   ├── presence.py
    │   └── misc.py
    └── models/           — Dataclass models
        ├── user.py
        ├── message.py
        ├── guild.py
        ├── channel.py
        └── presence.py
"""

from __future__ import annotations

import warnings as _warnings

__version__     = "3.0.0"
__author__      = "disapi contributors"
__license__     = "MIT"
__description__ = "Production-Grade Discord User API Wrapper"
__url__         = "https://github.com/disapi/disapi"
__python_requires__ = ">=3.9"

# ─── TOS Warning ────────────────────────────────────────────────────────────

_warnings.warn(
    "\n"
    "╔══════════════════════════════════════════════════════════════╗\n"
    "║                    ⚠  TOS WARNING  ⚠                        ║\n"
    "║                                                              ║\n"
    "║  Using selfbots violates Discord's Terms of Service.         ║\n"
    "║  Your account may be permanently terminated without notice.  ║\n"
    "║  This library is for EDUCATIONAL PURPOSES ONLY.              ║\n"
    "║  Use entirely at your own risk. Authors take no liability.   ║\n"
    "╚══════════════════════════════════════════════════════════════╝",
    UserWarning,
    stacklevel=2,
)

# ─── Core Client ────────────────────────────────────────────────────────────

from .client import Client, SyncClient, ClientOptions

# ─── HTTP + Gateway ─────────────────────────────────────────────────────────

from .http_client import HTTPClient, Route
from .rate_limiter import RateLimiter, RateLimitInfo

# ─── Constants ──────────────────────────────────────────────────────────────

from .constants import (
    API_VERSION,
    API_BASE_URL,
    GATEWAY_URL,
    ActivityType,
    ChannelType,
    Status,
    UserType,
    PremiumType,
    UserFlags,
    Permissions,
    RelationshipType,
    MessageType,
    GatewayOpcode,
    GatewayCloseCode,
    AuditLogEvent,
)

# ─── Exceptions ─────────────────────────────────────────────────────────────

from .exceptions import (
    DisapiException,
    DiscordException,
    HTTPException,
    RateLimited,
    Unauthorized,
    Forbidden,
    NotFound,
    BadRequest,
    Conflict,
    MethodNotAllowed,
    ServerError,
    GatewayException,
    ConnectionClosed,
    InvalidArgument,
    InvalidToken,
    MaxConcurrencyReached,
    ResponseCorrupt,
    ConfigurationError,
    LoginFailure,
)

# ─── Models ─────────────────────────────────────────────────────────────────

from .models import (
    User,
    Member,
    Message,
    Embed,
    Attachment,
    Reaction,
    MessageReference,
    Channel,
    Guild,
    Role,
    Activity,
    Presence,
)
from .models.channel import PermissionOverwrite
from .models.guild import Ban, Invite

# ─── Utils ──────────────────────────────────────────────────────────────────

from .utils import (
    generate_snowflake,
    parse_snowflake,
    snowflake_to_datetime,
    generate_nonce,
    escape_markdown,
    strip_markdown,
    mention_user,
    mention_channel,
    mention_role,
    custom_emoji,
    timestamp_style,
    split_message,
    validate_token,
    setup_logging,
)

# ─── Gateway (optional dep) ─────────────────────────────────────────────────

try:
    from .gateway import Gateway, GatewayConfig, EventType
except ImportError:
    Gateway = None      # type: ignore[assignment, misc]
    GatewayConfig = None  # type: ignore[assignment, misc]
    EventType = None    # type: ignore[assignment, misc]

# ─── Public API ─────────────────────────────────────────────────────────────

__all__: list[str] = [
    # Meta
    "__version__",
    "__author__",
    "__license__",
    "__description__",

    # Client
    "Client",
    "SyncClient",
    "ClientOptions",

    # HTTP
    "HTTPClient",
    "Route",
    "RateLimiter",
    "RateLimitInfo",

    # Constants
    "API_VERSION",
    "API_BASE_URL",
    "GATEWAY_URL",
    "ActivityType",
    "ChannelType",
    "Status",
    "UserType",
    "PremiumType",
    "UserFlags",
    "Permissions",
    "RelationshipType",
    "MessageType",
    "GatewayOpcode",
    "GatewayCloseCode",
    "AuditLogEvent",

    # Exceptions
    "DisapiException",
    "DiscordException",
    "HTTPException",
    "RateLimited",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "BadRequest",
    "Conflict",
    "MethodNotAllowed",
    "ServerError",
    "GatewayException",
    "ConnectionClosed",
    "InvalidArgument",
    "InvalidToken",
    "MaxConcurrencyReached",
    "ResponseCorrupt",
    "ConfigurationError",
    "LoginFailure",

    # Models
    "User",
    "Member",
    "Message",
    "Embed",
    "Attachment",
    "Reaction",
    "MessageReference",
    "Channel",
    "Guild",
    "Role",
    "Activity",
    "Presence",
    "PermissionOverwrite",
    "Ban",
    "Invite",

    # Utils
    "generate_snowflake",
    "parse_snowflake",
    "snowflake_to_datetime",
    "generate_nonce",
    "escape_markdown",
    "strip_markdown",
    "mention_user",
    "mention_channel",
    "mention_role",
    "custom_emoji",
    "timestamp_style",
    "split_message",
    "validate_token",
    "setup_logging",

    # Gateway
    "Gateway",
    "GatewayConfig",
    "EventType",
]
