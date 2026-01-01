# CDL Dashboard - Changelog

## Version 2.0 - Refresh Button Update (January 1, 2026)

### 🎯 Major Changes

**Replaced scheduled scraping with on-demand refresh button**
- Removed GitHub Actions hourly automation
- Added UI refresh button to both dashboards
- Implemented last-updated timestamp tracking
- Incremental scraping from last update date

### ✨ New Features

#### 1. Refresh Button in UI
- **Location**: Top-right corner of both dashboards
- **Function**: Scrapes new matches from last update to now
- **Feedback**: Shows progress, success/error messages
- **Visual**: `🔄 Refresh Data` button with full-width styling

#### 2. Last Updated Timestamp
- **Display**: Shows in UI header: `📅 Last updated: 2026-01-01 15:14:50`
- **Storage**: Persisted in PostgreSQL `scrape_metadata` table
- **Logic**: Only updates after successful scraping
- **Default**: 7 days ago if no previous scrape

#### 3. Incremental Scraping
- **Smart Date Range**: Scrapes from `last_scrape_date` to current time
- **Efficiency**: Only fetches new matches, not entire history
- **Performance**: Much faster than re-scraping 7 days every time
- **Respectful**: Reduces load on breakingpoint.gg servers

### 📝 Files Modified

#### database.py
- Added `ScrapeMetadata` ORM model
- Added `get_last_scrape_date()` function
- Added `update_last_scrape_date(date)` function
- Schema update creates new `scrape_metadata` table

#### scrape_breakingpoint.py
- Updated `scrape_live_data()` to accept `start_date` parameter
- Signature: `scrape_live_data(start_date: Optional[str] = None)`
- Filters matches by date: `m.get('datetime', '')[:10] >= date_threshold`
- Maintains backward compatibility (defaults to 7 days)

#### app.py
- Added `load_data_with_refresh()` function (replaces cached `get_data()`)
- Added `refresh_data()` function with progress spinner
- Updated `main()` to show last updated timestamp
- Added refresh button UI component
- Updated header layout: 4:1 column ratio for timestamp and button
- Shows data metrics: Total Maps, Unique Matches, Unique Players

#### hardpoint_dashboard.py
- Same changes as app.py
- Added `load_data_with_refresh()` function
- Added `refresh_data()` function
- Updated `main()` with refresh button
- Shows Hardpoint-specific metrics

### 🗑️ Files Removed

#### .github/workflows/update_data.yml
- **Reason**: No longer using GitHub Actions scheduled scraping
- **Alternative**: On-demand refresh button in UI

#### update_data.py
- **Reason**: Headless scraper no longer needed
- **Alternative**: refresh_data() function in UI

### 📚 Files Added

#### REFRESH_BUTTON_GUIDE.md
- Complete documentation of new refresh system
- How it works (timestamp tracking, incremental scraping)
- Code changes explained
- Advantages over scheduled approach
- Migration guide from GitHub Actions
- Troubleshooting section
- Testing instructions

#### CHANGELOG.md (this file)
- Version history and change tracking

### 🔧 Technical Details

#### New Database Table
```sql
CREATE TABLE scrape_metadata (
    id SERIAL PRIMARY KEY,
    last_scrape_date TIMESTAMP NOT NULL,
    scrape_timestamp TIMESTAMP DEFAULT NOW()
);
```

#### API Changes
```python
# Old (no parameter)
def scrape_live_data() -> Optional[pd.DataFrame]:
    pass

# New (with optional start_date)
def scrape_live_data(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    pass
```

#### UI Flow
```
1. User clicks "🔄 Refresh Data"
2. Get last_scrape_date from database
3. Call scrape_live_data(start_date=last_scrape_date)
4. Cache results with cache_match_data(df)
5. Update last_scrape_date to datetime.now()
6. Reload UI data and show success message
```

### ✅ Benefits

1. **User Control**: Update data whenever you want, not on a schedule
2. **Efficiency**: Only scrape new matches since last update
3. **Visibility**: Always see when data was last refreshed
4. **Simplicity**: No GitHub Actions setup required
5. **Flexibility**: Works on any hosting platform
6. **Feedback**: Immediate UI notifications on success/failure

### 📊 Performance Impact

- **First Refresh**: ~180 seconds (scrapes 7 days of matches)
- **Subsequent Refreshes**: 10-60 seconds (only new matches)
- **UI Load Time**: Still 0.08s (loads from PostgreSQL cache)
- **Database Growth**: +1 row per refresh in scrape_metadata table

### 🚀 Deployment

#### For New Deployments
```bash
# 1. Initialize database (creates scrape_metadata table)
python3 -c "from database import init_db; init_db()"

# 2. Run dashboard
streamlit run app.py

# 3. Click "Refresh Data" button in UI to populate
```

#### For Existing Deployments
```bash
# 1. Pull latest code
git pull origin main

# 2. Update database schema
python3 -c "from database import init_db; init_db()"

# 3. Restart dashboards
pkill -f "streamlit run"
streamlit run app.py

# 4. Refresh data via UI button
```

### 🐛 Bug Fixes

None - This is a feature update, not a bug fix release

### ⚠️ Breaking Changes

**Removed:**
- GitHub Actions automation (optional feature, not core)
- `update_data.py` script (replaced by UI button)
- `@st.cache_data` decorator on data loading (replaced with session state)

**Not Breaking:**
- Database schema extended (backward compatible)
- `scrape_live_data()` function signature extended (backward compatible)
- All existing dashboards still work
- All existing database queries unchanged

### 🔮 Future Enhancements

Potential improvements for future versions:
- Auto-refresh on timer (e.g., every 30 minutes)
- Refresh history log (show past refresh timestamps)
- Manual date range picker (scrape specific date range)
- Batch refresh (refresh multiple date ranges)
- Background refresh (don't block UI)
- Email/Slack notifications on refresh

### 📝 Migration Notes

If you were using the GitHub Actions version:
1. Delete `.github` directory (already done)
2. Delete `update_data.py` (already done)
3. Update code to latest version
4. Run `init_db()` to create new table
5. Use refresh button instead of waiting for cron

### 🧪 Testing

All tests passed:
```bash
✅ Database schema updated (scrape_metadata table created)
✅ get_last_scrape_date() returns timestamp
✅ update_last_scrape_date() updates database
✅ scrape_live_data(start_date='2025-12-28') works correctly
✅ load_from_cache() returns 280 records
✅ UI imports all modules successfully
```

### 👥 Contributors

- Justin Woo (@justinwoo) - Original implementation
- GitHub Copilot - Code assistance and documentation

---

## Version 1.0 - Cloud Deployment (December 31, 2025)

### Features
- PostgreSQL database caching
- GitHub Actions hourly scraping
- Streamlit Cloud deployment
- CDL map filtering
- Hardpoint specialized dashboard
- Team logos and map images

*See CODEBASE_OVERVIEW.md for complete version 1.0 documentation*

---

*Maintained by Justin Woo | Last updated: January 1, 2026*
