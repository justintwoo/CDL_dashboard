# CDL Dashboard - Refresh Button Guide

## Overview
The CDL Dashboard now uses an **on-demand refresh button** instead of scheduled scraping. This gives you full control over when to update data while maintaining a last-updated timestamp to track incremental updates.

## How It Works

### 1. Last Updated Timestamp
- The system stores a `last_scrape_date` in the PostgreSQL database
- When you click **Refresh Data**, it scrapes matches from that date forward
- After successful scraping, the timestamp is updated to the current time
- This ensures you only scrape new data, not the entire history

### 2. Incremental Scraping
- **First refresh**: Scrapes last 7 days of matches (default)
- **Subsequent refreshes**: Only scrapes from last update timestamp to now
- Example: If last update was 2026-01-01 10:00 AM, clicking refresh at 3:00 PM only scrapes 10 AM - 3 PM matches

### 3. Database Schema
New table added:
```sql
CREATE TABLE scrape_metadata (
    id SERIAL PRIMARY KEY,
    last_scrape_date TIMESTAMP NOT NULL,
    scrape_timestamp TIMESTAMP DEFAULT NOW()
);
```

## Using the Refresh Button

### Main Dashboard (app.py)
```
🎮 CDL Stats Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Last updated: 2026-01-01 15:14:50    [🔄 Refresh Data]
📦 72 matches | 2,472 player records

Total Maps: 2,472  |  Unique Matches: 72  |  Unique Players: 104
```

### Hardpoint Dashboard (hardpoint_dashboard.py)
```
🎯 CDL Hardpoint Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Last updated: 2026-01-01 15:14:50    [🔄 Refresh Data]
📦 72 matches | 2,472 player records

Hardpoint Maps: 904  |  Unique Matches: 24  |  Teams: 33  |  Players: 102
```

### When to Refresh
- **After major tournaments**: New matches need to be added
- **Daily/Weekly**: Catch up on recent matches
- **On-demand**: Only when you need the latest data

## Code Changes

### database.py
Added three new functions:
```python
def get_last_scrape_date() -> Optional[datetime]:
    """Get the last scrape date from metadata"""

def update_last_scrape_date(date: datetime) -> bool:
    """Update the last scrape date in metadata"""
```

### scrape_breakingpoint.py
Updated function signature:
```python
def scrape_live_data(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Args:
        start_date: Optional date string in 'YYYY-MM-DD' format.
                   If provided, only scrapes matches from this date forward.
                   If None, defaults to 7 days ago.
    """
```

### app.py & hardpoint_dashboard.py
Added refresh functionality:
```python
def refresh_data():
    """Refresh data by scraping from last scrape date to now"""
    last_date = get_last_scrape_date()
    new_df = scrape_live_data(start_date=last_date.strftime('%Y-%m-%d'))
    cache_match_data(new_df)
    update_last_scrape_date(datetime.now())
```

## Advantages

### ✅ User Control
- You decide when to update data
- No waiting for scheduled jobs
- Immediate feedback on refresh success/failure

### ✅ Efficient Scraping
- Only scrapes new matches since last update
- Respects breakingpoint.gg server (no unnecessary requests)
- Faster updates (only fetch what's needed)

### ✅ Timestamp Tracking
- Always know when data was last refreshed
- Visible in UI: `📅 Last updated: 2026-01-01 15:14:50`
- Stored in database for persistence

### ✅ Simpler Deployment
- No need for GitHub Actions
- No need for scheduled cron jobs
- Works on any hosting platform (Streamlit Cloud, Heroku, etc.)

## Deployment Considerations

### Local Development
```bash
# Run main dashboard
streamlit run app.py

# Run hardpoint dashboard
streamlit run hardpoint_dashboard.py

# Manual refresh via UI button
```

### Cloud Hosting (Streamlit Cloud, Heroku, etc.)
- Deploy as normal Streamlit app
- Refresh button works out of the box
- Database URL configured via environment variables
- No additional setup required (no GitHub Actions, no cron)

### Database Requirements
- PostgreSQL with existing tables (matches, player_stats)
- New table: `scrape_metadata` (created automatically by `init_db()`)
- Connection via `DATABASE_URL` environment variable

## Migration from GitHub Actions

If you previously had scheduled scraping via GitHub Actions:

### Files Removed:
- ❌ `.github/workflows/update_data.yml` (no longer needed)
- ❌ `update_data.py` (headless scraper, replaced by UI button)

### Files Modified:
- ✅ `database.py` - Added timestamp tracking functions
- ✅ `scrape_breakingpoint.py` - Added `start_date` parameter
- ✅ `app.py` - Added refresh button and `refresh_data()` function
- ✅ `hardpoint_dashboard.py` - Same refresh functionality

### Migration Steps:
1. Pull latest code
2. Run `python3 -c "from database import init_db; init_db()"` to create new table
3. Restart Streamlit apps
4. Click **Refresh Data** button to update

## Troubleshooting

### "No new matches found"
- Normal if no matches played since last update
- Wait for new matches to be completed on breakingpoint.gg
- Check last update timestamp to see coverage

### Refresh button shows error
- Check database connection (DATABASE_URL)
- Verify breakingpoint.gg is accessible
- Check terminal output for detailed error messages
- Try refreshing page and clicking again

### Last updated shows old date
- Click **Refresh Data** to update
- Timestamp only updates after successful scrape
- If scrape fails, timestamp remains unchanged

### Slow refresh
- Normal for first refresh (scrapes 7 days = ~70 matches)
- Subsequent refreshes faster (only new matches)
- Progress shown in terminal output

## Testing

Test the new functionality:
```bash
# Test database functions
python3 -c "from database import init_db, get_last_scrape_date, update_last_scrape_date; from datetime import datetime; init_db(); print(get_last_scrape_date()); update_last_scrape_date(datetime.now())"

# Test scraping with date
python3 -c "from scrape_breakingpoint import scrape_live_data; df = scrape_live_data(start_date='2025-12-28'); print(f'Scraped {len(df) if df is not None else 0} records')"

# Start dashboard and test refresh button
streamlit run app.py
```

## Summary

| Feature | Old (GitHub Actions) | New (Refresh Button) |
|---------|---------------------|---------------------|
| **Update Method** | Automatic hourly cron | Manual on-demand button |
| **User Control** | None | Full control |
| **Scraping Scope** | Last 7 days | From last update timestamp |
| **Deployment** | Requires GitHub Actions setup | Simple Streamlit deployment |
| **Timestamp Tracking** | Not stored | Stored in database |
| **Feedback** | No visibility | Immediate UI feedback |
| **Complexity** | High (GitHub secrets, workflows) | Low (just click button) |

---

*Last updated: January 1, 2026*
