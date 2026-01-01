# 🚀 Deployment Steps - Get Your CDL Dashboard Live

## Quick Overview

With the refresh button system, deployment is **much simpler** than before! No GitHub Actions, no scheduled jobs - just deploy and run.

**Time to Deploy:** ~15 minutes  
**Cost:** $0 (using free tiers)  
**Difficulty:** Easy

---

## Option 1: Streamlit Cloud (Recommended) ⭐

**Best for:** Quickest deployment, zero configuration, perfect for this project

### Step 1: Prepare Your Repository

```bash
# Make sure all changes are committed
cd /Users/justinwoo/cdl_dashboard
git add .
git commit -m "Clean repository ready for deployment"

# Push to GitHub (if not already there)
git push origin main
```

### Step 2: Set Up Cloud Database

You need a PostgreSQL database. Choose one:

#### Option A: Supabase (Recommended)
1. Go to https://supabase.com/
2. Click "Start your project"
3. Create free account
4. Click "New Project"
5. Choose organization and project name
6. **Save the database password!**
7. Wait 2 minutes for database to spin up
8. Go to Settings → Database
9. Copy the "Connection String" (URI format)
   - Example: `postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

#### Option B: Neon
1. Go to https://neon.tech/
2. Sign up for free
3. Create new project
4. Copy connection string from dashboard

#### Option C: Railway
1. Go to https://railway.app/
2. Sign up
3. New Project → Add PostgreSQL
4. Copy connection string from Variables tab

### Step 3: Initialize Cloud Database

```bash
# Set your database URL
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Initialize tables
python3 -c "from database import init_db; init_db()"

# You should see:
# ✅ Database initialized
```

### Step 4: Deploy to Streamlit Cloud

1. **Go to https://share.streamlit.io/**
2. Click **"New app"**
3. **Select your repository**
   - Repository: `your-username/cdl_dashboard`
   - Branch: `main`
   - Main file path: `app.py`
4. **Advanced settings** (click to expand)
   - Add secrets (TOML format):
     ```toml
     DATABASE_URL = "postgresql://your-connection-string-here"
     ```
5. Click **"Deploy!"**
6. Wait 2-3 minutes for deployment

### Step 5: First Data Refresh

1. Your app will load at: `https://your-app-name.streamlit.app`
2. You'll see "No data available" message
3. Click **"🔄 Refresh Data"** button
4. Wait 2-3 minutes for initial scrape
5. Done! Your dashboard is live with data

### Step 6: Deploy Hardpoint Dashboard (Optional)

Repeat Step 4 but:
- Main file path: `hardpoint_dashboard.py`
- Use same DATABASE_URL secret
- Will deploy at: `https://your-hardpoint-app.streamlit.app`

---

## Option 2: Heroku

**Best for:** More control, custom domain support, background workers

### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Or download from https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Create Heroku App

```bash
cd /Users/justinwoo/cdl_dashboard

# Login to Heroku
heroku login

# Create app
heroku create your-cdl-dashboard

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini
```

### Step 3: Configure Environment

```bash
# Heroku automatically sets DATABASE_URL, but verify:
heroku config

# Should see DATABASE_URL=postgresql://...
```

### Step 4: Create Procfile

```bash
cat > Procfile << 'EOF'
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
EOF
```

### Step 5: Deploy

```bash
git add Procfile
git commit -m "Add Procfile for Heroku"
git push heroku main

# Initialize database
heroku run python -c "from database import init_db; init_db()"

# Open app
heroku open
```

### Step 6: First Refresh

Click "🔄 Refresh Data" button in the UI to populate data.

---

## Option 3: Railway

**Best for:** Modern platform, great developer experience

### Step 1: Deploy

1. Go to https://railway.app/
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose `cdl_dashboard` repository
5. Click "Add PostgreSQL" from services
6. Railway auto-detects it's a Python app

### Step 2: Configure

1. Click on your service
2. Go to "Variables" tab
3. Add variable:
   - Key: `DATABASE_URL`
   - Value: Copy from PostgreSQL service connection string
4. Click "Settings" → "Generate Domain" to get public URL

### Step 3: Initialize & Refresh

```bash
# SSH into Railway container (or use their CLI)
railway run python -c "from database import init_db; init_db()"

# Or just visit your app and click "🔄 Refresh Data"
```

---

## Option 4: Local Network Access

**Best for:** Testing, internal team use, quick demos

### Step 1: Run with Network Access

```bash
cd /Users/justinwoo/cdl_dashboard

# Run with network binding
streamlit run app.py --server.address=0.0.0.0

# Find your local IP
ipconfig getifaddr en0  # macOS WiFi
# or
ipconfig getifaddr en1  # macOS Ethernet
```

### Step 2: Access from Other Devices

From any device on your network:
```
http://YOUR_LOCAL_IP:8501
```

Example: `http://192.168.1.100:8501`

---

## Post-Deployment Checklist

### ✅ Verify Everything Works

- [ ] App loads without errors
- [ ] Click "🔄 Refresh Data" button
- [ ] Wait for scraping to complete
- [ ] Verify matches appear in list
- [ ] Click on a match to see details
- [ ] Check all tabs work (Overview, Matches, Players, etc.)
- [ ] Verify charts render correctly
- [ ] Check "Last updated" timestamp shows

### ✅ Performance Check

