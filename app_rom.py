import streamlit as st
import pandas as pd
from datetime import datetime

DEFAULT_ROM_CONFIG = {
    'inboundFeeds': 1,
    'outboundFeeds': 1,
    'deHourlyRate': 80,
    'inboundHours': 296,
    'outboundHours': 254,
    'normalizationHours': 27.9,
    'workspaceSetupCost': 8000,
    'confluentAnnualCost': 11709,
    'gcpPerFeedAnnualCost': 9279,
    'escalationRate': 0.034,
    'startYear': 2025
}

st.set_page_config(
    page_title="Confluent Feed ROM Calculator",
    page_icon="📊",
    layout="wide"
)

if 'rom_config' not in st.session_state:
    st.session_state.rom_config = DEFAULT_ROM_CONFIG.copy()

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 Confluent Feed ROM Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Rough Order of Magnitude</div>', unsafe_allow_html=True)

def format_thousands(value):
    return f"${round(value / 1000)}"

def calculate_rom_costs(config):
    total_feeds = config['inboundFeeds'] + config['outboundFeeds']

    inbound_cost = config['inboundFeeds'] * config['inboundHours'] * config['deHourlyRate']
    outbound_cost = config['outboundFeeds'] * config['outboundHours'] * config['deHourlyRate']
    normalization_cost = config['normalizationHours'] * config['deHourlyRate']
    workspace_setup = config['workspaceSetupCost']

    one_time_development = inbound_cost + outbound_cost + normalization_cost + workspace_setup

    confluent_cost = config['confluentAnnualCost']
    gcp_cost = total_feeds * config['gcpPerFeedAnnualCost']
    first_year_cloud_cost = confluent_cost + gcp_cost

    initial_investment = [{
        'year': config['startYear'],
        'dataEngineering': one_time_development,
        'cloudInfrastructure': first_year_cloud_cost,
        'total': one_time_development + first_year_cloud_cost
    }]

    operating_variance = []
    cloud_infrastructure_7year = first_year_cloud_cost
    operating_variance_6year = 0

    for i in range(1, 7):
        year = config['startYear'] + i
        escalated_cloud_cost = first_year_cloud_cost * ((1 + config['escalationRate']) ** i)
        cloud_infrastructure_7year += escalated_cloud_cost
        operating_variance_6year += escalated_cloud_cost

        operating_variance.append({
            'year': year,
            'dataEngineering': 0,
            'cloudInfrastructure': escalated_cloud_cost,
            'total': escalated_cloud_cost
        })

    total_project_cost = one_time_development + cloud_infrastructure_7year

    return {
        'initialInvestment': initial_investment,
        'operatingVariance': operating_variance,
        'totalFeeds': total_feeds,
        'breakdown': {
            'inboundCost': inbound_cost,
            'outboundCost': outbound_cost,
            'normalizationCost': normalization_cost,
            'workspaceSetup': workspace_setup,
            'confluentCost': confluent_cost,
            'gcpCost': gcp_cost,
            'oneTimeDevelopment': one_time_development,
            'cloudInfrastructure7Year': cloud_infrastructure_7year,
            'operatingVariance6Year': operating_variance_6year,
            'totalProjectCost': total_project_cost
        }
    }

