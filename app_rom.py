import streamlit as st
import pandas as pd
from datetime import datetime
from utils.csv_parser import parse_csv_file, parse_databricks_table
from utils.export_data import generate_cost_projection_csv, generate_cost_projection_excel
from utils.rom_export import (
    generate_rom_export,
    generate_rom_export_excel,
    generate_rom_export_excel_de_only,
    generate_rom_export_excel_de_tslc,
    generate_rom_export_excel_cloud_only
)
from utils.technical_cost_model import (
    calculate_technical_costs,
    generate_technical_model_csv,
    generate_technical_model_excel,
    DEFAULT_TECHNICAL_INPUTS
)

# Default T-shirt sizes
DEFAULT_TSHIRT_SIZES = {
    'Small': {'partitions': 6, 'storage_gb': 15},
    'Medium': {'partitions': 24, 'storage_gb': 100},
    'Large': {'partitions': 50, 'storage_gb': 250},
    'X-Large': {'partitions': 100, 'storage_gb': 1000},
    'XX-Large': {'partitions': 197, 'storage_gb': 2500}
}

# Default CKU Configuration (Editable in settings)
DEFAULT_CKU_CONFIG = {
    'azure_ckus': 14,
    'azure_rate': 1925,
    'gcp_ckus': 28,
    'gcp_rate': 1585
}

# Default Flat Annual Costs (Editable in settings)
DEFAULT_FLAT_COSTS = {
    'storage': 180000,
    'network': 120000,
    'network_multiplier': 0.75,
    'governance': 42840
}

# Default network totals (editable in Cost settings)
DEFAULT_TOTAL_PARTITIONS = 20224
DEFAULT_TOTAL_STORAGE_GB = 30844.17

# Default Ingestion Rates (GB/day) - Affects network costs
DEFAULT_INGESTION_RATES = {
    'Small': {'inbound': 10, 'outbound': 10},
    'Medium': {'inbound': 50, 'outbound': 50},
    'Large': {'inbound': 150, 'outbound': 150},
    'X-Large': {'inbound': 500, 'outbound': 500},
    'XX-Large': {'inbound': 1500, 'outbound': 1500}
}

# Default ROM Configuration
DEFAULT_ROM_CONFIG = {
    'project_name': '',
    'inbound_feeds': 1,
    'outbound_feeds': 1,
    'de_hourly_rate': 80,
    'inbound_hours': 296,
    'outbound_hours': 254,
    'normalization_hours': 27.9,
    'workspace_setup_cost': 8000,
    'confluent_monthly_cost': 976,
    'gcp_per_feed_monthly_cost': 773,
    'escalation_rate': 0.034,
    'start_year': datetime.now().year,
    'records_per_day': 5000,
    'num_ingests': 1,
    'feed_configs': [
        {'inbound': 1, 'outbound': 1, 'partitions': 24}
    ]
}

# Page configuration
st.set_page_config(
    page_title="Confluent Cloud Cost Calculator",
    page_icon="🧮",
    layout="wide"
)

# Initialize session state
if "selected_env" not in st.session_state:
    st.session_state.selected_env = "default"
if 'tshirt_sizes' not in st.session_state:
    st.session_state.tshirt_sizes = DEFAULT_TSHIRT_SIZES.copy()
if 'ingestion_rates' not in st.session_state:
    st.session_state.ingestion_rates = DEFAULT_INGESTION_RATES.copy()
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False
if 'show_cost_settings' not in st.session_state:
    st.session_state.show_cost_settings = False
if 'cku_config' not in st.session_state:
    st.session_state.cku_config = DEFAULT_CKU_CONFIG.copy()
if 'flat_costs' not in st.session_state:
    st.session_state.flat_costs = DEFAULT_FLAT_COSTS.copy()
if 'governance' not in st.session_state.flat_costs:
    st.session_state.flat_costs['governance'] = DEFAULT_FLAT_COSTS['governance']
if 'rom_config' not in st.session_state:
    st.session_state.rom_config = DEFAULT_ROM_CONFIG.copy()
if 'show_rom_settings' not in st.session_state:
    st.session_state.show_rom_settings = False
if 'technical_inputs' not in st.session_state:
    st.session_state.technical_inputs = DEFAULT_TECHNICAL_INPUTS.copy()
if 'show_technical_model' not in st.session_state:
    st.session_state.show_technical_model = False
if 'total_partitions' not in st.session_state:
    st.session_state.total_partitions = DEFAULT_TOTAL_PARTITIONS
if 'total_storage_gb' not in st.session_state:
    st.session_state.total_storage_gb = DEFAULT_TOTAL_STORAGE_GB

