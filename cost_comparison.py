"""
Cost Comparison: CKU-Based vs Simplified Per-Feed Pricing

This script compares the two pricing methods to help decide which to use.
"""

# Current configuration from your app
TOTAL_PARTITIONS = 12034
TOTAL_STORAGE_GB = 30844.17

# CKU Configuration
azure_ckus = 14
azure_rate = 1925  # per CKU per month
gcp_ckus = 34
gcp_rate = 1585  # per CKU per month

# Flat costs
storage_annual = 180000
network_annual = 120000
network_multiplier = 1.0
governance_annual = 42840

# T-shirt sizes to test
tshirt_sizes = {
    'XS': {'partitions': 0.048, 'storage_gb': 1.23},
    'S': {'partitions': 24, 'storage_gb': 614.5},
    'M': {'partitions': 120.34, 'storage_gb': 3076.42},
    'L': {'partitions': 601.7, 'storage_gb': 15382.09},
    'XL': {'partitions': 12034, 'storage_gb': 30844.17}
}

# ROM simplified pricing
rom_confluent_monthly = 976
rom_gcp_monthly = 773
rom_base_network_annual = 120000
TOTAL_NETWORK_PARTITIONS = 12034.0

print("=" * 100)
print("COST COMPARISON: CKU-Based vs Simplified Per-Feed Pricing")
print("=" * 100)
print()

def calculate_cku_method(size_config):
    """CKU-based method (current top dashboard)"""
    azure_annual = azure_ckus * azure_rate * 12
    gcp_annual = gcp_ckus * gcp_rate * 12
    total_cku_cost_annual = azure_annual + gcp_annual

    partition_ratio = size_config['partitions'] / TOTAL_PARTITIONS if TOTAL_PARTITIONS > 0 else 0
    storage_ratio = size_config['storage_gb'] / TOTAL_STORAGE_GB if TOTAL_STORAGE_GB > 0 else 0

    compute = partition_ratio * total_cku_cost_annual
    storage = storage_ratio * storage_annual
    network = network_annual * network_multiplier  # Flat, not prorated
    governance = storage_ratio * governance_annual

    total_yearly = compute + storage + network + governance

    return {
        'compute': compute,
        'storage': storage,
        'network': network,
        'governance': governance,
        'total_yearly': total_yearly,
        'partition_ratio': partition_ratio,
        'storage_ratio': storage_ratio
    }

def calculate_rom_method(size_config, num_feeds=1, num_ingests=1, records_per_day=5000):
    """ROM simplified method (current ROM summary)"""
    total_partitions = size_config['partitions'] * num_ingests
    partition_utilization = total_partitions / TOTAL_NETWORK_PARTITIONS

    # Confluent cost scales with partitions
    confluent_cost = rom_confluent_monthly * 12 * num_feeds * (1 + partition_utilization)

    # GCP cost scales with feeds and storage
    records_per_year = records_per_day * 365
    storage_gb_per_year = records_per_year / (1024 * 1024)
    storage_multiplier = 1 + (storage_gb_per_year / 1000)
    gcp_cost = rom_gcp_monthly * 12 * num_feeds * storage_multiplier

    # Network costs based on partition usage
    network_cost = rom_base_network_annual * partition_utilization

    total_yearly = confluent_cost + gcp_cost + network_cost

    return {
        'confluent': confluent_cost,
        'gcp': gcp_cost,
        'network': network_cost,
        'total_yearly': total_yearly,
        'partition_utilization': partition_utilization
    }

print("\n" + "=" * 100)
print("SCENARIO 1: Single Feed Configuration")
print("=" * 100)

