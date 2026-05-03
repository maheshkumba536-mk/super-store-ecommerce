# Affiliate Marketing Platform - Task Tracker

## Phase 1: Backend (Models & Logic)
- [x] Update models.py — Category, enhanced Product with expiry, Wishlist
- [x] Update admin.py — WordPress-like admin with expiry, click tracking
- [x] Create management command — cleanup_expired
- [x] Update settings.py — Add humanize
- [x] Update views.py — New views (search, category, track_click, wishlist, pinterest)
- [x] Update urls.py — New URL patterns

## Phase 2: Frontend (Templates & CSS)
- [x] Update base.html — OG tags, Pinterest SDK, mobile nav, search, disclosure
- [x] Update home.html — Shopping app UI with search, categories, discount badges
- [x] Update product_detail.html — Enhanced detail with sharing, Pinterest
- [x] Create wishlist.html — Replace cart page
- [x] Create pinterest_feed.html — Pinterest-optimized feed
- [x] Update login.html & register.html — Match new design

## Phase 3: Styling & Interactivity
- [x] Complete CSS overhaul — Shopping app aesthetic
- [x] Enhanced JavaScript — Search, wishlist toggle, Pinterest share, dark mode

## Phase 4: Database & Testing
- [ ] Run migrations
- [ ] Create superuser (to access admin)
- [ ] Start server
- [ ] Visual verification in browser

---

## 🚀 Final Commands
Run these commands in your terminal to get started:

### 1. Set up Database
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Admin Account
```powershell
python manage.py createsuperuser
```
*(Follow prompts to set username and password)*

### 3. Start the Server
```powershell
python manage.py runserver
```

### 4. Cleanup Expired Products (Run occasionally)
```powershell
python manage.py cleanup_expired
```
