# Architecture: Adapter Pattern for Replaceable Dependencies

## 🎯 Core Principle

**`blivedm` is treated as a REPLACEABLE component behind a clean interface.**

If `blivedm` breaks, gets abandoned, or you want to switch platforms → **only ONE file changes**.

---

## 📁 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   app.py                            │
│            (Your Application Logic)                 │
│   - Knows NOTHING about blivedm or Bilibili        │
│   - Works with domain models only                   │
│   - Could work with ANY live stream platform        │
└─────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────┐
│            livestream_interface.py                   │
│              (Abstract Interface)                    │
│   - Defines what ANY adapter must provide           │
│   - LiveStreamAdapter (ABC)                         │
│   - LiveStreamEventHandler (Protocol)               │
└─────────────────────────────────────────────────────┘
                         ↑ implements
┌─────────────────────────────────────────────────────┐
│            bilibili_adapter.py                       │
│       (Bilibili-specific Implementation)             │
│   - ONLY file that imports blivedm                  │
│   - Translates blivedm events → domain events       │
│   - If blivedm breaks, ONLY THIS FILE changes       │
└─────────────────────────────────────────────────────┘
                         ↓ uses
┌─────────────────────────────────────────────────────┐
│                  blivedm                             │
│              (External Library)                      │
│   - Can be replaced without affecting app.py        │
└─────────────────────────────────────────────────────┘
```

---

## 📂 File Responsibilities

### 1. `domain_models.py` - Your Business Models
**What it does:**
- Defines YOUR application's understanding of events
- Independent of ANY platform (Bilibili, Twitch, YouTube)
- These are the "truth" for your application

**Key classes:**
- `ChatMessage` - A chat message
- `GiftEvent` - A gift/donation
- `SuperChatEvent` - A paid highlighted message
- `GuardPurchaseEvent` - A subscription/membership

**Dependencies:** NONE (pure Python)

```python
# This is YOUR model, not blivedm's
@dataclass
class GiftEvent:
    user_id: int
    gift_name: str
    value_in_cny: float  # Your calculation, your format
```

---

### 2. `livestream_interface.py` - The Contract
**What it does:**
- Defines the interface that ALL adapters must implement
- Abstract base class that enforces the contract
- Protocol for event handlers

**Key classes:**
- `LiveStreamAdapter` (ABC) - What an adapter must provide
- `LiveStreamEventHandler` (Protocol) - What your app must implement

**Dependencies:** Only `domain_models.py`

```python
class LiveStreamAdapter(ABC):
    @abstractmethod
    async def connect(self, room_id: str) -> None:
        pass
    # ... any adapter MUST implement these methods
```

---

### 3. `bilibili_adapter.py` - The Bilibili Implementation
**What it does:**
- Implements `LiveStreamAdapter` for Bilibili
- Wraps `blivedm` library
- Translates blivedm data → domain models
- **ONLY file that knows about blivedm**

**Key classes:**
- `BilibiliAdapter` - Main adapter implementation
- `_BilivedmHandler` - Internal bridge (private)

**Dependencies:** `blivedm`, `livestream_interface`, `domain_models`

**🎯 Critical Point:** If `blivedm` breaks → only edit THIS file!

```python
# Translates blivedm's format to YOUR format
def _on_gift(self, client, message: GiftMessage):
    gift_event = GiftEvent(  # Your domain model
        user_id=int(message.uid),  # blivedm's format
        gift_name=str(message.gift_name),
        # ... translation logic
    )
    self._notify_handlers('on_gift', gift_event)
```

---

### 4. `app.py` - Your Application
**What it does:**
- Contains your business logic
- Implements `LiveStreamEventHandler`
- Processes events and updates state
- **Knows NOTHING about blivedm!**

**Key classes:**
- `LiveStreamBot` - Your event processor
- `BotState` - Your application state

**Dependencies:** `livestream_interface`, `domain_models` (NO blivedm!)

```python
class LiveStreamBot(LiveStreamEventHandler):
    def on_gift(self, gift: GiftEvent):  # Domain model, not blivedm!
        # Your logic here
        logger.info(f"Received gift: {gift.gift_name}")
```

---

## 🔄 Data Flow

### When a Bilibili Gift Arrives:

```
1. Bilibili Server sends WebSocket message
         ↓
