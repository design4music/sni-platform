# SNI Frontend Testing Checklist

## Prerequisites

- Database populated with sample data:
  - At least 1 systemic centroid
  - At least 3 geographic centroids with iso_codes
  - At least 1 CTM with events_digest and summary_text
  - At least 5 titles linked to CTMs

## Manual Testing Checklist

### 1. Home Page (/)

- [ ] Logo displays correctly
- [ ] Navigation header visible
- [ ] Introduction section renders
- [ ] AI disclaimer box shows
- [ ] Map loads (Leaflet with countries)
- [ ] Map countries with centroids are highlighted
- [ ] Clicking a highlighted country navigates to centroid page
- [ ] System centroids section displays cards
- [ ] Each centroid card is clickable
- [ ] Region cards display (6 regions)
- [ ] Clicking region card navigates to region page
- [ ] "How it works" section visible

### 2. Global Page (/global)

- [ ] Page title shows "Global Centroids"
- [ ] Systemic centroids section displays
- [ ] Global non-state actors section displays (if any)
- [ ] All centroid cards are clickable
- [ ] Class badges show correctly

### 3. Region Page (/region/:region_key)

- [ ] Page title shows region name
- [ ] Centroids in region display
- [ ] No CTM content visible (directory only)
- [ ] Empty state shows if region has no centroids
- [ ] Invalid region key shows 404

### 4. Centroid Page (/c/:centroid_key)

- [ ] Page title shows centroid label
- [ ] Track cards display
- [ ] Each track card shows latest month
- [ ] Each track card shows title count
- [ ] Sidebar shows centroid type
- [ ] Sidebar shows region link (if applicable)
- [ ] Sidebar shows other centroids
- [ ] Invalid centroid key shows 404
- [ ] Empty state shows if no tracks exist

### 5. Track Page (/c/:centroid_key/t/:track_key)

**Dashboard Mode Elements:**
- [ ] Navigation header visible
- [ ] Dark theme applied

**Reading Mode Content:**
- [ ] Light theme for content area
- [ ] Breadcrumb link to centroid page works
- [ ] Track title displays correctly
- [ ] Month and article count show
- [ ] Summary text renders (if available)
- [ ] Events digest displays (if available)
- [ ] Each event shows date and summary
- [ ] Source articles section displays
- [ ] Article links open in new tab
- [ ] Publisher and date show for each article
- [ ] AI disclaimer at bottom

**Sidebar Navigation:**
- [ ] Month selector shows (if multiple months)
- [ ] Current month is highlighted
- [ ] Clicking different month updates content
- [ ] Other tracks section shows
- [ ] Clicking other track navigates correctly
- [ ] "Same track elsewhere" section shows
- [ ] Cross-centroid links work

**Edge Cases:**
- [ ] Invalid track key shows 404
- [ ] Invalid month parameter shows 404
- [ ] Missing query parameter defaults to latest month

### 6. Navigation Flow

**Home to CTM (2-click rule):**
- [ ] Click centroid card -> Centroid page (1 click)
- [ ] Click track card -> Track page with CTM (2 clicks)
- [ ] Total: User sees CTM content in 2 clicks

**Map Navigation:**
- [ ] Click country on map -> Centroid page (1 click)
- [ ] Click track -> Track page (2 clicks total)

**Cross-Navigation:**
- [ ] From track page, switch to different track
- [ ] From track page, navigate to same track on different centroid
- [ ] Navigate through month archive

### 7. Database Connectivity

- [ ] `/api/health` returns status: ok
- [ ] `/api/health` shows database timestamp
- [ ] Error state if database disconnected

### 8. Error Handling

- [ ] 404 page shows for invalid routes
- [ ] Error boundary catches runtime errors
- [ ] Database errors display gracefully
- [ ] Loading states show during navigation

### 9. Typography & Design

**Dashboard Mode:**
- [ ] Dark background (#0a0e1a)
- [ ] Light text readable
- [ ] Borders subtle but visible
- [ ] Card hover states work

**Reading Mode:**
- [ ] Light background (#ffffff)
- [ ] Dark text readable
- [ ] Proper line height for long text
- [ ] Strong typography hierarchy

### 10. Responsive Design

- [ ] Desktop (1920px): Full layout with sidebar
- [ ] Tablet (768px): Grid adjusts to 2 columns
- [ ] Mobile (375px): Single column, sidebar stacks

### 11. Performance

- [ ] Initial page load < 3 seconds
- [ ] Navigation transitions smooth
- [ ] Map renders without lag
- [ ] No console errors in browser
- [ ] Database queries execute quickly

## Automated Testing (Future)

### Unit Tests
- [ ] Database query functions
- [ ] Utility functions (formatMonth, etc.)
- [ ] Type safety checks

### Integration Tests
- [ ] Page rendering with mock data
- [ ] Navigation flows
- [ ] Error boundaries

### E2E Tests
- [ ] Complete user journeys
- [ ] Cross-browser testing
- [ ] Database integration

## Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Accessibility

- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators visible

## Known Limitations

- Map requires JavaScript enabled
- No offline support
- Real-time updates require page refresh
- No mobile app (web only)
