# UI Component Quick Reference

## 🎨 Color Gradients

### Primary (Brand)
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```
**Use for**: Headers, active tabs, primary buttons

### Secondary (Accent)
```css
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
```
**Use for**: Banners, CTAs, highlights

### Success
```css
background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
```
**Use for**: Success messages, hit picks, positive stats

### Danger
```css
background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
```
**Use for**: Error messages, chalked picks, warnings

### Info
```css
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
```
**Use for**: Info messages, help text, tooltips

---

## 📐 Spacing Scale

```
Extra Small: 8px
Small: 12px
Medium: 16px
Large: 24px
Extra Large: 32px
Huge: 48px
```

---

## 🎯 Component Classes

### Cards
```html
<div class="card-container">
  <!-- Content -->
</div>
```
**Features**: White background, shadow, rounded corners, hover lift

### Title Sections
```html
<div class="title-section">
  <h1>Title</h1>
</div>
```
**Features**: Gradient background, white text, shadow, rounded

### Metric Cards
```html
<div class="metric-card">
  <!-- Metrics -->
</div>
```
**Features**: White background, shadow, hover effect, padding

### Pick Status
```html
<span class="pick-hit">HIT ✅</span>
<span class="pick-chalked">CHALKED ❌</span>
<span class="pick-pending">PENDING ⏳</span>
```
**Features**: Gradient backgrounds, borders, hover scale

---

## 🖼️ Player Components

### Image Container
```html
<div class="player-image-container">
  <img src="..." alt="Player">
</div>
```
**Features**: Gradient tint, padding, hover zoom

### Detail Header
```html
<div class="player-detail-header">
  <div class="player-detail-image">
    <img src="..." alt="Player">
  </div>
  <div class="player-detail-info">
    <div class="player-detail-name">Player Name</div>
    <div class="player-detail-meta">
      <div class="player-detail-stat">
        <div class="player-detail-stat-label">Label</div>
        <div class="player-detail-stat-value">Value</div>
      </div>
    </div>
  </div>
</div>
```

---

## 🎬 Animation Classes

### Fade In
```css
animation: fadeIn 0.5s ease-in;
```

### Pulse
```css
animation: pulse 1.5s ease-in-out infinite;
```

### Spin (Loading)
```css
animation: spin 1s linear infinite;
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
  /* Mobile styles */
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
  /* Tablet styles */
}

/* Desktop */
@media (min-width: 1025px) {
  /* Desktop styles */
}
```

---

## 🎨 Shadow System

### Default Card Shadow
```css
box-shadow: 0 10px 30px rgba(0,0,0,0.1);
```

### Hover Shadow
```css
box-shadow: 0 15px 40px rgba(0,0,0,0.15);
```

### Enhanced Shadow
```css
box-shadow: 0 8px 20px rgba(0,0,0,0.3);
```

### Glow Effect
```css
box-shadow: 0 4px 15px rgba(102,126,234,0.4);
```

---

## 🔤 Typography Scale

### Headers
- **H1**: 42px, bold
- **H2**: 36px, bold
- **H3**: 28px, bold
- **H4**: 24px, semibold

### Body
- **Large**: 18px
- **Regular**: 16px
- **Small**: 14px
- **Tiny**: 12px

### Weights
- **Regular**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

---

## 🎯 Common Patterns

### Button Hover Effect
```css
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
hover: {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}
```

### Card Hover Effect
```css
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
hover: {
  transform: translateY(-4px);
  box-shadow: 0 15px 40px rgba(0,0,0,0.15);
}
```

### Scale Hover
```css
transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
hover: {
  transform: scale(1.05);
}
```

---

## 🎪 Upcoming Banner

```html
<div class="upcoming-banner">
  <div class="upcoming-banner-title">
    🔥 Upcoming Matches
  </div>
  <div class="upcoming-banner-content">
    <div class="upcoming-match-item">
      Team A <span class="upcoming-vs">VS</span> Team B
    </div>
  </div>
</div>
```

---

## 🔄 Loading Animation

```html
<div class="loading-container">
  <div class="spinner"></div>
  <div class="loading-text">Loading Title</div>
  <div class="loading-subtext">Loading subtitle...</div>
</div>
```

---

## 📊 Table Enhancement

Tables automatically get enhanced styling:
- Gradient headers
- Alternating row colors
- Hover effects
- Rounded corners
- Shadows

No additional classes needed!

---

## 🎨 CSS Variables Reference

```css
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
--success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
--danger-gradient: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
--info-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
--card-bg: #ffffff;
--card-shadow: 0 10px 30px rgba(0,0,0,0.1);
--hover-shadow: 0 15px 40px rgba(0,0,0,0.15);
--border-radius: 12px;
--transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

---

## 🚀 Quick Tips

1. **Always use CSS variables** for consistency
2. **Add hover states** to interactive elements
3. **Use transitions** for smooth animations
4. **Test on mobile** before finalizing
5. **Keep shadows consistent** across similar components
6. **Use gradients sparingly** for emphasis
7. **Maintain spacing** using the scale
8. **Follow the color system** for states (success/danger/info)

---

## 🎯 Common Mistakes to Avoid

❌ **Don't**: Mix different shadow styles
✅ **Do**: Use predefined shadow variables

❌ **Don't**: Create custom gradients without reason
✅ **Do**: Use the 5 core gradients

❌ **Don't**: Skip hover states
✅ **Do**: Add transitions to all interactive elements

❌ **Don't**: Use inline styles
✅ **Do**: Use predefined CSS classes

❌ **Don't**: Ignore mobile responsiveness
✅ **Do**: Test on all screen sizes

---

## 📚 Additional Resources

- **Full Guide**: `docs/UI_ENHANCEMENT_GUIDE.md`
- **Changelog**: `docs/CHANGELOG.md`
- **Main CSS**: Lines 90-520 in `app.py`

---

**Last Updated**: January 2, 2026
**Version**: 2.3
