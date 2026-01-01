"""
Utility functions for CDL stats analysis and aggregation.
These functions help compute various stats splits by mode, map, opponent, etc.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple


def get_player_overall_stats(
    df: pd.DataFrame,
    player: str,
    team: Optional[str] = None,
    season: Optional[int] = None,
    date_start: Optional[pd.Timestamp] = None,
    date_end: Optional[pd.Timestamp] = None,
) -> dict:
    """
    Get overall statistics for a player across all modes and maps.
    
    Args:
        df: Main dataframe
        player: Player name
        team: Optional team filter
        season: Optional season filter
        date_start: Optional start date
        date_end: Optional end date
    
    Returns:
        Dictionary with overall stats
    """
    filtered_df = df[df['player_name'] == player].copy()
    
    if team:
        filtered_df = filtered_df[filtered_df['team_name'] == team]
    if season:
        filtered_df = filtered_df[filtered_df['season'] == season]
    if date_start:
        filtered_df = filtered_df[filtered_df['date'] >= date_start]
    if date_end:
        filtered_df = filtered_df[filtered_df['date'] <= date_end]
    
    if filtered_df.empty:
        return {}
    
    stats = {
        'player': player,
        'maps_played': len(filtered_df),
        'avg_kills': round(filtered_df['kills'].mean(), 2),
        'avg_deaths': round(filtered_df['deaths'].mean(), 2),
        'avg_assists': round(filtered_df['assists'].mean(), 2),
        'avg_damage': round(filtered_df['damage'].mean(), 2),
        'kd_ratio': round(
            filtered_df['kills'].sum() / max(filtered_df['deaths'].sum(), 1), 2
        ),
        'total_kills': filtered_df['kills'].sum(),
        'total_deaths': filtered_df['deaths'].sum(),
        'total_damage': filtered_df['damage'].sum(),
        'avg_rating': round(filtered_df['rating'].mean(), 2) if 'rating' in filtered_df.columns else None,
        'win_rate': round(
            filtered_df['won_map'].sum() / len(filtered_df), 2
        ) if 'won_map' in filtered_df.columns else None,
    }
    
    return stats


def get_player_mode_stats(
    df: pd.DataFrame,
    player: str,
    team: Optional[str] = None,
    season: Optional[int] = None,
    date_start: Optional[pd.Timestamp] = None,
    date_end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Get player stats broken down by mode (Hardpoint, S&D, Overload).
    
    Args:
        df: Main dataframe
        player: Player name
        team: Optional team filter
        season: Optional season filter
        date_start: Optional start date
        date_end: Optional end date
    
    Returns:
        DataFrame with stats by mode
    """
    filtered_df = df[df['player_name'] == player].copy()
    
    if team:
        filtered_df = filtered_df[filtered_df['team_name'] == team]
    if season:
        filtered_df = filtered_df[filtered_df['season'] == season]
    if date_start:
        filtered_df = filtered_df[filtered_df['date'] >= date_start]
    if date_end:
        filtered_df = filtered_df[filtered_df['date'] <= date_end]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    mode_stats = filtered_df.groupby('mode').agg({
        'kills': ['mean', 'sum', 'count'],
        'deaths': ['mean', 'sum'],
        'assists': ['mean'],
        'damage': ['mean', 'sum'],
        'rating': ['mean'],
        'won_map': ['sum'],
    }).reset_index()
    
    # Flatten column names
    mode_stats.columns = [
        'Mode',
        'Avg_Kills', 'Total_Kills', 'Maps_Played',
        'Avg_Deaths', 'Total_Deaths',
        'Avg_Assists',
        'Avg_Damage', 'Total_Damage',
        'Avg_Rating',
        'Wins',
    ]
    
    # Calculate K/D and win rate
    mode_stats['KD_Ratio'] = (
        mode_stats['Total_Kills'] / 
        mode_stats['Total_Deaths'].replace(0, 1)
    ).round(2)
    
    mode_stats['Win_Rate'] = (
        mode_stats['Wins'] / mode_stats['Maps_Played']
    ).round(2)
    
    # Round numeric columns
    numeric_cols = mode_stats.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['Maps_Played', 'Total_Kills', 'Total_Deaths', 'Total_Damage', 'Wins']:
            mode_stats[col] = mode_stats[col].round(2)
    
    return mode_stats


