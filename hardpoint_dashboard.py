"""
Hardpoint Dashboard for CDL Stats
Focused on Hardpoint game mode analysis with multiple views and filters
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from database import load_from_cache, init_db, get_last_scrape_date, cache_match_data, update_last_scrape_date

# Official CDL map pools by mode
CDL_MAPS = {
    'Hardpoint': ['Blackheart', 'Colossus', 'Den', 'Exposure', 'Scar'],
    'Search & Destroy': ['Colossus', 'Den', 'Exposure', 'Raid', 'Scar'],
    'Overload': ['Den', 'Exposure', 'Scar']
}


def load_data_with_refresh() -> pd.DataFrame:
    """
    Load data from database cache.
    Returns DataFrame with all CDL data.
    """
    try:
        init_db()
        df = load_from_cache()
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return pd.DataFrame()


def refresh_data():
    """
    Refresh data by scraping from last scrape date to now.
    Updates the database and last scrape timestamp.
    """
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


def filter_hardpoint_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter data to only Hardpoint mode with official CDL maps"""
    hp_df = df[df['mode'] == 'Hardpoint'].copy()
    
    # Filter to only official CDL Hardpoint maps
    hp_df = hp_df[hp_df['map_name'].isin(CDL_MAPS['Hardpoint'])]
    
    return hp_df


def page_map_stats(df: pd.DataFrame):
    """Map-level Hardpoint statistics with filters"""
    st.header("🗺️ Hardpoint Map Statistics")
    st.caption("Average kills per map with team, win/loss, and opponent filters")
    
    # Filter to Hardpoint
    hp_df = filter_hardpoint_data(df)
    
    if hp_df.empty:
        st.warning("No Hardpoint data available")
        return
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        teams = ['All'] + sorted(hp_df['team_name'].unique().tolist())
        selected_team = st.selectbox("Team", teams, key='map_team')
    
    with col2:
        win_loss = st.selectbox("Result", ['All', 'Win', 'Loss'], key='map_result')
    
    with col3:
        opponents = ['All'] + sorted(hp_df['opponent_team_name'].unique().tolist())
        selected_opponent = st.selectbox("Opponent", opponents, key='map_opponent')
    
    # Apply filters
    filtered_df = hp_df.copy()
    
    if selected_team != 'All':
        filtered_df = filtered_df[filtered_df['team_name'] == selected_team]
    
    if win_loss == 'Win':
        filtered_df = filtered_df[filtered_df['won_map'] == True]
    elif win_loss == 'Loss':
        filtered_df = filtered_df[filtered_df['won_map'] == False]
    
    if selected_opponent != 'All':
        filtered_df = filtered_df[filtered_df['opponent_team_name'] == selected_opponent]
    
    if filtered_df.empty:
        st.warning("No data matches the selected filters")
        return
    
    # Calculate average kills per map
    map_stats = filtered_df.groupby(['map_name', 'map_number']).agg({
        'kills': 'mean',
        'deaths': 'mean',
        'damage': 'mean',
        'rating': 'mean',
        'match_id': 'nunique'
    }).reset_index()
    
    map_stats = map_stats.rename(columns={
        'kills': 'Avg Kills',
        'deaths': 'Avg Deaths',
        'damage': 'Avg Damage',
        'rating': 'Avg Rating',
        'match_id': 'Matches Played'
    })
    
    map_stats = map_stats.sort_values('map_number')
    
    # Display metrics
    st.subheader("📊 Average Kills by Map")
    
    cols = st.columns(len(map_stats))
    for idx, (_, row) in enumerate(map_stats.iterrows()):
        with cols[idx]:
            st.metric(
                label=f"Map {int(row['map_number'])}: {row['map_name']}",
                value=f"{row['Avg Kills']:.1f}",
                delta=f"{row['Matches Played']:.0f} matches"
            )
    
    # Bar chart
    st.subheader("Visual Breakdown")
    
    fig = px.bar(
        map_stats,
        x='map_name',
        y='Avg Kills',
        title='Average Kills per Hardpoint Map',
        labels={'map_name': 'Map', 'Avg Kills': 'Average Kills'},
        color='Avg Kills',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("Detailed Statistics")
    
    display_df = map_stats.copy()
    display_df['Avg Kills'] = display_df['Avg Kills'].round(2)
    display_df['Avg Deaths'] = display_df['Avg Deaths'].round(2)
    display_df['Avg Damage'] = display_df['Avg Damage'].round(0)
    display_df['Avg Rating'] = display_df['Avg Rating'].round(2)
    display_df['map_number'] = display_df['map_number'].astype(int)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'map_number': st.column_config.NumberColumn('Map #', format='%d'),
            'map_name': st.column_config.TextColumn('Map Name'),
            'Avg Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
            'Avg Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
            'Avg Damage': st.column_config.NumberColumn('Avg Damage', format='%.0f'),
            'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
            'Matches Played': st.column_config.NumberColumn('Matches', format='%d'),
        }
    )


