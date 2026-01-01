# 🎮 CDL Stats Dashboard# CDL Stats Dashboard



**Interactive analytics dashboard for Call of Duty League statistics from breakingpoint.gg**An interactive **Streamlit** dashboard for visualizing **Call of Duty League (CDL)** statistics exported from **breakingpoint.gg**.



[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)## Features

[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)

[![PostgreSQL](https://img.shields.io/badge/postgresql-latest-blue.svg)](https://www.postgresql.org/)### 📊 Data Overview

- Summary metrics (total matches, maps, players, teams)

---- Time-series visualization of maps played

- Mode distribution (Hardpoint, S&D, Overload)

## 📊 Features- Map frequency analysis

- Filters: date range, season, event, LAN/Online

### Two Specialized Dashboards

- **Main Dashboard** (`app.py`) - Comprehensive match analysis across all game modes### 👤 Player Overview

- **Hardpoint Dashboard** (`hardpoint_dashboard.py`) - Deep dive into Hardpoint mode statistics- Overall player statistics across all modes/maps

  - Average kills, deaths, K/D ratio, damage

### Core Capabilities- Mode-specific breakdown (kills, K/D by game mode)

- ✅ **On-Demand Data Refresh** - Click button to scrape latest matches from breakingpoint.gg- Performance trends over time

- ✅ **Incremental Scraping** - Only fetches new matches since last update (smart timestamp tracking)- Multi-player comparison support

- ✅ **PostgreSQL Caching** - 2,250x faster data loading (0.08s vs 180s)

- ✅ **CDL Map Filtering** - Only official competitive maps included### 🗺️ Per-Map / Per-Mode Breakdown

- ✅ **Interactive Visualizations** - Plotly charts with drill-down capabilities- Per-map statistics within a specific game mode

- ✅ **Match Detail Views** - Per-map player statistics and team comparisons  - Average kills, deaths, K/D, damage, win rate per map

- ✅ **Multi-Level Filtering** - Team, mode, opponent, win/loss filters- Visualizations:

  - Bar charts (avg kills, damage by map)

---  - Heatmap (map performance vs opponent teams)



## 🚀 Quick Start### ⚔️ Head-to-Head (vs Opponents)

- Player stats against specific opponent teams

### Prerequisites- Opponent-specific averages and trends

- Python 3.12+- Charts:

- PostgreSQL (local or cloud)  - Average kills by opponent

- 2GB RAM minimum  - K/D ratio by opponent

  - Win rate vs opponent

### Installation

## Getting Started

1. **Clone the repository**

```bash### Prerequisites

git clone <your-repo-url>

cd cdl_dashboard- Python 3.8+

```- pip or conda



2. **Install dependencies**### Installation

```bash

pip install -r requirements.txt1. **Clone or navigate to the project:**

```   ```bash

   cd cdl_dashboard

3. **Set up PostgreSQL**   ```

```bash

# Create database2. **Create a virtual environment (optional but recommended):**

createdb cdl_stats   ```bash

   python -m venv venv

# Or using psql   source venv/bin/activate  # On Windows: venv\Scripts\activate

psql -c "CREATE DATABASE cdl_stats;"   ```

```

3. **Install dependencies:**

4. **Configure database connection** (optional)   ```bash

```bash   pip install -r requirements.txt

# Set environment variable for custom database URL   ```

export DATABASE_URL="postgresql://user:password@localhost:5432/cdl_stats"

```### Running the Dashboard



5. **Initialize database**#### Option A: With Realistic Sample Data (Recommended)

```bash

python3 -c "from database import init_db; init_db()"1. **Generate realistic data with real CDL teams and players:**

```   ```bash

   python fetch_breakingpoint_data.py

6. **Run the dashboard**   ```

```bash   This creates `data/breakingpoint_cod_stats.csv` with realistic CDL data based on the 2025-2026 season teams and players.

# Main dashboard

streamlit run app.py2. **Run the Streamlit app:**

   ```bash

# Or Hardpoint-specific dashboard   streamlit run app.py

streamlit run hardpoint_dashboard.py   ```

```

3. **Open your browser** to `http://localhost:8501`

7. **Refresh data**

   - Open dashboard in browser (default: http://localhost:8501)#### Option B: With Original Synthetic Data

   - Click **🔄 Refresh Data** button to scrape latest matches

   - First refresh takes ~3 minutes (fetches last 7 days)If you prefer simpler synthetic data:

   - Subsequent refreshes take 10-60 seconds (only new matches)

```bash

---python generate_sample_data.py

streamlit run app.py

## 📖 How It Works```



### Data Flow#### Option C: With Real breakingpoint.gg Data

```

User clicks "Refresh Data" buttonFor real CDL statistics:

         ↓

System checks last_scrape_date from database1. **Read the comprehensive guide:** See `REAL_DATA_GUIDE.md` for detailed instructions on:

         ↓   - Manually exporting data from breakingpoint.gg

Scrapes breakingpoint.gg (only new matches since last update)   - Requesting API access

         ↓   - Setting up web scraping

Caches results to PostgreSQL   - Column mapping and customization

         ↓

Updates last_scrape_date timestamp2. **Quick start:** Download data from https://breakingpoint.gg/stats and place in `data/breakingpoint_cod_stats.csv`

         ↓

Reloads UI with fresh data3. **Run the dashboard:**

```   ```bash

   streamlit run app.py

### Timestamp Tracking   ```

- **Last updated**: Displayed in dashboard header

- **Stored in database**: `scrape_metadata` table   **Match Context:**

- **Smart incremental scraping**: Only fetches matches from last update to now   - `match_id` (string/int)

- **Default**: 7 days ago if no previous scrape exists   - `date` (datetime)

   - `event_name` (string)

---   - `series_type` (string, e.g., "BO5")

   - `is_lan` (bool)

## 🗂️ Project Structure   - `season` (int)



```   **Teams & Players:**

cdl_dashboard/   - `team_name` (string)

├── app.py                      # Main dashboard (full match analysis)   - `opponent_team_name` (string)

├── hardpoint_dashboard.py      # Hardpoint-specific dashboard   - `player_name` (string)

├── database.py                 # PostgreSQL ORM and caching

├── scrape_breakingpoint.py     # Web scraper for breakingpoint.gg   **Mode & Map:**

├── stats_utils.py              # Statistical calculations   - `mode` (string: "Hardpoint", "Search & Destroy", "Overload")

├── config.py                   # Configuration constants   - `map_name` (string)

├── requirements.txt            # Python dependencies   - `map_number` (int)

├── README.md                   # This file

├── docs/                       # Documentation   **Player Stats (per map):**

│   ├── QUICKSTART.md          # Detailed setup guide   - `kills` (int)

│   ├── ARCHITECTURE.md        # System design documentation   - `deaths` (int)

│   ├── CODEBASE_OVERVIEW.md   # Complete code walkthrough   - `assists` (int) — optional

│   ├── CHANGELOG.md           # Version history   - `damage` (float/int) — optional

│   └── REFRESH_BUTTON_GUIDE.md # Refresh system documentation   - `rating` (float) — optional

└── data/                       # Data files   - `won_map` (bool) — optional

    ├── team_logos/            # Team logo images (33 teams)   - `hill_time` (int, for HP) — optional

    └── map_images/            # Map images (10 maps)   - `plants` (int, for S&D) — optional

```

2. **Place your CSV** in the `data/` folder (default: `data/breakingpoint_cod_stats.csv`)

---

3. **If your CSV column names differ**, edit the `load_data()` function in `app.py`:

## 💾 Database Schema   ```python

   @st.cache_data

### Tables   def load_data(csv_path: str) -> pd.DataFrame:

       df = pd.read_csv(csv_path)

#### `matches`       

Stores match-level metadata       # Map your column names to the expected schema:

- `match_id` (PRIMARY KEY)       # df = df.rename(columns={

- `date`, `event_name`, `series_type`       #     'your_col_name': 'kills',

- `team1_name`, `team2_name`       #     'your_other_col': 'deaths',

- `team1_score`, `team2_score`       #     ...

- Indexes on `date`       # })

       

#### `player_stats`       if 'date' in df.columns:

Stores per-map player statistics           df['date'] = pd.to_datetime(df['date'])

- `id` (PRIMARY KEY)       

- `match_id` (FOREIGN KEY → matches)       return df

- `player_name`, `team_name`, `opponent_team_name`   ```

- `map_number`, `map_name`, `mode`

- `kills`, `deaths`, `assists`, `damage`, `rating`4. **Run the app:**

- `won_map` (boolean)   ```bash

- Indexes on `match_id`, `player_name`, `team_name`   streamlit run app.py

   ```

#### `scrape_metadata`

Stores scraping timestamps## Project Structure

- `id` (PRIMARY KEY)

- `last_scrape_date` (timestamp of last match scraped)```

- `scrape_timestamp` (when scrape operation occurred)cdl_dashboard/

├── app.py                          # Main Streamlit application

---├── stats_utils.py                  # Helper functions for stats aggregation

├── generate_sample_data.py         # Generate synthetic test data

## 🎯 Usage Examples├── requirements.txt                # Python dependencies

├── data/

### Main Dashboard Features│   └── breakingpoint_cod_stats.csv # Your CDL stats CSV (create this)

└── README.md                       # This file

#### Match List View```

- See all completed matches with scores

- Filter by team, mode, or date range## Customization & Extension

- Click match to see detailed breakdown

### Adding New Metrics

#### Match Detail View

- Per-map player statistics tables1. **Create a helper function** in `stats_utils.py`:

- Team performance comparisons   ```python

- Interactive kill charts   def get_first_bloods(df, player, ...):

- K/D ratio visualizations       """Calculate first blood statistics."""

       # Your logic here

#### Player Overview       return result

- Career statistics across all matches   ```

- Performance by game mode

- Win rate analysis2. **Wire it into the dashboard** in `app.py`:

- Head-to-head comparisons   ```python

   first_bloods = get_first_bloods(player_df, selected_player)

### Hardpoint Dashboard Features   st.metric("First Bloods", first_bloods)

   ```

#### Map Stats

- Average kills per Hardpoint map### Adding New Pages

- Filter by team, win/loss, opponent

- Detailed performance metrics1. **Create a new page function** in `app.py`:

   ```python

#### Player Stats   def page_new_analysis():

- Top performers by average kills       st.markdown('<div class="title-section"><h2>🆕 New Analysis</h2></div>', 

- Full player statistics table                   unsafe_allow_html=True)

- Win percentage tracking       # Your content here

   ```

#### Event Stats

- Tournament-level aggregations2. **Add it to the `pages` dictionary**:

- Match counts and participation   ```python

   pages = {

---       "📊 Data Overview": page_data_overview,

       # ... other pages ...

## 🔧 Configuration       "🆕 New Analysis": page_new_analysis,

   }

### Environment Variables   ```



```bash### Handling Missing Columns

# Database connection (optional, defaults to localhost)

export DATABASE_URL="postgresql://user:password@host:port/database"The dashboard gracefully skips features if columns are missing:

```- If `rating` is absent, rating metrics won't display

- If `won_map` is absent, win rates won't compute

### config.py Settings- If `hill_time` is absent, mode-specific HP stats won't show

- `CDL_MAPS` - Official competitive map pools

- `DATA_CSV_PATH` - CSV cache location## Troubleshooting

- Database connection settings

- UI configuration**Error: "Data file not found"**

- Ensure `data/breakingpoint_cod_stats.csv` exists

---- Run `python generate_sample_data.py` to create sample data



## 📊 Performance**Error: "No players available"**

- Check that your CSV has a `player_name` column

- **Initial scrape**: ~180 seconds (7 days of matches)- Verify your date filters aren't too restrictive

- **Incremental refresh**: 10-60 seconds (only new matches)

- **Database load**: 0.08 seconds (2,250x faster than scraping)**Charts not displaying**

- **UI response**: <1 second for most operations- Ensure Plotly is installed: `pip install plotly`

- **Storage**: ~2MB per 2,500 player records- Check that your data has the required columns



---**Performance issues with large datasets**

- The `@st.cache_data` decorator caches loaded data

## 🛠️ Development- Consider filtering by season/event in the sidebar first



### Running Tests## Data Notes

```bash

# Test database connection### Schema Flexibility

python3 -c "from database import init_db, get_cache_stats; init_db(); print(get_cache_stats())"This dashboard is designed to handle varying CSV schemas:

- Missing columns won't break the app (graceful degradation)

# Test scraping function- You can rename columns in the `load_data()` function

python3 -c "from scrape_breakingpoint import scrape_live_data; df = scrape_live_data(start_date='2025-12-28'); print(f'Scraped {len(df) if df is not None else 0} records')"- Mode values are flexible (any string works; examples: "Hardpoint", "Search & Destroy", "Overload")



# Test imports### Tips for breakingpoint.gg Exports

python3 -c "import streamlit; from database import *; from scrape_breakingpoint import *; print('✅ All imports successful')"- Download your data in CSV format from breakingpoint.gg

```- Ensure dates are in ISO format (YYYY-MM-DD) or recognizable by pandas

- Column names should ideally match the schema above, but the dashboard adapts

### Tech Stack

- **Backend**: Python 3.12, PostgreSQL, SQLAlchemy, pandas## Future Enhancements

- **Frontend**: Streamlit, Plotly

- **Scraping**: requests, BeautifulSoup4- [ ] Streaks and form analysis

- **Images**: Pillow (PIL)- [ ] First blood / non-traded kill stats

- [ ] Advanced filtering (multiple modes/maps simultaneously)

---- [ ] Playoff vs Regular Season comparison

- [ ] Team-level aggregations and team vs team analysis

## 📚 Documentation- [ ] Export/download functionality for reports

- [ ] Real-time data sync with breakingpoint.gg API (if available)

| Document | Description |

|----------|-------------|## License

| [QUICKSTART.md](docs/QUICKSTART.md) | Detailed setup and installation guide |

| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and data flow |This project is for personal/community use. Ensure you have permission to use breakingpoint.gg data.

| [CODEBASE_OVERVIEW.md](docs/CODEBASE_OVERVIEW.md) | Complete code walkthrough |

| [REFRESH_BUTTON_GUIDE.md](docs/REFRESH_BUTTON_GUIDE.md) | How the refresh system works |## Questions?

| [CHANGELOG.md](docs/CHANGELOG.md) | Version history and updates |

For issues or feature requests, refer to the comments in the code or extend the dashboard as needed.

---

---

## 🐛 Troubleshooting

**Built with ❤️ for CDL fans using Streamlit, Pandas, and Plotly**

### "No data available in database"
**Solution**: Click the **🔄 Refresh Data** button to scrape initial data

### "No new matches found"
**Normal** - No matches completed since last update. Check breakingpoint.gg for new matches.

### Database connection error
**Solution**: Verify PostgreSQL is running and `DATABASE_URL` is correct
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Refresh button shows error
**Debug steps**:
1. Check terminal output for detailed error messages
2. Verify breakingpoint.gg is accessible: `curl https://breakingpoint.gg/matches`
3. Check database connection
4. Try refreshing page and clicking again

---

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Cloud Hosting
Compatible with:
- **Streamlit Cloud** (recommended)
- **Heroku**
- **AWS/GCP** with managed PostgreSQL
- **Railway**
- **Render**

**Requirements**:
- Set `DATABASE_URL` environment variable
- PostgreSQL database (free tier available on Supabase, Neon, Railway)
- No GitHub Actions or cron jobs needed - refresh button works in cloud!

---

## 📝 License

This project is open source. Feel free to use and modify for your own purposes.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional visualizations
- More game modes
- Player comparison features
- Export functionality
- API endpoints

---

## 📧 Contact

**Author**: Justin Woo  
**Created**: January 2026  
**Last Updated**: January 1, 2026

---

## ⭐ Features Roadmap

### Upcoming
- [ ] Auto-refresh timer (optional background updates)
- [ ] Custom date range picker
- [ ] Player performance trends over time
- [ ] Team head-to-head comparisons
- [ ] Export to CSV/Excel
- [ ] Dark mode theme toggle

### Completed ✅
- [x] On-demand refresh button
- [x] Incremental timestamp tracking
- [x] PostgreSQL caching
- [x] CDL map filtering
- [x] Hardpoint specialized dashboard
- [x] Match detail views with per-map stats

---

**Built with ❤️ for the Call of Duty League community**
