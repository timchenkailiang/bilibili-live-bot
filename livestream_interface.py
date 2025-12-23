"""
Abstract interface for live stream platforms
This defines what ANY live stream adapter must provide
"""
from abc import ABC, abstractmethod
from typing import Protocol, Callable
from domain_models import ChatMessage, GiftEvent, SuperChatEvent, GuardPurchaseEvent


class LiveStreamEventHandler(Protocol):
    """
    Protocol defining what events handlers should implement
    Your application code implements this, not the adapter
    """
    
    def on_chat_message(self, message: ChatMessage) -> None:
        """Called when a chat message is received"""
        ...
    
    def on_gift(self, gift: GiftEvent) -> None:
        """Called when a gift is received"""
        ...
    
    def on_super_chat(self, sc: SuperChatEvent) -> None:
        """Called when a super chat is received"""
        ...
    
    def on_guard_purchase(self, guard: GuardPurchaseEvent) -> None:
        """Called when someone purchases guard/captain"""
        ...
    
    def on_connection_error(self, error: Exception) -> None:
        """Called when connection fails"""
        ...


class LiveStreamAdapter(ABC):
    """
    Abstract base class for any live streaming platform adapter.
    
    Today: BilibiliAdapter (using blivedm)
    Tomorrow: Could be TwitchAdapter, YouTubeAdapter, etc.
    """
    
    @abstractmethod
    async def connect(self, room_id: str) -> None:
        """
        Connect to a live stream room
        
        Args:
            room_id: Platform-specific room identifier
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the live stream"""
        pass
    
    @abstractmethod
    def add_handler(self, handler: LiveStreamEventHandler) -> None:
        """
        Register an event handler
        
        Args:
            handler: Object implementing LiveStreamEventHandler protocol
        """
        pass
    
    @abstractmethod
    def remove_handler(self, handler: LiveStreamEventHandler) -> None:
        """Remove an event handler"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start receiving events"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop receiving events"""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected"""
        pass
