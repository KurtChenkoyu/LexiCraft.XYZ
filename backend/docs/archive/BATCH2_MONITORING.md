# Batch 2 Monitoring Guide

## Quick Status Check

Run a single status check:

```bash
cd backend
./monitor_batch2.sh
```

Or:

```bash
cd backend
source venv/bin/activate
python -m scripts.monitor_batch2 --once
```

## Continuous Monitoring

Watch progress with automatic updates every 60 seconds:

```bash
cd backend
./monitor_batch2.sh --watch
```

Or with custom interval (e.g., every 30 seconds):

```bash
cd backend
source venv/bin/activate
python -m scripts.monitor_batch2 --interval 30
```

## What It Shows

- **Total Words in Range**: All words with ranks 1001-2000
- **Enriched**: How many words are fully enriched (all senses enriched)
- **Pending**: Words still needing enrichment
- **Enriched Senses**: Total number of enriched sense nodes
- **Progress Bar**: Visual progress indicator
- **Overall Status**: Total enrichment across all 3,500 words
- **Time Estimate**: Estimated time to complete remaining batches

## Current Status

As of last check:
- **152/680 words enriched** (22.4%) in ranks 1001-2000
- **~63 batches remaining** (~2.6 minutes estimated)
- **Overall: 1,231/3,500 words** (35.2%) enriched database-wide

## Background Process

The enrichment process is running in the background. You can:

1. **Check if it's still running:**
   ```bash
   ps aux | grep agent_batched | grep -v grep
   ```

2. **Monitor progress:**
   ```bash
   ./monitor_batch2.sh --watch
   ```

3. **Check logs** (if any errors occur, they'll appear in the terminal where the process was started)

## Completion

When Batch 2 is complete:
- All 680 words in ranks 1001-2000 will be enriched
- The monitor will show "🎉 Batch 2 Complete!"
- You can then proceed to Batch 3 (ranks 2001-3000)

