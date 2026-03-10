# Databricks Deployment Guide

This guide explains how to deploy the Confluent Cloud Cost Calculator as a Databricks App using volume storage.

## Prerequisites

- Access to Databricks workspace
- Permission to create volumes and apps
- Table: `edlprod_users.casey_y_smith.topic_list`
- Volume: `/Volumes/edlprod_users/casey_y_smith/cloud_cost`

## Deployment Steps

### Option 1: Databricks App (Recommended)

#### Step 1: Upload Files to Volume

```python
# In a Databricks notebook

# Create the volume directory if it doesn't exist
dbutils.fs.mkdirs("/Volumes/edlprod_users/casey_y_smith/cloud_cost/")

# Upload your local files to the volume
# You can use the Databricks UI or CLI to upload files
# Or use dbutils.fs.put() for file content

# Example: Copy files from workspace to volume
%sh
cp /Workspace/Users/<your-email>/confluent-cost-databricks/* /Volumes/edlprod_users/casey_y_smith/cloud_cost/
```

#### Step 2: Organize Files in Volume

Your volume structure should look like:

```
/Volumes/edlprod_users/casey_y_smith/cloud_cost/
├── app.py
├── requirements.txt
├── utils/
│   ├── __init__.py
│   ├── csv_parser.py
│   └── export_data.py
└── Topic_list.csv (optional fallback)
```

#### Step 3: Create Databricks App

1. **Navigate to Apps**:
   - In Databricks workspace, go to **"Apps"** in the left sidebar
   - Click **"Create App"**

2. **Configure App**:
   - **Name**: `confluent-cost-calculator`
   - **App Type**: Select **"Streamlit"**
   - **Source Path**: `/Volumes/edlprod_users/casey_y_smith/cloud_cost/app.py`
   - **Working Directory**: `/Volumes/edlprod_users/casey_y_smith/cloud_cost`

3. **Set Compute**:
   - **Cluster Type**: Single-node (sufficient for this app)
   - **Runtime**: DBR 13.3 LTS or higher
   - **Node Type**: Standard_DS3_v2 or similar (small instance)

4. **Deploy**:
   - Click **"Create"**
   - Wait for app to deploy (2-3 minutes)
   - Access via the provided URL

### Option 2: Databricks Notebook

If Databricks Apps are not available, you can run the app from a notebook:

#### Step 1: Create Notebook

Create a new Python notebook in your Databricks workspace.

#### Step 2: Install Dependencies

```python
# Cell 1: Install Streamlit
%pip install streamlit==1.28.0
dbutils.library.restartPython()
```

#### Step 3: Write Files to DBFS

```python
# Cell 2: Write app files
import os

# Set working directory
os.chdir('/dbfs/Volumes/edlprod_users/casey_y_smith/cloud_cost/')

# Verify files are present
!ls -la
```

#### Step 4: Run Streamlit

```python
# Cell 3: Start Streamlit
import subprocess
import os

os.chdir('/dbfs/Volumes/edlprod_users/casey_y_smith/cloud_cost/')

# Run streamlit
subprocess.Popen([
    "streamlit", "run", "app.py",
    "--server.port", "8501",
    "--server.headless", "true"
])
```

#### Step 5: Create Tunnel

```python
# Cell 4: Get the app URL
from databricks.sdk.runtime import *

# Get context
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
host = ctx.tags().get("browserHostName").get()
workspace_id = ctx.tags().get("orgId").get()
cluster_id = ctx.tags().get("clusterId").get()

# Print URL
print(f"Streamlit App URL:")
print(f"https://{host}/driver-proxy/o/{workspace_id}/{cluster_id}/8501/")
```

### Option 3: Using Databricks Files API

Upload files using the Databricks CLI:

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token

# Upload files to volume
databricks fs cp app.py dbfs:/Volumes/edlprod_users/casey_y_smith/cloud_cost/app.py
databricks fs cp -r utils dbfs:/Volumes/edlprod_users/casey_y_smith/cloud_cost/utils
databricks fs cp requirements.txt dbfs:/Volumes/edlprod_users/casey_y_smith/cloud_cost/requirements.txt
```

## Configuration

### Data Source Setup

The app is pre-configured to read from:
- **Table**: `edlprod_users.casey_y_smith.topic_list`
- **Volume**: `/Volumes/edlprod_users/casey_y_smith/cloud_cost`

To change the table:
1. Click **"Databricks Table"** in the sidebar
2. Enter the new fully qualified table name
3. Click **"Load from Table"**

### Table Schema Requirements

Your topic list table should have these columns (case-insensitive):

| Column Name | Type | Description |
|-------------|------|-------------|
| `Topic_Name` or `topic_name` or `name` | STRING | Topic identifier |
| `Partitions` or `partitions` | INT | Number of partitions |
| `Storage` or `storage` or `size` | STRING | Storage size with units (TB, GB, MB, KB, B) |

Example table data:
```sql
SELECT * FROM edlprod_users.casey_y_smith.topic_list LIMIT 5;

