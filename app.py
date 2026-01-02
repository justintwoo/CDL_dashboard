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
    from fetch_player_images import load_player_images
except ImportError:
    def load_player_images():
        """Fallback if image module not available"""
        return {}

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
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING & CACHING
# ============================================================================

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
    
    with st.spinner("🔄 Refreshing data from breakingpoint.gg..."):
        try:
            # Get the last scrape date
            last_date = get_last_scrape_date()
            if last_date:
                start_date_str = last_date.strftime('%Y-%m-%d')
                st.info(f"Scraping matches from {start_date_str} to now...")
            else:
                start_date_str = None
                st.info("Scraping matches from past 7 days...")
            
            # Scrape new data
            new_df = scrape_live_data(start_date=start_date_str)
            
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
            st.error(f"❌ Error refreshing data: {e}")
            import traceback
            st.code(traceback.format_exc())
            return False


# Legacy function for backward compatibility
def load_data(csv_path: str = "data/breakingpoint_cod_stats.csv") -> pd.DataFrame:
    """Legacy function - now just calls load_data_with_refresh()"""
    return load_data_with_refresh()


# ============================================================================
# SIDEBAR FILTERS
# ============================================================================

def render_sidebar_filters():
    """Render common filters in the sidebar."""
    st.sidebar.markdown("### 🎮 Filters")
    
    # Season filter
    seasons = sorted(st.session_state.df['season'].unique())
    selected_seasons = st.sidebar.multiselect(
        "Seasons",
        seasons,
        default=seasons,
        key="season_filter",
    )
    
    # Event filter
    events = sorted(st.session_state.df['event_name'].unique())
    selected_events = st.sidebar.multiselect(
        "Events",
        events,
        default=events,
        key="event_filter",
    )
    
    # LAN vs Online filter
    lan_options = st.sidebar.multiselect(
        "LAN / Online",
        ["LAN", "Online"],
        default=["LAN", "Online"],
        key="lan_filter",
    )
    
    # Apply filters
    filtered_df = st.session_state.df.copy()
    
    if selected_seasons:
        filtered_df = filtered_df[filtered_df['season'].isin(selected_seasons)]
    
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
        st.session_state.player_images = load_player_images()
    
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
# PAGE 2: PLAYER OVERVIEW
# ============================================================================

