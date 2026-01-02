"""
Real-time scraper for breakingpoint.gg CDL stats.
Fetches live player statistics and caches them to PostgreSQL database.
Supports both manual refresh and automatic daily updates.
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import time
from bs4 import BeautifulSoup
import re

# Database imports
try:
    from database import cache_match_data, load_from_cache, get_cache_stats
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️  Database module not available, falling back to CSV caching")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

CDL_PLAYERS = {
    'OpTic Texas': ['Dashy', 'Huke', 'Mercules', 'Shotzzy'],
    'Paris Gentle Mates': ['Envoy', 'Ghosty', 'Neptune', 'Sib'],
    'G2 Minnesota': ['Estreal', 'Kremp', 'Mamba', 'Skyz'],
    'Toronto KOI': ['CleanX', 'Insight', 'JoeDeceives', 'ReeaL'],
    'Cloud9 New York': ['Afro', 'Beans', 'Mack', 'Vivid'],
    'Carolina Royal Ravens': ['Craze', 'Lurqxx', 'Nero', 'SlasheR'],
    'Los Angeles Thieves': ['HyDra', 'Kenny', 'Scrap', 'aBeZy'],
    'Vancouver Surge': ['Abe', 'Gwinn', 'Lqgend', 'Lunarz'],
    'Miami Heretics': ['MettalZ', 'RenKoR', 'SupeR', 'Traixx'],
    'FaZe Vegas': ['04', 'Abuzah', 'Drazah', 'Simp'],
    'Boston Breach': ['Cammy', 'Nastie', 'Purj', 'Snoopy'],
    'Riyadh Falcons': ['Cellium', 'Exnid', 'KiSMET', 'Pred'],
}

CACHE_FILE = "data/breakingpoint_cache.json"
DATA_FILE = "data/breakingpoint_cod_stats.csv"


def get_cache() -> Dict:
    """Load cache metadata"""
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'last_updated': None, 'record_count': 0}


def save_cache(cache_data: Dict):
    """Save cache metadata"""
    Path("data").mkdir(exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)


def is_update_needed() -> bool:
    """Check if data needs updating (once per day)"""
    cache = get_cache()
    last_updated = cache.get('last_updated')
    
    if not last_updated:
        return True
    
    last_update_time = datetime.fromisoformat(last_updated)
    time_since_update = datetime.now() - last_update_time
    
    # Update needed if more than 24 hours have passed
    return time_since_update >= timedelta(hours=24)


def fetch_player_stats(player_name: str) -> Optional[Dict]:
    """
    Fetch individual player stats from breakingpoint.gg
    This is a fallback for when direct stats page doesn't work
    """
    try:
        url = f"https://breakingpoint.gg/players/{player_name}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Parse player page for stats (adjust selectors based on actual site structure)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a placeholder - actual selectors depend on site structure
        # In production, you'd need to inspect the site and find the right selectors
        stats = {
            'player_name': player_name,
            'fetched_at': datetime.now().isoformat(),
        }
        
        return stats
    except Exception as e:
        print(f"Error fetching stats for {player_name}: {e}")
        return None


def fetch_stats_page(url: str) -> Optional[pd.DataFrame]:
    """
    Fetch stats from breakingpoint.gg stats page
    Handles dynamic content and returns structured data
    """
    try:
        print(f"🌐 Fetching from: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Try to extract JSON data from page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for JSON in script tags (common for React apps)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and '__INITIAL_STATE__' in script.string:
                # Found potential data - parse it
                print("✅ Found embedded data in page")
                return response
        
        return response
    except Exception as e:
        print(f"❌ Error fetching stats page: {e}")
        return None


def fetch_match_player_stats(match_id: int) -> Optional[List[Dict]]:
    """
    Fetch detailed player statistics from a specific match page.
    Extracts player_stats from each game in initialMatchState.
    Enriches each player stat with game metadata (game_num, mode, map, won_map).
    
    Args:
        match_id: The breakingpoint match ID
        
    Returns:
        List of player stat records from all games in the match
    """
    try:
        match_url = f"https://www.breakingpoint.gg/match/{match_id}"
        
        response = requests.get(match_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', type='application/json')
        
        for script in scripts:
            content = script.string
            if not content:
                continue
            
            try:
                data = json.loads(content)
                page_props = data.get('props', {}).get('pageProps', {})
                
                # Extract games with player_stats from initialMatchState
                match_state = page_props.get('initialMatchState', {})
                games = match_state.get('games', [])
                
                if games:
                    all_player_stats = []
                    for game in games:
                        # Extract game metadata
                        game_num = game.get('game_num', 1)
                        mode_name = game.get('modes', {}).get('name', 'Unknown') if game.get('modes') else 'Unknown'
                        map_name = game.get('maps', {}).get('name', 'Unknown') if game.get('maps') else 'Unknown'
                        
                        # Determine game winner from scores
                        team_1_id = game.get('team_1_id')
                        team_2_id = game.get('team_2_id')
                        team_1_score = game.get('team_1_score', 0)
                        team_2_score = game.get('team_2_score', 0)
                        
                        # Determine winning team for this specific game
                        winning_team_id = team_1_id if team_1_score > team_2_score else team_2_id if team_2_score > team_1_score else None
                        
                        # Get player stats and enrich with game metadata
                        game_player_stats = game.get('player_stats', [])
                        for player_stat in game_player_stats:
                            # Add game metadata to player stat
                            player_stat['game_num'] = game_num
                            player_stat['mode_name'] = mode_name
                            player_stat['map_name'] = map_name
                            
                            # Add won_map based on this game's winner
                            player_team_id = player_stat.get('team_id')
                            player_stat['won_map'] = (player_team_id == winning_team_id) if winning_team_id else None
                            
                            # Add team and opponent scores for this game
                            if player_team_id == team_1_id:
                                player_stat['team_score'] = team_1_score
                                player_stat['opponent_score'] = team_2_score
                            elif player_team_id == team_2_id:
                                player_stat['team_score'] = team_2_score
                                player_stat['opponent_score'] = team_1_score
                            else:
                                player_stat['team_score'] = None
                                player_stat['opponent_score'] = None
                            
                            all_player_stats.append(player_stat)
                    
                    if all_player_stats:
                        return all_player_stats
                    
            except json.JSONDecodeError:
                continue
        
        return None
        
    except Exception as e:
        print(f"  ⚠️ Error fetching match {match_id}: {e}")
        return None


def scrape_live_data(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Scrape live data from breakingpoint.gg
    Extracts match-level data from the matches page, then scrapes individual
    match pages for detailed player statistics.
    
    Args:
        start_date: Optional date string in 'YYYY-MM-DD' format. If provided, only scrapes
                   matches from this date forward. If None, defaults to 7 days ago.
    
    Returns:
        DataFrame with player-level stats or None if scraping fails
    """
    print("🔄 Scraping live matches from breakingpoint.gg...")
    
    # Calculate date threshold
    from datetime import datetime, timedelta
    if start_date:
        date_threshold = start_date
        print(f"   Scraping matches from {start_date} to now")
    else:
        date_threshold = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        print(f"   Scraping matches from past 7 days")
    
    try:
        # Fetch the matches page
        response = requests.get("https://breakingpoint.gg/matches", headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', type='application/json')
        
        # Find and parse the data
        for script in scripts:
            content = script.string
            if not content:
                continue
                
            try:
                data = json.loads(content)
                page_props = data.get('props', {}).get('pageProps', {})
                
                if 'allMatches' not in page_props:
                    continue
                
                matches = page_props['allMatches']
                print(f"✅ Found {len(matches)} total matches in database")
                
                # Filter to completed CDL 2026 season matches with scores from the specified date
                # CDL matches have "CDL" in the event name and season_id = 2026
                completed = [m for m in matches 
                            if m.get('team1') and m.get('team2') 
                            and m.get('status') == 'complete'
                            and m.get('team_1_score') is not None
                            and m.get('team_2_score') is not None
                            and m.get('datetime')
                            and m.get('datetime', '')[:10] >= date_threshold
                            and m.get('event') 
                            and 'CDL' in m.get('event', {}).get('name', '')
                            and m.get('event', {}).get('season_id') == 2026]
                
                print(f"✅ Found {len(completed)} completed CDL 2026 season matches with scores (since {date_threshold})")
                
                if not completed:
                    print("⚠️ No completed matches found")
                    return None
                
                # Now scrape individual match pages for player statistics
                print(f"🔄 Fetching player stats from {len(completed)} matches...")
                print()
                
                records = []
                
                for idx, match in enumerate(completed, 1):
                    match_id_raw = match.get('id')
                    dt = match.get('datetime')
                    event_name = match.get('event', {}).get('name', 'Unknown') if match.get('event') else 'Unknown'
                    
                    team1_name = match.get('team1', {}).get('name', 'Unknown')
                    team2_name = match.get('team2', {}).get('name', 'Unknown')
                    
                    score1 = match.get('team_1_score', 0)
                    score2 = match.get('team_2_score', 0)
                    best_of = match.get('best_of', 5)
                    is_lan = match.get('event', {}).get('type', '').lower() != 'online' if match.get('event') else False
                    match_date = dt[:10] if dt else None
                    
                    # Show progress
                    print(f"[{idx}/{len(completed)}] {team1_name} vs {team2_name}...", end=" ")
                    
                    # Fetch player stats from this match
                    player_stats = fetch_match_player_stats(match_id_raw)
                    
                    if player_stats:
                        print(f"✅ Found {len(player_stats)} player records")
                        
                        # Convert player stats to records
                        for stat in player_stats:
                            player_tag = stat.get('player_tag', f'Player_{stat.get("player_id")}')
                            team_id = stat.get('team_id')
                            
                            # won_map is now included in the stat from fetch_match_player_stats
                            team_won = stat.get('won_map')
                            
                            # Determine team name based on team_id
                            if team_id == match.get('team_1_id'):
                                player_team = team1_name
                                opponent_team = team2_name
                            elif team_id == match.get('team_2_id'):
                                player_team = team2_name
                                opponent_team = team1_name
                            else:
                                player_team = 'Unknown'
                                opponent_team = 'Unknown'
                            
                            # Get map and game info (now from enriched player stat)
                            map_num = stat.get('game_num', 1)
                            map_name = stat.get('map_name', 'Unknown')
                            mode_name = stat.get('mode_name', 'Unknown')
                            
                            # Use bp_rating if available, otherwise calculate
                            rating = stat.get('bp_rating')
                            if rating is None or rating == 0:
                                rating = round((stat.get('kills', 0) + stat.get('assists', 0) * 0.25) / max(stat.get('deaths', 1), 1), 2)
                            else:
                                rating = round(rating, 2)
                            
                            records.append({
                                'match_id': f"MATCH_{match_id_raw}",
                                'date': match_date,
                                'event_name': event_name,
                                'series_type': f"BO{best_of}",
                                'is_lan': is_lan,
                                'season': 2026,
                                'team_name': player_team,
                                'opponent_team_name': opponent_team,
                                'player_name': player_tag,
                                'mode': mode_name,
                                'map_name': map_name,
                                'map_number': map_num,
                                'kills': stat.get('kills', 0),
                                'deaths': stat.get('deaths', 0),
                                'assists': stat.get('assists', 0),
                                'damage': stat.get('damage', 0),
                                'hill_time': stat.get('hill_time', 0),
                                'plants': stat.get('plant_count', 0) or 0,
                                'defuses': stat.get('defuse_count', 0) or 0,
                                'rating': rating,
                                'won_map': team_won,
                                'team_score': stat.get('team_score'),
                                'opponent_score': stat.get('opponent_score'),
                            })
                    else:
                        print("❌ No data")
                    
                    # Throttle requests
                    time.sleep(0.5)
                
                print()
                if records:
                    df = pd.DataFrame(records)
                    print(f"✅ Created {len(df)} player records from {len(completed)} matches")
                    return df
                else:
                    print("❌ No player records generated")
                    return None
                    
            except json.JSONDecodeError:
                continue
        
        print("❌ Could not find match data in page scripts")
        return None
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_cached_data() -> Optional[pd.DataFrame]:
    """Load data from cache CSV if available"""
    try:
        if Path(DATA_FILE).exists():
            df = pd.read_csv(DATA_FILE)
            print(f"✅ Loaded {len(df)} records from cache")
            return df
    except Exception as e:
        print(f"Error loading cache: {e}")
    
    return None


# Note: generate_synthetic_player_stats is no longer needed as we now scrape real player data
# from individual match pages. The function is kept for reference but not used.


def update_data(force_refresh: bool = False) -> Optional[pd.DataFrame]:
    """
    Update data from live source or cache (database-first approach).
    
    Args:
        force_refresh: If True, always attempt live scrape
    
    Returns:
        DataFrame with stats data (from database or live scrape)
    """
    print("🔄 Checking for updates...")
    
    # Try to load from database if available and not forcing refresh
    if DATABASE_AVAILABLE and not force_refresh:
        print("� Attempting to load from database cache...")
        cached_df = load_from_cache()
        if cached_df is not None and len(cached_df) > 0:
            print("✅ Loaded from database cache")
            return cached_df
    
    # If force_refresh or database empty, try to scrape live data
    print("🔄 Scraping live data from breakingpoint.gg...")
    print()
    
    live_data = scrape_live_data()
    
    if live_data is not None and len(live_data) > 0:
        print()
        print("✅ Successfully scraped live data with player stats!")
        print()
        
        # Cache to database if available
        if DATABASE_AVAILABLE:
            print("💾 Caching to database...")
            cache_match_data(live_data)
        
        # Also save to CSV as backup
        live_data.to_csv(DATA_FILE, index=False)
        
        # Update cache metadata
        cache = get_cache()
        cache['last_updated'] = datetime.now().isoformat()
        cache['record_count'] = len(live_data)
        save_cache(cache)
        
        return live_data
    
    # Fallback to CSV cache if live scrape fails
    print()
    print("⚠️  Live scrape failed, attempting to load from CSV backup...")
    fallback_data = load_cached_data()
    
    if fallback_data is not None:
        return fallback_data
    
    print("❌ Could not load data from any source")
    return None
    # Fallback to cached data if scraping fails
    print("⚠️ Live scraping failed, using cached data")
    cached_data = load_cached_data()
    
    if cached_data is not None:
        return cached_data
    
    print("❌ No data available (neither live nor cache)")
    return None


def get_data_status() -> Dict:
    """Get current data status for display in dashboard"""
    # Try to get status from database first
    if DATABASE_AVAILABLE:
        db_stats = get_cache_stats()
        if db_stats['is_cached']:
            return {
                'last_updated': db_stats['latest_date'].isoformat() if db_stats['latest_date'] else None,
                'record_count': db_stats['player_records'],
                'matches_count': db_stats['matches'],
                'update_needed': False,
                'data_available': True,
                'source': 'database',
            }
    
    # Fallback to CSV cache metadata
    cache = get_cache()
    last_updated = cache.get('last_updated')
    record_count = cache.get('record_count', 0)
    
    status = {
        'last_updated': last_updated,
        'record_count': record_count,
        'update_needed': is_update_needed(),
        'data_available': Path(DATA_FILE).exists(),
        'source': 'csv',
    }
    
    return status


if __name__ == "__main__":
    print("=" * 70)
    print("🎮 BREAKINGPOINT.GG REAL-TIME SCRAPER")
    print("=" * 70)
    print()
    
    # Show current status
    status = get_data_status()
    print(f"📊 Current Status:")
    print(f"  Data Available: {status['data_available']}")
    print(f"  Record Count: {status['record_count']}")
    print(f"  Last Updated: {status['last_updated']}")
    print(f"  Update Needed: {status['update_needed']}")
    print()
    
    # Attempt update
    df = update_data(force_refresh=True)
    
    if df is not None:
        print()
        print(f"✅ Success! Data loaded with {len(df)} records")
        print(f"📋 Columns: {', '.join(df.columns.tolist())}")
        print()
        print("📊 Data preview:")
        print(df.head(5).to_string())
    else:
        print()
        print("❌ Failed to load data")
    
    print()
    print("=" * 70)
    print("💡 INTEGRATION WITH DASHBOARD:")
    print("=" * 70)
    print("""
In app.py:

1. Import the scraper:
   from scrape_breakingpoint import update_data, get_data_status

2. Add refresh button and auto-update:
   col1, col2 = st.columns([3, 1])
   with col2:
       if st.button("🔄 Refresh Data"):
           df = update_data(force_refresh=True)
           st.rerun()
   
   # Auto-load with daily updates
   df = update_data(force_refresh=False)

3. Show data status:
   status = get_data_status()
   st.caption(f"Last updated: {status['last_updated']}")
    """)
    print("=" * 70)


def fetch_upcoming_matches() -> Optional[pd.DataFrame]:
    """
    Fetch upcoming CDL matches from breakingpoint.gg
    
    Returns:
        DataFrame with upcoming match information or None if scraping fails
    """
    print("📅 Fetching upcoming matches from breakingpoint.gg...")
    
    try:
        response = requests.get("https://breakingpoint.gg/matches", headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', type='application/json')
        
        for script in scripts:
            content = script.string
            if not content:
                continue
                
            try:
                data = json.loads(content)
                page_props = data.get('props', {}).get('pageProps', {})
                all_matches = page_props.get('allMatches', [])
                
                if not all_matches:
                    continue
                
                # Filter for upcoming matches (status != 'complete')
                upcoming_matches = []
                
                for match in all_matches:
                    status = match.get('status')
                    if status != 'complete':
                        # Extract match info with safe access
                        team1 = match.get('team1') or {}
                        team2 = match.get('team2') or {}
                        event = match.get('event') or {}
                        round_info = match.get('round') or {}
                        
                        match_info = {
                            'match_id': match.get('id'),
                            'datetime': match.get('datetime'),
                            'team_1': team1.get('name', 'TBD'),
                            'team_2': team2.get('name', 'TBD'),
                            'team_1_id': match.get('team_1_id'),
                            'team_2_id': match.get('team_2_id'),
                            'event_name': event.get('name', 'Unknown Event'),
                            'status': status,
                            'best_of': match.get('best_of', 5),
                            'round_name': round_info.get('name', ''),
                        }
                        
                        # Only include CDL events
                        event_name = match_info['event_name']
                        if 'CDL' in event_name:
                            upcoming_matches.append(match_info)
                
                if upcoming_matches:
                    df = pd.DataFrame(upcoming_matches)
                    
                    # Sort by datetime
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.sort_values('datetime')
                    
                    print(f"✅ Found {len(df)} upcoming CDL matches")
                    return df
                else:
                    print("⚠️  No upcoming CDL matches found")
                    return None
                    
            except json.JSONDecodeError:
                continue
        
        print("❌ Could not parse match data")
        return None
        
    except Exception as e:
        print(f"❌ Error fetching upcoming matches: {e}")
        return None

