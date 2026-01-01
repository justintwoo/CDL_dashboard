# CDL Dashboard - Complete Codebase Overview

## Project Summary
A comprehensive Call of Duty League (CDL) statistics dashboard that scrapes match data from breakingpoint.gg, caches it in PostgreSQL, and displays interactive analytics through Streamlit web interfaces. The system includes both a full match dashboard and a specialized Hardpoint mode dashboard.

---

## Architecture Overview

### System Components
1. **Data Scraping Layer** - Fetches live match data from breakingpoint.gg
2. **Database Layer** - PostgreSQL caching with SQLAlchemy ORM
3. **Analytics Layer** - Statistical calculations and aggregations
4. **Presentation Layer** - Streamlit web dashboards

### Data Flow
```
breakingpoint.gg API
    ↓
scrape_breakingpoint.py (fetch & parse)
    ↓
database.py (PostgreSQL cache)
    ↓
stats_utils.py (calculations)
    ↓
app.py / hardpoint_dashboard.py (UI)
    ↓
User Browser
```

---

## File-by-File Breakdown

### 1. `scrape_breakingpoint.py` (538 lines)
**Purpose**: Web scraping and data extraction from breakingpoint.gg

**Key Functions**:
- `fetch_match_player_stats(match_id)` - Scrapes individual match details and player statistics
  - Extracts game-by-game scores to determine map winners (lines 132-195)
  - Calculates `won_map` based on per-game score comparison, not match winner
  - Returns list of player stat dictionaries

- `scrape_live_data()` - Main scraping orchestrator (lines 210-350)
  - Fetches all matches from /matches page
  - **NEW: Filters to last 7 days only** (prevents full re-scrapes)
  - Iterates through completed matches to fetch player stats
  - Returns consolidated DataFrame

**Critical Fix Applied**:
- Lines 166-175: Fixed bug where all maps were marked as won by series winner
- Now correctly determines map winner by comparing `team_1_score` vs `team_2_score` per game

**Data Structure Returned**:
```python
{
    'match_id': str,
    'player_name': str,
    'team_name': str,
    'opponent_team_name': str,
    'map_number': int,
    'map_name': str,
    'mode': str (Hardpoint/Search & Destroy/Overload),
    'kills': int,
    'deaths': int,
    'assists': int,
    'damage': int,
    'rating': float,
    'won_map': bool,
    'date': str,
    'event_name': str,
    'series_type': str,
    'is_lan': bool,
    'season': str
}
```

---

### 2. `database.py` (~280 lines)
**Purpose**: PostgreSQL database schema and caching operations

**Database Configuration**:
- Host: localhost:5432
- Database: `cdl_stats`
- User: `justinwoo`
- Driver: SQLAlchemy with psycopg2

**Schema Design**:

#### Table: `matches`
```sql
CREATE TABLE matches (
    match_id VARCHAR PRIMARY KEY,
    date DATE,
    event_name VARCHAR,
    series_type VARCHAR,
    is_lan BOOLEAN,
    season VARCHAR,
    team1_name VARCHAR,        -- Added for quick lookups
    team2_name VARCHAR,        -- Added for quick lookups
    team1_score INTEGER,       -- Pre-calculated match score
    team2_score INTEGER,       -- Pre-calculated match score
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_date ON matches(date);
```

#### Table: `player_stats`
```sql
CREATE TABLE player_stats (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR REFERENCES matches(match_id) ON DELETE CASCADE,
    player_name VARCHAR,
    team_name VARCHAR,
    opponent_team_name VARCHAR,
    map_number INTEGER,
    map_name VARCHAR,
    mode VARCHAR,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    damage INTEGER,
    rating FLOAT,
    won_map BOOLEAN,           -- Accurate per-map result
    game_num INTEGER,
    timestamp TIMESTAMP
);

CREATE INDEX idx_match_id ON player_stats(match_id);
CREATE INDEX idx_player_name ON player_stats(player_name);
CREATE INDEX idx_team_name ON player_stats(team_name);
```

