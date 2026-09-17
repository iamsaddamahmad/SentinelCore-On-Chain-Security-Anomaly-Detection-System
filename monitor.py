# monitor.py
# ============================================================
# PHASE 2-3: SECURITY MONITOR (Multi-Chain)
# Real-time transaction monitoring across Ethereum, BSC, Polygon
# ============================================================

import os
import time
from datetime import datetime, timezone

from web3 import Web3

from config import (
    ALERTS_DIR,
    BLOCKS_TO_SCAN,
    CHAINS,
    HIGH_GAS_THRESHOLD_GWEI,
    LARGE_TRANSFER_THRESHOLD_ETH,
    LIVE_CHECK_INTERVAL,
    LOGS_DIR,
    MONITORED_ADDRESSES,
    SEND_TEST_ALERT_ON_STARTUP,
)
from ml_detector import MLAnomalyDetector
from telegram_alert import TelegramAlert
from utils import (
    create_directories,
    get_date_string,
    get_timestamp,
    load_json,
    save_json,
    wei_to_eth,
    wei_to_gwei,
)


class SecurityMonitor:
    """
    Real-time multi-chain security monitor for blockchain transactions.
    Combines rule-based and ML-based detection across multiple EVM chains.
    """

    def __init__(self):
        print("🔗 Initializing Multi-Chain Security Monitor...")
        print("=" * 60)

        # State
        self.alert_count = 0
        self.processed_txs = set()
        self.last_blocks = {}          # {chain_key: block_number}
        self.connections = {}          # {chain_key: Web3 instance}
        self.chain_configs = {}        # {chain_key: config dict}

        # Initialize directories
        create_directories()

        # Connect to each enabled chain
        print("\n🔌 Connecting to chains...")
        for chain_key, chain_config in CHAINS.items():
            if not chain_config.get("enabled", False):
                print(f"  ⏭️  {chain_config['name']}: disabled")
                continue

            try:
                w3 = Web3(Web3.HTTPProvider(
                    chain_config["rpc_url"],
                    request_kwargs={"timeout": 30},
                ))

                # --- PoA middleware for BSC, Polygon ---
                # BSC and Polygon use Proof-of-Authority consensus with
                # extraData > 32 bytes, which Web3.py rejects by default.
                if chain_key in ("bsc", "polygon"):
                    try:
                        from web3.middleware import ExtraDataToPOAMiddleware
                        w3.middleware_onion.inject(
                            ExtraDataToPOAMiddleware, layer=0)
                    except ImportError:
                        # Older web3.py versions
                        from web3.middleware import geth_poa_middleware
                        w3.middleware_onion.inject(
                            geth_poa_middleware, layer=0)

                if w3.is_connected():
                    block = w3.eth.block_number
                    print(f"  ✅ {chain_config['name']}: Block {block}")

                    self.connections[chain_key] = w3
                    self.chain_configs[chain_key] = chain_config
                    self.last_blocks[chain_key] = block
                else:
                    print(f"  ❌ {chain_config['name']}: Failed to connect")

            except Exception as e:
                print(f"  ❌ {chain_config['name']}: {e}")

        if not self.connections:
            raise ConnectionError(
                "Failed to connect to any chain. Check your RPC URLs.")

        print(f"\n✅ Connected to {len(self.connections)} chain(s)")

        # Initialize ML detector
        print("\n🧠 Initializing ML detector...")
        self.ml_detector = MLAnomalyDetector()
        self.ml_enabled = self.ml_detector.load()

        if self.ml_enabled:
            print("✅ ML detection enabled")
        else:
            print("ℹ️  ML detection disabled (train model with ml_detector.py)")

        # Initialize Telegram alerts
        print("\n📱 Initializing Telegram alerts...")
        self.telegram = TelegramAlert()

        if self.telegram.enabled and SEND_TEST_ALERT_ON_STARTUP:
            print("📤 Sending test alert (SEND_TEST_ALERT_ON_STARTUP=True)...")
            self.telegram.send_test_alert()
        elif self.telegram.enabled:
            print("📱 Telegram alerts enabled (no test alert on startup)")

        # Summary
        print("\n" + "=" * 60)
        for chain_key, config in self.chain_configs.items():
            addresses = MONITORED_ADDRESSES.get(chain_key, [])
            print(
                f"👁️  {config['name']}: watching {len(addresses)} address(es)")
        print(
            f"⚡ Alert threshold: {LARGE_TRANSFER_THRESHOLD_ETH} native tokens")
        print(f"⛽ High gas threshold: {HIGH_GAS_THRESHOLD_GWEI} Gwei")
        print("=" * 60)

    # ================================================================
    # LOGGING
    # ================================================================
    def log_alert(self, alert, tx_data, ml_result=None):
        """Log alert to JSON + system log AND send Telegram notification."""

        # --- 1. SEND TO TELEGRAM FIRST (don't let file errors block alerts) ---
        if hasattr(self, "telegram") and self.telegram.enabled:
            try:
                alert_data = {
                    "timestamp": get_timestamp(),
                    "type": alert["type"],
                    "severity": alert.get("severity", "LOW"),
                    "details": alert["details"],
                    "transaction": {
                        "chain": tx_data.get("chain", "unknown"),
                        "chain_name": tx_data.get("chain_name", "Unknown"),
                        "native_symbol": tx_data.get("native_symbol", ""),
                        "hash": tx_data.get("hash", "N/A"),
                        "from": tx_data.get("from", "N/A"),
                        "to": tx_data.get("to", "N/A"),
                        "value_eth": tx_data.get("value_eth", 0),
                        "block": tx_data.get("block", "N/A"),
                    },
                }
                self.telegram.send_alert(alert_data)
            except Exception as e:
                print(f"⚠️  Telegram send error: {e}")

        # --- 2. SAVE TO DAILY JSON FILE ---
        try:
            log_entry = {
                "timestamp": get_timestamp(),
                "alert": alert,
                "transaction": tx_data,
            }
            if ml_result:
                log_entry["ml_result"] = ml_result

            filename = f"alerts_{get_date_string()}.json"
            filepath = os.path.join(ALERTS_DIR, filename)

            existing = load_json(filepath)
            existing.append(log_entry)
            save_json(existing, filepath)
        except Exception as e:
            print(f"⚠️  JSON log error: {e}")

        # --- 3. WRITE TO SYSTEM LOG ---
        try:
            with open(os.path.join(LOGS_DIR, "alerts.log"), "a", encoding="utf-8") as f:
                f.write(
                    f"{get_timestamp()} | "
                    f"{tx_data.get('chain', 'unknown')} | "
                    f"{alert['type']} | "
                    f"{alert.get('severity', 'LOW')} | "
                    f"{tx_data.get('hash', 'N/A')[:20]} | "
                    f"{tx_data.get('value_eth', 0):.4f} {tx_data.get('native_symbol', '')}\n"
                )
        except Exception as e:
            print(f"⚠️  System log error: {e}")

    # ================================================================
    # TRANSACTION ANALYSIS
    # ================================================================
    def analyze_transaction(self, chain_key, tx, block_num):
        """
        Analyze a transaction on a specific chain.

        Returns:
            (alerts, tx_data, ml_result)
        """
        try:
            w3 = self.connections[chain_key]
            chain_config = self.chain_configs[chain_key]

            tx_hash = tx.hash
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
            except Exception:
                receipt = None

            # Build tx_data
            tx_data = {
                "chain": chain_key,
                "chain_name": chain_config["name"],
                "native_symbol": chain_config["native_symbol"],
                "explorer": chain_config["explorer"],
                "hash": tx_hash.hex(),
                "block": block_num,
                "from": tx["from"],
                "to": tx.get("to", "0x0"),
                "value_eth": wei_to_eth(tx["value"], w3),
                "gas_price_gwei": wei_to_gwei(tx["gasPrice"], w3),
                "gas": tx["gas"],
                "gas_used": receipt["gasUsed"] if receipt else 0,
                "input_length": len(tx["input"]),
                "is_contract": 1 if not tx.get("to") or tx["to"] == "0x0" else 0,
                "success": 1 if receipt and receipt.get("status") == 1 else 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            alerts = []
            ml_result = None

            # ---- RULE-BASED ALERTS ----

            # 1. Large transfer
            if tx_data["value_eth"] > LARGE_TRANSFER_THRESHOLD_ETH:
                alerts.append({
                    "type": "LARGE_TRANSFER",
                    "severity": "HIGH",
                    "details": (
                        f"{tx_data['value_eth']:.4f} {chain_config['native_symbol']} "
                        f"transferred on {chain_config['name']}"
                    ),
                })

            # 2. High gas price
            if tx_data["gas_price_gwei"] > HIGH_GAS_THRESHOLD_GWEI:
                alerts.append({
                    "type": "HIGH_GAS_PRICE",
                    "severity": "MEDIUM",
                    "details": f"{tx_data['gas_price_gwei']:.0f} Gwei on {chain_config['name']}",
                })

            # 3. Contract deployment
            if tx_data["is_contract"] == 1:
                alerts.append({
                    "type": "CONTRACT_DEPLOYMENT",
                    "severity": "MEDIUM",
                    "details": f"New contract on {chain_config['name']} by {tx_data['from'][:10]}...",
                })

            # 4. Failed transaction
            if tx_data["success"] == 0:
                alerts.append({
                    "type": "FAILED_TRANSACTION",
                    "severity": "LOW",
                    "details": f"Transaction failed on {chain_config['name']}",
                })

            # 5. Monitored address activity
            monitored = MONITORED_ADDRESSES.get(chain_key, [])
            for addr in monitored:
                if tx_data["from"].lower() == addr.lower():
                    alerts.append({
                        "type": "MONITORED_ADDRESS_ACTIVITY",
                        "severity": "INFO",
                        "details": f"Activity from monitored address {addr[:10]}... on {chain_config['name']}",
                    })

            # ---- ML-BASED DETECTION ----
            if self.ml_enabled:
                try:
                    ml_result = self.ml_detector.predict(tx_data)
                    if ml_result and ml_result.get("is_anomaly"):
                        alerts.append({
                            "type": "ML_ANOMALY_DETECTED",
                            "severity": "HIGH",
                            "details": f"ML anomaly score: {ml_result['score']:.3f}",
                            "confidence": ml_result.get("confidence", 0),
                        })
                except Exception as e:
                    print(f"⚠️  ML error: {e}")

            return alerts, tx_data, ml_result

        except Exception as e:
            print(f"⚠️  analyze_transaction error: {e}")
            return [], None, None

    # ================================================================
    # BLOCK PROCESSING
    # ================================================================
    def process_block(self, chain_key, block_num):
        """Process all transactions in a block on a specific chain."""
        try:
            w3 = self.connections[chain_key]
            block = w3.eth.get_block(block_num, full_transactions=True)

            monitored = MONITORED_ADDRESSES.get(chain_key, [])
            if not monitored:
                return

            for tx in block.transactions:
                tx_hash = tx.hash.hex()

                if tx_hash in self.processed_txs:
                    continue

                self.processed_txs.add(tx_hash)

                tx_from = tx.get("from", "").lower()
                tx_to = tx.get("to", "").lower() if tx.get("to") else ""

                for address in monitored:
                    address_lower = address.lower()

                    if tx_from == address_lower or tx_to == address_lower:
                        alerts, tx_data, ml_result = self.analyze_transaction(
                            chain_key, tx, block_num
                        )

                        if alerts and tx_data:
                            self.alert_count += 1
                            self._print_alert(
                                chain_key, block_num, tx_hash, tx_data, alerts, ml_result)

                            # Log every alert
                            for alert in alerts:
                                self.log_alert(alert, tx_data, ml_result)

                        break  # move to next tx

        except Exception as e:
            print(
                f"⚠️  Error processing block {block_num} on {chain_key}: {e}")

    def _print_alert(self, chain_key, block_num, tx_hash, tx_data, alerts, ml_result):
        """Pretty-print an alert to the console."""
        chain_config = self.chain_configs[chain_key]
        symbol = chain_config["native_symbol"]

        print("\n" + "=" * 70)
        print(f"🚨 ALERT #{self.alert_count} | {get_timestamp()}")
        print("=" * 70)
        print(f"Chain: {chain_config['name']} ({chain_key})")
        print(f"Block: {block_num}")
        print(f"Tx:    {tx_hash[:20]}...")
        print(f"From:  {tx_data['from'][:30]}...")
        print(f"To:    {tx_data['to'][:30]}...")
        print(f"Value: {tx_data['value_eth']:.6f} {symbol}")

        if ml_result and ml_result.get("is_anomaly"):
            print(f"🤖 ML Score: {ml_result['score']:.3f}")
            print(f"   Confidence: {ml_result.get('confidence', 0):.3f}")

        for alert in alerts:
            print(f"\n⚠️  [{alert['severity']}] {alert['type']}")
            print(f"   {alert['details']}")

    # ================================================================
    # LIVE MONITORING
    # ================================================================
    def live_monitor(self):
        """Continuous live monitoring across all chains."""
        print("\n" + "=" * 60)
        print("🔄 STARTING LIVE MULTI-CHAIN MONITORING")
        print("=" * 60)
        print(f"Chains active: {len(self.connections)}")
        for chain_key, config in self.chain_configs.items():
            print(f"  • {config['name']} ({chain_key})")
        print(
            f"ML detection: {'✅ ENABLED' if self.ml_enabled else '❌ DISABLED'}")
        print(f"Alerts logged to: {ALERTS_DIR}/alerts_*.json")
        print("Press Ctrl+C to stop")
        print("=" * 60)

        try:
            while True:
                for chain_key in self.connections:
                    try:
                        w3 = self.connections[chain_key]
                        current_block = w3.eth.block_number
                        last_block = self.last_blocks.get(
                            chain_key, current_block)

                        if current_block > last_block:
                            # Limit how far back we go in one loop (avoid flood)
                            start = max(last_block + 1, current_block - 20)

                            for block_num in range(start, current_block + 1):
                                print(
                                    f"\r📦 [{chain_key}] block {block_num}...",
                                    end="",
                                )
                                self.process_block(chain_key, block_num)

                            self.last_blocks[chain_key] = current_block
                            print(
                                f"\r✅ [{chain_key}] up to block {current_block} | "
                                f"Alerts: {self.alert_count}   ",
                                end="",
                            )
                    except Exception as e:
                        print(f"\n⚠️  Chain {chain_key} error: {e}")

                time.sleep(LIVE_CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("🛑 MONITORING STOPPED")
            print(f"Total alerts detected: {self.alert_count}")
            print(f"Transactions processed: {len(self.processed_txs)}")
            print("=" * 60)

    # ================================================================
    # HISTORICAL SCAN
    # ================================================================
    def scan_address(self, chain_key, address, num_blocks=BLOCKS_TO_SCAN):
        """Scan historical blocks for a specific address on a specific chain."""
        if chain_key not in self.connections:
            print(f"❌ Chain {chain_key} not connected")
            return

        w3 = self.connections[chain_key]
        chain_config = self.chain_configs[chain_key]

        print(f"\n🔍 Scanning {address[:15]}... on {chain_config['name']}")
        print(f"Looking back {num_blocks} blocks...")

        current_block = w3.eth.block_number
        start_block = max(0, current_block - num_blocks)
        address_lower = address.lower()

        found_txs = 0
        alerts_found = 0

        for block_num in range(start_block, current_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)

                for tx in block.transactions:
                    tx_from = tx.get("from", "").lower()
                    tx_to = tx.get("to", "").lower() if tx.get("to") else ""

                    if tx_from == address_lower or tx_to == address_lower:
                        found_txs += 1
                        alerts, _tx_data, _ = self.analyze_transaction(
                            chain_key, tx, block_num
                        )

                        if alerts:
                            alerts_found += 1
                            print(
                                f"\n📝 Block {block_num} | Tx: {tx.hash.hex()[:20]}..."
                            )
                            for alert in alerts:
                                print(
                                    f"  ⚠️  [{alert['severity']}] "
                                    f"{alert['type']}: {alert['details']}"
                                )

                if block_num % 10 == 0:
                    progress = ((block_num - start_block) / num_blocks) * 100
                    print(
                        f"\rProgress: {progress:.0f}% | Found: {found_txs} txs",
                        end="",
                    )

            except Exception:
                continue

        print("\n\n✅ Scan complete!")
        print(f"Transactions found: {found_txs}")
        print(f"Alerts triggered: {alerts_found}")


# ====================================================================
# MAIN MENU
# ====================================================================
def main():
    print("=" * 60)
    print("🔒 MULTI-CHAIN SECURITY MONITOR")
    print("=" * 60)

    try:
        monitor = SecurityMonitor()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your RPC URLs and API keys in config.py")
        return

    while True:
        print("\nSelect mode:")
        print("1. Live monitoring (all chains, real-time)")
        print("2. Scan specific address (historical)")
        print("3. View recent alerts")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            monitor.live_monitor()

        elif choice == "2":
            # Ask which chain
            available = list(monitor.connections.keys())
            if not available:
                print("❌ No chains connected")
                continue

            print("\nAvailable chains:")
            for i, chain_key in enumerate(available, 1):
                cfg = monitor.chain_configs[chain_key]
                print(f"  {i}. {cfg['name']} ({chain_key})")

            try:
                chain_choice = int(input("Select chain number: "))
                if not (1 <= chain_choice <= len(available)):
                    print("⚠️  Invalid chain choice")
                    continue
                chain_key = available[chain_choice - 1]
            except ValueError:
                print("⚠️  Invalid input")
                continue

            address = input("Enter address: ").strip()
            if not address.startswith("0x") or len(address) != 42:
                print("⚠️  Invalid address format!")
                continue

            blocks_input = input(
                f"Blocks to scan (default {BLOCKS_TO_SCAN}): ").strip()
            blocks = int(blocks_input) if blocks_input else BLOCKS_TO_SCAN

            monitor.scan_address(chain_key, address, blocks)

        elif choice == "3":
            alert_files = [
                f for f in os.listdir(ALERTS_DIR) if f.startswith("alerts_")
            ]
            if not alert_files:
                print("No alerts found.")
                continue

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
                tx = alert.get("transaction", {})
                print(f"\n{alert.get('timestamp', 'N/A')}")
                print(f"  Chain: {tx.get('chain_name', 'Unknown')}")
                print(
                    f"  Type:  {alert.get('alert', {}).get('type', 'Unknown')}")
                print(
                    f"  Info:  {alert.get('alert', {}).get('details', 'No details')}")

        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
