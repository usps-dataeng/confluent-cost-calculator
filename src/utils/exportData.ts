interface CostData {
  compute: number;
  storage: number;
  network: number;
  totalYearly: number;
  totalMonthly: number;
}

interface ExportConfig {
  selectedSize: string;
  partitions: number;
  storageGB: number;
  yearlyComputeCost: number;
  yearlyStorageCost: number;
  costs: CostData;
  annualIncreaseRate?: number;
}

export function generateCostProjectionCSV(config: ExportConfig): string {
  const {
    selectedSize,
    partitions,
    storageGB,
    costs,
    annualIncreaseRate = 0.03
  } = config;

  const currentYear = new Date().getFullYear();
  const monthlyIncreaseRate = 0.034;
  const csvRows: string[] = [];

  csvRows.push('Confluent Cloud Cost Calculator - 7 Year Projection');
  csvRows.push('');
  csvRows.push(`T-Shirt Size:,${selectedSize}`);
  csvRows.push(`Partitions:,${partitions}`);
  csvRows.push(`Storage (GB):,${storageGB}`);
  csvRows.push(`Annual Increase Rate:,${(annualIncreaseRate * 100).toFixed(1)}%`);
  csvRows.push(`Monthly Increase Rate:,${(monthlyIncreaseRate * 100).toFixed(1)}%`);
  csvRows.push('');

  csvRows.push('Current Year Cost Breakdown');
  csvRows.push('Category,Annual Cost,Monthly Cost');
  csvRows.push(`Compute,$${costs.compute.toFixed(2)},$${(costs.compute / 12).toFixed(2)}`);
  csvRows.push(`Storage,$${costs.storage.toFixed(2)},$${(costs.storage / 12).toFixed(2)}`);
  csvRows.push(`Network,$${costs.network.toFixed(2)},$${(costs.network / 12).toFixed(2)}`);
  csvRows.push(`Total,$${costs.totalYearly.toFixed(2)},$${costs.totalMonthly.toFixed(2)}`);
  csvRows.push('');

  csvRows.push('7-Year Cost Projection');
  csvRows.push('Year,Compute Cost,Storage Cost,Network Cost,Total Annual Cost,Cumulative Cost');

  let cumulativeCost = 0;

  for (let year = 0; year < 7; year++) {
    const yearLabel = currentYear + year;
    const multiplier = Math.pow(1 + annualIncreaseRate, year);

    const computeCost = costs.compute * multiplier;
    const storageCost = costs.storage * multiplier;
    const networkCost = costs.network * multiplier;
    const totalCost = computeCost + storageCost + networkCost;

    cumulativeCost += totalCost;

    csvRows.push(
      `${yearLabel},` +
      `$${computeCost.toFixed(2)},` +
      `$${storageCost.toFixed(2)},` +
      `$${networkCost.toFixed(2)},` +
      `$${totalCost.toFixed(2)},` +
      `$${cumulativeCost.toFixed(2)}`
    );
  }

  csvRows.push('');
  csvRows.push('Monthly Breakdown by Year');
  csvRows.push('Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,Annual Total');

  for (let year = 0; year < 7; year++) {
    const yearLabel = currentYear + year;
    const baseMonthly = costs.totalMonthly;
    const monthlyValues: string[] = [];
    let annualTotal = 0;

    for (let month = 0; month < 12; month++) {
      const monthsFromStart = year * 12 + month;
      const multiplier = Math.pow(1 + monthlyIncreaseRate, monthsFromStart);
      const monthlyCost = baseMonthly * multiplier;
      monthlyValues.push(`$${monthlyCost.toFixed(2)}`);
      annualTotal += monthlyCost;
    }

    csvRows.push(`${yearLabel},${monthlyValues.join(',')},$${annualTotal.toFixed(2)}`);
  }

  return csvRows.join('\n');
}

export function downloadCSV(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

export function generateExportFilename(): string {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0];
  return `confluent-cost-projection-${dateStr}.csv`;
}
