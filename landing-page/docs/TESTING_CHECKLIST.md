# Caching Implementation Testing Checklist

This checklist verifies that the "Last War" caching approach is working correctly.

## Prerequisites

- Backend server running on `http://localhost:8002`
- Frontend server running on `http://localhost:3000`
- Browser DevTools open (F12)
- Application tab open in DevTools (for IndexedDB inspection)

## Test 1: Verify Single Cache System

### 1.1 Check IndexedDB Usage

1. **Open DevTools → Application → IndexedDB**
2. **Login to the app**
3. **Verify data is stored in IndexedDB:**
   - Look for `lexicraft-db` database
   - Check `cache` object store
   - Verify you see entries for:
     - `user_profile`
     - `children`
     - `starter_pack_ids` (if you visit /mine page)

### 1.2 Check localStorage Usage

1. **Open DevTools → Application → Local Storage**
2. **Verify NO user data in localStorage:**
   - Should NOT see: `lexicraft_user_profile`
   - Should NOT see: `lexicraft_user_children`
   - ✅ Should see: `lexicraft_selected_child` (tiny UI preference - allowed)
   - ✅ Should see: `lexicraft_role_preference` (tiny UI preference - allowed)

### 1.3 Verify Role Detection

1. **Login as a parent user**
2. **Check console logs:**
   - Should see: `⚡ Loaded profile from IndexedDB cache`
   - Should see: `⚡ Loaded children from IndexedDB cache`
3. **Verify parent layout appears:**
   - Should see sidebar on desktop
   - Should see hamburger menu on mobile
   - Should NOT see bottom navigation (learner layout)

## Test 2: Data Persistence

### 2.1 Login and Cache

1. **Login to the app**
2. **Wait for data to load** (check console for cache logs)
3. **Verify data appears in UI:**
   - Profile information visible
   - Children list visible (if parent)
   - Dashboard content loads

### 2.2 Refresh Test

1. **Refresh the page (F5)**
2. **Check console logs:**
   - Should see: `⚡ Loaded profile from IndexedDB cache` (immediately)
   - Should see: `⚡ Loaded children from IndexedDB cache` (immediately)
3. **Verify UI loads instantly:**
   - No loading spinner for content
   - Data appears immediately
   - Background sync happens silently

### 2.3 Logout and Clear

1. **Click logout**
2. **Check IndexedDB:**
   - Should be cleared (no `user_profile` or `children` entries)
3. **Check localStorage:**
   - `lexicraft_selected_child` should be removed
   - `lexicraft_role_preference` may remain (allowed)

### 2.4 Login Again

1. **Login again with same account**
2. **Verify fresh data loads:**
   - Data should come from API first (no cache)
   - Then cached to IndexedDB
   - Subsequent refreshes should use cache

## Test 3: Offline Behavior

### 3.1 Cache Data First

1. **Login and navigate around the app**
2. **Verify data is cached in IndexedDB**
3. **Note what data is visible** (profile, children, etc.)

### 3.2 Go Offline

1. **Open DevTools → Network tab**
2. **Enable "Offline" mode** (checkbox in Network tab)
3. **Refresh the page**

### 3.3 Verify Offline Functionality

1. **Check console:**
   - Should see: `⚡ Loaded profile from IndexedDB cache`
   - Should see: `⚡ Loaded children from IndexedDB cache`
   - Should NOT see API errors
2. **Verify UI works:**
   - Profile information still visible
   - Children list still visible
   - Navigation works
   - No error messages about network failures

### 3.4 Go Online Again

1. **Disable "Offline" mode**
2. **Verify background sync:**
   - Check console for sync logs
   - Data should update silently when API responds

## Test 4: Visitor Behavior (Privacy)

### 4.1 Visit Landing Page

1. **Open app in incognito/private window**
2. **Navigate to landing page** (`/` or `/zh-TW`)
3. **Open DevTools → Application → IndexedDB**

### 4.2 Verify No User Data Loaded

1. **Check IndexedDB:**
   - Should NOT see `user_profile` entry
   - Should NOT see `children` entry
   - (May see other cached data like `starter_pack_ids` if you visited /mine - that's OK)
2. **Check console:**
   - Should NOT see: `⚡ Loaded profile from IndexedDB cache`
   - Should NOT see: `⚡ Loaded children from IndexedDB cache`
   - Should NOT see any errors
3. **Verify AppTopNav works:**
   - Navigation bar should render
   - Login/signup buttons should work
   - No errors in console

### 4.3 Verify No Privacy Leak

1. **If you previously logged in on this browser:**
   - Old cached data should NOT appear on landing page
   - UserDataProvider should NOT be loaded
   - No user data should be accessible

## Test 5: Edge Cases

### 5.1 Empty Cache

1. **Clear IndexedDB:**
   - DevTools → Application → IndexedDB → `lexicraft-db` → Delete database
2. **Login to app**
3. **Verify:**
   - Data loads from API
   - Data is cached to IndexedDB
   - Subsequent refreshes use cache

### 5.2 Corrupted Cache

1. **Manually corrupt IndexedDB data:**
   - DevTools → Application → IndexedDB → Edit an entry to invalid JSON
2. **Refresh page**
3. **Verify:**
   - App handles error gracefully
   - Falls back to API fetch
   - Rebuilds cache

### 5.3 Multiple Tabs

1. **Open app in two tabs**
2. **Login in first tab**
3. **Verify second tab:**
   - Should detect auth change
   - Should load data from IndexedDB
   - Should sync properly

## Expected Results Summary

✅ **All tests should pass:**
- IndexedDB is the single cache for user data
- localStorage only contains tiny UI preferences
- Data loads instantly from cache
- Offline mode works
- Visitors don't see cached user data
- Role detection works with IndexedDB-only profile
- Data persists across sessions

## Reporting Issues

If any test fails:
1. Note which test failed
2. Check console for errors
3. Check IndexedDB state in DevTools
4. Check localStorage state
5. Report with screenshots/logs

