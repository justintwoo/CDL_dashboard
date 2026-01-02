"""
Database module for CDL Stats Dashboard
Handles PostgreSQL connection, caching, and data persistence
"""

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Numeric, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
import os

# Import cloud-compatible database URL from config
from config import DATABASE_URL

# Database availability flag
DATABASE_AVAILABLE = False
engine = None
SessionLocal = None
Base = declarative_base()

# Try to create engine and session factory with error handling
try:
    # Check if DATABASE_URL is properly configured
    if not DATABASE_URL or DATABASE_URL == "postgresql://justinwoo@localhost:5432/cdl_stats":
        # Local dev environment or missing environment variable
        if os.getenv("DATABASE_URL") is None:
            print("⚠️ DATABASE_URL environment variable not set. Database features will be disabled.")
            DATABASE_AVAILABLE = False
        else:
            # Try to create engine
            engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            DATABASE_AVAILABLE = True
    else:
        # Custom DATABASE_URL provided
        engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DATABASE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Failed to initialize database connection: {e}")
    print("Database features will be disabled. The app will run in file-based mode.")


# ============================================================================
# ORM MODELS
# ============================================================================

class Match(Base):
    """Match metadata table"""
    __tablename__ = "matches"
    
    match_id = Column(String(50), primary_key=True)
    date = Column(DateTime, nullable=False)
    event_name = Column(String(255))
    series_type = Column(String(100))
    is_lan = Column(Boolean)
    season = Column(String(50))
    team1_name = Column(String(255))
    team2_name = Column(String(255))
    team1_score = Column(Integer)
    team2_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    player_stats = relationship("PlayerStats", back_populates="match", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Match {self.match_id} | {self.team1_name} {self.team1_score}-{self.team2_score} {self.team2_name}>"


class PlayerStats(Base):
    """Player statistics per map per match"""
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(50), ForeignKey("matches.match_id"), nullable=False)
    player_name = Column(String(255), nullable=False)
    team_name = Column(String(255), nullable=False)
    opponent_team_name = Column(String(255))
    position = Column(String(50))  # AR, SMG, or Flex
    map_number = Column(Integer)
    map_name = Column(String(255))
    mode = Column(String(100))
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    damage = Column(Numeric(10, 2))
    rating = Column(Numeric(10, 4))
    won_map = Column(Boolean)
    game_num = Column(Integer)
    team_score = Column(Integer)  # Team's score for this map (HP points, S&D rounds, Overload caps)
    opponent_score = Column(Integer)  # Opponent's score for this map
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    match = relationship("Match", back_populates="player_stats")
    
    def __repr__(self):
        return f"<PlayerStats {self.player_name} | {self.team_name} | {self.match_id}>"


class ScrapeMetadata(Base):
    """Stores metadata about scraping operations"""
    __tablename__ = "scrape_metadata"
    
    id = Column(Integer, primary_key=True)
    last_scrape_date = Column(DateTime, nullable=False)
    scrape_timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScrapeMetadata last_scrape={self.last_scrape_date}>"


class BettingLine(Base):
    """Stores player prop betting lines from Breaking Point"""
    __tablename__ = "betting_lines"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(50), ForeignKey("matches.match_id"), nullable=False)
    player_name = Column(String(255), nullable=False)
    team_name = Column(String(255), nullable=False)
    stat_type = Column(String(100), nullable=False)  # kills, deaths, damage, etc.
    line_value = Column(Numeric(10, 2), nullable=False)  # The over/under line
    map_scope = Column(String(50), nullable=False)  # "Map 1", "Map 2", "Map 3", "Maps 1-3"
    map_number = Column(Integer)  # 1, 2, 3, or None for multi-map
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BettingLine {self.player_name} {self.stat_type} {self.line_value} ({self.map_scope})>"


