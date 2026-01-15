import { useState, useEffect } from 'react';
import { Calculator, Server, Database, Network, DollarSign, TrendingUp, Upload, Settings, Download, Shield, FileSpreadsheet } from 'lucide-react';
import { parseCSV, ParsedData } from './utils/csvParser';
import { generateCostProjectionCSV, downloadCSV, generateExportFilename } from './utils/exportData';
import { generateROMExport, calculateROMCosts, ROMConfig } from './utils/romExport';
import topicListCSV from './assets/Topic_list.csv?raw';

interface TShirtSize {
  partitions: number;
  storageGB: number;
}

interface CKUConfig {
  azureCKUs: number;
  azureRate: number;
  gcpCKUs: number;
  gcpRate: number;
}

interface FlatCosts {
  storage: number;
  network: number;
  networkMultiplier: number;
  governance: number;
}

const DEFAULT_TSHIRT_SIZES: Record<string, TShirtSize> = {
  Small: { partitions: 6, storageGB: 15 },
  Medium: { partitions: 24, storageGB: 100 },
  Large: { partitions: 50, storageGB: 250 },
  'X-Large': { partitions: 100, storageGB: 1000 },
  'XX-Large': { partitions: 197, storageGB: 2500 },
};

const DEFAULT_CKU_CONFIG: CKUConfig = {
  azureCKUs: 14,
  azureRate: 1925,
  gcpCKUs: 28,
  gcpRate: 1585,
};

const DEFAULT_FLAT_COSTS: FlatCosts = {
  storage: 180000,
  network: 120000,
  networkMultiplier: 0.75,
  governance: 42840,
};

const DEFAULT_ROM_CONFIG: ROMConfig = {
  inboundFeeds: 12,
  outboundFeeds: 12,
  deHourlyRate: 80,
  inboundHours: 296,
  outboundHours: 254,
  normalizationHours: 27.9,
  workspaceSetupCost: 8000,
  confluentAnnualCost: 11709,
  gcpPerFeedAnnualCost: 9279,
  escalationRate: 0.034,
  startYear: new Date().getFullYear(),
  recordsPerDay: 5000,
  numIngests: 12,
  feedConfigs: Array.from({ length: 12 }, () => ({ inbound: 1, outbound: 1, partitions: 0.048 })),
};

