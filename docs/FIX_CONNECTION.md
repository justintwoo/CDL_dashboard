# 🔧 URGENT FIX: Database Connection Issue on Streamlit Cloud

## Problem
Streamlit Cloud can't connect to Supabase because:
- Error: "Cannot assign requested address" (IPv6 issue)
- The direct `db.amxinvsaknlxlgjqthho.supabase.co` host doesn't work from Streamlit Cloud's network
- Need to use the **connection pooler** instead

## Solution: Update Streamlit Secrets

### Go to Your App Settings
1. Click **"⋮"** (three dots) → **Settings**
2. Click **"Secrets"** in the left sidebar
3. **Replace the entire content** with this:

```toml
DATABASE_URL = "postgresql://postgres.amxinvsaknlxlgjqthho:%2BGq3qjKNWf3V%24q2@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
```

### Key Changes:
- ✅ Use **pooler** URL: `aws-0-us-west-1.pooler.supabase.com`
- ✅ Use **port 6543** (pooler port, not 5432)
- ✅ Include **full username**: `postgres.amxinvsaknlxlgjqthho`
- ✅ Password still URL-encoded: `%2BGq3qjKNWf3V%24q2`

### Why This Works:
- Connection pooler works better with cloud platforms
- Avoids IPv6 routing issues
- Supabase recommends pooler for serverless environments
- More reliable for intermittent connections

---

## Alternative URLs to Try (in order):

### Option 1: Transaction Pooler (Try First)
```toml
DATABASE_URL = "postgresql://postgres.amxinvsaknlxlgjqthho:%2BGq3qjKNWf3V%24q2@aws-0-us-west-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
```

### Option 2: Session Pooler
```toml
DATABASE_URL = "postgresql://postgres.amxinvsaknlxlgjqthho:%2BGq3qjKNWf3V%24q2@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
```

### Option 3: Direct with IPv4 hint
```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres?options=-c%20client_encoding=UTF8"
```

---

## Steps to Fix:

1. **Go to Streamlit Cloud** app settings
2. **Update secrets** with Option 1 (transaction pooler)
3. **Save** and wait for auto-redeploy (1 minute)
4. **Test the refresh button**
5. If still fails, try Option 2, then Option 3

---

## Getting the Correct Connection String from Supabase:

1. Go to: https://amxinvsaknlxlgjqthho.supabase.co
2. Settings → Database
3. Under "Connection String":
   - **Use "Transaction" mode** (recommended for serverless)
   - Copy the URI
   - It should look like: `postgresql://postgres.amxinvsaknlxlgjqthho:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`

4. Replace `[PASSWORD]` with URL-encoded password: `%2BGq3qjKNWf3V%24q2`

---

## Verification:

After updating secrets, you should see:
- ✅ App loads without database errors
- ✅ "Last updated" shows in header
- ✅ Refresh button works without IPv6 errors

---

**PRIORITY**: Update the Streamlit secrets NOW with the pooler URL!