class Slip(Base):
    """User-created betting slips"""
    __tablename__ = "slips"
    
    id = Column(Integer, primary_key=True)
    slip_name = Column(String(255))  # Optional user-friendly name
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, won, lost, void
    stake = Column(Numeric(10, 2))  # Amount user would bet
    potential_payout = Column(Numeric(10, 2))  # Calculated payout
    actual_payout = Column(Numeric(10, 2))  # Actual payout (if won)
    
    # Relationship
    picks = relationship("SlipPick", back_populates="slip", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Slip {self.id} | {self.slip_name} | {self.status}>"


class SlipPick(Base):
    """Individual picks within a slip"""
    __tablename__ = "slip_picks"
    
    id = Column(Integer, primary_key=True)
    slip_id = Column(Integer, ForeignKey("slips.id"), nullable=False)
    betting_line_id = Column(Integer, ForeignKey("betting_lines.id"), nullable=False)
    pick_type = Column(String(10), nullable=False)  # "over" or "under"
    result = Column(String(50))  # "won", "lost", "pending", "void"
    actual_value = Column(Numeric(10, 2))  # Actual stat value when match completes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    slip = relationship("Slip", back_populates="picks")
    
    def __repr__(self):
        return f"<SlipPick {self.pick_type} | {self.result}>"


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_db():
    """Initialize database tables"""
    if not DATABASE_AVAILABLE or engine is None:
        print("⚠️ Database not available. Skipping database initialization.")
        return False
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        print("The app will continue without database features.")
        return False


def get_session():
    """Get a database session"""
    if not DATABASE_AVAILABLE or SessionLocal is None:
        raise RuntimeError("Database not available")
    return SessionLocal()


def cache_match_data(df: pd.DataFrame) -> bool:
    """
    Cache player stats dataframe to database
    
    Args:
        df: DataFrame with player stats from scraper
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available. Skipping cache operation.")
        return False
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return False
    
    try:
        # Delete existing matches to avoid duplicates (we're replacing with fresh data)
        session.query(Match).delete()
        session.commit()
        
        # Process each match to calculate scores
        for match_id in df['match_id'].unique():
            match_df = df[df['match_id'] == match_id]
            
            # Get teams
            teams = sorted(match_df['team_name'].unique())
            if len(teams) < 2:
                continue
            
            team1_name = teams[0]
            team2_name = teams[1]
            
            # Calculate scores (number of maps won)
            team1_score = len(match_df[
                (match_df['team_name'] == team1_name) & 
                (match_df['won_map'] == True)
            ]['map_number'].unique())
            
            team2_score = len(match_df[
                (match_df['team_name'] == team2_name) & 
                (match_df['won_map'] == True)
            ]['map_number'].unique())
            
            # Get match metadata
            match_row = match_df.iloc[0]
            
            # Create match record with teams and scores
            match = Match(
                match_id=match_id,
                date=pd.to_datetime(match_row['date']).to_pydatetime(),
                event_name=str(match_row['event_name']),
                series_type=str(match_row['series_type']),
                is_lan=bool(match_row['is_lan']),
                season=str(match_row['season']),
                team1_name=str(team1_name),
                team2_name=str(team2_name),
                team1_score=int(team1_score),
                team2_score=int(team2_score),
            )
            session.add(match)
        
        session.commit()
        
        # Insert player stats
        for _, row in df.iterrows():
            # Handle both 'map_number' and 'game_num' column names
            map_num = row.get('map_number') or row.get('game_num')
            
            # Get player position
            from config import get_player_position
            position = get_player_position(row['player_name'])
            
            player_stat = PlayerStats(
                match_id=row['match_id'],
                player_name=row['player_name'],
                team_name=row['team_name'],
                opponent_team_name=row.get('opponent_team_name'),
                position=position,
                map_number=int(map_num) if pd.notna(map_num) else None,
                map_name=row.get('map_name'),
                mode=row.get('mode'),
                kills=int(row['kills']) if pd.notna(row['kills']) else None,
                deaths=int(row['deaths']) if pd.notna(row['deaths']) else None,
                assists=int(row['assists']) if pd.notna(row['assists']) else None,
                damage=float(row['damage']) if pd.notna(row['damage']) else None,
                rating=float(row['rating']) if pd.notna(row['rating']) else None,
                won_map=bool(row['won_map']) if pd.notna(row['won_map']) else None,
                game_num=int(row.get('game_num', map_num)) if pd.notna(row.get('game_num', map_num)) else None,
                team_score=int(row['team_score']) if pd.notna(row.get('team_score')) else None,
                opponent_score=int(row['opponent_score']) if pd.notna(row.get('opponent_score')) else None,
            )
            session.add(player_stat)
        
        session.commit()
        
        match_count = df['match_id'].nunique()
        print(f"✅ Cached {match_count} matches and {len(df)} player records")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error caching data: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def load_from_cache() -> Optional[pd.DataFrame]:
    """
    Load cached player stats from database
    
    Returns:
        DataFrame with all cached player stats, or None if cache is empty
    """
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available. Cannot load from cache.")
        return None
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return None
    
    try:
        # Query all player stats with match info
        query = session.query(PlayerStats).all()
        
        if not query:
            print("📭 Cache is empty")
            return None
        
        # Convert to DataFrame
        data = []
        for stat in query:
            data.append({
                'match_id': stat.match_id,
                'date': stat.match.date,
                'event_name': stat.match.event_name,
                'series_type': stat.match.series_type,
                'is_lan': stat.match.is_lan,
                'season': stat.match.season,
                'player_name': stat.player_name,
                'team_name': stat.team_name,
                'opponent_team_name': stat.opponent_team_name,
                'position': stat.position,
                'map_number': stat.map_number,
                'map_name': stat.map_name,
                'mode': stat.mode,
                'kills': stat.kills,
                'deaths': stat.deaths,
                'assists': stat.assists,
                'damage': stat.damage,
                'rating': stat.rating,
                'won_map': stat.won_map,
                'game_num': stat.game_num,
                'team_score': getattr(stat, 'team_score', None),  # Backward compatible
                'opponent_score': getattr(stat, 'opponent_score', None),  # Backward compatible
            })
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} player records from cache")
        return df
        
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return None
    finally:
        session.close()


def clear_cache():
    """Clear all cached data"""
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available. Cannot clear cache.")
        return False
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return False
    
    try:
        session.query(PlayerStats).delete()
        session.query(Match).delete()
        session.commit()
        print("✅ Cache cleared")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing cache: {e}")
        return False
    finally:
        session.close()


def get_cache_stats() -> dict:
    """Get cache statistics"""
    if not DATABASE_AVAILABLE:
        return {'is_cached': False, 'match_count': 0, 'player_count': 0}
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return {'is_cached': False, 'match_count': 0, 'player_count': 0}
    
    try:
        match_count = session.query(func.count(Match.match_id)).scalar()
        player_count = session.query(func.count(PlayerStats.id)).scalar()
        
        if match_count > 0:
            latest_match = session.query(func.max(Match.date)).scalar()
            oldest_match = session.query(func.min(Match.date)).scalar()
        else:
            latest_match = None
            oldest_match = None
        
        return {
            'matches': match_count,
            'player_records': player_count,
            'latest_date': latest_match,
            'oldest_date': oldest_match,
            'is_cached': match_count > 0,
        }
    finally:
        session.close()


def get_last_scrape_date() -> Optional[datetime]:
    """Get the last scrape date from metadata"""
    if not DATABASE_AVAILABLE:
        # Return 7 days ago as default when database not available
        return datetime.now() - timedelta(days=7)
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return datetime.now() - timedelta(days=7)
    
    try:
        metadata = session.query(ScrapeMetadata).order_by(ScrapeMetadata.scrape_timestamp.desc()).first()
        if metadata:
            return metadata.last_scrape_date
        # If no metadata exists, return 7 days ago as default
        return datetime.now() - timedelta(days=7)
    finally:
        session.close()


def update_last_scrape_date(date: datetime) -> bool:
    """Update the last scrape date in metadata"""
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available. Cannot update last scrape date.")
        return False
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return False
    
    try:
        # Create new metadata record
        metadata = ScrapeMetadata(last_scrape_date=date)
        session.add(metadata)
        session.commit()
        print(f"✅ Updated last scrape date to {date.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating last scrape date: {e}")
        return False
    finally:
        session.close()


def save_betting_lines(lines_df: pd.DataFrame) -> bool:
    """
    Save betting lines to database
    
    Args:
        lines_df: DataFrame with columns: match_id, player_name, team_name, stat_type, line_value, map_scope, map_number
    
    Returns:
        bool: True if successful
    """
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available. Cannot save betting lines.")
        return False
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return False
    
    try:
        for _, row in lines_df.iterrows():
            betting_line = BettingLine(
                match_id=row['match_id'],
                player_name=row['player_name'],
                team_name=row['team_name'],
                stat_type=row['stat_type'],
                line_value=float(row['line_value']),
                map_scope=row['map_scope'],
                map_number=int(row['map_number']) if pd.notna(row.get('map_number')) else None,
            )
            session.add(betting_line)
        
        session.commit()
        print(f"✅ Saved {len(lines_df)} betting lines")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error saving betting lines: {e}")
        return False
    finally:
        session.close()


def load_betting_lines(match_id: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Load betting lines from database
    
    Args:
        match_id: Optional match ID to filter by
    
    Returns:
        DataFrame with betting lines or None
    """
    if not DATABASE_AVAILABLE:
        return None
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return None
    
    try:
        query = session.query(BettingLine)
        if match_id:
            query = query.filter(BettingLine.match_id == match_id)
        
        lines = query.all()
        
        if not lines:
            return None
        
        data = []
        for line in lines:
            data.append({
                'id': line.id,
                'match_id': line.match_id,
                'player_name': line.player_name,
                'team_name': line.team_name,
                'stat_type': line.stat_type,
                'line_value': float(line.line_value),
                'map_scope': line.map_scope,
                'map_number': line.map_number,
                'created_at': line.created_at,
            })
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"❌ Error loading betting lines: {e}")
        return None
    finally:
        session.close()


