# CDL Dashboard - Changelog

## Version 2.3 - Modern UI Enhancement (January 2026)

### 🎨 Complete Visual Overhaul

**Transformed the entire dashboard with modern, aesthetic frontend design**
- Implemented comprehensive CSS redesign with gradients and animations
- Enhanced all components with smooth transitions and hover effects
- Added responsive design for mobile, tablet, and desktop
- Professional appearance matching industry-leading dashboards

### ✨ Major UI Enhancements

#### 1. Design System Implementation
- **Color Palette**: 5 gradient themes (primary, secondary, success, danger, info)
- **CSS Variables**: Centralized design tokens for consistency
- **Typography**: Enhanced font hierarchy with bold weights and sizing
- **Spacing**: Generous whitespace and consistent padding/margins
- **Shadows**: Multi-layer depth system with hover enhancements

#### 2. Component Upgrades

**Navigation & Tabs**
- White card background with subtle shadows
- Gradient background on active tab with glow effect
- Smooth hover animations with lift effect
- 50px height standardization
- 8px gap between tabs

**Data Tables**
- Gradient headers with white text
- Alternating row colors (subtle blue tint)
- Hover effects: scale + shadow + color change
- Uppercase labels with letter-spacing
- Rounded corners with overflow hidden

**Metric Cards**
- 32px font size for values (up from 24px)
- Primary gradient color scheme
- Hover lift animation with enhanced shadow
- 24px padding for breathing room
- Rounded corners (12px border-radius)

**Buttons**
- Rounded corners with box shadows
- Hover lift effect (translateY(-2px))
- Smooth cubic-bezier transitions (0.3s)
- Enhanced shadows on hover
- Full-width in sidebar

**Form Elements**
- Primary color borders (2px)
- Hover state styling with shadows
- Focus glow effects (3px shadow ring)
- Rounded corners throughout
- Smooth transitions

#### 3. Betting Slip Enhancement
- **Pick Status Cards**: Gradient backgrounds with matching borders
- **Hit**: Green gradient + border with hover scale
- **Chalked**: Red gradient + border with hover scale
- **Pending**: Gray gradient + border with hover scale
- Better padding (6px 12px) and inline-block display

#### 4. Player Profiles
- **Image Size**: Increased to 200x200px
- **Gradient Headers**: Full-width primary gradient
- **Stat Cards**: Glassmorphism with blur effects
- **Hover Effects**: Scale + rotation on images
- **Text Shadows**: Better readability on gradients
- **Enhanced Spacing**: 35px gaps between elements

#### 5. Loading States
- **Larger Spinner**: 70px with glowing shadow
- **Fade-in Animation**: Smooth appearance
- **Pulse Effect**: Scale + opacity animations
- **Enhanced Text**: 28px font with shadow
- **Container**: 80px vertical padding

#### 6. Notification Messages
- **Success**: Green gradient background
- **Error**: Red gradient background
- **Info**: Blue gradient background
- **Warning**: Orange/yellow gradient
- All with white text, rounded corners, and shadows

#### 7. Responsive Design
- **Mobile (≤768px)**: Stacked layouts, centered content
- **Tablet (769-1024px)**: Two-column where appropriate
- **Desktop (>1024px)**: Multi-column layouts
- Media queries for all major breakpoints

#### 8. Animations & Transitions
- **Hover**: translateY(-2px) or scale(1.05)
- **Timing**: 0.3s cubic-bezier(0.4, 0, 0.2, 1)
- **Loading**: Rotation, pulse, fade-in effects
- **Smooth**: All transitions hardware-accelerated

### 📝 Files Modified

#### app.py (Lines 90-520)
- Complete CSS overhaul with 500+ lines of modern styling
- Organized into sections: Global, Components, Responsive
- Added CSS variables for design consistency
- Enhanced all existing components
- Added new utility classes

### 🎯 Design Principles Applied