def get_player_map_mode_stats(
    df: pd.DataFrame,
    player: str,
    mode: str,
    team: Optional[str] = None,
    season: Optional[int] = None,
    date_start: Optional[pd.Timestamp] = None,
    date_end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Get per-map stats for a player in a specific mode.
    
    Args:
        df: Main dataframe
        player: Player name
        mode: Game mode (e.g., 'Hardpoint', 'Search & Destroy')
        team: Optional team filter
        season: Optional season filter
        date_start: Optional start date
        date_end: Optional end date
    
    Returns:
        DataFrame with per-map stats
    """
    filtered_df = df[
        (df['player_name'] == player) &
        (df['mode'] == mode)
    ].copy()
    
    if team:
        filtered_df = filtered_df[filtered_df['team_name'] == team]
    if season:
        filtered_df = filtered_df[filtered_df['season'] == season]
    if date_start:
        filtered_df = filtered_df[filtered_df['date'] >= date_start]
    if date_end:
        filtered_df = filtered_df[filtered_df['date'] <= date_end]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    map_stats = filtered_df.groupby('map_name').agg({
        'kills': ['mean', 'count'],
        'deaths': ['mean'],
        'assists': ['mean'],
        'damage': ['mean'],
        'rating': ['mean'],
        'won_map': ['sum'],
    }).reset_index()
    
    # Flatten column names
    map_stats.columns = [
        'Map',
        'Avg_Kills', 'Maps_Played',
        'Avg_Deaths',
        'Avg_Assists',
        'Avg_Damage',
        'Avg_Rating',
        'Wins',
    ]
    
    # Calculate K/D and win rate
    map_stats['KD_Ratio'] = (
        map_stats['Avg_Kills'] / 
        map_stats['Avg_Deaths'].replace(0, 1)
    ).round(2)
    
    map_stats['Win_Rate'] = (
        map_stats['Wins'] / map_stats['Maps_Played']
    ).round(2)
    
    # Sort by maps played (descending)
    map_stats = map_stats.sort_values('Maps_Played', ascending=False)
    
    # Round numeric columns
    numeric_cols = map_stats.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['Maps_Played', 'Wins']:
            map_stats[col] = map_stats[col].round(2)
    
    return map_stats


def get_player_vs_opponent_stats(
    df: pd.DataFrame,
    player: str,
    opponent_team: Optional[str] = None,
    mode: Optional[str] = None,
    map_name: Optional[str] = None,
    team: Optional[str] = None,
    season: Optional[int] = None,
    date_start: Optional[pd.Timestamp] = None,
    date_end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Get player stats vs specific opponent(s).
    
    Args:
        df: Main dataframe
        player: Player name
        opponent_team: Optional specific opponent team
        mode: Optional game mode filter
        map_name: Optional map filter
        team: Optional player's team filter
        season: Optional season filter
        date_start: Optional start date
        date_end: Optional end date
    
    Returns:
        DataFrame with stats vs opponents
    """
    filtered_df = df[df['player_name'] == player].copy()
    
    if team:
        filtered_df = filtered_df[filtered_df['team_name'] == team]
    if opponent_team:
        filtered_df = filtered_df[filtered_df['opponent_team_name'] == opponent_team]
    if mode:
        filtered_df = filtered_df[filtered_df['mode'] == mode]
    if map_name:
        filtered_df = filtered_df[filtered_df['map_name'] == map_name]
    if season:
        filtered_df = filtered_df[filtered_df['season'] == season]
    if date_start:
        filtered_df = filtered_df[filtered_df['date'] >= date_start]
    if date_end:
        filtered_df = filtered_df[filtered_df['date'] <= date_end]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # Group by opponent
    vs_stats = filtered_df.groupby('opponent_team_name').agg({
        'kills': ['mean', 'count'],
        'deaths': ['mean'],
        'assists': ['mean'],
        'damage': ['mean'],
        'rating': ['mean'],
        'won_map': ['sum'],
    }).reset_index()
    
    # Flatten column names
    vs_stats.columns = [
        'Opponent',
        'Avg_Kills', 'Maps_Played',
        'Avg_Deaths',
        'Avg_Assists',
        'Avg_Damage',
        'Avg_Rating',
        'Wins',
    ]
    
    # Calculate K/D and win rate
    vs_stats['KD_Ratio'] = (
        vs_stats['Avg_Kills'] / 
        vs_stats['Avg_Deaths'].replace(0, 1)
    ).round(2)
    
    vs_stats['Win_Rate'] = (
        vs_stats['Wins'] / vs_stats['Maps_Played']
    ).round(2)
    
    # Sort by maps played (descending)
    vs_stats = vs_stats.sort_values('Maps_Played', ascending=False)
    
    # Round numeric columns
    numeric_cols = vs_stats.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['Maps_Played', 'Wins']:
            vs_stats[col] = vs_stats[col].round(2)
    
    return vs_stats


def get_player_timeline(
    df: pd.DataFrame,
    player: str,
    team: Optional[str] = None,
    season: Optional[int] = None,
    date_start: Optional[pd.Timestamp] = None,
    date_end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Get player stats over time (map-by-map).
    
    Args:
        df: Main dataframe
        player: Player name
        team: Optional team filter
        season: Optional season filter
        date_start: Optional start date
        date_end: Optional end date
    
    Returns:
        DataFrame ordered by date
    """
    filtered_df = df[df['player_name'] == player].copy()
    
    if team:
        filtered_df = filtered_df[filtered_df['team_name'] == team]
    if season:
        filtered_df = filtered_df[filtered_df['season'] == season]
    if date_start:
        filtered_df = filtered_df[filtered_df['date'] >= date_start]
    if date_end:
        filtered_df = filtered_df[filtered_df['date'] <= date_end]
    
    filtered_df = filtered_df.sort_values('date').reset_index(drop=True)
    filtered_df['map_index'] = range(1, len(filtered_df) + 1)
    
    return filtered_df[['date', 'map_index', 'mode', 'map_name', 'opponent_team_name',
                        'kills', 'deaths', 'assists', 'damage', 'rating']]


def get_summary_stats(df: pd.DataFrame) -> dict:
    """
    Get high-level summary stats for the entire dataset.
    
    Args:
        df: Main dataframe
    
    Returns:
        Dictionary with summary metrics
    """
    return {
        'total_matches': df['match_id'].nunique(),
        'total_maps': len(df),
        'total_players': df['player_name'].nunique(),
        'total_teams': df['team_name'].nunique(),
        'date_range': (df['date'].min(), df['date'].max()),
        'modes': df['mode'].unique().tolist(),
        'maps': df['map_name'].nunique(),
    }


def get_mode_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get distribution of maps by mode.
    
    Args:
        df: Main dataframe
    
    Returns:
        DataFrame with mode distribution
    """
    mode_dist = df['mode'].value_counts().reset_index()
    mode_dist.columns = ['Mode', 'Count']
    return mode_dist


def get_map_distribution(df: pd.DataFrame, mode: Optional[str] = None) -> pd.DataFrame:
    """
    Get distribution of maps played.
    
    Args:
        df: Main dataframe
        mode: Optional filter by mode
    
    Returns:
        DataFrame with map distribution
    """
    filtered_df = df
    if mode:
        filtered_df = df[df['mode'] == mode]
    
    map_dist = filtered_df['map_name'].value_counts().reset_index()
    map_dist.columns = ['Map', 'Count']
    return map_dist


def get_players_by_team(df: pd.DataFrame, team: str) -> List[str]:
    """
    Get list of players for a given team.
    
    Args:
        df: Main dataframe
        team: Team name
    
    Returns:
        List of player names
    """
    players = df[df['team_name'] == team]['player_name'].unique().tolist()
    return sorted(players)
