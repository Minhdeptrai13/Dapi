"""
models/message.py — Discord Message Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..utils import snowflake_to_datetime
from .user import User, Member


__all__: list[str] = [
    "Message",
    "Embed",
    "EmbedField",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedImage",
    "Attachment",
    "Reaction",
    "MessageReference",
]


# ─── Embed Sub-Structures ─────────────────────────────────────────────────────

@dataclass
class EmbedField:
    """One field in an embed."""
    name: str
    value: str
    inline: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "inline": self.inline}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedField":
        return cls(name=d["name"], value=d["value"], inline=d.get("inline", False))


@dataclass
class EmbedAuthor:
    """Embed author section."""
    name: str
    url: Optional[str] = None
    icon_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name}
        if self.url:
            d["url"] = self.url
        if self.icon_url:
            d["icon_url"] = self.icon_url
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedAuthor":
        return cls(name=d.get("name", ""), url=d.get("url"), icon_url=d.get("icon_url"))


@dataclass
class EmbedFooter:
    """Embed footer section."""
    text: str
    icon_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"text": self.text}
        if self.icon_url:
            d["icon_url"] = self.icon_url
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedFooter":
        return cls(text=d.get("text", ""), icon_url=d.get("icon_url"))


@dataclass
class EmbedImage:
    """Embed image / thumbnail."""
    url: str
    proxy_url: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"url": self.url}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EmbedImage":
        return cls(
            url=d.get("url", ""),
            proxy_url=d.get("proxy_url"),
            height=d.get("height"),
            width=d.get("width"),
        )


# ─── Embed ────────────────────────────────────────────────────────────────────

class Embed:
    """Represents a Discord message embed.

    Provides a builder-style API for constructing embeds.

    Example:
        embed = (
            Embed(title="Hello!", color=0x5865F2)
            .set_description("This is an embed.")
            .set_author("disapi", icon_url="https://...")
            .add_field("Field 1", "Value 1", inline=True)
            .add_field("Field 2", "Value 2", inline=True)
            .set_footer("Footer text")
        )
        await client.messages.send(channel_id, embed=embed)

    Attributes:
        title: Embed title (max 256 chars).
        description: Embed description (max 4096 chars).
        url: URL that the title links to.
        color: Integer colour (hex e.g. 0x5865F2).
        timestamp: ISO8601 timestamp string.
        author: ``EmbedAuthor`` object.
        footer: ``EmbedFooter`` object.
        image: ``EmbedImage`` object.
        thumbnail: ``EmbedImage`` object.
        fields: List of ``EmbedField`` objects.
    """

    __slots__ = (
        "title", "description", "url", "color", "timestamp",
        "author", "footer", "image", "thumbnail", "fields",
    )

    def __init__(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        color: Optional[int] = None,
        colour: Optional[int] = None,
        timestamp: Optional[Union[datetime, str]] = None,
    ) -> None:
        self.title = title
        self.description = description
        self.url = url
        self.color = color or colour
        self.timestamp: Optional[str]
        if isinstance(timestamp, datetime):
            self.timestamp = timestamp.isoformat()
        else:
            self.timestamp = timestamp
        self.author: Optional[EmbedAuthor] = None
        self.footer: Optional[EmbedFooter] = None
        self.image: Optional[EmbedImage] = None
        self.thumbnail: Optional[EmbedImage] = None
        self.fields: List[EmbedField] = []

    # Builder methods

    def set_title(self, title: str) -> "Embed":
        """Set the embed title (max 256 chars)."""
        self.title = title[:256]
        return self

    def set_description(self, description: str) -> "Embed":
        """Set the embed description (max 4096 chars)."""
        self.description = description[:4096]
        return self

    def set_url(self, url: str) -> "Embed":
        """Set the URL the title links to."""
        self.url = url
        return self

    def set_color(self, color: int) -> "Embed":
        """Set the embed colour as an integer (e.g. 0x5865F2)."""
        self.color = color
        return self

    set_colour = set_color

    def set_timestamp(self, dt: Optional[datetime] = None) -> "Embed":
        """Set the embed timestamp (defaults to now)."""
        from datetime import timezone
        ts = dt or datetime.now(tz=timezone.utc)
        self.timestamp = ts.isoformat()
        return self

    def set_author(
        self,
        name: str,
        url: Optional[str] = None,
        icon_url: Optional[str] = None,
    ) -> "Embed":
        """Set the embed author section."""
        self.author = EmbedAuthor(name=name[:256], url=url, icon_url=icon_url)
        return self

    def set_footer(
        self,
        text: str,
        icon_url: Optional[str] = None,
    ) -> "Embed":
        """Set the embed footer."""
        self.footer = EmbedFooter(text=text[:2048], icon_url=icon_url)
        return self

    def set_image(self, url: str) -> "Embed":
        """Set the main embed image."""
        self.image = EmbedImage(url=url)
        return self

    def set_thumbnail(self, url: str) -> "Embed":
        """Set the embed thumbnail."""
        self.thumbnail = EmbedImage(url=url)
        return self

    def add_field(
        self,
        name: str,
        value: str,
        *,
        inline: bool = False,
    ) -> "Embed":
        """Add a field to the embed (max 25 fields).

        Args:
            name: Field name (max 256 chars).
            value: Field value (max 1024 chars).
            inline: Whether the field is inline.
        """
        if len(self.fields) < 25:
            self.fields.append(
                EmbedField(name=name[:256], value=value[:1024], inline=inline)
            )
        return self

    def clear_fields(self) -> "Embed":
        """Remove all fields."""
        self.fields.clear()
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a Discord API-compatible dict."""
        d: Dict[str, Any] = {}
        if self.title:
            d["title"] = self.title
        if self.description:
            d["description"] = self.description
        if self.url:
            d["url"] = self.url
        if self.color is not None:
            d["color"] = self.color
        if self.timestamp:
            d["timestamp"] = self.timestamp
        if self.author:
            d["author"] = self.author.to_dict()
        if self.footer:
            d["footer"] = self.footer.to_dict()
        if self.image:
            d["image"] = self.image.to_dict()
        if self.thumbnail:
            d["thumbnail"] = self.thumbnail.to_dict()
        if self.fields:
            d["fields"] = [f.to_dict() for f in self.fields]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Embed":
        """Parse an embed from a raw API response dict."""
        embed = cls(
            title=data.get("title"),
            description=data.get("description"),
            url=data.get("url"),
            color=data.get("color"),
            timestamp=data.get("timestamp"),
        )
        if "author" in data:
            embed.author = EmbedAuthor.from_dict(data["author"])
        if "footer" in data:
            embed.footer = EmbedFooter.from_dict(data["footer"])
        if "image" in data:
            embed.image = EmbedImage.from_dict(data["image"])
        if "thumbnail" in data:
            embed.thumbnail = EmbedImage.from_dict(data["thumbnail"])
        embed.fields = [EmbedField.from_dict(f) for f in data.get("fields", [])]
        return embed

    def __repr__(self) -> str:
        return f"<Embed title={self.title!r} fields={len(self.fields)}>"

    def __len__(self) -> int:
        """Total character count of the embed (Discord limits sum to 6000)."""
        total = 0
        if self.title:
            total += len(self.title)
        if self.description:
            total += len(self.description)
        if self.author:
            total += len(self.author.name)
        if self.footer:
            total += len(self.footer.text)
        for f in self.fields:
            total += len(f.name) + len(f.value)
        return total


