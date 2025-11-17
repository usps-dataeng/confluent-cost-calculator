from datetime import datetime

def generate_cost_projection_csv(
    selected_size,
    partitions,
    storage_gb,
    cku_config,
    flat_costs,
    costs,
    annual_increase_rate=0.034
):
    current_year = datetime.now().year
    csv_rows = []

    csv_rows.append('Confluent Cloud Cost Calculator - 7 Year Projection')
    csv_rows.append('')
    csv_rows.append(f'T-Shirt Size:,{selected_size}')
    csv_rows.append(f'Partitions:,{partitions}')
    csv_rows.append(f'Storage (GB):,{storage_gb}')
    csv_rows.append(f'Annual Increase Rate:,{annual_increase_rate * 100:.1f}%')
    csv_rows.append('')

    csv_rows.append('CKU Configuration')
    csv_rows.append(f"Azure CKUs:,{cku_config['azure_ckus']}")
    csv_rows.append(f"Azure Rate ($/CKU/Month):,${cku_config['azure_rate']}")
    csv_rows.append(f"GCP CKUs:,{cku_config['gcp_ckus']}")
    csv_rows.append(f"GCP Rate ($/CKU/Month):,${cku_config['gcp_rate']}")
    csv_rows.append('')

    csv_rows.append('Current Year Cost Breakdown')
    csv_rows.append('Category,Annual Cost,Monthly Cost')
    csv_rows.append(f"Compute (CKU),${costs['compute']:.2f},${costs['compute'] / 12:.2f}")
    csv_rows.append(f"Storage,${costs['storage']:.2f},${costs['storage'] / 12:.2f}")
    csv_rows.append(f"Network,${costs['network']:.2f},${costs['network'] / 12:.2f}")
    csv_rows.append(f"Governance,${costs['governance']:.2f},${costs['governance'] / 12:.2f}")
    csv_rows.append(f"Total,${costs['total_yearly']:.2f},${costs['total_monthly']:.2f}")
    csv_rows.append('')

    csv_rows.append('7-Year Cost Projection')
    csv_rows.append('Year,Compute Cost,Storage Cost,Network Cost,Governance Cost,Total Annual Cost,Cumulative Cost')

    cumulative_cost = 0

    for year in range(7):
        year_label = current_year + year
        multiplier = (1 + annual_increase_rate) ** year

        compute_cost = costs['compute'] * multiplier
        storage_cost = costs['storage'] * multiplier
        network_cost = costs['network'] * multiplier
        governance_cost = costs['governance'] * multiplier
        total_cost = compute_cost + storage_cost + network_cost + governance_cost

        cumulative_cost += total_cost

        csv_rows.append(
            f"{year_label},"
            f"${compute_cost:.2f},"
            f"${storage_cost:.2f},"
            f"${network_cost:.2f},"
            f"${governance_cost:.2f},"
            f"${total_cost:.2f},"
            f"${cumulative_cost:.2f}"
        )

    csv_rows.append('')
    csv_rows.append('Monthly Breakdown by Year')
    csv_rows.append('Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,Annual Total')

    for year in range(7):
        year_label = current_year + year
        multiplier = (1 + annual_increase_rate) ** year
        total_annual = costs['total_yearly'] * multiplier
        monthly_avg = total_annual / 12

        monthly_values = ','.join([f'${monthly_avg:.2f}'] * 12)
        csv_rows.append(f'{year_label},{monthly_values},${total_annual:.2f}')

    return '\n'.join(csv_rows)
