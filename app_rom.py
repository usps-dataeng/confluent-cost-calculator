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
    'storage': 180000,      # $15,000/month (Azure + GCP)
    'network': 120000,      # $10,000/month (Azure + GCP)
    'network_multiplier': 0.75,  # Network cost multiplier (adjustable)
    'governance': 42840     # $3,570/month (Azure + GCP)
}

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
    'records_per_day': 5000,  # Daily volume
    'num_ingests': 1,  # Number of separate ingests
    'feed_configs': [  # Configuration for each feed - will be overridden by T-shirt size selection
        {'inbound': 1, 'outbound': 1, 'partitions': 24}  # Default to Medium (24 partitions)
    ]
}

# Page configuration
st.set_page_config(
    page_title="Confluent Cloud Cost Calculator",
    page_icon="🧮",
    layout="wide"
)

# Initialize session state for selected_env
if "selected_env" not in st.session_state:
    st.session_state.selected_env = "default"  # or "dev", "prod", etc.
if 'tshirt_sizes' not in st.session_state:
    st.session_state.tshirt_sizes = DEFAULT_TSHIRT_SIZES.copy()
if 'ingestion_rates' not in st.session_state:
    st.session_state.ingestion_rates = DEFAULT_INGESTION_RATES.copy()
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False
if 'show_cost_settings' not in st.session_state:
    st.session_state.show_cost_settings = False
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'cku_config' not in st.session_state:
    st.session_state.cku_config = DEFAULT_CKU_CONFIG.copy()
if 'flat_costs' not in st.session_state:
    st.session_state.flat_costs = DEFAULT_FLAT_COSTS.copy()
if 'rom_config' not in st.session_state:
    st.session_state.rom_config = DEFAULT_ROM_CONFIG.copy()
if 'show_rom_settings' not in st.session_state:
    st.session_state.show_rom_settings = False

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

# Sidebar for file upload and settings
with st.sidebar:
    st.header("⚙️ Configuration")

    # Data Source Selection
    data_source = st.radio(
        "Data Source",
        ["Databricks Table", "Upload CSV"],
        help="Choose to read from Databricks table or upload CSV"
    )

    if data_source == "Databricks Table":
        table_name = st.text_input(
            "Table Name",
            value="edlprod_users.casey_y_smith.topic_list",
            help="Fully qualified table name"
        )
        if st.button("📊 Load from Table", use_container_width=True):
            try:
                st.session_state.parsed_data = parse_databricks_table(table_name)
                st.success(f"✅ Loaded from {table_name}")
            except Exception as e:
                st.error(f"❌ Error loading table: {str(e)}")
    else:
        # File upload
        uploaded_file = st.file_uploader("📤 Upload Topic List CSV", type=['csv'])
        if uploaded_file is not None:
            st.session_state.parsed_data = parse_csv_file(uploaded_file)
            st.success("File uploaded successfully!")

    # Load default data if no file uploaded
    if st.session_state.parsed_data is None:
        try:
            with open('Topic_list.csv', 'r') as f:
                st.session_state.parsed_data = parse_csv_file(f)
        except:
            st.info("💡 Please load data from Databricks table or upload a CSV file.")

    st.divider()

    # Settings toggles
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👕 Sizes", use_container_width=True):
            st.session_state.show_settings = not st.session_state.show_settings
    with col2:
        if st.button("💰 Cost", use_container_width=True):
            st.session_state.show_cost_settings = not st.session_state.show_cost_settings
    with col3:
        if st.button("📊 ROM", use_container_width=True):
            st.session_state.show_rom_settings = not st.session_state.show_rom_settings

# Check if data is loaded
if st.session_state.parsed_data is None:
    st.error("❌ Please upload a Topic List CSV file to begin.")
    st.info("""
    **Expected CSV Format:**
    - Column 0: Topic Name
    - Column 2: Number of Partitions
    - Column 5: Storage (with units: TB, GB, MB, KB, or B)
    """)
    st.stop()

parsed_data = st.session_state.parsed_data
TOTAL_PARTITIONS = parsed_data['total_partitions']
TOTAL_STORAGE_GB = parsed_data['total_storage_gb']

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

# Cost Settings panel (hidden by default)
if st.session_state.show_cost_settings:
    st.header("💰 CKU & Cost Configuration")

    st.info("⚙️ Edit these settings to match your infrastructure costs. All values are editable.")

    # CKU Configuration
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

    # Flat Annual Costs
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

    # Reset button
    if st.button("🔄 Reset All Costs to Defaults", use_container_width=True):
        st.session_state.cku_config = DEFAULT_CKU_CONFIG.copy()
        st.session_state.flat_costs = DEFAULT_FLAT_COSTS.copy()
        st.rerun()

    st.divider()