**Key Functions**:
- `init_db()` - Creates tables and indexes
- `cache_match_data(df)` - Stores DataFrame to database
  - Calculates team1_score/team2_score by counting maps won
  - Handles numpy.int64 → Python int conversion (lines 145-152)
  - Bulk inserts with upsert logic
  
- `load_from_cache()` - Retrieves all data as DataFrame
  - Performs JOIN between matches and player_stats
  - Returns ~2,472 records in 0.08 seconds (2,250x faster than scraping)

**Performance Metrics**:
- Load time: 0.08s (vs 180s for live scraping)
- Current cache: 72 matches, 2,472 player records

---

### 3. `stats_utils.py`
**Purpose**: Statistical calculations and data aggregations

**Key Functions**:
- `get_player_overall_stats(df, player_name)` - Career averages across all games
- `get_player_mode_stats(df, player_name, mode)` - Performance by game mode
- `get_player_map_mode_stats(df, player_name, map_name, mode)` - Specific map/mode stats
- `get_player_vs_opponent_stats(df, player_name, opponent)` - Head-to-head performance
- `get_summary_stats(df)` - Dataset overview (total games, players, teams, etc.)
- `get_mode_distribution(df)` - Game mode frequency counts
- `get_map_distribution(df)` - Map play frequency counts
- `get_players_by_team(df, team_name)` - Roster listing with stats

**Calculations Include**:
- K/D ratio: `kills / max(deaths, 1)`
- Win percentage: `sum(won_map) / total_maps * 100`
- Average stats: kills, deaths, assists, damage, rating per map
- Aggregations: by player, team, mode, map, opponent

---

### 4. `app.py` (1,613 lines)
**Purpose**: Main Streamlit dashboard with comprehensive match analysis

**CDL Map Filtering** (NEW):
```python
CDL_MAPS = {
    'Hardpoint': ['Blackheart', 'Colossus', 'Den', 'Exposure', 'Scar'],
    'Search & Destroy': ['Colossus', 'Den', 'Exposure', 'Raid', 'Scar'],
    'Overload': ['Den', 'Exposure', 'Scar']
}

def filter_cdl_maps(df):
    # Filters out non-CDL maps (Cortex, The Forge, Express, etc.)
    # Removes ~272 records of non-competitive maps
```

**Dashboard Pages**:

#### Overview Page
- Dataset summary statistics
- Recent matches list
- Mode and map distribution charts
- Team performance overview

#### Matches Page (lines 765-1200)
- **List View**: All matches with team logos, scores, dates
- **Detail View**: Individual match drill-down
  - Match header with team info and final score
  - Tabs for Overview + individual maps (Map 1, Map 2, etc.)
  - Per-map player statistics tables (4 players per team)
  - Team totals (kills, deaths, average rating)
  - Visualizations (kill charts, K/D comparisons)

**Critical Bug Fix** (lines 1098, 1113):
- Fixed `team1_map_data` → `team1_map_stats`
- Fixed `team2_map_data` → `team2_map_stats`
- Was causing silent NameError preventing player stats rendering

**Features**:
- Session state management for match selection
- Dynamic tab generation based on maps played
- Team logo and map image display
- Sortable dataframes with formatted columns
- Plotly interactive charts

---

### 5. `hardpoint_dashboard.py` (450 lines)
**Purpose**: Specialized dashboard for Hardpoint mode analysis

**Three Main Tabs**:

#### Tab 1: Map Stats
- Average kills per Hardpoint map
- Filters: Team, Win/Loss, Opponent
- Metrics cards showing avg kills for each map
- Bar chart visualization
- Detailed table: kills, deaths, damage, rating, match count

#### Tab 2: Player Stats
- All players' Hardpoint performance
- Filters: Map, Team, Win/Loss, Opponent
- Top 10 players by average kills (metric cards)
- Top 20 bar chart
- Full sortable player table with:
  - Avg Kills, Deaths, Assists, K/D Ratio
  - Avg Damage, Rating
  - Win %, Maps Played

#### Tab 3: Event Stats
- Tournament-level aggregations
- Average stats per event
- Number of matches, total maps, teams participating
- Bar chart of avg kills by event
- Comprehensive event statistics table

