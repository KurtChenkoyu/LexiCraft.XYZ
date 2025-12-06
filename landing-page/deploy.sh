#!/bin/bash

# Deployment script for lexicraft.xyz Landing Page

echo "🚀 Deploying lexicraft.xyz Landing Page to Vercel"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "🔐 You need to log in to Vercel first."
    echo "   Run: vercel login"
    echo ""
    echo "   This will open your browser to authenticate."
    echo "   After logging in, run this script again."
    exit 1
fi

echo "✅ Build check..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix errors before deploying."
    exit 1
fi

echo ""
echo "📦 Deploying to Vercel..."
echo ""

# Deploy to production
vercel --prod --yes

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Add environment variables in Vercel dashboard:"
    echo "      - NEXT_PUBLIC_EMAIL_SERVICE"
    echo "      - CONVERTKIT_API_KEY (or MAILCHIMP_API_KEY)"
    echo "      - CONVERTKIT_FORM_ID (or MAILCHIMP_LIST_ID)"
    echo "      - NEXT_PUBLIC_POSTHOG_KEY (or NEXT_PUBLIC_MIXPANEL_TOKEN)"
    echo ""
    echo "   2. Test your live site"
    echo "   3. Share with 5+ friends for feedback"
    echo ""
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi

