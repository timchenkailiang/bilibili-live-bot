"""
Bilibili adapter implementation using blivedm library
This is the ONLY file that knows about blivedm
If blivedm breaks or gets replaced, only THIS file changes
"""
import logging
import time
from typing import List, Optional

import blivedm
from blivedm import (
    BLiveClient,
    BaseHandler,
    DanmakuMessage,
    GiftMessage,
    SuperChatMessage,
    GuardBuyMessage,
)

from livestream_interface import LiveStreamAdapter, LiveStreamEventHandler
from domain_models import (
    ChatMessage,
    GiftEvent,
    SuperChatEvent,
    GuardPurchaseEvent,
    CoinType,
    GuardLevel,
)

logger = logging.getLogger(__name__)


class BilibiliAdapter(LiveStreamAdapter):
    """
    Adapter for Bilibili live streaming platform using blivedm library.
    
    This isolates blivedm from the rest of your application.
    If blivedm is replaced, only this class changes.
    """
    
    def __init__(self, session_data: Optional[str] = None):
        """
        Initialize Bilibili adapter
        
        Args:
            session_data: Optional SESSDATA cookie for authentication
        """
        self._client: Optional[BLiveClient] = None
        self._session_data = session_data
        self._handlers: List[LiveStreamEventHandler] = []
        self._internal_handler: Optional['_BilivedmHandler'] = None
        self._connected = False
    
    async def connect(self, room_id: str) -> None:
        """Connect to a Bilibili room"""
        try:
            room_id_int = int(room_id)
        except ValueError:
            raise ValueError(f"Bilibili room_id must be numeric, got: {room_id}")
        
        if self._session_data:
            self._client = BLiveClient(room_id_int, session=self._session_data)
        else:
            self._client = BLiveClient(room_id_int)
        
        # Create internal handler that bridges blivedm to our interface
        self._internal_handler = _BilivedmHandler(self._handlers)
        self._client.add_handler(self._internal_handler)
        
        self._connected = True
        logger.info(f"Connected to Bilibili room {room_id}")
    
    async def disconnect(self) -> None:
        """Disconnect from Bilibili"""
        if self._client:
            self._client.stop()
            self._client = None
            self._connected = False
            logger.info("Disconnected from Bilibili")
    
    def add_handler(self, handler: LiveStreamEventHandler) -> None:
        """Register an event handler"""
        if handler not in self._handlers:
            self._handlers.append(handler)
            logger.debug(f"Added handler: {handler.__class__.__name__}")
    
    def remove_handler(self, handler: LiveStreamEventHandler) -> None:
        """Remove an event handler"""
        if handler in self._handlers:
            self._handlers.remove(handler)
            logger.debug(f"Removed handler: {handler.__class__.__name__}")
    
    async def start(self) -> None:
        """Start receiving events"""
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        self._client.start()
        logger.info("Started receiving events from Bilibili")
    
    async def stop(self) -> None:
        """Stop receiving events"""
        if self._client:
            self._client.stop()
            logger.info("Stopped receiving events from Bilibili")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected and self._client is not None


