"""
CDL Stats Dashboard - Streamlit App
Interactive dashboard for Call of Duty League statistics from breakingpoint.gg

Features:
- Data Overview: Summary and filtering with Position filter (AR/SMG/Flex)
- Player Overview: Overall averages across all modes/maps
- Per-Map/Mode Breakdown: Detailed performance by map and game mode
- Head-to-Head: Performance vs specific opponents

Author: CDL Dashboard Team
Date: 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json

from stats_utils import (
    get_player_overall_stats,
    get_player_mode_stats,
    get_player_map_mode_stats,
    get_player_vs_opponent_stats,
    get_player_timeline,
    get_summary_stats,
    get_mode_distribution,
    get_map_distribution,
    get_players_by_team,
)

try:
    from scrape_breakingpoint import update_data, get_data_status
except ImportError:
    def update_data(force_refresh=False):
        """Fallback if scraper not available"""
        return None
    
    def get_data_status():
        """Fallback if scraper not available"""
        return None

# Official CDL map pools by mode
CDL_MAPS = {
    'Hardpoint': ['Blackheart', 'Colossus', 'Den', 'Exposure', 'Scar'],
    'Search & Destroy': ['Colossus', 'Den', 'Exposure', 'Raid', 'Scar'],
    'Overload': ['Den', 'Exposure', 'Scar']
}

def filter_cdl_maps(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataframe to only include official CDL maps for each mode"""
    if df is None or df.empty:
        return df
    
    # Create a mask for valid map/mode combinations
    mask = pd.Series([False] * len(df), index=df.index)
    
    for mode, valid_maps in CDL_MAPS.items():
        mode_mask = (df['mode'] == mode) & (df['map_name'].isin(valid_maps))
        mask = mask | mode_mask
    
    filtered_df = df[mask].copy()
    
    return filtered_df

try:
    from database import init_db, get_cache_stats, DATABASE_AVAILABLE
