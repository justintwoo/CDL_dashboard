# Map Score Fix - Summary

## Problem
Map scores were showing **32-27** (kills-deaths) instead of **250-233** (actual Hardpoint score).

## Root Cause
The database was missing `team_score` and `opponent_score` columns, so the app was falling back to calculating scores from kills/deaths.

## Solution Implemented

### 1. ✅ Database Schema Updated
- Added `team_score` column to `player_stats` table
- Added `opponent_score` column to `player_stats` table
- Migration successfully run on Neon database

### 2. ✅ Scraper Enhanced
The scraper now correctly extracts and saves:
- **Hardpoint**: Point scores (e.g., 250-233)
- **Search & Destroy**: Round scores (e.g., 6-1)
- **Overload**: Capture scores (e.g., 4-3)

### 3. ✅ Display Logic Fixed
- `calculate_map_scores_cached()` function now uses actual game scores
- Falls back to kills-deaths only if score data unavailable
- Backward compatible with old data

## Files Modified
1. `database.py` - Added columns to schema and load functions
2. `scrape_breakingpoint.py` - Enhanced to capture team_score/opponent_score (already working)
3. `app.py` - Updated map score calculation to use actual scores
4. `migrate_add_scores.py` - New migration script (already run successfully)

## Next Steps for You

### ⚠️ IMPORTANT: You must refresh the data to see correct scores!

1. **Reboot Streamlit Cloud App**
   - Go to your Streamlit Cloud dashboard
   - Find CDL_dashboard app
   - Click three-dot menu → Reboot app

2. **Refresh Data in App**
   - Open your dashboard
   - Click the **"🔄 Refresh Data"** button at the top
   - This will re-scrape all matches with correct scores
   - Wait for "Successfully refreshed!" message

3. **Verify Scores**
   - Navigate to a player detail page (e.g., Snoopy from Boston Breach)
   - Check the Map Score column
   - Should now show:
     - ✅ Hardpoint: **250-233** (not 32-27)
     - ✅ Search & Destroy: **6-1**
     - ✅ Overload: **4-3**

## Technical Details

### How Scores Are Extracted
```python
# From Breaking Point API
team_1_score = game.get('team_1_score', 0)  # e.g., 250 for Hardpoint
team_2_score = game.get('team_2_score', 0)  # e.g., 233 for Hardpoint

# Assigned to each player based on their team
if player_team_id == team_1_id:
    player_stat['team_score'] = team_1_score
    player_stat['opponent_score'] = team_2_score
```

### How Scores Are Displayed
```python
# In player detail page
if pd.notna(first_row.get('team_score')) and pd.notna(first_row.get('opponent_score')):
    team_score = int(first_row['team_score'])
    opponent_score = int(first_row['opponent_score'])
    map_scores[map_key] = f"{team_score}-{opponent_score}"  # e.g., "250-233"
```

## Commit History
- `e8fecf2` - Initial score column addition to schema
- `fd9e8dc` - Backward compatibility fix
- `7ba913c` - Migration script and successful execution

## Status
✅ Database migrated  
✅ Code deployed  
⏳ Waiting for data refresh (you need to do this)
