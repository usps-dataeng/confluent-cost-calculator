export interface FeedConfig {
  inbound: number;
  outbound: number;
  partitions: number;
}

export interface ROMConfig {
  inboundFeeds: number;
  outboundFeeds: number;
  deHourlyRate: number;
  inboundHours: number;
  outboundHours: number;
  normalizationHours: number;
  workspaceSetupCost: number;
  confluentAnnualCost: number;
  gcpPerFeedAnnualCost: number;
  escalationRate: number;
  startYear: number;
  recordsPerDay?: number;
  numIngests?: number;
  feedConfigs?: FeedConfig[];
}

interface YearlyROMCost {
  year: number;
  dataEngineering: number;
  cloudInfrastructure: number;
  total: number;
}

function formatInThousands(value: number): string {
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function calculateROMCosts(config: ROMConfig): {
  initialInvestment: YearlyROMCost[];
  operatingVariance: YearlyROMCost[];
  totalFeeds: number;
  totalPartitions: number;
  totalInboundFeeds: number;
  totalOutboundFeeds: number;
  feedConfigs: FeedConfig[];
  recordsPerDay: number;
  partitionUtilizationPct: number;
  breakdown: {
    inboundCost: number;
    outboundCost: number;
    normalizationCost: number;
    workspaceSetup: number;
    confluentCost: number;
    gcpCost: number;
    networkCost: number;
    oneTimeDevelopment: number;
    cloudInfrastructure7Year: number;
    operatingVariance6Year: number;
    totalProjectCost: number;
    firstYearCloudCost: number;
  };
} {
  // Calculate based on new feed_configs structure
  const numIngests = config.numIngests ?? 1;
  const feedConfigs = config.feedConfigs ?? [{ inbound: 1, outbound: 1, partitions: 0.048 }];
  const recordsPerDay = config.recordsPerDay ?? 5000;

  // Calculate total feeds and partitions from feedConfigs
  const totalInboundFeeds = feedConfigs.reduce((sum, f) => sum + f.inbound, 0);
  const totalOutboundFeeds = feedConfigs.reduce((sum, f) => sum + f.outbound, 0);
  const totalFeeds = numIngests; // Number of separate ingests
  const totalPartitions = feedConfigs.reduce((sum, f) => sum + f.partitions, 0);

  // Calculate engineering costs (scales with number of topics)
  const inboundCost = totalInboundFeeds * config.inboundHours * config.deHourlyRate;
  const outboundCost = totalOutboundFeeds * config.outboundHours * config.deHourlyRate;
  const normalizationCost = config.normalizationHours * config.deHourlyRate * totalFeeds;
  const workspaceSetup = config.workspaceSetupCost;

  const oneTimeDevelopment = inboundCost + outboundCost + normalizationCost + workspaceSetup;

  // Cloud costs - base cost is for 1 inbound+outbound pair, multiply by number of pairs
  const baseConfluentAnnual = config.confluentAnnualCost;
  const baseGcpAnnual = config.gcpPerFeedAnnualCost;

  // Network capacity: Reference shows 100 total partitions across all sources
  const TOTAL_NETWORK_PARTITIONS = 100.0;
  const partitionUtilization = totalPartitions / TOTAL_NETWORK_PARTITIONS;

  // Scale by number of inbound feeds (each inbound has a matching outbound)
  // Base costs already account for the pair, so multiply by inbound count only
  const confluentCost = baseConfluentAnnual * totalInboundFeeds;
  const gcpCost = baseGcpAnnual * totalInboundFeeds;

  // Network costs scale with partition usage
  const baseNetworkAnnual = 120000; // $10k/month baseline
  const networkCost = baseNetworkAnnual * partitionUtilization;

  const firstYearCloudCost = confluentCost + gcpCost + networkCost;

  const initialInvestment: YearlyROMCost[] = [
    {
      year: config.startYear,
      dataEngineering: oneTimeDevelopment,
      cloudInfrastructure: firstYearCloudCost,
      total: oneTimeDevelopment + firstYearCloudCost,
    },
  ];

  const operatingVariance: YearlyROMCost[] = [];
  let cloudInfrastructure7Year = firstYearCloudCost;
  let operatingVariance6Year = 0;

  for (let i = 1; i <= 6; i++) {
    const year = config.startYear + i;
    const escalatedCloudCost = firstYearCloudCost * Math.pow(1 + config.escalationRate, i);
    cloudInfrastructure7Year += escalatedCloudCost;
    operatingVariance6Year += escalatedCloudCost;

    operatingVariance.push({
      year,
      dataEngineering: 0,
      cloudInfrastructure: escalatedCloudCost,
      total: escalatedCloudCost,
    });
  }

  const totalProjectCost = oneTimeDevelopment + cloudInfrastructure7Year;

  return {
    initialInvestment,
    operatingVariance,
    totalFeeds,
    totalPartitions,
    totalInboundFeeds,
    totalOutboundFeeds,
    feedConfigs,
    recordsPerDay,
    partitionUtilizationPct: partitionUtilization * 100,
    breakdown: {
      inboundCost,
      outboundCost,
      normalizationCost,
      workspaceSetup,
      confluentCost,
      gcpCost,
      networkCost,
      oneTimeDevelopment,
      cloudInfrastructure7Year,
      operatingVariance6Year,
      totalProjectCost,
      firstYearCloudCost,
    },
  };
}

export function generateROMExport(config: ROMConfig): string {
  const results = calculateROMCosts(config);
  const lines: string[] = [];

  lines.push('Confluent Feed ROM - Rough Order of Magnitude');
  lines.push('');

  const years = [
    config.startYear,
    config.startYear + 1,
    config.startYear + 2,
    config.startYear + 3,
    config.startYear + 4,
    config.startYear + 5,
    config.startYear + 6,
    config.startYear + 7,
    config.startYear + 8,
    config.startYear + 9,
    config.startYear + 10,
    config.startYear + 11,
  ];
  lines.push('Fiscal Year,' + years.join(',') + ',Total');

  lines.push('INITIAL INVESTMENT EXPENSE');
  const initialDE = results.initialInvestment[0].dataEngineering;
  const deLine = `Data Engineering,${formatInThousands(initialDE)}` + ',,,,,,,,,,,' + `,${formatInThousands(initialDE)}`;
  lines.push(deLine);

  lines.push('Data Strategy and Governance,,,,,,,,,,,,$-');
  lines.push('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-');
  lines.push('Advance Modeling,,,,,,,,,,,,$-');
  lines.push('Service Performance,,,,,,,,,,,,$-');

  const initialCloud = results.initialInvestment[0].cloudInfrastructure;
  const cloudLine = 'GCP/GKE/Confluent';
  const cloudCosts = results.operatingVariance.map((ov) => formatInThousands(ov.cloudInfrastructure));
  lines.push(
    `${cloudLine},${formatInThousands(initialCloud)},${cloudCosts.join(',')},,,,,,${formatInThousands(results.breakdown.cloudInfrastructure7Year)}`
  );

  const initialTotal = results.initialInvestment[0].total;
  const totalLine = `TOTAL,${formatInThousands(initialTotal)},${cloudCosts.join(',')},,,,,,${formatInThousands(results.breakdown.totalProjectCost)}`;
  lines.push(totalLine);

  lines.push('');
  lines.push('');

  lines.push('Fiscal Year,' + years.join(',') + ',Total');
  lines.push('OPERATING VARIANCE');

  const opVarLine = 'Data Engineering';
  const opVarCosts = results.operatingVariance.map((ov) => formatInThousands(ov.cloudInfrastructure));
  lines.push(`${opVarLine},,${opVarCosts.join(',')},,,,,,${formatInThousands(results.breakdown.operatingVariance6Year)}`);

  lines.push('Data Strategy and Governance,,,,,,,,,,,,$-');
  lines.push('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-');
  lines.push('Advance Modeling,,,,,,,,,,,,$-');
  lines.push('Service Performance,,,,,,,,,,,,$-');

  const opVarTotal = `TOTAL,,${opVarCosts.join(',')},,,,,,${formatInThousands(results.breakdown.operatingVariance6Year)}`;
  lines.push(opVarTotal);

  lines.push('');
  lines.push('');

  lines.push('Summary');
  lines.push(`Capital,$-`);
  lines.push(`Expense,${formatInThousands(results.breakdown.totalProjectCost)}`);
  lines.push(`Variance,${formatInThousands(results.breakdown.operatingVariance6Year)}`);
  lines.push(`Total,${formatInThousands(results.breakdown.totalProjectCost)}`);

  lines.push('');
  lines.push('');
  lines.push(`Escalation Rate,${(config.escalationRate * 100).toFixed(1)}%`);

  lines.push('');
  lines.push('Note*');
  lines.push('"Estimate based on latest Payroll 2.0 scaling factors"');
  lines.push('"ROM may require revision as detailed requirements are finalized"');

  lines.push('');
  lines.push('Assumptions:');
  lines.push(`1,ROM covers ${results.totalFeeds} EEB ingest feed(s) with inbound/outbound data processing capabilities`);
  lines.push(`2,Feed ingests data with complex processing requirements`);
  lines.push(`3,Includes event data with facility impacts and workflow approvals`);
  lines.push(`4,Feed includes data normalization and standardization requirements`);
  lines.push(`5,Workspace/Environment setup costs included`);
  lines.push(`6,Confluent platform required for real-time streaming: ${formatInThousands(config.confluentAnnualCost)} per feed per year`);
  lines.push(`7,GCP/GKE infrastructure cost: ${formatInThousands(config.gcpPerFeedAnnualCost)} per feed per year for compute and storage`);
  lines.push(`8,ROM based on current understanding of high level requirements & known attributes`);
  lines.push(`9,As requirements are refined/finalized the ROM may need to be revised`);

  lines.push('');
  lines.push('Timeline');
  lines.push(`FY${config.startYear}-FY${config.startYear + 6}`);
  lines.push(`12,FY${config.startYear}: ${formatInThousands(initialTotal)} (Data Engineering + Cloud infrastructure setup - starting in 3 weeks)`);
  lines.push(`13,FY${config.startYear + 1}-${config.startYear + 6}: ${formatInThousands(results.breakdown.operatingVariance6Year / 6)} annually (ongoing cloud operations with ${(config.escalationRate * 100).toFixed(1)}% escalation) plus Operating Variance`);

  lines.push('');
  lines.push('Cost Breakdown per Feed:');
  lines.push(`14,Create inbound ingest: ${formatInThousands(config.inboundHours * config.deHourlyRate)},${Math.round(config.inboundHours)} (${Math.round(config.inboundHours)} hours)`);
  lines.push(`15,Create outbound enterprise data assets: ${formatInThousands(config.outboundHours * config.deHourlyRate)},${Math.round(config.outboundHours)} (${Math.round(config.outboundHours)} hours)`);
  lines.push(`16,Data normalization and standardization: ${formatInThousands(results.breakdown.normalizationCost)},${Math.round(config.normalizationHours)} (${config.normalizationHours} hours - ${results.totalFeeds} feeds)`);
  lines.push(`17,Workspace/Environment/Subscription Prep: ${formatInThousands(config.workspaceSetupCost)}`);
  lines.push(`18,Annual Confluent platform cost: ${formatInThousands(config.confluentAnnualCost)},${Math.round(config.confluentAnnualCost)}`);
  lines.push(`19,Annual GCP/GKE cost: ${formatInThousands(config.gcpPerFeedAnnualCost)},${Math.round(config.gcpPerFeedAnnualCost)} per feed`);

  lines.push('');
  lines.push(`Total ${results.totalFeeds}-Feed Investment`);
  lines.push(`${results.totalFeeds}-Feed Investment`);
  lines.push(`21,Data Engineering: ${formatInThousands(results.breakdown.oneTimeDevelopment)},${Math.round(results.breakdown.oneTimeDevelopment / 1000)} (one-time development)`);
  lines.push(`22,Cloud Infrastructure: ${formatInThousands(results.breakdown.cloudInfrastructure7Year)},${Math.round(results.breakdown.cloudInfrastructure7Year / 1000)} (7-year operational costs with ${(config.escalationRate * 100).toFixed(1)}% escalation)`);
  lines.push(`23,Operating Variance: ${formatInThousands(results.breakdown.operatingVariance6Year)},${Math.round(results.breakdown.operatingVariance6Year / 1000)} (6-year escalated costs)`);
  lines.push(`24,Total Project Cost: ${formatInThousands(results.breakdown.totalProjectCost)},${Math.round(results.breakdown.totalProjectCost / 1000)}`);

  return lines.join('\n');
}
