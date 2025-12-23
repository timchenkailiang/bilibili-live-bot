"""
Core domain models - Independent of any external library
These represent YOUR application's understanding of live stream events
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class CoinType(Enum):
    """Currency type for gifts"""
    GOLD = "gold"  # Paid currency (1000 gold = ¥1)
    SILVER = "silver"  # Free currency
    UNKNOWN = "unknown"


class GuardLevel(Enum):
    """Guard/Captain subscription levels"""
    NONE = 0
    GOVERNOR = 1  # 总督
    ADMIRAL = 2   # 提督
    CAPTAIN = 3   # 舰长


@dataclass
class ChatMessage:
    """
    Domain model for a chat message (弹幕)
    This is YOUR definition, not blivedm's
    """
    user_id: int
    username: str
    content: str
    timestamp: float
    
    # Optional enrichment data
    user_level: Optional[int] = None
    medal_name: Optional[str] = None
    is_admin: bool = False
    is_vip: bool = False


@dataclass
class GiftEvent:
    """
    Domain model for a gift event
    """
    user_id: int
    username: str
    gift_name: str
    quantity: int
    coin_type: CoinType
    total_value: int  # In coins (瓜子)
    timestamp: float
    
    # Optional data
    unit_price: Optional[int] = None
    guard_level: GuardLevel = GuardLevel.NONE
    
    @property
    def value_in_cny(self) -> float:
        """Calculate value in Chinese Yuan"""
        if self.coin_type == CoinType.GOLD:
            return self.total_value / 1000.0
        return 0.0


@dataclass
class SuperChatEvent:
    """
    Domain model for Super Chat (醒目留言)
    """
    user_id: int
    username: str
    message: str
    price_cny: float  # Price in Chinese Yuan
    message_id: int
    timestamp: float
    
    # Optional data
    duration_seconds: Optional[int] = None


@dataclass
class GuardPurchaseEvent:
    """
    Domain model for guard/captain subscription
    """
    user_id: int
    username: str
    guard_level: GuardLevel
    quantity: int
    price: int  # In gold coins
    timestamp: float
