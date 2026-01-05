# 🎯 Claude Model Switching Guide

Complete guide to switching between Claude models in the AI Website Builder.

---

## 🚀 Current Configuration

**✅ You are now using: Claude Opus 4** (`claude-opus-4-20250514`)

---

## 📊 Available Models

| Model | ID | Best For | Speed | Cost | Quality |
|-------|-------|----------|-------|------|---------|
| **Claude Opus 4** | `claude-opus-4-20250514` | Best quality websites | Slower | $$$ | ⭐⭐⭐⭐⭐ |
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | Balanced performance | Medium | $$ | ⭐⭐⭐⭐ |
| **Claude Haiku 3.5** | `claude-3-5-haiku-20241022` | Fast generation | Fast | $ | ⭐⭐⭐ |

---

## 🔧 Method 1: Using Environment Variable (Easiest)

### Step 1: Edit `.env` file

```bash
nano .env
```

### Step 2: Change the model

```env
# Choose one of these:
DEFAULT_CLAUDE_MODEL=claude-opus-4-20250514      # Best quality (CURRENT)
# DEFAULT_CLAUDE_MODEL=claude-sonnet-4-20250514  # Balanced
# DEFAULT_CLAUDE_MODEL=claude-3-5-haiku-20241022 # Fastest
```

### Step 3: Restart AI Engine

```bash
docker compose restart ai_engine
```

**Done!** The new model will be used immediately.

---

## 🔧 Method 2: Direct Code Change

### Edit `ai_engine/config.py`

```python
# Line 55: Change the default value
DEFAULT_CLAUDE_MODEL: str = os.getenv("DEFAULT_CLAUDE_MODEL", "claude-opus-4-20250514")
```

Change the second parameter to any model ID from the table above.

Then restart:
```bash
docker compose restart ai_engine
```

---

## 🔧 Method 3: Per-Request Model Selection (Advanced)

### Modify the generator to accept model parameter

In `ai_engine/services/claude_website_generator.py`, you can add:

```python
def __init__(self, model: str = None):
    self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    self.model = model or settings.DEFAULT_CLAUDE_MODEL
```

Then in `ai_engine/routers/build_website.py`:

```python
# Use Opus for complex requests
if len(data.user_prompt) > 100:
    generator = ClaudeWebsiteGenerator(model=settings.CLAUDE_MODEL_OPUS)
else:
    generator = ClaudeWebsiteGenerator(model=settings.CLAUDE_MODEL_SONNET)
```

---

## 📊 Model Comparison

### Claude Opus 4 (Current) ⭐⭐⭐⭐⭐
**Best for:**
- Complex, multi-section websites
- High-quality design requirements
- Professional portfolios
- When quality matters most

**Performance:**
- Generation time: 40-60 seconds
- Output quality: Exceptional
- HTML structure: Perfect
- Design aesthetics: Outstanding

**Cost:** ~3x more than Sonnet

---

### Claude Sonnet 4 ⭐⭐⭐⭐
**Best for:**
- Most use cases
- Good balance of speed and quality
- Production deployments
- Cost-conscious projects

**Performance:**
- Generation time: 30-45 seconds
- Output quality: Excellent
- HTML structure: Very good
- Design aesthetics: Very good

**Cost:** Balanced

---

### Claude Haiku 3.5 ⭐⭐⭐
**Best for:**
- Quick prototypes
- Simple landing pages
- High-volume generation
- Development/testing

**Performance:**
- Generation time: 15-25 seconds
- Output quality: Good
- HTML structure: Good
- Design aesthetics: Good

**Cost:** ~6x cheaper than Opus

---

## 🧪 Testing Different Models

### Quick Test Script

```bash
# Test with current model
curl -X POST http://localhost:8001/api/build/website \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","user_prompt":"Create a modern portfolio"}'
```

The response will show which model was used:
```json
{
  "model": "claude-opus-4-20250514",
  "execution_time": 45.2
}
```

---

## ⚙️ Advanced: Dynamic Model Selection

### Based on Request Complexity

Add this logic to `build_website.py`:

```python
# Intelligent model selection
def select_model(user_prompt: str, username: str) -> str:
    # Use Opus for detailed requests
    if len(user_prompt) > 200:
        return settings.CLAUDE_MODEL_OPUS

    # Use Haiku for quick tests
    if username.startswith("test"):
        return settings.CLAUDE_MODEL_HAIKU

    # Default to Sonnet
    return settings.CLAUDE_MODEL_SONNET

# In the endpoint:
model = select_model(data.user_prompt, data.username)
generator = ClaudeWebsiteGenerator(model=model)
```

---

## 📈 Cost Estimation

Based on typical website generation (3000 input tokens, 6000 output tokens):

| Model | Cost per Website | Cost per 100 Websites |
|-------|-----------------|----------------------|
| **Opus 4** | ~$0.45 | ~$45 |
| **Sonnet 4** | ~$0.15 | ~$15 |
| **Haiku 3.5** | ~$0.07 | ~$7 |

*Approximate costs - check Anthropic pricing for exact rates*

---

## ✅ Verification

### Check which model is currently active:

```bash
# Check environment variable
cat .env | grep DEFAULT_CLAUDE_MODEL

# Check config
docker exec ai_website_builder_ai_engine python -c "from config import settings; print(f'Model: {settings.DEFAULT_CLAUDE_MODEL}')"

# Generate a test website and check response
curl -X POST http://localhost:8001/api/build/website \
  -H "Content-Type: application/json" \
  -d '{"username":"test","user_prompt":"test"}' \
  | jq '.model'
```

---

## 🎯 Recommendations

### For Production:
- **Start with Sonnet 4** (balanced)
- Monitor quality and costs
- Switch to Opus 4 for premium users
- Use Haiku 3.5 for previews/tests

### For Development:
- **Use Haiku 3.5** (fast, cheap)
- Switch to Sonnet/Opus for final testing

### For Demos:
- **Use Opus 4** (best impression)
- Showcase highest quality

---

## 🔄 Quick Switch Commands

```bash
# Switch to Opus (best quality)
echo "DEFAULT_CLAUDE_MODEL=claude-opus-4-20250514" >> .env
docker compose restart ai_engine

# Switch to Sonnet (balanced)
echo "DEFAULT_CLAUDE_MODEL=claude-sonnet-4-20250514" >> .env
docker compose restart ai_engine

# Switch to Haiku (fastest)
echo "DEFAULT_CLAUDE_MODEL=claude-3-5-haiku-20241022" >> .env
docker compose restart ai_engine
```

---

## 📝 Current Status

✅ **Active Model:** Claude Opus 4 (`claude-opus-4-20250514`)
✅ **Configuration:** Set in `.env` file
✅ **Applied to:** Website generation + editing
✅ **Restart required:** Yes (already done)

---

## 🎉 You're All Set!

Your system is now using **Claude Opus 4** - the most powerful model!

**Try it now in your browser:**
1. Enter any username
2. Click "Quick Generate"
3. See the exceptional quality!

The generated websites will have:
- 🎨 Superior design aesthetics
- 💎 Perfect code structure
- ⚡ Smooth animations
- 📱 Flawless responsive design
- ✨ Outstanding attention to detail

---

**Need help?** Check the main README.md or run `./start.sh` to ensure everything is running.
