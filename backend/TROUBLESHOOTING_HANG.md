# Troubleshooting: Batch 2 Enrichment Hang

## Issue
The Batch 2 enrichment process appears to have hung or stopped making progress.

## What to Check

### 1. Google Cloud Console - API Quotas & Limits

**Check API Usage:**
1. Go to: https://console.cloud.google.com/apis/dashboard
2. Select your project
3. Click on "Generative Language API"
4. Go to "Quotas" tab

**Key Limits to Check:**
- **Requests per minute (RPM)**: Free tier = 60 RPM
- **Requests per day (RPD)**: Free tier = 1,500 RPD
- **Tokens per minute (TPM)**: Free tier = 32,000 TPM
- **Tokens per day (TPD)**: Free tier = 1,000,000 TPD

**What to Look For:**
- If you've hit the daily quota (1,500 requests/day), you'll need to wait until it resets (usually midnight PST)
- If you're hitting rate limits, you'll see 429 errors
- Check the "Usage" graph to see if requests are being made

### 2. Google Cloud Console - API Credentials

**Check API Key Status:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Find your API key
3. Check:
   - Is it enabled? ✅
   - Are there any restrictions? (IP, referrer, API restrictions)
   - Has it been revoked?

### 3. Check for Rate Limit Errors

**Common Error Codes:**
- **429**: Rate limit exceeded (too many requests per minute)
- **403**: Permission denied (API key issue or quota exceeded)
- **400**: Bad request (malformed request)
- **500**: Server error (temporary Google issue)

### 4. Check Process Status

```bash
# Check if process is running
ps aux | grep agent_batched | grep -v grep

# Check process CPU/memory usage
top -pid $(pgrep -f "agent_batched")

# Check if process is stuck (no CPU usage = likely waiting)
```

### 5. Check Logs

The `agent_batched.py` script prints errors to stdout. If running in background:
- Check the terminal where you started it
- Look for error messages like:
  - "Gemini API Error (batch): ..."
  - "429" errors
  - "Quota exceeded" messages

### 6. Test API Manually

```bash
cd backend
source venv/bin/activate
python3 -c "
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.0-flash')
try:
    response = model.generate_content('Test')
    print('✅ API working')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## Common Causes

### 1. Daily Quota Exceeded
- **Symptom**: Process runs but no progress, no errors
- **Solution**: Wait for quota reset (usually midnight PST) or upgrade to paid tier

### 2. Rate Limit (429 Errors)
- **Symptom**: Process hangs, occasional 429 errors in logs
- **Solution**: The code should retry with exponential backoff, but may need longer waits
- **Current code**: Only sleeps 2 seconds between batches (may not be enough)

### 3. API Key Issues
- **Symptom**: 403 errors
- **Solution**: Check API key in Google Cloud Console, regenerate if needed

### 4. Network Issues
- **Symptom**: Timeouts, connection errors
- **Solution**: Check internet connection, firewall settings

## Fixes

### If Hitting Rate Limits:
The `agent_batched.py` currently only sleeps 2 seconds between batches. You may need to:
1. Increase sleep time (line 237 in agent_batched.py)
2. Add retry logic with exponential backoff (like main_factory.py has)
3. Reduce batch size (from 10 to 5 words per batch)

### If Daily Quota Exceeded:
1. Wait for quota reset (check in Google Cloud Console)
2. Upgrade to paid tier for higher limits
3. Resume processing after quota resets

### If Process is Completely Hung:
1. Kill the process: `pkill -f "agent_batched"`
2. Check logs for errors
3. Restart with smaller batch size or longer delays

## Quick Diagnostic Commands

```bash
# Check if process exists
ps aux | grep agent_batched | grep -v grep

# Check API quota status (requires gcloud CLI)
gcloud services list --enabled | grep generativelanguage

# Test API directly
cd backend && source venv/bin/activate
python3 -c "import google.generativeai as genai; import os; from dotenv import load_dotenv; load_dotenv(); genai.configure(api_key=os.getenv('GOOGLE_API_KEY')); print('✅ API configured')"
```

## Next Steps

1. **Check Google Cloud Console** for quota/usage
2. **Test API manually** to see if it's working
3. **Check process logs** for error messages
4. **Restart with better error handling** if needed

