# Architecture Diagram

## 🎯 The Adapter Pattern in Action

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR APPLICATION                         │
│                            (app.py)                              │
│                                                                  │
│  class LiveStreamBot(LiveStreamEventHandler):                   │
│      def on_gift(self, gift: GiftEvent):  # Domain model!      │
│          stats = self.get_user_stats(gift.user_id)             │
│          stats.total += gift.value_in_cny                       │
│                                                                  │
│  ✅ Knows NOTHING about blivedm                                 │
│  ✅ Works with YOUR models                                      │
│  ✅ Platform-independent                                        │
└─────────────────────────────────────────────────────────────────┘
                               ↕
                        [Interface]
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                    ABSTRACT INTERFACE                            │
│                 (livestream_interface.py)                        │
│                                                                  │
│  class LiveStreamAdapter(ABC):                                  │
│      @abstractmethod                                            │
│      async def connect(room_id: str): ...                       │
│      @abstractmethod                                            │
│      def add_handler(handler): ...                              │
│                                                                  │
│  class LiveStreamEventHandler(Protocol):                        │
│      def on_gift(gift: GiftEvent): ...                         │
│                                                                  │
│  ✅ Defines the CONTRACT                                        │
│  ✅ Any adapter must implement this                             │
└─────────────────────────────────────────────────────────────────┘
                               ↕
                        [Implements]
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                     BILIBILI ADAPTER                             │
│                   (bilibili_adapter.py)                          │
│                                                                  │
│  class BilibiliAdapter(LiveStreamAdapter):                      │
│      def __init__(self):                                        │
│          self._client = BLiveClient(...)  # blivedm!           │
│                                                                  │
│      def _translate_gift(blivedm_gift):                         │
│          # Transform: blivedm format → YOUR format             │
│          return GiftEvent(                                      │
│              user_id=int(blivedm_gift.uid),                    │
│              gift_name=str(blivedm_gift.gift_name),            │
│              value_in_cny=calculate(blivedm_gift.price)        │
│          )                                                      │
│                                                                  │
│  ⚠️ ONLY file that imports blivedm                             │
│  ✅ Translates blivedm → domain models                         │
│  ✅ Replaceable without touching app.py                        │
└─────────────────────────────────────────────────────────────────┘
                               ↕
                          [Uses]
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                        BLIVEDM LIBRARY                           │
│                   (External, replaceable)                        │
│                                                                  │
│  from blivedm import BLiveClient, GiftMessage                   │
│                                                                  │
│  ❌ Unofficial, reverse-engineered                              │
│  ❌ Can break anytime                                           │
│  ❌ Might be abandoned                                          │
│  ✅ But your app is PROTECTED via adapter!                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Example: Gift Event

```
1. Bilibili server sends WebSocket data
   ↓
2. blivedm library receives and parses
   → Creates: GiftMessage(uid=123, gift_name="火箭", price=1000, ...)
   ↓
3. BilibiliAdapter._BilivedmHandler intercepts
   ↓
4. Adapter validates data:
   ✅ uid exists? 
   ✅ gift_name valid?
   ✅ price is number?
   ↓
5. Adapter translates to domain model:
   blivedm.GiftMessage → domain_models.GiftEvent
   {
     user_id: 123,              # Your naming
     gift_name: "火箭",         # Validated
     value_in_cny: 1.0,         # Your calculation (1000/1000)
     coin_type: CoinType.GOLD   # Your enum
   }
   ↓
6. Adapter notifies all handlers:
   handler.on_gift(gift_event)
   ↓
7. Your app receives clean domain event:
   def on_gift(self, gift: GiftEvent):
       # No idea this came from blivedm!
       # Just a clean GiftEvent object
       self.update_stats(gift.user_id, gift.value_in_cny)
```

---

## 🛡️ Protection Layers

