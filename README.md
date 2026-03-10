# Confluent Cloud Cost Calculator - Databricks Version

A Streamlit application for calculating Confluent Cloud costs using T-shirt sizing methodology.

## Features

- 📊 **T-Shirt Sizing**: Pre-configured sizes (Small, Medium, Large, X-Large, XX-Large)
- 💰 **Cost Calculation**: Compute, Storage, and Network cost breakdown
- 📈 **7-Year Projections**: Export detailed cost projections with annual increase rate
- ⚙️ **Customizable**: Modify T-shirt size configurations
- 📤 **CSV Upload**: Import your own topic list data
- 📥 **Export**: Download cost projections as CSV

## Installation

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   streamlit run app_rom.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8501`

### Databricks Deployment

#### Option 1: Databricks Apps (Recommended)

1. **Upload files to Databricks:**
   - Create a folder in your Databricks workspace (e.g., `/Workspace/Users/<your-email>/confluent-cost-calculator`)
   - Upload all files: `app.py`, `utils/`, `requirements.txt`, and `Topic_list.csv`

2. **Create Databricks App:**
   - In Databricks workspace, go to "Apps" → "Create App"
   - Select "Streamlit" as the app type
   - Point to your `app.py` file
   - Databricks will automatically install dependencies from `requirements.txt`

3. **Configure App:**
   - Set compute cluster (use a small cluster for cost efficiency)
   - Deploy the app

#### Option 2: Databricks Notebook

1. **Create a new notebook:**
   ```python
   # Cell 1: Install dependencies
   %pip install streamlit pandas
   
   # Cell 2: Copy app code
   # (Paste the contents of app.py, csv_parser.py, and export_data.py)
   
   # Cell 3: Run Streamlit
   !streamlit run app_rom.py --server.port 8501
   ```

2. **Create a tunnel:**
   ```python
   from dbruntime.databricks_repl_context import get_context
   ctx = get_context()
   print(f"https://{ctx.browserHostName}/driver-proxy/o/{ctx.workspaceId}/{ctx.clusterId}/8501/")
   ```

#### Option 3: Databricks File System (DBFS)

1. **Upload to DBFS:**
   ```python
   # Upload files to DBFS
   dbutils.fs.mkdirs("/FileStore/confluent-calculator/")
   dbutils.fs.put("/FileStore/confluent-calculator/app.py", open("app.py").read(), True)
   ```

2. **Run from notebook:**
   ```python
   %sh
   cd /dbfs/FileStore/confluent-calculator/
   streamlit run app.py
   ```

## CSV Format

The application expects a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| 0 | Topic Name |
| 2 | Number of Partitions |
| 5 | Storage Size (with units: TB, GB, MB, KB, or B) |

### Example CSV:

```csv
Topic Name,Cluster,Partitions,Replication,Retention,Storage
topic-1,prod,12,3,7d,1.5 GB
topic-2,prod,24,3,30d,10.2 GB
topic-3,prod,6,3,14d,500 MB
```

## Cost Calculation Formulas

### Compute Cost
```
(Partitions Needed / Total Partitions) × Total Yearly Compute Cost
```

### Storage Cost
```
(Storage Needed / Total Storage) × Total Yearly Storage Cost
```

### Network Cost
```
0.75 × Total Yearly Storage Cost
```

### Total Cost
```
Compute Cost + Storage Cost + Network Cost
```

## Default T-Shirt Sizes

| Size | Partitions | Storage (GB) |
|------|-----------|--------------|
| Small | 6 | 15 |
| Medium | 24 | 100 |
| Large | 50 | 250 |
| X-Large | 100 | 1,000 |
| XX-Large | 197 | 2,500 |

## Configuration

### Modifying T-Shirt Sizes

1. Click the **"🔧 T-Shirt Size Settings"** button in the sidebar
2. Adjust partition and storage values for each size
3. Click **"Reset to Defaults"** to restore original values

### Annual Increase Rate

The annual increase rate (default 3%) is used for 7-year cost projections. Adjust this value based on your organization's cost growth expectations.

## Export Functionality

The **"Export 7-Year Projection"** button generates a comprehensive CSV report including:

- Current year cost breakdown (Compute, Storage, Network)
- 7-year annual projections with cumulative costs
- Monthly breakdown for each year
- Configuration details (T-shirt size, partitions, storage)

## File Structure

```
confluent-cost-databricks/
├── app.py                    # Main Streamlit application
├── utils/
│   ├── __init__.py          # Package initializer
│   ├── csv_parser.py        # CSV parsing logic
│   └── export_data.py       # Export/projection logic
├── requirements.txt         # Python dependencies
├── Topic_list.csv          # Sample topic data (optional)
└── README.md               # This file
```

## Troubleshooting

### Issue: "No default Topic_list.csv found"
**Solution:** Upload a CSV file using the sidebar uploader, or place a `Topic_list.csv` file in the application directory.

### Issue: Streamlit won't start in Databricks
**Solution:** Ensure you have the correct permissions and the cluster has internet access to install Streamlit. Use a cluster with DBR 13.0+ for best compatibility.

### Issue: Export button doesn't work
**Solution:** Click "Export 7-Year Projection" first, then click the "Download CSV" button that appears below it.

## Support

For issues or questions, please contact your Databricks administrator or the application developer.

## Version History

- **v1.0** (2025-10-15): Initial Databricks/Streamlit version
  - Full feature parity with React version
  - Databricks deployment ready
  - CSV upload and export functionality
  - Customizable T-shirt sizes
  - 7-year cost projections

## License

Internal use only - USPS Data Engineering
