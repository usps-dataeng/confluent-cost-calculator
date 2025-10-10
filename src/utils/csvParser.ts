export interface TopicData {
  name: string;
  partitions: number;
  storageBytes: number;
  storageGB: number;
}

export interface ParsedData {
  topics: TopicData[];
  totalPartitions: number;
  totalStorageGB: number;
  totalStorageTB: number;
}

export function parseCSV(csvText: string): ParsedData {
  const lines = csvText.split('\n').filter(line => line.trim());
  const topics: TopicData[] = [];
  let totalPartitions = 0;
  let totalStorageBytes = 0;

  for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(',');
    const name = parts[0]?.trim() || '';
    const partitions = parseInt(parts[2]) || 0;
    const storage = parts[5]?.trim() || '';

    totalPartitions += partitions;

    let bytes = 0;
    if (storage) {
      if (storage.includes('TB')) {
        bytes = parseFloat(storage) * 1024 * 1024 * 1024 * 1024;
      } else if (storage.includes('GB')) {
        bytes = parseFloat(storage) * 1024 * 1024 * 1024;
      } else if (storage.includes('MB')) {
        bytes = parseFloat(storage) * 1024 * 1024;
      } else if (storage.includes('KB')) {
        bytes = parseFloat(storage) * 1024;
      } else if (storage.includes('B') && !storage.includes('KB') && !storage.includes('MB')) {
        bytes = parseFloat(storage);
      }
    }

    totalStorageBytes += bytes;

    if (name) {
      topics.push({
        name,
        partitions,
        storageBytes: bytes,
        storageGB: bytes / (1024 * 1024 * 1024),
      });
    }
  }

  const totalStorageGB = totalStorageBytes / (1024 * 1024 * 1024);
  const totalStorageTB = totalStorageGB / 1024;

  return {
    topics,
    totalPartitions,
    totalStorageGB: Math.round(totalStorageGB * 100) / 100,
    totalStorageTB: Math.round(totalStorageTB * 100) / 100,
  };
}