def generate_rom_export(config):
    results = calculate_rom_costs(config)
    lines = []

    lines.append('Confluent Feed ROM - Rough Order of Magnitude')
    lines.append('')

    years = [config['startYear'] + i for i in range(12)]
    lines.append('Fiscal Year,' + ','.join(map(str, years)) + ',Total')

    lines.append('INITIAL INVESTMENT EXPENSE')
    initial_de = results['initialInvestment'][0]['dataEngineering']
    de_line = f"Data Engineering,{format_thousands(initial_de)}" + ',,,,,,,,,,,' + f",{format_thousands(initial_de)}"
    lines.append(de_line)

    lines.append('Data Strategy and Governance,,,,,,,,,,,,$-')
    lines.append('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-')
    lines.append('Advance Modeling,,,,,,,,,,,,$-')
    lines.append('Service Performance,,,,,,,,,,,,$-')

    initial_cloud = results['initialInvestment'][0]['cloudInfrastructure']
    cloud_costs = [format_thousands(ov['cloudInfrastructure']) for ov in results['operatingVariance']]
    lines.append(
        f"GCP/GKE/Confluent,{format_thousands(initial_cloud)},{','.join(cloud_costs)},,,,,,{format_thousands(results['breakdown']['cloudInfrastructure7Year'])}"
    )

    initial_total = results['initialInvestment'][0]['total']
    total_line = f"TOTAL,{format_thousands(initial_total)},{','.join(cloud_costs)},,,,,,{format_thousands(results['breakdown']['totalProjectCost'])}"
    lines.append(total_line)

    lines.append('')
    lines.append('')

    lines.append('Fiscal Year,' + ','.join(map(str, years)) + ',Total')
    lines.append('OPERATING VARIANCE')

    op_var_costs = [format_thousands(ov['cloudInfrastructure']) for ov in results['operatingVariance']]
    lines.append(f"Data Engineering,,{','.join(op_var_costs)},,,,,,{format_thousands(results['breakdown']['operatingVariance6Year'])}")

    lines.append('Data Strategy and Governance,,,,,,,,,,,,$-')
    lines.append('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-')
    lines.append('Advance Modeling,,,,,,,,,,,,$-')
    lines.append('Service Performance,,,,,,,,,,,,$-')

    lines.append(f"TOTAL,,{','.join(op_var_costs)},,,,,,{format_thousands(results['breakdown']['operatingVariance6Year'])}")

    lines.append('')
    lines.append('')

    lines.append('Summary')
    lines.append('Capital,$-')
    lines.append(f"Expense,{format_thousands(results['breakdown']['totalProjectCost'])}")
    lines.append(f"Variance,{format_thousands(results['breakdown']['operatingVariance6Year'])}")
    lines.append(f"Total,{format_thousands(results['breakdown']['totalProjectCost'])}")

    lines.append('')
    lines.append('')
    lines.append(f"Escalation Rate,{config['escalationRate'] * 100:.1f}%")

    lines.append('')
    lines.append('Note*')
    lines.append('"Estimate based on latest Payroll 2.0 scaling factors"')
    lines.append('"ROM may require revision as detailed requirements are finalized"')

    lines.append('')
    lines.append('Assumptions:')
    lines.append(f"1,ROM covers {results['totalFeeds']} EEB ingest feed(s) with inbound/outbound data processing capabilities")
    lines.append('2,Feed ingests data with complex processing requirements')
    lines.append('3,Includes event data with facility impacts and workflow approvals')
    lines.append('4,Feed includes data normalization and standardization requirements')
    lines.append('5,Workspace/Environment setup costs included')
    lines.append(f"6,Confluent platform required for real-time streaming: {format_thousands(config['confluentAnnualCost'])} per feed per year")
    lines.append(f"7,GCP/GKE infrastructure cost: {format_thousands(config['gcpPerFeedAnnualCost'])} per feed per year for compute and storage")
    lines.append('8,ROM based on current understanding of high level requirements & known attributes')
    lines.append('9,As requirements are refined/finalized the ROM may need to be revised')

    lines.append('')
    lines.append('Timeline')
    lines.append(f"FY{config['startYear']}-FY{config['startYear'] + 6}")
    lines.append(f"12,FY{config['startYear']}: {format_thousands(initial_total)} (Data Engineering + Cloud infrastructure setup - starting in 3 weeks)")
    lines.append(f"13,FY{config['startYear'] + 1}-{config['startYear'] + 6}: {format_thousands(results['breakdown']['operatingVariance6Year'] / 6)} annually (ongoing cloud operations with {config['escalationRate'] * 100:.1f}% escalation) plus Operating Variance")

    lines.append('')
    lines.append('Cost Breakdown per Feed:')
    lines.append(f"14,Create inbound ingest: {format_thousands(config['inboundHours'] * config['deHourlyRate'])},{round(config['inboundHours'])} ({round(config['inboundHours'])} hours)")
    lines.append(f"15,Create outbound enterprise data assets: {format_thousands(config['outboundHours'] * config['deHourlyRate'])},{round(config['outboundHours'])} ({round(config['outboundHours'])} hours)")
    lines.append(f"16,Data normalization and standardization: {format_thousands(results['breakdown']['normalizationCost'])},{round(config['normalizationHours'])} ({config['normalizationHours']} hours - {results['totalFeeds']} feeds)")
    lines.append(f"17,Workspace/Environment/Subscription Prep: {format_thousands(config['workspaceSetupCost'])}")
    lines.append(f"18,Annual Confluent platform cost: {format_thousands(config['confluentAnnualCost'])},{round(config['confluentAnnualCost'])}")
    lines.append(f"19,Annual GCP/GKE cost: {format_thousands(config['gcpPerFeedAnnualCost'])},{round(config['gcpPerFeedAnnualCost'])} per feed")

    lines.append('')
    lines.append(f"Total {results['totalFeeds']}-Feed Investment")
    lines.append(f"{results['totalFeeds']}-Feed Investment")
    lines.append(f"21,Data Engineering: {format_thousands(results['breakdown']['oneTimeDevelopment'])},{round(results['breakdown']['oneTimeDevelopment'] / 1000)} (one-time development)")
    lines.append(f"22,Cloud Infrastructure: {format_thousands(results['breakdown']['cloudInfrastructure7Year'])},{round(results['breakdown']['cloudInfrastructure7Year'] / 1000)} (7-year operational costs with {config['escalationRate'] * 100:.1f}% escalation)")
    lines.append(f"23,Operating Variance: {format_thousands(results['breakdown']['operatingVariance6Year'])},{round(results['breakdown']['operatingVariance6Year'] / 1000)} (6-year escalated costs)")
    lines.append(f"24,Total Project Cost: {format_thousands(results['breakdown']['totalProjectCost'])},{round(results['breakdown']['totalProjectCost'] / 1000)}")

    return '\n'.join(lines)