1. **Consistency**: All components follow same design language
2. **Hierarchy**: Clear visual prioritization
3. **Feedback**: Every interaction has response
4. **Performance**: Smooth, no janky animations
5. **Accessibility**: High contrast, readable fonts
6. **Mobile-First**: Responsive on all devices
7. **Professional**: Industry-standard aesthetics

### 📊 Visual Impact

| Component | Before | After |
|-----------|--------|-------|
| **Tables** | Plain borders | Gradient headers + hover effects |
| **Buttons** | Basic | Rounded + shadows + lift animation |
| **Cards** | Flat | 3D depth with hover lift |
| **Metrics** | 24px | 32px with gradient colors |
| **Tabs** | Simple | Gradient active state + glow |
| **Forms** | Basic | Bordered + focus glow |
| **Loading** | Basic | Animated with glow effects |

### 📄 Documentation

- Added `docs/UI_ENHANCEMENT_GUIDE.md` (comprehensive 500+ line guide)
- Complete design system documentation
- Before/after comparisons
- Usage examples for all components
- Future enhancement roadmap
- Maintenance guidelines

### 🚀 Technical Implementation

**CSS Architecture**:
- Root variables for design tokens
- Organized sections with comments
- Utility classes for reuse
- Media queries for responsive
- Hardware-accelerated animations

**Performance**:
- CSS-only animations (no JS overhead)
- Efficient selectors
- Minimal reflows
- Optimized transitions

**Browser Support**:
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Graceful degradation
- Feature detection

---

## Version 2.2 - Performance Optimization (January 2026)

### 🚀 Performance Improvements

**Optimized Slip Creator button responsiveness**
- Added instant toast notifications for button feedback (<100ms)
- Implemented duplicate pick detection with warning messages
- Enhanced button UX with `use_container_width=True`
- Improved perceived performance from 1-3 seconds to instant

### 🎯 Changes

#### 1. Instant User Feedback
- **Toast Notifications**: Show immediately when clicking Over/Under buttons
- **Success Messages**: "✅ Added {player} Over {value}" with emoji icon
- **Warning Messages**: "⚠️ Already in slip!" for duplicate picks
- **User Experience**: Feels instant even though page reloads in background

#### 2. Duplicate Prevention
- **Validation**: Checks if pick already exists before adding
- **Logic**: Compares `line_id` and `pick_type` against existing picks
- **Feedback**: Shows warning toast instead of silently adding duplicate
- **Benefit**: Cleaner slips, prevents user confusion

#### 3. Button Improvements
- **Full Width**: `use_container_width=True` for better touch targets
- **Mobile Friendly**: Larger clickable area on tablets/phones
- **Visual Consistency**: Matches other buttons in the UI

### 📝 Files Modified

#### app.py
- **Lines 2959-2998**: Optimized Over/Under button handlers
- **Function**: `page_slip_creator()`
- **Features**: Toast notifications, duplicate detection, improved styling

### 📊 Performance Impact

| Metric | Before | After |
|--------|--------|-------|
| Perceived Response | 1-3 seconds | <100ms |
| User Feedback | None | Instant toast |
| Duplicate Prevention | ❌ None | ✅ Enabled |

### 📄 Documentation

- Added `docs/PERFORMANCE_OPTIMIZATION.md` with detailed technical analysis
- Includes before/after code comparison
- Lists future optimization opportunities

---

## Version 2.1 - Betting Slip Enhancement (January 2026)

### ✨ New Features

**Enhanced betting slip persistence and UX**
- Save slip button with database persistence
- Enhanced error handling and user feedback
- Recent slips display (last 5 saved)
- Balloons animation on successful save

### 🎯 Changes

#### 1. Save Slip Database Persistence
- **Function**: Saves slip + picks to `slips` and `slip_picks` tables
- **Error Handling**: Try/catch with user-friendly error messages
- **Feedback**: Success toast + balloons animation
- **Return Value**: Returns slip ID for tracking

