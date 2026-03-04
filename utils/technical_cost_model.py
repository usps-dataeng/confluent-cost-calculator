import pandas as pd
from typing import Dict, Any

DEFAULT_TECHNICAL_INPUTS = {
    'gb_per_day': 100,
    'messages_per_second': 1000,
    'retention_days': 7,
    'partitions': 6,
    'replication_factor': 3,
    'avg_message_size_kb': 1,
    'peak_to_avg_ratio': 2.5,
}

STORAGE_COST_PER_GB_MONTH = 0.10
THROUGHPUT_COST_PER_MBPS_MONTH = 0.08
NETWORK_COST_PER_GB_MONTH = 0.09
PARTITION_COST_PER_PARTITION_MONTH = 15

def calculate_technical_costs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    storage_gb = inputs['gb_per_day'] * inputs['retention_days'] * inputs['replication_factor']

    messages_per_day = inputs['messages_per_second'] * 86400
    data_per_day_gb = (messages_per_day * inputs['avg_message_size_kb']) / (1024 * 1024)
    throughput_mbps = (data_per_day_gb * 1024) / (24 * 60 * 60)
    peak_throughput_mbps = throughput_mbps * inputs['peak_to_avg_ratio']

    storage_cost_monthly = storage_gb * STORAGE_COST_PER_GB_MONTH
    throughput_cost_monthly = peak_throughput_mbps * THROUGHPUT_COST_PER_MBPS_MONTH
    network_cost_monthly = inputs['gb_per_day'] * 30 * NETWORK_COST_PER_GB_MONTH
    partition_cost_monthly = inputs['partitions'] * PARTITION_COST_PER_PARTITION_MONTH
    retention_cost_monthly = storage_gb * 0.05

    total_monthly = storage_cost_monthly + throughput_cost_monthly + network_cost_monthly + partition_cost_monthly + retention_cost_monthly
    total_annual = total_monthly * 12

    return {
        'storage_gb': round(storage_gb, 2),
        'storage_cost_annual': round(storage_cost_monthly * 12),
        'throughput_mbps': round(peak_throughput_mbps, 2),
        'throughput_cost_annual': round(throughput_cost_monthly * 12),
        'network_cost_annual': round(network_cost_monthly * 12),
        'partition_cost_annual': round(partition_cost_monthly * 12),
        'retention_cost_annual': round(retention_cost_monthly * 12),
        'total_annual': round(total_annual),
        'total_monthly': round(total_monthly),
        'methodology': {
            'storage_calc': f"{inputs['gb_per_day']} GB/day × {inputs['retention_days']} days × {inputs['replication_factor']} replicas = {storage_gb:.2f} GB",
            'throughput_calc': f"{inputs['messages_per_second']:,} msg/s × {inputs['avg_message_size_kb']} KB/msg = {throughput_mbps:.2f} MB/s avg, {peak_throughput_mbps:.2f} MB/s peak ({inputs['peak_to_avg_ratio']}x)",
            'network_calc': f"{inputs['gb_per_day']} GB/day × 30 days × ${NETWORK_COST_PER_GB_MONTH}/GB",
            'partition_calc': f"{inputs['partitions']} partitions × ${PARTITION_COST_PER_PARTITION_MONTH}/partition/month",
        }
    }

def generate_technical_model_csv(inputs: Dict[str, Any], costs: Dict[str, Any]) -> str:
    lines = [
        'Confluent Technical Cost Model Analysis',
        '',
        'INPUT PARAMETERS',
        'Parameter,Value,Unit',
        f"Data Volume,{inputs['gb_per_day']},GB/day",
        f"Message Rate,{inputs['messages_per_second']},messages/second",
        f"Average Message Size,{inputs['avg_message_size_kb']},KB",
        f"Retention Period,{inputs['retention_days']},days",
        f"Partitions,{inputs['partitions']},count",
        f"Replication Factor,{inputs['replication_factor']},x",
        f"Peak to Average Ratio,{inputs['peak_to_avg_ratio']},x",
        '',
        'CALCULATED STORAGE',
        'Metric,Value,Unit',
        f"Total Storage Required,{costs['storage_gb']},GB",
        f"Average Throughput,{(costs['throughput_mbps'] / inputs['peak_to_avg_ratio']):.2f},MB/s",
        f"Peak Throughput,{costs['throughput_mbps']},MB/s",
        '',
        'COST BREAKDOWN (Annual)',
        'Component,Cost,Calculation',
        f"Storage,\"${costs['storage_cost_annual']:,}\",\"{costs['methodology']['storage_calc']}\"",
        f"Throughput,\"${costs['throughput_cost_annual']:,}\",\"{costs['methodology']['throughput_calc']}\"",
        f"Network,\"${costs['network_cost_annual']:,}\",\"{costs['methodology']['network_calc']}\"",
        f"Partitions,\"${costs['partition_cost_annual']:,}\",\"{costs['methodology']['partition_calc']}\"",
        f"Retention,\"${costs['retention_cost_annual']:,}\",\"Additional 5% for retention management\"",
        '',
        'TOTAL COSTS',
        'Period,Cost',
        f"Monthly,\"${costs['total_monthly']:,}\"",
        f"Annual,\"${costs['total_annual']:,}\"",
        '',
        'COST DRIVERS',
        'Driver,Impact,Notes',
        'Data Volume (GB/day),High,Linear relationship with storage and network costs',
        'Message Rate (msg/s),High,Drives throughput and compute requirements',
        'Retention Period (days),Medium,Multiplies storage requirements',
        'Partitions,Medium,Fixed cost per partition for parallelism',
        'Replication Factor,High,Multiplies storage costs for durability',
        'Peak to Average Ratio,Medium,Impacts throughput capacity planning',
        '',
        'OPTIMIZATION RECOMMENDATIONS',
        'Category,Recommendation',
        'Storage,Consider tiered storage for older data to reduce costs',
        'Throughput,Batch messages when possible to improve efficiency',
        'Retention,Evaluate actual retention needs vs configured period',
        'Partitions,Right-size partition count based on parallelism needs',
        'Network,Use compression to reduce data transfer costs',
    ]

    return '\n'.join(lines)