with st.sidebar:
    st.header("⚙️ ROM Configuration")

    st.subheader("📊 Feed Configuration")
    st.session_state.rom_config['inboundFeeds'] = st.number_input(
        "Inbound Feeds",
        value=st.session_state.rom_config['inboundFeeds'],
        min_value=0,
        step=1
    )
    st.session_state.rom_config['outboundFeeds'] = st.number_input(
        "Outbound Feeds",
        value=st.session_state.rom_config['outboundFeeds'],
        min_value=0,
        step=1
    )

    st.divider()

    st.subheader("💼 Data Engineering")
    st.session_state.rom_config['deHourlyRate'] = st.number_input(
        "Hourly Rate ($)",
        value=st.session_state.rom_config['deHourlyRate'],
        min_value=0,
        step=5
    )
    st.session_state.rom_config['inboundHours'] = st.number_input(
        "Inbound Feed Hours",
        value=st.session_state.rom_config['inboundHours'],
        min_value=0.0,
        step=10.0
    )
    st.session_state.rom_config['outboundHours'] = st.number_input(
        "Outbound Feed Hours",
        value=st.session_state.rom_config['outboundHours'],
        min_value=0.0,
        step=10.0
    )
    st.session_state.rom_config['normalizationHours'] = st.number_input(
        "Normalization Hours",
        value=st.session_state.rom_config['normalizationHours'],
        min_value=0.0,
        step=1.0
    )
    st.session_state.rom_config['workspaceSetupCost'] = st.number_input(
        "Workspace Setup Cost ($)",
        value=st.session_state.rom_config['workspaceSetupCost'],
        min_value=0,
        step=100
    )

    st.divider()

    st.subheader("☁️ Cloud Infrastructure")
    st.session_state.rom_config['confluentAnnualCost'] = st.number_input(
        "Confluent Annual Cost ($)",
        value=st.session_state.rom_config['confluentAnnualCost'],
        min_value=0,
        step=100
    )
    st.session_state.rom_config['gcpPerFeedAnnualCost'] = st.number_input(
        "GCP/GKE Per Feed Annual ($)",
        value=st.session_state.rom_config['gcpPerFeedAnnualCost'],
        min_value=0,
        step=100
    )
    st.session_state.rom_config['escalationRate'] = st.number_input(
        "Escalation Rate (%)",
        value=st.session_state.rom_config['escalationRate'] * 100,
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        format="%.1f"
    ) / 100

    st.divider()

    st.subheader("📅 Timeline")
    st.session_state.rom_config['startYear'] = st.number_input(
        "Start Year",
        value=st.session_state.rom_config['startYear'],
        min_value=2020,
        max_value=2050,
        step=1
    )

    st.divider()

    if st.button("🔄 Reset to Defaults", use_container_width=True):
        st.session_state.rom_config = DEFAULT_ROM_CONFIG.copy()
        st.rerun()

results = calculate_rom_costs(st.session_state.rom_config)

st.markdown("## 📊 ROM Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Feeds",
        results['totalFeeds'],
        help=f"{st.session_state.rom_config['inboundFeeds']} inbound + {st.session_state.rom_config['outboundFeeds']} outbound"
    )

with col2:
    st.metric(
        "One-Time Development",
        f"${results['breakdown']['oneTimeDevelopment']:,.0f}",
        help="Data Engineering + Workspace Setup"
    )

with col3:
    st.metric(
        "7-Year Cloud Cost",
        f"${results['breakdown']['cloudInfrastructure7Year']:,.0f}",
        help="Confluent + GCP/GKE with escalation"
    )

with col4:
    st.metric(
        "Total Project Cost",
        f"${results['breakdown']['totalProjectCost']:,.0f}",
        help="Development + 7-Year Cloud Operations"
    )

