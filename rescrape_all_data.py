"""
Re-scrape all CDL data from scratch to populate team_score and opponent_score columns.
This script will:
1. Clear all existing cached data
2. Re-scrape all matches from the beginning of the season
3. Save with correct team_score and opponent_score fields
"""

import sys
from datetime import datetime
from database import clear_cache, cache_match_data, update_last_scrape_date
from scrape_breakingpoint import scrape_live_data

def rescrape_all_data():
    """Clear cache and re-scrape all data from the beginning"""
    
    print("=" * 70)
    print("CDL Dashboard - Full Data Re-scrape")
    print("This will re-scrape ALL matches with correct scores")
    print("=" * 70)
    print()
    
    # Step 1: Clear existing cache
    print("🗑️  Step 1: Clearing existing cached data...")
    try:
        success = clear_cache()
        if success:
            print("✅ Cache cleared successfully")
        else:
            print("⚠️  Cache may already be empty")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        return False
    
    print()
    
    # Step 2: Re-scrape all data from the beginning of the season
    print("📥 Step 2: Re-scraping all CDL 2026 matches...")
    print("   This will take a few minutes...")
    print()
    
    try:
        # Set start_date to None to scrape everything (or set to beginning of season)
        # The scraper defaults to 7 days ago if None, so let's explicitly set season start
        season_start = "2024-12-01"  # Start of CDL 2026 season
        
        print(f"   Scraping from {season_start} to present...")
        df = scrape_live_data(start_date=season_start)
        
        if df is None or df.empty:
            print("❌ No data scraped. Check your internet connection or Breaking Point availability.")
            return False
        
        print()
        print(f"✅ Successfully scraped {len(df)} player records from {df['match_id'].nunique()} matches")
        print()
        
    except Exception as e:
        print(f"❌ Error scraping data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Cache the new data
    print("💾 Step 3: Caching new data to database...")
    try:
        success = cache_match_data(df)
        if not success:
            print("❌ Failed to cache data")
            return False
        
        print("✅ Data cached successfully")
        print()
        
    except Exception as e:
        print(f"❌ Error caching data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Update last scrape date
    print("📅 Step 4: Updating last scrape timestamp...")
    try:
        update_last_scrape_date(datetime.now())
        print("✅ Timestamp updated")
        print()
    except Exception as e:
        print(f"⚠️  Warning: Could not update timestamp: {e}")
    
    # Step 5: Verify scores were captured
    print("🔍 Step 5: Verifying map scores...")
    if 'team_score' in df.columns and 'opponent_score' in df.columns:
        scored_maps = df[df['team_score'].notna()].shape[0]
        total_maps = df.shape[0]
        print(f"✅ Found scores for {scored_maps}/{total_maps} player records ({scored_maps/total_maps*100:.1f}%)")
        
        # Show sample scores
        sample = df[df['team_score'].notna()].head(3)
        if not sample.empty:
            print("\n📊 Sample map scores:")
            for _, row in sample.iterrows():
                print(f"   {row['team_name']} vs {row['opponent_team_name']}")
                print(f"   {row['mode']} on {row['map_name']}: {int(row['team_score'])}-{int(row['opponent_score'])}")
                print()
    else:
        print("⚠️  Warning: team_score and opponent_score columns not found in data")
    
    return True


if __name__ == "__main__":
    print()
    
    # Confirmation prompt
    response = input("⚠️  This will DELETE all existing data and re-scrape from scratch.\n   Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Operation cancelled")
        sys.exit(0)
    
    print()
    
    success = rescrape_all_data()
    
    print()
    print("=" * 70)
    if success:
        print("🎉 Re-scrape completed successfully!")
        print()
        print("✅ Your database now has:")
        print("   • All matches from CDL 2026 season")
        print("   • Correct map scores (HP points, S&D rounds, Overload caps)")
        print("   • team_score and opponent_score fields populated")
        print()
        print("📝 Next steps:")
        print("   1. Restart your Streamlit app (or reboot on Streamlit Cloud)")
        print("   2. Map scores will now display correctly!")
    else:
        print("❌ Re-scrape failed!")
        print("   Check the error messages above for details")
    print("=" * 70)
    print()
    
    sys.exit(0 if success else 1)
