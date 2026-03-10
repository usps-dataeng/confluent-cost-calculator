# Cost Calculator Updates - Version 1.2

## Summary of Changes

Based on your requirements, the cost calculator has been completely updated to use **total CKUs** and **editable costs**.

## ✅ What Changed

### 1. CKU Calculation (Fixed!)
**Before:** Used CKU increases (differences between existing and new)
**After:** Uses total CKUs directly

**New Configuration:**
- **Azure**: 14 CKUs × $1,925/month × 12 = **$323,400/year**
- **GCP**: 28 CKUs × $1,585/month × 12 = **$532,560/year**
- **Total Compute**: **$855,960/year**

### 2. Flat Costs (Doubled for Azure + GCP)
**Before:** Single provider baseline ($90K storage, $60K network, $21K governance)
**After:** Combined costs are **fully editable**

**Default Values:**
- **Storage**: $180,000/year ($15,000/month)
- **Network**: $120,000/year ($10,000/month)
- **Governance**: $42,840/year ($3,570/month)

### 3. Ingestion Rates (New Feature!)
**Added:** Ingestion table affects network costs

**Default Ingestion Rates (GB/day):**
| Size | Inbound | Outbound | Total |
|------|---------|----------|-------|
| Small | 10 | 10 | 20 |
| Medium | 50 | 50 | 100 |
| Large | 150 | 150 | 300 |
| X-Large | 500 | 500 | 1,000 |
| XX-Large | 1,500 | 1,500 | 3,000 |

**Network Cost Formula:**
```
Base Network Cost × Ingestion Multiplier

Where: Ingestion Multiplier = 1 + (Total Ingestion GB/day / 1000)
```

Example for Medium (100 GB/day total):
- Multiplier = 1 + (100 / 1000) = 1.10
- Network Cost = Base Cost × 1.10

### 4. Partition Clarification
**Added:** Partitions are now shown as split 50/50

**Example:**
- **24 partitions** = **12 inbound + 12 outbound**
- **50 partitions** = **25 inbound + 25 outbound**

This is displayed in the T-shirt size selector.

### 5. All Costs Editable
**Where:** Click **"💰 Costs"** button in sidebar

**Can Edit:**
- Total Azure CKUs
- Azure $/CKU/Month rate
- Total GCP CKUs
- GCP $/CKU/Month rate
- Storage annual cost
- Network annual cost
- Governance annual cost
- Ingestion rates for each T-shirt size

## 📊 Example Calculation (Medium Size)

### Your Data:
- **Total Partitions in CSV**: 12,034
- **Total Storage in CSV**: 31,000 GB

### Medium T-Shirt Size:
- **Partitions**: 24 (12 inbound + 12 outbound)
- **Storage**: 100 GB
- **Ingestion**: 50 GB/day in + 50 GB/day out

### Cost Calculation:
```
Utilization:
- Compute: 24 / 12,034 = 0.0020 (0.20%)
- Storage: 100 / 31,000 = 0.0032 (0.32%)

Compute Cost:
0.0020 × $855,960 = $1,712/year

Storage Cost:
0.0032 × $180,000 = $576/year

Network Cost:
Ingestion Multiplier = 1 + (100 / 1000) = 1.10
0.0032 × $120,000 × 1.10 = $422/year

Governance Cost:
0.0032 × $42,840 = $137/year

Total Yearly: $2,847/year ($237/month)
```

## 🔧 How to Use

### Viewing Default Costs:
1. Look at the **"💰 Cost Configuration"** panel (middle column)
2. Shows current CKU and flat costs
3. These drive all calculations

### Editing Costs:
1. Click **"💰 Costs"** button in sidebar
2. Edit any value:
   - Azure/GCP CKUs and rates
   - Storage/Network/Governance annual costs
   - Ingestion rates (in expander)
3. Changes apply immediately
4. Click **"🔄 Reset All Costs to Defaults"** to restore

### Understanding Your Cost:
1. **Select T-Shirt Size** (Small → XX-Large)
2. View **"💵 Cost Breakdown"** (right column)
3. See formulas showing exact calculations
4. Export 7-year projection for detailed analysis

## 📥 Export Changes

CSV export now includes:
- CKU configuration (Azure + GCP totals and rates)
- Flat annual costs
- Ingestion rates
- Partition split (inbound/outbound)
- 7-year projections with all cost components

## 🎯 Key Takeaways

1. **Costs are now realistic**: Based on your actual 42 CKUs and combined infrastructure
2. **Everything is editable**: No hardcoded values
3. **Ingestion matters**: Higher data ingestion increases network costs
4. **Partitions are clear**: Shows inbound/outbound split
5. **Formula transparency**: See exactly how costs are calculated

## 📝 Notes

- Default values match your specifications (14 Azure + 28 GCP CKUs)
- All flat costs doubled for Azure + GCP combined
- Ingestion multiplier is conservative (1% increase per 10 GB/day)
- You can adjust any value to match your actual costs

## Files Updated

**Both versions updated:**
- ✅ `confluent-cost-databricks/app.py`
- ✅ `confluent-cost-databricks/utils/export_data.py`
- ✅ `confluent-cost-github/app.py`
- ✅ `confluent-cost-github/utils/export_data.py`

Both Databricks and GitHub versions have identical functionality!