def page_player_stats(df: pd.DataFrame):
    """Player-level Hardpoint statistics with filters"""
    st.header("👤 Hardpoint Player Statistics")
    st.caption("All players' Hardpoint performance with map, team, win/loss, and opponent filters")
    
    # Filter to Hardpoint
    hp_df = filter_hardpoint_data(df)
    
    if hp_df.empty:
        st.warning("No Hardpoint data available")
        return
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        maps = ['All'] + sorted(hp_df['map_name'].unique().tolist())
        selected_map = st.selectbox("Map", maps, key='player_map')
    
    with col2:
        teams = ['All'] + sorted(hp_df['team_name'].unique().tolist())
        selected_team = st.selectbox("Team", teams, key='player_team')
    
    with col3:
        win_loss = st.selectbox("Result", ['All', 'Win', 'Loss'], key='player_result')
    
    with col4:
        opponents = ['All'] + sorted(hp_df['opponent_team_name'].unique().tolist())
        selected_opponent = st.selectbox("Opponent", opponents, key='player_opponent')
    
    # Apply filters
    filtered_df = hp_df.copy()
    
    if selected_map != 'All':
        filtered_df = filtered_df[filtered_df['map_name'] == selected_map]
    
    if selected_team != 'All':
        filtered_df = filtered_df[filtered_df['team_name'] == selected_team]
    
    if win_loss == 'Win':
        filtered_df = filtered_df[filtered_df['won_map'] == True]
    elif win_loss == 'Loss':
        filtered_df = filtered_df[filtered_df['won_map'] == False]
    
    if selected_opponent != 'All':
        filtered_df = filtered_df[filtered_df['opponent_team_name'] == selected_opponent]
    
    if filtered_df.empty:
        st.warning("No data matches the selected filters")
        return
    
    # Calculate player statistics
    player_stats = filtered_df.groupby(['player_name', 'team_name']).agg({
        'kills': 'mean',
        'deaths': 'mean',
        'assists': 'mean',
        'damage': 'mean',
        'rating': 'mean',
        'match_id': 'nunique',
        'won_map': lambda x: (x == True).sum() / len(x) * 100
    }).reset_index()
    
    player_stats = player_stats.rename(columns={
        'player_name': 'Player',
        'team_name': 'Team',
        'kills': 'Avg Kills',
        'deaths': 'Avg Deaths',
        'assists': 'Avg Assists',
        'damage': 'Avg Damage',
        'rating': 'Avg Rating',
        'match_id': 'Maps Played',
        'won_map': 'Win %'
    })
    
    # Calculate K/D ratio
    player_stats['K/D'] = player_stats['Avg Kills'] / player_stats['Avg Deaths'].replace(0, 1)
    
    # Sort by average kills
    player_stats = player_stats.sort_values('Avg Kills', ascending=False)
    
    # Display top performers
    st.subheader("🏆 Top 10 Players by Average Kills")
    
    top10 = player_stats.head(10)
    cols = st.columns(5)
    
    for idx, (_, row) in enumerate(top10.head(5).iterrows()):
        with cols[idx]:
            st.metric(
                label=row['Player'],
                value=f"{row['Avg Kills']:.1f}",
                delta=f"{row['Team']}"
            )
    
    # Bar chart for top 20
    st.subheader("Top 20 Players - Average Kills")
    
    top20 = player_stats.head(20)
    fig = px.bar(
        top20,
        x='Player',
        y='Avg Kills',
        color='Team',
        title='Top 20 Players by Average Kills in Hardpoint',
        labels={'Avg Kills': 'Average Kills', 'Player': 'Player'},
        hover_data=['Team', 'K/D', 'Avg Rating', 'Maps Played']
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Full player table
    st.subheader("All Players Statistics")
    
    display_df = player_stats.copy()
    display_df['Avg Kills'] = display_df['Avg Kills'].round(2)
    display_df['Avg Deaths'] = display_df['Avg Deaths'].round(2)
    display_df['Avg Assists'] = display_df['Avg Assists'].round(2)
    display_df['Avg Damage'] = display_df['Avg Damage'].round(0)
    display_df['Avg Rating'] = display_df['Avg Rating'].round(2)
    display_df['K/D'] = display_df['K/D'].round(2)
    display_df['Win %'] = display_df['Win %'].round(1)
    display_df['Maps Played'] = display_df['Maps Played'].astype(int)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Player': st.column_config.TextColumn('Player', width='medium'),
            'Team': st.column_config.TextColumn('Team', width='medium'),
            'Avg Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
            'Avg Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
            'Avg Assists': st.column_config.NumberColumn('Avg Assists', format='%.2f'),
            'K/D': st.column_config.NumberColumn('K/D', format='%.2f'),
            'Avg Damage': st.column_config.NumberColumn('Avg Damage', format='%.0f'),
            'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
            'Win %': st.column_config.NumberColumn('Win %', format='%.1f%%'),
            'Maps Played': st.column_config.NumberColumn('Maps Played', format='%d'),
        }
    )


