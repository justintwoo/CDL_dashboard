# 🚀 Streamlit Cloud Deployment - Step-by-Step Guide

**Repository**: https://github.com/justintwoo/CDL_dashboard  
**Status**: ✅ Ready to deploy!  
**Estimated Time**: 10 minutes

---

## ✅ Pre-Deployment Checklist (COMPLETED)

- [x] `.gitignore` created (protects `.env` file)
- [x] Code committed and pushed to GitHub
- [x] Syntax errors fixed in `app.py`
- [x] Database connection working locally
- [x] 280 player records loaded successfully

---

## 🎯 Deployment Steps (DO THIS NOW)

### Step 1: Go to Streamlit Cloud

**Open this URL**: https://share.streamlit.io/

### Step 2: Sign In with GitHub

1. Click **"Sign in with GitHub"**
2. Authorize Streamlit Cloud to access your repositories
3. You should see your GitHub account connected

### Step 3: Create New App

1. Click **"New app"** button (top right)
2. Fill in the deployment form:

```
Repository: justintwoo/CDL_dashboard
Branch: main
Main file path: app.py
App URL: (optional) cdl-dashboard-[your-custom-name]
```

### Step 4: Configure Secrets (CRITICAL!)

1. Click **"Advanced settings"** (expand it)
2. In the **"Secrets"** section, paste this EXACTLY:

```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres"
```

⚠️ **IMPORTANT**: 
- Use the TOML format (shown above)
- Include the quotes around the connection string
- This is your Supabase database URL with URL-encoded password

### Step 5: Deploy!

1. Click **"Deploy!"** button
2. Wait 2-3 minutes for deployment
3. Watch the logs - you should see:
   - Installing dependencies...
   - ✅ Database initialized
   - ✅ Loaded records from cache
   - Your app is live at: https://your-app-name.streamlit.app

### Step 6: First Data Refresh

1. Once the app loads, you'll see "No data available" message
2. Click the **"🔄 Refresh Data"** button in the top right
3. Wait 1-2 minutes for scraping to complete
4. Dashboard will reload with live match data!

---

## 🎉 Success Indicators

You'll know it worked when you see:

- ✅ App loads without errors
- ✅ "Last updated" timestamp shows
- ✅ Match list appears with real data
- ✅ Charts render correctly
- ✅ Player stats are visible

---

## 🔧 Troubleshooting

### "Could not connect to database"

**Fix**: Double-check the DATABASE_URL in secrets
- Go to app settings → Secrets
- Verify the connection string is correct
- Make sure password is URL-encoded: `%2B` for `+` and `%24` for `$`

### "No module named 'streamlit'"

**Fix**: This shouldn't happen, but if it does:
- Check that `requirements.txt` is in the root directory
- Redeploy the app

### "Refresh button does nothing"

**Fix**: 
- Check the logs (click "Manage app" → "Logs")
- Verify breakingpoint.gg is accessible
- Try refreshing the page and clicking again

### App is slow

**Normal!** First refresh takes 1-2 minutes. Subsequent refreshes are faster.

---

## 📋 Post-Deployment Checklist

After your app is live:

- [ ] Click "🔄 Refresh Data" to load initial data
- [ ] Verify matches appear in the list
- [ ] Click on a match to see details
- [ ] Check all navigation tabs work
- [ ] Test on mobile device
- [ ] Bookmark your app URL
- [ ] Share with friends! 🎉

---

## 🌐 Your App URLs

Once deployed, you'll have:

**Main Dashboard**: `https://[your-app-name].streamlit.app`

Want to deploy the Hardpoint-only dashboard too?
1. Repeat Step 3-5
2. Change "Main file path" to: `hardpoint_dashboard.py`
3. Use the SAME secrets (DATABASE_URL)

---

## 💡 Pro Tips

### Custom Domain (Optional)
Streamlit Cloud free tier doesn't support custom domains, but you can:
- Use the auto-generated URL
- Upgrade to Streamlit Cloud Team ($200/month) for custom domains
- Or use Cloudflare Workers to proxy the URL

### Monitoring
- Check app analytics in Streamlit Cloud dashboard
- Monitor Supabase usage: https://amxinvsaknlxlgjqthho.supabase.co
- Free tier limits: 500MB storage, 2GB bandwidth/month

### Regular Updates
- Click refresh button after major tournaments
- Check for new matches weekly
- Monitor database size monthly

---

## 📞 Need Help?

**Common Issues:**
1. **Database connection**: Verify DATABASE_URL in secrets
2. **Deployment fails**: Check logs for error messages
3. **App crashes**: May need to reduce data size or upgrade plan

**Resources:**
- Streamlit Docs: https://docs.streamlit.io/
- Supabase Docs: https://supabase.com/docs
- Your local docs: `README.md`, `docs/QUICKSTART.md`

---

## 🎯 Quick Copy-Paste Reference

**Your GitHub Repo**:
```
https://github.com/justintwoo/CDL_dashboard
```

**Main File Path**:
```
app.py
```

**Streamlit Secrets (copy-paste this)**:
```toml
DATABASE_URL = "postgresql://postgres:%2BGq3qjKNWf3V%24q2@db.amxinvsaknlxlgjqthho.supabase.co:5432/postgres"
```

**Hardpoint Dashboard File Path** (optional second app):
```
hardpoint_dashboard.py
```

---

## ✨ What's Next?

After deployment:

1. **Test Everything**: Click through all features
2. **Gather Feedback**: Share with CDL community
3. **Monitor Usage**: Check analytics and database usage
4. **Iterate**: Add features based on user requests

---

**Ready?** Go to https://share.streamlit.io/ and follow the steps above!

*Created: January 1, 2026*  
*Repository: github.com/justintwoo/CDL_dashboard*
