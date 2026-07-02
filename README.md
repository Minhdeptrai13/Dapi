# Disapi — Discord User API Wrapper Production-Grade

<div align="center">

**Async-First • Realistic Fingerprinting • Full Gateway Support • Type-Safe**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Async-First](https://img.shields.io/badge/async-first-brightgreen)](https://docs.python.org/3/library/asyncio.html)

</div>

---

## ⚠️ Cảnh báo Điều khoản Dịch vụ

**Sử dụng selfbot (tự động hóa tài khoản người dùng) vi phạm [Điều khoản Dịch vụ](https://discord.com/terms) và [Hướng dẫn Cộng đồng](https://discord.com/guidelines) của Discord.**

- ❌ Tài khoản của bạn **có thể bị chặn vĩnh viễn** mà không cảnh báo trước
- ❌ Không có tài khoản dự phòng được đảm bảo
- ❌ Discord liên tục cập nhật phát hiện

**Thư viện này chỉ được cung cấp cho MỤC ĐÍCH GIÁO DỤC VÀ NGHIÊN CỨU. Tác giả không chịu trách nhiệm cho bất kỳ hậu quả nào bao gồm ban tài khoản, mất dữ liệu, hoặc khác. Sử dụng hoàn toàn tại rủi ro của riêng bạn.**

---

## 📋 Mục lục

- [Tính Năng](#-tính-năng)
- [Yêu Cầu](#-yêu-cầu)
- [Cài Đặt](#-cài-đặt)
- [Hướng Dẫn Nhanh](#-hướng-dẫn-nhanh)
- [Ví Dụ](#-ví-dụ)
- [API Reference](#-api-reference)
- [Kiến Trúc](#-kiến-trúc)
- [Cấu Hình Nâng Cao](#-cấu-hình-nâng-cao)
- [Khắc Phục Sự Cố](#-khắc-phục-sự-cố)

---

## 🎯 Tính Năng

### Core
- ✅ **Async-First**: Sử dụng `httpx` + `asyncio` + `websockets`
- ✅ **Full Type Hints**: Hỗ trợ TypedDict, Protocol, và mypy
- ✅ **Context Manager**: Quản lý tài nguyên tự động với `async with`
- ✅ **Production-Grade**: Xử lý lỗi mạnh mẽ, logging chi tiết

### HTTP REST API
- ✅ **Modular Design**: Các module riêng biệt (messages, users, guilds, etc.)
- ✅ **Smart Rate Limiting**: Global + per-bucket + exponential backoff + jitter
- ✅ **Auto-Retry**: Tự động thử lại với 429/5xx errors
- ✅ **Proxy Support**: HTTP/SOCKS5 proxy cho mọi request

### Realistic Fingerprinting 
- ✅ **Browser Headers**: Giả lập Chrome 131/Edge 131/Firefox 133 (2026)
- ✅ **Super-Properties**: Fingerprint base64 giống Discord Web
- ✅ **User-Agent Rotation**: Thay đổi UA ngẫu nhiên mỗi request
- ✅ **Sec-CH-UA Headers**: Correct Client Hints cho Chrome versions
- ✅ **Build Number**: Realistic client build number (392024)

### Gateway WebSocket
- ✅ **Full IDENTIFY/RESUME**: Kết nối lâu dài với Discord
- ✅ **Auto-Reconnect**: Tự động reconnect với exponential backoff
- ✅ **Heartbeat Tracking**: ACK tracking, latency measurement
- ✅ **Zlib Compression**: Hỗ trợ zlib-stream compression
- ✅ **Event System**: Decorator-based event handlers
- ✅ **Lazy Loading**: Guild lazy loading (op 14)

### Models & Type Safety
- ✅ **TypedDict Models**: User, Guild, Channel, Message, etc.
- ✅ **Validation**: Tự động parse và validate dữ liệu Discord
- ✅ **Snowflake IDs**: Xử lý ID Discord (64-bit integers)
- ✅ **Timestamps**: Tự động parse ISO 8601 timestamps

---

## 📦 Yêu Cầu

- **Python**: 3.9+
- **OS**: Windows, macOS, Linux
- **Dependencies**: Tự động cài qua pip

---

## 🚀 Cài Đặt

### Từ PyPI (sắp có)

```bash
pip install disapi
```

### Từ GitHub (Development)

```bash
git clone https://github.com/Minhdeptrai13/Disapi.git
cd Disapi
pip install -e ".[dev]"
```

### Cài Đặt với Development Tools

```bash
# Cài đặt toàn bộ dev dependencies (testing, linting, docs)
pip install -e ".[dev]"

# Hoặc chỉ documentation
pip install -e ".[docs]"
```

---

## 🎬 Hướng Dẫn Nhanh

### Async - Cách Đề Nghị

```python
import asyncio
from disapi import Client

async def main():
    async with Client("your_token_here") as client:
        # Đăng nhập
        user = await client.login()
        print(f"✅ Logged in as {user.username}#{user.discriminator}")
        
        # Gửi tin nhắn
        msg = await client.messages.send("channel_id_here", "Hello, World! 👋")
        print(f"📤 Sent message: {msg.id}")
        
        # Thiết lập trạng thái người dùng
        await client.presence.set_status("idle")
        await client.presence.set_custom_status("Powered by disapi ⚡")
        
        # Lấy thông tin người dùng
        user_info = await client.users.get_profile("user_id_here")
        print(f"👤 User: {user_info.username}")

# Chạy
asyncio.run(main())
```

### Sync - Đơn Giản Hơn

```python
from disapi import SyncClient

with SyncClient("your_token_here") as client:
    user = client.login()
    msg = client.messages.send("channel_id", "Hello!")
    client.presence.set_custom_status("Status")
    print(f"✅ Done: {user}")
```

---

## 📚 Ví Dụ

### Ví Dụ 1: Gửi Tin Nhắn với Embed

```python
import asyncio
from disapi import Client

async def send_embed_message():
    async with Client("token") as client:
        await client.login()
        
        msg = await client.messages.send(
            "channel_id",
            content="Check this out! 🎨",
            embed={
                "title": "Disapi is Awesome",
                "description": "Production-grade Discord API wrapper",
                "color": 0x5865F2,  # Discord blue
                "fields": [
                    {
                        "name": "Feature",
                        "value": "✅ Async-First",
                        "inline": True,
                    },
                    {
                        "name": "Feature",
                        "value": "✅ Type-Safe",
                        "inline": True,
                    },
                ],
            }
        )
        print(f"📤 Sent: {msg.id}")

asyncio.run(send_embed_message())
```

### Ví Dụ 2: Event Listeners (Gateway)

```python
import asyncio
from disapi import Client

client = Client("token", enable_gateway=True)

@client.event("message_create")
async def on_message(event: dict):
    print(f"📨 Message: {event['d']['content']}")

@client.event("presence_update")
async def on_presence_update(event: dict):
    print(f"👤 Presence update: {event['d']}")

async def main():
    async with client:
        await client.login()
        await client.connect_gateway()
        await asyncio.sleep(3600)  # Keep running

asyncio.run(main())
```

### Ví Dụ 3: Rate Limiting Demo

```python
import asyncio
from disapi import Client

async def bulk_operations():
    """Thực hiện nhiều request - rate limiter xử lý tự động"""
    async with Client("token") as client:
        await client.login()
        
        tasks = []
        for i in range(50):
            tasks.append(
                client.messages.send("channel_id", f"Message {i}")
            )
        
        # Rate limiter tự động xử lý 429
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"✅ Sent {len(results)} messages")

asyncio.run(bulk_operations())
```

### Ví Dụ 4: Proxy & Custom Headers

```python
from disapi import Client, ClientOptions

options = ClientOptions(
    proxy="http://127.0.0.1:8080",  # HTTP proxy
    timeout=60.0,                    # Request timeout
    max_retries=5,                   # Retry on rate limit
    debug=True,                      # Log HTTP requests
)

async with Client("token", options=options) as client:
    await client.login()
    # Mọi request sẽ đi qua proxy
```

### Ví Dụ 5: Exception Handling

```python
from disapi import Client
from disapi.exceptions import (
    InvalidToken,
    RateLimited,
    Forbidden,
    NotFound,
    HTTPException,
)

async def safe_message_send():
    try:
        async with Client("token") as client:
            await client.login()
            await client.messages.send("channel_id", "Hello")
    
    except InvalidToken:
        print("❌ Token không hợp lệ")
    
    except RateLimited as e:
        print(f"⏱️ Rate limited! Retry in {e.retry_after}s")
    
    except Forbidden:
        print("❌ Không có quyền truy cập")
    
    except NotFound:
        print("❌ Channel không tồn tại")
    
    except HTTPException as e:
        print(f"❌ HTTP {e.status}: {e.message}")

import asyncio
asyncio.run(safe_message_send())
```

---

## 📖 API Reference

### Client (Async)

```python
async with Client("token") as client:
    # Authentication
    user = await client.login()              # Đăng nhập
    await client.logout()                    # Đăng xuất
    
    # Current User
    me = await client.get_current_user()     # Lấy thông tin hiện tại
    
    # Messages
    msg = await client.messages.send("ch_id", "content")
    await client.messages.edit("ch_id", "msg_id", "new content")
    await client.messages.delete("ch_id", "msg_id")
    await client.messages.bulk_delete("ch_id", ["id1", "id2"])
    
    # Users
    user = await client.users.get_profile("user_id")
    await client.users.get_mutual_friends("user_id")
    
    # Guilds
    guild = await client.guilds.get("guild_id")
    await client.guilds.leave("guild_id")
    
    # Presence
    await client.presence.set_status("online")        # online, idle, dnd, invisible
    await client.presence.set_custom_status("Away")   # Custom status
    await client.presence.set_activity("PLAYING", "Game")
    
    # Gateway
    await client.connect_gateway()
    await client.disconnect_gateway()
```

### SyncClient (Synchronous)

```python
with SyncClient("token") as client:
    user = client.login()                    # Tất cả giống async, nhưng blocking
    msg = client.messages.send("ch_id", "hi")
    client.presence.set_custom_status("Away")
```

### Models

```python
from disapi.models import User, Guild, Channel, Message

# Tất cả models là TypedDict hoặc dataclass
user: User = await client.get_current_user()
print(user.id)
print(user.username)
print(user.discriminator)
```

### Exceptions

```python
from disapi.exceptions import (
    DisapiException,          # Base
    InvalidToken,             # Token format lỗi
    LoginFailure,             # Login thất bại
    RateLimited,              # 429 Too Many Requests
    Unauthorized,             # 401 Invalid token
    Forbidden,                # 403 No permission
    NotFound,                 # 404 Not found
    ServerError,              # 5xx Discord server error
    ConnectionClosed,         # Gateway disconnected
)
```

---

## 🏗️ Kiến Trúc

```
disapi/
├── __init__.py                 # Package entry point, TOS warning
├── client.py                   # Client (async) + SyncClient
├── http_client.py              # HTTP layer (httpx)
├── gateway.py                  # WebSocket Gateway
├── rate_limiter.py             # Smart rate limiting
├── constants.py                # API endpoints, enums, fingerprinting
├── exceptions.py               # Exception hierarchy
├── types.py                    # Type definitions (TypedDict, Snowflake, etc.)
├── utils.py                    # Utilities (nonce, validation, etc.)
│
├── api/                        # Discord API modules
│   ├── __init__.py
│   ├── messages.py             # POST/EDIT/DELETE messages
│   ├── guilds.py               # Guild operations
│   ├── channels.py             # Channel operations
│   ├── users.py                # User operations
│   ├── presence.py             # Set status/activity
│   ├── reactions.py            # React to messages
│   ├── relationships.py        # Friends/blocks
│   └── misc.py                 # Other endpoints
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── user.py                 # User model
│   ├── guild.py                # Guild model
│   ├── channel.py              # Channel model
│   ├── message.py              # Message model
│   ├── presence.py             # Presence model
│   └── ...
│
├── examples/                   # Ví dụ
│   ├── basic.py                # Basic usage
│   ├── gateway.py              # Gateway example
│   └── advanced.py             # Advanced features
│
├── tests/                      # Unit tests
├── docs/                       # Sphinx documentation
├── pyproject.toml              # Project metadata (build, dependencies)
├── requirements.txt            # Pip dependencies
├── .gitignore                  # Git ignore patterns
└── README.md                   # Tài liệu này
```

### Luồng Request

```
User Code
   ↓
Client / SyncClient
   ↓
API Modules (messages, users, etc.)
   ↓
HTTPClient (routing, headers)
   ↓
RateLimiter (per-bucket/global)
   ↓
httpx.AsyncClient (HTTP/2, pooling)
   ↓
Discord API
```

---

## ⚙️ Cấu Hình Nâng Cao

### ClientOptions

```python
from disapi import Client, ClientOptions

options = ClientOptions(
    # HTTP Configuration
    proxy="http://127.0.0.1:8080",  # Proxy URL (optional)
    timeout=30.0,                   # Request timeout (seconds)
    max_retries=5,                  # Retry on rate limit/5xx
    
    # Logging
    debug=True,                     # Log HTTP requests/responses
    log_level=logging.DEBUG,        # Logging level
    
    # Gateway
    enable_gateway=True,            # Enable WebSocket
    gateway_intents=33281,          # Intents bitmask
    auto_reconnect=True,            # Reconnect on disconnect
    heartbeat_interval=0,           # 0 = auto-detect
    
    # Warnings
    suppress_warnings=False,        # Suppress TOS warning on import
)

async with Client("token", options=options) as client:
    ...
```

### Rate Limiter Configuration

Rate limiter tự động xử lý:
- **Global limit**: 50 requests/second
- **Per-bucket limit**: Từ response headers
- **Backoff strategy**: Exponential backoff + full jitter
- **Retry attempts**: Configurable via `max_retries`

```python
# Tự động, không cần cấu hình thêm
# Nhưng có thể truy cập:
rate_limiter = client.http.rate_limiter
remaining = rate_limiter.get_bucket("/channels/{id}/messages").remaining
```

### Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Disapi loggers
logging.getLogger("disapi.http").setLevel(logging.DEBUG)
logging.getLogger("disapi.gateway").setLevel(logging.DEBUG)
logging.getLogger("disapi.ratelimit").setLevel(logging.DEBUG)
```

---

## 🔧 Khắc Phục Sự Cố

### 1. InvalidToken Error

```
InvalidToken: Token format is invalid
```

**Giải pháp:**
- Kiểm tra token không trống: `len(token) > 0`
- Token phải là string: `isinstance(token, str)`
- Không có dấu cách thừa: `token.strip()`

```python
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN", "").strip()
if not token:
    raise ValueError("DISCORD_TOKEN not set in .env")
```

### 2. RateLimited (429)

```
RateLimited: retry_after=5.0
```

**Giải pháp:**
- Bình thường rate limiter tự động xử lý ✅
- Nếu vẫn bị, giảm số concurrent requests
- Dùng proxy để phân tán requests

```python
# ❌ Quá nhanh
for i in range(100):
    await client.messages.send("ch_id", f"Message {i}")

# ✅ Đúng cách
import asyncio
tasks = [client.messages.send("ch_id", f"Msg {i}") for i in range(100)]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. Unauthorized (401)

```
Unauthorized: Invalid or expired token
```

**Giải pháp:**
- Token đã hết hạn → regenerate từ Discord
- Token sai → kiểm tra lại
- Có thể bị rate limit global từ Discord

```python
# Kiểm tra token trước
try:
    user = await client.login()
except Unauthorized:
    print("Token không hợp lệ hoặc hết hạn")
```

### 4. Gateway Connection Issues

```
ConnectionClosed: WebSocket disconnected
```

**Giải pháp:**
- Kiểm tra internet connection
- `auto_reconnect=True` sẽ tự động retry
- Xem log chi tiết: `debug=True`

```python
options = ClientOptions(
    enable_gateway=True,
    auto_reconnect=True,
    debug=True,
)
```

### 5. Proxy Not Working

```
NetworkError: Proxy connection failed
```

**Giải pháp:**
- Kiểm tra proxy URL format: `http://host:port` hoặc `socks5://...`
- Proxy phải chạy và accessible
- Kiểm tra firewall

```python
# Test proxy
import httpx
try:
    async with httpx.AsyncClient(proxy="http://127.0.0.1:8080") as c:
        r = await c.get("https://discord.com")
        print(r.status_code)
except Exception as e:
    print(f"Proxy error: {e}")
```

### 6. Type Checking Errors

```
error: Argument 1 to "send" has incompatible type
```

**Giải pháp:**
- Đảm bảo type hints đúng
- Dùng type checker: `mypy disapi/`

```python
# ✅ Đúng
msg = await client.messages.send("123", "content")

# ❌ Sai
msg = await client.messages.send(123, 456)  # IDs phải là str
```

---

## 🤝 Contribution

Đóng góp được chào đón!

1. Fork repo
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m "Add amazing feature"`
4. Push: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📝 License

MIT License — xem [LICENSE](LICENSE) file

---

## 🙏 Cảm Ơn

- **Discord.py**: Inspiration cho API design
- **httpx**: Async HTTP client
- **websockets**: WebSocket support
- **Community**: Feedback và đóng góp

---

## ⚠️ Tuyên Bố Từ Chối Trách Nhiệm Cuối Cùng

**KHÔNG SỬ DỤNG SAI CÁCH.**

Thư viện này là một tool giáo dục. Tác giả:
- ❌ Không hỗ trợ hoặc khuyến khích việc vi phạm ToS
- ❌ Không chịu trách nhiệm nếu tài khoản bị ban
- ❌ Không bảo hành cho bất kỳ hệ quả nào

**Discord có thể:**
- Phát hiện và chặn tài khoản mà không cảnh báo
- Thay đổi API bất cứ lúc nào
- Cập nhật anti-bot detection

**Sử dụng hoàn toàn tại rủi ro của bạn.**

---

<div align="center">

Made with ❤️ for the Python Discord community

[⭐ Star on GitHub](https://github.com/Minhdeptrai13/Disapi) • 
[🐛 Report Issues](https://github.com/Minhdeptrai13/Disapi/issues) • 
[💬 Discussions](https://github.com/Minhdeptrai13/Disapi/discussions)

</div>
