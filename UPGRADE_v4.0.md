# Disapi v4.0 ELITE Upgrade Guide

## 🚀 What's New in v4.0

Disapi has been upgraded from v3.0 to **v4.0 ELITE** with production-grade advanced features for client & gateway management.

## 📋 Overview of Changes

### Before (v3.0)
```python
async with Client("token") as client:
    await client.login()
    msg = await client.messages.send("ch_id", "Hello!")
    # Basic connectivity, simple error handling
```

### After (v4.0 ELITE)
```python
async with Client("token") as client:
    # Event-driven architecture
    @client.event(EventType.MESSAGE_CREATE)
    async def on_message(data):
        print(f"Message: {data['content']}")
    
    @client.event(EventType.READY)
    async def on_ready(data):
        print(f"Connected as {data['user']['username']}")
    
    # Auto health checks, adaptive backoff, session recovery
    await client.login()
    
    # Access advanced metrics
    print(f"Latency: {client.latency:.1f}ms")
    print(f"Gateway: {client.gateway.avg_latency:.1f}ms avg")
```

---

## ✨ Elite Client Features (v4.0)

### 1. Event-Driven Architecture

Register events with decorators or programmatically:

```python
# Decorator style
@client.event(EventType.MESSAGE_CREATE)
async def handle_message(data):
    print(f"New message: {data['content']}")

@client.event(EventType.PRESENCE_UPDATE)
async def handle_presence(data):
    print(f"User presence: {data['user_id']}")

# Or use direct registration
async def on_guild_create(data):
    print(f"Guild: {data['name']}")

client.on(EventType.GUILD_CREATE)(on_guild_create)
```

### 2. Health Checks & Auto-Reconnect

Health checks run automatically in the background:

```python
options = ClientOptions(
    health_check_interval=30,          # Check every 30s
    auto_reconnect=True,                # Auto reconnect on failure
    max_reconnect_backoff=120,          # Max 2 minutes between retries
)

async with Client("token", options) as client:
    # Health checks run automatically
    # On failure: exponential backoff + automatic reconnection
    # Backoff: 1s → 2s → 4s → 8s → 16s → 32s → 64s → 120s
    await client.login()
```

### 3. Connection State & Metrics

Track connection health and performance:

```python
async with Client("token") as client:
    await client.login()
    
    # Get current latency
    print(f"Current latency: {client.latency * 1000:.1f}ms")
    
    # Access Gateway
    if client.gateway:
        print(f"Gateway avg latency: {client.gateway.avg_latency * 1000:.1f}ms")
        print(f"Connection uptime: {client.gateway.connection_uptime:.1f}s")
        print(f"Missed ACKs: {client.gateway.heartbeat_acks_missed}")
        print(f"Reconnect count: {client.gateway.reconnect_count}")
        print(f"Loaded guilds: {client.gateway._guilds_loaded}")
```

### 4. Advanced Options

```python
options = ClientOptions(
    proxy="http://127.0.0.1:8080",      # HTTP proxy
    timeout=30.0,                        # Request timeout
    max_retries=5,                       # Retry attempts
    debug=False,                         # Debug logging
    log_level=logging.INFO,              # Logging level
    
    # Advanced options (v4.0)
    health_check_interval=30,            # Health check every 30s
    max_reconnect_backoff=120,           # Max backoff 120s
    session_cache_size=100,              # Cache up to 100 sessions
    
    # Gateway options
    enable_gateway=True,
    gateway_intents=33281,
    auto_reconnect=True,
)

client = Client("token", options)
```

---

## 🔌 Elite Gateway Features (v4.0)

### 1. Latency Tracking

Gateway now tracks latency with historical data:

```python
gateway = client.gateway

# Current latency
print(f"Current: {gateway.latency * 1000:.1f}ms")

# Average of last 10 heartbeats
print(f"Average: {gateway.avg_latency * 1000:.1f}ms")

# Missed ACKs (health indicator)
if gateway.heartbeat_acks_missed > 0:
    print(f"⚠️ Missed {gateway.heartbeat_acks_missed} heartbeats")
```

### 2. Connection Metrics