**Data Filtering**:
- `filter_hardpoint_data()` - Filters to Hardpoint mode + CDL maps only
- Removes non-competitive Hardpoint maps
- Ensures only official CDL map pool data

**Key Calculations**:
```python
# Average kills per map
map_stats = df.groupby(['map_name', 'map_number']).agg({
    'kills': 'mean',
    'deaths': 'mean',
    'damage': 'mean',
    'rating': 'mean',
    'match_id': 'nunique'  # Count unique matches
})

# Player performance
player_stats = df.groupby(['player_name', 'team_name']).agg({
    'kills': 'mean',
    'deaths': 'mean',
    'won_map': lambda x: (x == True).sum() / len(x) * 100  # Win %
})
```

---

### 6. `config.py` (183 lines)
**Purpose**: Configuration constants and column mappings

**Key Constants**:
- `DATA_CSV_PATH = "data/breakingpoint_cod_stats.csv"`
- `EXPECTED_COLUMNS` - Maps data schema column names
- `GAME_MODES` - List of valid game modes
- `CDL_MAPS` - Official map pools (also defined in app.py)
- Database connection settings
- UI configuration (colors, themes, etc.)

---

### 7. `generate_sample_data.py`
**Purpose**: Creates sample data for testing (not used in production)

---

### 8. Asset Generation
**Team Logos**: 33 PNG files (200x200px)
- Colored squares with team initials
- Naming: lowercase with underscores (e.g., `optic_texas.png`)
- Location: `data/team_logos/`

**Map Images**: 10 PNG files (400x250px)
- Colored rectangles with map names
- Naming: lowercase with underscores (e.g., `blackheart.png`)
- Location: `data/map_images/`

---

## Data Model

### Core Entities
1. **Match** - Single series between two teams
   - Has multiple maps/games
   - Best-of-5 or Best-of-9 format
   - Tracks team1_score vs team2_score

2. **Player Stat** - Individual player performance in one map
   - 8 records per map (4 players × 2 teams)
   - Links to parent match via match_id
   - Contains kills, deaths, assists, damage, rating
   - Boolean won_map field (accurate per-game result)

3. **Mode** - Game type (Hardpoint, Search & Destroy, Overload)
   - Each mode has specific map pool
   - Different strategic considerations

4. **Map** - Specific battlefield
   - CDL-approved maps only after filtering
   - Map numbers indicate position in series (1, 2, 4, 5, etc.)

### Relationships
```
Match (1) ──→ (many) Player_Stats
Team (1) ──→ (many) Players
Event (1) ──→ (many) Matches
Mode (1) ──→ (many) Maps
```

---

## Key Features Implemented

### 1. Accurate Score Tracking
- **Problem**: Initially, all maps were marked as won by series winner
- **Solution**: Extract per-game scores and compare team_1_score vs team_2_score
- **Impact**: Match scores now correct (e.g., OpTic 1-4 Paris, not 0-5)

### 2. Database Caching
- **Performance**: 2,250x faster (0.08s vs 180s)
- **Persistence**: Data survives app restarts
- **Indexing**: Fast queries on player_name, team_name, date

### 3. CDL Map Filtering
- **Quality**: Removes 272 non-competitive map records
- **Accuracy**: Only official CDL map pool included
- **Consistency**: Applied across both dashboards

### 4. Incremental Scraping
- **Efficiency**: Only fetches last 7 days of matches
- **API Friendly**: Reduces server load on breakingpoint.gg
- **Update Speed**: Fast refresh without full re-scrape

### 5. Interactive UI
- **Drill-Down**: Match list → Match detail → Map tabs → Player stats
- **Filtering**: Multi-level filters (team, mode, opponent, win/loss)
- **Visualizations**: Charts, metrics, sortable tables
- **Responsive**: Works on different screen sizes

---

## Technical Stack

### Backend
- **Python 3.12**
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **psycopg2** - PostgreSQL driver
- **pandas** - Data manipulation
- **requests** - HTTP client for scraping
- **BeautifulSoup4** - HTML parsing

### Frontend
- **Streamlit** - Web framework
- **Plotly** - Interactive charts
- **PIL (Pillow)** - Image generation

### Deployment
- **Development**: Local Streamlit server
- **Main Dashboard**: Port 8501
- **Hardpoint Dashboard**: Port 8502

