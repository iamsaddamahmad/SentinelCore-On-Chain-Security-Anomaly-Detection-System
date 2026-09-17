# chain_manager.py
# ============================================================
# MULTI-CHAIN MANAGER
# Handles connections to multiple EVM chains
# ============================================================

from web3 import Web3

from config import CHAINS, MONITORED_ADDRESSES


class ChainManager:
    """Manages Web3 connections to multiple EVM chains"""

    def __init__(self):
        self.chains = {}
        self.connections = {}
        self._initialize()

    def _initialize(self):
        """Initialize connections to all enabled chains"""
        print("🔗 Initializing multi-chain connections...")

        for chain_key, chain_config in CHAINS.items():
            if not chain_config.get("enabled", False):
                continue

            try:
                w3 = Web3(Web3.HTTPProvider(
                    chain_config["rpc_url"],
                    request_kwargs={'timeout': 30}
                ))

                if w3.is_connected():
                    block = w3.eth.block_number
                    print(f"  ✅ {chain_config['name']}: Block {block}")
                    self.chains[chain_key] = chain_config
                    self.connections[chain_key] = w3
                else:
                    print(f"  ❌ {chain_config['name']}: Failed to connect")
            except Exception as e:
                print(f"  ❌ {chain_config['name']}: {e}")

        print(f"✅ Connected to {len(self.connections)} chains")

    def get_connection(self, chain_key):
        """Get Web3 connection for a specific chain"""
        return self.connections.get(chain_key)

    def get_chain_config(self, chain_key):
        """Get configuration for a specific chain"""
        return self.chains.get(chain_key)

    def get_monitored_addresses(self, chain_key):
        """Get monitored addresses for a specific chain"""
        return MONITORED_ADDRESSES.get(chain_key, [])

    def get_all_chain_keys(self):
        """Get list of all connected chain keys"""
        return list(self.connections.keys())

    def get_block_number(self, chain_key):
        """Get current block number for a chain"""
        w3 = self.connections.get(chain_key)
        if w3:
            return w3.eth.block_number
        return None

    def address_involved(self, chain_key, tx, address):
        """Check if an address is involved in a transaction"""
        tx_from = tx.get('from', '').lower()
        tx_to = tx.get('to', '').lower() if tx.get('to') else ''
        address_lower = address.lower()
        return tx_from == address_lower or tx_to == address_lower


# Quick test
if __name__ == "__main__":
    print("=" * 60)
    print("🔗 Multi-Chain Connection Test")
    print("=" * 60)

    manager = ChainManager()

    print("\n📊 Connected Chains:")
    for chain_key in manager.get_all_chain_keys():
        config = manager.get_chain_config(chain_key)
        block = manager.get_block_number(chain_key)
        print(f"  • {config['name']}: Block {block}")

    print("\n🎯 Monitored Addresses:")
    for chain_key in manager.get_all_chain_keys():
        addresses = manager.get_monitored_addresses(chain_key)
        print(f"  • {chain_key}: {len(addresses)} addresses")
