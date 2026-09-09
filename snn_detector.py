# snn_detector.py
# ============================================================
# UPDATED: SNN Detector for Ethereum Fraud Dataset
# Compatible with columns: FLAG, Address, Sent tnx, etc.
# ============================================================

import torch
import numpy as np
import pandas as pd
import os
import json
from config import *
from utils import *


class SpikeEncoder:
    """Convert transaction features to spike trains"""

    def __init__(self, time_window=100):
        self.time_window = time_window

    def encode_transaction(self, transaction_dict):
        """
        Encode transaction features as spike trains
        Using features from the Kaggle dataset
        """
        # Extract and normalize features
        features = []

        # Transaction volume features
        sent_tnx = min(transaction_dict.get('Sent tnx', 0) / 1000, 1.0)
        features.append(sent_tnx)

        received_tnx = min(transaction_dict.get('Received Tnx', 0) / 1000, 1.0)
        features.append(received_tnx)

        # Ether amounts (normalized)
        ether_sent = min(transaction_dict.get(
            'total Ether sent', 0) / 1000, 1.0)
        features.append(ether_sent)

        ether_received = min(transaction_dict.get(
            'total ether received', 0) / 1000, 1.0)
        features.append(ether_received)

        # Contract creation
        created_contracts = min(transaction_dict.get(
            'Number of Created Contracts', 0) / 10, 1.0)
        features.append(created_contracts)

        # Unique addresses
        unique_sent = min(transaction_dict.get(
            'Unique Sent To Addresses', 0) / 100, 1.0)
        features.append(unique_sent)

        unique_received = min(transaction_dict.get(
            'Unique Received From Addresses', 0) / 100, 1.0)
        features.append(unique_received)

        # Generate spike trains
        spike_rates = [f * 100 for f in features]
        spikes = []

        for rate in spike_rates:
            spike_train = torch.zeros(self.time_window)
            for t in range(self.time_window):
                if np.random.random() < rate / self.time_window:
                    spike_train[t] = 1
            spikes.append(spike_train)

        return torch.stack(spikes)


class SNNAnomalyDetector:
    """SNN detector for Ethereum fraud detection"""

    def __init__(self):
        self.encoder = SpikeEncoder()
        self.trained = False
        self.threshold = 0.5
        print("🧠 SNN Anomaly Detector initialized for Ethereum dataset")

    def encode_dataset(self, df):
        """Encode the entire dataset as spike sequences"""
        encoded = []
        for _, row in df.iterrows():
            # Convert row to dict with only relevant features
            tx_dict = {
                'Sent tnx': row.get('Sent tnx', 0),
                'Received Tnx': row.get('Received Tnx', 0),
                'total Ether sent': row.get('total Ether sent', 0),
                'total ether received': row.get('total ether received', 0),
                'Number of Created Contracts': row.get('Number of Created Contracts', 0),
                'Unique Sent To Addresses': row.get('Unique Sent To Addresses', 0),
                'Unique Received From Addresses': row.get('Unique Received From Addresses', 0)
            }
            spikes = self.encoder.encode_transaction(tx_dict)
            encoded.append(spikes)
        return encoded

    def train_simple(self, data, epochs=10):
        """
        Simple SNN training for demonstration

        In practice, you'd use BindsNET for full STDP training
        This is a simplified version for compatibility
        """
        print("🧠 Training SNN (simplified version)...")
        print("   Using features from Ethereum Fraud Dataset")

        if isinstance(data, pd.DataFrame):
            encoded_data = self.encode_dataset(data)
        else:
            encoded_data = data

        # Simple Hebbian-like learning
        # For demonstration, we just learn the average spike pattern
        avg_spikes = torch.zeros(7, 100)  # 7 features, 100 time steps

        for seq in encoded_data[:1000]:  # Use first 1000 for training
            avg_spikes += seq

        avg_spikes /= min(1000, len(encoded_data))

        # Store as pattern template
        self.pattern = avg_spikes

        # Calculate threshold for anomaly detection
        self.threshold = avg_spikes.mean() * 1.5

        self.trained = True
        print("✅ SNN training complete!")
        return True

    def detect_anomalies(self, transaction_sequence):
        """Detect anomalies in a sequence of transactions"""
        if not self.trained:
            print("⚠️ Model not trained!")
            return None

        if isinstance(transaction_sequence, pd.DataFrame):
            encoded_data = self.encode_dataset(transaction_sequence)
        else:
            encoded_data = [self.encoder.encode_transaction(
                tx) for tx in transaction_sequence]

        results = []

        for i, spikes in enumerate(encoded_data):
            # Compare with learned pattern
            similarity = torch.cosine_similarity(
                spikes.flatten(), self.pattern.flatten(), dim=0)
            is_anomaly = similarity < self.threshold

            results.append({
                'index': i,
                'is_anomaly': is_anomaly.item() if torch.is_tensor(is_anomaly) else is_anomaly,
                'similarity': similarity.item() if torch.is_tensor(similarity) else similarity
            })

        return results

    def get_threat_summary(self, transaction_sequence):
        """Get threat summary for a transaction sequence"""
        results = self.detect_anomalies(transaction_sequence)
        if not results:
            return None

        anomalies = [r for r in results if r['is_anomaly']]

        return {
            'total_transactions': len(results),
            'anomalies_detected': len(anomalies),
            'anomaly_rate': len(anomalies) / len(results) * 100 if results else 0,
            'details': results
        }


def main():
    print("="*60)
    print("🧠 SNN Anomaly Detector (Ethereum Fraud Dataset)")
    print("="*60)

    detector = SNNAnomalyDetector()

    while True:
        print("\nSelect option:")
        print("1. Train on dataset")
        print("2. Test with sample data")
        print("3. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":
            # Load dataset
            data_files = [f for f in os.listdir(
                DATA_DIR) if f.endswith('.csv')]
            if not data_files:
                print("❌ No data files found!")
                continue

            latest = sorted(data_files)[-1]
            df = pd.read_csv(os.path.join(DATA_DIR, latest))
            print(f"Loaded {len(df)} records")

            # Train
            detector.train_simple(df.head(1000))

        elif choice == "2":
            if not detector.trained:
                print("⚠️ Train first!")
                continue

            # Create sample transactions
            sample_txs = [
                {'Sent tnx': 500, 'Received Tnx': 200, 'total Ether sent': 100, 'total ether received': 50,
                 'Number of Created Contracts': 0, 'Unique Sent To Addresses': 50, 'Unique Received From Addresses': 30},
                {'Sent tnx': 5000, 'Received Tnx': 50, 'total Ether sent': 1000, 'total ether received': 10,
                 'Number of Created Contracts': 0, 'Unique Sent To Addresses': 5, 'Unique Received From Addresses': 2},
                {'Sent tnx': 10, 'Received Tnx': 5, 'total Ether sent': 1, 'total ether received': 0.5,
                 'Number of Created Contracts': 0, 'Unique Sent To Addresses': 3, 'Unique Received From Addresses': 2},
            ]

            results = detector.detect_anomalies(sample_txs)
            if results:
                print("\n📊 Detection Results:")
                for r in results:
                    print(
                        f"  Tx {r['index']+1}: {'🚨 ANOMALY' if r['is_anomaly'] else '✅ Normal'}")
                    print(f"     Similarity: {r['similarity']:.3f}")

        elif choice == "3":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
