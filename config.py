"""
Configuration and constants for the CDL Dashboard.
Customize these settings to match your data schema and preferences.
"""

import os

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Cloud database URL (set via environment variable for Streamlit Cloud / GitHub Actions)
# For local development, falls back to localhost PostgreSQL
def get_database_url():
    """Get database URL from Streamlit secrets or environment variable."""
    try:
        import streamlit as st
        # Try to get from Streamlit secrets first (for Streamlit Cloud)
        return st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://justinwoo@localhost:5432/cdl_stats"))
    except (ImportError, FileNotFoundError, AttributeError):
        # Fall back to environment variable (for local development)
        return os.getenv("DATABASE_URL", "postgresql://justinwoo@localhost:5432/cdl_stats")

DATABASE_URL = get_database_url()

# ============================================================================
# PLAYER POSITIONS (2026 CDL Season)
# ============================================================================
PLAYER_POSITIONS = {
    # Boston Breach
    'Cammy': 'AR',
    'Snoopy': 'SMG',
    'Purj': 'SMG',
    'Nastie': 'Flex',
    
    # Carolina Royal Ravens
    'SlasheR': 'AR',
    'Nero': 'SMG',
    'Lurqxx': 'SMG',
    'Craze': 'Flex',
    
    # Cloud9 New York
    'Mack': 'AR',
    'Afro': 'SMG',
    'Beans': 'SMG',
    'Vivid': 'Flex',
    
    # FaZe Vegas
    'Drazah': 'AR',
    'Abuzah': 'SMG',
    '04': 'SMG',
    'Simp': 'Flex',
    
    # G2 Minnesota
    'Skyz': 'AR',
    'Estreal': 'SMG',
    'Kremp': 'SMG',
    'Mamba': 'Flex',
    
    # Los Angeles Thieves
    'aBeZy': 'AR',
    'HyDra': 'SMG',
    'Scrap': 'SMG',
    'Kenny': 'Flex',
    
    # Miami Heretics
    'MettalZ': 'AR',
    'Traixx': 'SMG',
    'SupeR': 'SMG',
    'RenKoR': 'Flex',
    
    # OpTic Texas
    'Shotzzy': 'SMG',
    'Dashy': 'AR',
    'Huke': 'SMG',
    'Mercules': 'Flex',
    
    # Paris Gentle Mates
    'Envoy': 'AR',
    'Ghosty': 'SMG',
    'Neptune': 'SMG',
    'Sib': 'Flex',
    
    # Riyadh Falcons
    'Cellium': 'AR',
    'Pred': 'Flex',
    'Exnid': 'SMG',
    'KiSMET': 'SMG',
    
    # Toronto KOI
    'ReeaL': 'AR',
    'CleanX': 'SMG',
    'JoeDeceives': 'SMG',
    'Insight': 'Flex',
    
    # Vancouver Surge
    'Abe': 'AR',
    'Gwinn': 'SMG',
    'Lunarz': 'SMG',
    'Lqgend': 'Flex',
}

def get_player_position(player_name: str) -> str:
    """Get the position for a player, returns 'Unknown' if not found"""
    return PLAYER_POSITIONS.get(player_name, 'Unknown')

# ============================================================================
# COLUMN MAPPING
# ============================================================================
# If your breakingpoint.gg export uses different column names, map them here.
# Then update the load_data() function in app.py to use these mappings.

EXPECTED_COLUMNS = {
    # Match metadata
    'match_id': 'match_id',
    'date': 'date',
    'event_name': 'event_name',
    'series_type': 'series_type',
    'is_lan': 'is_lan',
    'season': 'season',
    
    # Team / Player info
    'team_name': 'team_name',
    'opponent_team_name': 'opponent_team_name',
    'player_name': 'player_name',
    
    # Mode / Map
    'mode': 'mode',
    'map_name': 'map_name',
    'map_number': 'map_number',
    
    # Stats
    'kills': 'kills',
    'deaths': 'deaths',
    'assists': 'assists',
    'damage': 'damage',
    'rating': 'rating',
    'won_map': 'won_map',
    
    # Optional mode-specific stats
    'hill_time': 'hill_time',
    'plants': 'plants',
    'defuses': 'defuses',
}

