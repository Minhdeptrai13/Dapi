"""
examples/messages.py - Ví dụ Gửi Tin Nhắn
==========================================

Hiển thị cách gửi, chỉnh sửa, xóa, và tương tác với tin nhắn.
"""

import asyncio
import os
from dotenv import load_dotenv
from disapi import Client


async def message_examples():
    """Các ví dụ về tin nhắn."""
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL_ID", "your_channel_id")
    
    if not token:
        print("❌ Set DISCORD_TOKEN trong .env")
        return
    
    async with Client(token) as client:
        await client.login()
        print("✅ Logged in\n")
        
        # 1. Gửi tin nhắn đơn giản
        print("1️⃣ Gửi tin nhắn đơn giản...")
        msg = await client.messages.send(channel_id, "Hello from Disapi! 👋")
        print(f"   ✅ Sent: {msg.id}\n")
        
        # 2. Gửi tin nhắn với Embed
        print("2️⃣ Gửi tin nhắn với Embed...")
        embed_msg = await client.messages.send(
            channel_id,
            content="Check this embed! 🎨",
            embed={
                "title": "Disapi Embed",
                "description": "This is a test embed",
                "color": 0x5865F2,  # Discord blue
                "fields": [
                    {
                        "name": "Feature 1",
                        "value": "✅ Production-grade",
                        "inline": True,
                    },
                    {
                        "name": "Feature 2",
                        "value": "✅ Async-First",
                        "inline": True,
                    },
                ],
                "footer": {"text": "Powered by disapi"},
            }
        )
        print(f"   ✅ Sent embed: {embed_msg.id}\n")
        
        # 3. Chỉnh sửa tin nhắn
        print("3️⃣ Chỉnh sửa tin nhắn...")
        edited = await client.messages.edit(
            channel_id,
            msg.id,
            "✏️ Edited message - new content!"
        )
        print(f"   ✅ Edited: {edited.id}\n")
        
        # 4. Xóa tin nhắn
        print("4️⃣ Xóa tin nhắn...")
        await client.messages.delete(channel_id, msg.id)
        print("   ✅ Deleted\n")
        
        # 5. Gửi tin nhắn nhiều dòng
        print("5️⃣ Gửi tin nhắn multi-line...")
        multiline = await client.messages.send(
            channel_id,
            "Line 1\nLine 2\nLine 3"
        )
        print(f"   ✅ Sent: {multiline.id}\n")
        
        print("✅ Tất cả ví dụ hoàn thành!")


if __name__ == "__main__":
    print("═" * 60)
    print("Disapi - Message Examples")
    print("═" * 60 + "\n")
    
    asyncio.run(message_examples())
