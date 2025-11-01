# Project Samarth - Plugin Architecture - Deployment Guide

## 🚀 Quick Deployment Overview

This guide covers deploying the Plugin Architecture backend API to production platforms.

**What you'll deploy:**
- FastAPI backend with plugin-based query engine
- Port: 8001 (configurable)
- Python 3.12 runtime
- Data.gov.in API integration

---

## Option 1: Deploy to Render.com (Recommended - Free Tier)

### Step 1: Prepare Your Code

1. **Push to GitHub:**
```bash
cd /Users/paritoshdwivedi/Downloads/Projects/project-samarth-plugin
git init
git add .
git commit -m "Initial commit: Plugin Architecture"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/project-samarth-plugin.git
git push -u origin main
```

2. **Create `runtime.txt` in backend folder:**
```bash
echo "python-3.12.0" > backend/runtime.txt
```

### Step 2: Deploy on Render

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `project-samarth-plugin`
   - **Environment:** `Python 3`
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Environment Variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Key: `DATAGOV_API_KEY`
   - Value: `579b464db66ec23bdd0000017e45d19883a942ae7781476b6cbd2e97`

6. Click **"Create Web Service"**

7. Wait 3-5 minutes for deployment

8. **Your API will be live at:** `https://project-samarth-plugin.onrender.com`

### Step 3: Test Deployment

```bash
# Health check
curl https://project-samarth-plugin.onrender.com/health

# Test query
curl -X POST https://project-samarth-plugin.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare rainfall in Kerala and Punjab over 3 years"}'
```

---

## Option 2: Deploy to Railway.app (Free Tier)

### Step 1: Setup Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click **"Start a New Project"** → **"Deploy from GitHub repo"**
4. Select `project-samarth-plugin`

### Step 2: Configure

1. Railway auto-detects Python
2. **Add Environment Variables:**
   - Go to Variables tab
   - Add: `DATAGOV_API_KEY=579b464db66ec23bdd0000017e45d19883a942ae7781476b6cbd2e97`

3. **Set Root Directory:**
   - Settings → Root Directory → `backend`

4. **Custom Start Command (if needed):**
   - Settings → Start Command
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Deploy

1. Click **"Deploy"**
2. Railway will build and deploy automatically
3. **Get your URL:** Settings → Domains → Generate Domain
4. Your API: `https://project-samarth-plugin.up.railway.app`

---

## Option 3: Deploy to Vercel (Serverless)

### Step 1: Create `vercel.json`

```bash
cd backend
cat > vercel.json << 'VERCEL'
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
VERCEL
```

### Step 2: Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd backend
vercel --prod

# Add environment variable
vercel env add DATAGOV_API_KEY
# Enter: 579b464db66ec23bdd0000017e45d19883a942ae7781476b6cbd2e97
```

---

## Option 4: Local with ngrok (Quick Demo)

Perfect for Loom video without permanent deployment:

```bash
# Terminal 1: Run backend
cd backend
source .venv/bin/activate
export DATAGOV_API_KEY=579b464db66ec23bdd0000017e45d19883a942ae7781476b6cbd2e97
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Expose with ngrok
brew install ngrok  # or download from ngrok.com
ngrok http 8001
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

---

## Testing Your Deployment

### Health Check
```bash
curl https://YOUR_DEPLOYED_URL/health
# Expected: {"status":"ok"}
```

### Test All 4 Plugin Types

**1. Compare Rainfall & Crops:**
```bash
curl -X POST https://YOUR_DEPLOYED_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare rainfall in Kerala and Punjab over 3 years"
  }'
```

**2. District Extremes:**
```bash
curl -X POST https://YOUR_DEPLOYED_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which district in Punjab had the highest wheat production in 2020?"
  }'
```

**3. Production Trend:**
```bash
curl -X POST https://YOUR_DEPLOYED_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show rice production trend in Tamil Nadu over 5 years"
  }'
```

**4. Policy Arguments:**
```bash
curl -X POST https://YOUR_DEPLOYED_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why should Karnataka shift from cotton to sugarcane?"
  }'
```

---

## Troubleshooting

### Build Fails

**Error: `pandas` compilation fails**
- **Cause:** Using Python 3.14 (incompatible)
- **Fix:** Ensure `runtime.txt` has `python-3.12.0`

**Error: Module not found**
- **Cause:** Requirements not installed
- **Fix:** Verify `requirements.txt` in backend folder

### Runtime Errors

**Error: API key not set**
- **Fix:** Add `DATAGOV_API_KEY` environment variable in platform settings

**Error: Port binding**
- **Fix:** Ensure start command uses `--port $PORT` (not hardcoded 8001)

### Slow First Request

- **Normal:** First query loads datasets from data.gov.in
- **Expected:** 5-10 seconds on first request
- **After:** <1 second (cached in memory)

---

## Architecture Highlights for Demo

When showing your deployed API, highlight:

### 1. Plugin Registry
```bash
# Show logs on Render/Railway
# Look for: "Registered 4 plugins: compare_rainfall_and_crops, ..."
```

### 2. Plugin Routing
- Each query goes to different plugin
- No coupling between plugins
- Debug response shows which plugin handled it

### 3. Production Features
✅ **Error Handling:** Graceful failures with error messages
✅ **Data Fallback:** Local CSV if API is slow
✅ **Caching:** In-memory data cache
✅ **Citations:** Every answer cites data.gov.in sources

---

## Platform Comparison

| Platform | Free Tier | Cold Start | Custom Domain | Logs |
|----------|-----------|------------|---------------|------|
| **Render** | Yes (750hrs/mo) | ~30s | Yes | Excellent |
| **Railway** | Yes ($5 credit) | ~20s | Yes | Good |
| **Vercel** | Yes | <1s (serverless) | Yes | Limited |
| **ngrok** | Yes (temp URL) | None | No | Local only |

**Recommendation:** 
- **Render** for permanent deployment
- **ngrok** for quick Loom demo

---

## Loom Video Checklist

**Before Recording:**
- [ ] API deployed and health check passing
- [ ] Test all 4 query types successfully
- [ ] Copy deployment URL
- [ ] Open logs panel (to show plugin execution)

**During Demo:**
- [ ] Show deployed URL in browser/Postman
- [ ] Run 2-3 queries showing different plugins
- [ ] Point to debug field showing plugin name
- [ ] Show logs with plugin registration
- [ ] Mention production-ready features

**Script:**
"This is deployed on [Render/Railway] at [URL]. Let me show you the plugin system in action. Notice in the logs how each query is routed to a different plugin - compare_rainfall_and_crops for this one, district_extremes for that one. The beauty of this architecture is I can add a 5th plugin tomorrow without touching any existing code."

---

## Next Steps After Deployment

1. **Add monitoring:** Use Render/Railway built-in metrics
2. **Set up alerts:** Get notified of errors
3. **Add rate limiting:** Prevent abuse
4. **Enable HTTPS:** Automatically handled by platforms
5. **Custom domain:** Point your domain to deployment

---

## Production Checklist

✅ **Deployed:** API accessible via HTTPS
✅ **Environment Variables:** API key configured
✅ **Health Check:** `/health` endpoint responding
✅ **All Plugins Working:** 4/4 query types functional
✅ **Logs Visible:** Can monitor plugin execution
✅ **Error Handling:** Graceful failures
✅ **Performance:** <1s response time (after cache)

**You're production-ready!** 🚀