- [ ] Page load time < 3 seconds
- [ ] Refresh takes 1-3 minutes (first time)
- [ ] Subsequent refreshes < 1 minute
- [ ] Database stats showing correct counts

### ✅ Set Up Regular Refreshes

Since there's no automatic scraping, you have options:

**Option A: Manual Refresh (Simplest)**
- Just click button when you want new data
- Check breakingpoint.gg for new matches
- Refresh after tournaments

**Option B: Add Auto-Refresh Timer (Code Change)**
```python
# In app.py main(), add:
import time
from datetime import datetime, timedelta

# Check if last refresh was > 6 hours ago
last_scrape = get_last_scrape_date()
if last_scrape and datetime.now() - last_scrape > timedelta(hours=6):
    with st.spinner("Auto-refreshing data..."):
        refresh_data()
```

**Option C: Browser Extension**
- Use "Auto Refresh Plus" extension
- Set to refresh your dashboard URL every 6 hours
- Triggers page load which shows refresh button

---

## Troubleshooting

### "Cannot connect to database"

**Check connection string:**
```bash
python3 << 'EOF'
import os
from sqlalchemy import create_engine

url = os.getenv("DATABASE_URL", "check-your-env-variable")
print(f"Connecting to: {url[:30]}...")
try:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

**Common fixes:**
- Verify DATABASE_URL is set in Streamlit secrets
- Check for special characters in password (URL encode them)
- Verify database is running (Supabase, Neon, etc.)
- Try connection string in local terminal first

### "Refresh button does nothing"

**Debug steps:**
1. Check terminal/logs for error messages
2. Verify breakingpoint.gg is accessible
3. Try running scraper manually:
   ```bash
   python3 -c "from scrape_breakingpoint import scrape_live_data; df = scrape_live_data(); print(len(df))"
   ```
4. Check if database has write permissions

### "Slow performance"

**Solutions:**
- Reduce data in database (keep last 30 days only)
- Ensure indexes exist on player_stats table
- Use database connection pooling (already configured)
- Check if database is in same region as app

### "App crashes on refresh"

**Check:**
- Memory limits (Streamlit Cloud free tier has limits)
- Scraping timeout (breakingpoint.gg may be slow)
- Database connection pool exhausted
- Too many matches being scraped at once

**Fix:**
```python
# In scrape_breakingpoint.py, limit matches:
completed = completed[:50]  # Only scrape 50 most recent
```

---

## Monitoring & Maintenance

### Check Health

```bash
# Test database
python3 -c "from database import get_cache_stats; print(get_cache_stats())"

# Test scraping
python3 -c "from scrape_breakingpoint import scrape_live_data; df = scrape_live_data(start_date='2026-01-01'); print(len(df))"
```

### Update Data Regularly

**Daily:** Click refresh button after major matches  
**Weekly:** Check for new teams/maps that need logos  
**Monthly:** Review database size, clear old data if needed  

### Backup Strategy

```bash
# Backup database (PostgreSQL)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Or use your cloud provider's backup feature
# Supabase: Automatic daily backups
# Neon: Point-in-time restore
# Railway: Database snapshots
```

---

## Cost Breakdown

### Free Tier (Recommended for Starting)

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Streamlit Cloud** | ✅ Unlimited | Public apps only |
| **Supabase** | ✅ 500MB DB | 2GB bandwidth/month |
| **Neon** | ✅ 3GB DB | 1 project |
| **Railway** | ✅ $5 credit/month | Enough for small apps |
| **Total** | **$0/month** | Perfect for this project |

### Paid Tier (For Growth)

| Service | Cost | Benefits |
|---------|------|----------|
| **Streamlit Cloud Team** | $200/month | Private apps, more resources |
| **Supabase Pro** | $25/month | 8GB DB, better performance |
| **Heroku Hobby** | $7/month | Custom domain, SSL |
| **Railway Pro** | $20 credit/month | More resources |

---

## Next Steps After Deployment

1. **Share the URL** 🎉
   - Send to friends/community
   - Post on CDL subreddit
   - Share on social media

2. **Monitor Usage**
   - Check visitor count (Streamlit Cloud analytics)
   - Track refresh frequency
   - Monitor database size

3. **Gather Feedback**
   - What features do users want?
   - Any performance issues?
   - Missing stats or visualizations?

4. **Iterate**
   - Add requested features
   - Improve visualizations
   - Optimize performance

---

## Quick Reference Commands

```bash
# Local development
streamlit run app.py

# Initialize database
python3 -c "from database import init_db; init_db()"

# Test scraping
python3 -c "from scrape_breakingpoint import scrape_live_data; df = scrape_live_data(); print(len(df))"

# Check database stats
python3 -c "from database import get_cache_stats; print(get_cache_stats())"

# Test all imports
python3 -c "from app import *; from hardpoint_dashboard import *; print('✅ All imports work')"
```

---

## Support & Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **Supabase Docs**: https://supabase.com/docs
- **Heroku Docs**: https://devcenter.heroku.com/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

- **Your Documentation**: 
  - `README.md` - Main guide
  - `docs/QUICKSTART.md` - Setup instructions
  - `docs/REFRESH_BUTTON_GUIDE.md` - How refresh works
  - `docs/ARCHITECTURE.md` - System design

---

**Ready to deploy?** Start with **Option 1 (Streamlit Cloud)** - it's the easiest and works great for this project!

*Last updated: January 1, 2026*