```python
# How many times reconnected
print(f"Reconnect attempts: {gateway.reconnect_count}")

# How long connected
print(f"Uptime: {gateway.connection_uptime:.1f}s")

# Session ID and URL
print(f"Session: {gateway.session_id}")
print(f"Resume URL: {gateway._resume_url}")
```

### 3. Async Event Dispatching

Events are queued and dispatched asynchronously (non-blocking):

```python
@client.event(EventType.MESSAGE_CREATE)
async def on_message(data):
    # This runs concurrently with other handlers
    # Non-blocking, full async support
    await asyncio.sleep(1)  # Long operation
    print(f"Processed: {data['content']}")

@client.event(EventType.MESSAGE_CREATE)
async def on_message_second(data):
    # Multiple handlers run in parallel
    print(f"Also received: {data['content']}")
```

### 4. Adaptive Reconnect Backoff

Automatically manages reconnection with intelligent backoff:

```
Connection fails
    ↓ (wait 1s + jitter)
Retry 1 fails
    ↓ (wait 2s + jitter)
Retry 2 fails
    ↓ (wait 4s + jitter)
Retry 3 fails
    ↓ (wait 8s + jitter)
... (exponential growth)
    ↓ (capped at 120s)
Stable → Backoff resets to 1s
```

---

## 💡 Usage Examples

### Example 1: Simple Event Handler

```python
import asyncio
import disapi
from disapi import Client, EventType

async def main():
    client = Client("your_token_here")
    
    @client.event(EventType.READY)
    async def on_ready(data):
        print(f"✅ Logged in as {data['user']['username']}")
    
    @client.event(EventType.MESSAGE_CREATE)
    async def on_message(data):
        content = data.get("content", "")
        if content.startswith("!ping"):
            await client.messages.send(
                data["channel_id"],
                f"🏓 Pong! Latency: {client.latency * 1000:.1f}ms"
            )
    
    async with client:
        await client.login()
        if client.gateway:
            await client.gateway.connect()

asyncio.run(main())
```

### Example 2: Health Monitoring

```python
async def main():
    options = disapi.ClientOptions(
        health_check_interval=10,
        auto_reconnect=True,
    )
    
    async with Client("token", options) as client:
        @client.event(EventType.READY)
        async def on_ready(data):
            print("Connected!")
        
        await client.login()
        
        # Monitor health
        for _ in range(60):
            await asyncio.sleep(1)
            gw = client.gateway
            if gw:
                print(
                    f"Uptime: {gw.connection_uptime:.1f}s | "
                    f"Latency: {gw.latency*1000:.1f}ms | "
                    f"Avg: {gw.avg_latency*1000:.1f}ms | "
                    f"Reconnects: {gw.reconnect_count}"
                )
```

### Example 3: Presence Management

```python
async def main():
    async with Client("token") as client:
        await client.login()
        
        gw = client.gateway
        if gw:
            # Set status
            await gw.set_status("online")
            
            # Set activity
            await gw.set_activity(
                "Disapi v4.0 ELITE",
                activity_type=disapi.ActivityType.PLAYING
            )
            
            # Set custom status
            await gw.set_custom_status(
                "🚀 Running Disapi v4.0",
                emoji_name="🚀"
            )
            
            await gw.connect()
```

---

## 📊 Performance Improvements

### v4.0 ELITE Advantages

| Feature | v3.0 | v4.0 |
|---------|------|------|
| Event System | ❌ | ✅ Decorator-based |
| Health Checks | ❌ | ✅ Background loop |
| Latency Tracking | Basic | ✅ 10-sample history |
| Auto-Reconnect | Basic | ✅ Adaptive backoff |
| Connection Pooling | ❌ | ✅ Session caching |
| Event Dispatching | Sync | ✅ Async queue-based |
| Metrics | Limited | ✅ Detailed (uptime, ACKs, etc) |
| Error Recovery | Basic | ✅ Advanced |

---

## 🔧 Configuration Reference

### ClientOptions (v4.0)

