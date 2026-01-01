# CDL Dashboard Deployment Instructions for New Workspace

**Supabase Project URL**: https://amxinvsaknlxlgjqthho.supabase.co

## Overview

This is a Call of Duty League (CDL) stats dashboard built with:
- **Backend**: Python 3.12, PostgreSQL (Supabase), SQLAlchemy
- **Frontend**: Streamlit with Plotly visualizations
- **Data**: Web scraping from breakingpoint.gg with on-demand refresh button

## Quick Setup (10 minutes)

### 1. Get the Supabase Connection String

```bash
# Go to: https://amxinvsaknlxlgjqthho.supabase.co
# Navigate to: Settings → Database → Connection String → URI
# Copy the connection string, it looks like:
# postgresql://postgres.amxinvsaknlxlgjqthho:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

**Important**: Replace `[YOUR-PASSWORD]` with your actual Supabase password.

### 2. Set Up Environment Variable

```bash
# Add to your shell profile (~/.zshrc or ~/.bashrc):
export DATABASE_URL="postgresql://postgres.amxinvsaknlxlgjqthho:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Or create a .env file in the project root:
echo 'DATABASE_URL="postgresql://postgres.amxinvsaknlxlgjqthho:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"' > .env

# Reload your shell:
source ~/.zshrc  # or source ~/.bashrc
```

### 3. Install Dependencies

```bash
cd cdl_dashboard
pip install -r requirements.txt
```

### 4. Initialize Database (ONLY IF FRESH DATABASE)

**Check if database is already initialized:**

```bash
# Try loading data first
python3 -c "from database import load_from_cache; print(f'Records: {len(load_from_cache())}')"
```

**If you see "Records: 0" or errors about missing tables:**

```bash
# Initialize the database schema
python3 -c "from database import init_db; init_db()"
```

**If you see "Records: 280+" (or any number > 0):**
- Database is already set up! Skip to step 5.

### 5. Run the Dashboard

```bash
# Main dashboard
streamlit run app.py

# Or the Hardpoint-specific dashboard
streamlit run hardpoint_dashboard.py
```

### 6. First Data Refresh

1. Dashboard opens in browser (usually http://localhost:8501)
2. Click the **"🔄 Refresh Data"** button in the top right
3. Wait 30-60 seconds for scraping to complete
4. Dashboard will reload with live data

---

## Project Structure

```
cdl_dashboard/
├── app.py                       # Main dashboard (all game modes)
├── hardpoint_dashboard.py       # Hardpoint-only dashboard
├── database.py                  # PostgreSQL ORM & caching
├── scrape_breakingpoint.py      # Web scraper for breakingpoint.gg
├── config.py                    # CDL maps/teams configuration
├── stats_utils.py               # Statistical analysis functions
├── requirements.txt             # Python dependencies
├── README.md                    # Main documentation
├── docs/
│   ├── DEPLOYMENT_STEPS.md      # Cloud deployment guide
│   ├── QUICKSTART.md            # Detailed setup guide
│   ├── REFRESH_BUTTON_GUIDE.md  # How refresh system works
│   ├── ARCHITECTURE.md          # System design
│   └── CODEBASE_OVERVIEW.md     # Complete code walkthrough
├── assets/
│   ├── team_logos/              # 33 team PNG logos
│   └── map_images/              # 10 map PNG images
└── data/
    └── breakingpoint_cod_stats.csv  # Sample data (reference only)
```

---

## Database Schema

The Supabase database has 3 tables:

### 1. `matches` table
- `match_id` (primary key)
- `team1`, `team2`, `result`, `score1`, `score2`
- `datetime`, `url`, `event_name`

### 2. `player_stats` table
- `id` (primary key)
- `match_id` (foreign key)
- `player_name`, `team`, `map_name`, `mode`
- `kills`, `deaths`, `damage`, `hill_time`

### 3. `scrape_metadata` table
- `id` (primary key)
- `last_scrape_date` (datetime of last successful scrape)
- `scrape_timestamp` (when scrape was initiated)

---

## Key Features

✅ **On-Demand Refresh Button** - No scheduled jobs, scrape when you want
✅ **Incremental Scraping** - Only fetches matches since last update (10-60s vs 180s)
✅ **CDL Map Filtering** - Only shows official competitive maps
✅ **Match Detail Views** - Per-map breakdowns with player stats
✅ **Interactive Charts** - Plotly visualizations with hover details
✅ **Hardpoint Dashboard** - Specialized view for Hardpoint mode
✅ **Team Logos & Map Images** - Visual assets included

---

## How the Refresh System Works

1. **User clicks "🔄 Refresh Data" button**
2. System checks `scrape_metadata` table for `last_scrape_date`
3. Scraper fetches only matches from that date to now
4. New data cached to PostgreSQL
5. `last_scrape_date` updated to current timestamp
6. Dashboard reloads with fresh data

**First refresh**: Scrapes last 7 days (default)  
**Subsequent refreshes**: Only scrapes since last update (much faster)

---

## Common Commands

```bash
# Check database connection
python3 -c "from database import engine; print(engine.url)"