# ROM Settings panel (hidden by default)
if st.session_state.show_rom_settings:
    st.header("📊 ROM Configuration")

    st.info("⚙️ Edit these settings to match your ROM requirements.")

    # Volume and Ingests Configuration
    st.markdown("### 📊 Project Basics")

    # Project Name Input
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
            max_value=15,
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

    # Initialize feed_configs if not present
    if 'feed_configs' not in st.session_state.rom_config or len(st.session_state.rom_config['feed_configs']) != st.session_state.rom_config['num_ingests']:
        st.session_state.rom_config['feed_configs'] = [
            {'inbound': 1, 'outbound': 1, 'partitions': 0.048}
            for _ in range(st.session_state.rom_config['num_ingests'])
        ]

    st.divider()

    # Engineering Hours Configuration
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

    # Cloud Costs Configuration
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
        # Support both old and new config keys
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
        # Support both old and new config keys
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

    # Reset button
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

with col2:
    st.markdown("### 💰 Cost Configuration")

    # Calculate total CKU costs
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
        f"${st.session_state.flat_costs['governance']:,}",
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

# Calculate costs function with actual formulas
def calculate_costs(size_config, selected_size):
    # Calculate total CKU cost
    azure_annual = st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12
    gcp_annual = st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12
    total_cku_cost_annual = azure_annual + gcp_annual

    # Prorate costs based on resource utilization
    partition_ratio = size_config['partitions'] / TOTAL_PARTITIONS if TOTAL_PARTITIONS > 0 else 0
    storage_ratio = size_config['storage_gb'] / TOTAL_STORAGE_GB if TOTAL_STORAGE_GB > 0 else 0

    # Base costs prorated by usage
    compute = partition_ratio * total_cku_cost_annual
    storage = storage_ratio * st.session_state.flat_costs['storage']

    # Network cost is flat: Network Annual × Network Multiplier (not prorated)
    network = st.session_state.flat_costs['network'] * st.session_state.flat_costs['network_multiplier']

    governance = storage_ratio * st.session_state.flat_costs['governance']

    total_yearly = compute + storage + network + governance
    total_monthly = total_yearly / 12

    return {
        'compute': compute,
        'storage': storage,
        'network': network,
        'governance': governance,
        'total_yearly': total_yearly,
        'total_monthly': total_monthly
    }

# T-shirt size selection
st.markdown("## 👕 Select T-Shirt Size")
size_cols = st.columns(5)

selected_size = st.radio(
    "Choose Size",
    options=list(st.session_state.tshirt_sizes.keys()),
    index=1,  # Default to Medium
    horizontal=True,
    label_visibility="collapsed"
)

# Display size cards
for idx, (size_name, config) in enumerate(st.session_state.tshirt_sizes.items()):
    with size_cols[idx]:
        is_selected = (size_name == selected_size)
        if is_selected:
            st.markdown(f"**🔹 {size_name}**")
        else:
            st.markdown(f"{size_name}")

        # Show partition split (50/50 inbound/outbound)
        inbound_partitions = config['partitions'] // 2
        outbound_partitions = config['partitions'] - inbound_partitions
        st.caption(f"{config['partitions']} partitions ({inbound_partitions} in / {outbound_partitions} out)")
        st.caption(f"{config['storage_gb']} GB")

st.divider()

# Get selected configuration and calculate costs
size_config = st.session_state.tshirt_sizes[selected_size]
costs = calculate_costs(size_config, selected_size)