```
Your App Logic
    ↑ Clean domain models only
    ├─ GiftEvent (your format)
    ├─ ChatMessage (your format)
    └─ SuperChatEvent (your format)
    
Translation Layer (Adapter)
    ↑ Validates and converts
    ├─ Null checks
    ├─ Type conversions
    ├─ Error handling
    └─ Format translation
    
External Library (blivedm)
    ↑ Raw, unvalidated data
    ├─ Can have None values
    ├─ Can have wrong types
    ├─ Can change format
    └─ Can break anytime
```

---

## 🔀 Swapping Adapters

### Scenario: blivedm dies, you want to use `bili-live-api`

```
┌──────────────┐              ┌──────────────┐
│   app.py     │              │   app.py     │
│ (unchanged!) │              │ (unchanged!) │
└──────┬───────┘              └──────┬───────┘
       │                             │
       ↓                             ↓
┌──────────────┐              ┌──────────────┐
│ BilibiliAdapter │  REPLACE  │ NewLibAdapter│
│ uses blivedm │    ────→     │ uses bili-live│
└──────┬───────┘              └──────┬───────┘
       │                             │
       ↓                             ↓
┌──────────────┐              ┌──────────────┐
│   blivedm    │              │ bili-live-api│
│   (dead ❌)  │              │   (works ✅) │
└──────────────┘              └──────────────┘
```

**Changes needed:**
1. Create `NewLibAdapter` implementing `LiveStreamAdapter`
2. Update 1 line in `app.py` to import new adapter
3. Done! ✅

---

## 🧪 Testing Benefits

### Without Adapter (Old Way):
```python
# Hard to test - requires real network connection
def test_gift_processing():
    # Need actual Bilibili connection
    client = blivedm.BLiveClient(123456)  # Network required!
    # How to send fake gift? 😰
```

### With Adapter (New Way):
```python
# Easy to test - no network needed!
class MockAdapter(LiveStreamAdapter):
    def send_fake_gift(self):
        fake_gift = GiftEvent(
            user_id=999,
            gift_name="Test Gift",
            value_in_cny=10.0
        )
        for handler in self._handlers:
            handler.on_gift(fake_gift)

# Test without network! ✅
def test_gift_processing():
    bot = LiveStreamBot()
    adapter = MockAdapter()
    adapter.add_handler(bot)
    adapter.send_fake_gift()
    
    assert bot.state.user_stats[999].gift_value_today == 10.0
```

---

## 📊 Complexity vs. Benefits

```
Complexity:
  Simple (mvp):     ███░░░░░░░ 30%
  Adapter Pattern:  ███████░░░ 70%

Maintainability:
  Simple (mvp):     ███░░░░░░░ 30%
  Adapter Pattern:  █████████░ 90%

Replaceability:
  Simple (mvp):     █░░░░░░░░░ 10%
  Adapter Pattern:  ██████████ 100%

Risk Management:
  Simple (mvp):     ██░░░░░░░░ 20%
  Adapter Pattern:  █████████░ 90%
```

**Trade-off:** More upfront complexity → Much better long-term

---

## 🎓 Key Design Principles Applied

### 1. Dependency Inversion Principle (DIP)
```
High-level (app.py) should NOT depend on low-level (blivedm)
Both should depend on abstractions (LiveStreamAdapter)
```

### 2. Single Responsibility Principle (SRP)
```
app.py          → Business logic only
adapter.py      → Translation only
interface.py    → Contract definition only
domain_models.py → Data structures only
```

### 3. Open/Closed Principle (OCP)
```
Open for extension:   Add new adapters easily ✅
Closed for modification: Don't touch app.py ✅
```

### 4. Interface Segregation Principle (ISP)
```
Clean, focused interfaces
No bloated "god interfaces"
```

---

## 🎯 Summary: The Core Insight

```
┌─────────────────────────────────────────┐
│  "Your app should depend on WHAT you    │
│   need, not HOW you get it"             │
│                                          │
│  WHAT: GiftEvent with user_id and value │
│  HOW:  Could be blivedm, another lib,   │
│        mock data, different platform... │
└─────────────────────────────────────────┘
```

**The adapter pattern lets you change the HOW without touching the WHAT!**

This is **professional software engineering**. 🏆