# Custom CSS
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
        color: #262730;
    }
    .metric-card h2, .metric-card h4 {
        color: #262730;
    }
    .cost-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🧮 Confluent Cloud Cost Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">T-Shirt Sizing ROM (Rough Order of Magnitude)</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # Data Source Selection (optional — data no longer required to run)
    data_source = st.radio(
        "Data Source (Optional)",
        ["None", "Databricks Table", "Upload CSV"],
        help="Optionally load topic data. Network totals are editable in Cost settings."
    )

    if data_source == "Databricks Table":
        table_name = st.text_input(
            "Table Name",
            value="edlprod_users.casey_y_smith.topic_list",
            help="Fully qualified table name"
        )
        if st.button("📊 Load from Table", use_container_width=True):
            try:
                parsed = parse_databricks_table(table_name)
                st.session_state.total_partitions = parsed['total_partitions']
                st.session_state.total_storage_gb = parsed['total_storage_gb']
                st.success(f"✅ Loaded from {table_name}")
            except Exception as e:
                st.error(f"❌ Error loading table: {str(e)}")
    elif data_source == "Upload CSV":
        uploaded_file = st.file_uploader("📤 Upload Topic List CSV", type=['csv'])
        if uploaded_file is not None:
            parsed = parse_csv_file(uploaded_file)
            st.session_state.total_partitions = parsed['total_partitions']
            st.session_state.total_storage_gb = parsed['total_storage_gb']
            st.success("File uploaded successfully!")

    st.divider()

    # Settings toggles
    if st.button("👕 Sizes", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings

    if st.button("💰 Cost", use_container_width=True):
        st.session_state.show_cost_settings = not st.session_state.show_cost_settings

    if st.button("📊 ROM", use_container_width=True):
        st.session_state.show_rom_settings = not st.session_state.show_rom_settings

    if st.button("⚡ Technical", use_container_width=True):
        st.session_state.show_technical_model = not st.session_state.show_technical_model

# Convenience aliases — all downstream code uses these variables
TOTAL_PARTITIONS = st.session_state.total_partitions
TOTAL_STORAGE_GB = st.session_state.total_storage_gb

# T-Shirt Size Settings panel
if st.session_state.show_settings:
    st.header("👕 T-Shirt Size Configuration")

    cols = st.columns(3)
    with cols[0]:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.session_state.tshirt_sizes = DEFAULT_TSHIRT_SIZES.copy()
            st.rerun()

    st.divider()

    size_cols = st.columns(5)
    for idx, (size_name, config) in enumerate(st.session_state.tshirt_sizes.items()):
        with size_cols[idx % 5]:
            st.subheader(size_name)
            partitions = st.number_input(
                "Partitions",
                value=config['partitions'],
                min_value=0,
                key=f"part_{size_name}"
            )
            storage = st.number_input(
                "Storage (GB)",
                value=config['storage_gb'],
                min_value=0,
                key=f"stor_{size_name}"
            )
            st.session_state.tshirt_sizes[size_name] = {
                'partitions': partitions,
                'storage_gb': storage
            }

    st.divider()

# Cost Settings panel
if st.session_state.show_cost_settings:
    st.header("💰 CKU & Cost Configuration")

    st.info("⚙️ Edit these settings to match your infrastructure costs. All values are editable.")

    # ── Network Totals ────────────────────────────────────────────────────────
    st.subheader("Network Totals")
    st.caption("Total partitions and storage for the entire Confluent cluster. Changing these affects all cost ratios.")

    net_col1, net_col2, net_col3 = st.columns([2, 2, 1])

    with net_col1:
        st.session_state.total_partitions = st.number_input(
            "Total Network Partitions",
            value=int(st.session_state.total_partitions),
            min_value=1,
            step=1,
            key="total_partitions_input",
            help="Total partitions across all topics in the cluster"
        )

    with net_col2:
        st.session_state.total_storage_gb = st.number_input(
            "Total Network Storage (GB)",
            value=float(st.session_state.total_storage_gb),
            min_value=0.01,
            step=100.0,
            format="%.2f",
            key="total_storage_gb_input",
            help="Total storage across all topics in the cluster"
        )

    with net_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="reset_network_totals", use_container_width=True):
            st.session_state.total_partitions = DEFAULT_TOTAL_PARTITIONS
            st.session_state.total_storage_gb = DEFAULT_TOTAL_STORAGE_GB
            st.rerun()

    # Update aliases after potential widget changes
    TOTAL_PARTITIONS = st.session_state.total_partitions
    TOTAL_STORAGE_GB = st.session_state.total_storage_gb

    st.divider()

    # ── CKU Configuration ────────────────────────────────────────────────────
    st.subheader("CKU Configuration")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Azure**")
        st.session_state.cku_config['azure_ckus'] = st.number_input(
            "Total Azure CKUs",
            value=st.session_state.cku_config['azure_ckus'],
            min_value=0,
            step=1,
            key="azure_ckus_input"
        )
        st.session_state.cku_config['azure_rate'] = st.number_input(
            "Azure $/CKU/Month",
            value=st.session_state.cku_config['azure_rate'],
            min_value=0,
            step=10,
            key="azure_rate_input"
        )
        azure_annual = st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12
        st.metric("Azure Annual Cost", f"${azure_annual:,.0f}")

    with col2:
        st.markdown("**GCP**")
        st.session_state.cku_config['gcp_ckus'] = st.number_input(
            "Total GCP CKUs",
            value=st.session_state.cku_config['gcp_ckus'],
            min_value=0,
            step=1,
            key="gcp_ckus_input"
        )
        st.session_state.cku_config['gcp_rate'] = st.number_input(
            "GCP $/CKU/Month",
            value=st.session_state.cku_config['gcp_rate'],
            min_value=0,
            step=10,
            key="gcp_rate_input"
        )
        gcp_annual = st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12
        st.metric("GCP Annual Cost", f"${gcp_annual:,.0f}")

    total_compute = azure_annual + gcp_annual
    st.success(f"**Total Compute Annual Cost: ${total_compute:,.0f}**")

    st.divider()

    # ── Flat Annual Costs ────────────────────────────────────────────────────
    st.subheader("Flat Annual Costs")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.session_state.flat_costs['storage'] = st.number_input(
            "Storage (Annual $)",
            value=st.session_state.flat_costs['storage'],
            min_value=0,
            step=1000,
            key="storage_input",
            help="Total annual storage cost (Azure + GCP)"
        )

    with col2:
        st.session_state.flat_costs['network'] = st.number_input(
            "Network (Annual $)",
            value=st.session_state.flat_costs['network'],
            min_value=0,
            step=1000,
            key="network_input",
            help="Total annual network cost (Azure + GCP)"
        )

    with col3:
        st.session_state.flat_costs['network_multiplier'] = st.number_input(
            "Network Multiplier",
            value=st.session_state.flat_costs['network_multiplier'],
            min_value=0.0,
            max_value=2.0,
            step=0.05,
            format="%.2f",
            key="network_mult_input",
            help="Network cost multiplier (default 0.75)"
        )

    with col4:
        st.session_state.flat_costs['governance'] = st.number_input(
            "Governance (Annual $)",
            value=st.session_state.flat_costs['governance'],
            min_value=0,
            step=1000,
            key="governance_input",
            help="Total annual governance cost (Azure + GCP)"
        )

    st.divider()
    st.caption("💡 Note: Partitions are split 50/50 between inbound and outbound")

    if st.button("🔄 Reset All Costs to Defaults", use_container_width=True):
        st.session_state.cku_config = DEFAULT_CKU_CONFIG.copy()
        st.session_state.flat_costs = DEFAULT_FLAT_COSTS.copy()
        st.rerun()

    st.divider()

