import csv
import io
import re

def parse_storage_to_gb(storage_str):
    if not storage_str or storage_str.strip() == '':
        return 0.0

    storage_str = str(storage_str).strip().upper()

    match = re.match(r'([\d.]+)\s*([A-Z]*)', storage_str)
    if not match:
        return 0.0

    value = float(match.group(1))
    unit = match.group(2) if match.group(2) else 'B'

    conversions = {
        'TB': 1024,
        'GB': 1,
        'MB': 1/1024,
        'KB': 1/(1024*1024),
        'B': 1/(1024*1024*1024)
    }

    return value * conversions.get(unit, 1)

def parse_csv_file(file):
    if hasattr(file, 'read'):
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
    else:
        content = file

    csv_reader = csv.reader(io.StringIO(content))

    rows = list(csv_reader)

    total_partitions = 0
    total_storage_gb = 0.0
    topics = []

    for row in rows[1:]:
        if len(row) < 6:
            continue

        try:
            topic_name = row[0].strip()
            partitions = int(row[2]) if row[2].strip() else 0
            storage_str = row[5].strip()
            storage_gb = parse_storage_to_gb(storage_str)

            total_partitions += partitions
            total_storage_gb += storage_gb

            topics.append({
                'name': topic_name,
                'partitions': partitions,
                'storage_gb': storage_gb,
                'storage_raw': storage_str
            })
        except (ValueError, IndexError):
            continue

    return {
        'total_partitions': total_partitions,
        'total_storage_gb': total_storage_gb,
        'topics': topics
    }

def parse_databricks_table(table_name):
    try:
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        df = spark.sql(f"SELECT * FROM {table_name}")

        pandas_df = df.toPandas()

        total_partitions = 0
        total_storage_gb = 0.0
        topics = []

        for _, row in pandas_df.iterrows():
            topic_name = str(row.iloc[0]).strip()
            partitions = int(row.iloc[2]) if row.iloc[2] else 0
            storage_str = str(row.iloc[5]).strip()
            storage_gb = parse_storage_to_gb(storage_str)

            total_partitions += partitions
            total_storage_gb += storage_gb

            topics.append({
                'name': topic_name,
                'partitions': partitions,
                'storage_gb': storage_gb,
                'storage_raw': storage_str
            })

        return {
            'total_partitions': total_partitions,
            'total_storage_gb': total_storage_gb,
            'topics': topics
        }

    except Exception as e:
        raise Exception(f"Failed to load Databricks table: {str(e)}")
