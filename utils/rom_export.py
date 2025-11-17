def format_in_thousands(value):
    return f"${value:,.0f}"

def calculate_rom_costs(config):
    total_feeds = config['inbound_feeds'] + config['outbound_feeds']

    inbound_cost = config['inbound_feeds'] * config['inbound_hours'] * config['de_hourly_rate']
    outbound_cost = config['outbound_feeds'] * config['outbound_hours'] * config['de_hourly_rate']
    normalization_cost = config['normalization_hours'] * config['de_hourly_rate']
    workspace_setup = config['workspace_setup_cost']

    one_time_development = inbound_cost + outbound_cost + normalization_cost + workspace_setup

    confluent_cost = config['confluent_annual_cost']
    gcp_cost = total_feeds * config['gcp_per_feed_annual_cost']
    first_year_cloud_cost = confluent_cost + gcp_cost

    initial_investment = [{
        'year': config['start_year'],
        'data_engineering': one_time_development,
        'cloud_infrastructure': first_year_cloud_cost,
        'total': one_time_development + first_year_cloud_cost
    }]

    operating_variance = []
    cloud_infrastructure_7year = first_year_cloud_cost
    operating_variance_6year = 0

    for i in range(1, 7):
        year = config['start_year'] + i
        escalated_cloud_cost = first_year_cloud_cost * ((1 + config['escalation_rate']) ** i)
        cloud_infrastructure_7year += escalated_cloud_cost
        operating_variance_6year += escalated_cloud_cost

        operating_variance.append({
            'year': year,
            'data_engineering': 0,
            'cloud_infrastructure': escalated_cloud_cost,
            'total': escalated_cloud_cost
        })

    total_project_cost = one_time_development + cloud_infrastructure_7year

    return {
        'initial_investment': initial_investment,
        'operating_variance': operating_variance,
        'total_feeds': total_feeds,
        'breakdown': {
            'inbound_cost': inbound_cost,
            'outbound_cost': outbound_cost,
            'normalization_cost': normalization_cost,
            'workspace_setup': workspace_setup,
            'confluent_cost': confluent_cost,
            'gcp_cost': gcp_cost,
            'one_time_development': one_time_development,
            'cloud_infrastructure_7year': cloud_infrastructure_7year,
            'operating_variance_6year': operating_variance_6year,
            'total_project_cost': total_project_cost
        }
    }