# ─── Attachment ───────────────────────────────────────────────────────────────

@dataclass
class Attachment:
    """Represents a file attachment on a message.

    Attributes:
        id: Attachment snowflake ID.
        filename: Original filename.
        description: Optional alt-text description.
        content_type: MIME type, if known.
        size: File size in bytes.
        url: CDN URL for the file.
        proxy_url: Proxied CDN URL.
        height: Image height (if image), or None.
        width: Image width (if image), or None.
        ephemeral: True if the attachment is ephemeral.
    """

    id: str
    filename: str
    size: int
    url: str
    proxy_url: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    ephemeral: bool = False

    @property
    def is_image(self) -> bool:
        """True if the attachment is an image."""
        if self.content_type:
            return self.content_type.startswith("image/")
        return self.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))

    @property
    def is_video(self) -> bool:
        """True if the attachment is a video."""
        if self.content_type:
            return self.content_type.startswith("video/")
        return self.filename.lower().endswith((".mp4", ".mov", ".webm", ".avi"))

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Attachment":
        return cls(
            id=d["id"],
            filename=d["filename"],
            size=d.get("size", 0),
            url=d.get("url", ""),
            proxy_url=d.get("proxy_url", ""),
            description=d.get("description"),
            content_type=d.get("content_type"),
            height=d.get("height"),
            width=d.get("width"),
            ephemeral=d.get("ephemeral", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.size,
            "url": self.url,
            "proxy_url": self.proxy_url,
            "description": self.description,
            "content_type": self.content_type,
            "height": self.height,
            "width": self.width,
            "ephemeral": self.ephemeral,
        }

    def __repr__(self) -> str:
        return f"<Attachment id={self.id!r} filename={self.filename!r} size={self.size}>"


# ─── Reaction ─────────────────────────────────────────────────────────────────

@dataclass
class Reaction:
    """Represents a reaction on a message.

    Attributes:
        count: Number of users who reacted with this emoji.
        me: Whether the current user has reacted with this emoji.
        emoji: Dict with ``id``, ``name``, ``animated`` keys.
    """

    count: int
    me: bool
    emoji: Dict[str, Any]

    @property
    def emoji_str(self) -> str:
        """The emoji as a string suitable for the API (``name:id`` for custom, ``name`` for unicode)."""
        name = self.emoji.get("name", "")
        emoji_id = self.emoji.get("id")
        if emoji_id:
            return f"{name}:{emoji_id}"
        return name

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Reaction":
        return cls(count=d.get("count", 0), me=d.get("me", False), emoji=d.get("emoji", {}))

    def to_dict(self) -> Dict[str, Any]:
        return {"count": self.count, "me": self.me, "emoji": self.emoji}

    def __repr__(self) -> str:
        return f"<Reaction emoji={self.emoji_str!r} count={self.count} me={self.me}>"


# ─── MessageReference ─────────────────────────────────────────────────────────

@dataclass
class MessageReference:
    """A reference to another message (used for replies and crossposting).

    Attributes:
        message_id: ID of the message being referenced.
        channel_id: Channel of the referenced message.
        guild_id: Guild of the referenced message (if applicable).
        fail_if_not_exists: Raise an error if the referenced message is deleted.
    """

    message_id: Optional[str] = None
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    fail_if_not_exists: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"fail_if_not_exists": self.fail_if_not_exists}
        if self.message_id:
            d["message_id"] = self.message_id
        if self.channel_id:
            d["channel_id"] = self.channel_id
        if self.guild_id:
            d["guild_id"] = self.guild_id
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MessageReference":
        return cls(
            message_id=d.get("message_id"),
            channel_id=d.get("channel_id"),
            guild_id=d.get("guild_id"),
            fail_if_not_exists=d.get("fail_if_not_exists", False),
        )