except ImportError:
    DATABASE_AVAILABLE = False
    def init_db():
        return False
    def get_cache_stats():
        return {'is_cached': False}

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="CDL Stats Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better appearance
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .title-section {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin: 40px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .loading-text {
        color: white;
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        animation: pulse 1.5s ease-in-out infinite;
    }
    .loading-subtext {
        color: rgba(255,255,255,0.9);
        font-size: 16px;
        margin-top: 10px;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    .spinner {
        border: 8px solid rgba(255,255,255,0.2);
        border-top: 8px solid white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .upcoming-banner {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px 25px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .upcoming-banner-content {
        display: flex;
        align-items: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    .upcoming-match-item {
        background: rgba(255,255,255,0.2);
        padding: 8px 15px;
        border-radius: 8px;
        backdrop-filter: blur(10px);
        color: white;
        font-weight: 600;
        font-size: 14px;
        white-space: nowrap;
    }
    .upcoming-banner-title {
        color: white;
        font-size: 16px;
        font-weight: bold;
        margin-right: 15px;
    }
    .upcoming-vs {
        color: white;
        font-weight: bold;
        padding: 0 8px;
    }
    .player-image-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
    }
    .player-image-container img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    .player-detail-header {
        display: flex;
        align-items: center;
        gap: 30px;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .player-detail-image {
        flex-shrink: 0;
    }
    .player-detail-image img {
        width: 180px;
        height: 180px;
        object-fit: cover;
        border-radius: 12px;
        border: 4px solid white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .player-detail-info {
        flex-grow: 1;
        color: white;
    }
    .player-detail-name {
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .player-detail-meta {
        display: flex;
        gap: 30px;
        margin-top: 15px;
    }
    .player-detail-stat {
        background: rgba(255,255,255,0.2);
        padding: 12px 20px;
        border-radius: 8px;
        backdrop-filter: blur(10px);
    }
    .player-detail-stat-label {
        font-size: 12px;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .player-detail-stat-value {
        font-size: 24px;
        font-weight: bold;
        margin-top: 5px;
    }
    .pick-hit {
        color: #28a745;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        background: rgba(40, 167, 69, 0.1);
    }
    .pick-chalked {
        color: #dc3545;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        background: rgba(220, 53, 69, 0.1);
    }
    .pick-pending {
        color: #6c757d;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        background: rgba(108, 117, 125, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)# ============================================================================
# DATA LOADING & CACHING
# ============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_player_images_cached():
    """
    Cached version of player images loading.
    TTL of 600 seconds (10 minutes).
    """
    try:
        import json
        with open('data/player_images.json', 'r') as f:
            return json.load(f)
    except:
        return {}


def show_loading_animation(message="Loading CDL Data", subtext="Please wait while we fetch the latest stats..."):
    """Display an aesthetic loading animation"""
    return st.markdown(f"""
        <div class="loading-container">
            <div class="spinner"></div>
            <div class="loading-text">{message}</div>
            <div class="loading-subtext">{subtext}</div>
        </div>
    """, unsafe_allow_html=True)

def load_data_with_refresh() -> pd.DataFrame:
    """
    Load CDL stats data from database cache.
    Returns filtered DataFrame with CDL maps only.
    """
    from database import load_from_cache, init_db
    
    try:
        init_db()
        df = load_from_cache()
        
        if df is not None and not df.empty:
            # Convert date column to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # Filter to only official CDL maps
            df = filter_cdl_maps(df)
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return pd.DataFrame()


def refresh_data():
    """
    Refresh data by scraping from last scrape date to now.
    Updates the database and last scrape timestamp.
    """
    from database import get_last_scrape_date, cache_match_data, update_last_scrape_date
    from scrape_breakingpoint import scrape_live_data
    from datetime import datetime
    
    # Create a placeholder for the loading animation
    loading_placeholder = st.empty()
    
    try:
        # Show loading animation
        with loading_placeholder:
            show_loading_animation("🔄 Refreshing Data", "Scraping latest matches from breakingpoint.gg...")
        
        # Get the last scrape date
        last_date = get_last_scrape_date()
        if last_date:
            start_date_str = last_date.strftime('%Y-%m-%d')
        else:
            start_date_str = None
        
        # Scrape new data
        new_df = scrape_live_data(start_date=start_date_str)
        
        # Clear loading animation
        loading_placeholder.empty()
        
        if new_df is not None and not new_df.empty:
            # Cache to database
            cache_match_data(new_df)
            
            # Update last scrape date to now
            update_last_scrape_date(datetime.now())
            
            st.success(f"✅ Successfully refreshed! Added {len(new_df)} new player records.")
            
            # Clear the session state to force reload
            if 'df' in st.session_state:
                del st.session_state.df
            
            return True
        else:
            st.warning("No new matches found.")
            return False
            
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"❌ Error refreshing data: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False


# Legacy function for backward compatibility
def load_data(csv_path: str = "data/breakingpoint_cod_stats.csv") -> pd.DataFrame:
    """Legacy function - now just calls load_data_with_refresh()"""
    return load_data_with_refresh()


# ============================================================================
# FILTER LOGIC (NO UI - UI added per page) - WITH CACHING
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_filtered_data_cached(df_hash, selected_seasons_tuple, selected_events_tuple, lan_options_tuple):
    """
    Cached version of filter operations to avoid recomputing on every page load.
    Uses tuple parameters for hashability.
    TTL of 300 seconds (5 minutes) to balance freshness and performance.
    """
    df = st.session_state.df
    filtered_df = df.copy()
    
    # Convert tuples back to lists
    selected_seasons = list(selected_seasons_tuple) if selected_seasons_tuple else []
    selected_events = list(selected_events_tuple) if selected_events_tuple else []
    lan_options = list(lan_options_tuple) if lan_options_tuple else []
    
    # Apply season filter
    if selected_seasons:
        filtered_df = filtered_df[filtered_df['season'].isin(selected_seasons)]
    
    # Apply event filter
    if selected_events:
        filtered_df = filtered_df[filtered_df['event_name'].isin(selected_events)]
    
    # Filter by LAN/Online
    lan_bool_map = {}
    if "LAN" in lan_options:
        lan_bool_map[True] = True
    if "Online" in lan_options:
        lan_bool_map[False] = True
    
    if lan_bool_map:
        filtered_df = filtered_df[filtered_df['is_lan'].isin(lan_bool_map.keys())]
    
    return filtered_df


def get_filtered_data(selected_seasons=None, selected_events=None, lan_options=None):
    """Apply filters to the dataframe without rendering UI - uses caching for performance."""
    # If no filters provided, use all data
    if selected_seasons is None:
        selected_seasons = sorted(st.session_state.df['season'].unique())
    if selected_events is None:
        selected_events = sorted(st.session_state.df['event_name'].unique())
    if lan_options is None:
        lan_options = ["LAN", "Online"]
    
    # Create a hash of the dataframe for cache invalidation
    df_hash = hash(str(st.session_state.df.shape) + str(st.session_state.df.columns.tolist()))
    
    # Convert lists to tuples for hashability
    seasons_tuple = tuple(sorted(selected_seasons)) if selected_seasons else tuple()
    events_tuple = tuple(sorted(selected_events)) if selected_events else tuple()
    lan_tuple = tuple(sorted(lan_options)) if lan_options else tuple()
    
    return get_filtered_data_cached(df_hash, seasons_tuple, events_tuple, lan_tuple)


def render_sidebar_filters():
    """Legacy function - returns all data (filters moved to individual pages)."""
    # Return reference instead of copy for better performance
    return st.session_state.df


# ============================================================================
# PAGE 1: DATA OVERVIEW
# ============================================================================

def page_data_overview():
    """Display overall data summary and distribution."""
    st.markdown('<div class="title-section"><h2>📊 Data Overview</h2></div>', 
                unsafe_allow_html=True)
    
    filtered_df = render_sidebar_filters()
    
    # Default to maps 1-3 (map_number 1, 2, or 3)
    filtered_df = filtered_df[filtered_df['map_number'].isin([1, 2, 3])]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Matches", filtered_df['match_id'].nunique())
    with col2:
        st.metric("Total Maps", len(filtered_df))
    with col3:
        st.metric("Total Players", filtered_df['player_name'].nunique())
    with col4:
        st.metric("Total Teams", filtered_df['team_name'].nunique())
    
    st.divider()
    
    # ========== PLAYER STATS TABLE SECTION ==========
    st.markdown("### 👥 Player Statistics")
    
    # Load player images
    if 'player_images' not in st.session_state:
        st.session_state.player_images = load_player_images_cached()
    
    # Page-level filters for player stats
    st.markdown("**Filters:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Game mode filter - single selection with default "Maps 1-3"
        mode_options = ["Maps 1-3", "Hardpoint", "Search & Destroy", "Overload"]
        selected_mode = st.selectbox(
            "Game Mode",
            mode_options,
            index=0,
            key="player_mode_filter"
        )
    
    with col2:
        # Map filter - single selection, default empty
        maps = sorted(filtered_df['map_name'].unique())
        selected_map = st.selectbox(
            "Map",
            [""] + maps,
            index=0,
            key="player_map_filter"
        )
    
    with col3:
        # Opponent filter - single selection, default empty
        opponents = sorted(filtered_df['opponent_team_name'].unique())
        selected_opponent = st.selectbox(
            "Opponent",
            [""] + opponents,
            index=0,
            key="player_opponent_filter"
        )
    
    with col4:
        # Win/Loss filter
        result_options = st.multiselect(
            "Map Result",
            ["Won", "Lost"],
            default=["Won", "Lost"],
            key="player_result_filter"
        )
    
    # Add position filter on a new row with clear label
    st.markdown("**Position Filter:**")
    col1_pos, col2_pos, col3_pos, col4_pos = st.columns(4)
    with col1_pos:
        # Position filter
        positions = ['All']
        if 'position' in filtered_df.columns:
            positions += sorted(filtered_df['position'].unique().tolist())
        else:
            st.warning("⚠️ Position data not available")
        selected_position = st.selectbox(
            "Position (AR/SMG/Flex)",
            positions,
            index=0,
            key="player_position_filter",
            help="Filter players by their position: AR (Assault Rifle), SMG (Sub-Machine Gun), or Flex"
        )
    
    # Apply player stats filters
    player_filtered_df = filtered_df.copy()
    
    # Apply mode filter
    if selected_mode == "Maps 1-3":
        # For "Maps 1-3", only show maps 1-3 data
        player_filtered_df = player_filtered_df[player_filtered_df['map_number'].isin([1, 2, 3])]
    else:
        # For specific mode, filter by that game mode
        player_filtered_df = player_filtered_df[player_filtered_df['mode'] == selected_mode]
    
    # Apply map filter (only if not empty and specific mode is selected)
    if selected_map and selected_mode != "Maps 1-3":
        player_filtered_df = player_filtered_df[player_filtered_df['map_name'] == selected_map]
    
    # Apply position filter
    if selected_position != 'All' and 'position' in player_filtered_df.columns:
        player_filtered_df = player_filtered_df[player_filtered_df['position'] == selected_position]
    
    # Apply opponent filter (only if not empty)
    if selected_opponent:
        player_filtered_df = player_filtered_df[player_filtered_df['opponent_team_name'] == selected_opponent]
    
    # Map result to boolean
    result_bool_map = {}
    if "Won" in result_options:
        result_bool_map[True] = True
    if "Lost" in result_options:
        result_bool_map[False] = True
    
    if result_bool_map:
        player_filtered_df = player_filtered_df[player_filtered_df['won_map'].isin(result_bool_map.keys())]
    
    # Calculate player aggregate stats (average across all their maps in filtered data)
    player_stats = player_filtered_df.groupby('player_name').agg({
        'kills': 'mean',
        'deaths': 'mean',
        'assists': 'mean',
        'damage': 'mean',
        'rating': 'mean',
        'match_id': 'count',
        'team_name': 'first',
    }).reset_index()
    
    player_stats.columns = ['Player', 'Avg_Kills', 'Avg_Deaths', 'Avg_Assists', 
                            'Avg_Damage', 'Avg_Rating', 'Maps_Played', 'Team']
    
    # Calculate K/D ratio
    player_stats['K/D'] = (player_stats['Avg_Kills'] / player_stats['Avg_Deaths']).round(2)
    
    # Team filter
    teams_list = sorted(filtered_df['team_name'].unique())
    selected_team = st.selectbox(
        "Filter by Team (or select 'All Teams')",
        ["All Teams"] + teams_list,
        key="player_team_filter"
    )
    
    if selected_team != "All Teams":
        player_stats = player_stats[player_stats['Team'] == selected_team]
    
    # View selection
    view_type = st.radio(
        "Display view:",
        ["Table", "Gallery"],
        horizontal=True,
        key="player_view"
    )
    
    if view_type == "Gallery":
        # Display players as a gallery with images
        st.markdown("#### Player Gallery")
        
        # Sorting options for gallery
        sort_col = st.selectbox(
            "Sort by",
            ["K/D", "Avg_Kills", "Avg_Rating", "Avg_Damage", "Avg_Deaths", "Maps_Played"],
            key="player_sort_gallery"
        )
        
        player_stats = player_stats.sort_values(sort_col, ascending=(sort_col == "Avg_Deaths"))
        
        # Display players in grid (3 columns)
        cols = st.columns(3)
        for idx, (_, row) in enumerate(player_stats.iterrows()):
            with cols[idx % 3]:
                player_name = row['Player']
                image_url = st.session_state.player_images.get(player_name)
                
                # Display player image if available
                if image_url:
                    try:
                        st.image(image_url, width=150, use_column_width=False)
                    except Exception as e:
                        st.warning(f"Could not load image for {player_name}")
                else:
                    st.info(f"No image for {player_name}")
                
                # Display player info
                st.markdown(f"**{player_name}**")
                st.markdown(f"*{row['Team']}*")
                st.markdown(f"K/D: **{row['K/D']}** | Rating: **{row['Avg_Rating']:.2f}**")
                st.caption(f"{int(row['Maps_Played'])} maps")
    
    else:
        # Table view
        # Sorting options
        sort_col = st.selectbox(
            "Sort by",
            ["K/D", "Avg_Kills", "Avg_Rating", "Avg_Damage", "Avg_Deaths", "Maps_Played"],
            key="player_sort"
        )
        
        # Sort and display
        player_stats = player_stats.sort_values(sort_col, ascending=(sort_col == "Avg_Deaths"))
        
        # Format for display
        display_stats = player_stats[[
            'Player', 'Team', 'K/D', 'Avg_Kills', 'Avg_Deaths', 'Avg_Rating', 'Avg_Damage', 'Maps_Played'
        ]].copy()
        
        display_stats['Avg_Kills'] = display_stats['Avg_Kills'].round(2)
        display_stats['Avg_Deaths'] = display_stats['Avg_Deaths'].round(2)
        display_stats['Avg_Rating'] = display_stats['Avg_Rating'].round(2)
        display_stats['Avg_Damage'] = display_stats['Avg_Damage'].round(0).astype(int)
        display_stats['Maps_Played'] = display_stats['Maps_Played'].astype(int)
        
        st.dataframe(
            display_stats,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Player': st.column_config.TextColumn('Player', width='medium'),
                'Team': st.column_config.TextColumn('Team', width='medium'),
                'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
                'Avg_Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
                'Avg_Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
                'Avg_Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
                'Avg_Damage': st.column_config.NumberColumn('Avg Damage', format='%d'),
                'Maps_Played': st.column_config.NumberColumn('Maps', format='%d'),
            }
        )
    
    st.divider()
    
    # ========== VISUALIZATION SECTION ==========
    
    # Charts
    col1, col2 = st.columns(2)
    
    # Mode distribution
    with col1:
        st.markdown("### Mode Distribution")
        mode_dist = get_mode_distribution(player_filtered_df)
        fig_mode = px.pie(
            mode_dist,
            values='Count',
            names='Mode',
            hole=0.3,
        )
        fig_mode.update_layout(height=400)
        st.plotly_chart(fig_mode, use_container_width=True)
    
    # Maps by count
    with col2:
        st.markdown("### Most Played Maps")
        map_dist = get_map_distribution(player_filtered_df)
        fig_maps = px.bar(
            map_dist.head(10),
            x='Map',
            y='Count',
            color='Count',
            color_continuous_scale='Viridis',
        )
        fig_maps.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_maps, use_container_width=True)
    
    # Maps by mode
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Maps by Mode")
        mode_selected = st.selectbox("Select Mode", player_filtered_df['mode'].unique())
        map_mode_dist = get_map_distribution(player_filtered_df, mode=mode_selected)
        fig_map_mode = px.bar(
            map_mode_dist.head(10),
            x='Map',
            y='Count',
            color='Count',
            color_continuous_scale='Plasma',
        )
        fig_map_mode.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_map_mode, use_container_width=True)
    
    # Data table
    with col2:
        st.markdown("### Win/Loss Distribution")
        win_loss = player_filtered_df['won_map'].value_counts().reset_index()
        win_loss.columns = ['Result', 'Count']
        win_loss['Result'] = win_loss['Result'].map({True: 'Won', False: 'Lost'})
        fig_winloss = px.bar(
            win_loss,
            x='Result',
            y='Count',
            color='Result',
            color_discrete_map={'Won': '#00CC96', 'Lost': '#EF553B'},
        )
        fig_winloss.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_winloss, use_container_width=True)
    
    # Data table
    st.markdown("### Data Sample")
    st.dataframe(
        player_filtered_df[[
            'team_name', 'opponent_team_name', 'player_name',
            'mode', 'map_name', 'kills', 'deaths', 'assists', 'damage', 'won_map'
        ]].head(20),
        use_container_width=True,
    )


# ============================================================================
# TEAM DETAIL PAGE
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def calculate_map_scores_cached(df_hash, player_name, match_ids_tuple, map_numbers_tuple, data_version='v2'):
    """
    Cached calculation of map scores using actual game scores (HP points, S&D rounds, Overload caps).
    Falls back to kills-deaths if score data not available.
    TTL of 300 seconds (5 minutes).
    data_version parameter forces cache invalidation after data refresh.
    """
    full_df = st.session_state.df
    player_df = full_df[full_df['player_name'] == player_name]
    map_scores = {}
    
    match_ids = set(match_ids_tuple)
    map_numbers = set(map_numbers_tuple)
    
    for match_id in match_ids:
        for map_number in map_numbers:
            map_key = (match_id, map_number)
            # Get player's row for this specific map to get team_score and opponent_score
            player_map_data = player_df[(player_df['match_id'] == match_id) & 
                                       (player_df['map_number'] == map_number)]
            
            if not player_map_data.empty:
                # Try to use actual game scores first
                first_row = player_map_data.iloc[0]
                if pd.notna(first_row.get('team_score')) and pd.notna(first_row.get('opponent_score')):
                    team_score = int(first_row['team_score'])
                    opponent_score = int(first_row['opponent_score'])
                    map_scores[map_key] = f"{team_score}-{opponent_score}"
                else:
                    # Fallback: Get ALL players on this team for this map to calculate team total
                    team_name = first_row['team_name']
                    all_team_data = full_df[(full_df['match_id'] == match_id) & 
                                           (full_df['map_number'] == map_number) &
                                           (full_df['team_name'] == team_name)]
                    team_kills = all_team_data['kills'].sum()
                    team_deaths = all_team_data['deaths'].sum()
                    map_scores[map_key] = f"{int(team_kills)}-{int(team_deaths)}"
    
    return map_scores


def page_player_detail(player_name):
    """Display detailed player dashboard with granular match history."""
    
    # Back button
    if st.button("← Back to Player Overview"):
        if 'current_player' in st.session_state:
            del st.session_state.current_player
        st.rerun()
    
    filtered_df = render_sidebar_filters()
    player_df = filtered_df[filtered_df['player_name'] == player_name]
    
    if player_df.empty:
        st.warning(f"No data available for {player_name}")
        return
    
    # Get player info
    team_name = player_df['team_name'].iloc[0]
    from config import get_player_position
    position = get_player_position(player_name)
    
    # Load player image using cached function
    player_images = load_player_images_cached()
    player_image_url = player_images.get(player_name)
    
    # Create aesthetic player header
    if player_image_url:
        header_html = f'''
        <div class="player-detail-header">
            <div class="player-detail-image">
                <img src="{player_image_url}" alt="{player_name}">
            </div>
            <div class="player-detail-info">
                <div class="player-detail-name">🎮 {player_name}</div>
                <div class="player-detail-meta">
                    <div class="player-detail-stat">
                        <div class="player-detail-stat-label">Team</div>
                        <div class="player-detail-stat-value">{team_name}</div>
                    </div>
                    <div class="player-detail-stat">
                        <div class="player-detail-stat-label">Position</div>
                        <div class="player-detail-stat-value">{position}</div>
                    </div>
                    <div class="player-detail-stat">
                        <div class="player-detail-stat-label">Maps Played</div>
                        <div class="player-detail-stat-value">{len(player_df)}</div>
                    </div>
                </div>
            </div>
        </div>
        '''
    else:
        # Fallback header without image
        header_html = f'''
        <div class="player-detail-header">
            <div class="player-detail-info">
                <div class="player-detail-name">🎮 {player_name}</div>
                <div class="player-detail-meta">
                    <div class="player-detail-stat">
                        <div class="player-detail-stat-label">Team</div>
                        <div class="player-detail-stat-value">{team_name}</div>
                    </div>
                    <div class="player-detail-stat">
                        <div class="player-detail-stat-label">Position</div>
                        <div class="player-detail-stat-value">{position}</div>
                    </div>
                    <div class="player-detail-stat">
                        <div class="player-detail-stat-label">Maps Played</div>
                        <div class="player-detail-stat-value">{len(player_df)}</div>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    st.divider()
    
    # Recent Match Performance with Filters
    st.markdown("### Recent Match Performance")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mode_options = ['All Modes'] + sorted(player_df['mode'].unique().tolist())
        selected_mode = st.selectbox("Filter by Mode", mode_options, key="player_mode_filter")
    
    with col2:
        map_options = ['All Maps'] + sorted(player_df['map_name'].unique().tolist())
        selected_map = st.selectbox("Filter by Map", map_options, key="player_map_filter")
    
    with col3:
        result_options = ['All Results', 'Wins Only', 'Losses Only']
        selected_result = st.selectbox("Filter by Result", result_options, key="player_result_filter")
    
    # Apply filters
    player_df_filtered = player_df.copy()
    
    if selected_mode != 'All Modes':
        player_df_filtered = player_df_filtered[player_df_filtered['mode'] == selected_mode]
    
    if selected_map != 'All Maps':
        player_df_filtered = player_df_filtered[player_df_filtered['map_name'] == selected_map]
    
    if selected_result == 'Wins Only':
        player_df_filtered = player_df_filtered[player_df_filtered['won_map'] == True]
    elif selected_result == 'Losses Only':
        player_df_filtered = player_df_filtered[player_df_filtered['won_map'] == False]
    
    if player_df_filtered.empty:
        st.info("No matches found with the selected filters.")
    else:
        # Sort by date (most recent first)
        player_df_sorted = player_df_filtered.sort_values(['date', 'match_id', 'map_number'], ascending=[False, False, True])
        
        # Calculate map scores using cached function
        df_hash = hash(str(st.session_state.df.shape) + str(st.session_state.df.columns.tolist()))
        match_ids_tuple = tuple(player_df_sorted['match_id'].unique())
        map_numbers_tuple = tuple(player_df_sorted['map_number'].unique())
        map_scores = calculate_map_scores_cached(df_hash, player_name, match_ids_tuple, map_numbers_tuple)
        
        # Team-based color mapping (each opponent team gets a consistent color)
        TEAM_COLORS = {
            'Boston Breach': '#D6EAF8',          # Light blue
            'Carolina Royal Ravens': '#FCF3CF',  # Light yellow
            'Cloud9 New York': '#D5F4E6',        # Light green
            'FaZe Vegas': '#FADBD8',             # Light red/pink
            'G2 Minnesota': '#E8DAEF',           # Light purple
            'Los Angeles Thieves': '#FAE5D3',    # Light orange
            'Miami Heretics': '#D5DBDB',         # Light gray
            'OpTic Texas': '#D4EFDF',            # Mint green
            'Paris Gentle Mates': '#E3F2FD',     # Sky blue
            'Riyadh Falcons': '#FFF9C4',         # Pale yellow
            'Toronto KOI': '#C8E6C9',            # Pale green
            'Vancouver Surge': '#F8BBD0',        # Pink
        }
        
        # Create detailed match table with opponent-based color coding
        match_data = []
        row_colors = []  # Store color for each row based on opponent
        
        for _, row in player_df_sorted.iterrows():
            map_key = (row['match_id'], row['map_number'])
            
            # Get color based on opponent team
            opponent_color = TEAM_COLORS.get(row['opponent_team_name'], '#FFFFFF')
            row_colors.append(opponent_color)
            
            match_data.append({
                'Match ID': row['match_id'],
                'Map Score': map_scores.get(map_key, 'N/A'),
                'Date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'N/A',
                'Opponent': row['opponent_team_name'],
                'Map': row['map_name'],
                'Mode': row['mode'],
                'Map #': int(row['map_number']) if pd.notna(row['map_number']) else 'N/A',
                'Kills': int(row['kills']),
                'Deaths': int(row['deaths']),
                'Assists': int(row['assists']),
                'K/D': round(row['kills'] / row['deaths'], 2) if row['deaths'] > 0 else row['kills'],
                'Damage': int(row['damage']),
                'Result': '✅ Win' if row['won_map'] else '❌ Loss'
            })
        
        match_df = pd.DataFrame(match_data)
        
        # Create a mapping from index to color for styling (based on opponent)
        index_to_color = {idx: color for idx, color in enumerate(row_colors)}
        
        # Display with styling using Streamlit's dataframe
        def highlight_by_opponent(row):
            """Color each row based on the opponent team"""
            color = index_to_color.get(row.name, '#FFFFFF')
            return [f'background-color: {color}; color: #000000' for _ in row]
        
        # Drop Match ID column and apply styling
        display_df = match_df.drop(columns=['Match ID'])
        styled_df = display_df.style.apply(highlight_by_opponent, axis=1)
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=600
        )
    
    st.divider()
    
    # Performance by Mode
    st.markdown("### Performance by Game Mode")
    
    mode_tabs = st.tabs(["📊 Overview", "🎯 Hardpoint", "💣 Search & Destroy", "⚡ Overload"])
    
    with mode_tabs[0]:
        # Mode comparison
        mode_stats = []
        for mode in ['Hardpoint', 'Search & Destroy', 'Overload']:
            mode_df = player_df[player_df['mode'] == mode]
            if not mode_df.empty:
                mode_stats.append({
                    'Mode': mode,
                    'Maps': len(mode_df),
                    'Avg Kills': mode_df['kills'].mean(),
                    'Avg Deaths': mode_df['deaths'].mean(),
                    'K/D': mode_df['kills'].mean() / mode_df['deaths'].mean() if mode_df['deaths'].mean() > 0 else 0,
                    'Avg Damage': mode_df['damage'].mean(),
                    'Win %': (mode_df['won_map'].sum() / len(mode_df) * 100)
                })
        
        if mode_stats:
            mode_stats_df = pd.DataFrame(mode_stats)
            st.dataframe(
                mode_stats_df.style.format({
                    'Avg Kills': '{:.1f}',
                    'Avg Deaths': '{:.1f}',
                    'K/D': '{:.2f}',
                    'Avg Damage': '{:.0f}',
                    'Win %': '{:.1f}%'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(mode_stats_df, x='Mode', y='Avg Kills', color='Avg Kills',
                           color_continuous_scale='Blues', title='Avg Kills by Mode')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(mode_stats_df, x='Mode', y='K/D', color='K/D',
                           color_continuous_scale='Greens', title='K/D by Mode')
                st.plotly_chart(fig, use_container_width=True)
    
    # Individual mode tabs
    for idx, mode in enumerate(['Hardpoint', 'Search & Destroy', 'Overload'], 1):
        with mode_tabs[idx]:
            mode_df = player_df[player_df['mode'] == mode]
            if mode_df.empty:
                st.info(f"No {mode} data available.")
            else:
                # Performance by map
                st.markdown(f"#### {mode} Performance by Map")
                map_stats = mode_df.groupby('map_name').agg({
                    'kills': 'mean',
                    'deaths': 'mean',
                    'damage': 'mean',
                    'won_map': lambda x: (x.sum() / len(x) * 100)
                }).reset_index()
                
                map_stats.columns = ['Map', 'Avg Kills', 'Avg Deaths', 'Avg Damage', 'Win %']
                map_stats['K/D'] = map_stats['Avg Kills'] / map_stats['Avg Deaths']
                map_stats['Maps'] = mode_df.groupby('map_name').size().values
                
                st.dataframe(
                    map_stats[['Map', 'Maps', 'Avg Kills', 'Avg Deaths', 'K/D', 'Avg Damage', 'Win %']].style.format({
                        'Avg Kills': '{:.1f}',
                        'Avg Deaths': '{:.1f}',
                        'K/D': '{:.2f}',
                        'Avg Damage': '{:.0f}',
                        'Win %': '{:.1f}%'
                    }),
                    use_container_width=True,
                    hide_index=True
                )


def page_team_detail(team_name):
    """Display detailed team dashboard with mode-specific analysis."""
    st.markdown(f'<div class="title-section"><h2>🏆 {team_name}</h2></div>', 
                unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Player Overview"):
        if 'current_team' in st.session_state:
            del st.session_state.current_team
        st.rerun()
    
    filtered_df = render_sidebar_filters()
    team_df = filtered_df[filtered_df['team_name'] == team_name]
    
    if team_df.empty:
        st.warning(f"No data available for {team_name}")
        return
    
    # Team overview metrics
    st.markdown("### Team Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_maps = len(team_df.groupby(['match_id', 'map_number']).size())
        st.metric("Total Maps", total_maps)
    
    with col2:
        total_series = team_df['match_id'].nunique()
        st.metric("Series Played", total_series)
    
    with col3:
        # Calculate win rate correctly by counting unique maps won
        unique_maps = team_df.groupby(['match_id', 'map_number'])['won_map'].first()
        maps_won = unique_maps.sum()
        total_unique_maps = len(unique_maps)
        win_rate = (maps_won / total_unique_maps * 100) if total_unique_maps > 0 else 0
        st.metric("Map Win Rate", f"{win_rate:.1f}%")
    
    st.divider()
    
    # Mode tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Hardpoint", "💣 Search & Destroy", "⚡ Overload"])
    
    # ===== HARDPOINT TAB =====
    with tab1:
        st.markdown("### Hardpoint Analysis")
        hp_df = team_df[team_df['mode'] == 'Hardpoint']
        
        if hp_df.empty:
            st.info("No Hardpoint data available.")
        else:
            # Win/Loss filter
            win_loss_filter = st.radio(
                "Filter by Result",
                ["All Maps", "Wins Only", "Losses Only"],
                horizontal=True,
                key="hp_filter"
            )
            
            # Apply filter
            if win_loss_filter == "Wins Only":
                hp_filtered = hp_df[hp_df['won_map'] == True]
            elif win_loss_filter == "Losses Only":
                hp_filtered = hp_df[hp_df['won_map'] == False]
            else:
                hp_filtered = hp_df
            
            # Get unique maps
            maps = sorted(hp_filtered['map_name'].unique())
            
            # Display stats by map
            for map_name in maps:
                map_df = hp_filtered[hp_filtered['map_name'] == map_name]
                
                # Calculate map record
                map_total = len(map_df.groupby(['match_id', 'map_number']).size())
                map_won = len(map_df[map_df['won_map'] == True].groupby(['match_id', 'map_number']).size())
                map_lost = map_total - map_won
                
                with st.expander(f"📍 {map_name} ({map_won}-{map_lost})"):
                    # Player stats on this map
                    player_stats = []
                    players = sorted(map_df['player_name'].unique())
                    
                    # Display player buttons for navigation
                    st.markdown("**Click player name to view detailed stats:**")
                    player_cols = st.columns(min(len(players), 4))
                    for idx, player in enumerate(players):
                        with player_cols[idx % 4]:
                            if st.button(f"👤 {player}", key=f"hp_{map_name}_{player}", use_container_width=True):
                                st.session_state.current_player = player
                                if 'current_team' in st.session_state:
                                    del st.session_state.current_team
                                st.rerun()
                    
                    st.markdown("---")
                    
                    for player in players:
                        player_map_df = map_df[map_df['player_name'] == player]
                        stats = {
                            'Player': player,
                            'Maps': len(player_map_df),
                            'Avg Kills': player_map_df['kills'].mean(),
                            'Avg Deaths': player_map_df['deaths'].mean(),
                            'K/D': player_map_df['kills'].mean() / player_map_df['deaths'].mean() if player_map_df['deaths'].mean() > 0 else 0,
                            'Avg Damage': player_map_df['damage'].mean(),
                            'Win %': (player_map_df['won_map'].sum() / len(player_map_df) * 100) if len(player_map_df) > 0 else 0
                        }
                        player_stats.append(stats)
                    
                    stats_df = pd.DataFrame(player_stats)
                    st.dataframe(
                        stats_df.style.format({
                            'Avg Kills': '{:.1f}',
                            'Avg Deaths': '{:.1f}',
                            'K/D': '{:.2f}',
                            'Avg Damage': '{:.0f}',
                            'Win %': '{:.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
    
    # ===== SEARCH & DESTROY TAB =====
    with tab2:
        st.markdown("### Search & Destroy Analysis")
        snd_df = team_df[team_df['mode'] == 'Search & Destroy']
        
        if snd_df.empty:
            st.info("No Search & Destroy data available.")
        else:
            # Win/Loss filter
            win_loss_filter = st.radio(
                "Filter by Result",
                ["All Maps", "Wins Only", "Losses Only"],
                horizontal=True,
                key="snd_filter"
            )
            
            # Apply filter
            if win_loss_filter == "Wins Only":
                snd_filtered = snd_df[snd_df['won_map'] == True]
            elif win_loss_filter == "Losses Only":
                snd_filtered = snd_df[snd_df['won_map'] == False]
            else:
                snd_filtered = snd_df
            
            # Get unique maps
            maps = sorted(snd_filtered['map_name'].unique())
            
            # Display stats by map
            for map_name in maps:
                map_df = snd_filtered[snd_filtered['map_name'] == map_name]
                
                # Calculate map record
                map_total = len(map_df.groupby(['match_id', 'map_number']).size())
                map_won = len(map_df[map_df['won_map'] == True].groupby(['match_id', 'map_number']).size())
                map_lost = map_total - map_won
                
                with st.expander(f"📍 {map_name} ({map_won}-{map_lost})"):
                    # Player stats on this map
                    player_stats = []
                    players = sorted(map_df['player_name'].unique())
                    
                    # Display player buttons for navigation
                    st.markdown("**Click player name to view detailed stats:**")
                    player_cols = st.columns(min(len(players), 4))
                    for idx, player in enumerate(players):
                        with player_cols[idx % 4]:
                            if st.button(f"👤 {player}", key=f"snd_{map_name}_{player}", use_container_width=True):
                                st.session_state.current_player = player
                                if 'current_team' in st.session_state:
                                    del st.session_state.current_team
                                st.rerun()
                    
                    st.markdown("---")
                    
                    for player in players:
                        player_map_df = map_df[map_df['player_name'] == player]
                        stats = {
                            'Player': player,
                            'Maps': len(player_map_df),
                            'Avg Kills': player_map_df['kills'].mean(),
                            'Avg Deaths': player_map_df['deaths'].mean(),
                            'K/D': player_map_df['kills'].mean() / player_map_df['deaths'].mean() if player_map_df['deaths'].mean() > 0 else 0,
                            'Avg Damage': player_map_df['damage'].mean(),
                            'Win %': (player_map_df['won_map'].sum() / len(player_map_df) * 100) if len(player_map_df) > 0 else 0
                        }
                        player_stats.append(stats)
                    
                    stats_df = pd.DataFrame(player_stats)
                    st.dataframe(
                        stats_df.style.format({
                            'Avg Kills': '{:.1f}',
                            'Avg Deaths': '{:.1f}',
                            'K/D': '{:.2f}',
                            'Avg Damage': '{:.0f}',
                            'Win %': '{:.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
    
    # ===== OVERLOAD TAB =====
    with tab3:
        st.markdown("### Overload Analysis")
        overload_df = team_df[team_df['mode'] == 'Overload']
        
        if overload_df.empty:
            st.info("No Overload data available.")
        else:
            # Win/Loss filter
            win_loss_filter = st.radio(
                "Filter by Result",
                ["All Maps", "Wins Only", "Losses Only"],
                horizontal=True,
                key="overload_filter"
            )
            
            # Apply filter
            if win_loss_filter == "Wins Only":
                overload_filtered = overload_df[overload_df['won_map'] == True]
            elif win_loss_filter == "Losses Only":
                overload_filtered = overload_df[overload_df['won_map'] == False]
            else:
                overload_filtered = overload_df
            
            # Get unique maps
            maps = sorted(overload_filtered['map_name'].unique())
            
            # Display stats by map
            for map_name in maps:
                map_df = overload_filtered[overload_filtered['map_name'] == map_name]
                
                # Calculate map record
                map_total = len(map_df.groupby(['match_id', 'map_number']).size())
                map_won = len(map_df[map_df['won_map'] == True].groupby(['match_id', 'map_number']).size())
                map_lost = map_total - map_won
                
                with st.expander(f"📍 {map_name} ({map_won}-{map_lost})"):
                    # Player stats on this map
                    player_stats = []
                    players = sorted(map_df['player_name'].unique())
                    
                    # Display player buttons for navigation
                    st.markdown("**Click player name to view detailed stats:**")
                    player_cols = st.columns(min(len(players), 4))
                    for idx, player in enumerate(players):
                        with player_cols[idx % 4]:
                            if st.button(f"👤 {player}", key=f"overload_{map_name}_{player}", use_container_width=True):
                                st.session_state.current_player = player
                                if 'current_team' in st.session_state:
                                    del st.session_state.current_team
                                st.rerun()
                    
                    st.markdown("---")
                    
                    for player in players:
                        player_map_df = map_df[map_df['player_name'] == player]
                        stats = {
                            'Player': player,
                            'Maps': len(player_map_df),
                            'Avg Kills': player_map_df['kills'].mean(),
                            'Avg Deaths': player_map_df['deaths'].mean(),
                            'K/D': player_map_df['kills'].mean() / player_map_df['deaths'].mean() if player_map_df['deaths'].mean() > 0 else 0,
                            'Avg Damage': player_map_df['damage'].mean(),
                            'Win %': (player_map_df['won_map'].sum() / len(player_map_df) * 100) if len(player_map_df) > 0 else 0
                        }
                        player_stats.append(stats)
                    
                    stats_df = pd.DataFrame(player_stats)
                    st.dataframe(
                        stats_df.style.format({
                            'Avg Kills': '{:.1f}',
                            'Avg Deaths': '{:.1f}',
                            'K/D': '{:.2f}',
                            'Avg Damage': '{:.0f}',
                            'Win %': '{:.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )


# ============================================================================
# PAGE 2: PLAYER OVERVIEW
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def calculate_team_records_cached(df_hash, team_name):
    """
    Cached calculation of team records to avoid recomputing on each render.
    TTL of 300 seconds (5 minutes).
    """
    team_df = st.session_state.df[st.session_state.df['team_name'] == team_name]
    
    # Calculate series record
    matches = team_df.groupby('match_id')
    series_wins = sum(match['won_map'].iloc[0] for _, match in matches if not match.empty)
    series_losses = len(matches) - series_wins
    
    # Calculate mode-specific map records
    records = {'series_wins': series_wins, 'series_losses': series_losses}
    
    for mode_name, mode_label in [('Hardpoint', 'hp'), ('Search & Destroy', 'snd'), ('Overload', 'overload')]:
        mode_df = team_df[team_df['mode'] == mode_name]
        total = len(mode_df.groupby(['match_id', 'map_number']).size()) if not mode_df.empty else 0
        won = len(mode_df[mode_df['won_map'] == True].groupby(['match_id', 'map_number']).size()) if not mode_df.empty else 0
        records[f'{mode_label}_total'] = total
        records[f'{mode_label}_won'] = won
        records[f'{mode_label}_lost'] = total - won
    
    return records


@st.cache_data(ttl=300, show_spinner=False)
def calculate_player_stats_cached(df_hash, player_name, team_name, filter_type):
    """
    Cached calculation of player statistics to avoid recomputing.
    filter_type: 'all', 'wins', or 'losses'
    TTL of 300 seconds (5 minutes).
    """
    df = st.session_state.df
    player_data = df[(df['player_name'] == player_name) & (df['team_name'] == team_name)]
    
    # Apply filter
    if filter_type == 'wins':
        player_data = player_data[player_data['won_map'] == True]
    elif filter_type == 'losses':
        player_data = player_data[player_data['won_map'] == False]
    
    if player_data.empty:
        return None
    
    # Calculate stats by mode
    stats = {}
    for mode in ['Hardpoint', 'Search & Destroy', 'Overload']:
        mode_data = player_data[player_data['mode'] == mode]
        if not mode_data.empty:
            stats[mode] = {
                'kills': round(mode_data['kills'].mean(), 1),
                'deaths': round(mode_data['deaths'].mean(), 1),
                'kd': round(mode_data['kills'].mean() / mode_data['deaths'].mean(), 2) if mode_data['deaths'].mean() > 0 else 0,
                'damage': round(mode_data['damage'].mean(), 0)
            }
    
    return stats


def page_player_overview():
    """Display team-organized player statistics across all game modes."""
    st.markdown('<div class="title-section"><h2>👤 Player Overview</h2></div>', 
                unsafe_allow_html=True)
    
    # Check if we should show player detail page
    if 'current_player' in st.session_state and st.session_state.current_player:
        page_player_detail(st.session_state.current_player)
        return
    
    # Check if we should show team detail page
    if 'current_team' in st.session_state and st.session_state.current_team:
        page_team_detail(st.session_state.current_team)
        return
    
    filtered_df = render_sidebar_filters()
    
    # Load player images using cached function
    player_images = load_player_images_cached()
    
    # Use all available data (maps 1-5) for more accurate mode averages
    maps_df = filtered_df.copy()
    
    if maps_df.empty:
        st.info("No data available.")
        return
    
    # Get unique teams
    teams = sorted(maps_df['team_name'].unique())
    
    # Create team player mapping from config
    team_player_map = {
        'Boston Breach': ['Cammy', 'Snoopy', 'Purj', 'Nastie'],
        'Carolina Royal Ravens': ['SlasheR', 'Nero', 'Lurqxx', 'Craze'],
        'Cloud9 New York': ['Mack', 'Afro', 'Beans', 'Vivid'],
        'FaZe Vegas': ['Drazah', 'Abuzah', '04', 'Simp'],
        'G2 Minnesota': ['Skyz', 'Estreal', 'Kremp', 'Mamba'],
        'Los Angeles Thieves': ['aBeZy', 'HyDra', 'Scrap', 'Kenny'],
        'Miami Heretics': ['MettalZ', 'Traixx', 'SupeR', 'RenKoR'],
        'OpTic Texas': ['Shotzzy', 'Dashy', 'Huke', 'Mercules'],
        'Paris Gentle Mates': ['Envoy', 'Ghosty', 'Neptune', 'Sib'],
        'Riyadh Falcons': ['Cellium', 'Pred', 'Exnid', 'KiSMET'],
        'Toronto KOI': ['ReeaL', 'CleanX', 'JoeDeceives', 'Insight'],
        'Vancouver Surge': ['Abe', 'Gwinn', 'Lunarz', 'Lqgend'],
    }
    
    # Display each team
    for team in teams:
        team_df = maps_df[maps_df['team_name'] == team]
        
        # Calculate series/match record (wins/losses of BO5 series)
        # Group by match_id and count maps won per series
        match_results = team_df.groupby('match_id').agg({
            'won_map': lambda x: x.sum(),  # Count maps won in this series
            'map_number': 'count'  # Total maps played
        }).reset_index()
        
        # A team wins the series if they won more than half the maps
        match_results['series_won'] = match_results['won_map'] > (match_results['map_number'] / 2)
        series_wins = match_results['series_won'].sum()
        total_series = len(match_results)
        series_losses = total_series - series_wins
        
        # Calculate mode-specific map records (individual map wins/losses)
        # Hardpoint
        hp_df = team_df[team_df['mode'] == 'Hardpoint']
        hp_total = len(hp_df.groupby(['match_id', 'map_number']).size()) if not hp_df.empty else 0
        hp_won = len(hp_df[hp_df['won_map'] == True].groupby(['match_id', 'map_number']).size()) if not hp_df.empty else 0
        hp_lost = hp_total - hp_won
        
        # Search & Destroy
        snd_df = team_df[team_df['mode'] == 'Search & Destroy']
        snd_total = len(snd_df.groupby(['match_id', 'map_number']).size()) if not snd_df.empty else 0
        snd_won = len(snd_df[snd_df['won_map'] == True].groupby(['match_id', 'map_number']).size()) if not snd_df.empty else 0
        snd_lost = snd_total - snd_won
        
        # Overload
        overload_df = team_df[team_df['mode'] == 'Overload']
        overload_total = len(overload_df.groupby(['match_id', 'map_number']).size()) if not overload_df.empty else 0
        overload_won = len(overload_df[overload_df['won_map'] == True].groupby(['match_id', 'map_number']).size()) if not overload_df.empty else 0
        overload_lost = overload_total - overload_won
        
        # Team header with records and filter toggle
        col_header, col_button = st.columns([4, 1])
        
        with col_header:
            st.markdown(f"### {team}")
            st.caption(f"**Match Record: {series_wins}-{series_losses}**")
            st.caption(f"Hardpoint: **{hp_won}-{hp_lost}** | Search & Destroy: **{snd_won}-{snd_lost}** | Overload: **{overload_won}-{overload_lost}**")
        
        with col_button:
            if st.button("View Details →", key=f"view_{team}", use_container_width=True):
                st.session_state.current_team = team
                st.rerun()
        
        # Win/Loss filter - radio button for clear selection
        filter_option = st.radio(
            "Show stats for:",
            ["All Maps", "Wins Only", "Losses Only"],
            horizontal=True,
            key=f"{team}_filter"
        )
        
        # Filter data based on selection
        if filter_option == "Wins Only":
            team_df_filtered = team_df[team_df['won_map'] == True]
            filter_label = " (Wins Only)"
        elif filter_option == "Losses Only":
            team_df_filtered = team_df[team_df['won_map'] == False]
            filter_label = " (Losses Only)"
        else:  # All Maps
            team_df_filtered = team_df
            filter_label = ""
        
        # Get players for this team (from roster or from data)
        if team in team_player_map:
            players = team_player_map[team]
        else:
            players = sorted(team_df_filtered['player_name'].unique())
        
        # Create columns for each player (max 4 per row)
        cols = st.columns(4)
        
        for idx, player in enumerate(players):
            # Use filtered data based on win/loss toggle
            player_data = team_df_filtered[team_df_filtered['player_name'] == player]
            
            if player_data.empty:
                continue
            
            with cols[idx % 4]:
                # Player image - centered
                if player in player_images:
                    st.markdown(
                        f'<div class="player-image-container"><img src="{player_images[player]}" width="150"></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div style='text-align: center;'><strong>{player}</strong></div>", unsafe_allow_html=True)
                
                # Get player position from config
                from config import get_player_position
                player_position = get_player_position(player)
                
                # Calculate stats using ALL available data for each mode
                # Hardpoint (Maps 1 & 4)
                hp_data = player_data[player_data['mode'] == 'Hardpoint']
                avg_kills_hp = hp_data['kills'].mean() if not hp_data.empty else 0
                
                # Search & Destroy (Maps 2 & 5)
                snd_data = player_data[player_data['mode'] == 'Search & Destroy']
                avg_kills_snd = snd_data['kills'].mean() if not snd_data.empty else 0
                
                # Overload (Map 3)
                overload_data = player_data[player_data['mode'] == 'Overload']
                avg_kills_overload = overload_data['kills'].mean() if not overload_data.empty else 0
                
                # Sum of mode averages (using all available data)
                avg_kills_total = avg_kills_hp + avg_kills_snd + avg_kills_overload
                
                # Display player name as clickable button
                if st.button(f"📊 {player}", key=f"player_overview_{team}_{player}", use_container_width=True):
                    st.session_state.current_player = player
                    st.rerun()
                
                st.caption(f"Position: {player_position}")
                st.metric("Avg Map 1-3 Kills", f"{avg_kills_total:.1f}")
                st.caption(f"Hardpoint (Maps 1,4): **{avg_kills_hp:.1f}**")
                st.caption(f"Search & Destroy (Maps 2,5): **{avg_kills_snd:.1f}**")
                st.caption(f"Overload (Map 3): **{avg_kills_overload:.1f}**")
        
        st.divider()


# ============================================================================
# PAGE 3: PER-MAP/MODE BREAKDOWN
# ============================================================================

def page_map_mode_breakdown():
    """Display aggregated map and mode statistics by position."""
    st.markdown('<div class="title-section"><h2>🗺️ Per-Map / Per-Mode Breakdown</h2></div>', 
                unsafe_allow_html=True)
    
    # Data Filters Section
    st.markdown("### 🎮 Data Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        seasons = sorted(st.session_state.df['season'].unique())
        selected_seasons = st.multiselect(
            "Seasons",
            seasons,
            default=seasons,
            key="breakdown_season_filter",
        )
    
    with filter_col2:
        events = sorted(st.session_state.df['event_name'].unique())
        selected_events = st.multiselect(
            "Events",
            events,
            default=events,
            key="breakdown_event_filter",
        )
    
    with filter_col3:
        lan_options = st.multiselect(
            "LAN / Online",
            ["LAN", "Online"],
            default=["LAN", "Online"],
            key="breakdown_lan_filter",
        )
    
    # Apply data filters
    filtered_df = get_filtered_data(selected_seasons, selected_events, lan_options)
    
    # Check if position data is available
    if 'position' not in filtered_df.columns:
        st.warning("⚠️ Position data not available in the dataset.")
        return
    
    st.divider()
    
    # Analysis Filters Section
    st.markdown("### 📊 Analysis Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Position filter - multiselect with default all positions
        available_positions = sorted(filtered_df['position'].unique().tolist())
        selected_positions = st.multiselect(
            "Position",
            available_positions,
            default=available_positions,  # Default to all positions
            key="map_mode_positions",
            help="Select one or more positions to compare (AR, SMG, Flex)"
        )
    
    with col2:
        # Mode filter - multiselect with default Hardpoint
        available_modes = sorted(filtered_df['mode'].unique().tolist())
        selected_modes = st.multiselect(
            "Game Mode",
            available_modes,
            default=['Hardpoint'] if 'Hardpoint' in available_modes else available_modes[:1],
            key="map_mode_modes",
            help="Select one or more game modes to analyze"
        )
    
    with col3:
        # Win/Loss filter - single select with default All
        result_filter = st.selectbox(
            "Result",
            ["All", "Win", "Loss"],
            index=0,
            key="map_mode_result",
            help="Filter by match result: Win (only winning teams), Loss (only losing teams), or All"
        )
    
    if not selected_positions:
        st.warning("Please select at least one position.")
        return
    
    if not selected_modes:
        st.warning("Please select at least one game mode.")
        return
    
    # Filter data by selected positions and modes
    analysis_df = filtered_df[
        (filtered_df['position'].isin(selected_positions)) &
        (filtered_df['mode'].isin(selected_modes))
    ]
    
    # Apply Win/Loss filter
    if result_filter == "Win":
        analysis_df = analysis_df[analysis_df['won_map'] == True]
    elif result_filter == "Loss":
        analysis_df = analysis_df[analysis_df['won_map'] == False]
    # If "All", no additional filtering needed
    
    if analysis_df.empty:
        st.info("No data available for selected filters.")
        return
    
    # Display summary metrics
    st.markdown("### 📊 Overall Averages")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Maps", len(analysis_df))
    with col2:
        st.metric("Avg Kills", f"{analysis_df['kills'].mean():.2f}")
    with col3:
        st.metric("Avg Deaths", f"{analysis_df['deaths'].mean():.2f}")
    with col4:
        avg_kd = analysis_df['kills'].mean() / analysis_df['deaths'].mean() if analysis_df['deaths'].mean() > 0 else 0
        st.metric("Avg K/D", f"{avg_kd:.2f}")
    with col5:
        st.metric("Avg Damage", f"{analysis_df['damage'].mean():.0f}")
    
    # Average kills by map (aggregated across selected positions)
    st.markdown("### 🗺️ Average Kills by Map")
    
    # Group by map only - combining all selected positions
    map_stats = analysis_df.groupby('map_name').agg({
        'kills': 'mean',
        'deaths': 'mean',
        'damage': 'mean',
        'rating': 'mean',
        'match_id': 'nunique',
        'won_map': lambda x: (x == True).sum() / len(x) * 100 if len(x) > 0 else 0
    }).reset_index()
    
    map_stats.columns = ['Map', 'Avg Kills', 'Avg Deaths', 'Avg Damage', 'Avg Rating', 'Maps Played', 'Win %']
    map_stats['K/D'] = map_stats['Avg Kills'] / map_stats['Avg Deaths'].replace(0, 1)
    
    # Display selected positions info
    positions_text = ", ".join(selected_positions)
    result_text = f" ({result_filter}s only)" if result_filter != "All" else " (All matches)"
    st.caption(f"Showing combined averages for: **{positions_text}**{result_text}")
    
    # Display as table
    st.dataframe(
        map_stats.round(2),
        use_container_width=True,
        hide_index=True,
        column_config={
            'Map': st.column_config.TextColumn('Map', width='medium'),
            'Avg Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
            'Avg Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
            'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
            'Avg Damage': st.column_config.NumberColumn('Avg Damage', format='%.0f'),
            'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
            'Win %': st.column_config.NumberColumn('Win %', format='%.1f%%'),
            'Maps Played': st.column_config.NumberColumn('Maps Played', format='%d'),
        }
    )
    
    # Visualizations
    st.markdown("### 📈 Visual Breakdown")
    
    # Bar chart: Average Kills by Map
    fig_kills = px.bar(
        map_stats,
        x='Map',
        y='Avg Kills',
        title=f'Average Kills by Map ({positions_text})',
        labels={'Avg Kills': 'Average Kills', 'Map': 'Map'},
        color='Avg Kills',
        color_continuous_scale='Blues',
        hover_data=['K/D', 'Avg Rating', 'Maps Played']
    )
    fig_kills.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig_kills, use_container_width=True)
    
    # Additional charts side by side
    col1, col2 = st.columns(2)
    
    with col1:
        # K/D by Map
        fig_kd = px.bar(
            map_stats,
            x='Map',
            y='K/D',
            title='K/D Ratio by Map',
            labels={'Map': 'Map', 'K/D': 'K/D Ratio'},
            color='K/D',
            color_continuous_scale='RdYlGn'
        )
        fig_kd.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_kd, use_container_width=True)
    
    with col2:
        # Damage by Map
        fig_damage = px.bar(
            map_stats,
            x='Map',
            y='Avg Damage',
            title='Average Damage by Map',
            labels={'Map': 'Map', 'Avg Damage': 'Average Damage'},
            color='Avg Damage',
            color_continuous_scale='Reds'
        )
        fig_damage.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_damage, use_container_width=True)


# ============================================================================
# PAGE 5: MATCHES - Detailed Match Breakdown
# ============================================================================

def page_matches():
    """Display all matches in a table, with drill-down to detailed view."""
    st.markdown('<div class="title-section"><h2>🏆 Matches</h2></div>', 
                unsafe_allow_html=True)
    
    filtered_df = render_sidebar_filters()
    
    # Get unique matches with team info
    matches_data = []
    for match_id in filtered_df['match_id'].unique():
        match_df = filtered_df[filtered_df['match_id'] == match_id]
        
        # Get the two teams
        teams = match_df['team_name'].unique()
        if len(teams) < 2:
            continue
            
        team1 = teams[0]
        team2 = teams[1]
        
        # Calculate wins per team
        team1_wins = len(match_df[(match_df['team_name'] == team1) & (match_df['won_map'] == True)]['map_number'].unique())
        team2_wins = len(match_df[(match_df['team_name'] == team2) & (match_df['won_map'] == True)]['map_number'].unique())
        
        matches_data.append({
            'match_id': match_id,
            'date': match_df['date'].iloc[0],
            'event_name': match_df['event_name'].iloc[0],
            'series_type': match_df['series_type'].iloc[0],
            'is_lan': match_df['is_lan'].iloc[0],
            'team1': team1,
            'team2': team2,
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
        })
    
    if len(matches_data) == 0:
        st.warning("No matches available for selected filters.")
        return
    
    matches_list = pd.DataFrame(matches_data)
    # Sort by date - most recent first
    matches_list = matches_list.sort_values('date', ascending=False).reset_index(drop=True)
    
    # Initialize session state for selected match
    if 'selected_match_id' not in st.session_state:
        st.session_state.selected_match_id = None
    
    # SHOW DETAIL VIEW if a match is selected
    if st.session_state.selected_match_id:
        # Add back button
        if st.button("← Back to Matches List"):
            st.session_state.selected_match_id = None
            st.rerun()
        
        st.markdown("---")
        
        selected_match_id = st.session_state.selected_match_id
        
        # Get all data for this match
        match_data = filtered_df[filtered_df['match_id'] == selected_match_id].copy()
        
        if len(match_data) == 0:
            st.error("No data available for this match.")
            return
        
        # Extract match metadata
        match_date = match_data['date'].iloc[0]
        event_name = match_data['event_name'].iloc[0]
        series_type = match_data['series_type'].iloc[0]
        is_lan = match_data['is_lan'].iloc[0]
        
        # Determine teams - only show each team once
        teams_in_match = sorted(match_data['team_name'].unique())
        team1 = teams_in_match[0]
        team2 = teams_in_match[1] if len(teams_in_match) > 1 else teams_in_match[0]
        
        # Calculate wins per team
        team1_wins = len(match_data[(match_data['team_name'] == team1) & (match_data['won_map'] == True)]['map_number'].unique())
        team2_wins = len(match_data[(match_data['team_name'] == team2) & (match_data['won_map'] == True)]['map_number'].unique())
        
        # ========== MATCH HEADER WITH LOGOS ==========
        col1, col2, col3 = st.columns([1.5, 1, 1.5])
        
        # Team 1
        with col1:
            try:
                logo_path1 = f'data/team_logos/{team1.replace(" ", "_").lower()}.png'
                st.image(logo_path1, width=100, use_column_width=False)
            except:
                st.info("📷 Logo")
            st.markdown(f"## {team1}")
            st.metric("Maps Won", team1_wins)
        
        # VS
        with col2:
            st.markdown("## VS")
            col_score1, col_score2 = st.columns(2)
            with col_score1:
                st.metric("Score", team1_wins)
            with col_score2:
                st.metric("Score", team2_wins)
        
        # Team 2
        with col3:
            try:
                logo_path2 = f'data/team_logos/{team2.replace(" ", "_").lower()}.png'
                st.image(logo_path2, width=100, use_column_width=False)
            except:
                st.info("📷 Logo")
            st.markdown(f"## {team2}")
            st.metric("Maps Won", team2_wins)
        
        st.markdown(f"**{match_date.strftime('%B %d, %Y')}** | {event_name} | {series_type} | {'🏟️ LAN' if is_lan else '🌐 Online'}")
        st.divider()
        
        # ========== TABS: OVERVIEW + MAP BREAKDOWN ==========
        maps_in_match = sorted(match_data['map_number'].unique())
        
        if len(maps_in_match) > 0:
            # Create tab labels with Overview first
            tab_labels = ["📊 Overview"] + [f"Map {int(m)}" for m in maps_in_match]
            map_tabs = st.tabs(tab_labels)
            
            # ========== OVERVIEW TAB ==========
            with map_tabs[0]:
                st.markdown("## Series Overview")
                
                # Series stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Maps", len(maps_in_match))
                with col2:
                    st.metric("Game Modes", match_data['mode'].nunique())
                with col3:
                    st.metric("Unique Maps", match_data['map_name'].nunique())
                with col4:
                    st.metric("Event Type", "🏟️ LAN" if is_lan else "🌐 Online")
                
                st.markdown("---")
                
                # Team comparison across all maps
                st.markdown("### Team Stats (All Maps)")
                
                team_overview_stats = []
                for team in [team1, team2]:
                    team_data = match_data[match_data['team_name'] == team]
                    if len(team_data) > 0:
                        team_stats = team_data.agg({
                            'kills': ['sum', 'mean'],
                            'deaths': ['sum', 'mean'],
                            'assists': ['sum', 'mean'],
                            'damage': ['sum', 'mean'],
                            'rating': 'mean',
                        })
                        team_overview_stats.append({
                            'Team': team,
                            'Total Kills': int(team_stats['kills']['sum']),
                            'Avg Kills': round(team_stats['kills']['mean'], 2),
                            'Total Deaths': int(team_stats['deaths']['sum']),
                            'Avg Deaths': round(team_stats['deaths']['mean'], 2),
                            'Avg K/D': round(team_stats['kills']['mean'] / max(team_stats['deaths']['mean'], 1), 2),
                            'Total Damage': int(team_stats['damage']['sum']),
                            'Avg Rating': round(team_stats['rating'], 2),
                        })
                
                comparison_df = pd.DataFrame(team_overview_stats)
                st.dataframe(
                    comparison_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Team': st.column_config.TextColumn('Team', width='medium'),
                        'Total Kills': st.column_config.NumberColumn('Total Kills', format='%d'),
                        'Avg Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
                        'Total Deaths': st.column_config.NumberColumn('Total Deaths', format='%d'),
                        'Avg Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
                        'Avg K/D': st.column_config.NumberColumn('Avg K/D', format='%.2f'),
                        'Total Damage': st.column_config.NumberColumn('Total Damage', format='%d'),
                        'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
                    }
                )
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_kills = px.bar(
                        comparison_df,
                        x='Team',
                        y='Total Kills',
                        color='Team',
                        color_discrete_map={team1: '#1f77b4', team2: '#ff7f0e'},
                        title="Total Kills (Series)",
                    )
                    fig_kills.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_kills, use_container_width=True)
                
                with col2:
                    fig_rating = px.bar(
                        comparison_df,
                        x='Team',
                        y='Avg Rating',
                        color='Team',
                        color_discrete_map={team1: '#1f77b4', team2: '#ff7f0e'},
                        title="Avg Rating (Series)",
                    )
                    fig_rating.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_rating, use_container_width=True)
                
                st.markdown("---")
                
                # Top performers
                st.markdown("### Top Performers (Series)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"#### {team1}")
                    team1_full_data = match_data[match_data['team_name'] == team1]
                    team1_players = team1_full_data.groupby('player_name').agg({
                        'kills': 'sum',
                        'deaths': 'sum',
                        'rating': 'mean',
                    }).reset_index()
                    team1_players.columns = ['Player', 'Total Kills', 'Total Deaths', 'Avg Rating']
                    team1_players['K/D'] = (team1_players['Total Kills'] / team1_players['Total Deaths'].clip(lower=1)).round(2)
                    team1_players = team1_players.sort_values('Total Kills', ascending=False).head(5)
                    
                    st.dataframe(
                        team1_players[['Player', 'Total Kills', 'K/D', 'Avg Rating']],
                        use_container_width=True,
                        hide_index=True,
                    )
                
                with col2:
                    st.markdown(f"#### {team2}")
                    team2_full_data = match_data[match_data['team_name'] == team2]
                    team2_players = team2_full_data.groupby('player_name').agg({
                        'kills': 'sum',
                        'deaths': 'sum',
                        'rating': 'mean',
                    }).reset_index()
                    team2_players.columns = ['Player', 'Total Kills', 'Total Deaths', 'Avg Rating']
                    team2_players['K/D'] = (team2_players['Total Kills'] / team2_players['Total Deaths'].clip(lower=1)).round(2)
                    team2_players = team2_players.sort_values('Total Kills', ascending=False).head(5)
                    
                    st.dataframe(
                        team2_players[['Player', 'Total Kills', 'K/D', 'Avg Rating']],
                        use_container_width=True,
                        hide_index=True,
                    )
            
            # ========== INDIVIDUAL MAP TABS ==========
            for tab_idx, map_num in enumerate(maps_in_match):
                with map_tabs[tab_idx + 1]:  # +1 because Overview is tab 0
                    map_data = match_data[match_data['map_number'] == map_num]
                    
                    # Map info header
                    map_name = map_data['map_name'].iloc[0] if len(map_data) > 0 else 'Unknown'
                    mode = map_data['mode'].iloc[0] if len(map_data) > 0 else 'Unknown'
                    
                    # Display map image with info
                    col1, col2 = st.columns([1.2, 1.8])
                    
                    with col1:
                        try:
                            map_image_path = f'data/map_images/{map_name.replace(" ", "_").lower()}.png'
                            st.image(map_image_path, use_column_width=True)
                        except:
                            st.info("📷 Map Image")
                    
                    with col2:
                        st.markdown(f"## {map_name}")
                        st.metric("Mode", mode)
                        
                        # Determine map winner
                        team1_map_data = map_data[map_data['team_name'] == team1]
                        team2_map_data = map_data[map_data['team_name'] == team2]
                        
                        team1_won = team1_map_data['won_map'].iloc[0] if len(team1_map_data) > 0 else False
                        team2_won = team2_map_data['won_map'].iloc[0] if len(team2_map_data) > 0 else False
                        
                        # Map winner display
                        if team1_won:
                            st.success(f"✅ {team1} Won")
                        elif team2_won:
                            st.success(f"✅ {team2} Won")
                    
                    st.markdown("---")
                    
                    # Player stats table
                    st.markdown("### Player Stats")
                    
                    # Add some debug info
                    st.caption(f"Showing stats for {len(map_data)} players")
                    
                    col1, col2 = st.columns(2)
                    
                    # Team 1 stats
                    with col1:
                        st.markdown(f"#### {team1}")
                        team1_map_stats = map_data[map_data['team_name'] == team1]
                        if len(team1_map_stats) > 0:
                            team1_player_list = []
                            for _, row in team1_map_stats.iterrows():
                                kd_ratio = row['kills'] / max(row['deaths'], 1)
                                team1_player_list.append({
                                    'Player': row['player_name'],
                                    'Kills': int(row['kills']),
                                    'Deaths': int(row['deaths']),
                                    'Assists': int(row['assists']),
                                    'Damage': int(row['damage']) if row['damage'] else 0,
                                    'K/D': round(kd_ratio, 2),
                                    'Rating': round(row['rating'], 2),
                                })
                            team1_stats_df = pd.DataFrame(team1_player_list)
                            team1_stats_df = team1_stats_df.sort_values('Kills', ascending=False)
                            st.dataframe(
                                team1_stats_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'Player': st.column_config.TextColumn('Player', width='medium'),
                                    'Kills': st.column_config.NumberColumn('Kills', format='%d'),
                                    'Deaths': st.column_config.NumberColumn('Deaths', format='%d'),
                                    'Assists': st.column_config.NumberColumn('Assists', format='%d'),
                                    'Damage': st.column_config.NumberColumn('Damage', format='%d'),
                                    'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
                                    'Rating': st.column_config.NumberColumn('Rating', format='%.2f'),
                                }
                            )
                    
                    # Team 2 stats
                    with col2:
                        st.markdown(f"#### {team2}")
                        team2_map_stats = map_data[map_data['team_name'] == team2]
                        if len(team2_map_stats) > 0:
                            team2_player_list = []
                            for _, row in team2_map_stats.iterrows():
                                kd_ratio = row['kills'] / max(row['deaths'], 1)
                                team2_player_list.append({
                                    'Player': row['player_name'],
                                    'Kills': int(row['kills']),
                                    'Deaths': int(row['deaths']),
                                    'Assists': int(row['assists']),
                                    'Damage': int(row['damage']) if row['damage'] else 0,
                                    'K/D': round(kd_ratio, 2),
                                    'Rating': round(row['rating'], 2),
                                })
                            team2_stats_df = pd.DataFrame(team2_player_list)
                            team2_stats_df = team2_stats_df.sort_values('Kills', ascending=False)
                            st.dataframe(
                                team2_stats_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'Player': st.column_config.TextColumn('Player', width='medium'),
                                    'Kills': st.column_config.NumberColumn('Kills', format='%d'),
                                    'Deaths': st.column_config.NumberColumn('Deaths', format='%d'),
                                    'Assists': st.column_config.NumberColumn('Assists', format='%d'),
                                    'Damage': st.column_config.NumberColumn('Damage', format='%d'),
                                    'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
                                    'Rating': st.column_config.NumberColumn('Rating', format='%.2f'),
                                }
                            )
                    
                    # Team totals
                    st.markdown("### Team Totals")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**{team1}**")
                        team1_map_agg = team1_map_stats.agg({
                            'kills': 'sum',
                            'deaths': 'sum',
                            'rating': 'mean',
                        })
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Kills", int(team1_map_agg['kills']))
                        with col_b:
                            st.metric("Deaths", int(team1_map_agg['deaths']))
                        with col_c:
                            st.metric("Avg Rating", round(team1_map_agg['rating'], 2))
                    
                    with col2:
                        st.markdown(f"**{team2}**")
                        team2_map_agg = team2_map_stats.agg({
                            'kills': 'sum',
                            'deaths': 'sum',
                            'rating': 'mean',
                        })
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Kills", int(team2_map_agg['kills']))
                        with col_b:
                            st.metric("Deaths", int(team2_map_agg['deaths']))
                        with col_c:
                            st.metric("Avg Rating", round(team2_map_agg['rating'], 2))
                    
                    # Visualizations
                    st.markdown("### Visualizations")
                    
                    col1, col2 = st.columns(2)
                    
                    # Prepare combined data for charts
                    all_player_stats = []
                    
                    # Add team 1 players
                    team1_map_stats = map_data[map_data['team_name'] == team1]
                    for _, row in team1_map_stats.iterrows():
                        kd_ratio = row['kills'] / max(row['deaths'], 1)
                        all_player_stats.append({
                            'Player': row['player_name'],
                            'Team': team1,
                            'Kills': int(row['kills']),
                            'K/D': round(kd_ratio, 2),
                        })
                    
                    # Add team 2 players
                    team2_map_stats = map_data[map_data['team_name'] == team2]
                    for _, row in team2_map_stats.iterrows():
                        kd_ratio = row['kills'] / max(row['deaths'], 1)
                        all_player_stats.append({
                            'Player': row['player_name'],
                            'Team': team2,
                            'Kills': int(row['kills']),
                            'K/D': round(kd_ratio, 2),
                        })
                    
                    if all_player_stats:
                        all_stats_df = pd.DataFrame(all_player_stats)
                        
                        with col1:
                            # Kills comparison
                            fig_kills = px.bar(
                                all_stats_df.sort_values('Kills', ascending=True),
                                y='Player',
                                x='Kills',
                                orientation='h',
                                color='Team',
                                color_discrete_map={team1: '#1f77b4', team2: '#ff7f0e'},
                                title=f"Kills - Map {int(map_num)}",
                            )
                            fig_kills.update_layout(height=400, showlegend=False)
                            st.plotly_chart(fig_kills, use_container_width=True)
                        
                        with col2:
                            # K/D comparison
                            fig_kd = px.bar(
                                all_stats_df.sort_values('K/D', ascending=True),
                                y='Player',
                                x='K/D',
                                orientation='h',
                                color='Team',
                                color_discrete_map={team1: '#1f77b4', team2: '#ff7f0e'},
                                title=f"K/D Ratio - Map {int(map_num)}",
                            )
                            fig_kd.update_layout(height=400, showlegend=False)
                            st.plotly_chart(fig_kd, use_container_width=True)
        
        st.divider()
        
        # ========== SERIES OVERVIEW ==========
        st.markdown("## 📈 Series Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Maps", int(match_data['map_number'].max()))
        with col2:
            st.metric("Game Modes", int(match_data['mode'].nunique()))
        with col3:
            st.metric("Unique Maps", int(match_data['map_name'].nunique()))
        with col4:
            st.metric("Event Type", "🏟️ LAN" if is_lan else "🌐 Online")
        
        # Team series comparison
        st.markdown("### Team Comparison (Full Series)")
        
        team_series_stats = []
        for team in [team1, team2]:
            team_data = match_data[match_data['team_name'] == team]
            if len(team_data) > 0:
                team_stats = team_data.agg({
                    'kills': 'mean',
                    'deaths': 'mean',
                    'assists': 'mean',
                    'damage': 'mean',
                    'rating': 'mean',
                })
                team_series_stats.append({
                    'Team': team,
                    'Avg Kills': round(team_stats['kills'], 2),
                    'Avg Deaths': round(team_stats['deaths'], 2),
                    'Avg Assists': round(team_stats['assists'], 2),
                    'Avg Damage': int(team_stats['damage']),
                    'Avg Rating': round(team_stats['rating'], 2),
                })
        
        comparison_df = pd.DataFrame(team_series_stats)
        
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Avg Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
                'Avg Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
                'Avg Assists': st.column_config.NumberColumn('Avg Assists', format='%.2f'),
                'Avg Damage': st.column_config.NumberColumn('Avg Damage', format='%d'),
                'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
            }
        )
        
        # Series comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_avg_kills = px.bar(
                comparison_df,
                x='Team',
                y='Avg Kills',
                color='Team',
                color_discrete_map={team1: '#1f77b4', team2: '#ff7f0e'},
                title="Avg Kills per Player (Series)",
            )
            fig_avg_kills.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_avg_kills, use_container_width=True)
        
        with col2:
            fig_avg_rating = px.bar(
                comparison_df,
                x='Team',
                y='Avg Rating',
                color='Team',
                color_discrete_map={team1: '#1f77b4', team2: '#ff7f0e'},
                title="Avg Rating per Player (Series)",
            )
            fig_avg_rating.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_avg_rating, use_container_width=True)
        
        st.divider()
        
        # ========== TOP PERFORMERS ==========
        st.markdown("## ⭐ Top Performers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {team1}")
            team1_full_data = match_data[match_data['team_name'] == team1]
            team1_players = team1_full_data.groupby('player_name').agg({
                'kills': 'sum',
                'deaths': 'sum',
                'rating': 'mean',
            }).reset_index()
            team1_players.columns = ['Player', 'Total Kills', 'Total Deaths', 'Avg Rating']
            team1_players['K/D'] = (team1_players['Total Kills'] / team1_players['Total Deaths'].clip(lower=1)).round(2)
            team1_players = team1_players.sort_values('Total Kills', ascending=False)
            
            st.dataframe(
                team1_players[['Player', 'Total Kills', 'K/D', 'Avg Rating']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Total Kills': st.column_config.NumberColumn('Total Kills', format='%d'),
                    'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
                    'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
                }
            )
        
        with col2:
            st.markdown(f"### {team2}")
            team2_full_data = match_data[match_data['team_name'] == team2]
            team2_players = team2_full_data.groupby('player_name').agg({
                'kills': 'sum',
                'deaths': 'sum',
                'rating': 'mean',
            }).reset_index()
            team2_players.columns = ['Player', 'Total Kills', 'Total Deaths', 'Avg Rating']
            team2_players['K/D'] = (team2_players['Total Kills'] / team2_players['Total Deaths'].clip(lower=1)).round(2)
            team2_players = team2_players.sort_values('Total Kills', ascending=False)
            
            st.dataframe(
                team2_players[['Player', 'Total Kills', 'K/D', 'Avg Rating']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Total Kills': st.column_config.NumberColumn('Total Kills', format='%d'),
                    'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
                    'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
                }
            )
    
    else:
        # Display matches table (no match selected)
        st.markdown("### All Matches")
        st.markdown("Click on a row to view detailed stats:")
        
        # Create display dataframe
        display_df = matches_list.copy()
        display_df['Date'] = display_df['date'].dt.strftime('%m/%d/%Y')
        display_df['Match'] = display_df.apply(
            lambda row: f"{row['team1']} {int(row['team1_wins'])} vs {int(row['team2_wins'])} {row['team2']}", 
            axis=1
        )
        display_df['Event'] = display_df['event_name']
        display_df['Series'] = display_df['series_type']
        display_df['Venue'] = display_df['is_lan'].map({True: '🏟️ LAN', False: '🌐 Online'})
        
        # Table header
        cols = st.columns([1, 3, 2, 1, 1, 0.5])
        cols[0].markdown("**Date**")
        cols[1].markdown("**Match**")
        cols[2].markdown("**Event**")
        cols[3].markdown("**Series**")
        cols[4].markdown("**Venue**")
        
        st.divider()
        
        # Render each row
        for idx, (_, row) in enumerate(display_df.iterrows()):
            cols = st.columns([1, 3, 2, 1, 1, 0.5])
            
            with cols[0]:
                st.text(row['Date'])
            
            with cols[1]:
                if st.button(
                    row['Match'],
                    key=f"match_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.selected_match_id = row['match_id']
                    st.rerun()
            
            with cols[2]:
                st.text(row['Event'][:25])
            
            with cols[3]:
                st.text(row['Series'])
            
            with cols[4]:
                st.text(row['Venue'])

# PAGE 4: HEAD-TO-HEAD
def page_vs_opponents():
    """Display league-wide aggregated stats vs selected opponent team."""
    st.markdown('<div class="title-section"><h2>⚔️ Head-to-Head vs Opponents</h2></div>', 
                unsafe_allow_html=True)
    
    filtered_df = render_sidebar_filters()
    
    # Get all teams
    all_teams = sorted(filtered_df['opponent_team_name'].unique())
    
    # Default to Boston Breach if available
    default_team = 'Boston Breach' if 'Boston Breach' in all_teams else (all_teams[0] if all_teams else None)
    default_index = all_teams.index(default_team) if default_team else 0
    
    # Team selection filter in main area
    st.markdown("### Select Opponent Team")
    selected_opponent = st.selectbox(
        "Opponent Team",
        all_teams,
        index=default_index,
        key="vs_opponent_team",
    )
    
    if not selected_opponent:
        st.warning("No opponent teams available.")
        return
    
    # Filter data for matches against selected opponent (league-wide)
    opponent_df = filtered_df[filtered_df['opponent_team_name'] == selected_opponent]
    
    if opponent_df.empty:
        st.info(f"No data available against {selected_opponent}.")
        return
    
    st.markdown(f"### League Averages vs {selected_opponent}")
    st.markdown("*Aggregated averages across all teams who played against this opponent*")
    st.divider()
    
    # Calculate aggregated mode-specific stats
    modes = ['Hardpoint', 'Search & Destroy', 'Overload']
    mode_stats = []
    
    for mode in modes:
        mode_df = opponent_df[opponent_df['mode'] == mode]
        
        if not mode_df.empty:
            stats = {
                'Mode': mode,
                'Maps': len(mode_df),
                'Avg Kills': mode_df['kills'].mean(),
                'Avg Deaths': mode_df['deaths'].mean(),
                'K/D': mode_df['kills'].mean() / mode_df['deaths'].mean() if mode_df['deaths'].mean() > 0 else 0,
                'Avg Damage': mode_df['damage'].mean(),
                'Win %': (mode_df['won_map'].sum() / len(mode_df) * 100) if len(mode_df) > 0 else 0
            }
            mode_stats.append(stats)
    
    if not mode_stats:
        st.info("No mode statistics available.")
        return
    
    mode_stats_df = pd.DataFrame(mode_stats)
    
    # Calculate Map 1-3 Average (sum of mode averages)
    avg_kills_hp = mode_stats_df[mode_stats_df['Mode'] == 'Hardpoint']['Avg Kills'].values[0] if 'Hardpoint' in mode_stats_df['Mode'].values else 0
    avg_kills_snd = mode_stats_df[mode_stats_df['Mode'] == 'Search & Destroy']['Avg Kills'].values[0] if 'Search & Destroy' in mode_stats_df['Mode'].values else 0
    avg_kills_overload = mode_stats_df[mode_stats_df['Mode'] == 'Overload']['Avg Kills'].values[0] if 'Overload' in mode_stats_df['Mode'].values else 0
    avg_map_1_3 = avg_kills_hp + avg_kills_snd + avg_kills_overload
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_maps = len(opponent_df)
        st.metric("Total Maps", total_maps)
    
    with col2:
        st.metric("Avg Map 1-3 Kills", f"{avg_map_1_3:.1f}")
    
    with col3:
        overall_kd = opponent_df['kills'].sum() / opponent_df['deaths'].sum() if opponent_df['deaths'].sum() > 0 else 0
        st.metric("Overall K/D", f"{overall_kd:.2f}")
    
    with col4:
        win_rate = (opponent_df['won_map'].sum() / len(opponent_df) * 100) if len(opponent_df) > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    # Mode breakdown table
    st.markdown("### Mode Breakdown")
    st.dataframe(
        mode_stats_df.style.format({
            'Avg Kills': '{:.1f}',
            'Avg Deaths': '{:.1f}',
            'K/D': '{:.2f}',
            'Avg Damage': '{:.0f}',
            'Win %': '{:.1f}%'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig_kills = px.bar(
            mode_stats_df,
            x='Mode',
            y='Avg Kills',
            color='Avg Kills',
            color_continuous_scale='Blues',
            title=f"Avg Kills by Mode vs {selected_opponent}",
        )
        fig_kills.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_kills, use_container_width=True)
    
    with col2:
        fig_kd = px.bar(
            mode_stats_df,
            x='Mode',
            y='K/D',
            color='K/D',
            color_continuous_scale='Greens',
            title=f"K/D by Mode vs {selected_opponent}",
        )
        fig_kd.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_kd, use_container_width=True)
    
    # Win rate by mode
    st.markdown("### Win Rate by Mode")
    fig_wr = px.bar(
        mode_stats_df,
        x='Mode',
        y='Win %',
        color='Win %',
        color_continuous_scale='RdYlGn',
        title=f"Win Rate by Mode vs {selected_opponent}",
    )
    fig_wr.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_wr, use_container_width=True)


# ============================================================================
# PAGE 5: UPCOMING MATCHES
# ============================================================================

def page_upcoming_matches():
    """Display upcoming CDL matches."""
    st.markdown('<div class="title-section"><h2>📅 Upcoming Matches</h2></div>', 
                unsafe_allow_html=True)
    
    # Import the scraper function
    from scrape_breakingpoint import fetch_upcoming_matches
    
    # Add refresh button
    col1, col2 = st.columns([5, 1])
    with col2:
        refresh = st.button("🔄 Refresh", use_container_width=True)
    
    # Fetch upcoming matches
    with st.spinner("Loading upcoming matches..."):
        upcoming_df = fetch_upcoming_matches()
    
    if upcoming_df is None or upcoming_df.empty:
        st.info("No upcoming CDL matches found.")
        return
    
    # Convert datetime to readable format
    upcoming_df['date'] = upcoming_df['datetime'].dt.strftime('%B %d, %Y')
    upcoming_df['time'] = upcoming_df['datetime'].dt.strftime('%I:%M %p ET')
    
    # Group by event
    st.markdown(f"### Total Upcoming Matches: {len(upcoming_df)}")
    st.divider()
    
    events = upcoming_df['event_name'].unique()
    
    for event in events:
        event_matches = upcoming_df[upcoming_df['event_name'] == event]
        
        st.markdown(f"### {event}")
        st.caption(f"{len(event_matches)} matches scheduled")
        
        # Display matches in a clean format
        for _, match in event_matches.iterrows():
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.markdown(f"**{match['date']}**")
                st.caption(match['time'])
            
            with col2:
                st.markdown(f"**{match['team_1']}** vs **{match['team_2']}**")
                if match['round_name']:
                    st.caption(f"{match['round_name']} • Best of {match['best_of']}")
                else:
                    st.caption(f"Best of {match['best_of']}")
            
            with col3:
                status_emoji = "🔴" if match['status'] == 'live' else "📅"
                st.markdown(f"{status_emoji} {match['status'].title()}")
            
            st.divider()


def page_slip_creator():
    """PrizePicks-style slip creator interface."""
    st.markdown('<div class="title-section"><h2>🎯 Slip Creator</h2></div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Build your betting slips like PrizePicks!**  
    Select an upcoming match, then pick player props (Over/Under) to add to your slip.
    """)
    
    # Initialize session state
    if 'slip_picks' not in st.session_state:
        st.session_state.slip_picks = []
    if 'selected_match_id' not in st.session_state:
        st.session_state.selected_match_id = None
    
    # Try to load betting lines and upcoming matches
    from database import load_betting_lines, save_slip
    from scrape_breakingpoint import fetch_upcoming_matches
    
    # Sidebar for current slip
    with st.sidebar:
        st.markdown("### 🎫 Your Slip")
        
        if not st.session_state.slip_picks:
            st.info("No picks yet. Select props below!")
        else:
            total_picks = len(st.session_state.slip_picks)
            st.markdown(f"**{total_picks} Pick{'s' if total_picks != 1 else ''}**")
            
            # Display picks
            for i, pick in enumerate(st.session_state.slip_picks):
                pick_symbol = "🔺" if pick['pick_type'] == 'over' else "🔻"
                st.markdown(f"""
                **{i+1}. {pick_symbol} {pick['player_name']}**  
                {pick['stat_type']}: {pick['pick_type'].upper()} {pick['line_value']}  
                _{pick['map_scope']}_
                """)
                if st.button(f"❌ Remove", key=f"remove_{i}"):
                    st.session_state.slip_picks.pop(i)
                    st.rerun()
                st.divider()
            
            # Payout calculator
            st.markdown("### 💰 Potential Payout")
            stake = st.number_input("Stake Amount ($)", min_value=1, max_value=1000, value=10, step=5)
            
            # Simple multiplier calculation (demo)
            multiplier = 1.0 + (total_picks * 0.5)
            potential_payout = stake * multiplier
            
            st.metric("Multiplier", f"{multiplier}x")
            st.metric("Potential Payout", f"${potential_payout:.2f}")
            
            # Save slip button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Slip", use_container_width=True):
                    slip_name = f"Slip {datetime.now().strftime('%m/%d %I:%M%p')}"
                    slip_data = {
                        'slip_name': slip_name,
                        'stake': stake,
                        'potential_payout': potential_payout
                    }
                    picks_to_save = [
                        {'betting_line_id': p['line_id'], 'pick_type': p['pick_type']}
                        for p in st.session_state.slip_picks
                    ]
                    
                    slip_id = save_slip(slip_data, picks_to_save)
                    if slip_id:
                        st.success(f"✅ Slip saved! ID: {slip_id}")
                        st.session_state.slip_picks = []
                        st.rerun()
                    else:
                        st.warning("⚠️ Could not save slip (database unavailable)")
            
            with col2:
                if st.button("🗑️ Clear Slip", use_container_width=True):
                    st.session_state.slip_picks = []
                    st.rerun()
    
    # Main content - Show upcoming matches first
    st.markdown("### 🎮 Select a Match")
    
    # Fetch upcoming matches
    upcoming_df = fetch_upcoming_matches()
    
    # Check if we have betting lines
    betting_lines_df = load_betting_lines()
    
    # Generate demo data if no real data
    if betting_lines_df is None or betting_lines_df.empty:
        st.info("💡 **Demo Mode**: Showing sample data for testing")
        
        # Create mock upcoming matches
        mock_matches = []
        teams = [
            ('OpTic Texas', 'FaZe Vegas'),
            ('Toronto KOI', 'Boston Breach'),
            ('G2 Minnesota', 'Paris Gentle Mates'),
        ]
        
        for i, (team1, team2) in enumerate(teams):
            mock_matches.append({
                'match_id': f'demo_match_{i+1}',
                'team_1': team1,
                'team_2': team2,
                'datetime': datetime.now() + timedelta(days=i+1),
                'event_name': 'CDL Major 1 Qualifier',
                'best_of': 5,
                'status': 'upcoming'
            })
        
        upcoming_df = pd.DataFrame(mock_matches)
        
        # Create mock betting lines for demo matches
        mock_data = []
        players_by_team = {
            'OpTic Texas': ['Shotzzy', 'Dashy'],
            'FaZe Vegas': ['Simp', 'aBeZy'],
            'Toronto KOI': ['Insight', 'CleanX'],
            'Boston Breach': ['Cammy', 'Nastie'],
            'G2 Minnesota': ['Skyz', 'Mamba'],
            'Paris Gentle Mates': ['Ghosty', 'Envoy'],
        }
        
        stat_types = ['Kills', 'K/D']
        map_scopes = ['Map 1', 'Map 2', 'Map 3', 'Maps 1-3']
        
        line_id = 1
        for match_idx, (team1, team2) in enumerate(teams):
            match_id = f'demo_match_{match_idx+1}'
            all_players = players_by_team[team1] + players_by_team[team2]
            
            for player_idx, player in enumerate(all_players):
                team = team1 if player in players_by_team[team1] else team2
                
                for stat in stat_types:
                    for map_scope in map_scopes:
                        if stat == 'Kills':
                            base_line = 18 + player_idx * 2
                        else:  # K/D
                            base_line = 1.0 + player_idx * 0.15
                        
                        # Adjust for map scope
                        if 'Maps 1-3' in map_scope:
                            line_val = base_line * 3 if stat == 'Kills' else base_line
                        else:
                            line_val = base_line
                        
                        map_num = None
                        if 'Map 1' in map_scope and 'Maps' not in map_scope:
                            map_num = 1
                        elif 'Map 2' in map_scope:
                            map_num = 2
                        elif 'Map 3' in map_scope:
                            map_num = 3
                        
                        mock_data.append({
                            'id': line_id,
                            'match_id': match_id,
                            'player_name': player,
                            'team_name': team,
                            'stat_type': stat,
                            'line_value': round(line_val, 1),
                            'map_scope': map_scope,
                            'map_number': map_num,
                        })
                        line_id += 1
        
        betting_lines_df = pd.DataFrame(mock_data)
    
    if upcoming_df is None or upcoming_df.empty:
        st.warning("⚠️ No upcoming matches found. Check back later!")
        return
    
    # Display upcoming matches as clickable cards
    for idx, match in upcoming_df.iterrows():
        match_id = match['match_id']
        is_selected = st.session_state.selected_match_id == match_id
        
        # Create a card-like container
        border_color = "#4CAF50" if is_selected else "#e0e0e0"
        bg_color = "#f0f8f0" if is_selected else "#ffffff"
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            if st.button(
                f"{'✓ ' if is_selected else ''}{match['team_1']} vs {match['team_2']}",
                key=f"match_btn_{match_id}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.selected_match_id = match_id
                st.rerun()
        
        with col2:
            st.caption(match['datetime'].strftime('%b %d, %I:%M%p') if hasattr(match['datetime'], 'strftime') else 'TBD')
        
        with col3:
            # Count available lines for this match
            if betting_lines_df is not None:
                lines_count = len(betting_lines_df[betting_lines_df['match_id'] == match_id])
                st.caption(f"📊 {lines_count} props")
    
    st.divider()
    
    # Show player props for selected match
    if st.session_state.selected_match_id:
        selected_match = upcoming_df[upcoming_df['match_id'] == st.session_state.selected_match_id].iloc[0]
        
        st.markdown(f"### 📊 Player Props: {selected_match['team_1']} vs {selected_match['team_2']}")
        
        # Filter betting lines for selected match
        match_lines = betting_lines_df[betting_lines_df['match_id'] == st.session_state.selected_match_id]
        
        if match_lines.empty:
            st.warning("No betting lines available for this match yet.")
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            map_options = ['All'] + sorted(match_lines['map_scope'].unique().tolist())
            selected_map = st.selectbox("Map Scope", options=map_options, key="map_filter")
        
        with col2:
            stat_options = ['All'] + sorted(match_lines['stat_type'].unique().tolist())
            selected_stat = st.selectbox("Stat Type", options=stat_options, key="stat_filter")
        
        with col3:
            search_player = st.text_input("Search Player", "", key="player_search")
        
        # Apply filters
        filtered_lines = match_lines.copy()
        if selected_map != 'All':
            filtered_lines = filtered_lines[filtered_lines['map_scope'] == selected_map]
        if selected_stat != 'All':
            filtered_lines = filtered_lines[filtered_lines['stat_type'] == selected_stat]
        if search_player:
            filtered_lines = filtered_lines[filtered_lines['player_name'].str.contains(search_player, case=False)]
        
        # Display props
        st.markdown(f"_Showing {len(filtered_lines)} props_")
        
        for idx, row in filtered_lines.iterrows():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.markdown(f"**{row['player_name']}** ({row['team_name']})")
                st.caption(f"{row['stat_type']} • {row['map_scope']}")
            
            with col2:
                st.metric("Line", f"{row['line_value']}")
            
            with col3:
                pick_col1, pick_col2 = st.columns(2)
                with pick_col1:
                    if st.button("� Over", key=f"over_{row['id']}"):
                        pick = {
                            'line_id': row['id'],
                            'player_name': row['player_name'],
                            'team_name': row['team_name'],
                            'stat_type': row['stat_type'],
                            'line_value': row['line_value'],
                            'map_scope': row['map_scope'],
                            'pick_type': 'over'
                        }
                        st.session_state.slip_picks.append(pick)
                        st.rerun()
                
                with pick_col2:
                    if st.button("🔻 Under", key=f"under_{row['id']}"):
                        pick = {
                            'line_id': row['id'],
                            'player_name': row['player_name'],
                            'team_name': row['team_name'],
                            'stat_type': row['stat_type'],
                            'line_value': row['line_value'],
                            'map_scope': row['map_scope'],
                            'pick_type': 'under'
                        }
                        st.session_state.slip_picks.append(pick)
                        st.rerun()
            
            st.divider()
    else:
        st.info("👆 Select a match above to view available player props")


def page_slip_tracker():
    """Track and manage saved betting slips."""
    st.markdown('<div class="title-section"><h2>📋 Slip Tracker</h2></div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Track your betting slips and see results!**  
    View all your saved slips, see which ones hit, and track your overall record.
    """)
    
    # Add refresh button at the top
    col_title, col_refresh = st.columns([5, 1])
    with col_refresh:
        if st.button("🔄 Refresh Data", use_container_width=True, key="slip_tracker_refresh"):
            with st.spinner("Refreshing match data and checking slip results..."):
                # Refresh the main data
                from scrape_breakingpoint import update_data
                from database import load_from_cache, update_slip_results, load_slips as load_slips_db
                
                # Update match data
                updated = update_data(force_refresh=False)
                
                if updated:
                    # Reload data into session state
                    st.session_state.df = load_from_cache()
                    
                    # Check all pending slips
                    slips_df = load_slips_db()
                    if slips_df is not None and not slips_df.empty:
                        pending_slips = slips_df[slips_df['status'] == 'pending']
                        updated_count = 0
                        
                        for _, slip in pending_slips.iterrows():
                            if st.session_state.df is not None:
                                if update_slip_results(slip['id'], st.session_state.df):
                                    updated_count += 1
                        
                        if updated_count > 0:
                            st.success(f"✅ Updated {updated_count} pending slip(s)!")
                        else:
                            st.info("ℹ️ No slip updates available yet")
                    
                    st.rerun()
                else:
                    st.warning("⚠️ Could not refresh data")
    
    from database import load_slips
    
    slips_df = load_slips()
    
    if slips_df is None or slips_df.empty:
        st.info("""
        📭 **No slips saved yet**
        
        Create your first slip in the **Slip Creator** tab!
        """)
        return
    
    # Summary metrics
    st.markdown("### 📊 Overall Stats")
    col1, col2, col3, col4 = st.columns(4)
    
    total_slips = len(slips_df)
    won_slips = len(slips_df[slips_df['status'] == 'won'])
    pending_slips = len(slips_df[slips_df['status'] == 'pending'])
    total_staked = slips_df['stake'].sum()
    total_payout = slips_df[slips_df['status'] == 'won']['actual_payout'].sum()
    
    with col1:
        st.metric("Total Slips", total_slips)
    with col2:
        st.metric("Won", won_slips, delta=f"{(won_slips/total_slips*100):.1f}%" if total_slips > 0 else "0%")
    with col3:
        st.metric("Pending", pending_slips)
    with col4:
        profit_loss = total_payout - total_staked
        st.metric("Profit/Loss", f"${profit_loss:.2f}", delta=f"${profit_loss:.2f}")
    
    st.divider()
    
    # Check All Results button for pending slips
    if pending_slips > 0 and st.session_state.get('df') is not None:
        if st.button(f"🔄 Check All Pending Results ({pending_slips} slips)", use_container_width=False):
            with st.spinner("Checking results for all pending slips..."):
                from database import update_slip_results
                pending_slip_list = slips_df[slips_df['status'] == 'pending']
                updated_count = 0
                
                for _, slip in pending_slip_list.iterrows():
                    if update_slip_results(slip['id'], st.session_state.df):
                        updated_count += 1
                
                if updated_count > 0:
                    st.success(f"✅ Checked {updated_count} slip(s)!")
                    st.rerun()
                else:
                    st.info("ℹ️ No matches completed yet for pending slips")
    
    # Filter by status
    status_filter = st.selectbox(
        "Filter by Status",
        options=['All', 'Pending', 'Won', 'Lost', 'Void'],
        index=0
    )
    
    filtered_slips = slips_df.copy()
    if status_filter != 'All':
        filtered_slips = filtered_slips[filtered_slips['status'] == status_filter.lower()]
    
    # Display slips
    st.markdown(f"### 🎫 Slips ({len(filtered_slips)})")
    
    from database import get_slip_picks, update_slip_results
    
    for _, slip in filtered_slips.iterrows():
        # Status emoji
        status_emoji = {
            'pending': '⏳',
            'won': '✅',
            'lost': '❌',
            'void': '⚪'
        }.get(slip['status'], '❓')
        
        with st.expander(f"{status_emoji} {slip['slip_name']} - {slip['created_at'].strftime('%m/%d/%Y %I:%M%p')}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Picks", slip['num_picks'])
            with col2:
                st.metric("Stake", f"${slip['stake']:.2f}")
            with col3:
                if slip['status'] == 'won':
                    st.metric("Payout", f"${slip['actual_payout']:.2f}")
                else:
                    st.metric("Potential", f"${slip['potential_payout']:.2f}")
            with col4:
                st.markdown(f"**Status**")
                st.markdown(f"{slip['status'].title()}")
            
            # Get picks for this slip
            picks_df = get_slip_picks(slip['id'])
            
            if picks_df is not None and not picks_df.empty:
                st.markdown("---")
                st.markdown("#### 📊 Picks")
                
                # Check results button for pending slips
                if slip['status'] == 'pending' and st.session_state.get('df') is not None:
                    if st.button(f"🔄 Check Results", key=f"check_{slip['id']}"):
                        with st.spinner("Checking results..."):
                            if update_slip_results(slip['id'], st.session_state.df):
                                st.success("✅ Results updated!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Could not update results")
                
                # Display each pick
                for idx, pick in picks_df.iterrows():
                    pick_symbol = "🔺" if pick['pick_type'] == 'over' else "🔻"
                    
                    # Determine if pick hit
                    if pick['result'] == 'won':
                        result_color = "green"
                        result_emoji = "✅"
                        result_text = "HIT"
                    elif pick['result'] == 'lost':
                        result_color = "red"
                        result_emoji = "❌"
                        result_text = "CHALKED"
                    else:
                        result_color = "gray"
                        result_emoji = "⏳"
                        result_text = "PENDING"
                    
                    # Create columns for pick display
                    pcol1, pcol2, pcol3 = st.columns([3, 2, 2])
                    
                    with pcol1:
                        st.markdown(f"{pick_symbol} **{pick['player_name']}** ({pick['team_name']})")
                        st.caption(f"{pick['stat_type']} • {pick['map_scope']}")
                    
                    with pcol2:
                        st.markdown(f"**Line:** {pick['pick_type'].upper()} {pick['line_value']}")
                        if pick['actual_value'] is not None:
                            st.markdown(f"**Actual:** {pick['actual_value']:.2f}")
                    
                    with pcol3:
                        st.markdown(f":{result_color}[{result_emoji} **{result_text}**]")
                    
                    st.divider()
                
                # Power play note
                if slip['status'] == 'lost':
                    st.error("❌ **Slip Chalked** - In power play mode, all picks must hit to win.")
                elif slip['status'] == 'won':
                    st.success("✅ **All picks hit!** Congratulations!")
            else:
                st.caption("_No pick details available_")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application entry point."""
    
    # Initialize database on first load
    if 'db_initialized' not in st.session_state:
        if DATABASE_AVAILABLE:
            # Show loading animation while initializing
            loading_placeholder = st.empty()
            with loading_placeholder:
                show_loading_animation("Initializing Database", "Connecting to CDL Stats Database...")
            
            success = init_db()
            loading_placeholder.empty()
            
            if not success:
                st.warning(
                    "⚠️ Database connection failed. The app will run in fallback mode.\n\n"
                    "You can still use the app by uploading CSV files manually."
                )
        else:
            st.info(
                "ℹ️ Running in file-based mode (database not configured).\n\n"
                "To enable database features, set the DATABASE_URL environment variable."
            )
        st.session_state.db_initialized = True
    
    # Load data from database
    if 'df' not in st.session_state or st.session_state.df is None or st.session_state.df.empty:
        # Show loading animation while loading data
        loading_placeholder = st.empty()
        with loading_placeholder:
            show_loading_animation("Loading CDL Data", "Fetching player statistics and match data...")
        
        st.session_state.df = load_data_with_refresh()
        loading_placeholder.empty()
        
        if st.session_state.df.empty:
            if DATABASE_AVAILABLE:
                st.warning(
                    "⚠️ No data available in database.\n\n"
                    "Click the **Refresh Data** button to scrape the latest matches."
                )
            else:
                st.warning(
                    "⚠️ No data available.\n\n"
                    "Please upload a CSV file to get started, or configure DATABASE_URL to enable data scraping."
                )
    
    # Header
    st.title("🎮 CDL Stats Dashboard")
    st.markdown("**Interactive analytics for Call of Duty League statistics from breakingpoint.gg**")
    
    # Top bar with last updated info and refresh button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        try:
            from database import get_last_scrape_date, get_cache_stats
            last_scrape = get_last_scrape_date()
            status = get_cache_stats()
            
            if last_scrape:
                st.caption(f"� Last updated: {last_scrape.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.caption("📅 No data scraped yet")
            
            st.caption(f"📦 {status.get('matches', 0)} matches | {status.get('player_records', 0)} player records")
        except Exception as e:
            st.caption(f"📊 Data loaded | {len(st.session_state.df)} records")
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            if refresh_data():
                # Reload the data after refresh
                st.session_state.df = load_data_with_refresh()
                st.rerun()
    
    st.divider()
    
    # Show upcoming matches banner
    if not st.session_state.df.empty:
        try:
            from scrape_breakingpoint import fetch_upcoming_matches
            upcoming_df = fetch_upcoming_matches()
            
            if upcoming_df is not None and not upcoming_df.empty:
                # Get next 3 upcoming matches
                next_matches = upcoming_df.head(3)
                
                # Build banner HTML
                banner_html = '<div class="upcoming-banner">'
                banner_html += '<span class="upcoming-banner-title">🔥 UPCOMING MATCHES</span>'
                banner_html += '<div class="upcoming-banner-content">'
                
                for _, match in next_matches.iterrows():
                    match_date = match['datetime'].strftime('%b %d')
                    match_time = match['datetime'].strftime('%I:%M %p')
                    matchup = f"{match['team_1']} <span class='upcoming-vs'>vs</span> {match['team_2']}"
                    banner_html += f'<div class="upcoming-match-item">{match_date} • {matchup}</div>'
                
                banner_html += '</div></div>'
                st.markdown(banner_html, unsafe_allow_html=True)
        except Exception as e:
            pass  # Silently fail if upcoming matches can't be loaded
        
        st.divider()
        
        # Page navigation - ALWAYS show in sidebar
        pages = {
            "👤 Player Overview": page_player_overview,
            "🗺️ Map/Mode Breakdown": page_map_mode_breakdown,
            "⚔️ Head-to-Head": page_vs_opponents,
            "📅 Upcoming Matches": page_upcoming_matches,
            "🎯 Slip Creator": page_slip_creator,
            "📋 Slip Tracker": page_slip_tracker,
        }
        
        # Always show navigation in sidebar
        selected_page = st.sidebar.radio(
            "📍 Navigation",
            list(pages.keys()),
            key="main_navigation"
        )
        
        # Determine which page to show
        if 'current_team' in st.session_state or 'current_player' in st.session_state:
            # On detail page, ignore navigation selection and show Player Overview (which handles detail routing)
            pages["👤 Player Overview"]()
        else:
            # Normal navigation - display selected page
            pages[selected_page]()
    
    # Footer
    st.divider()
    st.markdown(
        """
        ---
        **CDL Stats Dashboard** | Data sourced from breakingpoint.gg  
        For questions or to add new metrics, please refer to the documentation.
        """
    )


if __name__ == "__main__":
    main()
