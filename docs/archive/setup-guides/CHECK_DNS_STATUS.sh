#!/bin/bash

# DNS Status Checker for lexicraft.xyz
# Run this script to check DNS propagation status

echo "🔍 Checking DNS Status for lexicraft.xyz"
echo "========================================"
echo ""

# Check A record for root domain
echo "1. Root Domain (lexicraft.xyz) A Record:"
A_RECORD=$(dig A lexicraft.xyz +short)
if [ -z "$A_RECORD" ]; then
    echo "   ❌ No A record found (DNS not configured or not propagated)"
else
    echo "   ✅ A record found: $A_RECORD"
    # Check if it's a Vercel IP (common Vercel IPs)
    if [[ "$A_RECORD" =~ ^76\.76\. ]] || [[ "$A_RECORD" =~ ^76\.76\.21\. ]]; then
        echo "   ✅ Looks like a Vercel IP address"
    fi
fi
echo ""

# Check CNAME for www
echo "2. WWW Subdomain (www.lexicraft.xyz) CNAME Record:"
CNAME_RECORD=$(dig CNAME www.lexicraft.xyz +short)
if [ -z "$CNAME_RECORD" ]; then
    echo "   ❌ No CNAME record found"
else
    echo "   ✅ CNAME record found: $CNAME_RECORD"
    if [[ "$CNAME_RECORD" == *"vercel"* ]]; then
        echo "   ✅ Points to Vercel"
    fi
fi
echo ""

# Check HTTPS accessibility
echo "3. HTTPS Accessibility:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://lexicraft.xyz 2>/dev/null)
if [ "$HTTP_STATUS" == "200" ] || [ "$HTTP_STATUS" == "301" ] || [ "$HTTP_STATUS" == "302" ]; then
    echo "   ✅ Website is accessible (HTTP $HTTP_STATUS)"
else
    echo "   ⚠️  Website returned HTTP $HTTP_STATUS (may still be propagating)"
fi
echo ""

# Check SSL certificate
echo "4. SSL Certificate:"
SSL_CHECK=$(echo | openssl s_client -connect lexicraft.xyz:443 -servername lexicraft.xyz 2>/dev/null | grep -c "Verify return code: 0")
if [ "$SSL_CHECK" -gt 0 ]; then
    echo "   ✅ SSL certificate is valid"
else
    echo "   ⚠️  SSL certificate check failed (may still be provisioning)"
fi
echo ""

echo "========================================"
echo "💡 Next Steps:"
echo "   1. Check Vercel Dashboard → Settings → Domains"
echo "   2. Verify 'Proxy Detected' warning is gone"
echo "   3. Status should show 'Valid Configuration'"
echo ""
echo "🔗 Useful Links:"
echo "   - DNS Checker: https://dnschecker.org/#A/lexicraft.xyz"
echo "   - Vercel Dashboard: https://vercel.com/dashboard"


