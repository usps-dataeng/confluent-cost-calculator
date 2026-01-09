import streamlit as st
import pandas as pd
from datetime import datetime
from utils.csv_parser import parse_csv_file, parse_databricks_table
from utils.export_data import generate_cost_projection_csv, generate_cost_projection_excel
from utils.rom_export import generate_rom_export, generate_rom_export_excel

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
    'inbound_feeds': 1,
    'outbound_feeds': 1,
    'de_hourly_rate': 80,
    'inbound_hours': 296,
    'outbound_hours': 254,
    'normalization_hours': 27.9,
    'workspace_setup_cost': 8000,
    'confluent_annual_cost': 11709,
    'gcp_per_feed_annual_cost': 9279,
    'escalation_rate': 0.034,
    'start_year': datetime.now().year,
    'records_per_day': 5000,  # Daily volume
    'num_ingests': 1,  # Number of separate ingests
    'feed_configs': [  # Configuration for each feed
        {'inbound': 1, 'outbound': 1, 'partitions': 0.048}  # Default: 1->1 with low partitions
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
        if st.button("💰 Costs", use_container_width=True):
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
    vol_col1, vol_col2, vol_col3 = st.columns(3)

    with vol_col1:
        st.session_state.rom_config['records_per_day'] = st.number_input(
            "Records per Day",
            value=st.session_state.rom_config.get('records_per_day', 5000),
            min_value=0,
            step=1000,
            key="records_per_day_input",
            help="Daily volume of records being processed"
        )

    with vol_col2:
        st.session_state.rom_config['num_ingests'] = st.number_input(
            "Number of Ingests",
            value=st.session_state.rom_config.get('num_ingests', 1),
            min_value=1,
            max_value=10,
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

    # Feed Pattern Configuration
    st.markdown("### 🔄 Feed Patterns")
    st.caption("Configure each ingest pattern (e.g., Feed 1: 3 inbound → 1 outbound)")

    for i in range(st.session_state.rom_config['num_ingests']):
        with st.expander(f"📝 Feed {i+1} Configuration", expanded=(i==0)):
            feed_col1, feed_col2, feed_col3 = st.columns(3)

            with feed_col1:
                inbound = st.number_input(
                    f"Inbound Topics",
                    value=st.session_state.rom_config['feed_configs'][i]['inbound'],
                    min_value=1,
                    step=1,
                    key=f"feed_{i}_inbound"
                )
                st.session_state.rom_config['feed_configs'][i]['inbound'] = inbound

            with feed_col2:
                outbound = st.number_input(
                    f"Outbound Topics",
                    value=st.session_state.rom_config['feed_configs'][i]['outbound'],
                    min_value=1,
                    step=1,
                    key=f"feed_{i}_outbound"
                )
                st.session_state.rom_config['feed_configs'][i]['outbound'] = outbound

            with feed_col3:
                partitions = st.number_input(
                    f"Partitions (GB)",
                    value=st.session_state.rom_config['feed_configs'][i]['partitions'],
                    min_value=0.001,
                    step=0.1,
                    format="%.3f",
                    key=f"feed_{i}_partitions",
                    help="Partition size from reference table"
                )
                st.session_state.rom_config['feed_configs'][i]['partitions'] = partitions

            st.info(f"🔹 **Feed {i+1}:** {inbound} inbound → {outbound} outbound | {partitions} partitions")

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
        st.session_state.rom_config['confluent_annual_cost'] = st.number_input(
            "Confluent Annual Cost ($)",
            value=st.session_state.rom_config['confluent_annual_cost'],
            min_value=0,
            step=100,
            key="confluent_annual_input",
            help="Annual Confluent cost per feed"
        )

    with cloud_col3:
        st.session_state.rom_config['gcp_per_feed_annual_cost'] = st.number_input(
            "GCP Per Feed Annual Cost ($)",
            value=st.session_state.rom_config['gcp_per_feed_annual_cost'],
            min_value=0,
            step=100,
            key="gcp_per_feed_input",
            help="Annual GCP cost per feed"
        )

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

# Export functionality
st.divider()
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("📥 Export Reports", use_container_width=True, type="primary"):
        excel_content = generate_cost_projection_excel(
            selected_size=selected_size,
            partitions=size_config['partitions'],
            storage_gb=size_config['storage_gb'],
            cku_config=st.session_state.cku_config,
            flat_costs=st.session_state.flat_costs,
            costs=costs,
            annual_increase_rate=annual_increase_rate / 100
        )

        excel_filename = f"confluent-cost-projection-{st.session_state.selected_env}-{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="💾 Download Cost Projection Excel",
                data=excel_content,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            rom_excel_content = generate_rom_export_excel(st.session_state.rom_config)
            rom_excel_filename = f"confluent-rom-{st.session_state.rom_config['start_year']}-{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(
                label="📊 Download ROM Excel",
                data=rom_excel_content,
                file_name=rom_excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
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