def generate_rom_export(config):
    results = calculate_rom_costs(config)
    lines = []

    lines.append('Confluent Feed ROM - Rough Order of Magnitude')
    lines.append('')

    years = [config['start_year'] + i for i in range(12)]
    lines.append('Fiscal Year,' + ','.join(map(str, years)) + ',Total')

    lines.append('INITIAL INVESTMENT EXPENSE')
    initial_de = results['initial_investment'][0]['data_engineering']
    de_line = f"Data Engineering,{format_in_thousands(initial_de)}" + ',,,,,,,,,,,' + f",{format_in_thousands(initial_de)}"
    lines.append(de_line)

    lines.append('Data Strategy and Governance,,,,,,,,,,,,$-')
    lines.append('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-')
    lines.append('Advance Modeling,,,,,,,,,,,,$-')
    lines.append('Service Performance,,,,,,,,,,,,$-')

    initial_cloud = results['initial_investment'][0]['cloud_infrastructure']
    cloud_costs = [format_in_thousands(ov['cloud_infrastructure']) for ov in results['operating_variance']]
    lines.append(
        f"GCP/GKE/Confluent,{format_in_thousands(initial_cloud)},{','.join(cloud_costs)},,,,,,{format_in_thousands(results['breakdown']['cloud_infrastructure_7year'])}"
    )

    initial_total = results['initial_investment'][0]['total']
    total_line = f"TOTAL,{format_in_thousands(initial_total)},{','.join(cloud_costs)},,,,,,{format_in_thousands(results['breakdown']['total_project_cost'])}"
    lines.append(total_line)

    lines.append('')
    lines.append('')

    lines.append('Fiscal Year,' + ','.join(map(str, years)) + ',Total')
    lines.append('OPERATING VARIANCE')

    op_var_costs = [format_in_thousands(ov['cloud_infrastructure']) for ov in results['operating_variance']]
    lines.append(f"Data Engineering,,{','.join(op_var_costs)},,,,,,{format_in_thousands(results['breakdown']['operating_variance_6year'])}")

    lines.append('Data Strategy and Governance,,,,,,,,,,,,$-')
    lines.append('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-')
    lines.append('Advance Modeling,,,,,,,,,,,,$-')
    lines.append('Service Performance,,,,,,,,,,,,$-')

    lines.append(f"TOTAL,,{','.join(op_var_costs)},,,,,,{format_in_thousands(results['breakdown']['operating_variance_6year'])}")

    lines.append('')
    lines.append('')

    lines.append('Summary')
    lines.append('Capital,$-')
    lines.append(f"Expense,{format_in_thousands(results['breakdown']['total_project_cost'])}")
    lines.append(f"Variance,{format_in_thousands(results['breakdown']['operating_variance_6year'])}")
    lines.append(f"Total,{format_in_thousands(results['breakdown']['total_project_cost'])}")

    lines.append('')
    lines.append('')
    lines.append(f"Escalation Rate,{config['escalation_rate'] * 100:.1f}%")

    lines.append('')
    lines.append('Note*')
    lines.append('"Estimate based on latest Payroll 2.0 scaling factors"')
    lines.append('"ROM may require revision as detailed requirements are finalized"')

    lines.append('')
    lines.append('Assumptions:')
    lines.append(f"1,ROM covers {results['total_feeds']} EEB ingest feed(s) with inbound/outbound data processing capabilities")
    lines.append('2,Feed ingests data with complex processing requirements')
    lines.append('3,Includes event data with facility impacts and workflow approvals')
    lines.append('4,Feed includes data normalization and standardization requirements')
    lines.append('5,Workspace/Environment setup costs included')
    lines.append(f"6,Confluent platform required for real-time streaming: {format_in_thousands(config['confluent_annual_cost'])} per feed per year")
    lines.append(f"7,GCP/GKE infrastructure cost: {format_in_thousands(config['gcp_per_feed_annual_cost'])} per feed per year for compute and storage")
    lines.append('8,ROM based on current understanding of high level requirements & known attributes')
    lines.append('9,As requirements are refined/finalized the ROM may need to be revised')

    lines.append('')
    lines.append('Timeline')
    lines.append(f"FY{config['start_year']}-FY{config['start_year'] + 6}")
    lines.append(f"12,FY{config['start_year']}: {format_in_thousands(initial_total)} (Data Engineering + Cloud infrastructure setup - starting in 3 weeks)")
    lines.append(f"13,FY{config['start_year'] + 1}-{config['start_year'] + 6}: {format_in_thousands(results['breakdown']['operating_variance_6year'] / 6)} annually (ongoing cloud operations with {config['escalation_rate'] * 100:.1f}% escalation) plus Operating Variance")

    lines.append('')
    lines.append('Cost Breakdown per Feed:')
    lines.append(f"14,Create inbound ingest: {format_in_thousands(config['inbound_hours'] * config['de_hourly_rate'])},{round(config['inbound_hours'])} ({round(config['inbound_hours'])} hours)")
    lines.append(f"15,Create outbound enterprise data assets: {format_in_thousands(config['outbound_hours'] * config['de_hourly_rate'])},{round(config['outbound_hours'])} ({round(config['outbound_hours'])} hours)")
    lines.append(f"16,Data normalization and standardization: {format_in_thousands(results['breakdown']['normalization_cost'])},{round(config['normalization_hours'])} ({config['normalization_hours']} hours - {results['total_feeds']} feeds)")
    lines.append(f"17,Workspace/Environment/Subscription Prep: {format_in_thousands(config['workspace_setup_cost'])}")
    lines.append(f"18,Annual Confluent platform cost: {format_in_thousands(config['confluent_annual_cost'])},{round(config['confluent_annual_cost'])}")
    lines.append(f"19,Annual GCP/GKE cost: {format_in_thousands(config['gcp_per_feed_annual_cost'])},{round(config['gcp_per_feed_annual_cost'])} per feed")

    lines.append('')
    lines.append(f"Total {results['total_feeds']}-Feed Investment")
    lines.append(f"{results['total_feeds']}-Feed Investment")
    lines.append(f"21,Data Engineering: {format_in_thousands(results['breakdown']['one_time_development'])},{round(results['breakdown']['one_time_development'] / 1000)} (one-time development)")
    lines.append(f"22,Cloud Infrastructure: {format_in_thousands(results['breakdown']['cloud_infrastructure_7year'])},{round(results['breakdown']['cloud_infrastructure_7year'] / 1000)} (7-year operational costs with {config['escalation_rate'] * 100:.1f}% escalation)")
    lines.append(f"23,Operating Variance: {format_in_thousands(results['breakdown']['operating_variance_6year'])},{round(results['breakdown']['operating_variance_6year'] / 1000)} (6-year escalated costs)")
    lines.append(f"24,Total Project Cost: {format_in_thousands(results['breakdown']['total_project_cost'])},{round(results['breakdown']['total_project_cost'] / 1000)}")

    return '\n'.join(lines)