# Display total cost in col3 (delayed until costs are calculated)
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
    **📈 Utilization Percentages:**
    - Compute: {(size_config['partitions'] / TOTAL_PARTITIONS) * 100:.3f}%
    - Storage: {(size_config['storage_gb'] / TOTAL_STORAGE_GB) * 100:.3f}%
    """)

with col2:
    st.markdown("### 💵 Cost Breakdown")

    # Calculate total CKU cost for display
    azure_annual = st.session_state.cku_config['azure_ckus'] * st.session_state.cku_config['azure_rate'] * 12
    gcp_annual = st.session_state.cku_config['gcp_ckus'] * st.session_state.cku_config['gcp_rate'] * 12
    total_cku_annual = azure_annual + gcp_annual

    partition_ratio = size_config['partitions'] / TOTAL_PARTITIONS if TOTAL_PARTITIONS > 0 else 0
    storage_ratio = size_config['storage_gb'] / TOTAL_STORAGE_GB if TOTAL_STORAGE_GB > 0 else 0

    st.markdown(f"""
        **🖥️ Compute (CKU) Cost:** ${costs['compute']:,.0f}

        _{partition_ratio:.4f} × ${total_cku_annual:,.0f}_

        _({st.session_state.cku_config['azure_ckus']} Azure CKUs + {st.session_state.cku_config['gcp_ckus']} GCP CKUs)_
    """)

    st.markdown(f"""
        **💾 Storage Cost:** ${costs['storage']:,.0f}

        _{storage_ratio:.4f} × ${st.session_state.flat_costs['storage']:,.0f}_
    """)

    st.markdown(f"""
        **🌐 Network Cost:** ${costs['network']:,.0f}

        _{st.session_state.flat_costs['network_multiplier']} × ${st.session_state.flat_costs['network']:,.0f}_
    """)

    st.markdown(f"""
        **🔒 Governance Cost:** ${costs['governance']:,.0f}

        _{storage_ratio:.4f} × ${st.session_state.flat_costs['governance']:,.0f}_
    """)

    st.markdown(f"""
        ---
        ### **Total Yearly Cost: ${costs['total_yearly']:,.0f}**
    """)

# ROM Cost Preview
st.divider()
st.markdown("## 📊 ROM Summary")

# Calculate ROM costs to preview - use selected T-shirt size partitions
from utils.rom_export import calculate_rom_costs

# Create a preview config that uses the selected T-shirt size partitions
preview_rom_config = st.session_state.rom_config.copy()
preview_rom_config['feed_configs'] = [
    {
        'inbound': st.session_state.rom_config.get('inbound_feeds', 1),
        'outbound': st.session_state.rom_config.get('outbound_feeds', 1),
        'partitions': size_config['partitions']
    }
    for _ in range(st.session_state.rom_config.get('num_ingests', 1))
]

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
                Confluent: ${rom_results['breakdown']['confluent_cost']:,.0f}<br>
                GCP: ${rom_results['breakdown']['gcp_cost']:,.0f}<br>
                Network: ${rom_results['breakdown']['network_cost']:,.0f}
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
**ROM Configuration:** {rom_results['total_feeds']} ingest(s) | {rom_results['records_per_day']:,} records/day | {size_config['partitions']} total partitions (T-shirt size: {selected_size})

Cost scales with: Number of topics ({rom_results['total_inbound_feeds']} in + {rom_results['total_outbound_feeds']} out), partition usage ({rom_results['partition_utilization_pct']:.2f}%), and daily volume ({rom_results['records_per_day']:,} records)
""")

# Export functionality
st.divider()
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("📥 Export Reports", use_container_width=True, type="primary"):
        # Update ROM config with selected T-shirt size partitions
        export_rom_config = st.session_state.rom_config.copy()

        # Get the selected size's partition count
        selected_partitions = size_config['partitions']

        # Update feed_configs with the actual partition count from the selected T-shirt size
        export_rom_config['feed_configs'] = [
            {
                'inbound': st.session_state.rom_config.get('inbound_feeds', 1),
                'outbound': st.session_state.rom_config.get('outbound_feeds', 1),
                'partitions': selected_partitions
            }
            for _ in range(st.session_state.rom_config.get('num_ingests', 1))
        ]

        # Provide three separate ROM exports
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
    ```

    #### Storage Cost Formula:
    ```
    (Storage Needed / Total Storage) × Total Annual Storage Cost

    Current: ${st.session_state.flat_costs['storage']:,}
    ```

    #### Network Cost Formula:
    ```
    Network Multiplier × Total Annual Network Cost (flat, not prorated)

    Current: {st.session_state.flat_costs['network_multiplier']} × ${st.session_state.flat_costs['network']:,} = ${st.session_state.flat_costs['network'] * st.session_state.flat_costs['network_multiplier']:,.0f}
    ```

    #### Governance Cost Formula:
    ```
    (Storage Needed / Total Storage) × Total Annual Governance Cost

    Current: ${st.session_state.flat_costs['governance']:,}
    ```

    **Notes:**
    - Partitions are split 50/50 between inbound and outbound
    - Network cost is flat (not prorated by usage)
    - All costs are editable in Settings (💰 Costs button)
    """)

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
