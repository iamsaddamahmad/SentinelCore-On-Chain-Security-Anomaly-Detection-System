# config.py
# ============================================================
# CONFIGURATION - Update with your keys
# ============================================================

# Get your API key from https://infura.io
INFURA_API_KEY = "<your_infura_api_key>"

# ============================================================
# MULTI-CHAIN RPC CONFIGURATION
# ============================================================
CHAINS = {
    "ethereum": {
        "name": "Ethereum Mainnet",
        "rpc_url": f"https://mainnet.infura.io/v3/{INFURA_API_KEY}",
        "chain_id": 1,
        "explorer": "https://etherscan.io",
        "native_symbol": "ETH",
        "enabled": True,
    },
    "bsc": {
        "name": "BNB Smart Chain",
        "rpc_url": "https://bsc-dataseed.binance.org/",
        "chain_id": 56,
        "explorer": "https://bscscan.com",
        "native_symbol": "BNB",
        "enabled": True,
    },
    "polygon": {
        "name": "Polygon Mainnet",
        "rpc_url": f"https://polygon-mainnet.infura.io/v3/{INFURA_API_KEY}",
        "chain_id": 137,
        "explorer": "https://polygonscan.com",
        "native_symbol": "MATIC",
        "enabled": True,
    },
}

# Old format — still works with current monitor.py
MONITORED_ADDRESSES = [
    "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD68",
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
]

# ============================================================
# ADDRESSES TO MONITOR (per chain)
# ============================================================
MONITORED_ADDRESSES = {
    "ethereum": [
        "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD68",  # Vitalik Buterin
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik's ENS
    ],
    "bsc": [
        # Add BSC addresses here
    ],
    "polygon": [
        # Add Polygon addresses here
    ],
}

# ============================================================
# BACKWARD COMPATIBILITY (defaults to Ethereum)
# ============================================================
RPC_URL = CHAINS["ethereum"]["rpc_url"]

# ============================================================
# ALERT THRESHOLDS
# ============================================================
LARGE_TRANSFER_THRESHOLD_ETH = 100      # Alert on transfers > 100 ETH
HIGH_GAS_THRESHOLD_GWEI = 200           # Alert on gas > 200 Gwei
MAX_ANOMALY_SCORE = 0.8                 # ML anomaly threshold

# ============================================================
# PER-CHAIN ALERT THRESHOLDS
# ============================================================
# Each chain has different native token values, gas behavior,
# and typical transaction sizes. Tune separately.

LARGE_TRANSFER_THRESHOLD = {
    "ethereum": 100,      # 100 ETH
    "bsc": 50,            # 50 BNB
    "polygon": 10000,     # 10,000 MATIC
}

HIGH_GAS_THRESHOLD = {
    "ethereum": 200,      # 200 Gwei
    "bsc": 50,            # 50 Gwei (BSC gas is cheaper)
    "polygon": 500,       # 500 Gwei (Polygon gas spikes often)
}

# ============================================================
# DIRECTORIES
# ============================================================
DATA_DIR = "data"
MODELS_DIR = "models"
LOGS_DIR = "logs"
ALERTS_DIR = "alerts"

# ============================================================
# SNN CONFIGURATION (Phase 5)
# ============================================================
SNN_INPUT_SIZE = 5
SNN_HIDDEN_SIZE = 50
SNN_OUTPUT_SIZE = 1
SNN_EPOCHS = 10
SNN_LEARNING_RATE = 0.01

# ============================================================
# SYSTEM CONFIGURATION
# ============================================================
BLOCKS_TO_SCAN = 100
LIVE_CHECK_INTERVAL = 3
MAX_TRANSACTIONS_PER_BATCH = 1000

# ============================================================
# TELEGRAM ALERT CONFIGURATION
# ============================================================
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
TELEGRAM_ENABLED = True

# Set to True to send a test alert on monitor startup
SEND_TEST_ALERT_ON_STARTUP = False

# ============================================================
# ALERT SEVERITY LEVELS
# ============================================================
ALERT_SEVERITY_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
