# Bilibili Live Bot (Bbot)

A professional-grade, real-time Bilibili livestream monitoring bot with clean architecture that tracks user interactions and statistics.

## ✨ Features
- 🎯 Monitor chat messages (弹幕)
- 🎁 Track gifts and their counts with value calculation
- 🚢 Detect guard/captain subscriptions (大航海)
- 💬 Capture Super Chat messages (SC/醒目留言)
- 📊 User statistics tracking
- 🔄 Event deduplication
- 🏗️ **Adapter Pattern** - Easily replaceable dependencies
- 🧪 **Testable** - Mock adapters for testing without network
- 🔌 **Platform-agnostic** - Extensible to other streaming platforms

## 🚀 Quick Start

### 1. Create Virtual Environment (if not exists)
```bash
python3 -m venv .venv
```

### 2. Activate Virtual Environment
```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Room ID
Edit `app.py` and change the room number:
```python
ROOM_ID = "123456"  # Change to your target Bilibili room ID
```

### 5. Run the Bot
```bash
# Production-ready version (Adapter Pattern)
python app.py

# Or use the simple MVP version for learning
python mvp_blive_bot.py
```

## 🏗️ Architecture

This project uses the **Adapter Pattern** to keep `blivedm` as a replaceable dependency:

```
app.py (your logic)
  ↓ uses
livestream_interface.py (abstract contract)
  ↑ implements  
bilibili_adapter.py (blivedm wrapper)
  ↓ uses
blivedm (external, replaceable!)
```

**Key benefit:** If `blivedm` breaks or gets abandoned, you only need to update `bilibili_adapter.py`, not your entire application!

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed explanation.

## 📁 Project Structure
```
Bbot/
├── .venv/                      # Virtual environment (isolated dependencies)
│
├── Core Application (Adapter Pattern - Recommended for production)
│   ├── app.py                  # Main application (platform-independent!)
│   ├── domain_models.py        # Your business models
│   ├── livestream_interface.py # Abstract interface
│   └── bilibili_adapter.py     # Bilibili/blivedm adapter (ONLY file importing blivedm)
│
├── Reference Implementation (For learning/comparison)
│   └── mvp_blive_bot.py        # Simple version (tightly-coupled, not recommended for production)
│
├── Documentation
│   ├── README.md               # This file
│   ├── QUICKSTART.md           # Quick comparison guide
│   ├── ARCHITECTURE.md         # Detailed architecture explanation
│   ├── DIAGRAMS.md             # Visual diagrams
│   ├── VENV_GUIDE.md           # Virtual environment guide
│   └── PROJECT_STRUCTURE.md    # This project's file organization
│
└── Configuration
    ├── requirements.txt        # Python dependencies
    └── .vscode/                # VS Code settings
```

## 🎓 Learning Path

1. **Start simple:** Read and run `mvp_blive_bot.py` to understand the basics
2. **Understand the problem:** Why tight coupling to `blivedm` is risky
3. **Learn the solution:** Study the adapter pattern in `app.py`
4. **Deep dive:** Read `ARCHITECTURE.md` for full explanation

## 🔧 Advanced Usage

### Optional: Add Authentication
For more stable connection and complete event data, add your SESSDATA cookie in `app.py`:
```python
from bilibili_adapter import BilibiliAdapter
adapter = BilibiliAdapter(session_data="your_SESSDATA_here")
```

### Testing Without Network
```python
from livestream_interface import LiveStreamAdapter
from domain_models import GiftEvent

class MockAdapter(LiveStreamAdapter):
    def send_fake_event(self):
        gift = GiftEvent(user_id=123, username="Test", ...)
        # Notify handlers without real connection
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick comparison between simple and adapter versions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into the adapter pattern
- **[DIAGRAMS.md](DIAGRAMS.md)** - Visual architecture diagrams
- **[VENV_GUIDE.md](VENV_GUIDE.md)** - Virtual environment management guide

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick comparison between simple and adapter versions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into the adapter pattern
- **[DIAGRAMS.md](DIAGRAMS.md)** - Visual architecture diagrams
- **[VENV_GUIDE.md](VENV_GUIDE.md)** - Virtual environment management guide

---

## 🛠️ Development

### Deactivate Virtual Environment
When you're done working:
```bash
deactivate
```

### Activate venv every time you work:
```bash
source .venv/bin/activate
```

### Install new packages:
```bash
pip install package_name
pip freeze > requirements.txt  # Update requirements
```

### Share with others:
They just need to:
```bash
git clone <your-repo>
cd Bbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## 🎯 Why This Architecture?

**Traditional approach (mvp_blive_bot.py):**
```python
import blivedm  # ❌ Tightly coupled
# If blivedm breaks → Rewrite everything
```

**Adapter pattern approach (app.py):**
```python
# app.py knows nothing about blivedm! ✅
from livestream_interface import LiveStreamAdapter
# If blivedm breaks → Only update bilibili_adapter.py
```

**Benefits:**
- ✅ Testable (mock adapters for unit tests)
- ✅ Maintainable (clear separation of concerns)
- ✅ Flexible (easily switch libraries or platforms)
- ✅ Professional (industry-standard design pattern)

This is how production systems handle external dependencies!
