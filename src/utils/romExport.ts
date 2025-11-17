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
}

interface YearlyROMCost {
  year: number;
  dataEngineering: number;
  cloudInfrastructure: number;
  total: number;
}

function calculateROMCosts(config: ROMConfig): {
  initialInvestment: YearlyROMCost[];
  operatingVariance: YearlyROMCost[];
  totalFeeds: number;
  breakdown: {
    inboundCost: number;
    outboundCost: number;
    normalizationCost: number;
    workspaceSetup: number;
    confluentCost: number;
    gcpCost: number;
    oneTimeDevelopment: number;
    cloudInfrastructure7Year: number;
    operatingVariance6Year: number;
    totalProjectCost: number;
  };
} {
  const totalFeeds = config.inboundFeeds + config.outboundFeeds;

  const inboundCost = config.inboundFeeds * config.inboundHours * config.deHourlyRate;
  const outboundCost = config.outboundFeeds * config.outboundHours * config.deHourlyRate;
  const normalizationCost = config.normalizationHours * config.deHourlyRate;
  const workspaceSetup = config.workspaceSetupCost;

  const oneTimeDevelopment = inboundCost + outboundCost + normalizationCost + workspaceSetup;

  const confluentCost = config.confluentAnnualCost;
  const gcpCost = totalFeeds * config.gcpPerFeedAnnualCost;
  const firstYearCloudCost = confluentCost + gcpCost;

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
    breakdown: {
      inboundCost,
      outboundCost,
      normalizationCost,
      workspaceSetup,
      confluentCost,
      gcpCost,
      oneTimeDevelopment,
      cloudInfrastructure7Year,
      operatingVariance6Year,
      totalProjectCost,
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
  const deLine = `Data Engineering,$${initialDE.toLocaleString()}` + ',,,,,,,,,,,' + `,$${initialDE.toLocaleString()}`;
  lines.push(deLine);

  lines.push('Data Strategy and Governance,,,,,,,,,,,,$-');
  lines.push('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-');
  lines.push('Advance Modeling,,,,,,,,,,,,$-');
  lines.push('Service Performance,,,,,,,,,,,,$-');

  const initialCloud = results.initialInvestment[0].cloudInfrastructure;
  const cloudLine = 'Google Cloud Platform (GCP)';
  const cloudCosts = results.operatingVariance.map((ov) => `$${Math.round(ov.cloudInfrastructure).toLocaleString()}`);
  lines.push(
    `${cloudLine},$${Math.round(initialCloud).toLocaleString()},${cloudCosts.join(',')},,,,,,$${Math.round(results.breakdown.cloudInfrastructure7Year).toLocaleString()}`
  );

  const initialTotal = results.initialInvestment[0].total;
  const totalLine = `TOTAL,$${Math.round(initialTotal).toLocaleString()},${cloudCosts.join(',')},,,,,,$${Math.round(results.breakdown.totalProjectCost).toLocaleString()}`;
  lines.push(totalLine);

  lines.push('');
  lines.push('');

  lines.push('Fiscal Year,' + years.join(',') + ',Total');
  lines.push('OPERATING VARIANCE');

  const opVarLine = 'Data Engineering';
  const opVarCosts = results.operatingVariance.map((ov) => `$${Math.round(ov.cloudInfrastructure).toLocaleString()}`);
  lines.push(`${opVarLine},,${ opVarCosts.join(',')},,,,,,$${Math.round(results.breakdown.operatingVariance6Year).toLocaleString()}`);

  lines.push('Data Strategy and Governance,,,,,,,,,,,,$-');
  lines.push('Enterprise Reporting and Dashboard,,,,,,,,,,,,$-');
  lines.push('Advance Modeling,,,,,,,,,,,,$-');
  lines.push('Service Performance,,,,,,,,,,,,$-');

  const opVarTotal = `TOTAL,,${ opVarCosts.join(',')},,,,,,$${Math.round(results.breakdown.operatingVariance6Year).toLocaleString()}`;
  lines.push(opVarTotal);

  lines.push('');
  lines.push('');

  lines.push('Summary');
  lines.push(`Capital,$-`);
  lines.push(`Expense,$${Math.round(results.breakdown.totalProjectCost).toLocaleString()}`);
  lines.push(`Variance,$${Math.round(results.breakdown.operatingVariance6Year).toLocaleString()}`);
  lines.push(`Total,$${Math.round(results.breakdown.totalProjectCost).toLocaleString()}`);

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
  lines.push(`6,Confluent platform required for real-time streaming: $${config.confluentAnnualCost.toLocaleString()} per feed per year`);
  lines.push(`7,GCP/GKE infrastructure cost: $${config.gcpPerFeedAnnualCost.toLocaleString()} per feed per year for compute and storage`);
  lines.push(`8,ROM based on current understanding of high level requirements & known attributes`);
  lines.push(`9,As requirements are refined/finalized the ROM may need to be revised`);

  lines.push('');
  lines.push('Timeline');
  lines.push(`FY${config.startYear}-FY${config.startYear + 5}`);
  lines.push(`12,FY${config.startYear}: $${Math.round(initialTotal).toLocaleString()} (Data Engineering + Cloud infrastructure setup - starting in 3 weeks)`);
  lines.push(`13,FY${config.startYear + 1}-${config.startYear + 5}: $${Math.round(results.breakdown.operatingVariance6Year / 6).toLocaleString()} annually (ongoing cloud operations with ${(config.escalationRate * 100).toFixed(1)}% escalation) plus Operating Variance`);

  lines.push('');
  lines.push('Cost Breakdown per Feed:');
  lines.push(`14,Create inbound ingest: $${Math.round(config.inboundHours * config.deHourlyRate).toLocaleString()} (${config.inboundHours} hours)`);
  lines.push(`15,Create outbound enterprise data assets: $${Math.round(config.outboundHours * config.deHourlyRate).toLocaleString()} (${config.outboundHours} hours)`);
  lines.push(`16,Data normalization and standardization: $${Math.round(results.breakdown.normalizationCost).toLocaleString()} (${config.normalizationHours} hours - ${results.totalFeeds} feeds)`);
  lines.push(`17,Workspace/Environment/Subscription Prep: $${config.workspaceSetupCost.toLocaleString()}`);
  lines.push(`18,Annual Confluent platform cost: $${config.confluentAnnualCost.toLocaleString()}`);
  lines.push(`19,Annual GCP/GKE cost: $${config.gcpPerFeedAnnualCost.toLocaleString()} per feed`);

  lines.push('');
  lines.push(`Total ${results.totalFeeds}-Feed Investment`);
  lines.push(`1-Feed Investment`);
  lines.push(`21,Data Engineering: $${Math.round(results.breakdown.oneTimeDevelopment).toLocaleString()} (one-time development)`);
  lines.push(`18,Cloud Infrastructure: $${Math.round(results.breakdown.cloudInfrastructure7Year).toLocaleString()} (7-year operational costs with ${(config.escalationRate * 100).toFixed(1)}% escalation)`);
  lines.push(`19,Operating Variance: $${Math.round(results.breakdown.operatingVariance6Year).toLocaleString()} (6-year escalated costs)`);
  lines.push(`20,Total Project Cost: $${Math.round(results.breakdown.totalProjectCost).toLocaleString()}`);

  return lines.join('\n');
}
