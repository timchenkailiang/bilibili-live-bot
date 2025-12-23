"""
MVP Bilibili Live Bot - Simple Version
=======================================

⚠️ THIS IS THE OLD/SIMPLE VERSION FOR REFERENCE ONLY ⚠️

For production use, see: app.py (Adapter Pattern Architecture)

This file demonstrates:
- ❌ Tight coupling to blivedm (hard to replace)
- ❌ Direct dependency on external library
- ✅ Simple and easy to understand
- ✅ Good for learning and quick prototypes

Use this if:
- You're learning Python/blivedm basics
- Quick prototype/testing (< 1 week)
- Don't care about replacing blivedm later

For production/long-term projects, use the adapter pattern version:
- app.py (application logic)
- bilibili_adapter.py (blivedm wrapper)
- domain_models.py (your data models)
- livestream_interface.py (abstract interface)

See QUICKSTART.md for detailed comparison.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Set, Optional

import blivedm
from blivedm import (
    BLiveClient,
    BaseHandler,
    DanmakuMessage,
    GiftMessage,
    GuardBuyMessage,
    SuperChatMessage,
)


# ---------- 你的统一事件模型（后面扩展很舒服） ----------
@dataclass
class UserStats:
    gift_count_today: int = 0
    gift_value_today: float = 0.0
    last_seen_ts: float = 0.0


@dataclass
class BotState:
    processed_ids: Set[str] = field(default_factory=set)           # 去重
    user_stats: Dict[int, UserStats] = field(default_factory=dict) # user_id -> stats


state = BotState()


def today_key() -> str:
    # MVP 先不做跨天清理，你后续可以每天0点重置或按日期分桶
    return time.strftime("%Y-%m-%d", time.localtime())


def dedup(event_id: str) -> bool:
    """返回 True 表示新事件，False 表示重复。"""
    if not event_id:
        return True
    if event_id in state.processed_ids:
        return False
    state.processed_ids.add(event_id)
    # 防止集合无限长：简单粗暴定期清理（MVP够用）
    if len(state.processed_ids) > 200000:
        state.processed_ids.clear()
    return True


def get_user_stat(uid: int) -> UserStats:
    if uid not in state.user_stats:
        state.user_stats[uid] = UserStats()
    return state.user_stats[uid]


# ---------- 事件处理 ----------
class MyHandler(BaseHandler):
    # 弹幕
    def _on_danmaku(self, client: BLiveClient, message: DanmakuMessage):
        uid = int(message.uid)
        uname = message.uname
        content = message.msg

        st = get_user_stat(uid)
        st.last_seen_ts = time.time()

        print(f"[DANMU] {uname}({uid}): {content}")

    # 普通礼物
    def _on_gift(self, client: BLiveClient, message: GiftMessage):
        # message.gift_name, message.num, message.uid, message.uname
        uid = int(message.uid)
        uname = message.uname
        gift_name = message.gift_name
        count = int(message.num or 1)

        # 事件去重：不同消息类型可能字段不同，MVP先用时间+uid+礼物拼一个
        event_id = f"gift:{message.timestamp}:{uid}:{gift_name}:{count}"
        if not dedup(event_id):
            return

        st = get_user_stat(uid)
        st.gift_count_today += count
        st.last_seen_ts = time.time()

        # 价格有时拿不到（取决于消息字段），MVP先只统计次数
        print(f"[GIFT] {uname}({uid}) sent {count} x {gift_name} | today_gifts={st.gift_count_today}")

    # 上舰（大航海）
    def _on_guard_buy(self, client: BLiveClient, message: GuardBuyMessage):
        uid = int(message.uid)
        uname = message.username
        guard_level = message.guard_level  # 1总督 2提督 3舰长（具体映射你后面可再做）
        num = int(message.num or 1)

        event_id = f"guard:{message.start_time}:{uid}:{guard_level}:{num}"
        if not dedup(event_id):
            return

        print(f"[GUARD] {uname}({uid}) bought guard level={guard_level} x{num}")

    # SC / 醒目留言
    def _on_super_chat(self, client: BLiveClient, message: SuperChatMessage):
        uid = int(message.uid)
        uname = message.uname
        price = float(message.price)
        content = message.message

        event_id = f"sc:{message.id}:{uid}"
        if not dedup(event_id):
            return

        st = get_user_stat(uid)
        st.gift_value_today += price
        st.last_seen_ts = time.time()

        print(f"[SC] {uname}({uid}) ¥{price}: {content} | today_value={st.gift_value_today:.2f}")


async def main():
    # ✅ 改成你要监听的直播间房间号（浏览器 URL 里能看到）
    room_id = 32581508

    # 可选：如果你发现某些房间“未登录”拿不到完整事件，可以加 cookie（更稳定）
    # sessdata = "你的SESSDATA"   # 从浏览器 Cookie 拿（注意保护隐私，不要提交到仓库）
    # client = blivedm.BLiveClient(room_id, sessdata=sessdata)

    client = blivedm.BLiveClient(room_id)

    handler = MyHandler()
    client.add_handler(handler)

    print(f"Connecting to room {room_id} ...")
    client.start()

    try:
        # 一直跑
        while True:
            await asyncio.sleep(60)
            # 你也可以在这里做周期性打印榜单/清理等
            # print(f"users tracked={len(state.user_stats)}")
    finally:
        client.stop()


if __name__ == "__main__":
    asyncio.run(main())