# Check number of records
python3 -c "from database import load_from_cache; df = load_from_cache(); print(f'Matches: {len(df)}')"

# Check last scrape time
python3 -c "from database import get_last_scrape_date; print(get_last_scrape_date())"

# Manually scrape last 7 days
python3 -c "from scrape_breakingpoint import scrape_live_data; from database import cache_match_data; df = scrape_live_data(); cache_match_data(df) if df is not None else print('No data')"

# Run main dashboard
streamlit run app.py

# Run hardpoint dashboard
streamlit run hardpoint_dashboard.py

# Run on local network (access from other devices)
streamlit run app.py --server.address 0.0.0.0
```

---

## Troubleshooting

### "No module named 'streamlit'" or similar
```bash
pip install -r requirements.txt
```

### "Could not connect to database"
```bash
# Verify DATABASE_URL is set
echo $DATABASE_URL

# If empty, set it:
export DATABASE_URL="postgresql://postgres.amxinvsaknlxlgjqthho:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
```

### "No data available" in dashboard
```bash
# Click the "🔄 Refresh Data" button in the UI
# OR manually scrape:
python3 -c "from scrape_breakingpoint import scrape_live_data; from database import cache_match_data; df = scrape_live_data(); cache_match_data(df)"
```

### Refresh button not working
```bash
# Check if scraping works manually:
python3 -c "from scrape_breakingpoint import scrape_live_data; df = scrape_live_data(); print(f'Scraped {len(df)} records' if df is not None else 'No data')"

# Check database write permissions:
python3 -c "from database import init_db; init_db()"
```

### Database already has data but shows old data
```bash
# Clear cache and refresh:
python3 -c "from database import Session, Match, PlayerStat; session = Session(); print(f'Matches: {session.query(Match).count()}, Stats: {session.query(PlayerStat).count()}')"
```

---

## Cloud Deployment (Optional)

To deploy this dashboard to the web:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud** (free):
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repo
   - Main file: `app.py`
   - Advanced settings → Secrets:
     ```
     DATABASE_URL = "postgresql://postgres.amxinvsaknlxlgjqthho:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
     ```
   - Click "Deploy"

3. **First refresh on cloud**: Click "🔄 Refresh Data" button after deployment

**See `docs/DEPLOYMENT_STEPS.md` for full cloud deployment guide** (4 platform options).

---

## Important Notes

⚠️ **Never commit your DATABASE_URL with password to Git**  
⚠️ **Supabase free tier**: 500MB storage, 2GB bandwidth/month  
⚠️ **First scrape takes 60s** (fetches 7 days), subsequent scrapes are faster (10-30s)  
⚠️ **Refresh after tournaments** to get latest match data  

✅ **Database is already initialized** if you see records when querying  
✅ **No scheduled jobs needed** - refresh is manual/on-demand  
✅ **Works on any platform** - local, Streamlit Cloud, Heroku, Railway  

---

## Quick Copy-Paste Setup

```bash
# 1. Set environment variable (replace [PASSWORD])
export DATABASE_URL="postgresql://postgres.amxinvsaknlxlgjqthho:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# 2. Install dependencies
cd cdl_dashboard
pip install -r requirements.txt

# 3. Check if database is initialized (should show number > 0 if already set up)
python3 -c "from database import load_from_cache; print(f'Records: {len(load_from_cache())}')"

# 4. If step 3 shows errors or 0 records, initialize database:
python3 -c "from database import init_db; init_db()"

# 5. Run dashboard
streamlit run app.py

# 6. In browser, click "🔄 Refresh Data" button
```

---

## Support & Documentation

- **Main README**: `README.md`
- **Full Deployment Guide**: `docs/DEPLOYMENT_STEPS.md`
- **Setup Guide**: `docs/QUICKSTART.md`
- **Refresh System Details**: `docs/REFRESH_BUTTON_GUIDE.md`
- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Code Walkthrough**: `docs/CODEBASE_OVERVIEW.md`

---

## What Makes This Dashboard Special

1. **On-Demand Updates**: Click button to refresh, no cron jobs needed
2. **Incremental Scraping**: Only fetches new matches (smart and fast)
3. **CDL Official Maps Only**: Filters out non-competitive data
4. **Hardpoint Specialized View**: Dedicated dashboard for Hardpoint mode
5. **Production Ready**: Clean codebase, comprehensive docs, cloud-deployable

---

**Created**: January 1, 2026  
**Supabase Project**: https://amxinvsaknlxlgjqthho.supabase.co  
**Database**: PostgreSQL (Supabase hosted)  
**Framework**: Streamlit + SQLAlchemy + Plotly