def page_player_overview():
    """Display team-organized player statistics across all game modes."""
    st.markdown('<div class="title-section"><h2>👤 Player Overview</h2></div>', 
                unsafe_allow_html=True)
    
    filtered_df = render_sidebar_filters()
    
    # Load player images
    import json
    player_images = {}
    try:
        with open('data/player_images.json', 'r') as f:
            player_images = json.load(f)
    except:
        st.warning("Player images not found. Displaying without images.")
    
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
        
        # Team header with records
        st.markdown(f"### {team}")
        st.caption(f"**Match Record: {series_wins}-{series_losses}**")
        st.caption(f"Hardpoint: **{hp_won}-{hp_lost}** | Search & Destroy: **{snd_won}-{snd_lost}** | Overload: **{overload_won}-{overload_lost}**")
        
        # Get players for this team (from roster or from data)
        if team in team_player_map:
            players = team_player_map[team]
        else:
            players = sorted(team_df['player_name'].unique())
        
        # Create columns for each player (max 4 per row)
        cols = st.columns(4)
        
        for idx, player in enumerate(players):
            player_data = team_df[team_df['player_name'] == player]
            
            if player_data.empty:
                continue
            
            with cols[idx % 4]:
                # Player image
                if player in player_images:
                    st.image(player_images[player], width=150, use_container_width=False)
                else:
                    st.markdown(f"**{player}**")
                
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
                
                # Display player name, position, and stats
                st.markdown(f"**{player}**")
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
    
    filtered_df = render_sidebar_filters()
    
    # Check if position data is available
    if 'position' not in filtered_df.columns:
        st.warning("⚠️ Position data not available in the dataset.")
        return
    
    # Main area filters
    st.markdown("### Filters")
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
    """Display head-to-head stats vs opponents."""
    st.markdown('<div class="title-section"><h2>⚔️ Head-to-Head vs Opponents</h2></div>', 
                unsafe_allow_html=True)
    
    filtered_df = render_sidebar_filters()
    
    # Sidebar selections
    st.sidebar.markdown("### Selection")
    
    all_players = sorted(filtered_df['player_name'].unique())
    selected_player = st.sidebar.selectbox(
        "Select Player",
        all_players,
        key="vs_player",
    )
    
    if not selected_player:
        st.warning("No players available.")
        return
    
    player_df = filtered_df[filtered_df['player_name'] == selected_player]
    
    all_opponents = sorted(player_df['opponent_team_name'].unique())
    selected_opponents = st.sidebar.multiselect(
        "Select Opponents",
        all_opponents,
        default=all_opponents[:3] if len(all_opponents) > 0 else [],
    )
    
    if not selected_opponents:
        st.warning("Please select at least one opponent.")
        return
    
    st.markdown(f"### {selected_player} vs Selected Opponents")
    
    # Get vs stats for each opponent
    vs_stats_list = []
    for opponent in selected_opponents:
        vs_stats = get_player_vs_opponent_stats(
            player_df,
            selected_player,
            opponent_team=opponent,
        )
        if not vs_stats.empty:
            vs_stats_list.append(vs_stats)
    
    if not vs_stats_list:
        st.info("No data available for selected filters.")
        return
    
    vs_stats_combined = pd.concat(vs_stats_list, ignore_index=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Maps vs Selected", vs_stats_combined['Maps_Played'].sum())
    with col2:
        avg_kills = vs_stats_combined['Avg_Kills'].mean()
        st.metric("Avg Kills", round(avg_kills, 2))
    with col3:
        avg_kd = vs_stats_combined['KD_Ratio'].mean()
        st.metric("Avg K/D", round(avg_kd, 2))
    with col4:
        win_rate = (vs_stats_combined['Wins'].sum() / vs_stats_combined['Maps_Played'].sum())
        st.metric("Overall Win Rate", f"{(win_rate * 100):.1f}%")
    
    # Opponent stats table
    st.markdown("#### Stats by Opponent")
    display_cols = [
        'Opponent', 'Maps_Played', 'Avg_Kills', 'Avg_Deaths',
        'KD_Ratio', 'Avg_Damage', 'Win_Rate'
    ]
    available_cols = [c for c in display_cols if c in vs_stats_combined.columns]
    
    st.dataframe(
        vs_stats_combined[available_cols].sort_values('Maps_Played', ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_kills = px.bar(
            vs_stats_combined.sort_values('Avg_Kills', ascending=False),
            x='Opponent',
            y='Avg_Kills',
            color='Avg_Kills',
            color_continuous_scale='Blues',
            title="Avg Kills vs Opponent",
        )
        fig_kills.update_layout(height=400)
        st.plotly_chart(fig_kills, use_container_width=True)
    
    with col2:
        fig_kd = px.bar(
            vs_stats_combined.sort_values('KD_Ratio', ascending=False),
            x='Opponent',
            y='KD_Ratio',
            color='KD_Ratio',
            color_continuous_scale='Greens',
            title="K/D Ratio vs Opponent",
        )
        fig_kd.update_layout(height=400)
        st.plotly_chart(fig_kd, use_container_width=True)
    
    # Win rate by opponent
    st.markdown("#### Win Rate vs Opponent")
    fig_wr = px.bar(
        vs_stats_combined.sort_values('Win_Rate', ascending=False),
        x='Opponent',
        y='Win_Rate',
        color='Win_Rate',
        color_continuous_scale='RdYlGn',
        title="Win Rate vs Opponent",
    )
    fig_wr.update_layout(height=400)
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


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application entry point."""
    
    # Initialize database on first load
    if 'db_initialized' not in st.session_state:
        if DATABASE_AVAILABLE:
            success = init_db()
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
        st.session_state.df = load_data_with_refresh()
        
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
    
    # Show data metrics
    if not st.session_state.df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Maps", len(st.session_state.df))
        with col2:
            st.metric("Unique Matches", st.session_state.df['match_id'].nunique())
        with col3:
            st.metric("Unique Players", st.session_state.df['player_name'].nunique())
        
        st.divider()
        
        # Page navigation
        pages = {
            "👤 Player Overview": page_player_overview,
            "🗺️ Map/Mode Breakdown": page_map_mode_breakdown,
            "⚔️ Head-to-Head": page_vs_opponents,
            "📅 Upcoming Matches": page_upcoming_matches,
        }
        
        selected_page = st.sidebar.radio(
            "📍 Navigation",
            list(pages.keys()),
        )
        
        # Display selected page
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
