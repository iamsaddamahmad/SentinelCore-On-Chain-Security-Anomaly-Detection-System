# config.py
# ============================================================
# CONFIGURATION - Update with your keys
# ============================================================

# Get your API key from https://infura.io
INFURA_API_KEY = "YOUR_INFURA_API_KEY_HERE"

# Ethereum RPC URL
RPC_URL = "https://mainnet.infura.io/v3/Your_INFURA_API_KEY"

# ============================================================
# ADDRESSES TO MONITOR
# ============================================================
MONITORED_ADDRESSES = [
    "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD68",  # Vitalik Buterin
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik's ENS
    # Add more addresses here
]

# ============================================================
# ALERT THRESHOLDS
# ============================================================
LARGE_TRANSFER_THRESHOLD_ETH = 100      # Alert on transfers > 100 ETH
HIGH_GAS_THRESHOLD_GWEI = 200           # Alert on gas > 200 Gwei
MAX_ANOMALY_SCORE = 0.8                 # ML anomaly threshold

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
SNN_INPUT_SIZE = 5                      # Number of spike input features
SNN_HIDDEN_SIZE = 50                    # Hidden layer size
SNN_OUTPUT_SIZE = 1                     # Output (anomaly / normal)
SNN_EPOCHS = 10                         # Training epochs
SNN_LEARNING_RATE = 0.01               # STDP learning rate

# ============================================================
# SYSTEM CONFIGURATION
# ============================================================
BLOCKS_TO_SCAN = 100                    # Default blocks to scan
LIVE_CHECK_INTERVAL = 3                 # Seconds between checks
MAX_TRANSACTIONS_PER_BATCH = 1000      # Max txs to process at once