# ROM Settings panel
if st.session_state.show_rom_settings:
    st.header("📊 ROM Configuration")
    st.info("⚙️ Edit these settings to match your ROM requirements.")

    st.markdown("### 📊 Project Basics")

    if 'project_name' not in st.session_state.rom_config:
        st.session_state.rom_config['project_name'] = ""

    st.session_state.rom_config['project_name'] = st.text_input(
        "Project Name",
        value=st.session_state.rom_config.get('project_name', ''),
        key="project_name_input",
        help="Project name to appear in Excel export headers"
    )

    vol_col1, vol_col2, vol_col3 = st.columns(3)

    with vol_col1:
        st.session_state.rom_config['records_per_day'] = st.number_input(
            "Records per Day",
            value=st.session_state.rom_config.get('records_per_day', 5000),
            min_value=1,
            step=1,
            key="records_per_day_input",
            help="Daily volume of records being processed"
        )

    with vol_col2:
        st.session_state.rom_config['num_ingests'] = st.number_input(
            "Number of Ingests",
            value=st.session_state.rom_config.get('num_ingests', 1),
            min_value=1,
            max_value=500,
            step=1,
            key="num_ingests_input",
            help="How many separate ingest feeds/patterns"
        )

    with vol_col3:
        st.session_state.rom_config['de_hourly_rate'] = st.number_input(
            "DE Hourly Rate ($)",
            value=st.session_state.rom_config['de_hourly_rate'],
            min_value=0,
            step=5,
            key="de_hourly_rate_input"
        )

    if 'feed_configs' not in st.session_state.rom_config or len(st.session_state.rom_config['feed_configs']) != st.session_state.rom_config['num_ingests']:
        st.session_state.rom_config['feed_configs'] = [
            {'inbound': 1, 'outbound': 1, 'partitions': 0.048}
            for _ in range(st.session_state.rom_config['num_ingests'])
        ]

    st.divider()

    st.markdown("### 👨‍💻 Engineering Hours")
    eng_col1, eng_col2, eng_col3 = st.columns(3)

    with eng_col1:
        st.session_state.rom_config['inbound_hours'] = st.number_input(
            "Inbound Hours",
            value=st.session_state.rom_config['inbound_hours'],
            min_value=0,
            step=1,
            key="inbound_hours_input"
        )

    with eng_col2:
        st.session_state.rom_config['outbound_hours'] = st.number_input(
            "Outbound Hours",
            value=st.session_state.rom_config['outbound_hours'],
            min_value=0,
            step=1,
            key="outbound_hours_input"
        )

    with eng_col3:
        st.session_state.rom_config['normalization_hours'] = st.number_input(
            "Normalization Hours",
            value=st.session_state.rom_config['normalization_hours'],
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key="normalization_hours_input"
        )

    st.divider()

    st.markdown("### ☁️ Cloud Costs")
    cloud_col1, cloud_col2, cloud_col3 = st.columns(3)

    with cloud_col1:
        st.session_state.rom_config['workspace_setup_cost'] = st.number_input(
            "Workspace Setup Cost ($)",
            value=st.session_state.rom_config['workspace_setup_cost'],
            min_value=0,
            step=1000,
            key="workspace_setup_input"
        )

    with cloud_col2:
        if 'confluent_monthly_cost' not in st.session_state.rom_config:
            st.session_state.rom_config['confluent_monthly_cost'] = st.session_state.rom_config.get('confluent_annual_cost', 11709) / 12

        monthly_confluent = st.number_input(
            "Confluent Monthly Cost ($/month)",
            value=float(st.session_state.rom_config['confluent_monthly_cost']),
            min_value=0.0,
            step=10.0,
            key="confluent_monthly_input",
            help="Monthly Confluent cost per feed"
        )
        st.session_state.rom_config['confluent_monthly_cost'] = monthly_confluent
        st.caption(f"Annual: ${monthly_confluent * 12:,.0f}")

    with cloud_col3:
        if 'gcp_per_feed_monthly_cost' not in st.session_state.rom_config:
            st.session_state.rom_config['gcp_per_feed_monthly_cost'] = st.session_state.rom_config.get('gcp_per_feed_annual_cost', 9279) / 12

        monthly_gcp = st.number_input(
            "GCP Per Feed Monthly ($/month)",
            value=float(st.session_state.rom_config['gcp_per_feed_monthly_cost']),
            min_value=0.0,
            step=10.0,
            key="gcp_per_feed_input",
            help="Monthly GCP cost per feed"
        )
        st.session_state.rom_config['gcp_per_feed_monthly_cost'] = monthly_gcp
        st.caption(f"Annual: ${monthly_gcp * 12:,.0f}")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.rom_config['escalation_rate'] = st.number_input(
            "Escalation Rate",
            value=st.session_state.rom_config['escalation_rate'],
            min_value=0.0,
            max_value=1.0,
            step=0.001,
            format="%.3f",
            key="escalation_rate_input",
            help="Annual cost increase rate (e.g., 0.034 = 3.4%)"
        )
    with col2:
        st.session_state.rom_config['start_year'] = st.number_input(
            "Start Year",
            value=st.session_state.rom_config['start_year'],
            min_value=2020,
            max_value=2050,
            step=1,
            key="start_year_input"
        )

    st.divider()

    if st.button("🔄 Reset ROM Settings to Defaults", use_container_width=True):
        st.session_state.rom_config = DEFAULT_ROM_CONFIG.copy()
        st.rerun()

    st.divider()

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🖥️ Total Resources")
    st.metric("Total Partitions", f"{TOTAL_PARTITIONS:,}")
    st.metric("Total Storage", f"{TOTAL_STORAGE_GB:,.2f} GB")
    st.caption(f"{TOTAL_STORAGE_GB / 1024:.2f} TB")
    st.caption("Edit in 💰 Cost settings")

