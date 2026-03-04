export interface TechnicalModelInputs {
  gbPerDay: number;
  messagesPerSecond: number;
  retentionDays: number;
  partitions: number;
  replicationFactor: number;
  avgMessageSizeKB: number;
  peakToAvgRatio: number;
}

export interface TechnicalCostBreakdown {
  storageGB: number;
  storageCostAnnual: number;
  throughputMBps: number;
  throughputCostAnnual: number;
  networkCostAnnual: number;
  partitionCostAnnual: number;
  retentionCostAnnual: number;
  totalAnnual: number;
  totalMonthly: number;
  methodology: {
    storageCalc: string;
    throughputCalc: string;
    networkCalc: string;
    partitionCalc: string;
  };
}

export const DEFAULT_TECHNICAL_INPUTS: TechnicalModelInputs = {
  gbPerDay: 100,
  messagesPerSecond: 1000,
  retentionDays: 7,
  partitions: 6,
  replicationFactor: 3,
  avgMessageSizeKB: 1,
  peakToAvgRatio: 2.5,
};

const STORAGE_COST_PER_GB_MONTH = 0.10;
const THROUGHPUT_COST_PER_MBPS_MONTH = 0.08;
const NETWORK_COST_PER_GB_MONTH = 0.09;
const PARTITION_COST_PER_PARTITION_MONTH = 15;

export function calculateTechnicalCosts(inputs: TechnicalModelInputs): TechnicalCostBreakdown {
  const storageGB = inputs.gbPerDay * inputs.retentionDays * inputs.replicationFactor;

  const messagesPerDay = inputs.messagesPerSecond * 86400;
  const dataPerDayGB = (messagesPerDay * inputs.avgMessageSizeKB) / (1024 * 1024);
  const throughputMBps = (dataPerDayGB * 1024) / (24 * 60 * 60);
  const peakThroughputMBps = throughputMBps * inputs.peakToAvgRatio;

  const storageCostMonthly = storageGB * STORAGE_COST_PER_GB_MONTH;
  const throughputCostMonthly = peakThroughputMBps * THROUGHPUT_COST_PER_MBPS_MONTH;
  const networkCostMonthly = inputs.gbPerDay * 30 * NETWORK_COST_PER_GB_MONTH;
  const partitionCostMonthly = inputs.partitions * PARTITION_COST_PER_PARTITION_MONTH;
  const retentionCostMonthly = (storageGB * 0.05);

  const totalMonthly = storageCostMonthly + throughputCostMonthly + networkCostMonthly + partitionCostMonthly + retentionCostMonthly;
  const totalAnnual = totalMonthly * 12;

  return {
    storageGB: Math.round(storageGB * 100) / 100,
    storageCostAnnual: Math.round(storageCostMonthly * 12),
    throughputMBps: Math.round(peakThroughputMBps * 100) / 100,
    throughputCostAnnual: Math.round(throughputCostMonthly * 12),
    networkCostAnnual: Math.round(networkCostMonthly * 12),
    partitionCostAnnual: Math.round(partitionCostMonthly * 12),
    retentionCostAnnual: Math.round(retentionCostMonthly * 12),
    totalAnnual: Math.round(totalAnnual),
    totalMonthly: Math.round(totalMonthly),
    methodology: {
      storageCalc: `${inputs.gbPerDay} GB/day × ${inputs.retentionDays} days × ${inputs.replicationFactor} replicas = ${storageGB.toFixed(2)} GB`,
      throughputCalc: `${inputs.messagesPerSecond.toLocaleString()} msg/s × ${inputs.avgMessageSizeKB} KB/msg = ${throughputMBps.toFixed(2)} MB/s avg, ${peakThroughputMBps.toFixed(2)} MB/s peak (${inputs.peakToAvgRatio}x)`,
      networkCalc: `${inputs.gbPerDay} GB/day × 30 days × $${NETWORK_COST_PER_GB_MONTH}/GB`,
      partitionCalc: `${inputs.partitions} partitions × $${PARTITION_COST_PER_PARTITION_MONTH}/partition/month`,
    },
  };
}