for size_name, size_config in tshirt_sizes.items():
    print(f"\n{size_name} Size - {size_config['partitions']:.2f} partitions, {size_config['storage_gb']:.2f} GB")
    print("-" * 100)

    cku_result = calculate_cku_method(size_config)
    rom_result = calculate_rom_method(size_config, num_feeds=1, num_ingests=1)

    print(f"  CKU-Based Method:")
    print(f"    Compute:    ${cku_result['compute']:>12,.0f}  ({cku_result['partition_ratio']*100:>6.3f}% of total CKUs)")
    print(f"    Storage:    ${cku_result['storage']:>12,.0f}  ({cku_result['storage_ratio']*100:>6.3f}% of total storage)")
    print(f"    Network:    ${cku_result['network']:>12,.0f}  (flat)")
    print(f"    Governance: ${cku_result['governance']:>12,.0f}")
    print(f"    TOTAL:      ${cku_result['total_yearly']:>12,.0f}/year  (${cku_result['total_yearly']/12:>10,.0f}/month)")

    print(f"\n  ROM Simplified Method:")
    print(f"    Confluent:  ${rom_result['confluent']:>12,.0f}  ({rom_result['partition_utilization']*100:>6.3f}% partition util)")
    print(f"    GCP:        ${rom_result['gcp']:>12,.0f}")
    print(f"    Network:    ${rom_result['network']:>12,.0f}")
    print(f"    TOTAL:      ${rom_result['total_yearly']:>12,.0f}/year  (${rom_result['total_yearly']/12:>10,.0f}/month)")

    difference = cku_result['total_yearly'] - rom_result['total_yearly']
    pct_diff = (difference / cku_result['total_yearly'] * 100) if cku_result['total_yearly'] > 0 else 0
    print(f"\n  Difference: ${abs(difference):>12,.0f} ({abs(pct_diff):>6.1f}%) - {'CKU method higher' if difference > 0 else 'ROM method higher'}")

print("\n\n" + "=" * 100)
print("SCENARIO 2: Multiple Feeds (3 ingests, 1 in + 1 out topics each)")
print("=" * 100)

for size_name, size_config in tshirt_sizes.items():
    print(f"\n{size_name} Size - {size_config['partitions']:.2f} partitions per feed × 3 ingests")
    print("-" * 100)

    cku_result = calculate_cku_method(size_config)
    rom_result = calculate_rom_method(size_config, num_feeds=6, num_ingests=3)  # 3 ingests × 2 topics each

    print(f"  CKU-Based Method: ${cku_result['total_yearly']:>12,.0f}/year")
    print(f"  ROM Simplified:   ${rom_result['total_yearly']:>12,.0f}/year")

    difference = cku_result['total_yearly'] - rom_result['total_yearly']
    pct_diff = (difference / cku_result['total_yearly'] * 100) if cku_result['total_yearly'] > 0 else 0
    print(f"  Difference:       ${abs(difference):>12,.0f} ({abs(pct_diff):>6.1f}%) - {'CKU method higher' if difference > 0 else 'ROM method higher'}")

print("\n\n" + "=" * 100)
print("KEY DIFFERENCES:")
print("=" * 100)
print("""
CKU-Based Method (Current Top Dashboard):
  ✓ Uses actual CKU pricing ($1,925/month for Azure, $1,585/month for GCP)
  ✓ Prorates based on partition usage (% of 12,034 total partitions)
  ✓ Prorates storage and governance based on % of 30TB total storage
  ✓ Network cost is FLAT ($120k/year regardless of size)
  ✓ DOES scale with T-shirt size selection (smaller % = lower cost)
  ✗ DOES NOT scale with number of feeds/ingests

ROM Simplified Method (Current ROM Summary):
  ✓ Uses simplified per-feed pricing ($976/month Confluent, $773/month GCP per feed)
  ✓ Scales with number of feeds and ingests
  ✓ Network cost scales with partition utilization (not flat)
  ✓ Includes partition utilization multiplier
  ✗ Does NOT use actual CKU pricing
  ✗ Less accurate for real infrastructure costs

RECOMMENDATION:
The CKU-based method is more accurate for actual infrastructure costs but doesn't scale
with number of feeds. The ROM method scales better but uses simplified pricing.

SOLUTION OPTIONS:
1. Use CKU method everywhere (more accurate but need to add feed scaling)
2. Use ROM method everywhere (less accurate but scales with feeds)
3. Keep both but label them clearly as different estimation methods
""")

print("\n" + "=" * 100)
