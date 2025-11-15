export interface ParsedData {
  totalPartitions: number;
  totalStorageGB: number;
  topics: Array<{
    name: string;
    partitions: number;
    storageGB: number;
  }>;
}

function parseStorageValue(storage: string): number {
  if (!storage || storage === '0B') return 0;

  const match = storage.match(/^([\d.]+)(TB|GB|MB|KB|B)$/);
  if (!match) return 0;

  const value = parseFloat(match[1]);
  const unit = match[2];

  switch (unit) {
    case 'TB': return value * 1024;
    case 'GB': return value;
    case 'MB': return value / 1024;
    case 'KB': return value / (1024 * 1024);
    case 'B': return value / (1024 * 1024 * 1024);
    default: return 0;
  }
}

export function parseCSV(csvContent: string): ParsedData {
  const lines = csvContent.trim().split('\n');
  const topics: ParsedData['topics'] = [];
  let totalPartitions = 0;
  let totalStorageGB = 0;

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const columns = line.split(',');
    if (columns.length < 6) continue;

    const name = columns[0];
    const partitions = parseInt(columns[2]) || 0;
    const storageStr = columns[5] || '0B';
    const storageGB = parseStorageValue(storageStr);

    if (name && partitions > 0) {
      topics.push({ name, partitions, storageGB });
      totalPartitions += partitions;
      totalStorageGB += storageGB;
    }
  }

  return {
    totalPartitions,
    totalStorageGB,
    topics
  };
}
