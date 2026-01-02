"""
Database migration script to add team_score and opponent_score columns
to the player_stats table in Neon PostgreSQL.

Run this script once to add the new columns to your existing database.
"""

import os
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def migrate_database():
    """Add team_score and opponent_score columns to player_stats table"""
    
    print("🔄 Starting database migration...")
    print(f"📡 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as conn:
            # Check if columns already exist
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'player_stats' 
                AND column_name IN ('team_score', 'opponent_score');
            """)
            
            result = conn.execute(check_query)
            existing_columns = [row[0] for row in result]
            
            if 'team_score' in existing_columns and 'opponent_score' in existing_columns:
                print("✅ Columns already exist! No migration needed.")
                return True
            
            # Add team_score column if it doesn't exist
            if 'team_score' not in existing_columns:
                print("➕ Adding team_score column...")
                conn.execute(text("ALTER TABLE player_stats ADD COLUMN team_score INTEGER;"))
                conn.commit()
                print("✅ Added team_score column")
            
            # Add opponent_score column if it doesn't exist
            if 'opponent_score' not in existing_columns:
                print("➕ Adding opponent_score column...")
                conn.execute(text("ALTER TABLE player_stats ADD COLUMN opponent_score INTEGER;"))
                conn.commit()
                print("✅ Added opponent_score column")
            
            print("\n✅ Migration completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Deploy your app to Streamlit Cloud (or restart local server)")
            print("   2. Click the '🔄 Refresh Data' button in the app")
            print("   3. This will re-scrape all matches with the correct scores")
            print("   4. Map scores will then display correctly (250-233, 6-1, etc.)")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CDL Dashboard - Database Migration")
    print("Adding team_score and opponent_score columns")
    print("=" * 60)
    print()
    
    if not DATABASE_URL or DATABASE_URL == "postgresql://justinwoo@localhost:5432/cdl_stats":
        print("❌ Error: DATABASE_URL not configured!")
        print("Please set your Neon database URL in the .env file or environment variables.")
        exit(1)
    
    success = migrate_database()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Migration successful!")
        print("=" * 60)
        exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Migration failed!")
        print("=" * 60)
        exit(1)