---

## Current Data Stats
- **Total Records**: 2,472 player stats (after CDL map filtering: 2,200)
- **Matches**: 72 completed matches
- **Teams**: 33 unique teams
- **Players**: ~100+ unique players
- **Date Range**: Last 7 days (with historical data cached)
- **Modes**: Hardpoint (904 maps), Search & Destroy (848), Overload (720)
- **Maps**: 10 unique maps (5 CDL Hardpoint, 5 CDL S&D, 3 CDL Overload)

---

## File Structure
```
cdl_dashboard/
├── app.py                          # Main dashboard (1,613 lines)
├── hardpoint_dashboard.py          # Hardpoint-specific dashboard (450 lines)
├── scrape_breakingpoint.py         # Web scraper (538 lines)
├── database.py                     # PostgreSQL ORM (~280 lines)
├── stats_utils.py                  # Statistical calculations
├── config.py                       # Configuration constants (183 lines)
├── generate_sample_data.py         # Test data generator
├── requirements.txt                # Python dependencies
├── ARCHITECTURE.md                 # System design docs
├── QUICKSTART.md                   # Setup instructions
├── README.md                       # Project overview
├── data/
│   ├── breakingpoint_cod_stats.csv # CSV cache (2,472 records)
│   ├── team_logos/                 # 33 team logo PNGs
│   └── map_images/                 # 10 map image PNGs
└── __pycache__/                    # Python cache
```

---

## API Integration Details

### breakingpoint.gg Scraping
**Matches List Endpoint**:
- URL: `https://breakingpoint.gg/matches`
- Method: Parse server-side rendered JSON from `<script type="application/json">`
- Data Location: `props.pageProps.allMatches`
- Fields Used: `id`, `team1`, `team2`, `team_1_score`, `team_2_score`, `status`, `datetime`, `event`, `best_of`

**Individual Match Endpoint**:
- URL: `https://breakingpoint.gg/match/{match_id}`
- Method: Parse `window.initialMatchState` JavaScript object
- Data Location: `initialMatchState.games[].player_stats[]`
- Fields Extracted: Per-game scores, player stats (kills, deaths, assists, damage, rating)

**Rate Limiting**: 
- 1-second delay between match requests
- User-Agent header included
- Respectful scraping practices

---

## Known Issues & Limitations

### Fixed Issues ✅
1. ✅ Map winners calculated from match winner (now uses per-game scores)
2. ✅ Variable name mismatch in app.py (team1_map_data → team1_map_stats)
3. ✅ Import errors in hardpoint_dashboard.py (wrong function names)
4. ✅ Non-CDL maps included in analysis (now filtered out)

### Current Limitations
1. **No Real-Time Updates**: Requires manual refresh to fetch new data
2. **Local Only**: Not deployed to web (Streamlit runs locally)
3. **No User Authentication**: Open access to all data
4. **No Historical Trending**: Only shows last 7 days incremental
5. **API Dependency**: Relies on breakingpoint.gg structure not changing

---

## Performance Characteristics

### Database Performance
- Initial scrape: ~180 seconds (72 matches)
- Database cache load: 0.08 seconds
- Query speed: Sub-second for most aggregations
- Storage: ~2MB for 2,472 records

### UI Performance
- Page load: 1-2 seconds
- Filter application: Instant (client-side pandas)
- Chart rendering: <1 second (Plotly)
- Image loading: Instant (local files)

---

## Future Enhancement Opportunities

### Data Layer
1. **Incremental Updates**: Automatic background scraping every 30 minutes
2. **Historical Archive**: Keep all data beyond 7 days
3. **Player Images**: Scrape and cache player headshots
4. **Live Match Tracking**: Real-time score updates during ongoing matches

### Analytics Layer
5. **Predictive Models**: Win probability based on player matchups
6. **Trend Analysis**: Performance over time with line charts
7. **Comparative Stats**: Player vs player, team vs team rankings
8. **Advanced Metrics**: eDPI, accuracy %, objective time

