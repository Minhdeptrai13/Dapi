"""
examples/advanced.py - Ví dụ Nâng Cao
====================================

Hiển thị các tính năng nâng cao: rate limiting, proxy, error handling.
"""

import asyncio
import os
from dotenv import load_dotenv
from disapi import Client, ClientOptions
from disapi.exceptions import (
    InvalidToken,
    RateLimited,
    Unauthorized,
    Forbidden,
    NotFound,
    HTTPException,
)


async def advanced_examples():
    """Ví dụ về các tính năng nâng cao."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL_ID", "your_channel_id")
    
    if not token:
        print("❌ Set DISCORD_TOKEN trong .env")
        return
    
    # ─── Ví dụ 1: Proxy Support ──────────────────────────────────────────
    print("1️⃣ Proxy Configuration Example")
    print("-" * 50)
    
    options = ClientOptions(
        proxy="http://127.0.0.1:8080",  # HTTP proxy
        timeout=60.0,
        max_retries=5,
        debug=True,
    )
    
    async with Client(token, options=options) as client:
        await client.login()
        print("✅ Connected via proxy\n")
    
    # ─── Ví dụ 2: Error Handling ─────────────────────────────────────────
    print("2️⃣ Error Handling Example")
    print("-" * 50)
    
    async with Client(token) as client:
        await client.login()
        
        try:
            # Thử gửi tin nhắn đến channel không tồn tại
            await client.messages.send("invalid_channel_id", "Hello")
        except NotFound as e:
            print(f"❌ Not Found: {e.message}")
        except Forbidden as e:
            print(f"❌ Forbidden: {e.message}")
        except RateLimited as e:
            print(f"⏱️ Rate limited: retry in {e.retry_after}s")
        except HTTPException as e:
            print(f"❌ HTTP {e.status}: {e.message}\n")
    
    # ─── Ví dụ 3: Bulk Operations & Rate Limiting ─────────────────────────
    print("3️⃣ Bulk Operations (Rate Limiting Demo)")
    print("-" * 50)
    
    async with Client(token) as client:
        await client.login()
        
        print("Sending 10 messages concurrently...")
        tasks = []
        for i in range(10):
            tasks.append(
                client.messages.send(channel_id, f"Message {i+1} 🔢")
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count
        
        print(f"✅ Success: {success_count}")
        if error_count > 0:
            print(f"❌ Errors: {error_count}\n")
    
    # ─── Ví dụ 4: Timeout Handling ────────────────────────────────────────
    print("4️⃣ Timeout Configuration")
    print("-" * 50)
    
    options = ClientOptions(
        timeout=5.0,  # 5 second timeout
    )
    
    async with Client(token, options=options) as client:
        await client.login()
        print("✅ Client configured with 5s timeout\n")
    
    # ─── Ví dụ 5: Debug Logging ──────────────────────────────────────────
    print("5️⃣ Debug Logging Example")
    print("-" * 50)
    
    options = ClientOptions(debug=True)
    
    async with Client(token, options=options) as client:
        await client.login()
        print("✅ Debug mode enabled (check console for detailed logs)\n")
    
    # ─── Ví dụ 6: Token Validation ───────────────────────────────────────
    print("6️⃣ Token Validation")
    print("-" * 50)
    
    try:
        client = Client("")  # Invalid token
    except InvalidToken as e:
        print(f"❌ Token validation failed: {e.message}\n")
    
    print("✅ Tất cả ví dụ nâng cao hoàn thành!")


if __name__ == "__main__":
    print("═" * 60)
    print("Disapi - Advanced Examples")
    print("═" * 60 + "\n")
    
    asyncio.run(advanced_examples())
