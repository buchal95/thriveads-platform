#!/usr/bin/env node

/**
 * Local Meta API Performance Test
 * 
 * This script tests Meta API performance directly from your local machine
 * to compare with Railway performance and identify bottlenecks.
 * 
 * Usage:
 *   node test-meta-api-local.js
 * 
 * Make sure to set your Meta credentials in environment variables:
 *   export META_ACCESS_TOKEN="your_token_here"
 *   export META_AD_ACCOUNT_ID="513010266454814"
 */

const https = require('https');
const { performance } = require('perf_hooks');

// Configuration
const ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';
const AD_ACCOUNT_ID = process.env.META_AD_ACCOUNT_ID || '513010266454814';
const BASE_URL = 'graph.facebook.com';
const API_VERSION = 'v23.0';

if (!ACCESS_TOKEN) {
    console.error('❌ Error: META_ACCESS_TOKEN environment variable is required');
    console.log('Set it with: export META_ACCESS_TOKEN="your_token_here"');
    process.exit(1);
}

// Helper function to make API requests
function makeRequest(path) {
    return new Promise((resolve, reject) => {
        const url = `/${API_VERSION}/${path}&access_token=${ACCESS_TOKEN}`;
        
        const options = {
            hostname: BASE_URL,
            path: url,
            method: 'GET',
            headers: {
                'User-Agent': 'ThriveAds-Local-Test/1.0'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve(jsonData);
                } catch (error) {
                    reject(new Error(`JSON Parse Error: ${error.message}`));
                }
            });
        });

        req.on('error', (error) => {
            reject(error);
        });

        req.setTimeout(30000, () => {
            req.destroy();
            reject(new Error('Request timeout (30s)'));
        });

        req.end();
    });
}

// Helper function to format time
function formatTime(ms) {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
}

// Helper function to get date range
function getDateRange(days = 30) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    return {
        since: startDate.toISOString().split('T')[0],
        until: endDate.toISOString().split('T')[0]
    };
}

