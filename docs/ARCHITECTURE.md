# CDL Dashboard - Architecture & Design Guide

## Overview

The CDL Dashboard is a modular Streamlit application for analyzing Call of Duty League statistics from breakingpoint.gg exports. It's built with extensibility and customization in mind.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit App (app.py)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Page Navigation (sidebar)                      │   │
│  │  - Data Overview                                │   │
│  │  - Player Overview                              │   │
│  │  - Per-Map/Mode Breakdown                       │   │
│  │  - Head-to-Head                                 │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
     ┌───────────┴────────────┐
     │                        │
┌────▼──────────────┐   ┌────▼──────────────┐
│  stats_utils.py   │   │   config.py       │
│  (14+ Functions)  │   │  (Configuration)  │
│                   │   │                   │
│ - get_player_*    │   │ - Column Mapping  │
│ - get_mode_*      │   │ - Color Schemes   │
│ - get_map_*       │   │ - Defaults        │
│ - get_vs_*        │   │ - Thresholds      │
│ - get_summary_*   │   │                   │
└───────┬───────────┘   └───────────────────┘
        │
┌───────▼──────────────┐
│   Data Layer         │
│                      │
│ CSV → Pandas DF      │
│                      │
│ @st.cache_data       │
└──────────────────────┘
```

## Component Description

### 1. **app.py** - Main Dashboard Application

**Purpose:** Streamlit UI and page logic

**Key Components:**
- **Page Functions:** `page_data_overview()`, `page_player_overview()`, `page_map_mode_breakdown()`, `page_vs_opponents()`
- **Sidebar Filters:** `render_sidebar_filters()` - Global filtering logic
- **Data Loading:** `load_data()` - Cached CSV loading with column parsing
- **Styling:** Custom CSS for cards and sections

**Dependencies:**
- `streamlit` - UI framework
- `plotly` - Interactive charts
- `pandas` - Data manipulation
- `stats_utils` - Stats calculations

**Page Count:** 4 interactive pages
**Lines of Code:** ~550

### 2. **stats_utils.py** - Statistical Aggregation Library

**Purpose:** Pure data processing functions (no UI)

**Key Functions:**

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_player_overall_stats()` | Overall averages across all maps/modes | Dict with KPIs |
| `get_player_mode_stats()` | Stats split by game mode | DataFrame (Hardpoint, S&D, Overload) |
| `get_player_map_mode_stats()` | Per-map stats within a mode | DataFrame with map breakdown |
| `get_player_vs_opponent_stats()` | Stats against specific opponents | DataFrame by opponent |
| `get_player_timeline()` | Map-by-map progression over time | DataFrame ordered by date |
| `get_summary_stats()` | High-level dataset summary | Dict with totals |
| `get_mode_distribution()` | Count of maps by mode | DataFrame |
| `get_map_distribution()` | Count of maps by name | DataFrame |
| `get_players_by_team()` | List of players for a team | List of strings |

**Design Principles:**
- Pure functions (no side effects)
- Accepts filtered DataFrames as input
- Returns structured DataFrames/dicts
- Graceful handling of missing columns
- Flexible filtering parameters

**Dependencies:**
- `pandas` - Data manipulation
- `numpy` - Numeric operations

**Lines of Code:** ~350

### 3. **config.py** - Configuration & Constants

**Purpose:** Centralized settings and customization

**Contents:**
- **Column Mapping:** Expected vs actual column names
- **Game Modes:** List of valid modes (Hardpoint, S&D, Overload)
- **Color Schemes:** Plotly color scale assignments
- **Display Settings:** Which stats to show, precision levels
- **Paths:** Data file locations
- **UI Customization:** Titles, descriptions, themes
- **Performance Thresholds:** Excellence levels for stats

**Usage:**
```python
from config import GAME_MODES, COLOR_SCHEMES, DISPLAY_STATS
```

**Lines of Code:** ~120

### 4. **generate_sample_data.py** - Synthetic Data Generator

**Purpose:** Create realistic test data for development

**Features:**
- Generates 50 matches (configurable)
- 12 realistic CDL teams
- 3-4 players per team
- Multiple game modes
- Realistic stat distributions
- Date range spanning 150 days

**Output:**
- CSV file: `data/breakingpoint_cod_stats.csv`
- 1,200+ records (configurable)
- All required columns

**Usage:**
```bash
python generate_sample_data.py
```

**Lines of Code:** ~130

### 5. **examples.py** - Usage Examples

**Purpose:** Demonstrate programmatic use of stats_utils

**Examples:**
1. Load and inspect data
2. Get player overall stats
3. Compare mode breakdown
4. Map-specific analysis
5. Head-to-head stats
6. Team analysis
7. Export stats to CSV
8. Trend analysis

**Usage:**
```bash
python examples.py
```

**Lines of Code:** ~200

---

## Data Flow

### Query Lifecycle (Per User Interaction)

```
User Selects Filters (sidebar)
    ↓
render_sidebar_filters() applies filters
    ↓
filtered_df created (subset of main df)
    ↓
select page function
    ↓
page function calls stats_utils
    ↓
stats_utils.get_* functions
    ↓
Result aggregation (groupby, agg, etc.)
    ↓
Return structured result (dict/DataFrame)
    ↓
Page function creates charts/tables
    ↓
Plotly/st.dataframe renders output
    ↓
Display to user
```

### Caching Strategy

```
@st.cache_data
load_data(csv_path)
    ↓
CSV loaded once, held in memory
    ↓
Reused across all page views
    ↓
Filters applied in-memory (fast)
    ↓
Cache invalidates if code changes
```

---

## Extending the Dashboard

### Adding a New Statistic