def generate_technical_model_excel(inputs: Dict[str, Any], costs: Dict[str, Any]) -> bytes:
    import io

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_inputs = pd.DataFrame([
            {'Parameter': 'Data Volume', 'Value': inputs['gb_per_day'], 'Unit': 'GB/day'},
            {'Parameter': 'Message Rate', 'Value': inputs['messages_per_second'], 'Unit': 'messages/second'},
            {'Parameter': 'Average Message Size', 'Value': inputs['avg_message_size_kb'], 'Unit': 'KB'},
            {'Parameter': 'Retention Period', 'Value': inputs['retention_days'], 'Unit': 'days'},
            {'Parameter': 'Partitions', 'Value': inputs['partitions'], 'Unit': 'count'},
            {'Parameter': 'Replication Factor', 'Value': inputs['replication_factor'], 'Unit': 'x'},
            {'Parameter': 'Peak to Average Ratio', 'Value': inputs['peak_to_avg_ratio'], 'Unit': 'x'},
        ])
        df_inputs.to_excel(writer, sheet_name='Input Parameters', index=False)

        df_calculated = pd.DataFrame([
            {'Metric': 'Total Storage Required', 'Value': costs['storage_gb'], 'Unit': 'GB'},
            {'Metric': 'Average Throughput', 'Value': round(costs['throughput_mbps'] / inputs['peak_to_avg_ratio'], 2), 'Unit': 'MB/s'},
            {'Metric': 'Peak Throughput', 'Value': costs['throughput_mbps'], 'Unit': 'MB/s'},
        ])
        df_calculated.to_excel(writer, sheet_name='Calculated Metrics', index=False)

        df_costs = pd.DataFrame([
            {'Component': 'Storage', 'Annual Cost': costs['storage_cost_annual'], 'Calculation': costs['methodology']['storage_calc']},
            {'Component': 'Throughput', 'Annual Cost': costs['throughput_cost_annual'], 'Calculation': costs['methodology']['throughput_calc']},
            {'Component': 'Network', 'Annual Cost': costs['network_cost_annual'], 'Calculation': costs['methodology']['network_calc']},
            {'Component': 'Partitions', 'Annual Cost': costs['partition_cost_annual'], 'Calculation': costs['methodology']['partition_calc']},
            {'Component': 'Retention', 'Annual Cost': costs['retention_cost_annual'], 'Calculation': 'Additional 5% for retention management'},
            {'Component': '', 'Annual Cost': '', 'Calculation': ''},
            {'Component': 'TOTAL', 'Annual Cost': costs['total_annual'], 'Calculation': f"Monthly: ${costs['total_monthly']:,}"},
        ])
        df_costs.to_excel(writer, sheet_name='Cost Breakdown', index=False)

        df_drivers = pd.DataFrame([
            {'Driver': 'Data Volume (GB/day)', 'Impact': 'High', 'Notes': 'Linear relationship with storage and network costs'},
            {'Driver': 'Message Rate (msg/s)', 'Impact': 'High', 'Notes': 'Drives throughput and compute requirements'},
            {'Driver': 'Retention Period (days)', 'Impact': 'Medium', 'Notes': 'Multiplies storage requirements'},
            {'Driver': 'Partitions', 'Impact': 'Medium', 'Notes': 'Fixed cost per partition for parallelism'},
            {'Driver': 'Replication Factor', 'Impact': 'High', 'Notes': 'Multiplies storage costs for durability'},
            {'Driver': 'Peak to Average Ratio', 'Impact': 'Medium', 'Notes': 'Impacts throughput capacity planning'},
        ])
        df_drivers.to_excel(writer, sheet_name='Cost Drivers', index=False)

    output.seek(0)
    return output.getvalue()
