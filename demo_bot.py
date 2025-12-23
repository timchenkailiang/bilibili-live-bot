"""
DEMO: Mock Bilibili Bot - Shows how it works without network
This simulates what happens when the bot receives events
"""
import asyncio
import time
from mvp_blive_bot import MyHandler, state, BotState
from blivedm import DanmakuMessage, GiftMessage, SuperChatMessage, GuardBuyMessage

# Reset state for demo
state.processed_ids.clear()
state.user_stats.clear()

print("="*60)
print("🎬 DEMO: Bilibili Live Bot Simulation")
print("="*60)
print("This shows what would happen when events arrive...")
print()

# Simulate incoming events
handler = MyHandler()

# Mock client (not needed for demo, but handler expects it)
class MockClient:
    pass

client = MockClient()

# 1. Simulate chat messages
print("📢 Simulating chat messages...")
msg1 = DanmakuMessage()
msg1.uid = 123456
msg1.uname = "测试用户A"
msg1.msg = "主播好！"
msg1.timestamp = int(time.time() * 1000)

msg2 = DanmakuMessage()
msg2.uid = 789012
msg2.uname = "测试用户B"  
msg2.msg = "支持主播！"
msg2.timestamp = int(time.time() * 1000)

handler._on_danmaku(client, msg1)
handler._on_danmaku(client, msg2)
print()

# 2. Simulate gifts
print("🎁 Simulating gift events...")
gift1 = GiftMessage()
gift1.uid = 123456
gift1.uname = "测试用户A"
gift1.gift_name = "辣条"
gift1.num = 5
gift1.timestamp = int(time.time())

gift2 = GiftMessage()
gift2.uid = 789012
gift2.uname = "测试用户B"
gift2.gift_name = "小心心"
gift2.num = 10
gift2.timestamp = int(time.time())

handler._on_gift(client, gift1)
handler._on_gift(client, gift2)
print()

# 3. Simulate Super Chat
print("💬 Simulating Super Chat...")
sc = SuperChatMessage()
sc.uid = 123456
sc.uname = "测试用户A"
sc.price = 50
sc.message = "加油！继续努力！"
sc.id = 9999

handler._on_super_chat(client, sc)
print()

# 4. Simulate Guard purchase
print("🚢 Simulating Guard purchase...")
guard = GuardBuyMessage()
guard.uid = 789012
guard.username = "测试用户B"
guard.guard_level = 3  # 舰长
guard.num = 1
guard.start_time = int(time.time())

handler._on_guard_buy(client, guard)
print()

# Show final stats
print("="*60)
print("📊 Final Statistics:")
print("="*60)
for uid, stats in state.user_stats.items():
    print(f"User {uid}:")
    print(f"  - Gifts today: {stats.gift_count_today}")
    print(f"  - Value today: ¥{stats.gift_value_today:.2f}")
    print(f"  - Last seen: {time.strftime('%H:%M:%S', time.localtime(stats.last_seen_ts))}")
    print()

print("="*60)
print("✅ Demo complete!")
print()
print("💡 This shows how your bot WOULD work when connected.")
print("⚠️  Currently, blivedm can't connect due to Bilibili API changes.")
print("✨  This is why the Adapter Pattern (app.py) is important!")
print("="*60)