2. blivedm library parses it → GiftMessage (blivedm's model)
         ↓
3. BilibiliAdapter._BilivedmHandler receives it
         ↓
4. Adapter translates: GiftMessage → GiftEvent (YOUR model)
         ↓
5. Adapter calls: handler.on_gift(gift_event)
         ↓
6. Your app receives GiftEvent (clean domain model)
         ↓
7. Your app processes it (update stats, log, etc.)
```

**Key Insight:** Your app NEVER sees `blivedm.GiftMessage`!

---

## ✅ Benefits of This Architecture

### 1. **Replaceability** 🔄
```python
# Today: Bilibili
from bilibili_adapter import BilibiliAdapter
adapter = BilibiliAdapter()

# Tomorrow: Twitch (if blivedm dies)
from twitch_adapter import TwitchAdapter
adapter = TwitchAdapter()

# Your app.py code? UNCHANGED! ✅
```

### 2. **Testability** 🧪
```python
# Create a fake adapter for testing
class MockAdapter(LiveStreamAdapter):
    def send_fake_gift(self):
        gift = GiftEvent(user_id=123, gift_name="Test", ...)
        self.notify_handlers('on_gift', gift)

# Test your app WITHOUT blivedm or network!
```

### 3. **Isolation** 🛡️
```
blivedm breaks → bilibili_adapter.py fails ❌
              → app.py still works ✅ (can use mock adapter)
              → domain_models.py unaffected ✅
              → interface.py unaffected ✅
```

### 4. **Clarity** 📖
- Each file has ONE job
- Clear boundaries
- Easy to understand
- Easy to maintain

### 5. **Flexibility** 🎨
```python
# Support MULTIPLE platforms simultaneously!
bilibili_adapter = BilibiliAdapter()
twitch_adapter = TwitchAdapter()

bot = LiveStreamBot()
bilibili_adapter.add_handler(bot)  # Same bot!
twitch_adapter.add_handler(bot)    # Same bot!

# Now bot receives events from BOTH platforms!
```

---

## 🆚 Comparison: Old vs New

### Old Architecture (mvp_blive_bot.py):
```
app.py
  → directly imports blivedm
  → uses blivedm.GiftMessage everywhere
  → tightly coupled to blivedm

If blivedm breaks:
❌ Rewrite entire app.py
❌ Change all event handlers
❌ Update all data models
```

### New Architecture (Adapter Pattern):
```
app.py
  → imports livestream_interface (abstract!)
  → uses GiftEvent (your model!)
  → loosely coupled via interface

If blivedm breaks:
✅ Edit only bilibili_adapter.py
✅ OR create new adapter (e.g., different_library_adapter.py)
✅ app.py unchanged!
```

---

## 🔧 How to Replace blivedm

### Scenario: blivedm gets abandoned, you want to use `my_new_lib`

**Steps:**

1. **Create new adapter file:**
   ```bash
   cp bilibili_adapter.py my_new_lib_adapter.py
   ```

2. **Edit `my_new_lib_adapter.py`:**
   ```python
   import my_new_lib  # Instead of blivedm
   
   class MyNewLibAdapter(LiveStreamAdapter):
       # Implement the same interface
       # Translate my_new_lib events → domain models
   ```

3. **Update `app.py` (ONE LINE):**
   ```python
   # from bilibili_adapter import BilibiliAdapter
   from my_new_lib_adapter import MyNewLibAdapter
   
   # adapter = BilibiliAdapter()
   adapter = MyNewLibAdapter()
   ```

4. **Done!** ✅
   - `app.py` logic unchanged
   - Domain models unchanged
   - Interface unchanged
   - Only adapter changed

---

## 📊 Dependency Graph

```
app.py
  ├─→ livestream_interface.py (abstract)
  ├─→ domain_models.py (your models)
  └─→ bilibili_adapter.py (concrete)
        └─→ blivedm (external, replaceable!)

Key principle:
- app.py depends on ABSTRACTIONS (interface, models)
- app.py does NOT depend on IMPLEMENTATIONS (blivedm)
```

This follows **Dependency Inversion Principle**:
> "Depend on abstractions, not concretions"

---

## 🎓 Design Patterns Used

### 1. **Adapter Pattern** 🔌
- `BilibiliAdapter` adapts `blivedm` to your interface
- Converts incompatible interfaces to compatible ones

### 2. **Strategy Pattern** 🎯
- `LiveStreamAdapter` is interchangeable
- Can swap strategies at runtime

### 3. **Observer Pattern** 👀
- Handlers register to receive events
- Loose coupling between event source and handlers

### 4. **Dependency Inversion** 🔄
- High-level (`app.py`) doesn't depend on low-level (`blivedm`)
- Both depend on abstractions (`interface.py`)

---

## 🚀 Usage Example

```python
# In app.py - notice NO mention of blivedm!

class LiveStreamBot(LiveStreamEventHandler):
    def on_gift(self, gift: GiftEvent):
        # Domain model, not platform-specific!
        print(f"{gift.username} sent {gift.gift_name}")
        print(f"Value: ¥{gift.value_in_cny}")

# Main
adapter = BilibiliAdapter()  # Could be ANY adapter!
bot = LiveStreamBot()

await adapter.connect("123456")
adapter.add_handler(bot)
await adapter.start()

# Bot receives clean domain events
# No knowledge of blivedm, websockets, protocols, etc.
```

---

## 🛡️ Risk Management

### What if blivedm changes its API?

**Impact:** 🟡 Medium  
**Affected files:** `bilibili_adapter.py` only  
**Fix time:** 1-2 hours  

### What if blivedm is abandoned?

**Impact:** 🟢 Low  
**Affected files:** Create new adapter  
**Fix time:** 4-8 hours  
**Your app logic:** UNAFFECTED ✅

### What if Bilibili changes protocol?

**Impact:** 🟡 Medium  
**Affected files:** `bilibili_adapter.py` (update translation logic)  
**Fix time:** 2-4 hours  
**Your app logic:** UNAFFECTED ✅

---

## 📝 Summary

**Key Takeaway:**
> blivedm is just ONE way to connect to Bilibili.  
> Your app doesn't care HOW it connects, only WHAT events it receives.

**Architecture:**
```
Your App (independent)
    ↓ uses
Interface (contract)
    ↑ implements
Adapter (replaceable!)
    ↓ uses
blivedm (external, swappable)
```

**Benefits:**
- ✅ Replaceable dependencies
- ✅ Testable without network
- ✅ Clear separation of concerns
- ✅ Platform-agnostic application
- ✅ Future-proof design

**This is professional-grade architecture!** 🎯