1. **Define in `stats_utils.py`:**
   ```python
   def get_player_first_bloods(df, player, **filters):
       """Calculate first blood statistics."""
       # Your logic
       return result
   ```

2. **Wire into `app.py`:**
   ```python
   first_bloods = get_player_first_bloods(filtered_df, selected_player)
   st.metric("First Bloods", first_bloods)
   ```

### Adding a New Page

1. **Create page function in `app.py`:**
   ```python
   def page_new_analysis():
       st.markdown('...')
       filtered_df = render_sidebar_filters()
       # Your content
   ```

2. **Register in pages dict:**
   ```python
   pages = {
       "📊 Data Overview": page_data_overview,
       "🆕 New Page": page_new_analysis,
   }
   ```

### Adapting to Different CSV Schemas

1. **Option A: Rename in `load_data()`:**
   ```python
   df = df.rename(columns={
       'Player': 'player_name',
       'Opponent': 'opponent_team_name',
   })
   ```

2. **Option B: Use `config.py` mapping:**
   ```python
   # Edit config.py EXPECTED_COLUMNS
   # Then call rename_columns(df) in load_data()
   ```

### Adding Conditional Features

```python
if 'rating' in df.columns:
    st.metric("Avg Rating", overall_stats['avg_rating'])
else:
    st.info("Rating data not available in CSV")
```

---

## Performance Considerations

### Current Limitations

- **Dataset Size:** Optimized for <50K records (real-time filtering)
- **Caching:** Data cached in memory (suitable for ~10MB CSVs)
- **Chart Updates:** Real-time on filter change (minor latency expected)

### Optimization Strategies

For larger datasets:

1. **Pre-aggregate data:**
   ```python
   # Cache computed aggregates instead of raw records
   @st.cache_data
   def load_aggregated_stats(csv_path):
       df = pd.read_csv(csv_path)
       return df.groupby(...).agg(...)
   ```

2. **Use database backend:**
   ```python
   # Replace CSV with SQL queries
   import sqlite3
   conn = sqlite3.connect('stats.db')
   df = pd.read_sql(query, conn)
   ```

3. **Pagination:**
   ```python
   # Limit rows shown in tables
   st.dataframe(df.head(100))
   ```

---

## Testing & Validation

### Unit Testing Stats Functions

```python
import pandas as pd
from stats_utils import get_player_overall_stats

def test_player_stats():
    df = pd.read_csv('data/test_data.csv')
    stats = get_player_overall_stats(df, 'TestPlayer')
    assert stats['maps_played'] > 0
    assert stats['kd_ratio'] > 0
```

### Integration Testing

```bash
# Run the examples script
python examples.py

# Verify no errors and expected output
```

### UI Testing

```bash
# Manual testing checklist
streamlit run app.py

# Test each page:
# - [ ] Data Overview (all filters work)
# - [ ] Player Overview (multi-select works)
# - [ ] Map/Mode (heatmap renders)
# - [ ] Head-to-Head (opponent filter works)

# Test edge cases:
# - [ ] Empty filters
# - [ ] Single player/mode
# - [ ] Large date range
```

---

## Column Schema Reference

### Required Columns

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | str/int | Unique match identifier |
| `date` | datetime | Match date |
| `team_name` | str | Player's team |
| `opponent_team_name` | str | Opposing team |
| `player_name` | str | Player name |
| `mode` | str | Game mode (Hardpoint, S&D, Overload) |
| `map_name` | str | Map name |
| `kills` | int | Player kills |
| `deaths` | int | Player deaths |
| `damage` | float | Player damage dealt |

### Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `assists` | int | Player assists |
| `rating` | float | breakingpoint.gg rating |
| `won_map` | bool | Did player's team win? |
| `hill_time` | int | Time on hill (Hardpoint) |
| `plants` | int | Bomb plants (S&D) |
| `defuses` | int | Bomb defuses (S&D) |
| `event_name` | str | Event name |
| `series_type` | str | Series type (BO3, BO5) |
| `is_lan` | bool | LAN or online |
| `season` | int | CDL season |

---

## Troubleshooting Guide

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError: CSV` | Missing data file | Run `generate_sample_data.py` |
| `KeyError: 'player_name'` | Wrong column names | Update `load_data()` or `config.py` |
| `ValueError: Cannot reshape` | Data type mismatch | Check CSV for non-numeric kills/deaths |
| `Empty dataframe` | Filters too restrictive | Adjust date range in sidebar |
| `Chart not rendering` | Missing data for chart | Verify mode/map values exist |

---

## Contributing Guidelines

1. **Keep functions pure** - No side effects in `stats_utils.py`
2. **Add docstrings** - Explain parameters and returns
3. **Handle missing columns** - Use `if 'column' in df.columns`
4. **Test edge cases** - Empty filters, single values, large ranges
5. **Document changes** - Update README.md if adding features
6. **Follow naming** - Use snake_case for functions, CamelCase for classes

---

## Future Enhancements

- [ ] Real-time data sync from breakingpoint.gg API
- [ ] Team-level aggregations
- [ ] Advanced filtering (multiple modes simultaneously)
- [ ] Performance comparisons (vs self, vs teammates, vs opponent)
- [ ] Streaks and form tracking
- [ ] Export/PDF reports
- [ ] Dashboard deployment (Heroku, AWS, Azure)
- [ ] Multi-season analysis
- [ ] Player market value predictions

---

## License & Attribution

This dashboard is for personal/community use. Ensure you have permission to use breakingpoint.gg data in your analysis.

**Built with:** Streamlit, Pandas, Plotly, NumPy

---

**Questions?** Refer to inline comments in code or extend the dashboard as needed!
