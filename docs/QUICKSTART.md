# 🚀 Quick Start Guide - CDL Stats Dashboard

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample data
python generate_sample_data.py

# 3. Run the dashboard
streamlit run app.py
```

Dashboard opens at: **http://localhost:8501**

---

## What's Included

✅ **4 Interactive Pages:**
1. **Data Overview** - Summary metrics, trends, mode/map distribution
2. **Player Overview** - Individual player stats, mode breakdowns, timeline
3. **Per-Map/Mode** - Map-specific analysis with heatmaps
4. **Head-to-Head** - Stats vs specific opponent teams

✅ **Smart Features:**
- Multi-filter sidebar (date, season, event, LAN/Online)
- Dynamic calculations (K/D, win rate, averages)
- Responsive Plotly charts
- Graceful handling of missing data columns

✅ **Sample Data:**
- 50 synthetic matches
- 12 CDL teams
- 1,200 individual map records
- Mix of modes: Hardpoint, S&D, Overload

---

## Using Your Own Data

### From breakingpoint.gg:

1. Export your stats as CSV
2. Place in `data/breakingpoint_cod_stats.csv`
3. If column names differ, edit `load_data()` in `app.py` (see README.md)
4. Run `streamlit run app.py`

### Example CSV Format:

```
match_id,date,event_name,series_type,is_lan,season,team_name,opponent_team_name,player_name,mode,map_name,map_number,kills,deaths,assists,damage,rating,won_map
MATCH_001,2024-01-15,CDL Regular Season,BO5,True,2024,Team A,Team B,Player1,Hardpoint,Tuscan,1,25,18,5,950,1.45,True
```

---

## File Guide

```
cdl_dashboard/
├── app.py                      # Main dashboard (4 pages, all interactive)
├── stats_utils.py              # Helper functions (14 utility functions)
├── generate_sample_data.py     # Create synthetic data for testing
├── requirements.txt            # Dependencies (streamlit, pandas, plotly, numpy)
├── data/
│   └── breakingpoint_cod_stats.csv  # Your data goes here
├── README.md                   # Full documentation
├── QUICKSTART.md               # This file
└── .gitignore                  # Git ignore rules
```

---

## Extending the Dashboard

### Add a New Stat

In `stats_utils.py`, add:
```python
def get_new_stat(df, player, ...):
    """Your custom statistic."""
    return result
```

Then use it in `app.py`:
```python
stat_value = get_new_stat(filtered_df, selected_player)
st.metric("My New Stat", stat_value)
```

### Add a New Page

In `app.py`, create:
```python
def page_new_view():
    st.markdown('<div class="title-section"><h2>🆕 New View</h2></div>', unsafe_allow_html=True)
    # Your content
```

Then add to `pages` dict:
```python
pages = {
    "📊 Data Overview": page_data_overview,
    "🆕 New View": page_new_view,
    ...
}
```

---

## Keyboard Shortcuts (in Streamlit)

- `c` - Clear cache
- `r` - Rerun script
- `t` - Toggle theme (dark/light)
- `?` - Help menu

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Data file not found" | Run `python generate_sample_data.py` |
| "No players available" | Check CSV has `player_name` column |
| Blank page | Check console for errors; verify CSV format |
| Slow performance | Filter by date/season first; data > 10K rows may need optimization |

---

## Next Steps

1. ✅ Run the sample dashboard
2. ✅ Explore all 4 pages and filters
3. ✅ Export your own data from breakingpoint.gg
4. ✅ Update CSV location in `load_data()` if needed
5. ✅ Customize colors/layout as desired
6. ✅ Add new pages/metrics for your use case

---

**Ready to dive in? Run:**
```bash
streamlit run app.py
```

**Happy analyzing! 🎮**
