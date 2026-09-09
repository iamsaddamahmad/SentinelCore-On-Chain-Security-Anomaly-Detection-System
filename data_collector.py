# data_collector.py
# ============================================================
# PHASE 1: DATA COLLECTOR
# Collects transaction data for analysis and ML training
# ============================================================

from web3 import Web3
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime
from config import *
from utils import *


class DataCollector:
    """Collects and processes blockchain transaction data"""

    def __init__(self):
        print("🔗 DataCollector initializing...")
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))

        if not self.w3.is_connected():
            raise ConnectionError(
                "Failed to connect to Ethereum. Check your API key.")

        print(f"✅ Connected to Ethereum (Block: {self.w3.eth.block_number})")
        create_directories()
        self.total_txs = 0

    def collect_transactions(self, num_blocks=100, save=True):
        """
        Collect transactions from specified number of blocks

        Args:
            num_blocks: Number of blocks to scan (default: 100)
            save: Whether to save to CSV (default: True)

        Returns:
            DataFrame with transaction data
        """
        print(f"\n📊 Collecting {num_blocks} blocks of transaction data...")

        current_block = self.w3.eth.block_number
        start_block = max(0, current_block - num_blocks)

        transactions = []
        timer = Timer().start()

        for i, block_num in enumerate(range(start_block, current_block + 1)):
            try:
                block = self.w3.eth.get_block(
                    block_num, full_transactions=True)

                for tx in block.transactions:
                    try:
                        receipt = self.w3.eth.get_transaction_receipt(tx.hash)

                        tx_data = {
                            'block_number': block_num,
                            'timestamp': block.timestamp,
                            'block_time': datetime.fromtimestamp(block.timestamp).isoformat(),
                            'hash': tx.hash.hex(),
                            'from': tx['from'],
                            'to': tx.get('to', '0x0'),
                            'value_eth': wei_to_eth(tx['value'], self.w3),
                            'gas_price_gwei': wei_to_gwei(tx['gasPrice'], self.w3),
                            'gas': tx['gas'],
                            'gas_used': receipt['gasUsed'] if receipt else 0,
                            'input_length': len(tx['input']),
                            'status': receipt['status'] if receipt else 0,
                            'is_contract': 1 if not tx.get('to') or tx['to'] == '0x0' else 0,
                            'success': 1 if receipt and receipt.get('status') == 1 else 0
                        }
                        transactions.append(tx_data)
                        self.total_txs += 1

                    except Exception as e:
                        # Skip this transaction on error
                        continue

                # Progress indicator
                progress = ((i + 1) / (current_block - start_block + 1)) * 100
                print_progress(i + 1, current_block - start_block + 1,
                               prefix=f'Block {block_num}',
                               suffix=f'| Collected: {len(transactions)} txs')

                # Rate limiting to avoid being blocked
                time.sleep(0.05)

            except Exception as e:
                print(f"\n⚠️ Error processing block {block_num}: {e}")
                continue

        timer.stop()
        print(f"\n✅ Collection complete in {timer.elapsed_str()}")

        df = pd.DataFrame(transactions)

        if df.empty:
            print("⚠️ No transactions collected!")
            return df

        print(f"\n📈 Statistics:")
        print(f"   Total transactions: {len(df)}")
        print(f"   Unique addresses: {df['from'].nunique()}")
        print(f"   Average value: {df['value_eth'].mean():.4f} ETH")
        print(f"   Max value: {df['value_eth'].max():.4f} ETH")
        print(f"   Success rate: {(df['success'].sum() / len(df) * 100):.1f}%")

        if save:
            filename = f"transactions_{get_date_string()}_{len(df)}.csv"
            filepath = os.path.join(DATA_DIR, filename)
            df.to_csv(filepath, index=False)
            print(f"💾 Saved to: {filepath}")

        return df

    def collect_address_history(self, address, num_blocks=500):
        """
        Collect all transactions for a specific address

        Args:
            address: Ethereum address
            num_blocks: Number of blocks to scan (default: 500)

        Returns:
            DataFrame with transaction history
        """
        print(f"\n🔍 Collecting history for {address[:10]}...")

        current_block = self.w3.eth.block_number
        start_block = max(0, current_block - num_blocks)
        address_lower = address.lower()

        transactions = []
        timer = Timer().start()

        for block_num in range(start_block, current_block + 1):
            try:
                block = self.w3.eth.get_block(
                    block_num, full_transactions=True)

                for tx in block.transactions:
                    tx_from = tx.get('from', '').lower()
                    tx_to = tx.get('to', '').lower() if tx.get('to') else ''

                    if tx_from == address_lower or tx_to == address_lower:
                        receipt = self.w3.eth.get_transaction_receipt(tx.hash)

                        tx_data = {
                            'block_number': block_num,
                            'timestamp': block.timestamp,
                            'hash': tx.hash.hex(),
                            'from': tx['from'],
                            'to': tx.get('to', '0x0'),
                            'value_eth': wei_to_eth(tx['value'], self.w3),
                            'gas_price_gwei': wei_to_gwei(tx['gasPrice'], self.w3),
                            'gas': tx['gas'],
                            'gas_used': receipt['gasUsed'] if receipt else 0,
                            'input_length': len(tx['input'])
                        }
                        transactions.append(tx_data)

                if block_num % 100 == 0:
                    print_progress(block_num - start_block, num_blocks,
                                   prefix='Scanning blocks',
                                   suffix=f'Found: {len(transactions)} txs')

            except Exception as e:
                continue

        timer.stop()
        print(f"\n✅ Collection complete in {timer.elapsed_str()}")

        df = pd.DataFrame(transactions)

        if df.empty:
            print("⚠️ No transactions found for this address")
            return df

        print(f"📈 Found {len(df)} transactions")

        # Save
        filename = f"address_{address[:10]}_{get_date_string()}.csv"
        filepath = os.path.join(DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        print(f"💾 Saved to: {filepath}")

        return df

    def collect_contract_interactions(self, contract_address, num_blocks=500):
        """
        Collect all interactions with a specific contract

        Args:
            contract_address: Contract address
            num_blocks: Number of blocks to scan

        Returns:
            DataFrame with contract interactions
        """
        print(
            f"\n📝 Collecting interactions with contract {contract_address[:10]}...")

        current_block = self.w3.eth.block_number
        start_block = max(0, current_block - num_blocks)
        contract_lower = contract_address.lower()

        interactions = []

        for block_num in range(start_block, current_block + 1):
            try:
                block = self.w3.eth.get_block(
                    block_num, full_transactions=True)

                for tx in block.transactions:
                    tx_to = tx.get('to', '').lower()

                    if tx_to == contract_lower:
                        interactions.append({
                            'block': block_num,
                            'hash': tx.hash.hex(),
                            'from': tx['from'],
                            'value_eth': wei_to_eth(tx['value'], self.w3),
                            'gas_price_gwei': wei_to_gwei(tx['gasPrice'], self.w3),
                            'input_length': len(tx['input'])
                        })

                if block_num % 100 == 0:
                    print_progress(block_num - start_block, num_blocks,
                                   prefix='Scanning',
                                   suffix=f'Found: {len(interactions)} interactions')

            except Exception as e:
                continue

        df = pd.DataFrame(interactions)
        print(f"\n✅ Found {len(df)} interactions with contract")
        return df


def main():
    print("="*60)
    print("📊 DATA COLLECTOR")
    print("="*60)

    try:
        collector = DataCollector()
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    while True:
        print("\nSelect collection type:")
        print("1. Collect general transactions (for ML training)")
        print("2. Collect specific address history")
        print("3. Collect contract interactions")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ")

        if choice == "1":
            blocks = input("Number of blocks (default 100): ")
            blocks = int(blocks) if blocks else 100
            collector.collect_transactions(blocks)

        elif choice == "2":
            address = input("Enter Ethereum address: ")
            blocks = input("Blocks to scan (default 500): ")
            blocks = int(blocks) if blocks else 500
            collector.collect_address_history(address, blocks)

        elif choice == "3":
            contract = input("Enter contract address: ")
            blocks = input("Blocks to scan (default 500): ")
            blocks = int(blocks) if blocks else 500
            collector.collect_contract_interactions(contract, blocks)

        elif choice == "4":
            print("Goodbye!")
            break

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
