import { useState, useEffect } from 'react';
import { Calculator, Server, Database, Network, DollarSign, TrendingUp, Upload, Settings, Download } from 'lucide-react';
import { parseCSV, ParsedData } from './utils/csvParser';
import { generateCostProjectionCSV, downloadCSV, generateExportFilename } from './utils/exportData';
import topicListCSV from './assets/Topic_list.csv?raw';

interface TShirtSize {
  partitions: number;
  storageGB: number;
}

const DEFAULT_TSHIRT_SIZES: Record<string, TShirtSize> = {
  Small: { partitions: 6, storageGB: 15 },
  Medium: { partitions: 24, storageGB: 100 },
  Large: { partitions: 50, storageGB: 250 },
  'X-Large': { partitions: 100, storageGB: 1000 },
  'XX-Large': { partitions: 197, storageGB: 2500 },
};

function App() {
  const [selectedSize, setSelectedSize] = useState<string>('Medium');
  const [yearlyComputeCost, setYearlyComputeCost] = useState<string>('500000');
  const [yearlyStorageCost, setYearlyStorageCost] = useState<string>('200000');
  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [tshirtSizes, setTshirtSizes] = useState<Record<string, TShirtSize>>(DEFAULT_TSHIRT_SIZES);
  const [showSettings, setShowSettings] = useState(false);
  const [editingSizes, setEditingSizes] = useState<Record<string, TShirtSize>>(DEFAULT_TSHIRT_SIZES);
  const [annualIncreaseRate, setAnnualIncreaseRate] = useState<string>('3');

  useEffect(() => {
    const data = parseCSV(topicListCSV);
    setParsedData(data);
  }, []);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const data = parseCSV(text);
        setParsedData(data);
      };
      reader.readAsText(file);
    }
  };

  const handleSaveSettings = () => {
    setTshirtSizes(editingSizes);
    setShowSettings(false);
  };

  const handleResetSettings = () => {
    setEditingSizes(DEFAULT_TSHIRT_SIZES);
    setTshirtSizes(DEFAULT_TSHIRT_SIZES);
  };

  const handleExport = () => {
    const csvContent = generateCostProjectionCSV({
      selectedSize,
      partitions: sizeConfig.partitions,
      storageGB: sizeConfig.storageGB,
      yearlyComputeCost: parseFloat(yearlyComputeCost) || 0,
      yearlyStorageCost: parseFloat(yearlyStorageCost) || 0,
      costs,
      annualIncreaseRate: parseFloat(annualIncreaseRate) / 100 || 0.03,
    });

    const filename = generateExportFilename();
    downloadCSV(csvContent, filename);
  };

  if (!parsedData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading data...</div>
      </div>
    );
  }

  const TOTAL_PARTITIONS = parsedData.totalPartitions;
  const TOTAL_STORAGE_GB = parsedData.totalStorageGB;

  const calculateCosts = () => {
    const size = tshirtSizes[selectedSize];
    if (!size) return { compute: 0, storage: 0, network: 0, totalYearly: 0, totalMonthly: 0 };

    const compute = parseFloat(yearlyComputeCost) || 0;
    const storage = parseFloat(yearlyStorageCost) || 0;

    const computeCost = (size.partitions / TOTAL_PARTITIONS) * compute;
    const storageCost = (size.storageGB / TOTAL_STORAGE_GB) * storage;
    const networkCost = 0.75 * storage;

    const totalYearly = computeCost + storageCost + networkCost;
    const totalMonthly = totalYearly / 12;

    return {
      compute: computeCost,
      storage: storageCost,
      network: networkCost,
      totalYearly,
      totalMonthly,
    };
  };

  const costs = calculateCosts();
  const sizeConfig = tshirtSizes[selectedSize];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Calculator className="w-10 h-10 text-blue-400" />
                <h1 className="text-4xl font-bold text-white">Confluent Cloud Cost Calculator</h1>
              </div>
              <p className="text-slate-400 text-lg">T-Shirt Sizing ROM (Rough Order of Magnitude)</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                <Download className="w-5 h-5" />
                <span>Export 7-Year</span>
              </button>
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                  <Upload className="w-5 h-5" />
                  <span>Upload CSV</span>
                </div>
              </label>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5" />
                <span>Settings</span>
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Server className="w-6 h-6 text-blue-400" />
              <h3 className="text-lg font-semibold text-white">Total Resources</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-slate-400 text-sm">Total Partitions</div>
                <div className="text-2xl font-bold text-white">{TOTAL_PARTITIONS.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-slate-400 text-sm">Total Storage</div>
                <div className="text-2xl font-bold text-white">{TOTAL_STORAGE_GB.toLocaleString()} GB</div>
                <div className="text-slate-400 text-xs">{(TOTAL_STORAGE_GB / 1024).toFixed(2)} TB</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <DollarSign className="w-6 h-6 text-green-400" />
              <h3 className="text-lg font-semibold text-white">Yearly Costs</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-slate-400 text-sm block mb-2">Compute Cost</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                  <input
                    type="number"
                    value={yearlyComputeCost}
                    onChange={(e) => setYearlyComputeCost(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-600 rounded-lg pl-8 pr-4 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="text-slate-400 text-sm block mb-2">Storage Cost</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                  <input
                    type="number"
                    value={yearlyStorageCost}
                    onChange={(e) => setYearlyStorageCost(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-600 rounded-lg pl-8 pr-4 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="text-slate-400 text-sm block mb-2">Annual Increase Rate (%)</label>
                <div className="relative">
                  <input
                    type="number"
                    value={annualIncreaseRate}
                    onChange={(e) => setAnnualIncreaseRate(e.target.value)}
                    step="0.1"
                    min="0"
                    max="100"
                    className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">%</span>
                </div>
                <div className="text-xs text-slate-500 mt-1">Used for 7-year cost projection</div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 text-white">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="w-6 h-6" />
              <h3 className="text-lg font-semibold">Estimated Total Cost</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-blue-100 text-sm">Monthly</div>
                <div className="text-3xl font-bold">${costs.totalMonthly.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
              </div>
              <div className="border-t border-blue-500 pt-3">
                <div className="text-blue-100 text-sm">Yearly</div>
                <div className="text-2xl font-bold">${costs.totalYearly.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
              </div>
            </div>
          </div>
        </div>

        {showSettings && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white">T-Shirt Size Configuration</h3>
              <div className="flex gap-3">
                <button
                  onClick={handleResetSettings}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm"
                >
                  Reset to Defaults
                </button>
                <button
                  onClick={handleSaveSettings}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                >
                  Save Changes
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.keys(editingSizes).map((sizeName) => (
                <div key={sizeName} className="bg-slate-900 p-4 rounded-lg">
                  <div className="text-white font-semibold mb-3">{sizeName}</div>
                  <div className="space-y-3">
                    <div>
                      <label className="text-slate-400 text-sm block mb-1">Partitions</label>
                      <input
                        type="number"
                        value={editingSizes[sizeName].partitions}
                        onChange={(e) => setEditingSizes({
                          ...editingSizes,
                          [sizeName]: { ...editingSizes[sizeName], partitions: parseInt(e.target.value) || 0 }
                        })}
                        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 text-sm block mb-1">Storage (GB)</label>
                      <input
                        type="number"
                        value={editingSizes[sizeName].storageGB}
                        onChange={(e) => setEditingSizes({
                          ...editingSizes,
                          [sizeName]: { ...editingSizes[sizeName], storageGB: parseInt(e.target.value) || 0 }
                        })}
                        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
          <h3 className="text-xl font-semibold text-white mb-6">Select T-Shirt Size</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.keys(tshirtSizes).map((size) => {
              const config = tshirtSizes[size];
              const isSelected = selectedSize === size;
              return (
                <button
                  key={size}
                  onClick={() => setSelectedSize(size)}
                  className={`p-6 rounded-xl border-2 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-500/20 shadow-lg shadow-blue-500/20'
                      : 'border-slate-600 bg-slate-900 hover:border-slate-500'
                  }`}
                >
                  <div className="text-center">
                    <div className={`text-2xl font-bold mb-2 ${isSelected ? 'text-blue-400' : 'text-white'}`}>
                      {size}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="text-slate-400">
                        <span className="font-semibold text-white">{config.partitions}</span> partitions
                      </div>
                      <div className="text-slate-400">
                        <span className="font-semibold text-white">{config.storageGB}</span> GB
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Size Configuration</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg">
                <div>
                  <div className="text-slate-400 text-sm">Partitions Needed</div>
                  <div className="text-2xl font-bold text-white">{sizeConfig.partitions}</div>
                </div>
                <Server className="w-8 h-8 text-blue-400" />
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg">
                <div>
                  <div className="text-slate-400 text-sm">Storage Needed</div>
                  <div className="text-2xl font-bold text-white">{sizeConfig.storageGB} GB</div>
                </div>
                <Database className="w-8 h-8 text-green-400" />
              </div>
              <div className="p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
                <div className="text-blue-300 text-sm mb-1">Utilization Percentages</div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-slate-300">
                    <span>Compute:</span>
                    <span className="font-semibold">
                      {((sizeConfig.partitions / TOTAL_PARTITIONS) * 100).toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Storage:</span>
                    <span className="font-semibold">
                      {((sizeConfig.storageGB / TOTAL_STORAGE_GB) * 100).toFixed(3)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Cost Breakdown</h3>
            <div className="space-y-3">
              <div className="p-4 bg-slate-900 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Server className="w-5 h-5 text-blue-400" />
                    <span className="text-slate-300">Compute Cost</span>
                  </div>
                  <span className="text-white font-semibold">
                    ${costs.compute.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  ({sizeConfig.partitions} / {TOTAL_PARTITIONS.toLocaleString()}) × ${parseFloat(yearlyComputeCost).toLocaleString()}
                </div>
              </div>

              <div className="p-4 bg-slate-900 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-green-400" />
                    <span className="text-slate-300">Storage Cost</span>
                  </div>
                  <span className="text-white font-semibold">
                    ${costs.storage.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  ({sizeConfig.storageGB} / {TOTAL_STORAGE_GB.toLocaleString()}) × ${parseFloat(yearlyStorageCost).toLocaleString()}
                </div>
              </div>

              <div className="p-4 bg-slate-900 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Network className="w-5 h-5 text-amber-400" />
                    <span className="text-slate-300">Network Cost</span>
                  </div>
                  <span className="text-white font-semibold">
                    ${costs.network.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  0.75 × ${parseFloat(yearlyStorageCost).toLocaleString()}
                </div>
              </div>

              <div className="p-4 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg mt-4">
                <div className="flex items-center justify-between">
                  <span className="text-white font-semibold text-lg">Total Yearly Cost</span>
                  <span className="text-white font-bold text-xl">
                    ${costs.totalYearly.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Formula Reference</h3>
          <div className="space-y-3 text-sm">
            <div className="p-4 bg-slate-900 rounded-lg font-mono">
              <div className="text-blue-400 mb-2">Compute Cost Formula:</div>
              <div className="text-slate-300">
                (number of partitions needed / Total partitions) × Total yearly compute cost
              </div>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg font-mono">
              <div className="text-green-400 mb-2">Storage Cost Formula:</div>
              <div className="text-slate-300">
                (storage needed / Total Storage) × Total yearly Storage Cost
              </div>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg font-mono">
              <div className="text-amber-400 mb-2">Network Cost Formula:</div>
              <div className="text-slate-300">0.75 × Total yearly Storage Cost</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;