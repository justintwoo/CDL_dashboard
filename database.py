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

# Import cloud-compatible database URL from config
from config import DATABASE_URL

# Create engine and session factory
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


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


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


def get_session():
    """Get a database session"""
    return SessionLocal()


def cache_match_data(df: pd.DataFrame) -> bool:
    """
    Cache player stats dataframe to database
    
    Args:
        df: DataFrame with player stats from scraper
    
    Returns:
        bool: True if successful, False otherwise
    """
    session = get_session()
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
            
            player_stat = PlayerStats(
                match_id=row['match_id'],
                player_name=row['player_name'],
                team_name=row['team_name'],
                opponent_team_name=row.get('opponent_team_name'),
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
    session = get_session()
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
    session = get_session()
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
    session = get_session()
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
    session = get_session()
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
    session = get_session()
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


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    init_db()
    print(get_cache_stats())
