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

def format_in_thousands(value: float) -> str:
    return f"${value:,.0f}"

def generate_technical_model_csv(inputs: Dict[str, Any], costs: Dict[str, Any]) -> str:
    lines = []

    lines.append('Confluent Technical Cost Model Analysis')
    lines.append('Infrastructure Capacity Planning & Cost Estimation')
    lines.append('')

    lines.append('INPUT PARAMETERS')
    lines.append('Parameter,Value,Unit,Notes')
    lines.append(f"Data Volume,{inputs['gb_per_day']},GB/day,Daily data ingestion volume")
    lines.append(f"Message Rate,{inputs['messages_per_second']:,},messages/second,Peak message throughput")
    lines.append(f"Average Message Size,{inputs['avg_message_size_kb']},KB,Per message payload size")
    lines.append(f"Retention Period,{inputs['retention_days']},days,Data retention duration")
    lines.append(f"Partitions,{inputs['partitions']},count,Topic partition count for parallelism")
    lines.append(f"Replication Factor,{inputs['replication_factor']},replicas,Data redundancy multiplier")
    lines.append(f"Peak to Average Ratio,{inputs['peak_to_avg_ratio']},x,Traffic spike multiplier")
    lines.append('')

    lines.append('CALCULATED METRICS')
    lines.append('Metric,Value,Unit,Calculation')
    lines.append(f"Total Storage Required,{costs['storage_gb']:,},GB,\"{inputs['gb_per_day']} × {inputs['retention_days']} days × {inputs['replication_factor']} replicas\"")
    lines.append(f"Average Throughput,{(costs['throughput_mbps'] / inputs['peak_to_avg_ratio']):.2f},MB/s,Base data transfer rate")
    lines.append(f"Peak Throughput,{costs['throughput_mbps']:,},MB/s,\"{(costs['throughput_mbps'] / inputs['peak_to_avg_ratio']):.2f} MB/s × {inputs['peak_to_avg_ratio']}x peak ratio\"")
    lines.append(f"Monthly Data Transfer,{(inputs['gb_per_day'] * 30):,},GB,Network egress volume")
    lines.append('')

    lines.append('ANNUAL COST BREAKDOWN')
    lines.append('Component,Annual Cost,Monthly Cost,Cost Driver,Unit Rate')
    lines.append(f"Storage,{format_in_thousands(costs['storage_cost_annual'])},{format_in_thousands(costs['storage_cost_annual'] / 12)},{costs['storage_gb']:,} GB,{format_in_thousands(STORAGE_COST_PER_GB_MONTH * 12)}/GB/year")
    lines.append(f"Throughput,{format_in_thousands(costs['throughput_cost_annual'])},{format_in_thousands(costs['throughput_cost_annual'] / 12)},{costs['throughput_mbps']:,} MB/s peak,{format_in_thousands(THROUGHPUT_COST_PER_MBPS_MONTH * 12)}/MBps/year")
    lines.append(f"Network Transfer,{format_in_thousands(costs['network_cost_annual'])},{format_in_thousands(costs['network_cost_annual'] / 12)},{(inputs['gb_per_day'] * 30):,} GB/month,{format_in_thousands(NETWORK_COST_PER_GB_MONTH * 12)}/GB/year")
    lines.append(f"Partition Management,{format_in_thousands(costs['partition_cost_annual'])},{format_in_thousands(costs['partition_cost_annual'] / 12)},{inputs['partitions']} partitions,{format_in_thousands(PARTITION_COST_PER_PARTITION_MONTH * 12)}/partition/year")
    lines.append(f"Retention Overhead,{format_in_thousands(costs['retention_cost_annual'])},{format_in_thousands(costs['retention_cost_annual'] / 12)},5% storage overhead,Additional retention management cost")
    lines.append('')

    lines.append('TOTAL INFRASTRUCTURE COST')
    lines.append('Period,Total Cost,Breakdown')
    lines.append(f"Monthly,{format_in_thousands(costs['total_monthly'])},\"Storage + Throughput + Network + Partitions + Retention\"")
    lines.append(f"Annual,{format_in_thousands(costs['total_annual'])},\"{format_in_thousands(costs['total_monthly'])} × 12 months\"")
    lines.append('')

    lines.append('COST SENSITIVITY ANALYSIS')
    lines.append('Parameter,Impact Level,Cost Sensitivity,Notes')
    per_gb_cost = round((STORAGE_COST_PER_GB_MONTH * inputs['retention_days'] * inputs['replication_factor'] + NETWORK_COST_PER_GB_MONTH * 30) * 12)
    lines.append(f"Data Volume (GB/day),HIGH,{format_in_thousands(per_gb_cost)} per GB/day,\"Linear relationship with storage and network costs\"")
    lines.append('Message Rate (msg/s),HIGH,Variable,"Drives throughput and compute requirements"')
    per_day_cost = round(inputs['gb_per_day'] * inputs['replication_factor'] * STORAGE_COST_PER_GB_MONTH * 12)
    lines.append(f"Retention Period (days),HIGH,{format_in_thousands(per_day_cost)} per day,\"Direct multiplier on storage costs\"")
    per_replica_cost = round(inputs['gb_per_day'] * inputs['retention_days'] * STORAGE_COST_PER_GB_MONTH * 12)
    lines.append(f"Replication Factor,HIGH,{format_in_thousands(per_replica_cost)} per replica,\"Direct multiplier on storage costs\"")
    lines.append(f"Partitions,MEDIUM,{format_in_thousands(PARTITION_COST_PER_PARTITION_MONTH * 12)} per partition,\"Fixed cost per partition for parallelism\"")
    lines.append('Peak to Average Ratio,MEDIUM,Variable,"Impacts throughput capacity planning"')
    lines.append('')

    lines.append('METHODOLOGY DETAILS')
    lines.append('Calculation,Formula,Example Values')
    lines.append(f"Storage Calculation,\"GB/day × Retention Days × Replication Factor\",\"{costs['methodology']['storage_calc']}\"")
    lines.append(f"Throughput Calculation,\"msg/s × message_size × peak_ratio\",\"{costs['methodology']['throughput_calc']}\"")
    lines.append(f"Network Calculation,\"GB/day × 30 days × rate/GB\",\"{costs['methodology']['network_calc']}\"")
    lines.append(f"Partition Cost,\"Partitions × rate/partition\",\"{costs['methodology']['partition_calc']}\"")
    lines.append('')

    lines.append('PRICING ASSUMPTIONS')
    lines.append('Component,Unit Rate (Monthly),Unit Rate (Annual),Notes')
    lines.append(f"Storage,{format_in_thousands(STORAGE_COST_PER_GB_MONTH)}/GB,{format_in_thousands(STORAGE_COST_PER_GB_MONTH * 12)}/GB,Includes replication and backups")
    lines.append(f"Throughput,{format_in_thousands(THROUGHPUT_COST_PER_MBPS_MONTH)}/MBps,{format_in_thousands(THROUGHPUT_COST_PER_MBPS_MONTH * 12)}/MBps,Peak capacity provisioning")
    lines.append(f"Network Transfer,{format_in_thousands(NETWORK_COST_PER_GB_MONTH)}/GB,{format_in_thousands(NETWORK_COST_PER_GB_MONTH * 12)}/GB,Data egress charges")
    lines.append(f"Partitions,{format_in_thousands(PARTITION_COST_PER_PARTITION_MONTH)}/partition,{format_in_thousands(PARTITION_COST_PER_PARTITION_MONTH * 12)}/partition,Compute overhead per partition")
    lines.append('Retention Management,5% of storage,5% of storage,Additional overhead for lifecycle management')
    lines.append('')

    lines.append('COST OPTIMIZATION RECOMMENDATIONS')
    lines.append('Category,Recommendation,Potential Savings,Implementation Complexity')
    lines.append('Storage,Implement tiered storage for data older than 48 hours,20-40% storage cost reduction,Medium')
    lines.append('Throughput,Enable message batching and compression,15-25% throughput cost reduction,Low')
    lines.append('Retention,Audit and reduce retention periods where possible,Direct 1:1 with days reduced,Low')
    lines.append('Partitions,Right-size partition count based on actual parallelism needs,Varies by over-provisioning,Medium')
    lines.append('Network,Optimize message payloads and enable compression,10-30% network cost reduction,Medium')
    lines.append('Replication,Evaluate if 3x replication is required for all data,33% storage cost reduction if reduced to 2x,High - impacts durability')
    lines.append('Peak Ratio,Implement auto-scaling to handle peaks more efficiently,10-20% throughput cost reduction,High')
    lines.append('')

    lines.append('ASSUMPTIONS & CONSTRAINTS')
    lines.append('1,Pricing based on representative Kafka/Confluent cloud infrastructure costs')
    lines.append('2,Actual costs may vary based on specific cloud provider (AWS/Azure/GCP) and region')
    lines.append('3,Does not include additional costs for: Schema Registry; Connect clusters; ksqlDB; Enterprise support')
    lines.append('4,Network costs assume standard egress rates; ingress typically free')
    lines.append('5,Peak to average ratio assumes consistent traffic patterns; may need adjustment for bursty workloads')
    lines.append('6,Retention management overhead estimated at 5%; actual may vary')
    lines.append('7,Partition costs include compute/memory overhead for partition leadership and replication')
    lines.append('8,Storage costs include overhead for indexing; compression; and operational buffers')
    lines.append('')

    from datetime import date
    current_date = date.today().isoformat()
    lines.append(f'Generated: {current_date}')
    lines.append('Model Version: Technical Cost Model v1.0')
    lines.append('Contact: Infrastructure Planning Team for questions or clarifications')

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
