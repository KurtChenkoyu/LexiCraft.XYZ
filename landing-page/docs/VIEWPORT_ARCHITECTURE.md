# Viewport Architecture

**The "Game Frame"** - How LexiCraft achieves "Last War" feel

---

## The Problem

Traditional web apps use the **document flow model**:
- Content determines page height
- Body scrolls vertically
- Navigation reloads/re-renders on page change
- Feels like reading a document

**Result:** Slow, janky, web-like

---

## The Solution

Games use the **fixed viewport model**:
- Viewport is locked to screen size
- HUD floats above content
- Content scrolls in designated areas
- Navigation is instant (state changes, not page loads)

**Result:** Fast, smooth, game-like

---

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│           BEFORE (Web Page)                  │
├─────────────────────────────────────────────┤
│  <body> (scrolls vertically)                │
│  ┌─────────────────────────────────────┐   │
│  │  <nav> (reloads on page change)     │   │
│  ├─────────────────────────────────────┤   │
│  │  <main> (content grows infinitely)  │   │
│  │                                      │   │
│  │  ...more content...                 │   │
│  │                                      │   │
│  │  ...keeps going...                  │   │
│  │                                      │   │ ← Body scrolls
│  ├─────────────────────────────────────┤   │
│  │  <footer>                           │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