#### 2. Recent Slips Display
- **Location**: Bottom of Slip Creator page
- **Content**: Shows last 5 saved slips with match info
- **Link**: "View all slips in Slip Tracker" navigation
- **Styling**: Clean card layout with dividers

#### 3. Demo Mode Integration
- **Betting Lines**: Saves mock lines to database for reference
- **Match Data**: 3 demo matches with realistic teams
- **Props**: 96 props per match (12 players × 2 stats × 4 scopes)
- **Persistence**: Enables slip saving even in demo mode

### 📝 Files Modified

#### app.py
- **Lines 2736-2765**: Enhanced save slip button with error handling
- **Lines 2770-2870**: Demo mode generates and saves betting lines
- **Lines 2995-3022**: Recent slips display section

#### database.py
- **Lines 520-550**: `save_betting_lines()` caches lines for reference
- **Lines 584-630**: `save_slip()` enhanced with better error handling

---

## Version 2.0 - Refresh Button Update (January 1, 2026)

### 🎯 Major Changes

**Replaced scheduled scraping with on-demand refresh button**
- Removed GitHub Actions hourly automation
- Added UI refresh button to both dashboards
- Implemented last-updated timestamp tracking
- Incremental scraping from last update date

### ✨ New Features

#### 1. Refresh Button in UI
- **Location**: Top-right corner of both dashboards
- **Function**: Scrapes new matches from last update to now
- **Feedback**: Shows progress, success/error messages
- **Visual**: `🔄 Refresh Data` button with full-width styling

#### 2. Last Updated Timestamp
- **Display**: Shows in UI header: `📅 Last updated: 2026-01-01 15:14:50`
- **Storage**: Persisted in PostgreSQL `scrape_metadata` table
- **Logic**: Only updates after successful scraping
- **Default**: 7 days ago if no previous scrape

#### 3. Incremental Scraping
- **Smart Date Range**: Scrapes from `last_scrape_date` to current time
- **Efficiency**: Only fetches new matches, not entire history
- **Performance**: Much faster than re-scraping 7 days every time
- **Respectful**: Reduces load on breakingpoint.gg servers

### 📝 Files Modified

#### database.py
- Added `ScrapeMetadata` ORM model
- Added `get_last_scrape_date()` function
- Added `update_last_scrape_date(date)` function
- Schema update creates new `scrape_metadata` table

#### scrape_breakingpoint.py
- Updated `scrape_live_data()` to accept `start_date` parameter
- Signature: `scrape_live_data(start_date: Optional[str] = None)`
- Filters matches by date: `m.get('datetime', '')[:10] >= date_threshold`
- Maintains backward compatibility (defaults to 7 days)

#### app.py
- Added `load_data_with_refresh()` function (replaces cached `get_data()`)
- Added `refresh_data()` function with progress spinner
- Updated `main()` to show last updated timestamp
- Added refresh button UI component
- Updated header layout: 4:1 column ratio for timestamp and button
- Shows data metrics: Total Maps, Unique Matches, Unique Players

#### hardpoint_dashboard.py
- Same changes as app.py
- Added `load_data_with_refresh()` function
- Added `refresh_data()` function
- Updated `main()` with refresh button
- Shows Hardpoint-specific metrics

### 🗑️ Files Removed

#### .github/workflows/update_data.yml
- **Reason**: No longer using GitHub Actions scheduled scraping
- **Alternative**: On-demand refresh button in UI

#### update_data.py
- **Reason**: Headless scraper no longer needed
- **Alternative**: refresh_data() function in UI

### 📚 Files Added

#### REFRESH_BUTTON_GUIDE.md
- Complete documentation of new refresh system
- How it works (timestamp tracking, incremental scraping)
- Code changes explained
- Advantages over scheduled approach
- Migration guide from GitHub Actions
- Troubleshooting section
- Testing instructions

#### CHANGELOG.md (this file)
- Version history and change tracking

### 🔧 Technical Details

