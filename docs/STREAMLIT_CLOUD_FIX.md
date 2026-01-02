# 🚨 Critical Fix: Streamlit Cloud IPv6 Issue with Supabase

## The Problem

Streamlit Cloud is trying to connect via **IPv6** but getting "Cannot assign requested address". This is a known issue with some cloud platforms and Supabase.

## The Solution: Add Connection Parameters

Update your **Streamlit Cloud Secrets** to include connection parameters that force better compatibility:

### ✅ RECOMMENDED FIX (Copy This):

```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres?sslmode=require&connect_timeout=10"
```

### What This Does:
- ✅ Forces SSL connection
- ✅ Adds 10-second timeout
- ✅ May help with IPv4/IPv6 resolution

---

## Alternative Fixes (Try In Order):

### Option 1: Use Supabase Pooler with IPv4 Prefix
```toml
# Get this from Supabase Dashboard → Settings → Database → Connection pooling
# Use the "Transaction" mode connection string
DATABASE_URL = "postgresql://postgres.amxinvsaknlxlgjqthho:%2BGq3qjKNWf3V%24q2@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
```

### Option 2: Try Different Supabase Region/Host
Go to Supabase Dashboard and check if there's an alternate host or IPv4-only endpoint.

### Option 3: Use Neon or Alternative Database
If Supabase continues to have issues, consider migrating to:
- **Neon** (https://neon.tech) - Better Streamlit Cloud compatibility
- **Railway PostgreSQL** 
- **Heroku Postgres**

---

## Immediate Action Required:

### Step 1: Update Streamlit Secrets

1. Go to your Streamlit Cloud app
2. Click ⋮ → Settings → Secrets
3. Replace with:

```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres?sslmode=require&connect_timeout=10"
```

4. Click **Save**
5. Wait 30 seconds for auto-redeploy

### Step 2: Check Supabase Connection Pooling Settings

1. Go to: https://amxinvsaknlxlgjqthho.supabase.co
2. Settings → Database → Connection Pooling
3. Make sure it's **enabled**
4. Try the "Transaction" mode connection string

### Step 3: Contact Supabase Support (If Still Failing)

The IPv6 issue might be on Supabase's end. They may need to:
- Enable IPv4-only mode
- Fix IPv6 routing for your project
- Provide alternative endpoints

---

## Why This Is Happening:

1. **Streamlit Cloud uses IPv6** for outbound connections
2. **Supabase returns IPv6 address** for `db.amxinvsaknlxlgjqthho.supabase.co`
3. **Network routing fails** between Streamlit Cloud and Supabase IPv6
4. Error: "Cannot assign requested address"

This is a **network infrastructure issue**, not a code issue.

---

## Quick Workaround: Use Neon Database (5 minutes)

If Supabase continues to fail, here's a quick migration:

### 1. Create Neon Account
- Go to https://neon.tech
- Sign up (free)
- Create new project

### 2. Get Connection String
- Copy the connection string from dashboard
- It will look like: `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname`

### 3. Update Streamlit Secrets
```toml
DATABASE_URL = "postgresql://[your-neon-connection-string]"
```

### 4. Initialize Database
The app will auto-create tables on first run.

---

## For Now: Try These Secrets

**Try #1** (with SSL and timeout):
```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres?sslmode=require&connect_timeout=10"
```

**Try #2** (force IPv4 if supported):
```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres?sslmode=require&target_session_attrs=any"
```

**Try #3** (minimal):
```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres"
```

Update secrets, save, wait 30 seconds, and test each one.

---

Let me know which option works, or if we need to migrate to Neon for better Streamlit Cloud compatibility!