def save_slip(slip_data: dict, picks: list) -> Optional[int]:
    """
    Save a betting slip with picks
    
    Args:
        slip_data: Dict with slip_name, stake, potential_payout
        picks: List of dicts with betting_line_id, pick_type
    
    Returns:
        Slip ID if successful, None otherwise
    """
    if not DATABASE_AVAILABLE:
        return None
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return None
    
    try:
        slip = Slip(
            slip_name=slip_data.get('slip_name', 'Untitled Slip'),
            stake=slip_data.get('stake', 0),
            potential_payout=slip_data.get('potential_payout', 0),
            status="pending"
        )
        session.add(slip)
        session.flush()  # Get slip ID
        
        for pick in picks:
            slip_pick = SlipPick(
                slip_id=slip.id,
                betting_line_id=pick['betting_line_id'],
                pick_type=pick['pick_type'],
                result="pending"
            )
            session.add(slip_pick)
        
        session.commit()
        print(f"✅ Saved slip {slip.id} with {len(picks)} picks")
        return slip.id
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error saving slip: {e}")
        return None
    finally:
        session.close()


def load_slips() -> Optional[pd.DataFrame]:
    """Load all slips from database"""
    if not DATABASE_AVAILABLE:
        return None
    
    try:
        session = get_session()
    except Exception as e:
        print(f"❌ Failed to get database session: {e}")
        return None
    
    try:
        slips = session.query(Slip).order_by(Slip.created_at.desc()).all()
        
        if not slips:
            return None
        
        data = []
        for slip in slips:
            data.append({
                'id': slip.id,
                'slip_name': slip.slip_name,
                'created_at': slip.created_at,
                'status': slip.status,
                'stake': float(slip.stake) if slip.stake else 0,
                'potential_payout': float(slip.potential_payout) if slip.potential_payout else 0,
                'actual_payout': float(slip.actual_payout) if slip.actual_payout else 0,
                'num_picks': len(slip.picks),
            })
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"❌ Error loading slips: {e}")
        return None
    finally:
        session.close()


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    init_db()
    print(get_cache_stats())