// Test 1: Simple campaign count
async function testSimpleCampaigns() {
    console.log('\n📊 Test 1: Simple Campaign Count');
    console.log('='.repeat(50));
    
    const startTime = performance.now();
    
    try {
        const path = `act_${AD_ACCOUNT_ID}/campaigns?fields=id,name,status&limit=100`;
        const data = await makeRequest(path);
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        if (data.error) {
            console.log(`❌ Error: ${data.error.message} (Code: ${data.error.code})`);
            return false;
        }
        
        console.log(`✅ Success! Found ${data.data.length} campaigns`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        console.log(`📈 Rate: ${(data.data.length / (duration / 1000)).toFixed(1)} campaigns/second`);
        
        // Show sample campaigns
        console.log('\nSample campaigns:');
        data.data.slice(0, 5).forEach(campaign => {
            console.log(`  - ${campaign.name} (${campaign.status})`);
        });
        
        return true;
    } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        console.log(`❌ Network Error: ${error.message}`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        return false;
    }
}

// Test 2: Campaigns with insights (traditional approach)
async function testCampaignsWithInsights() {
    console.log('\n🎯 Test 2: Campaigns with Insights (Traditional)');
    console.log('='.repeat(50));
    
    const startTime = performance.now();
    const { since, until } = getDateRange(30);
    
    try {
        const path = `act_${AD_ACCOUNT_ID}/campaigns?fields=id,name,status,insights{spend,impressions,clicks}&time_range={'since':'${since}','until':'${until}'}&limit=50`;
        const data = await makeRequest(path);
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        if (data.error) {
            console.log(`❌ Error: ${data.error.message} (Code: ${data.error.code})`);
            return false;
        }
        
        // Filter campaigns with spend
        const campaignsWithSpend = data.data.filter(campaign => 
            campaign.insights && 
            campaign.insights.data.length > 0 && 
            parseFloat(campaign.insights.data[0].spend || 0) > 0
        );
        
        console.log(`✅ Success! Found ${data.data.length} total campaigns, ${campaignsWithSpend.length} with spend`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        console.log(`📈 Rate: ${(data.data.length / (duration / 1000)).toFixed(1)} campaigns/second`);
        
        // Show campaigns with spend
        console.log('\nCampaigns with spend:');
        campaignsWithSpend.slice(0, 5).forEach(campaign => {
            const insight = campaign.insights.data[0];
            console.log(`  - ${campaign.name}: $${insight.spend} spend, ${insight.impressions} impressions`);
        });
        
        return true;
    } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        console.log(`❌ Network Error: ${error.message}`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        return false;
    }
}

// Test 3: Direct insights API (optimized approach)
async function testInsightsDirectly() {
    console.log('\n⚡ Test 3: Direct Insights API (Optimized)');
    console.log('='.repeat(50));
    
    const startTime = performance.now();
    const { since, until } = getDateRange(30);
    
    try {
        const path = `act_${AD_ACCOUNT_ID}/insights?fields=campaign_id,campaign_name,spend,impressions,clicks&time_range={'since':'${since}','until':'${until}'}&level=campaign&limit=100`;
        const data = await makeRequest(path);
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        if (data.error) {
            console.log(`❌ Error: ${data.error.message} (Code: ${data.error.code})`);
            return false;
        }
        
        // Filter insights with spend
        const insightsWithSpend = data.data.filter(insight => parseFloat(insight.spend || 0) > 0);
        
        console.log(`✅ Success! Found ${data.data.length} total insights, ${insightsWithSpend.length} with spend`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        console.log(`📈 Rate: ${(data.data.length / (duration / 1000)).toFixed(1)} insights/second`);
        
        // Show insights with spend
        console.log('\nInsights with spend:');
        insightsWithSpend.slice(0, 5).forEach(insight => {
            console.log(`  - ${insight.campaign_name}: $${insight.spend} spend, ${insight.impressions} impressions`);
        });
        
        return true;
    } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        console.log(`❌ Network Error: ${error.message}`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        return false;
    }
}

// Test 4: Account info (baseline test)
async function testAccountInfo() {
    console.log('\n🔍 Test 4: Account Info (Baseline)');
    console.log('='.repeat(50));
    
    const startTime = performance.now();
    
    try {
        const path = `act_${AD_ACCOUNT_ID}?fields=id,name,account_status,currency,timezone_name`;
        const data = await makeRequest(path);
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        if (data.error) {
            console.log(`❌ Error: ${data.error.message} (Code: ${data.error.code})`);
            return false;
        }
        
        console.log(`✅ Success! Account info retrieved`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        console.log(`📊 Account: ${data.name} (${data.currency})`);
        console.log(`🌍 Timezone: ${data.timezone_name}`);
        console.log(`📈 Status: ${data.account_status}`);
        
        return true;
    } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        console.log(`❌ Network Error: ${error.message}`);
        console.log(`⏱️  Time: ${formatTime(duration)}`);
        return false;
    }
}

// Main test runner
async function runAllTests() {
    console.log('🚀 Meta API Local Performance Test');
    console.log('='.repeat(50));
    console.log(`📍 Testing from: Local machine`);
    console.log(`🎯 Ad Account: ${AD_ACCOUNT_ID}`);
    console.log(`🔑 Token: ${ACCESS_TOKEN.substring(0, 10)}...`);
    
    const results = [];
    
    // Run all tests
    results.push(await testAccountInfo());
    results.push(await testSimpleCampaigns());
    results.push(await testCampaignsWithInsights());
    results.push(await testInsightsDirectly());
    
    // Summary
    console.log('\n📊 Test Summary');
    console.log('='.repeat(50));
    const passed = results.filter(r => r).length;
    const total = results.length;
    
    console.log(`✅ Passed: ${passed}/${total} tests`);
    
    if (passed === total) {
        console.log('🎉 All tests passed! Meta API is working well locally.');
        console.log('💡 If Railway is slow, the issue is likely infrastructure-related.');
    } else {
        console.log('⚠️  Some tests failed. Check your Meta API credentials and permissions.');
    }
    
    console.log('\n💡 Next steps:');
    console.log('  1. Compare these times with Railway performance');
    console.log('  2. If local is much faster, consider Railway resource limits');
    console.log('  3. Consider using Railway Pro plan for better performance');
    console.log('  4. Implement caching to reduce API calls');
}

// Run the tests
if (require.main === module) {
    runAllTests().catch(error => {
        console.error('💥 Unexpected error:', error);
        process.exit(1);
    });
}

module.exports = {
    testSimpleCampaigns,
    testCampaignsWithInsights,
    testInsightsDirectly,
    testAccountInfo
};