# ─── Message ──────────────────────────────────────────────────────────────────

@dataclass
class Message:
    """Represents a Discord message.

    Attributes:
        id: Snowflake message ID.
        channel_id: Channel where the message was sent.
        guild_id: Guild ID (None for DMs).
        author: The ``User`` who sent the message.
        member: The ``Member`` object if in a guild (may be None).
        content: Text content of the message.
        timestamp: ISO8601 timestamp string.
        edited_timestamp: ISO8601 edit timestamp, or None.
        tts: True if the message uses text-to-speech.
        mention_everyone: True if ``@everyone`` or ``@here`` was mentioned.
        mention_roles: List of role IDs mentioned.
        mentions: List of ``User`` objects mentioned.
        attachments: List of ``Attachment`` objects.
        embeds: List of ``Embed`` objects.
        reactions: List of ``Reaction`` objects.
        pinned: True if the message is pinned.
        type: Message type integer (see ``MessageType``).
        message_reference: Reference to the replied-to message, or None.
        referenced_message: The actual replied-to ``Message`` object, or None.
        flags: Message flags bitmask.
        nonce: Nonce sent with the message.
        webhook_id: ID if sent by a webhook, or None.
        thread: Thread channel opened from this message, or None.
        components: List of message components.
    """

    id: str
    channel_id: str
    author: User
    content: str = ""
    guild_id: Optional[str] = None
    member: Optional[Member] = None
    timestamp: Optional[str] = None
    edited_timestamp: Optional[str] = None
    tts: bool = False
    mention_everyone: bool = False
    mention_roles: List[str] = field(default_factory=list)
    mentions: List[User] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    embeds: List[Embed] = field(default_factory=list)
    reactions: List[Reaction] = field(default_factory=list)
    pinned: bool = False
    type: int = 0
    message_reference: Optional[MessageReference] = None
    referenced_message: Optional["Message"] = None
    flags: int = 0
    nonce: Optional[Union[str, int]] = None
    webhook_id: Optional[str] = None
    thread: Optional[Dict[str, Any]] = None
    components: List[Dict[str, Any]] = field(default_factory=list)

    # ─── Computed Properties ─────────────────────────────────────────────────

    @property
    def created_at(self) -> datetime:
        """When this message was sent."""
        return snowflake_to_datetime(self.id)

    @property
    def jump_url(self) -> str:
        """Discord message URL for jumping to this message."""
        guild_part = self.guild_id or "@me"
        return f"https://discord.com/channels/{guild_part}/{self.channel_id}/{self.id}"

    @property
    def is_reply(self) -> bool:
        """True if this message is a reply."""
        return self.message_reference is not None

    @property
    def is_system(self) -> bool:
        """True if this is a system-generated message (join, pin, etc.)."""
        return self.type not in (0, 19, 20, 23)

    @property
    def clean_content(self) -> str:
        """Message content with mention formatting resolved to plain text."""
        content = self.content
        for user in self.mentions:
            content = content.replace(f"<@{user.id}>", f"@{user.display_name}")
            content = content.replace(f"<@!{user.id}>", f"@{user.display_name}")
        return content

    # ─── Serialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Construct a Message from a raw Discord API dict."""
        author_data = data.get("author", {})
        author = User.from_dict(author_data) if author_data else User(id="0", username="Unknown")

        member: Optional[Member] = None
        member_data = data.get("member")
        if member_data and author_data:
            merged = {**member_data, "user": author_data}
            member = Member.from_dict(merged, guild_id=data.get("guild_id"))

        ref: Optional[MessageReference] = None
        ref_data = data.get("message_reference")
        if ref_data:
            ref = MessageReference.from_dict(ref_data)

        referenced_message: Optional[Message] = None
        ref_msg = data.get("referenced_message")
        if ref_msg:
            referenced_message = cls.from_dict(ref_msg)

        return cls(
            id=data["id"],
            channel_id=data["channel_id"],
            author=author,
            content=data.get("content", ""),
            guild_id=data.get("guild_id"),
            member=member,
            timestamp=data.get("timestamp"),
            edited_timestamp=data.get("edited_timestamp"),
            tts=data.get("tts", False),
            mention_everyone=data.get("mention_everyone", False),
            mention_roles=data.get("mention_roles", []),
            mentions=[User.from_dict(u) for u in data.get("mentions", [])],
            attachments=[Attachment.from_dict(a) for a in data.get("attachments", [])],
            embeds=[Embed.from_dict(e) for e in data.get("embeds", [])],
            reactions=[Reaction.from_dict(r) for r in data.get("reactions", [])],
            pinned=data.get("pinned", False),
            type=data.get("type", 0),
            message_reference=ref,
            referenced_message=referenced_message,
            flags=data.get("flags", 0),
            nonce=data.get("nonce"),
            webhook_id=data.get("webhook_id"),
            thread=data.get("thread"),
            components=data.get("components", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a dict."""
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "author": self.author.to_dict(),
            "content": self.content,
            "timestamp": self.timestamp,
            "edited_timestamp": self.edited_timestamp,
            "tts": self.tts,
            "mention_everyone": self.mention_everyone,
            "mention_roles": self.mention_roles,
            "mentions": [u.to_dict() for u in self.mentions],
            "attachments": [a.to_dict() for a in self.attachments],
            "embeds": [e.to_dict() for e in self.embeds],
            "reactions": [r.to_dict() for r in self.reactions],
            "pinned": self.pinned,
            "type": self.type,
            "flags": self.flags,
            "nonce": self.nonce,
            "webhook_id": self.webhook_id,
            "components": self.components,
        }

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id!r} channel={self.channel_id!r} "
            f"author={self.author!r} content={self.content[:50]!r}>"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Message) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
