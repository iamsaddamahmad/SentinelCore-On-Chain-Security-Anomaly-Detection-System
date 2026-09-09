# utils.py
# ============================================================
# UTILITY FUNCTIONS
# ============================================================

import os
import json
import time
from datetime import datetime
from web3 import Web3
import pandas as pd
import numpy as np


def create_directories():
    """Create all required directories"""
    dirs = ['data', 'models', 'logs', 'alerts']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("✅ Directories created")


def get_timestamp():
    """Get current timestamp as string"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_date_string():
    """Get date string for filenames"""
    return datetime.now().strftime('%Y%m%d')


def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def load_json(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(data, filepath):
    """Save JSON file safely"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def wei_to_eth(wei_value, w3):
    """Convert wei to ETH"""
    try:
        return float(w3.from_wei(wei_value, 'ether'))
    except:
        return 0.0


def wei_to_gwei(wei_value, w3):
    """Convert wei to Gwei"""
    try:
        return float(w3.from_wei(wei_value, 'gwei'))
    except:
        return 0.0


def print_progress(current, total, prefix='', suffix=''):
    """Print progress bar"""
    percent = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current // total) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f'\r{prefix} [{bar}] {percent:.1f}% {suffix}', end='')


class Timer:
    """Simple timer for performance tracking"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()
        return self

    def stop(self):
        self.end_time = time.time()
        return self

    def elapsed(self):
        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return end - self.start_time

    def elapsed_str(self):
        seconds = self.elapsed()
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