with col2:
    st.markdown("### 💰 Cost Configuration")

    azure_annual = st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12
    gcp_annual = st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12
    total_cku_cost_annual = azure_annual + gcp_annual

    st.metric(
        "Compute (CKU) Annual",
        f"${total_cku_cost_annual:,.0f}",
        help=f"Azure: ${azure_annual:,.0f} + GCP: ${gcp_annual:,.0f}"
    )
    st.metric(
        "Storage Annual",
        f"${st.session_state.flat_costs['storage']:,}",
        help="Total annual storage cost (Azure + GCP)"
    )
    st.metric(
        "Network Annual",
        f"${st.session_state.flat_costs['network']:,}",
        help="Total annual network cost (Azure + GCP)"
    )
    st.metric(
        "Governance Annual",
        f"${st.session_state.flat_costs.get('governance', 42840):,}",
        help="Total annual governance cost (Azure + GCP)"
    )

    annual_increase_rate = st.number_input(
        "Annual Increase Rate (%)",
        value=3.0,
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        format="%.1f",
        help="Used for 7-year cost projection"
    )

# Calculate costs function
def calculate_costs(size_config, selected_size, num_ingests=1, records_per_day=5000):
    azure_annual = st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12
    gcp_annual = st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12
    total_cku_cost_annual = azure_annual + gcp_annual

    partition_ratio = size_config['partitions'] / TOTAL_PARTITIONS if TOTAL_PARTITIONS > 0 else 0
    storage_ratio = size_config['storage_gb'] / TOTAL_STORAGE_GB if TOTAL_STORAGE_GB > 0 else 0

    base_cost_per_ingest = total_cku_cost_annual * 0.30 / 100
    variable_cost = partition_ratio * total_cku_cost_annual * 0.70
    compute = (base_cost_per_ingest * num_ingests) + (variable_cost * num_ingests)

    base_storage_per_ingest = st.session_state.flat_costs['storage'] * 0.40 / 100
    variable_storage = storage_ratio * st.session_state.flat_costs['storage'] * 0.60
    storage = (base_storage_per_ingest * num_ingests) + (variable_storage * num_ingests)

    total_partitions_used = size_config['partitions'] * num_ingests
    partition_utilization = total_partitions_used / TOTAL_PARTITIONS if TOTAL_PARTITIONS > 0 else 0
    partition_utilization = min(partition_utilization, 1.0)
    network = st.session_state.flat_costs['network'] * partition_utilization

    base_governance_per_ingest = st.session_state.flat_costs.get('governance', 42840) * 0.40 / 100
    variable_governance = storage_ratio * st.session_state.flat_costs.get('governance', 42840) * 0.60
    governance = (base_governance_per_ingest * num_ingests) + (variable_governance * num_ingests)

    records_per_year = records_per_day * 365
    storage_gb_per_year = records_per_year / (1024 * 1024)
    storage_multiplier = 1 + (storage_gb_per_year / 1000)
    storage = storage * storage_multiplier

    total_yearly = compute + storage + network + governance
    total_monthly = total_yearly / 12

    return {
        'compute': compute,
        'storage': storage,
        'network': network,
        'governance': governance,
        'total_yearly': total_yearly,
        'total_monthly': total_monthly,
        'partition_utilization': partition_utilization * 100,
        'num_ingests': num_ingests
    }

