# Repository Cleanup Plan

## Files to Remove:

### 1. Python Cache Files (should be in .gitignore)
- __pycache__/ directory and all .pyc files

### 2. Test/Debug Scripts (one-time use)
- test_connection.py - Used for initial database setup
- test_position_filter.py - Used for testing position filter
- migrate_add_scores.py - Migration already completed
- rescrape_all_data.py - One-time data refresh script

### 3. Old/Unused Code
- hardpoint_dashboard.py - Old separate dashboard (functionality in app.py)

### 4. Redundant Documentation
- docs/DATABASE_CONNECTION_FIX.md
- docs/FIX_CONNECTION.md
- docs/STREAMLIT_CLOUD_FIX.md
- docs/MAP_SCORE_FIX.md
- docs/MAP_SCORE_RESOLUTION.md
- docs/NEON_SETUP_STEPS.md
- docs/SETUP_COMPLETE.md
- docs/DEPLOY_NOW.md
- docs/CLEANUP_SUMMARY.md
- docs/BEFORE_AFTER.md
- NEON_READY.md

### 5. Keep These Files:
- app.py (main application)
- database.py (database operations)
- scrape_breakingpoint.py (data scraping)
- stats_utils.py (utility functions)
- config.py (configuration)
- requirements.txt (dependencies)
- README.md (project documentation)
- .gitignore (git configuration)
- .env (local environment variables)
- docs/QUICKSTART.md (user guide)
- docs/DEPLOYMENT_INSTRUCTIONS.md (deployment guide)
- docs/CODEBASE_OVERVIEW.md (code documentation)
- docs/ARCHITECTURE.md (system architecture)
- docs/CHANGELOG.md (version history)
- data/ directory (contains necessary data files)