class _BilivedmHandler(BaseHandler):
    """
    Internal handler that translates blivedm events into domain events.
    This is the "translation layer" between blivedm and our domain.
    """
    
    def __init__(self, handlers: List[LiveStreamEventHandler]):
        super().__init__()
        self._handlers = handlers
    
    def _notify_handlers(self, method_name: str, *args, **kwargs):
        """Notify all registered handlers"""
        for handler in self._handlers:
            try:
                method = getattr(handler, method_name, None)
                if method:
                    method(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in handler {handler.__class__.__name__}.{method_name}: {e}",
                    exc_info=True
                )
    
    def _on_danmaku(self, client: BLiveClient, message: DanmakuMessage):
        """Translate blivedm danmaku to ChatMessage"""
        try:
            # Validate required fields
            if not message.uid or not message.uname or not message.msg:
                logger.warning("Danmaku missing required fields, skipping")
                return
            
            # Translate to domain model
            chat_msg = ChatMessage(
                user_id=int(message.uid),
                username=str(message.uname),
                content=str(message.msg),
                timestamp=float(message.timestamp) if message.timestamp else time.time(),
                user_level=int(message.user_level) if message.user_level is not None else None,
                medal_name=str(message.medal_name) if message.medal_name else None,
                is_admin=bool(message.admin) if message.admin else False,
                is_vip=bool(message.vip or message.svip) if (message.vip or message.svip) else False,
            )
            
            # Notify application handlers
            self._notify_handlers('on_chat_message', chat_msg)
            
        except Exception as e:
            logger.error(f"Failed to process danmaku: {e}", exc_info=True)
    
    def _on_gift(self, client: BLiveClient, message: GiftMessage):
        """Translate blivedm gift to GiftEvent"""
        try:
            # Validate required fields
            if not message.uid or not message.uname or not message.gift_name:
                logger.warning("Gift missing required fields, skipping")
                return
            
            # Parse coin type
            coin_type = CoinType.UNKNOWN
            if message.coin_type:
                try:
                    coin_type = CoinType(str(message.coin_type).lower())
                except ValueError:
                    coin_type = CoinType.UNKNOWN
            
            # Parse guard level
            guard_level = GuardLevel.NONE
            if message.guard_level:
                try:
                    guard_level = GuardLevel(int(message.guard_level))
                except ValueError:
                    guard_level = GuardLevel.NONE
            
            # Translate to domain model
            gift_event = GiftEvent(
                user_id=int(message.uid),
                username=str(message.uname),
                gift_name=str(message.gift_name),
                quantity=int(message.num) if message.num else 1,
                coin_type=coin_type,
                total_value=int(message.total_coin) if message.total_coin else 0,
                timestamp=float(message.timestamp) if message.timestamp else time.time(),
                unit_price=int(message.price) if message.price else None,
                guard_level=guard_level,
            )
            
            # Notify application handlers
            self._notify_handlers('on_gift', gift_event)
            
        except Exception as e:
            logger.error(f"Failed to process gift: {e}", exc_info=True)
    
    def _on_super_chat(self, client: BLiveClient, message: SuperChatMessage):
        """Translate blivedm super chat to SuperChatEvent"""
        try:
            # Validate required fields
            if not message.uid or not message.uname:
                logger.warning("SuperChat missing required fields, skipping")
                return
            
            # Translate to domain model
            sc_event = SuperChatEvent(
                user_id=int(message.uid),
                username=str(message.uname),
                message=str(message.message) if message.message else "",
                price_cny=float(message.price) if message.price else 0.0,
                message_id=int(message.id) if message.id else 0,
                timestamp=float(message.start_time) if message.start_time else time.time(),
                duration_seconds=int(message.time) if message.time else None,
            )
            
            # Notify application handlers
            self._notify_handlers('on_super_chat', sc_event)
            
        except Exception as e:
            logger.error(f"Failed to process super chat: {e}", exc_info=True)
    
    def _on_guard_buy(self, client: BLiveClient, message: GuardBuyMessage):
        """Translate blivedm guard buy to GuardPurchaseEvent"""
        try:
            # Validate required fields
            if not message.uid or not message.username:
                logger.warning("GuardBuy missing required fields, skipping")
                return
            
            # Parse guard level
            guard_level = GuardLevel.NONE
            if message.guard_level:
                try:
                    guard_level = GuardLevel(int(message.guard_level))
                except ValueError:
                    guard_level = GuardLevel.NONE
            
            # Translate to domain model
            guard_event = GuardPurchaseEvent(
                user_id=int(message.uid),
                username=str(message.username),
                guard_level=guard_level,
                quantity=int(message.num) if message.num else 1,
                price=int(message.price) if message.price else 0,
                timestamp=float(message.start_time) if message.start_time else time.time(),
            )
            
            # Notify application handlers
            self._notify_handlers('on_guard_purchase', guard_event)
            
        except Exception as e:
            logger.error(f"Failed to process guard purchase: {e}", exc_info=True)