# T-shirt size selection
st.markdown("## 👕 Select T-Shirt Size")
size_cols = st.columns(5)

selected_size = st.radio(
    "Choose Size",
    options=list(st.session_state.tshirt_sizes.keys()),
    index=1,
    horizontal=True,
    label_visibility="collapsed"
)

for idx, (size_name, config) in enumerate(st.session_state.tshirt_sizes.items()):
    with size_cols[idx]:
        is_selected = (size_name == selected_size)
        if is_selected:
            st.markdown(f"**🔹 {size_name}**")
        else:
            st.markdown(f"{size_name}")
        inbound_partitions = config['partitions'] // 2
        outbound_partitions = config['partitions'] - inbound_partitions
        st.caption(f"{config['partitions']} partitions ({inbound_partitions} in / {outbound_partitions} out)")
        st.caption(f"{config['storage_gb']} GB")

st.divider()

size_config = st.session_state.tshirt_sizes[selected_size]
num_ingests = st.session_state.rom_config.get('num_ingests', 1)
records_per_day = st.session_state.rom_config.get('records_per_day', 5000)

# Technical Model Settings
if st.session_state.show_technical_model:
    st.markdown("### ⚡ Technical Cost Model Configuration")

    st.info(f"""
    **Current ROM Configuration:**
    - Number of Ingests: {num_ingests}
    - Total Partitions: {size_config['partitions'] * num_ingests:.0f}
    - Total Records per Day: {records_per_day * num_ingests:,}
    - Per-Ingest Records per Day: {records_per_day:,}
    """)

    if st.button("🔄 Sync from ROM", use_container_width=True, type="primary"):
        total_partitions_used = size_config['partitions'] * num_ingests
        total_records_per_day = records_per_day * num_ingests
        messages_per_second = total_records_per_day / 86400
        gb_per_day = (total_records_per_day * 1) / (1024 * 1024 * 1024)

        st.session_state.technical_inputs['partitions'] = max(1, int(total_partitions_used + 0.5))
        st.session_state.technical_inputs['messages_per_second'] = messages_per_second
        st.session_state.technical_inputs['gb_per_day'] = gb_per_day

        st.session_state['tech_partitions'] = st.session_state.technical_inputs['partitions']
        st.session_state['tech_msg_per_sec'] = st.session_state.technical_inputs['messages_per_second']
        st.session_state['tech_gb_per_day'] = st.session_state.technical_inputs['gb_per_day']

        st.success(f"✅ Technical Model synced from ROM configuration ({num_ingests} ingests)!")
        st.rerun()

    st.divider()

    tech_col1, tech_col2, tech_col3 = st.columns(3)

    with tech_col1:
        st.markdown("#### Data Volume")
        st.session_state.technical_inputs['gb_per_day'] = st.number_input(
            "GB per Day",
            value=float(st.session_state.technical_inputs['gb_per_day']),
            min_value=0.0,
            step=10.0,
            key="tech_gb_per_day"
        )
        st.session_state.technical_inputs['messages_per_second'] = st.number_input(
            "Messages per Second",
            value=float(st.session_state.technical_inputs['messages_per_second']),
            min_value=0.0,
            step=100.0,
            key="tech_msg_per_sec"
        )
        st.session_state.technical_inputs['avg_message_size_kb'] = st.number_input(
            "Avg Message Size (KB)",
            value=float(st.session_state.technical_inputs['avg_message_size_kb']),
            min_value=0.0,
            step=0.1,
            key="tech_msg_size"
        )

    with tech_col2:
        st.markdown("#### Configuration")
        st.session_state.technical_inputs['retention_days'] = st.number_input(
            "Retention Days",
            value=int(st.session_state.technical_inputs['retention_days']),
            min_value=1,
            step=1,
            key="tech_retention"
        )
        st.session_state.technical_inputs['partitions'] = st.number_input(
            "Partitions",
            value=int(st.session_state.technical_inputs['partitions']),
            min_value=1,
            step=1,
            key="tech_partitions"
        )
        st.session_state.technical_inputs['replication_factor'] = st.number_input(
            "Replication Factor",
            value=int(st.session_state.technical_inputs['replication_factor']),
            min_value=1,
            step=1,
            key="tech_replication"
        )

    with tech_col3:
        st.markdown("#### Performance")
        st.session_state.technical_inputs['peak_to_avg_ratio'] = st.number_input(
            "Peak to Average Ratio",
            value=float(st.session_state.technical_inputs['peak_to_avg_ratio']),
            min_value=1.0,
            step=0.1,
            key="tech_peak_ratio"
        )

        tech_costs_preview = calculate_technical_costs(st.session_state.technical_inputs)
        st.metric("Calculated Storage", f"{tech_costs_preview['storage_gb']:,.2f} GB")
        st.metric("Peak Throughput", f"{tech_costs_preview['throughput_mbps']:,.2f} MB/s")

    st.markdown("#### Cost Preview")
    tech_preview_col1, tech_preview_col2, tech_preview_col3, tech_preview_col4, tech_preview_col5 = st.columns(5)

    with tech_preview_col1:
        st.metric("Storage (Annual)", f"${tech_costs_preview['storage_cost_annual']:,}")
    with tech_preview_col2:
        st.metric("Throughput (Annual)", f"${tech_costs_preview['throughput_cost_annual']:,}")
    with tech_preview_col3:
        st.metric("Network (Annual)", f"${tech_costs_preview['network_cost_annual']:,}")
    with tech_preview_col4:
        st.metric("Partitions (Annual)", f"${tech_costs_preview['partition_cost_annual']:,}")
    with tech_preview_col5:
        st.metric("Total Annual", f"${tech_costs_preview['total_annual']:,}")

    if st.button("🔄 Reset Technical Model to Defaults", use_container_width=True):
        st.session_state.technical_inputs = DEFAULT_TECHNICAL_INPUTS.copy()
        st.rerun()

    st.divider()

