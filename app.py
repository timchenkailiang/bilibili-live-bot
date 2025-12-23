"""
Application logic - Completely independent of blivedm or any specific platform
This code works with ANY adapter (Bilibili, Twitch, YouTube, etc.)
"""
import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Set

from livestream_interface import LiveStreamAdapter, LiveStreamEventHandler
from domain_models import ChatMessage, GiftEvent, SuperChatEvent, GuardPurchaseEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------- Application State (Platform-independent) ----------
@dataclass
class UserStats:
    """Statistics for a single user"""
    gift_count_today: int = 0
    gift_value_today: float = 0.0
    chat_count_today: int = 0
    last_seen_ts: float = 0.0


@dataclass
class BotState:
    """Global application state"""
    processed_event_ids: Set[str] = field(default_factory=set)
    user_stats: Dict[int, UserStats] = field(default_factory=dict)


# ---------- Application Logic ----------
class LiveStreamBot(LiveStreamEventHandler):
    """
    Your application logic.
    
    This class knows NOTHING about blivedm, Bilibili, or any specific platform.
    It only works with domain models (ChatMessage, GiftEvent, etc.)
    """
    
    def __init__(self):
        self.state = BotState()
    
    def _dedup(self, event_id: str) -> bool:
        """Check if event is duplicate"""
        if not event_id:
            return True
        if event_id in self.state.processed_event_ids:
            return False
        self.state.processed_event_ids.add(event_id)
        
        # Prevent unbounded growth
        if len(self.state.processed_event_ids) > 200000:
            logger.warning("Clearing event dedup cache (reached 200k)")
            self.state.processed_event_ids.clear()
        
        return True
    
    def _get_user_stats(self, user_id: int) -> UserStats:
        """Get or create user stats"""
        if user_id not in self.state.user_stats:
            self.state.user_stats[user_id] = UserStats()
        return self.state.user_stats[user_id]
    
    # ========== Event Handlers ==========
    # These receive domain events, NOT platform-specific data
    
    def on_chat_message(self, message: ChatMessage) -> None:
        """Handle chat message"""
        try:
            stats = self._get_user_stats(message.user_id)
            stats.chat_count_today += 1
            stats.last_seen_ts = time.time()
            
            logger.info(
                f"[CHAT] {message.username}({message.user_id}): {message.content}"
            )
        except Exception as e:
            logger.error(f"Error handling chat message: {e}", exc_info=True)
    
    def on_gift(self, gift: GiftEvent) -> None:
        """Handle gift event"""
        try:
            # Deduplicate
            event_id = f"gift:{gift.timestamp}:{gift.user_id}:{gift.gift_name}:{gift.quantity}"
            if not self._dedup(event_id):
                logger.debug(f"Duplicate gift event: {event_id}")
                return
            
            # Update stats
            stats = self._get_user_stats(gift.user_id)
            stats.gift_count_today += gift.quantity
            stats.gift_value_today += gift.value_in_cny
            stats.last_seen_ts = time.time()
            
            logger.info(
                f"[GIFT] {gift.username}({gift.user_id}) sent {gift.quantity}x {gift.gift_name} "
                f"(¥{gift.value_in_cny:.2f}) | today_total={stats.gift_count_today}"
            )
        except Exception as e:
            logger.error(f"Error handling gift: {e}", exc_info=True)
    
    def on_super_chat(self, sc: SuperChatEvent) -> None:
        """Handle super chat event"""
        try:
            # Deduplicate
            event_id = f"sc:{sc.message_id}:{sc.user_id}"
            if not self._dedup(event_id):
                logger.debug(f"Duplicate SC event: {event_id}")
                return
            
            # Update stats
            stats = self._get_user_stats(sc.user_id)
            stats.gift_value_today += sc.price_cny
            stats.last_seen_ts = time.time()
            
            logger.info(
                f"[SC] {sc.username}({sc.user_id}) ¥{sc.price_cny}: {sc.message} "
                f"| today_value=¥{stats.gift_value_today:.2f}"
            )
        except Exception as e:
            logger.error(f"Error handling super chat: {e}", exc_info=True)
    
    def on_guard_purchase(self, guard: GuardPurchaseEvent) -> None:
        """Handle guard purchase event"""
        try:
            # Deduplicate
            event_id = f"guard:{guard.timestamp}:{guard.user_id}:{guard.guard_level.value}"
            if not self._dedup(event_id):
                logger.debug(f"Duplicate guard event: {event_id}")
                return
            
            logger.info(
                f"[GUARD] {guard.username}({guard.user_id}) "
                f"bought {guard.guard_level.name} x{guard.quantity}"
            )
        except Exception as e:
            logger.error(f"Error handling guard purchase: {e}", exc_info=True)
    
    def on_connection_error(self, error: Exception) -> None:
        """Handle connection error"""
        logger.error(f"Connection error: {error}")
    
    def get_stats_summary(self) -> Dict:
        """Get summary statistics"""
        total_users = len(self.state.user_stats)
        total_gifts = sum(s.gift_count_today for s in self.state.user_stats.values())
        total_value = sum(s.gift_value_today for s in self.state.user_stats.values())
        
        return {
            "total_users": total_users,
            "total_gifts": total_gifts,
            "total_value_cny": total_value,
        }


# ---------- Main Application ----------
async def main():
    """
    Main application entry point.
    
    Notice how this code doesn't mention blivedm at all!
    We just import ANY adapter that implements LiveStreamAdapter.
    """
    
    # Configuration
    ROOM_ID = "123456"  # ← Change to your target room
    
    # Choose adapter (swap this to use different platform)
    from bilibili_adapter import BilibiliAdapter
    adapter: LiveStreamAdapter = BilibiliAdapter()
    
    # Alternative: If you later want to support Twitch, just swap the adapter:
    # from twitch_adapter import TwitchAdapter
    # adapter: LiveStreamAdapter = TwitchAdapter()
    
    # Create application logic (platform-independent!)
    bot = LiveStreamBot()
    
    # Wire up
    try:
        logger.info(f"Starting bot for room {ROOM_ID}")
        
        # Connect and start
        await adapter.connect(ROOM_ID)
        adapter.add_handler(bot)
        await adapter.start()
        
        # Main loop with health checks
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            stats = bot.get_stats_summary()
            logger.info(
                f"Bot health: {stats['total_users']} users, "
                f"{stats['total_gifts']} gifts, "
                f"¥{stats['total_value_cny']:.2f} total"
            )
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        try:
            await adapter.stop()
            await adapter.disconnect()
            logger.info("Bot shutdown complete")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
