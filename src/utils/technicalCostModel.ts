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

export function generateTechnicalModelCSV(inputs: TechnicalModelInputs, costs: TechnicalCostBreakdown): string {
  const lines = [
    'Confluent Technical Cost Model Analysis',
    '',
    'INPUT PARAMETERS',
    'Parameter,Value,Unit',
    `Data Volume,${inputs.gbPerDay},GB/day`,
    `Message Rate,${inputs.messagesPerSecond},messages/second`,
    `Average Message Size,${inputs.avgMessageSizeKB},KB`,
    `Retention Period,${inputs.retentionDays},days`,
    `Partitions,${inputs.partitions},count`,
    `Replication Factor,${inputs.replicationFactor},x`,
    `Peak to Average Ratio,${inputs.peakToAvgRatio},x`,
    '',
    'CALCULATED STORAGE',
    'Metric,Value,Unit',
    `Total Storage Required,${costs.storageGB},GB`,
    `Average Throughput,${(costs.throughputMBps / inputs.peakToAvgRatio).toFixed(2)},MB/s`,
    `Peak Throughput,${costs.throughputMBps},MB/s`,
    '',
    'COST BREAKDOWN (Annual)',
    'Component,Cost,Calculation',
    `Storage,"$${costs.storageCostAnnual.toLocaleString()}","${costs.methodology.storageCalc}"`,
    `Throughput,"$${costs.throughputCostAnnual.toLocaleString()}","${costs.methodology.throughputCalc}"`,
    `Network,"$${costs.networkCostAnnual.toLocaleString()}","${costs.methodology.networkCalc}"`,
    `Partitions,"$${costs.partitionCostAnnual.toLocaleString()}","${costs.methodology.partitionCalc}"`,
    `Retention,"$${costs.retentionCostAnnual.toLocaleString()}","Additional 5% for retention management"`,
    '',
    'TOTAL COSTS',
    'Period,Cost',
    `Monthly,"$${costs.totalMonthly.toLocaleString()}"`,
    `Annual,"$${costs.totalAnnual.toLocaleString()}"`,
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
  ];

  return lines.join('\n');
}