# Calculate costs
costs = calculate_costs(size_config, selected_size, num_ingests, records_per_day)

# Display total cost in col3
with col3:
    st.markdown("### 📊 Estimated Total Cost")
    st.markdown(f"""
        <div class="cost-card">
            <h4 style="margin:0; color:white;">Monthly</h4>
            <h2 style="margin:0.5rem 0; color:white;">${costs['total_monthly']:,.0f}</h2>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <h4 style="margin:0; color:white;">Yearly</h4>
            <h3 style="margin:0.5rem 0; color:white;">${costs['total_yearly']:,.0f}</h3>
        </div>
    """, unsafe_allow_html=True)

# Size Configuration and Cost Breakdown
col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚙️ Size Configuration")

    st.markdown(f"""
        <div class="metric-card">
            <h4>🖥️ Partitions Needed</h4>
            <h2>{size_config['partitions']}</h2>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #4CAF50;">
            <h4>💾 Storage Needed</h4>
            <h2>{size_config['storage_gb']} GB</h2>
        </div>
    """, unsafe_allow_html=True)

    st.info(f"""
    **📈 Utilization & Scaling:**
    - Compute: {(size_config['partitions'] / TOTAL_PARTITIONS) * 100:.3f}% per ingest × {num_ingests} ingests
    - Storage: {(size_config['storage_gb'] / TOTAL_STORAGE_GB) * 100:.3f}% per ingest × {num_ingests} ingests
    - Network: {costs['partition_utilization']:.2f}% utilization ({size_config['partitions'] * num_ingests:.2f} total partitions)
    - Records: {records_per_day:,} per day
    """)

with col2:
    st.markdown("### 💵 Cost Breakdown")

    azure_annual = st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12
    gcp_annual = st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12
    total_cku_annual = azure_annual + gcp_annual

    partition_ratio = size_config['partitions'] / TOTAL_PARTITIONS if TOTAL_PARTITIONS > 0 else 0
    storage_ratio = size_config['storage_gb'] / TOTAL_STORAGE_GB if TOTAL_STORAGE_GB > 0 else 0

    st.markdown(f"""
        **🖥️ Compute (CKU) Cost:** ${costs['compute']:,.0f}

        _{partition_ratio:.4f} × ${total_cku_annual:,.0f} × {num_ingests} ingests_

        _({st.session_state.cku_config['azure_ckus']} Azure CKUs + {st.session_state.cku_config['gcp_ckus']} GCP CKUs)_
    """)

    st.markdown(f"""
        **💾 Storage Cost:** ${costs['storage']:,.0f}

        _{storage_ratio:.4f} × ${st.session_state.flat_costs['storage']:,.0f} × {num_ingests} ingests × volume_
    """)

    st.markdown(f"""
        **🌐 Network Cost:** ${costs['network']:,.0f}

        _{costs['partition_utilization']:.2f}% × ${st.session_state.flat_costs['network']:,.0f}_
    """)

    st.markdown(f"""
        **🔒 Governance Cost:** ${costs['governance']:,.0f}

        _{storage_ratio:.4f} × ${st.session_state.flat_costs.get('governance', 42840):,.0f} × {num_ingests} ingests_
    """)

    st.markdown(f"""
        ---
        ### **Total Yearly Cost: ${costs['total_yearly']:,.0f}**
    """)

