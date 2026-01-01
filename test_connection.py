"""
Test database connection for Streamlit Cloud deployment
Run this locally to verify the connection string works
"""

import os

# Test the connection string
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres"

print("🔍 Testing database connection...")
print(f"Connection string (first 50 chars): {DATABASE_URL[:50]}...")

try:
    import psycopg2
    from urllib.parse import urlparse
    
    # Parse the URL
    result = urlparse(DATABASE_URL)
    
    print(f"\n📋 Connection Details:")
    print(f"  Host: {result.hostname}")
    print(f"  Port: {result.port}")
    print(f"  Database: {result.path[1:]}")
    print(f"  Username: {result.username}")
    print(f"  Password: {'*' * len(result.password) if result.password else 'NOT SET'}")
    
    # Try to connect
    print(f"\n🔌 Attempting connection...")
    conn = psycopg2.connect(DATABASE_URL)
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    
    print(f"✅ CONNECTION SUCCESSFUL!")
    print(f"PostgreSQL version: {version[0][:50]}...")
    
    cursor.close()
    conn.close()
    
    print(f"\n🎉 Your DATABASE_URL is CORRECT!")
    print(f"Copy this to Streamlit Cloud secrets:")
    print(f'\nDATABASE_URL = "{DATABASE_URL}"')
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"Error: {e}")
    print(f"\nPossible fixes:")
    print(f"1. Check if password is URL-encoded")
    print(f"2. Verify host is 'db.amxinvsaknlxlgjqthho.supabase.co'")
    print(f"3. Make sure port is 5432")
    print(f"4. Check Supabase database is running")
