"""
examples/basic.py - Ví dụ Cơ Bản
================================

Hiển thị cách sử dụng Disapi một cách đơn giản nhất.
"""

import asyncio
import os
from dotenv import load_dotenv
from disapi import Client, SyncClient


# ─── Async Example ───────────────────────────────────────────────────────────

async def async_example():
    """Ví dụ async cơ bản."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ Vui lòng set DISCORD_TOKEN trong .env")
        return
    
    async with Client(token) as client:
        # Đăng nhập
        user = await client.login()
        print(f"✅ Logged in as {user.username}#{user.discriminator}")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Verified: {user.verified}")
        
        # Lấy thông tin hiện tại
        me = await client.get_current_user()
        print(f"\n📝 Current User: {me.username}")
        
        # Thiết lập trạng thái
        await client.presence.set_status("online")
        await client.presence.set_custom_status("Using disapi ⚡")
        print("✅ Presence set")


# ─── Sync Example ────────────────────────────────────────────────────────────

def sync_example():
    """Ví dụ sync - dễ hơn cho người mới bắt đầu."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ Vui lòng set DISCORD_TOKEN trong .env")
        return
    
    with SyncClient(token) as client:
        user = client.login()
        print(f"✅ Logged in as {user.username}")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 60)
    print("Disapi - Discord User API Wrapper")
    print("═" * 60)
    
    # Chọn async hay sync
    choice = input("\nChọn mode:\n1. Async (Recommended)\n2. Sync\n> ").strip()
    
    if choice == "1":
        print("\n🚀 Running async example...")
        asyncio.run(async_example())
    elif choice == "2":
        print("\n🚀 Running sync example...")
        sync_example()
    else:
        print("❌ Lựa chọn không hợp lệ")
