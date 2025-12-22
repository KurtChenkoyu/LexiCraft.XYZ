#!/bin/bash
# Helper script to set Railway environment variables
# Run this AFTER: railway login && railway init (or railway link)

echo "Setting Railway environment variables..."

railway variables set DATABASE_URL="postgresql://postgres.cwgexbjyfcqndeyhravb:ZEt%25t7Yx%5Dbkgn@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
railway variables set NEO4J_URI="neo4j+s://fcc4b033.databases.neo4j.io"
railway variables set NEO4J_USER="neo4j"
railway variables set NEO4J_PASSWORD="DDIbeIEDdi4wS4wB4H23TaSiLOWJPT7MnVLf69ENN-0"

echo "✅ Environment variables set!"
echo ""
echo "Next step: railway up"

