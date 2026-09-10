# monitor.py
# ============================================================
# PHASE 2-3: SECURITY MONITOR
# Real-time transaction monitoring with rule-based alerts
# ============================================================

import os
import time
from datetime import datetime, timezone

from web3 import Web3

from config import *
from ml_detector import MLAnomalyDetector
from utils import *


class SecurityMonitor:
    """
    Real-time security monitor for blockchain transactions
    Combines rule-based and ML-based detection
    """

    def __init__(self):
        print("🔗 Initializing Security Monitor...")

        # Connect to Ethereum
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError(
                "Failed to connect to Ethereum. Check your API key.")

        print(f"✅ Connected to Ethereum (Block: {self.w3.eth.block_number})")

        # State
        self.last_block = self.w3.eth.block_number
        self.alert_count = 0
        self.processed_txs = set()

        # Initialize directories
        create_directories()

        # Initialize ML detector (optional)
        self.ml_detector = MLAnomalyDetector()
        self.ml_enabled = self.ml_detector.load()

        if self.ml_enabled:
            print("✅ ML detection enabled")
        else:
            print("ℹ️ ML detection disabled (train model with ml_detector.py)")

        print(f"Watching {len(MONITORED_ADDRESSES)} addresses")
        print(f"Alert threshold: {LARGE_TRANSFER_THRESHOLD_ETH} ETH")
        print("="*50)

    def analyze_transaction(self, tx, block_num):
        """
        Comprehensive transaction analysis

        Returns:
            (alerts, tx_data, ml_result)
        """
        try:
            tx_hash = tx.hash
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)

            # Extract transaction data
            tx_data = {
                'hash': tx_hash.hex(),
                'block': block_num,
                'from': tx['from'],
                'to': tx.get('to', '0x0'),
                'value_eth': wei_to_eth(tx['value'], self.w3),
                'gas_price_gwei': wei_to_gwei(tx['gasPrice'], self.w3),
                'gas': tx['gas'],
                'gas_used': receipt['gasUsed'] if receipt else 0,
                'input_length': len(tx['input']),
                'is_contract': 1 if not tx.get('to') or tx['to'] == '0x0' else 0,
                'success': 1 if receipt and receipt.get('status') == 1 else 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            alerts = []
            ml_result = None

            # ---- RULE-BASED ALERTS ----

            # 1. Large transfer
            if tx_data['value_eth'] > LARGE_TRANSFER_THRESHOLD_ETH:
                alerts.append({
                    'type': 'LARGE_TRANSFER',
                    'severity': 'HIGH',
                    'details': f"{tx_data['value_eth']:.2f} ETH transferred"
                })

            # 2. High gas price
            if tx_data['gas_price_gwei'] > HIGH_GAS_THRESHOLD_GWEI:
                alerts.append({
                    'type': 'HIGH_GAS_PRICE',
                    'severity': 'MEDIUM',
                    'details': f"{tx_data['gas_price_gwei']:.0f} Gwei"
                })

            # 3. Contract deployment
            if tx_data['is_contract'] == 1:
                alerts.append({
                    'type': 'CONTRACT_DEPLOYMENT',
                    'severity': 'MEDIUM',
                    'details': f"New contract by {tx_data['from'][:10]}..."
                })

            # 4. Failed transaction
            if tx_data['success'] == 0:
                alerts.append({
                    'type': 'FAILED_TRANSACTION',
                    'severity': 'LOW',
                    'details': "Transaction failed"
                })

            # 5. Address monitoring
            for addr in MONITORED_ADDRESSES:
                if tx_data['from'].lower() == addr.lower():
                    alerts.append({
                        'type': 'MONITORED_ADDRESS_ACTIVITY',
                        'severity': 'INFO',
                        'details': f"Activity from monitored address: {addr[:10]}..."
                    })

            # ---- ML-BASED DETECTION ----
            if self.ml_enabled:
                try:
                    ml_result = self.ml_detector.predict(tx_data)
                    if ml_result and ml_result['is_anomaly']:
                        alerts.append({
                            'type': 'ML_ANOMALY_DETECTED',
                            'severity': 'HIGH',
                            'details': f"ML anomaly score: {ml_result['score']:.3f}",
                            'confidence': ml_result['confidence']
                        })
                except Exception as e:
                    print(f"⚠️ ML error: {e}")

            return alerts, tx_data, ml_result

        except Exception:
            return [], None, None

    def log_alert(self, alert, tx_data, ml_result=None):
        """Log alert to file"""
        log_entry = {
            'timestamp': get_timestamp(),
            'alert': alert,
            'transaction': tx_data
        }

        if ml_result:
            log_entry['ml_result'] = ml_result

        # Daily log file
        filename = f"alerts_{get_date_string()}.json"
        filepath = os.path.join(ALERTS_DIR, filename)

        existing = load_json(filepath)
        existing.append(log_entry)
        save_json(existing, filepath)

    def process_block(self, block_num):
        """Process all transactions in a block"""
        try:
            block = self.w3.eth.get_block(block_num, full_transactions=True)

            for tx in block.transactions:
                tx_hash = tx.hash.hex()

                # Skip if already processed
                if tx_hash in self.processed_txs:
                    continue

                self.processed_txs.add(tx_hash)

                # Check if any monitored address is involved
                tx_from = tx.get('from', '').lower()
                tx_to = tx.get('to', '').lower() if tx.get('to') else ''

                for address in MONITORED_ADDRESSES:
                    address_lower = address.lower()

                    if tx_from == address_lower or tx_to == address_lower:
                        alerts, tx_data, ml_result = self.analyze_transaction(
                            tx, block_num)

                        if alerts:
                            self.alert_count += 1
                            print("\n" + "="*70)
                            print(
                                f"🚨 ALERT #{self.alert_count} | {get_timestamp()}")
                            print("="*70)
                            print(f"Block: {block_num}")
                            print(f"Tx: {tx_hash[:20]}...")
                            print(f"From: {tx_data['from'][:30]}...")
                            print(f"To: {tx_data['to'][:30]}...")
                            print(f"Value: {tx_data['value_eth']:.6f} ETH")

                            if ml_result and ml_result.get('is_anomaly'):
                                print(f"🤖 ML Score: {ml_result['score']:.3f}")
                                print(
                                    f"   Confidence: {ml_result['confidence']:.3f}")

                            for alert in alerts:
                                print(
                                    f"\n⚠️ [{alert['severity']}] {alert['type']}")
                                print(f"   {alert['details']}")

                            # Log all alerts
                            for alert in alerts:
                                self.log_alert(alert, tx_data, ml_result)

                            # Also log to alerts.log
                            with open(os.path.join(LOGS_DIR, 'alerts.log'), 'a') as f:
                                f.write(
                                    f"{get_timestamp()} | {alerts[0]['type']} | {tx_hash[:20]}\n")

                        break  # Found address match

        except Exception as e:
            print(f"⚠️ Error processing block {block_num}: {e}")

    def live_monitor(self):
        """Continuous live monitoring"""
        print("\n" + "="*60)
        print("🔄 STARTING LIVE MONITORING")
        print("="*60)
        print(f"Addresses watched: {len(MONITORED_ADDRESSES)}")
        print(
            f"ML detection: {'✅ ENABLED' if self.ml_enabled else '❌ DISABLED'}")
        print(f"Alerts logged to: {ALERTS_DIR}/alerts_*.json")
        print("Press Ctrl+C to stop")
        print("="*60)

        try:
            while True:
                current_block = self.w3.eth.block_number

                if current_block > self.last_block:
                    # Process new blocks
                    for block_num in range(self.last_block + 1, current_block + 1):
                        print(f"\r📦 Processing block {block_num}...", end="")
                        self.process_block(block_num)

                    self.last_block = current_block
                    print(
                        f"\r✅ Processed up to block {current_block} | Alerts: {self.alert_count}  ")

                time.sleep(LIVE_CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("🛑 MONITORING STOPPED")
            print(f"Total alerts detected: {self.alert_count}")
            print(f"Transactions processed: {len(self.processed_txs)}")
            print("="*60)

    def scan_address(self, address, num_blocks=BLOCKS_TO_SCAN):
        """Scan historical blocks for address activity"""
        print(f"\n🔍 Scanning address: {address[:15]}...")
        print(f"Looking back {num_blocks} blocks...")

        current_block = self.w3.eth.block_number
        start_block = max(0, current_block - num_blocks)

        found_txs = 0
        alerts_found = 0

        for block_num in range(start_block, current_block + 1):
            try:
                block = self.w3.eth.get_block(
                    block_num, full_transactions=True)

                for tx in block.transactions:
                    tx_from = tx.get('from', '').lower()
                    tx_to = tx.get('to', '').lower() if tx.get('to') else ''
                    address_lower = address.lower()

                    if tx_from == address_lower or tx_to == address_lower:
                        found_txs += 1
                        alerts, _tx_data, _ = self.analyze_transaction(
                            tx, block_num)

                        if alerts:
                            alerts_found += 1
                            print(
                                f"\n📝 Block {block_num} | Tx: {tx.hash.hex()[:20]}...")
                            for alert in alerts:
                                print(
                                    f"  ⚠️ [{alert['severity']}] {alert['type']}: {alert['details']}")

                if block_num % 10 == 0:
                    progress = ((block_num - start_block) / num_blocks * 100)
                    print(
                        f"\rProgress: {progress:.0f}% | Found: {found_txs} txs", end="")

            except Exception:
                continue

        print("\n\n✅ Scan complete!")
        print(f"Transactions found: {found_txs}")
        print(f"Alerts triggered: {alerts_found}")


def main():
    print("="*60)
    print("🔒 SECURITY MONITOR")
    print("="*60)

    try:
        monitor = SecurityMonitor()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your Infura API key is correct in config.py")
        return

    while True:
        print("\nSelect mode:")
        print("1. Live monitoring (real-time)")
        print("2. Scan specific address (historical)")
        print("3. View recent alerts")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ")

        if choice == "1":
            monitor.live_monitor()

        elif choice == "2":
            address = input("Enter Ethereum address: ")
            if not address.startswith('0x') or len(address) != 42:
                print("⚠️ Invalid address format!")
                continue
            blocks = input(f"Blocks to scan (default {BLOCKS_TO_SCAN}): ")
            blocks = int(blocks) if blocks else BLOCKS_TO_SCAN
            monitor.scan_address(address, blocks)

        elif choice == "3":
            # View latest alerts
            alert_files = [f for f in os.listdir(
                ALERTS_DIR) if f.startswith('alerts_')]
            if not alert_files:
                print("No alerts found.")
                continue

            # latest = sorted(alert_files)[-1]
            latest = max(alert_files)
            filepath = os.path.join(ALERTS_DIR, latest)
            alerts = load_json(filepath)

            if not alerts:
                print("No alerts in file.")
                continue

            print(f"\n📋 Latest alerts from {latest}")
            print(f"Total alerts: {len(alerts)}")
            print("\nLast 5 alerts:")

            for alert in alerts[-5:]:
                print(f"\n{alert.get('timestamp', 'N/A')}")
                print(f"  {alert.get('alert', {}).get('type', 'Unknown')}")
                print(f"  {alert.get('alert', {}).get('details', 'No details')}")

        elif choice == "4":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