Problems:
❌ Page height unbounded (grows with content)
❌ Body scrollbar (browser chrome shows/hides)
❌ Nav remounts on navigation (flicker)
❌ Pull-to-refresh triggers (iOS)
❌ Text selection possible (doesn't feel like game)
```

```
┌─────────────────────────────────────────────┐
│           AFTER (Game Viewport)              │
├─────────────────────────────────────────────┤
│  <body> (fixed, no scroll)                  │
│  ┌─────────────────────────────────────┐   │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │   │
│  │ ┃ TopBar (z-40, absolute)        ┃ │   │ ← HUD Layer
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │   │   (Never scrolls)
│  │ ┌────────────────────────────────┐ │   │
│  │ │ Content (z-0, scrollable)      │ │   │
│  │ │                                │ │   │
│  │ │ ...content scrolls here...     │◄──┼───┐ Scrolls
│  │ │                                │ │   │ │ independently
│  │ │ ...independently...            │ │   │ │
│  │ │                                │ │   │ │
│  │ └────────────────────────────────┘ │   │ │
│  │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │   │
│  │ ┃ BottomNav (z-40, absolute)     ┃ │   │ ← HUD Layer
│  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │   │   (Never scrolls)
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
         ↑
         └─ h-[100dvh] w-screen overflow-hidden fixed

Benefits:
✅ Viewport locked to 100dvh (exact screen fit)
✅ No body scrollbar (game feel)
✅ HUD persists during navigation (no flicker)
✅ Pull-to-refresh disabled
✅ Text selection disabled (game control)
✅ Proper Z-layering (HUD above content)
```

---

## Z-Index Hierarchy

```
 z-50 ┃ Toast Notifications (ephemeral feedback)
━━━━━━┫
 z-40 ┃ HUD (TopBar + BottomNav) ← ALWAYS VISIBLE
━━━━━━┫
 z-30 ┃ Modals (confirm dialogs, full-screen overlays)
━━━━━━┫
 z-20 ┃ Overlays (dimmed backgrounds)
━━━━━━┫
 z-10 ┃ Full-screen Activities (Mine, Workshop)
━━━━━━┫
 z-0  ┃ World/Map (base content layer)
━━━━━━┛
```

**Rule:** Lower layers never cover higher layers.

---

## Implementation

### 1. Lock the Viewport (`globals.css`)

```css
html, body {
  height: 100dvh;           /* Lock to viewport */
  width: 100vw;
  overflow: hidden;          /* Kill scroll */
  position: fixed;           /* Prevent any movement */
  overscroll-behavior: none; /* Disable pull-to-refresh */
}
```

### 2. Create Game Container

```tsx
<div className="game-container flex flex-col">
  {/* Fixed viewport: h-[100dvh] w-screen overflow-hidden */}
</div>
```

### 3. Layer the HUD

```tsx
<div className="game-container">
  {/* Top HUD */}
  <div className="z-hud absolute top-0 left-0 right-0">
    <TopBar />
  </div>

  {/* Scrollable Content */}
  <main className="z-world flex-1 overflow-y-auto">
    {children}
  </main>

  {/* Bottom HUD */}
  <div className="z-hud absolute bottom-0 left-0 right-0">
    <BottomNav />
  </div>
</div>
```

---

## CSS Rules Enforced

### Kill Web Defaults

```css
/* No text selection */
* {
  -webkit-user-select: none;
  user-select: none;
}

/* No tap highlights */
* {
  -webkit-tap-highlight-color: transparent;
}

/* No iOS zoom */
* {
  touch-action: pan-x pan-y;
}
```

### Allow Selection in Specific Areas

```css
/* Inputs, textareas, and marked elements */
input, textarea, .text-selectable {
  -webkit-user-select: text;
  user-select: text;
}
```

### Enable Smooth Scrolling in Content

```css
.scrollable {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
```

---

## Route-Specific Behavior

### Learner Routes (`/learner/*`)
- ✅ Game Frame activated
- ✅ LearnerTopBar (custom HUD)
- ✅ Fixed viewport
- ✅ Z-layering enforced

### Parent Routes (`/parent/*`)
- ✅ AppTopNav (standard nav)
- ✅ Sidebar layout
- ⚠️ Still uses normal flow (can be migrated later)

### Marketing Routes (`/`, `/privacy`)
- ✅ AppTopNav
- ✅ Normal scrolling allowed
- ⚠️ Not game-optimized (intentional, for SEO)

---

## Safe Areas (Notched Phones)

The HUD respects device safe areas:

```tsx
<div className="pt-safe">
  {/* Content pushed below notch */}
</div>

<div className="pb-safe">
  {/* Content pushed above home bar */}
</div>
```

These utilities use `env(safe-area-inset-*)` to adapt to device cutouts.

---

## How to Add New Screens

### Full-Screen Activity (e.g., Quiz)

```tsx
function QuizScreen() {
  return (
    <div className="z-content h-full flex flex-col">
      <header>Quiz Header</header>
      <div className="flex-1 overflow-y-auto scrollable">
        {/* Questions scroll here */}
      </div>
      <footer>Quiz Controls</footer>
    </div>
  )
}
```

### Modal Dialog

```tsx
function ConfirmDialog() {
  return (
    <div className="z-modal fixed inset-0">
      {/* Dim background */}
      <div className="absolute inset-0 bg-black/50" />
      
      {/* Dialog content */}
      <div className="relative z-10 flex items-center justify-center h-full">
        <div className="bg-white rounded-lg p-6">
          <h2>Confirm Action</h2>
          <button>OK</button>
        </div>
      </div>
    </div>
  )
}
```

### Toast Notification

```tsx
function Toast() {
  return (
    <div className="z-toast fixed top-4 right-4">
      <div className="bg-green-500 text-white px-4 py-2 rounded-lg">
        Achievement unlocked!
      </div>
    </div>
  )
}
```

---

## Testing Checklist

### Visual
- [ ] No body scrollbar visible
- [ ] HUD stays fixed during scroll
- [ ] Content scrolls independently
- [ ] No "bounce" effect on iOS

### Functional
- [ ] Navigation doesn't remount HUD
- [ ] Pull-to-refresh disabled
- [ ] Text selection disabled (except inputs)
- [ ] Safe areas respected on notched devices

### Cross-Browser
- [ ] Safari (iOS)
- [ ] Chrome (Android)
- [ ] Desktop browsers

---

## Troubleshooting

### "Content is cut off at the bottom"
- Check if you're using `pb-safe` for bottom padding
- Verify HUD height matches padding offset

### "HUD scrolls with content"
- Ensure HUD uses `absolute` positioning
- Check that container uses `relative` positioning

### "Can't scroll content"
- Verify content area has `overflow-y-auto` and `scrollable` class
- Check that `flex-1` is applied to content area

### "Navigation flickers"
- HUD should be in layout, not page component
- Check that Z-index is properly applied

---

## References

- `.cursorrules` - "UI/UX & Game Feel Standards"
- `PHASE2_COMPLETE_SUMMARY.md` - Implementation guide
- `app/globals.css` - CSS rules
- `app/[locale]/(app)/learner/layout.tsx` - Layout implementation