function formatInThousands(value: number): string {
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function generateTechnicalModelCSV(inputs: TechnicalModelInputs, costs: TechnicalCostBreakdown): string {
  const lines: string[] = [];

  lines.push('Confluent Technical Cost Model Analysis');
  lines.push('Infrastructure Capacity Planning & Cost Estimation');
  lines.push('');

  lines.push('INPUT PARAMETERS');
  lines.push('Parameter,Value,Unit,Notes');
  lines.push(`Data Volume,${inputs.gbPerDay},GB/day,Daily data ingestion volume`);
  lines.push(`Message Rate,${inputs.messagesPerSecond.toLocaleString()},messages/second,Peak message throughput`);
  lines.push(`Average Message Size,${inputs.avgMessageSizeKB},KB,Per message payload size`);
  lines.push(`Retention Period,${inputs.retentionDays},days,Data retention duration`);
  lines.push(`Partitions,${inputs.partitions},count,Topic partition count for parallelism`);
  lines.push(`Replication Factor,${inputs.replicationFactor},replicas,Data redundancy multiplier`);
  lines.push(`Peak to Average Ratio,${inputs.peakToAvgRatio},x,Traffic spike multiplier`);
  lines.push('');

  lines.push('CALCULATED METRICS');
  lines.push('Metric,Value,Unit,Calculation');
  lines.push(`Total Storage Required,${costs.storageGB.toLocaleString()},GB,"${inputs.gbPerDay} × ${inputs.retentionDays} days × ${inputs.replicationFactor} replicas"`);
  lines.push(`Average Throughput,${(costs.throughputMBps / inputs.peakToAvgRatio).toFixed(2)},MB/s,Base data transfer rate`);
  lines.push(`Peak Throughput,${costs.throughputMBps.toLocaleString()},MB/s,"${(costs.throughputMBps / inputs.peakToAvgRatio).toFixed(2)} MB/s × ${inputs.peakToAvgRatio}x peak ratio"`);
  lines.push(`Monthly Data Transfer,${(inputs.gbPerDay * 30).toLocaleString()},GB,Network egress volume`);
  lines.push('');

  lines.push('ANNUAL COST BREAKDOWN');
  lines.push('Component,Annual Cost,Monthly Cost,Cost Driver,Unit Rate');
  lines.push(`Storage,${formatInThousands(costs.storageCostAnnual)},${formatInThousands(costs.storageCostAnnual / 12)},${costs.storageGB.toLocaleString()} GB,${formatInThousands(STORAGE_COST_PER_GB_MONTH * 12)}/GB/year`);
  lines.push(`Throughput,${formatInThousands(costs.throughputCostAnnual)},${formatInThousands(costs.throughputCostAnnual / 12)},${costs.throughputMBps.toLocaleString()} MB/s peak,${formatInThousands(THROUGHPUT_COST_PER_MBPS_MONTH * 12)}/MBps/year`);
  lines.push(`Network Transfer,${formatInThousands(costs.networkCostAnnual)},${formatInThousands(costs.networkCostAnnual / 12)},${(inputs.gbPerDay * 30).toLocaleString()} GB/month,${formatInThousands(NETWORK_COST_PER_GB_MONTH * 12)}/GB/year`);
  lines.push(`Partition Management,${formatInThousands(costs.partitionCostAnnual)},${formatInThousands(costs.partitionCostAnnual / 12)},${inputs.partitions} partitions,${formatInThousands(PARTITION_COST_PER_PARTITION_MONTH * 12)}/partition/year`);
  lines.push(`Retention Overhead,${formatInThousands(costs.retentionCostAnnual)},${formatInThousands(costs.retentionCostAnnual / 12)},5% storage overhead,Additional retention management cost`);
  lines.push('');

  lines.push('TOTAL INFRASTRUCTURE COST');
  lines.push('Period,Total Cost,Breakdown');
  lines.push(`Monthly,${formatInThousands(costs.totalMonthly)},"Storage + Throughput + Network + Partitions + Retention"`);
  lines.push(`Annual,${formatInThousands(costs.totalAnnual)},"${formatInThousands(costs.totalMonthly)} × 12 months"`);
  lines.push('');

  lines.push('COST SENSITIVITY ANALYSIS');
  lines.push('Parameter,Impact Level,Cost Sensitivity,Notes');
  lines.push('Data Volume (GB/day),HIGH,${formatInThousands(Math.round((STORAGE_COST_PER_GB_MONTH * inputs.retentionDays * inputs.replicationFactor + NETWORK_COST_PER_GB_MONTH * 30) * 12))} per GB/day,"Linear relationship with storage and network costs"');
  lines.push('Message Rate (msg/s),HIGH,Variable,"Drives throughput and compute requirements"');
  lines.push('Retention Period (days),HIGH,${formatInThousands(Math.round(inputs.gbPerDay * inputs.replicationFactor * STORAGE_COST_PER_GB_MONTH * 12))} per day,"Direct multiplier on storage costs"');
  lines.push('Replication Factor,HIGH,${formatInThousands(Math.round(inputs.gbPerDay * inputs.retentionDays * STORAGE_COST_PER_GB_MONTH * 12))} per replica,"Direct multiplier on storage costs"');
  lines.push('Partitions,MEDIUM,${formatInThousands(PARTITION_COST_PER_PARTITION_MONTH * 12)} per partition,"Fixed cost per partition for parallelism"');
  lines.push('Peak to Average Ratio,MEDIUM,Variable,"Impacts throughput capacity planning"');
  lines.push('');

  lines.push('METHODOLOGY DETAILS');
  lines.push('Calculation,Formula,Example Values');
  lines.push(`Storage Calculation,"GB/day × Retention Days × Replication Factor","${costs.methodology.storageCalc}"`);
  lines.push(`Throughput Calculation,"msg/s × message_size × peak_ratio","${costs.methodology.throughputCalc}"`);
  lines.push(`Network Calculation,"GB/day × 30 days × rate/GB","${costs.methodology.networkCalc}"`);
  lines.push(`Partition Cost,"Partitions × rate/partition","${costs.methodology.partitionCalc}"`);
  lines.push('');

  lines.push('PRICING ASSUMPTIONS');
  lines.push('Component,Unit Rate (Monthly),Unit Rate (Annual),Notes');
  lines.push(`Storage,${formatInThousands(STORAGE_COST_PER_GB_MONTH)}/GB,${formatInThousands(STORAGE_COST_PER_GB_MONTH * 12)}/GB,Includes replication and backups`);
  lines.push(`Throughput,${formatInThousands(THROUGHPUT_COST_PER_MBPS_MONTH)}/MBps,${formatInThousands(THROUGHPUT_COST_PER_MBPS_MONTH * 12)}/MBps,Peak capacity provisioning`);
  lines.push(`Network Transfer,${formatInThousands(NETWORK_COST_PER_GB_MONTH)}/GB,${formatInThousands(NETWORK_COST_PER_GB_MONTH * 12)}/GB,Data egress charges`);
  lines.push(`Partitions,${formatInThousands(PARTITION_COST_PER_PARTITION_MONTH)}/partition,${formatInThousands(PARTITION_COST_PER_PARTITION_MONTH * 12)}/partition,Compute overhead per partition`);
  lines.push(`Retention Management,5% of storage,5% of storage,Additional overhead for lifecycle management`);
  lines.push('');

  lines.push('COST OPTIMIZATION RECOMMENDATIONS');
  lines.push('Category,Recommendation,Potential Savings,Implementation Complexity');
  lines.push('Storage,Implement tiered storage for data older than 48 hours,20-40% storage cost reduction,Medium');
  lines.push('Throughput,Enable message batching and compression,15-25% throughput cost reduction,Low');
  lines.push('Retention,Audit and reduce retention periods where possible,Direct 1:1 with days reduced,Low');
  lines.push('Partitions,Right-size partition count based on actual parallelism needs,Varies by over-provisioning,Medium');
  lines.push('Network,Optimize message payloads and enable compression,10-30% network cost reduction,Medium');
  lines.push('Replication,Evaluate if 3x replication is required for all data,33% storage cost reduction if reduced to 2x,High - impacts durability');
  lines.push('Peak Ratio,Implement auto-scaling to handle peaks more efficiently,10-20% throughput cost reduction,High');
  lines.push('');

  lines.push('ASSUMPTIONS & CONSTRAINTS');
  lines.push('1,Pricing based on representative Kafka/Confluent cloud infrastructure costs');
  lines.push('2,Actual costs may vary based on specific cloud provider (AWS/Azure/GCP) and region');
  lines.push('3,Does not include additional costs for: Schema Registry; Connect clusters; ksqlDB; Enterprise support');
  lines.push('4,Network costs assume standard egress rates; ingress typically free');
  lines.push('5,Peak to average ratio assumes consistent traffic patterns; may need adjustment for bursty workloads');
  lines.push('6,Retention management overhead estimated at 5%; actual may vary');
  lines.push('7,Partition costs include compute/memory overhead for partition leadership and replication');
  lines.push('8,Storage costs include overhead for indexing; compression; and operational buffers');
  lines.push('');

  const currentDate = new Date().toISOString().split('T')[0];
  lines.push(`Generated: ${currentDate}`);
  lines.push(`Model Version: Technical Cost Model v1.0`);
  lines.push(`Contact: Infrastructure Planning Team for questions or clarifications`);

  return lines.join('\n');
}
