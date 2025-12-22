# Sound Effects Download & Setup Guide

## Quick Start

1. **Download** Kenney Interface Sounds pack
2. **Run** the conversion script
3. **Verify** files are in place
4. **Upload** to Supabase (when ready)

## Step 1: Download Kenney Interface Sounds

### Option A: GitHub (Recommended)
1. Visit: https://github.com/Calinou/kenney-interface-sounds
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file to a temporary location (e.g., `~/Downloads/kenney-interface-sounds`)

### Option B: Itch.io
1. Visit: https://kenney.itch.io/kenney-game-assets
2. Download the "All-in-1" bundle (includes interface sounds)
3. Extract and navigate to the interface sounds folder

## Step 2: Convert Files

### Prerequisites
Install ffmpeg:
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html

### Run Conversion Script

```bash
cd landing-page
./scripts/convert-sfx.sh <kenney_extracted_path> ./public/audio/fx
```

**Example:**
```bash
./scripts/convert-sfx.sh ~/Downloads/kenney-interface-sounds ./public/audio/fx
```

The script will:
- Convert all OGG files to MP3
- Rename files to match convention (`correct_001.mp3`, etc.)
- Place them in `landing-page/public/audio/fx/`

### Manual Conversion (if script doesn't work)

If the Kenney pack has different file names, you'll need to manually map them:

```bash
# Example: Convert confirmation sounds to correct sounds
ffmpeg -i confirmation_001.ogg -codec:a libmp3lame -qscale:a 2 correct_001.mp3
ffmpeg -i confirmation_002.ogg -codec:a libmp3lame -qscale:a 2 correct_002.mp3
# ... repeat for all 30 files
```

**Sound Mapping:**
- **Correct**: `confirmation_001.ogg` → `confirmation_005.ogg`
- **Wrong**: `error_001.ogg` → `error_005.ogg`
- **Click**: `click_001.ogg` → `click_005.ogg` (keep similar!)
- **Levelup**: `confirmation_006.ogg` → `confirmation_010.ogg` (make distinct!)
- **Celebrate**: `confirmation_011.ogg` → `confirmation_015.ogg` (make distinct!)
- **Unlock**: `confirmation_016.ogg` → `confirmation_020.ogg`

## Step 3: Verify Files

Check that all 30 files exist:

```bash
ls -la landing-page/public/audio/fx/ | wc -l
# Should show 30 files (plus . and .. = 32 total)
```

Expected files:
- `correct_001.mp3` through `correct_005.mp3` (5 files)
- `wrong_001.mp3` through `wrong_005.mp3` (5 files)
- `click_001.mp3` through `click_005.mp3` (5 files)
- `levelup_001.mp3` through `levelup_005.mp3` (5 files)
- `celebrate_001.mp3` through `celebrate_005.mp3` (5 files)
- `unlock_001.mp3` through `unlock_005.mp3` (5 files)

## Step 4: Test Locally

1. Start the development server:
   ```bash
   cd landing-page
   npm run dev
   ```

2. Navigate to a page that uses sound effects (e.g., `/learner/verification`)
3. Trigger sound effects and verify:
   - Different variants play randomly
   - Sounds are clear and appropriate
   - No console errors

## Step 5: Upload to Supabase (When Ready)

Once all files are verified locally, upload to Supabase Storage:

```bash
cd landing-page
npm run upload-audio
```

Or manually:
```bash
npx tsx scripts/upload-audio-to-supabase.ts
```

## Troubleshooting

### Script fails: "ffmpeg not found"
- Install ffmpeg (see Prerequisites above)
- Verify installation: `ffmpeg -version`

### Script fails: "Missing input file"
- Check that the Kenney pack was extracted correctly
- Verify file names match expected pattern
- Some Kenney packs may have different naming - adjust script or convert manually

### Files don't play in browser
- Check browser console for 404 errors
- Verify files are in `landing-page/public/audio/fx/`
- Check file permissions (should be readable)
- Verify MP3 files are valid (try playing one manually)

### Wrong sounds playing
- Verify file naming matches convention exactly: `{effect}_001.mp3`
- Check that variant numbers are zero-padded: `001` not `1`
- Clear browser cache and reload

## Notes

- **Click sounds**: Keep variants similar (subtle pitch shifts) to avoid feeling "loose"
- **Celebrate/Levelup sounds**: Make variants distinct (different instruments) for excitement
- All files should be MP3 format, <100KB each
- The audio service will fall back to generated sounds if files are missing

