#!/bin/bash

echo "🧪 TESTING META API PERFORMANCE IMPROVEMENTS"
echo "============================================="
echo ""

# Test 1: Simple Meta API Test (Most Important)
echo "1️⃣ Testing Simple Meta API Endpoint:"
echo "   Before: 901 campaigns, 70k+ tokens, timeout"
echo "   Expected: ~16 campaigns, ~1.6 seconds"
echo ""
echo "   Running test..."
time curl -s -X POST https://thriveads-platform-production.up.railway.app/test-meta-api-simple | jq '.campaigns_found, .note'
echo ""

# Test 2: Campaigns 2025 Data
echo "2️⃣ Testing Campaigns 2025 Data Endpoint:"
echo "   Expected: Only campaigns with spend > 0"
echo ""
echo "   Running test..."
time curl -s "https://thriveads-platform-production.up.railway.app/api/v1/campaigns/2025-data" | jq '.total_campaigns, .message'
echo ""

# Test 3: Ads 2025 Data  
echo "3️⃣ Testing Ads 2025 Data Endpoint:"
echo "   Expected: Only ads with spend > 0"
echo ""
echo "   Running test..."
time curl -s "https://thriveads-platform-production.up.railway.app/api/v1/ads/2025-data" | jq '.total_ads, .message'
echo ""

# Test 4: Top Performing Campaigns
echo "4️⃣ Testing Top Performing Campaigns:"
echo "   Expected: Fast response with spend-filtered campaigns"
echo ""
echo "   Running test..."
time curl -s "https://thriveads-platform-production.up.railway.app/api/v1/campaigns/top-performing?limit=5" | jq '.campaigns | length'
echo ""

# Test 5: Top Performing Ads
echo "5️⃣ Testing Top Performing Ads:"
echo "   Expected: Fast response with spend-filtered ads"
echo ""
echo "   Running test..."
time curl -s "https://thriveads-platform-production.up.railway.app/api/v1/ads/top-performing?limit=5" | jq '.ads | length'
echo ""

echo "✅ PERFORMANCE TESTING COMPLETE!"
echo ""
echo "📊 EXPECTED RESULTS:"
echo "   • All responses should be under 5 seconds"
echo "   • Campaigns/ads counts should be much lower (only with spend > 0)"
echo "   • No timeouts or hanging requests"
echo "   • Response payloads should be manageable size"
