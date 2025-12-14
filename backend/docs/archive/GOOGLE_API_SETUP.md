# Google API (Gemini) Setup Guide

This guide walks you through setting up Google's Generative AI (Gemini) API for content enrichment in the LexiCraft project.

## What You'll Need

- A Google account
- 5-10 minutes
- Your API key (we'll get this together)

## Step 1: Get Your Google API Key

### Option A: Google AI Studio (Recommended - Easiest)

1. **Go to Google AI Studio**
   - Visit: https://aistudio.google.com/
   - Sign in with your Google account

2. **Get Your API Key**
   - Click "Get API Key" in the left sidebar (or top right)
   - If prompted, create a new Google Cloud project (or select an existing one)
   - Click "Create API Key"
   - **Copy the API key immediately** - you won't be able to see it again!

3. **Enable the API** (if needed)
   - Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   - Make sure "Generative Language API" is enabled
   - If not, click "Enable"

### Option B: Google Cloud Console (More Control)

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select a Project**
   - Click the project dropdown at the top
   - Click "New Project" or select an existing one
   - Give it a name (e.g., "lexicraft")

3. **Enable the Generative Language API**
   - Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   - Click "Enable"

4. **Create API Key**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "API Key"
   - Copy the API key
   - (Optional) Click "Restrict Key" to limit usage to specific APIs

## Step 2: Set Up Environment Variables

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Create a `.env` file** (if it doesn't exist)
   ```bash
   touch .env
   ```

3. **Add your API key to `.env`**
   ```bash
   # Google Generative AI (Gemini) API
   GOOGLE_API_KEY=your_api_key_here
   
   # Neo4j (if you haven't set this up yet)
   # NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   # NEO4J_USER=neo4j
   # NEO4J_PASSWORD=your_password_here
   
   # PostgreSQL/Supabase (if you haven't set this up yet)
   # DATABASE_URL=postgresql://user:password@host:port/database
   ```

4. **Replace `your_api_key_here`** with the actual API key you copied

5. **Important**: Never commit `.env` to git! It should already be in `.gitignore`

## Step 3: Verify Installation

1. **Make sure the package is installed**
   ```bash
   cd backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install google-generativeai
   ```

2. **Test the connection** (optional)
   ```bash
   python3 -c "import google.generativeai as genai; import os; genai.configure(api_key=os.getenv('GOOGLE_API_KEY')); print('✅ API key configured successfully!')"
   ```

## Step 4: Test the Agent

You can test the agent with mock data first (no API key needed):

```bash
cd backend
source venv/bin/activate
python3 -m src.agent --word bank --mock
```

Then test with the real API:

```bash
python3 -m src.agent --word bank
```

## Pricing & Limits

### Free Tier
- **60 requests per minute** (RPM)
- **1,500 requests per day** (RPD)
- **32,000 tokens per minute** (TPM)
- **1 million tokens per day** (TPD)

### Paid Tier
- Starts at $0.000125 per 1K characters (input)
- $0.0005 per 1K characters (output)
- Higher rate limits

**For MVP**: The free tier should be sufficient for development and initial testing.

## Troubleshooting

### Error: "API key not valid"
- Make sure you copied the entire API key (no spaces)
- Check that the Generative Language API is enabled
- Verify the API key in `.env` file

### Error: "Quota exceeded"
- You've hit the rate limit (60 requests/minute)
- Wait a minute and try again
- Consider upgrading to paid tier for higher limits

### Error: "Module not found: google.generativeai"
- Install the package: `pip install google-generativeai`
- Make sure you're in the virtual environment

### Warning: "GOOGLE_API_KEY not found"
- Check that `.env` file exists in the `backend` directory
- Verify the variable name is exactly `GOOGLE_API_KEY`
- Make sure `python-dotenv` is installed (it's in requirements.txt)

## Security Best Practices

1. **Never commit `.env` to version control**
   - It should be in `.gitignore`
   - Use `.env.example` for documentation

2. **Restrict API Key** (Optional but recommended)
   - In Google Cloud Console, go to API credentials
   - Click on your API key
   - Under "API restrictions", select "Restrict key"
   - Choose "Generative Language API"

3. **Set Application Restrictions** (Optional)
   - Under "Application restrictions"
   - Choose "IP addresses" or "HTTP referrers" for web apps

4. **Rotate Keys Regularly**
   - If a key is compromised, delete it and create a new one

## Next Steps

Once your API key is set up, you can:

1. **Run the enrichment agent**
   ```bash
   python3 -m src.agent --limit 10
   ```

2. **Enrich specific words**
   ```bash
   python3 -m src.agent --word bank
   ```

3. **Use mock mode for testing** (no API calls)
   ```bash
   python3 -m src.agent --word bank --mock
   ```

## Additional Resources

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Pricing Information](https://ai.google.dev/pricing)
- [API Reference](https://ai.google.dev/api)

---

**Need Help?** Check the main project README or create an issue in the repository.

