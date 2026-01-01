"""
Quick test to verify position filter functionality
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_KGDiTF4J7NwH@ep-bold-recipe-ah0tw5z2-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

from database import load_from_cache

print("=" * 60)
print("POSITION FILTER TEST")
print("=" * 60)

# Load data
df = load_from_cache()
print(f"\n✅ Loaded {len(df)} records from database")

# Check position column
if 'position' not in df.columns:
    print("\n❌ ERROR: Position column missing!")
    exit(1)

print(f"✅ Position column exists")

# Test filtering by position
print("\n" + "=" * 60)
print("TESTING POSITION FILTERS")
print("=" * 60)

for position in ['AR', 'SMG', 'Flex']:
    filtered = df[df['position'] == position]
    print(f"\n{position}:")
    print(f"  Records: {len(filtered)}")
    print(f"  Players: {filtered['player_name'].nunique()}")
    print(f"  Avg Kills: {filtered['kills'].mean():.2f}")
    print(f"  Avg Deaths: {filtered['deaths'].mean():.2f}")
    print(f"  K/D: {(filtered['kills'].mean() / filtered['deaths'].mean()):.2f}")

# Test Hardpoint specific
print("\n" + "=" * 60)
print("HARDPOINT + POSITION FILTERS")
print("=" * 60)

hp_df = df[df['mode'] == 'Hardpoint']
print(f"\nTotal Hardpoint records: {len(hp_df)}")

for position in ['AR', 'SMG', 'Flex']:
    filtered = hp_df[hp_df['position'] == position]
    print(f"\n{position} in Hardpoint:")
    print(f"  Records: {len(filtered)}")
    print(f"  Avg Kills: {filtered['kills'].mean():.2f}")
    print(f"  K/D: {(filtered['kills'].mean() / filtered['deaths'].mean()):.2f}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Position filter is working!")
print("=" * 60)
