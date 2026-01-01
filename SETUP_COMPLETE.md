# CDL Dashboard - Setup Complete! 🎉

## Setup Date
January 1, 2026

## Configuration Summary

### ✅ What Was Done

1. **Environment Configuration**
   - Created `.env` file with Supabase credentials
   - Corrected database connection URL to use `db.amxinvsaknlxlgjqthho.supabase.co`
   - Password URL-encoded to handle special characters

2. **Dependencies**
   - All Python packages from `requirements.txt` installed
   - Virtual environment: `/Users/justinwoo/Documents/GitHub/CDL_dashboard/.venv/`
   - Python version: 3.13.2

3. **Database Setup**
   - Connected to Supabase PostgreSQL database
   - Initialized 3 tables: `matches`, `player_stats`, `scrape_metadata`
   - Database currently has **280 player records**

4. **Application Launch**
   - Fixed syntax error in `app.py` (line 1634)
   - Streamlit dashboard started successfully
   - **Access URL**: http://localhost:8502

---

## Database Connection Details

**Connection String** (stored in `.env`):
```
DATABASE_URL="postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres"
```

**Important Notes**:
- The password contains special characters (`+` and `$`) that are URL-encoded
- Use `db.amxinvsaknlxlgjqthho.supabase.co` (NOT the pooler URL)
- Port: 5432 (standard PostgreSQL port)

---

## How to Run the Dashboard

### Start Main Dashboard
```bash
cd /Users/justinwoo/Documents/GitHub/CDL_dashboard
/Users/justinwoo/Documents/GitHub/CDL_dashboard/.venv/bin/streamlit run app.py
```

### Start Hardpoint Dashboard
```bash
/Users/justinwoo/Documents/GitHub/CDL_dashboard/.venv/bin/streamlit run hardpoint_dashboard.py
```

### Access in Browser
- Main Dashboard: http://localhost:8502 (or whatever port Streamlit assigns)
- The browser should open automatically

---

## Next Steps

### 1. Refresh Data
Once the dashboard opens:
1. Click the **"🔄 Refresh Data"** button in the top right
2. Wait 30-60 seconds for scraping to complete
3. Dashboard will reload with the latest match data

### 2. Explore Features
- **Player Overview**: Individual player stats and performance
- **Map/Mode Breakdown**: Analysis by map and game mode
- **Head-to-Head**: Compare players or teams

### 3. Customize (Optional)
- Edit `config.py` for CDL teams/maps
- Modify `stats_utils.py` for new statistics
- Update `app.py` to add new visualizations

---

## Database Status

Current database state:
- **Matches table**: Empty (needs first scrape)
- **PlayerStats table**: 280 records (likely from cache)
- **ScrapeMetadata table**: Empty (will track scrape history)

After clicking "Refresh Data", the database will populate with:
- Latest 7 days of matches (first scrape)
- All player statistics from those matches
- Timestamp of last successful scrape

---

## Troubleshooting

### If dashboard won't start
```bash
# Check if port is in use
lsof -i :8502

# Try different port
/Users/justinwoo/Documents/GitHub/CDL_dashboard/.venv/bin/streamlit run app.py --server.port 8503
```

### If database connection fails
```bash
# Verify .env file exists
cat /Users/justinwoo/Documents/GitHub/CDL_dashboard/.env

# Test connection
/Users/justinwoo/Documents/GitHub/CDL_dashboard/.venv/bin/python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres'
from database import load_from_cache
print('✅ Connected' if load_from_cache() is not None else '❌ Failed')
"
```

### If refresh button doesn't work
```bash
# Manually scrape data
/Users/justinwoo/Documents/GitHub/CDL_dashboard/.venv/bin/python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres'
from scrape_breakingpoint import scrape_live_data
from database import cache_match_data
df = scrape_live_data()
if df is not None:
    cache_match_data(df)
    print(f'✅ Scraped {len(df)} records')
"
```

---

## Files Created/Modified

1. **`.env`** - Database credentials (KEEP PRIVATE, don't commit to Git)
2. **`app.py`** - Fixed syntax error on line 1634

---

## Important Security Notes

⚠️ **DO NOT commit `.env` file to Git**
- Contains your Supabase password
- Already added to `.gitignore` (verify this)

⚠️ **Supabase Free Tier Limits**
- 500MB storage
- 2GB bandwidth/month
- Monitor usage at: https://amxinvsaknlxlgjqthho.supabase.co

---

## Success Indicators

✅ `.env` file created with correct credentials  
✅ All dependencies installed  
✅ Database connected successfully  
✅ Database tables initialized  
✅ 280 player records loaded  
✅ Streamlit app running at http://localhost:8502  
✅ No critical errors in console  

---

## Quick Reference Commands

```bash
# Start dashboard
cd /Users/justinwoo/Documents/GitHub/CDL_dashboard
.venv/bin/streamlit run app.py

# Check database status
.venv/bin/python -c "from database import get_cache_stats; print(get_cache_stats())"

# View last scrape time
.venv/bin/python -c "from database import get_last_scrape_date; print(get_last_scrape_date())"

# Reinstall dependencies (if needed)
.venv/bin/pip install -r requirements.txt
```

---

**Setup completed successfully!** 🚀

Your CDL Dashboard is now ready to use. Visit **http://localhost:8502** to start exploring the data!