### Presentation Layer
9. **Responsive Design**: Mobile-optimized layouts
10. **Dark Mode**: Theme toggle
11. **Export Functions**: Download filtered data as CSV/Excel
12. **Sharing**: Generate shareable links to specific views

### Deployment
13. **Cloud Hosting**: Deploy to Streamlit Cloud, Heroku, or AWS
14. **Custom Domain**: Brand with custom URL
15. **Authentication**: User accounts with saved preferences
16. **API Endpoint**: REST API for external integrations

---

## Code Quality & Best Practices

### Strengths
- ✅ Type hints on most functions
- ✅ Docstrings for key functions
- ✅ Error handling with try-except blocks
- ✅ Database connection pooling
- ✅ Indexed database tables
- ✅ Modular file structure
- ✅ Configuration centralized in config.py

### Areas for Improvement
- ⚠️ Limited unit test coverage
- ⚠️ Some magic numbers (could use constants)
- ⚠️ Long functions (app.py page_matches is 400+ lines)
- ⚠️ Duplicate CDL_MAPS definition (in app.py and hardpoint_dashboard.py)
- ⚠️ No logging framework (just print statements)

---

## Testing Recommendations

### Manual Testing Done ✅
- Data scraping: Verified 72 matches scraped correctly
- Database caching: Confirmed 2,472 records loaded in 0.08s
- Map filtering: Verified 272 non-CDL records removed
- Score accuracy: Confirmed OpTic vs Paris shows 1-4 (not 0-5)
- UI rendering: Both dashboards load without errors

### Automated Testing Needed
1. **Unit Tests**: Test individual functions (stats calculations, filtering)
2. **Integration Tests**: Test database operations end-to-end
3. **Scraping Tests**: Mock breakingpoint.gg responses
4. **UI Tests**: Selenium/Playwright for dashboard interactions
5. **Performance Tests**: Load testing with large datasets

---

## Dependencies (requirements.txt)
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
requests>=2.31.0
beautifulsoup4>=4.12.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
Pillow>=10.0.0
```

---

## Environment Setup

### Database Setup
```sql
-- Create database
CREATE DATABASE cdl_stats;

-- Create user (if needed)
CREATE USER justinwoo WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE cdl_stats TO justinwoo;
```

### Python Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "from database import init_db; init_db()"

# Run main dashboard
streamlit run app.py

# Run hardpoint dashboard
streamlit run hardpoint_dashboard.py
```

---

## Summary for ChatGPT / Claude

**Use Case**: "I have a working Streamlit dashboard that scrapes CDL stats, caches in PostgreSQL, and displays analytics. I want to convert this into a live website accessible on the internet."

**Current State**:
- ✅ Fully functional locally on ports 8501/8502
- ✅ PostgreSQL database with optimized schema
- ✅ Two Streamlit dashboards (main + hardpoint-specific)
- ✅ Web scraping with 7-day incremental updates
- ✅ Interactive charts and filtering
- ✅ 2,472 player records, 72 matches

**Key Technologies**: Python, Streamlit, PostgreSQL, SQLAlchemy, Plotly, pandas

**Goal**: Deploy to cloud with:
- Public URL (not localhost)
- Managed database (not local PostgreSQL)
- Automatic updates (not manual refresh)
- Scalable infrastructure
- Optional: Custom domain, authentication, API endpoints

**Files to Focus On**:
1. `app.py` - Main UI
2. `hardpoint_dashboard.py` - Secondary UI
3. `database.py` - Database schema and operations
4. `scrape_breakingpoint.py` - Data ingestion
5. `config.py` - Configuration management

---

## Questions for Framework Decision

1. **Hosting Platform**: Streamlit Cloud (easiest), Heroku, AWS, Google Cloud, or custom VPS?
2. **Database**: Managed PostgreSQL (Supabase, Railway, Neon) or stick with local?
3. **Domain**: Custom domain or use platform subdomain?
4. **Authentication**: Public access or login required?
5. **Update Schedule**: Automatic hourly/daily scraping or manual trigger?
6. **Cost**: Free tier acceptable or willing to pay for hosting?
7. **Scale**: Expected traffic (100 users/day? 10,000?)?

---

*This overview was generated on January 1, 2026 for the CDL Dashboard project.*