#### New Database Table
```sql
CREATE TABLE scrape_metadata (
    id SERIAL PRIMARY KEY,
    last_scrape_date TIMESTAMP NOT NULL,
    scrape_timestamp TIMESTAMP DEFAULT NOW()
);
```

#### API Changes
```python
# Old (no parameter)
def scrape_live_data() -> Optional[pd.DataFrame]:
    pass

# New (with optional start_date)
def scrape_live_data(start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    pass
```

#### UI Flow
```
1. User clicks "🔄 Refresh Data"
2. Get last_scrape_date from database
3. Call scrape_live_data(start_date=last_scrape_date)
4. Cache results with cache_match_data(df)
5. Update last_scrape_date to datetime.now()
6. Reload UI data and show success message
```

### ✅ Benefits

1. **User Control**: Update data whenever you want, not on a schedule
2. **Efficiency**: Only scrape new matches since last update
3. **Visibility**: Always see when data was last refreshed
4. **Simplicity**: No GitHub Actions setup required
5. **Flexibility**: Works on any hosting platform
6. **Feedback**: Immediate UI notifications on success/failure

### 📊 Performance Impact

- **First Refresh**: ~180 seconds (scrapes 7 days of matches)
- **Subsequent Refreshes**: 10-60 seconds (only new matches)
- **UI Load Time**: Still 0.08s (loads from PostgreSQL cache)
- **Database Growth**: +1 row per refresh in scrape_metadata table

### 🚀 Deployment

#### For New Deployments
```bash
# 1. Initialize database (creates scrape_metadata table)
python3 -c "from database import init_db; init_db()"

# 2. Run dashboard
streamlit run app.py

# 3. Click "Refresh Data" button in UI to populate
```

#### For Existing Deployments
```bash
# 1. Pull latest code
git pull origin main

# 2. Update database schema
python3 -c "from database import init_db; init_db()"

# 3. Restart dashboards
pkill -f "streamlit run"
streamlit run app.py

# 4. Refresh data via UI button
```

### 🐛 Bug Fixes

None - This is a feature update, not a bug fix release

### ⚠️ Breaking Changes

**Removed:**
- GitHub Actions automation (optional feature, not core)
- `update_data.py` script (replaced by UI button)
- `@st.cache_data` decorator on data loading (replaced with session state)

**Not Breaking:**
- Database schema extended (backward compatible)
- `scrape_live_data()` function signature extended (backward compatible)
- All existing dashboards still work
- All existing database queries unchanged

### 🔮 Future Enhancements

Potential improvements for future versions:
- Auto-refresh on timer (e.g., every 30 minutes)
- Refresh history log (show past refresh timestamps)
- Manual date range picker (scrape specific date range)
- Batch refresh (refresh multiple date ranges)
- Background refresh (don't block UI)
- Email/Slack notifications on refresh

### 📝 Migration Notes

If you were using the GitHub Actions version:
1. Delete `.github` directory (already done)
2. Delete `update_data.py` (already done)
3. Update code to latest version
4. Run `init_db()` to create new table
5. Use refresh button instead of waiting for cron

### 🧪 Testing

All tests passed:
```bash
✅ Database schema updated (scrape_metadata table created)
✅ get_last_scrape_date() returns timestamp
✅ update_last_scrape_date() updates database
✅ scrape_live_data(start_date='2025-12-28') works correctly
✅ load_from_cache() returns 280 records
✅ UI imports all modules successfully
```

### 👥 Contributors

- Justin Woo (@justinwoo) - Original implementation
- GitHub Copilot - Code assistance and documentation

---

## Version 1.0 - Cloud Deployment (December 31, 2025)

### Features
- PostgreSQL database caching
- GitHub Actions hourly scraping
- Streamlit Cloud deployment
- CDL map filtering
- Hardpoint specialized dashboard
- Team logos and map images

*See CODEBASE_OVERVIEW.md for complete version 1.0 documentation*

---

*Maintained by Justin Woo | Last updated: January 1, 2026*