def page_event_stats(df: pd.DataFrame):
    """Event-level Hardpoint statistics"""
    st.header("🏆 Hardpoint Statistics by Event")
    st.caption("Performance metrics aggregated by tournament/event")
    
    # Filter to Hardpoint
    hp_df = filter_hardpoint_data(df)
    
    if hp_df.empty:
        st.warning("No Hardpoint data available")
        return
    
    # Calculate event statistics
    event_stats = hp_df.groupby('event_name').agg({
        'kills': 'mean',
        'deaths': 'mean',
        'damage': 'mean',
        'rating': 'mean',
        'match_id': 'nunique',
        'map_number': 'count',
        'team_name': lambda x: x.nunique()
    }).reset_index()
    
    event_stats = event_stats.rename(columns={
        'event_name': 'Event',
        'kills': 'Avg Kills',
        'deaths': 'Avg Deaths',
        'damage': 'Avg Damage',
        'rating': 'Avg Rating',
        'match_id': 'Matches',
        'map_number': 'Total Maps',
        'team_name': 'Teams'
    })
    
    # Calculate K/D
    event_stats['Avg K/D'] = event_stats['Avg Kills'] / event_stats['Avg Deaths'].replace(0, 1)
    
    # Sort by total maps
    event_stats = event_stats.sort_values('Total Maps', ascending=False)
    
    # Display metrics
    st.subheader("📊 Event Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Events", len(event_stats))
    
    with col2:
        st.metric("Total Matches", event_stats['Matches'].sum())
    
    with col3:
        st.metric("Total HP Maps", event_stats['Total Maps'].sum())
    
    with col4:
        avg_kills = event_stats['Avg Kills'].mean()
        st.metric("Avg Kills/Map", f"{avg_kills:.1f}")
    
    # Bar chart - avg kills by event
    st.subheader("Average Kills by Event")
    
    fig = px.bar(
        event_stats,
        x='Event',
        y='Avg Kills',
        title='Average Kills per Event',
        labels={'Event': 'Event', 'Avg Kills': 'Average Kills'},
        color='Avg Kills',
        color_continuous_scale='Reds',
        hover_data=['Matches', 'Total Maps', 'Teams']
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("Event Statistics Table")
    
    display_df = event_stats.copy()
    display_df['Avg Kills'] = display_df['Avg Kills'].round(2)
    display_df['Avg Deaths'] = display_df['Avg Deaths'].round(2)
    display_df['Avg K/D'] = display_df['Avg K/D'].round(2)
    display_df['Avg Damage'] = display_df['Avg Damage'].round(0)
    display_df['Avg Rating'] = display_df['Avg Rating'].round(2)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Event': st.column_config.TextColumn('Event', width='large'),
            'Avg Kills': st.column_config.NumberColumn('Avg Kills', format='%.2f'),
            'Avg Deaths': st.column_config.NumberColumn('Avg Deaths', format='%.2f'),
            'Avg K/D': st.column_config.NumberColumn('Avg K/D', format='%.2f'),
            'Avg Damage': st.column_config.NumberColumn('Avg Damage', format='%.0f'),
            'Avg Rating': st.column_config.NumberColumn('Avg Rating', format='%.2f'),
            'Matches': st.column_config.NumberColumn('Matches', format='%d'),
            'Total Maps': st.column_config.NumberColumn('Total Maps', format='%d'),
            'Teams': st.column_config.NumberColumn('Teams', format='%d'),
        }
    )


def main():
    st.set_page_config(
        page_title="CDL Hardpoint Dashboard",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 CDL Hardpoint Dashboard")
    st.caption("Focused analysis of Hardpoint game mode performance")
    
    # Top bar with last updated info and refresh button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        try:
            from database import get_cache_stats
            last_scrape = get_last_scrape_date()
            status = get_cache_stats()
            
            if last_scrape:
                st.caption(f"� Last updated: {last_scrape.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.caption("📅 No data scraped yet")
            
            st.caption(f"📦 {status.get('matches', 0)} matches | {status.get('player_records', 0)} player records")
        except Exception as e:
            st.caption("📊 Data loaded from cache")
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            if refresh_data():
                # Reload the data after refresh
                if 'df' in st.session_state:
                    del st.session_state.df
                st.rerun()
    
    # Load data
    if 'df' not in st.session_state:
        with st.spinner("Loading data from database..."):
            st.session_state.df = load_data_with_refresh()
    
    df = st.session_state.df
    
    if df.empty:
        st.warning("⚠️ No data available in database. Click the **Refresh Data** button to scrape the latest matches.")
        return
    
    # Show data summary
    hp_df = filter_hardpoint_data(df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Hardpoint Maps", len(hp_df))
    with col2:
        st.metric("Unique Matches", hp_df['match_id'].nunique())
    with col3:
        st.metric("Teams", hp_df['team_name'].nunique())
    with col4:
        st.metric("Players", hp_df['player_name'].nunique())
    
    st.markdown("---")
    
    # Navigation
    tabs = st.tabs(["📊 Map Stats", "👤 Player Stats", "🏆 Event Stats"])
    
    with tabs[0]:
        page_map_stats(df)
    
    with tabs[1]:
        page_player_stats(df)
    
    with tabs[2]:
        page_event_stats(df)


if __name__ == "__main__":
    main()