```python
class ClientOptions:
    # Network
    proxy: Optional[str] = None                    # Proxy URL
    timeout: float = 30.0                          # Request timeout (s)
    max_retries: int = 5                           # Retry count
    
    # Logging
    debug: bool = False                            # Debug mode
    log_level: int = logging.INFO                  # Log level
    suppress_warnings: bool = False                # Suppress TOS warning
    
    # Gateway
    enable_gateway: bool = True                    # Enable WebSocket
    gateway_intents: int = 33281                   # Intent bitmask
    auto_reconnect: bool = True                    # Auto-reconnect
    heartbeat_interval: int = 0                    # Manual heartbeat (0=auto)
    
    # Health & Recovery (NEW in v4.0)
    health_check_interval: int = 30                # Health check every 30s
    max_reconnect_backoff: int = 120               # Max backoff 120s
    session_cache_size: int = 100                  # Cache size
```

---

## 🛡️ Error Handling (Enhanced)

```python
try:
    async with Client("token") as client:
        await client.login()
except disapi.InvalidToken:
    print("Invalid token!")
except disapi.LoginFailure:
    print("Login failed!")
except disapi.RateLimited as e:
    print(f"Rate limited, retry in {e.retry_after}s")
except disapi.ServerError:
    print("Discord server error, will auto-retry")
```

---

## ⚡ Migration Guide (v3.0 → v4.0)

### Code Changes Required

**v3.0:**
```python
async with Client("token") as client:
    await client.login()
    msg = await client.messages.send("ch_id", "Hello")
```

**v4.0:** (backward compatible!)
```python
async with Client("token") as client:
    await client.login()
    msg = await client.messages.send("ch_id", "Hello")
    
    # NEW: Access events
    @client.event(EventType.MESSAGE_CREATE)
    async def on_msg(data):
        pass
```

✅ **Fully backward compatible** - existing code works without changes!

---

## 📈 Performance Tips

### Tip 1: Use Event Queue Over Polling

❌ Bad (polling):
```python
while True:
    msg = await get_message()  # Wasteful
    await asyncio.sleep(0.1)
```

✅ Good (events):
```python
@client.event(EventType.MESSAGE_CREATE)
async def on_message(data):
    pass  # Called immediately when event arrives
```

### Tip 2: Configure Health Checks

```python
# For low-latency environments
options = ClientOptions(health_check_interval=60)  # Less frequent

# For unreliable connections
options = ClientOptions(health_check_interval=10)  # More frequent
```

### Tip 3: Monitor Metrics

```python
# Health check loop
while True:
    await asyncio.sleep(5)
    gw = client.gateway
    if gw and gw.heartbeat_acks_missed > 2:
        print("⚠️ Possible connection issue!")
```

---

## 🐛 Troubleshooting

### Issue: Too many missed heartbeat ACKs

**Symptom:**
```
⚠️ Error in heartbeat loop: Too many missed heartbeat ACKs
```

**Solutions:**
1. Check network stability
2. Increase `health_check_interval` (reduce frequency)
3. Check Discord server status
4. Try different proxy

### Issue: Frequent reconnects

**Symptom:**
```
Reconnecting in 32.5s (attempt 6)…
```

**Solutions:**
1. Reduce `health_check_interval` if too aggressive
2. Check token validity
3. Monitor latency with `gateway.avg_latency`
4. Check for rate limiting

### Issue: Event handlers not firing

**Symptom:**
```
@client.event() decorator registered but handler not called
```

**Solutions:**
1. Ensure `enable_gateway=True` in options
2. Ensure `await gateway.connect()` is called
3. Check `client.event()` vs `gateway.on()` - use client version
4. Enable debug logging: `log_level=logging.DEBUG`

---

## 📚 Related Files

- [README.md](README.md) - Vietnamese documentation
- [examples/basic.py](examples/basic.py) - Basic usage
- [examples/gateway.py](examples/gateway.py) - Gateway events
- [examples/advanced.py](examples/advanced.py) - Advanced features

---

## 🎯 Summary

**Disapi v4.0 ELITE brings:**
- ✅ Event-driven architecture with decorators
- ✅ Advanced health checks & auto-recovery
- ✅ Detailed performance metrics
- ✅ Async event dispatching
- ✅ Connection pooling & session management
- ✅ Production-grade reliability

**Fully backward compatible with v3.0** - upgrade today! 🚀

---

**Version:** 4.0 ELITE  
**Release Date:** 2026-07-02  
**Status:** Production-Ready ✅