function App() {
  const [selectedSize, setSelectedSize] = useState<string>('Medium');
  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [tshirtSizes, setTshirtSizes] = useState<Record<string, TShirtSize>>(DEFAULT_TSHIRT_SIZES);
  const [ckuConfig, setCkuConfig] = useState<CKUConfig>(DEFAULT_CKU_CONFIG);
  const [flatCosts, setFlatCosts] = useState<FlatCosts>(DEFAULT_FLAT_COSTS);
  const [showSettings, setShowSettings] = useState(false);
  const [showCostSettings, setShowCostSettings] = useState(false);
  const [showROMSettings, setShowROMSettings] = useState(false);
  const [romConfig, setRomConfig] = useState<ROMConfig>(DEFAULT_ROM_CONFIG);
  const [editingROM, setEditingROM] = useState<ROMConfig>(DEFAULT_ROM_CONFIG);
  const [editingSizes, setEditingSizes] = useState<Record<string, TShirtSize>>(DEFAULT_TSHIRT_SIZES);
  const [editingCKU, setEditingCKU] = useState<CKUConfig>(DEFAULT_CKU_CONFIG);
  const [editingFlatCosts, setEditingFlatCosts] = useState<FlatCosts>(DEFAULT_FLAT_COSTS);
  const [annualIncreaseRate, setAnnualIncreaseRate] = useState<string>('3.4');

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

  const handleSaveCostSettings = () => {
    setCkuConfig(editingCKU);
    setFlatCosts(editingFlatCosts);
    setShowCostSettings(false);
  };

  const handleResetSettings = () => {
    setEditingSizes(DEFAULT_TSHIRT_SIZES);
    setTshirtSizes(DEFAULT_TSHIRT_SIZES);
  };

  const handleResetCostSettings = () => {
    setEditingCKU(DEFAULT_CKU_CONFIG);
    setEditingFlatCosts(DEFAULT_FLAT_COSTS);
    setCkuConfig(DEFAULT_CKU_CONFIG);
    setFlatCosts(DEFAULT_FLAT_COSTS);
  };

  const handleSaveROMSettings = () => {
    setRomConfig(editingROM);
    setShowROMSettings(false);
  };

  const handleResetROMSettings = () => {
    setEditingROM(DEFAULT_ROM_CONFIG);
    setRomConfig(DEFAULT_ROM_CONFIG);
  };

  const handleExportROM = () => {
    const csvContent = generateROMExport(romConfig);
    const filename = `confluent-rom-${romConfig.startYear}-${new Date().toISOString().split('T')[0]}.csv`;
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
    if (!size) return { compute: 0, storage: 0, network: 0, governance: 0, totalYearly: 0, totalMonthly: 0 };

    const azureAnnual = ckuConfig.azureCKUs * ckuConfig.azureRate * 12;
    const gcpAnnual = ckuConfig.gcpCKUs * ckuConfig.gcpRate * 12;
    const totalCKUCostAnnual = azureAnnual + gcpAnnual;

    const partitionRatio = TOTAL_PARTITIONS > 0 ? size.partitions / TOTAL_PARTITIONS : 0;
    const storageRatio = TOTAL_STORAGE_GB > 0 ? size.storageGB / TOTAL_STORAGE_GB : 0;

    const compute = partitionRatio * totalCKUCostAnnual;
    const storage = storageRatio * flatCosts.storage;
    const network = flatCosts.network * flatCosts.networkMultiplier;
    const governance = storageRatio * flatCosts.governance;

    const totalYearly = compute + storage + network + governance;
    const totalMonthly = totalYearly / 12;

    return {
      compute,
      storage,
      network,
      governance,
      totalYearly,
      totalMonthly,
    };
  };

  const costs = calculateCosts();
  const sizeConfig = tshirtSizes[selectedSize];
  const azureAnnual = ckuConfig.azureCKUs * ckuConfig.azureRate * 12;
  const gcpAnnual = ckuConfig.gcpCKUs * ckuConfig.gcpRate * 12;
  const totalCKUAnnual = azureAnnual + gcpAnnual;

  const handleExport = () => {
    const csvContent = generateCostProjectionCSV({
      selectedSize,
      partitions: sizeConfig.partitions,
      storageGB: sizeConfig.storageGB,
      ckuConfig,
      flatCosts,
      costs,
      annualIncreaseRate: parseFloat(annualIncreaseRate) / 100 || 0.034,
    });

    const filename = generateExportFilename();
    downloadCSV(csvContent, filename);
  };

  const partitionRatio = TOTAL_PARTITIONS > 0 ? sizeConfig.partitions / TOTAL_PARTITIONS : 0;
  const storageRatio = TOTAL_STORAGE_GB > 0 ? sizeConfig.storageGB / TOTAL_STORAGE_GB : 0;
  const inboundPartitions = Math.floor(sizeConfig.partitions / 2);
  const outboundPartitions = sizeConfig.partitions - inboundPartitions;

  // Calculate ROM costs for current configuration
  const romCosts = calculateROMCosts(romConfig);

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
              <button
                onClick={handleExportROM}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors"
              >
                <FileSpreadsheet className="w-5 h-5" />
                <span>Export ROM</span>
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
                <span>Sizes</span>
              </button>
              <button
                onClick={() => setShowCostSettings(!showCostSettings)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <DollarSign className="w-5 h-5" />
                <span>Costs</span>
              </button>
              <button
                onClick={() => setShowROMSettings(!showROMSettings)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                <FileSpreadsheet className="w-5 h-5" />
                <span>ROM</span>
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
              <h3 className="text-lg font-semibold text-white">Cost Configuration</h3>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Compute (CKU)</span>
                <span className="text-white font-semibold">${totalCKUAnnual.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Storage</span>
                <span className="text-white font-semibold">${flatCosts.storage.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Network</span>
                <span className="text-white font-semibold">${flatCosts.network.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Governance</span>
                <span className="text-white font-semibold">${flatCosts.governance.toLocaleString()}</span>
              </div>
              <div className="pt-2 border-t border-slate-600">
                <label className="text-slate-400 text-xs block mb-1">Annual Increase (%)</label>
                <input
                  type="number"
                  value={annualIncreaseRate}
                  onChange={(e) => setAnnualIncreaseRate(e.target.value)}
                  step="0.1"
                  min="0"
                  max="100"
                  className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                />
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
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

        {showCostSettings && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white">CKU & Cost Configuration</h3>
              <div className="flex gap-3">
                <button
                  onClick={handleResetCostSettings}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm"
                >
                  Reset to Defaults
                </button>
                <button
                  onClick={handleSaveCostSettings}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                >
                  Save Changes
                </button>
              </div>
            </div>

            <div className="mb-6">
              <h4 className="text-lg font-semibold text-white mb-4">CKU Configuration</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900 p-4 rounded-lg">
                  <h5 className="text-white font-semibold mb-3">Azure</h5>
                  <div className="space-y-3">
                    <div>
                      <label className="text-slate-400 text-sm block mb-1">Total Azure CKUs</label>
                      <input
                        type="number"
                        value={editingCKU.azureCKUs}
                        onChange={(e) => setEditingCKU({ ...editingCKU, azureCKUs: parseInt(e.target.value) || 0 })}
                        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 text-sm block mb-1">Azure $/CKU/Month</label>
                      <input
                        type="number"
                        value={editingCKU.azureRate}
                        onChange={(e) => setEditingCKU({ ...editingCKU, azureRate: parseInt(e.target.value) || 0 })}
                        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div className="pt-2 border-t border-slate-700">
                      <div className="text-slate-400 text-sm">Azure Annual Cost</div>
                      <div className="text-xl font-bold text-white">
                        ${(editingCKU.azureCKUs * editingCKU.azureRate * 12).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900 p-4 rounded-lg">
                  <h5 className="text-white font-semibold mb-3">GCP</h5>
                  <div className="space-y-3">
                    <div>
                      <label className="text-slate-400 text-sm block mb-1">Total GCP CKUs</label>
                      <input
                        type="number"
                        value={editingCKU.gcpCKUs}
                        onChange={(e) => setEditingCKU({ ...editingCKU, gcpCKUs: parseInt(e.target.value) || 0 })}
                        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 text-sm block mb-1">GCP $/CKU/Month</label>
                      <input
                        type="number"
                        value={editingCKU.gcpRate}
                        onChange={(e) => setEditingCKU({ ...editingCKU, gcpRate: parseInt(e.target.value) || 0 })}
                        className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div className="pt-2 border-t border-slate-700">
                      <div className="text-slate-400 text-sm">GCP Annual Cost</div>
                      <div className="text-xl font-bold text-white">
                        ${(editingCKU.gcpCKUs * editingCKU.gcpRate * 12).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
                <div className="text-blue-300 text-sm">Total Compute Annual Cost</div>
                <div className="text-2xl font-bold text-white">
                  ${((editingCKU.azureCKUs * editingCKU.azureRate * 12) + (editingCKU.gcpCKUs * editingCKU.gcpRate * 12)).toLocaleString()}
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Flat Annual Costs</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900 p-4 rounded-lg">
                  <label className="text-slate-400 text-sm block mb-2">Storage (Annual $)</label>
                  <input
                    type="number"
                    value={editingFlatCosts.storage}
                    onChange={(e) => setEditingFlatCosts({ ...editingFlatCosts, storage: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="bg-slate-900 p-4 rounded-lg">
                  <label className="text-slate-400 text-sm block mb-2">Network (Annual $)</label>
                  <input
                    type="number"
                    value={editingFlatCosts.network}
                    onChange={(e) => setEditingFlatCosts({ ...editingFlatCosts, network: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="bg-slate-900 p-4 rounded-lg">
                  <label className="text-slate-400 text-sm block mb-2">Network Multiplier</label>
                  <input
                    type="number"
                    value={editingFlatCosts.networkMultiplier}
                    onChange={(e) => setEditingFlatCosts({ ...editingFlatCosts, networkMultiplier: parseFloat(e.target.value) || 0 })}
                    step="0.05"
                    className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="bg-slate-900 p-4 rounded-lg">
                  <label className="text-slate-400 text-sm block mb-2">Governance (Annual $)</label>
                  <input
                    type="number"
                    value={editingFlatCosts.governance}
                    onChange={(e) => setEditingFlatCosts({ ...editingFlatCosts, governance: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">ROM Summary</h3>
            <div className="text-sm text-slate-400">
              {romCosts.totalInboundFeeds} inbound + {romCosts.totalOutboundFeeds} outbound topics
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900 border border-slate-600 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-6 h-6 text-orange-400" />
                <h4 className="text-lg font-semibold text-white">One-Time Engineering</h4>
              </div>
              <div className="text-4xl font-bold text-white mb-4">
                ${romCosts.breakdown.oneTimeDevelopment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="text-sm text-slate-400">
                {romCosts.totalInboundFeeds} inbound + {romCosts.totalOutboundFeeds} outbound topics
              </div>
            </div>

            <div className="bg-slate-900 border border-emerald-600 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Server className="w-6 h-6 text-emerald-400" />
                <h4 className="text-lg font-semibold text-white">First Year Cloud</h4>
              </div>
              <div className="text-4xl font-bold text-white mb-4">
                ${romCosts.breakdown.firstYearCloudCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between text-slate-300">
                  <span>Confluent:</span>
                  <span className="font-semibold">${romCosts.breakdown.confluentCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>GCP:</span>
                  <span className="font-semibold">${romCosts.breakdown.gcpCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Network:</span>
                  <span className="font-semibold">${romCosts.breakdown.networkCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-blue-600 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <TrendingUp className="w-6 h-6 text-blue-400" />
                <h4 className="text-lg font-semibold text-white">7-Year Total</h4>
              </div>
              <div className="text-4xl font-bold text-white mb-4">
                ${romCosts.breakdown.totalProjectCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="text-sm text-slate-400">
                {romConfig.numIngests ?? 1} ingests | {romCosts.partitionUtilizationPct.toFixed(2)}% network
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-900/20 border border-blue-800 rounded-lg text-sm text-blue-200">
            Cost scales with: Number of topics ({romCosts.totalInboundFeeds} in + {romCosts.totalOutboundFeeds} out),
            partition usage ({romCosts.partitionUtilizationPct.toFixed(2)}%), and daily volume ({romCosts.recordsPerDay.toLocaleString()} records)
          </div>

          <div className="mt-6">
            <h4 className="text-white font-semibold mb-4">7-Year Cost Projection ({(romConfig.escalationRate * 100).toFixed(1)}% Annual Escalation)</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left text-slate-400 font-semibold py-3 px-4">Fiscal Year</th>
                    <th className="text-right text-slate-400 font-semibold py-3 px-4">Data Engineering</th>
                    <th className="text-right text-slate-400 font-semibold py-3 px-4">Cloud Infrastructure</th>
                    <th className="text-right text-slate-400 font-semibold py-3 px-4">Year Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-slate-700 bg-slate-900">
                    <td className="py-3 px-4 text-white font-medium">FY{romConfig.startYear}</td>
                    <td className="py-3 px-4 text-right text-white">
                      ${romCosts.breakdown.oneTimeDevelopment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-3 px-4 text-right text-white">
                      ${romCosts.breakdown.firstYearCloudCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-3 px-4 text-right text-white font-semibold">
                      ${(romCosts.breakdown.oneTimeDevelopment + romCosts.breakdown.firstYearCloudCost).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                  {romCosts.operatingVariance.map((yearData) => (
                    <tr key={yearData.year} className="border-b border-slate-700">
                      <td className="py-3 px-4 text-slate-300">FY{yearData.year}</td>
                      <td className="py-3 px-4 text-right text-slate-500">$0</td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        ${yearData.cloudInfrastructure.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300 font-semibold">
                        ${yearData.total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-blue-900/30 border-t-2 border-blue-600">
                    <td className="py-4 px-4 text-white font-bold">7-Year Total</td>
                    <td className="py-4 px-4 text-right text-white font-bold">
                      ${romCosts.breakdown.oneTimeDevelopment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-4 px-4 text-right text-white font-bold">
                      ${romCosts.breakdown.cloudInfrastructure7Year.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-4 px-4 text-right text-white font-bold text-lg">
                      ${romCosts.breakdown.totalProjectCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {showROMSettings && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white">ROM Configuration</h3>
              <div className="flex gap-3">
                <button
                  onClick={handleResetROMSettings}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm"
                >
                  Reset to Defaults
                </button>
                <button
                  onClick={handleSaveROMSettings}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                >
                  Save Changes
                </button>
              </div>
            </div>

            <div className="mb-6 bg-slate-900 p-4 rounded-lg">
              <h4 className="text-white font-semibold mb-4">Project Basics</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-slate-400 text-sm block mb-1">Records per Day</label>
                  <input
                    type="number"
                    value={editingROM.recordsPerDay ?? 5000}
                    onChange={(e) => setEditingROM({ ...editingROM, recordsPerDay: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 text-sm block mb-1">Number of Ingests</label>
                  <input
                    type="number"
                    value={editingROM.numIngests ?? 1}
                    min={1}
                    max={15}
                    onChange={(e) => {
                      const numIngests = Math.max(1, parseInt(e.target.value) || 1);
                      const feedConfigs = editingROM.feedConfigs ?? [];
                      const newFeedConfigs = Array.from({ length: numIngests }, (_, i) =>
                        feedConfigs[i] ?? { inbound: 1, outbound: 1, partitions: 0.048 }
                      );
                      setEditingROM({ ...editingROM, numIngests, feedConfigs: newFeedConfigs });
                    }}
                    className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="flex items-end">
                  <div className="w-full pt-2 border-t border-slate-700">
                    <div className="text-slate-400 text-sm">Total Partitions</div>
                    <div className="text-xl font-bold text-white">
                      {(editingROM.feedConfigs ?? []).reduce((sum, f) => sum + f.partitions, 0).toFixed(3)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

              <div className="bg-slate-900 p-4 rounded-lg">
                <h4 className="text-white font-semibold mb-4">Data Engineering</h4>
                <div className="space-y-3">
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Hourly Rate ($)</label>
                    <input
                      type="number"
                      value={editingROM.deHourlyRate}
                      onChange={(e) => setEditingROM({ ...editingROM, deHourlyRate: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Inbound Hours (per feed)</label>
                    <input
                      type="number"
                      value={editingROM.inboundHours}
                      onChange={(e) => setEditingROM({ ...editingROM, inboundHours: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Outbound Hours (per feed)</label>
                    <input
                      type="number"
                      value={editingROM.outboundHours}
                      onChange={(e) => setEditingROM({ ...editingROM, outboundHours: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Normalization Hours (total)</label>
                    <input
                      type="number"
                      value={editingROM.normalizationHours}
                      onChange={(e) => setEditingROM({ ...editingROM, normalizationHours: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 p-4 rounded-lg">
                <h4 className="text-white font-semibold mb-4">Cloud Infrastructure</h4>
                <div className="space-y-3">
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Workspace Setup ($)</label>
                    <input
                      type="number"
                      value={editingROM.workspaceSetupCost}
                      onChange={(e) => setEditingROM({ ...editingROM, workspaceSetupCost: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Confluent Annual Cost ($)</label>
                    <input
                      type="number"
                      value={editingROM.confluentAnnualCost}
                      onChange={(e) => setEditingROM({ ...editingROM, confluentAnnualCost: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">GCP/GKE Per Feed Annual ($)</label>
                    <input
                      type="number"
                      value={editingROM.gcpPerFeedAnnualCost}
                      onChange={(e) => setEditingROM({ ...editingROM, gcpPerFeedAnnualCost: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Escalation Rate (%)</label>
                    <input
                      type="number"
                      value={(editingROM.escalationRate * 100).toFixed(1)}
                      onChange={(e) => setEditingROM({ ...editingROM, escalationRate: parseFloat(e.target.value) / 100 || 0 })}
                      step="0.1"
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Start Year</label>
                    <input
                      type="number"
                      value={editingROM.startYear}
                      onChange={(e) => setEditingROM({ ...editingROM, startYear: parseInt(e.target.value) || new Date().getFullYear() })}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-blue-300 text-sm">One-Time Engineering</div>
                  <div className="text-2xl font-bold text-white">
                    ${Math.round(calculateROMCosts(editingROM).breakdown.oneTimeDevelopment).toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {calculateROMCosts(editingROM).totalInboundFeeds} in + {calculateROMCosts(editingROM).totalOutboundFeeds} out topics
                  </div>
                </div>
                <div>
                  <div className="text-blue-300 text-sm">First Year Cloud</div>
                  <div className="text-2xl font-bold text-white">
                    ${Math.round(calculateROMCosts(editingROM).breakdown.firstYearCloudCost).toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {calculateROMCosts(editingROM).partitionUtilizationPct.toFixed(2)}% network utilization
                  </div>
                </div>
                <div>
                  <div className="text-blue-300 text-sm">7-Year Total</div>
                  <div className="text-2xl font-bold text-white">
                    ${Math.round(calculateROMCosts(editingROM).breakdown.totalProjectCost).toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {editingROM.numIngests ?? 1} ingests | {calculateROMCosts(editingROM).totalPartitions.toFixed(3)} partitions
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
          <h3 className="text-xl font-semibold text-white mb-6">Select T-Shirt Size</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.keys(tshirtSizes).map((size) => {
              const config = tshirtSizes[size];
              const isSelected = selectedSize === size;
              const inbound = Math.floor(config.partitions / 2);
              const outbound = config.partitions - inbound;

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
                      <div className="text-slate-500 text-xs">
                        ({inbound} in / {outbound} out)
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
                  <div className="text-slate-500 text-xs mt-1">
                    {inboundPartitions} inbound / {outboundPartitions} outbound
                  </div>
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
                    <span className="font-semibold">{(partitionRatio * 100).toFixed(3)}%</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Storage:</span>
                    <span className="font-semibold">{(storageRatio * 100).toFixed(3)}%</span>
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
                    <span className="text-slate-300">Compute (CKU) Cost</span>
                  </div>
                  <span className="text-white font-semibold">
                    ${costs.compute.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  {partitionRatio.toFixed(4)} × ${totalCKUAnnual.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  ({ckuConfig.azureCKUs} Azure + {ckuConfig.gcpCKUs} GCP CKUs)
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
                  {storageRatio.toFixed(4)} × ${flatCosts.storage.toLocaleString()}
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
                  {flatCosts.networkMultiplier} × ${flatCosts.network.toLocaleString()} (flat, not prorated)
                </div>
              </div>

              <div className="p-4 bg-slate-900 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-400" />
                    <span className="text-slate-300">Governance Cost</span>
                  </div>
                  <span className="text-white font-semibold">
                    ${costs.governance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  {storageRatio.toFixed(4)} × ${flatCosts.governance.toLocaleString()}
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
              <div className="text-blue-400 mb-2">Compute (CKU) Cost Formula:</div>
              <div className="text-slate-300">
                (Partitions Needed / Total Partitions) × Total CKU Annual Cost
              </div>
              <div className="text-slate-500 mt-2 text-xs">
                Total CKU Annual = (Azure CKUs × Azure Rate × 12) + (GCP CKUs × GCP Rate × 12)
              </div>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg font-mono">
              <div className="text-green-400 mb-2">Storage Cost Formula:</div>
              <div className="text-slate-300">
                (Storage Needed / Total Storage) × Total Annual Storage Cost
              </div>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg font-mono">
              <div className="text-amber-400 mb-2">Network Cost Formula:</div>
              <div className="text-slate-300">
                Network Multiplier × Total Annual Network Cost (flat, not prorated)
              </div>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg font-mono">
              <div className="text-purple-400 mb-2">Governance Cost Formula:</div>
              <div className="text-slate-300">
                (Storage Needed / Total Storage) × Total Annual Governance Cost
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