# ROM Cost Preview
st.divider()
st.markdown("## 📊 ROM Summary")

from utils.rom_export import calculate_rom_costs

preview_rom_config = st.session_state.rom_config.copy()
preview_rom_config['feed_configs'] = [
    {
        'inbound': st.session_state.rom_config.get('inbound_feeds', 1),
        'outbound': st.session_state.rom_config.get('outbound_feeds', 1),
        'partitions': size_config['partitions']
    }
    for _ in range(st.session_state.rom_config.get('num_ingests', 1))
]

preview_rom_config['azure_ckus'] = st.session_state.cku_config['azure_ckus']
preview_rom_config['azure_rate'] = st.session_state.cku_config['azure_rate']
preview_rom_config['gcp_ckus'] = st.session_state.cku_config['gcp_ckus']
preview_rom_config['gcp_rate'] = st.session_state.cku_config['gcp_rate']
preview_rom_config['total_partitions'] = TOTAL_PARTITIONS
preview_rom_config['total_storage_gb'] = TOTAL_STORAGE_GB
preview_rom_config['storage_annual'] = st.session_state.flat_costs.get('storage', 180000)
preview_rom_config['network_annual'] = st.session_state.flat_costs.get('network', 120000)
preview_rom_config['governance_annual'] = st.session_state.flat_costs.get('governance', 42840)

rom_results = calculate_rom_costs(preview_rom_config)

rom_col1, rom_col2, rom_col3 = st.columns(3)

with rom_col1:
    st.markdown(f"""
        <div class="metric-card">
            <h4>💼 One-Time Engineering</h4>
            <h2>${rom_results['breakdown']['one_time_development']:,.0f}</h2>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                {rom_results['total_inbound_feeds']} inbound + {rom_results['total_outbound_feeds']} outbound topics
            </p>
        </div>
    """, unsafe_allow_html=True)

with rom_col2:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #4CAF50;">
            <h4>☁️ First Year Cloud</h4>
            <h2>${rom_results['breakdown']['first_year_cloud_cost']:,.0f}</h2>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                Compute: ${rom_results['breakdown']['confluent_cost']:,.0f}<br>
                Storage: ${rom_results['breakdown']['gcp_cost']:,.0f}<br>
                Network: ${rom_results['breakdown']['network_cost']:,.0f}<br>
                Governance: ${rom_results['breakdown']['governance_cost']:,.0f}
            </p>
        </div>
    """, unsafe_allow_html=True)

with rom_col3:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #FF9800;">
            <h4>📈 7-Year Total</h4>
            <h2>${rom_results['breakdown']['total_project_cost']:,.0f}</h2>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                {rom_results['total_feeds']} ingests | {rom_results['partition_utilization_pct']:.2f}% network
            </p>
        </div>
    """, unsafe_allow_html=True)

st.info(f"""
**ROM Configuration:** {rom_results['total_feeds']} ingest(s) | {rom_results['records_per_day']:,} records/day | {size_config['partitions']:.2f} partitions per ingest (T-shirt size: {selected_size})

**Pricing Method:** CKU-based (actual infrastructure costs)

**Cost scales with:** Number of ingests ({rom_results['total_feeds']}), T-shirt size selection ({selected_size}), partition usage ({rom_results['partition_utilization_pct']:.2f}%), and daily volume ({rom_results['records_per_day']:,} records)
""")

# Technical Cost Model Analysis
st.divider()
st.markdown("## ⚡ Technical Cost Model Analysis")

tech_costs = calculate_technical_costs(st.session_state.technical_inputs)

tech_display_col1, tech_display_col2, tech_display_col3 = st.columns(3)

with tech_display_col1:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #00BCD4;">
            <h4>💾 Storage Required</h4>
            <h2>{tech_costs['storage_gb']:,.2f} GB</h2>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                {tech_costs['methodology']['storage_calc']}
            </p>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                Annual Cost: ${tech_costs['storage_cost_annual']:,}
            </p>
        </div>
    """, unsafe_allow_html=True)

with tech_display_col2:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #FF9800;">
            <h4>⚡ Peak Throughput</h4>
            <h2>{tech_costs['throughput_mbps']:,.2f} MB/s</h2>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                {tech_costs['methodology']['throughput_calc']}
            </p>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                Annual Cost: ${tech_costs['throughput_cost_annual']:,}
            </p>
        </div>
    """, unsafe_allow_html=True)

