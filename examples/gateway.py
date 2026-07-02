"""
examples/gateway.py - Ví dụ Gateway WebSocket
==============================================

Hiển thị cách kết nối Gateway và lắng nghe sự kiện.
"""

import asyncio
import os
from dotenv import load_dotenv
from disapi import Client, ClientOptions


async def gateway_example():
    """Ví dụ kết nối Gateway và lắng nghe sự kiện."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ Set DISCORD_TOKEN trong .env")
        return
    
    # Tạo client với Gateway enabled
    options = ClientOptions(
        enable_gateway=True,
        debug=True,  # Log debug info
    )
    
    client = Client(token, options=options)
    
    # Đăng ký event handlers
    @client.event("ready")
    async def on_ready(event):
        print(f"\n🟢 Gateway READY!")
        print(f"   Version: {event['d'].get('v')}")
        print(f"   Session ID: {event['d'].get('session_id')}")
        print(f"   Guilds: {len(event['d'].get('guilds', []))}")
    
    @client.event("message_create")
    async def on_message(event):
        msg = event['d']
        author = msg.get('author', {})
        print(f"📨 Message from {author.get('username')}: {msg.get('content')}")
    
    @client.event("presence_update")
    async def on_presence_update(event):
        user = event['d'].get('user', {})
        status = event['d'].get('status')
        print(f"👤 Presence: {user.get('username')} -> {status}")
    
    @client.event("channel_update")
    async def on_channel_update(event):
        channel = event['d']
        print(f"📝 Channel updated: {channel.get('name')}")
    
    async with client:
        print("🔗 Connecting to Discord...")
        await client.login()
        
        print("🔗 Connecting to Gateway...")
        await client.connect_gateway()
        
        print("\n✅ Gateway connected! Listening for events...")
        print("   (Ctrl+C to stop)\n")
        
        try:
            # Keep the bot running for 1 hour
            await asyncio.sleep(3600)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")


if __name__ == "__main__":
    print("═" * 60)
    print("Disapi - Gateway Example")
    print("═" * 60 + "\n")
    
    asyncio.run(gateway_example())
