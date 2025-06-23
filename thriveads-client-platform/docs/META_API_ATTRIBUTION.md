# Meta API Attribution Windows Implementation

## Overview

This document explains the correct implementation of Meta Marketing API attribution windows for purchase conversions, specifically focusing on **7-day click** and **default** attribution windows.

## Attribution Windows Explained

### Default Attribution (`default`)
- **Definition**: 7-day click + 1-day view attribution
- **What it includes**: 
  - Conversions that happen within 7 days of clicking an ad
  - Conversions that happen within 1 day of viewing an ad (without clicking)
- **Use case**: Meta's standard attribution model, includes view-through conversions
- **API parameter**: `default` or `["7d_click","1d_view"]`

### 7-Day Click Attribution (`7d_click`)
- **Definition**: 7-day click attribution only
- **What it includes**: 
  - Only conversions that happen within 7 days of clicking an ad
  - Excludes view-through conversions
- **Use case**: More conservative attribution, closer to Google Ads attribution
- **API parameter**: `7d_click`

## API Implementation

### Correct API Request

```javascript
const queryParams = new URLSearchParams({
  access_token: accessToken,
  level: 'campaign', // or 'account', 'adset', 'ad'
  time_range: JSON.stringify({
    since: '2024-11-18',
    until: '2024-11-24'
  }),
  fields: [
    'spend',
    'impressions',
    'clicks',
    'actions',        // Contains conversion counts
    'action_values'   // Contains conversion values (purchase amounts)
  ].join(','),
  // CRITICAL: Include both attribution windows
  action_attribution_windows: ['default', '7d_click'].join(','),
  limit: '100'
});
```

### API Response Structure

```json
{
  "data": [
    {
      "spend": "1000.00",
      "impressions": "50000",
      "clicks": "500",
      "actions": [
        {
          "action_type": "purchase",
          "value": "25",      // Total purchases (all attribution)
          "default": "25",    // Default attribution (7d_click + 1d_view)
          "7d_click": "18"    // 7-day click attribution only
        }
      ],
      "action_values": [
        {
          "action_type": "purchase",
          "value": "2500.00",    // Total purchase value
          "default": "2500.00",  // Default attribution value
          "7d_click": "1800.00"  // 7-day click attribution value
        }
      ]
    }
  ]
}
```

## Data Processing

### Extracting Purchase Conversions

```typescript
private extractPurchaseConversions(
  actions?: Array<any>, 
  actionValues?: Array<any>
): PurchaseConversions {
  const purchaseAction = actions?.find(action => action.action_type === 'purchase');
  const purchaseValue = actionValues?.find(action => action.action_type === 'purchase');

  return {
    default: {
      count: purchaseAction?.default ? parseInt(purchaseAction.default) : 0,
      value: purchaseValue?.default ? parseFloat(purchaseValue.default) : 0
    },
    '7d_click': {
      count: purchaseAction?.['7d_click'] ? parseInt(purchaseAction['7d_click']) : 0,
      value: purchaseValue?.['7d_click'] ? parseFloat(purchaseValue['7d_click']) : 0
    }
  };
}
```

### Calculating ROAS for Both Attributions

```typescript
const purchases = this.extractPurchaseConversions(data.actions, data.action_values);
const spend = parseFloat(data.spend || '0');

// Calculate ROAS for both attribution windows
const roasDefault = spend > 0 ? purchases.default.value / spend : 0;
const roas7dClick = spend > 0 ? purchases['7d_click'].value / spend : 0;
```

## Why Both Attribution Windows Matter

### Business Impact

1. **Default Attribution (7d_click + 1d_view)**:
   - Shows full impact of Meta ads including brand awareness
   - Includes view-through conversions (people who saw ad but didn't click)
   - Higher conversion numbers and ROAS
   - Better for understanding total campaign impact

2. **7-Day Click Attribution**:
   - More conservative, direct-response focused
   - Easier to compare with Google Ads (similar attribution)
   - Lower conversion numbers and ROAS
   - Better for performance optimization

### Example Comparison

```
Campaign: Black Friday Sale
Spend: €3,245

Default Attribution (7d_click + 1d_view):
- Purchases: 187 conversions
- Value: €15,576
- ROAS: 4.8x

7-Day Click Attribution:
- Purchases: 142 conversions  
- Value: €11,836
- ROAS: 3.6x

Difference:
- View-through conversions: 45 (24% of total)
- View-through value: €3,740 (24% of total)
```

## Implementation Best Practices

### 1. Always Request Both Attribution Windows

```javascript
// ✅ CORRECT: Request both attribution windows
action_attribution_windows: ['default', '7d_click'].join(',')

// ❌ WRONG: Only request one attribution window
action_attribution_windows: '7d_click'
```

### 2. Store Both Values in Database

```sql
CREATE TABLE campaign_metrics (
  id SERIAL PRIMARY KEY,
  campaign_id VARCHAR(255),
  date DATE,
  spend DECIMAL(10,2),
  
  -- Store both attribution windows
  purchases_default_count INTEGER,
  purchases_default_value DECIMAL(10,2),
  purchases_7d_click_count INTEGER,
  purchases_7d_click_value DECIMAL(10,2),
  
  -- Calculate ROAS for both
  roas_default DECIMAL(5,2),
  roas_7d_click DECIMAL(5,2)
);
```

### 3. Display Both in UI

- Show default attribution as primary metric
- Provide toggle or comparison view for 7d_click
- Explain the difference to users
- Use consistent labeling

### 4. Error Handling

```typescript
// Handle missing attribution data gracefully
const purchaseAction = actions?.find(action => action.action_type === 'purchase');

if (!purchaseAction) {
  return {
    default: { count: 0, value: 0 },
    '7d_click': { count: 0, value: 0 }
  };
}

// Some campaigns might not have 7d_click data
const defaultCount = purchaseAction.default ? parseInt(purchaseAction.default) : 0;
const clickCount = purchaseAction['7d_click'] ? parseInt(purchaseAction['7d_click']) : defaultCount;
```

## Common Mistakes to Avoid

1. **Using only one attribution window**: Always fetch both for complete picture
2. **Mixing attribution windows**: Don't compare default ROAS with 7d_click spend
3. **Ignoring view-through conversions**: They represent real business value
4. **Not explaining to clients**: Attribution differences can be confusing
5. **Inconsistent labeling**: Use clear, consistent names across the platform

## Testing the Implementation

### 1. Verify API Response
- Check that both `default` and `7d_click` values are present
- Ensure `default` >= `7d_click` (default includes more conversions)
- Validate that action_values correspond to actions

### 2. Data Validation
- ROAS calculations should be consistent
- Conversion counts should be integers
- Values should be positive numbers
- Default attribution should typically be higher than 7d_click

### 3. UI Testing
- Both attribution windows display correctly
- Switching between attributions works
- Explanatory text is clear and accurate
- Numbers add up correctly in summaries

This implementation ensures accurate, transparent reporting of Meta Ads performance with proper attribution window handling.