with tech_display_col3:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #4CAF50;">
            <h4>💰 Total Cost</h4>
            <h2>${tech_costs['total_annual']:,}</h2>
            <hr style="border-color: #ddd; margin: 0.5rem 0;">
            <p style="font-size: 0.85rem; margin: 0;">
                Monthly: ${tech_costs['total_monthly']:,}<br>
                Network: ${tech_costs['network_cost_annual']:,}<br>
                Partitions: ${tech_costs['partition_cost_annual']:,}
            </p>
        </div>
    """, unsafe_allow_html=True)

st.info(f"""
**Technical Model Parameters:** {st.session_state.technical_inputs['gb_per_day']} GB/day | {st.session_state.technical_inputs['messages_per_second']:,} msg/s | {st.session_state.technical_inputs['retention_days']} days retention | {st.session_state.technical_inputs['replication_factor']}x replication
""")

with st.expander("📊 Cost Driver Methodology"):
    st.markdown(f"""
    **Storage:** {tech_costs['methodology']['storage_calc']}

    **Throughput:** {tech_costs['methodology']['throughput_calc']}

    **Network:** {tech_costs['methodology']['network_calc']}

    **Partitions:** {tech_costs['methodology']['partition_calc']}
    """)

# Export functionality
st.divider()
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("📥 Export Reports", use_container_width=True, type="primary"):
        export_rom_config = st.session_state.rom_config.copy()
        selected_partitions = size_config['partitions']

        export_rom_config['feed_configs'] = [
            {
                'inbound': st.session_state.rom_config.get('inbound_feeds', 1),
                'outbound': st.session_state.rom_config.get('outbound_feeds', 1),
                'partitions': selected_partitions
            }
            for _ in range(st.session_state.rom_config.get('num_ingests', 1))
        ]

        st.markdown("### ROM Exports")
        rom_col1, rom_col2, rom_col3 = st.columns(3)

        with rom_col1:
            rom_de_content = generate_rom_export_excel_de_tslc(export_rom_config)
            rom_de_filename = f"confluent-rom-de-tslc-{st.session_state.rom_config['start_year']}-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(
                label="DE TSLC",
                data=rom_de_content,
                file_name=rom_de_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Data Engineering costs in TSLC format"
            )

        with rom_col2:
            rom_cloud_content = generate_rom_export_excel_cloud_only(export_rom_config)
            rom_cloud_filename = f"confluent-rom-cloud-only-{st.session_state.rom_config['start_year']}-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(
                label="Cloud Only",
                data=rom_cloud_content,
                file_name=rom_cloud_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Cloud infrastructure costs only"
            )

        with rom_col3:
            rom_complete_content = generate_rom_export_excel(export_rom_config)
            rom_complete_filename = f"confluent-rom-complete-{st.session_state.rom_config['start_year']}-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(
                label="Complete",
                data=rom_complete_content,
                file_name=rom_complete_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Complete ROM with DE + Cloud costs"
            )

        st.markdown("### Technical Model Export")
        tech_export_content = generate_technical_model_excel(st.session_state.technical_inputs, tech_costs)
        tech_export_filename = f"confluent-technical-model-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        st.download_button(
            label="📊 Technical Model",
            data=tech_export_content,
            file_name=tech_export_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Technical cost model with methodology"
        )

# Formula Reference
with st.expander("📐 Formula Reference"):
    st.markdown(f"""
    #### Compute (CKU) Cost Formula:
    ```
    (Partitions Needed / Total Partitions) × Total CKU Annual Cost

    Where: Total CKU Annual Cost = (Azure CKUs × Azure Rate × 12) + (GCP CKUs × GCP Rate × 12)

    Current: ({st.session_state.cku_config['azure_ckus']} × ${st.session_state.cku_config['azure_rate']} × 12) +
             ({st.session_state.cku_config['gcp_ckus']} × ${st.session_state.cku_config['gcp_rate']} × 12) =
             ${(st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12 + st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12):,.0f}

    Total Network Partitions (denominator): {TOTAL_PARTITIONS:,}
    ```

    #### Storage Cost Formula:
    ```
    (Storage Needed / Total Storage) × Total Annual Storage Cost

    Current: ${st.session_state.flat_costs['storage']:,}
    Total Network Storage (denominator): {TOTAL_STORAGE_GB:,.2f} GB
    ```

    #### Network Cost Formula:
    ```
    Network Multiplier × Total Annual Network Cost (flat, not prorated)

    Current: {st.session_state.flat_costs['network_multiplier']} × ${st.session_state.flat_costs['network']:,} = ${st.session_state.flat_costs['network'] * st.session_state.flat_costs['network_multiplier']:,.0f}
    ```

    #### Governance Cost Formula:
    ```
    (Storage Needed / Total Storage) × Total Annual Governance Cost

    Current: ${st.session_state.flat_costs.get('governance', 42840):,}
    ```

    **Notes:**
    - Partitions are split 50/50 between inbound and outbound
    - Network cost is flat (not prorated by usage)
    - All costs are editable in Settings (💰 Costs button)
    - Total Network Partitions and Storage are editable in 💰 Cost settings
    """)

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