# ============================================================================
# GAME MODES
# ============================================================================
GAME_MODES = [
    'Hardpoint',
    'Search & Destroy',
    'Overload',
]

# ============================================================================
# COLOR SCHEMES
# ============================================================================
# Plotly color scales: https://plotly.com/python/builtin-colorscales/

COLOR_SCHEMES = {
    'kills': 'Blues',
    'damage': 'Viridis',
    'kd_ratio': 'Reds',
    'win_rate': 'RdYlGn',
    'heatmap': 'YlOrRd',
    'default': 'Plasma',
}

# ============================================================================
# METRICS & AGGREGATION
# ============================================================================

# Define which stats to display in overview tables
DISPLAY_STATS = [
    'Maps_Played',
    'Avg_Kills',
    'Avg_Deaths',
    'KD_Ratio',
    'Avg_Damage',
    'Avg_Rating',
    'Win_Rate',
]

# Rounding precision
PRECISION = {
    'kd_ratio': 2,
    'win_rate': 2,
    'average': 2,
    'total': 0,
}

# ============================================================================
# DATA PATHS
# ============================================================================

DATA_CSV_PATH = "data/breakingpoint_cod_stats.csv"

# ============================================================================
# CUSTOM COLUMN RENAME FUNCTION
# ============================================================================
# Use this if your CSV has different column names than the standard schema

def rename_columns(df):
    """
    Rename columns from your export format to the standard schema.
    
    Example:
        If your CSV has 'Player' instead of 'player_name', add:
        'Player': 'player_name'
    """
    rename_map = {
        # 'your_column_name': 'expected_column_name',
    }
    
    if rename_map:
        df = df.rename(columns=rename_map)
    
    return df

# ============================================================================
# FILTERS & DEFAULTS
# ============================================================================

DEFAULT_DATE_OFFSET_DAYS = 90  # Show last 90 days by default
DEFAULT_TOP_N_PLAYERS = 2      # Show top N players in multi-select
DEFAULT_TOP_N_OPPONENTS = 3    # Show top N opponents in head-to-head

# ============================================================================
# UI CUSTOMIZATION
# ============================================================================

DASHBOARD_TITLE = "🎮 CDL Stats Dashboard"
DASHBOARD_SUBTITLE = "Interactive analytics for Call of Duty League statistics from breakingpoint.gg"

# Page descriptions (shown in sidebar)
PAGE_DESCRIPTIONS = {
    "📊 Data Overview": "Overall data summary, trends, and distributions",
    "👤 Player Overview": "Individual player statistics and mode breakdowns",
    "🗺️ Map/Mode Breakdown": "Per-map analysis with opponent heatmaps",
    "⚔️ Head-to-Head": "Performance against specific opponent teams",
}

# ============================================================================
# PERFORMANCE THRESHOLDS
# ============================================================================
# Use these to color-code or flag performance levels

PERFORMANCE_THRESHOLDS = {
    'kd_ratio': {
        'excellent': 1.5,
        'good': 1.2,
        'average': 1.0,
        'below_average': 0.8,
    },
    'avg_kills': {
        'excellent': 30,
        'good': 25,
        'average': 20,
        'below_average': 15,
    },
    'win_rate': {
        'excellent': 0.65,
        'good': 0.55,
        'average': 0.50,
        'below_average': 0.40,
    },
}

# ============================================================================
# ADVANCED OPTIONS
# ============================================================================

# Cache data for faster loading
USE_CACHE = True

# Number of rows to display in tables by default
TABLE_MAX_ROWS = 100

# Enable debug mode (prints extra info)
DEBUG_MODE = False

# Maximum number of players to compare in Player Overview
MAX_PLAYERS_TO_COMPARE = 5