st.divider()

st.markdown("## 💰 Cost Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Initial Investment (Year 1)")

    st.markdown(f"""
    **Data Engineering Hours:**
    - Inbound: {st.session_state.rom_config['inboundFeeds']} × {st.session_state.rom_config['inboundHours']} hrs × ${st.session_state.rom_config['deHourlyRate']} = ${results['breakdown']['inboundCost']:,.0f}
    - Outbound: {st.session_state.rom_config['outboundFeeds']} × {st.session_state.rom_config['outboundHours']} hrs × ${st.session_state.rom_config['deHourlyRate']} = ${results['breakdown']['outboundCost']:,.0f}
    - Normalization: {st.session_state.rom_config['normalizationHours']} hrs × ${st.session_state.rom_config['deHourlyRate']} = ${results['breakdown']['normalizationCost']:,.0f}

    **Setup Costs:**
    - Workspace/Environment: ${results['breakdown']['workspaceSetup']:,.0f}

    **Total Development: ${results['breakdown']['oneTimeDevelopment']:,.0f}**
    """)

with col2:
    st.markdown("### Annual Cloud Infrastructure")

    st.markdown(f"""
    **Year 1 Costs:**
    - Confluent Platform: ${results['breakdown']['confluentCost']:,.0f}
    - GCP/GKE ({results['totalFeeds']} feeds): ${results['breakdown']['gcpCost']:,.0f}

    **Total Year 1 Cloud: ${results['initialInvestment'][0]['cloudInfrastructure']:,.0f}**

    **7-Year Total (with {st.session_state.rom_config['escalationRate']*100:.1f}% escalation):**
    - Total Cloud Infrastructure: ${results['breakdown']['cloudInfrastructure7Year']:,.0f}
    - Operating Variance (Years 2-7): ${results['breakdown']['operatingVariance6Year']:,.0f}
    """)

st.divider()

st.markdown("## 📅 Year-by-Year Projection")

years_data = []
years_data.append({
    'Year': results['initialInvestment'][0]['year'],
    'Data Engineering': f"${results['initialInvestment'][0]['dataEngineering']:,.0f}",
    'Cloud Infrastructure': f"${results['initialInvestment'][0]['cloudInfrastructure']:,.0f}",
    'Total': f"${results['initialInvestment'][0]['total']:,.0f}",
    'Type': 'Initial Investment'
})

for ov in results['operatingVariance']:
    years_data.append({
        'Year': ov['year'],
        'Data Engineering': '$0',
        'Cloud Infrastructure': f"${ov['cloudInfrastructure']:,.0f}",
        'Total': f"${ov['total']:,.0f}",
        'Type': 'Operating Variance'
    })

df = pd.DataFrame(years_data)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

col1, col2 = st.columns([3, 1])

with col2:
    if st.button("📥 Export ROM", use_container_width=True, type="primary"):
        csv_content = generate_rom_export(st.session_state.rom_config)
        filename = f"confluent-rom-{datetime.now().strftime('%Y-%m-%d')}.csv"

        st.download_button(
            label="💾 Download CSV",
            data=csv_content,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )

with st.expander("📐 Formula Reference"):
    st.markdown(f"""
    #### Data Engineering Cost:
    ```
    Inbound Cost = Inbound Feeds × Inbound Hours × Hourly Rate
    Outbound Cost = Outbound Feeds × Outbound Hours × Hourly Rate
    Normalization Cost = Normalization Hours × Hourly Rate
    Total Development = Inbound + Outbound + Normalization + Workspace Setup
    ```

    #### Cloud Infrastructure Cost:
    ```
    Year 1 Cloud = Confluent Annual + (Total Feeds × GCP Per Feed Annual)

    Years 2-7 = Year 1 Cloud × (1 + Escalation Rate)^Year

    7-Year Total = Sum of all years
    ```

    #### Total Project Cost:
    ```
    Total = One-Time Development + 7-Year Cloud Infrastructure
    ```

    **Current Configuration:**
    - Hourly Rate: ${st.session_state.rom_config['deHourlyRate']}
    - Inbound Hours: {st.session_state.rom_config['inboundHours']}
    - Outbound Hours: {st.session_state.rom_config['outboundHours']}
    - Confluent Annual: ${st.session_state.rom_config['confluentAnnualCost']:,}
    - GCP/GKE Per Feed: ${st.session_state.rom_config['gcpPerFeedAnnualCost']:,}
    - Escalation Rate: {st.session_state.rom_config['escalationRate']*100:.1f}%
    """)

st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