-- Expected output:
-- topic_name          | partitions | storage
-- --------------------|------------|--------
-- my-topic-1          | 12         | 1.5 GB
-- my-topic-2          | 24         | 10.2 GB
-- my-topic-3          | 6          | 500 MB
```

### CKU Cost Configuration

The app includes actual CKU cost data:

#### CKU Rates:
- **Azure East**: $1,925/CKU/month
- **GCP C1 & E4**: $1,585/CKU/month

#### Flat Annual Costs:
- **Storage**: $90,000/year ($7,500/month)
- **Network**: $60,000/year ($5,000/month)
- **Governance**: $21,420/year ($1,785/month)

To view/modify these settings:
1. Click **"💰 Costs"** button in the sidebar
2. Select environment and regions
3. View CKU configuration tables

## Usage

### Basic Workflow

1. **Load Data**:
   - Select "Databricks Table" as data source
   - Click "Load from Table"
   - Verify total partitions and storage displayed

2. **Select T-Shirt Size**:
   - Choose from: Small, Medium, Large, X-Large, XX-Large
   - View resource allocation (partitions, storage)

3. **Review Costs**:
   - View cost breakdown (Compute, Storage, Network, Governance)
   - Costs are calculated based on CKU configuration

4. **Export Projections**:
   - Click "Export 7-Year Projection"
   - Download CSV with detailed cost projections
   - Adjust annual increase rate (default: 3%)

### Advanced Features

#### Custom T-Shirt Sizes

1. Click **"👕 Sizes"** in sidebar
2. Modify partition and storage values
3. Changes are applied immediately
4. Click "Reset to Defaults" to restore original values

#### Environment Selection

1. Click **"💰 Costs"** in sidebar
2. Select environment: Prod, PreProd, CAT, SIT, or DEV
3. Select regions: Azure_E, GCP_C1, GCP_E4
4. CKU costs update automatically

## Troubleshooting

### Issue: "PySpark not available"

**Solution**: The app needs to run in a Databricks environment with Spark session. Ensure you're using DBR 13.0+ and running in a cluster context.

### Issue: Table not found

**Solution**:
```python
# Verify table exists
%sql
DESCRIBE TABLE edlprod_users.casey_y_smith.topic_list;
```

### Issue: Volume path not accessible

**Solution**:
```python
# Check volume permissions
dbutils.fs.ls("/Volumes/edlprod_users/casey_y_smith/")

# Verify cloud_cost folder exists
dbutils.fs.ls("/Volumes/edlprod_users/casey_y_smith/cloud_cost/")
```

### Issue: Streamlit won't start

**Solution**:
1. Verify Python version (3.9+)
2. Check requirements are installed: `%pip list | grep streamlit`
3. Ensure port 8501 is not in use
4. Restart cluster if needed

### Issue: Missing governance cost in breakdown

**Solution**: Ensure you're using the latest version of `app.py` and `export_data.py`. The governance cost component was added in v1.1.

## Performance Tips

1. **Cluster Size**: A small single-node cluster is sufficient for this app
2. **Caching**: Topic data is loaded once and cached in session state
3. **Cost Calculations**: All calculations are done in-memory (very fast)

## Security Considerations

1. **Data Access**: Ensure users have read access to the topic list table
2. **Volume Permissions**: Restrict write access to the volume to authorized users only
3. **App Access**: Use Databricks workspace permissions to control who can access the app

## Version History

- **v1.1** (2025-10-15): Added CKU configuration, real cost formulas, governance costs, Databricks table support
- **v1.0** (2025-10-15): Initial Databricks/Streamlit version

## Support

For issues or questions:
- Check Databricks workspace logs
- Review app logs in the Databricks App UI
- Contact your Databricks administrator

## Additional Resources

- [Databricks Apps Documentation](https://docs.databricks.com/applications/index.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Databricks Volumes](https://docs.databricks.com/sql/language-manual/sql-ref-volumes.html)
