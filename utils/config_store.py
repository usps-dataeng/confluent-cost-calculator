"""
Loads and saves shared infrastructure config from network_config.json
in the project root. Edit this file (or use the app's Save button) to
update values for everyone who runs the app.
"""

import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'network_config.json')

DEFAULTS = {
    'total_partitions': 20224,
    'total_storage_gb': 30844.17,
    'network_annual': 120000,
    'storage_annual': 180000,
    'governance_annual': 42840,
    'azure_ckus': 14,
    'azure_rate': 1925,
    'gcp_ckus': 28,
    'gcp_rate': 1585,
    'network_multiplier': 0.75,
}


def load_config() -> dict:
    """Load config from network_config.json. Falls back to DEFAULTS if file missing or corrupt."""
    try:
        with open(_CONFIG_PATH, 'r') as f:
            data = json.load(f)
        return {
            'total_partitions': int(data.get('total_partitions', DEFAULTS['total_partitions'])),
            'total_storage_gb': float(data.get('total_storage_gb', DEFAULTS['total_storage_gb'])),
            'network_annual': int(data.get('network_annual', DEFAULTS['network_annual'])),
            'storage_annual': int(data.get('storage_annual', DEFAULTS['storage_annual'])),
            'governance_annual': int(data.get('governance_annual', DEFAULTS['governance_annual'])),
            'azure_ckus': int(data.get('azure_ckus', DEFAULTS['azure_ckus'])),
            'azure_rate': int(data.get('azure_rate', DEFAULTS['azure_rate'])),
            'gcp_ckus': int(data.get('gcp_ckus', DEFAULTS['gcp_ckus'])),
            'gcp_rate': int(data.get('gcp_rate', DEFAULTS['gcp_rate'])),
            'network_multiplier': float(data.get('network_multiplier', DEFAULTS['network_multiplier'])),
        }
    except Exception:
        return dict(DEFAULTS)


def save_config(cfg: dict) -> bool:
    """Write updated config back to network_config.json. Returns True on success."""
    try:
        data = {
            'total_partitions': int(cfg['total_partitions']),
            'total_storage_gb': float(cfg['total_storage_gb']),
            'network_annual': int(cfg['network_annual']),
            'storage_annual': int(cfg['storage_annual']),
            'governance_annual': int(cfg['governance_annual']),
            'azure_ckus': int(cfg['azure_ckus']),
            'azure_rate': int(cfg['azure_rate']),
            'gcp_ckus': int(cfg['gcp_ckus']),
            'gcp_rate': int(cfg['gcp_rate']),
            'network_multiplier': float(cfg['network_multiplier']),
        }
        with open(_CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
