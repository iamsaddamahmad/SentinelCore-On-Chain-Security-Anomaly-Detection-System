# data_collector.py
# ============================================================
# PHASE 1: MULTI-CHAIN DATA COLLECTOR
# Collects transaction data for each chain separately
# ============================================================

import os
import time
import argparse
from datetime import datetime, timezone

import pandas as pd
from web3 import Web3

from config import CHAINS, DATA_DIR
from utils import create_directories, print_progress, Timer


class DataCollector:
    """Collects and processes blockchain transaction data per chain"""

    def __init__(self, chain_key):
        if chain_key not in CHAINS:
            raise ValueError(
                f"Unknown chain: {chain_key}. Valid: {list(CHAINS.keys())}")

        self.chain_key = chain_key
        self.chain_config = CHAINS[chain_key]

        print(f"🔗 DataCollector for {self.chain_config['name']}")

        # Connect
        self.w3 = Web3(Web3.HTTPProvider(
            self.chain_config["rpc_url"],
            request_kwargs={"timeout": 30},
        ))

        # PoA middleware for BSC / Polygon
        if chain_key in ("bsc", "polygon"):
            try:
                from web3.middleware import ExtraDataToPOAMiddleware
                self.w3.middleware_onion.inject(
                    ExtraDataToPOAMiddleware, layer=0)
            except ImportError:
                from web3.middleware import geth_poa_middleware
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not self.w3.is_connected():
            raise ConnectionError(
                f"Failed to connect to {self.chain_config['name']}")

        print(f"✅ Connected (Block: {self.w3.eth.block_number})")
        create_directories()

    def collect_transactions(self, num_blocks=100, save=True):
        """Collect transactions from N blocks"""
        print(
            f"\n📊 Collecting {num_blocks} blocks from {self.chain_config['name']}...")

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
                            'chain': self.chain_key,
                            'block_number': block_num,
                            'timestamp': block.timestamp,
                            'block_time': datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat(),
                            'hash': tx.hash.hex(),
                            'from': tx['from'],
                            'to': tx.get('to', '0x0'),
                            'value_eth': float(self.w3.from_wei(tx['value'], 'ether')),
                            'gas_price_gwei': float(self.w3.from_wei(tx['gasPrice'], 'gwei')),
                            'gas': tx['gas'],
                            'gas_used': receipt['gasUsed'] if receipt else 0,
                            'input_length': len(tx['input']),
                            'is_contract': 1 if not tx.get('to') or tx['to'] == '0x0' else 0,
                            'success': 1 if receipt and receipt.get('status') == 1 else 0,
                        }
                        transactions.append(tx_data)
                    except Exception:
                        continue

                # Progress
                done = i + 1
                total = current_block - start_block + 1
                print_progress(done, total,
                               prefix=f'[{self.chain_key}] block {block_num}',
                               suffix=f'| {len(transactions)} txs')

                time.sleep(0.02)

            except Exception as e:
                print(f"\n⚠️ Error on block {block_num}: {e}")
                continue

        timer.stop()
        print(f"\n✅ Collection complete in {timer.elapsed_str()}")

        df = pd.DataFrame(transactions)

        if df.empty:
            print("⚠️ No transactions collected!")
            return df

        print(f"\n📈 Statistics ({self.chain_config['name']}):")
        print(f"   Total transactions: {len(df)}")
        print(f"   Unique addresses: {df['from'].nunique()}")
        print(
            f"   Avg value: {df['value_eth'].mean():.6f} {self.chain_config['native_symbol']}")
        print(
            f"   Max value: {df['value_eth'].max():.4f} {self.chain_config['native_symbol']}")
        print(f"   Success rate: {(df['success'].sum() / len(df) * 100):.1f}%")

        if save:
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"transactions_{self.chain_key}_{date_str}_{len(df)}.csv"
            filepath = os.path.join(DATA_DIR, filename)
            df.to_csv(filepath, index=False)
            print(f"💾 Saved to: {filepath}")

        return df


def main():
    parser = argparse.ArgumentParser(description="Multi-chain data collector")
    parser.add_argument(
        "--chain",
        choices=list(CHAINS.keys()),
        default="ethereum",
        help="Which chain to collect from",
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=100,
        help="Number of blocks to collect",
    )
    args = parser.parse_args()

    collector = DataCollector(args.chain)
    collector.collect_transactions(num_blocks=args.blocks)


if __name__ == "__main__":
    main()
