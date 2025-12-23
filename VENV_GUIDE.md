# Virtual Environment Strategy Guide

## Understanding What's Shared vs. Separate

### ✅ SHARED (Automatically)
- **Python interpreter** - Symlinked from system Python
- **No duplication** - Only one Python installation on your Mac

### 📦 SEPARATE (By Design)
- **All pip packages** - Each venv has its own copy
- **Why?** - Prevents version conflicts between projects

---

## Strategy: What to Share, What to Separate

### 🌍 Install GLOBALLY (Shared across all projects):
Use `pipx` for command-line tools you use everywhere:

```bash
# Install pipx once
brew install pipx
pipx ensurepath

# Install global tools (each in isolated environment!)
pipx install black        # Code formatter
pipx install flake8       # Linter  
pipx install mypy         # Type checker
pipx install httpie       # HTTP client
pipx install ipython      # Better Python REPL

# Now these work anywhere, but won't conflict!
black --version   # ✅ Works in any directory
```

### 🔒 Install in VENV (Project-specific):
Libraries and packages specific to your project:

```bash
# Activate your project venv
source .venv/bin/activate

# Install project dependencies
pip install blivedm      # Bilibili library
pip install aiohttp      # Async HTTP
pip install requests     # HTTP library
pip install pandas       # Data analysis (if needed)
```

---

## Decision Tree: Where to Install?

```
Is it a CLI tool? (black, flake8, pytest, etc.)
├─ YES → Use pipx (global but isolated)
└─ NO → Is it used by your code?
    ├─ YES → Install in venv (pip install)
    └─ NO → Don't install it
```

### Examples:

| Package | Where? | Why? |
|---------|--------|------|
| `black` | pipx | CLI tool, use everywhere |
| `flake8` | pipx | CLI tool, use everywhere |
| `blivedm` | venv | Library for your code |
| `requests` | venv | Library for your code |
| `ipython` | pipx | Better REPL, use everywhere |
| `pytest` | Could be either! | CLI tool, but version might matter per project |

---

## Your Current Setup (Bbot)

### Recommended Changes:

1. **Keep in venv** (already done ✅):
   ```bash
   # .venv/lib/python3.13/site-packages/
   blivedm
   aiohttp
   aiosignal
   # ... etc
   ```

2. **Move to pipx** (if you want these tools globally):
   ```bash
   # Currently not installed, but when you need them:
   pipx install black
   pipx install flake8
   pipx install pytest
   ```

---

## Quick Commands

### Check what's in your venv:
```bash
source .venv/bin/activate
pip list
```

### Check global pipx tools:
```bash
pipx list
```

### Check system Python:
```bash
which python3
python3 --version
```

### Verify venv is using symlinked Python:
```bash
ls -la .venv/bin/python*
# Should show: python3.13 -> /opt/homebrew/...
```

---

## Space Optimization Tips

1. **Delete old venvs** when project is done:
   ```bash
   rm -rf /path/to/old-project/.venv
   ```

2. **Find all venvs** on your Mac:
   ```bash
   find ~/Documents/Code -name ".venv" -type d
   ```

3. **Check their sizes**:
   ```bash
   find ~/Documents/Code -name ".venv" -type d -exec du -sh {} \;
   ```

4. **Use pipx for tools** - Installs once, works everywhere

---

## Real-World Example

### Bad Approach (Everything in venv):
```bash
# Project A
cd ~/project-a
source .venv/bin/activate
pip install black flake8 blivedm
# Total: 25 MB

# Project B  
cd ~/project-b
source .venv/bin/activate
pip install black flake8 requests
# Total: 25 MB

# Total waste: black + flake8 duplicated!
```

### Good Approach (Split tools and libraries):
```bash
# Install tools once with pipx
pipx install black    # 10 MB, shared!
pipx install flake8   # 5 MB, shared!

# Project A
cd ~/project-a
source .venv/bin/activate
pip install blivedm   # 10 MB only
# Total: 10 MB

# Project B
cd ~/project-b  
source .venv/bin/activate
pip install requests  # 10 MB only
# Total: 10 MB

# Total space: 10 (pipx) + 10 + 10 = 30 MB
# vs. 50 MB with bad approach!
```

---

## Summary

✅ **Python**: Always shared (symlink)  
✅ **CLI Tools**: Use `pipx` (installed once, work everywhere)  
✅ **Libraries**: Use `venv` (isolated per project)  
✅ **Result**: Best isolation + minimal duplication!
