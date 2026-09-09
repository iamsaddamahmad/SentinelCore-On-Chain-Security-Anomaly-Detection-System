# ml_detector.py
# ============================================================
# UPDATED: ML Anomaly Detector for Ethereum Fraud Dataset
# Compatible with the Kaggle dataset (columns: FLAG, Address, etc.)
# ============================================================

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
import json
from config import *
from utils import *


class MLAnomalyDetector:
    """ML-based anomaly detector for Ethereum transactions"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.model_stats = {}
        create_directories()

    def load_data(self, filename=None):
        """Load transaction data from CSV"""
        if filename:
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.exists(filepath):
                print(f"📂 Loading: {filename}")
                return pd.read_csv(filepath)

        # Find most recent data file
        csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

        if not csv_files:
            print("❌ No data files found! Run data_collector.py first.")
            return None

        latest_file = sorted(csv_files)[-1]
        filepath = os.path.join(DATA_DIR, latest_file)
        print(f"📂 Loading latest: {latest_file}")
        return pd.read_csv(filepath)

    def prepare_features(self, df):
        """
        Prepare features for ML training
        Using the Kaggle Ethereum Fraud Detection Dataset columns
        """
        # Feature columns available in this dataset
        feature_mapping = {
            'Sent tnx': 'sent_transactions',
            'Received Tnx': 'received_transactions',
            'Number of Created Contracts': 'created_contracts',
            'Unique Received From Addresses': 'unique_received_from',
            'Unique Sent To Addresses': 'unique_sent_to',
            'min value received': 'min_value_received',
            'max value received ': 'max_value_received',
            'avg val received': 'avg_value_received',
            'min val sent': 'min_value_sent',
            'max val sent': 'max_value_sent',
            'avg val sent': 'avg_value_sent',
            'total transactions (including tnx to create contract': 'total_transactions',
            'total Ether sent': 'total_ether_sent',
            'total ether received': 'total_ether_received',
            'total ether balance': 'total_ether_balance'
        }

        # Select available features
        available_features = []
        for col in feature_mapping.keys():
            if col in df.columns:
                available_features.append(col)

        if not available_features:
            print("❌ No feature columns found!")
            print(f"Available columns in dataset: {list(df.columns)}")
            return None

        # Also add ERC20 features if available
        erc20_features = [
            ' Total ERC20 tnxs',
            ' ERC20 total Ether received',
            ' ERC20 total ether sent',
            ' ERC20 min val rec',
            ' ERC20 max val rec',
            ' ERC20 avg val rec'
        ]

        for col in erc20_features:
            if col in df.columns:
                available_features.append(col)

        print(f"✅ Using {len(available_features)} features")
        self.feature_columns = available_features

        # Extract features
        X = df[available_features].fillna(0)

        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)

        return X

    def train(self, data=None, contamination=0.05):
        """
        Train the Isolation Forest model

        Args:
            data: DataFrame with transaction data
            contamination: Expected proportion of anomalies (fraud rate ~5%)
        """
        print("🧠 Training Isolation Forest model...")
        print("   Using Kaggle Ethereum Fraud Detection Dataset")

        if data is None:
            data = self.load_data()
            if data is None:
                return False

        X = self.prepare_features(data)
        if X is None:
            return False

        print(f"Training data shape: {X.shape}")
        print(f"Features: {list(X.columns)}")

        # Scale features
        print("📊 Scaling features...")
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        print("🌲 Training Isolation Forest...")
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            bootstrap=False
        )
        self.model.fit(X_scaled)

        # Save model
        model_path = os.path.join(MODELS_DIR, 'isolation_forest.pkl')
        scaler_path = os.path.join(MODELS_DIR, 'scaler.pkl')
        features_path = os.path.join(MODELS_DIR, 'features.json')

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        with open(features_path, 'w') as f:
            json.dump(self.feature_columns, f)

        # Save stats
        self.model_stats = {
            'training_date': get_timestamp(),
            'samples': len(X),
            'features': self.feature_columns,
            'contamination': contamination
        }

        stats_path = os.path.join(MODELS_DIR, 'model_stats.json')
        save_json(self.model_stats, stats_path)

        print(f"✅ Model saved to: {model_path}")
        print(f"✅ Scaler saved to: {scaler_path}")

        # Evaluate on training data
        self.evaluate(data)

        return True

    def load(self):
        """Load trained model"""
        model_path = os.path.join(MODELS_DIR, 'isolation_forest.pkl')
        scaler_path = os.path.join(MODELS_DIR, 'scaler.pkl')
        features_path = os.path.join(MODELS_DIR, 'features.json')

        if not os.path.exists(model_path):
            print("❌ Model not found! Train first.")
            return False

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)

        try:
            with open(features_path, 'r') as f:
                self.feature_columns = json.load(f)
        except:
            self.feature_columns = None

        print("✅ Model loaded successfully!")
        return True

    def predict(self, transaction_dict):
        """
        Predict if a transaction is anomalous

        Args:
            transaction_dict: Dictionary with transaction data

        Returns:
            dict: Prediction result
        """
        if self.model is None:
            if not self.load():
                return None

        # Extract features based on available columns
        features = []
        for col in self.feature_columns:
            if col in transaction_dict:
                features.append(transaction_dict[col])
            else:
                features.append(0)

        # Scale
        X_scaled = self.scaler.transform([features])

        # Predict
        prediction = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]

        return {
            'is_anomaly': prediction == -1,
            'score': float(score),
            'confidence': float(1 / (1 + np.exp(-abs(score)))),
            'features': dict(zip(self.feature_columns, features))
        }

    def evaluate(self, data=None):
        """Evaluate model performance with actual labels"""
        if self.model is None:
            if not self.load():
                return

        if data is None:
            data = self.load_data()
            if data is None:
                return

        X = self.prepare_features(data)
        if X is None:
            return

        X_scaled = self.scaler.transform(X)

        # Predict
        predictions = self.model.predict(X_scaled)
        anomalies = sum(1 for p in predictions if p == -1)
        normal = sum(1 for p in predictions if p == 1)

        print("\n📊 Model Evaluation:")
        print("="*50)
        print(f"Total transactions: {len(predictions)}")
        print(
            f"Anomalies detected: {anomalies} ({anomalies/len(predictions)*100:.2f}%)")
        print(
            f"Normal transactions: {normal} ({normal/len(predictions)*100:.2f}%)")

        # Compare with actual labels (FLAG column)
        if 'FLAG' in data.columns:
            actual = data['FLAG'].values
            # Convert -1 (anomaly) to 1, 1 (normal) to 0
            predicted = [1 if p == -1 else 0 for p in predictions]

            print("\n🎯 Accuracy vs Actual Labels:")
            print(f"   Accuracy: {accuracy_score(actual, predicted):.4f}")
            print(
                f"   Fraud detected: {sum(predicted)} (actual fraud: {sum(actual)})")

            print("\n📋 Classification Report:")
            print(classification_report(actual, predicted,
                  target_names=['Legitimate', 'Fraudulent']))

            print("Confusion Matrix:")
            print(confusion_matrix(actual, predicted))
        else:
            print("\n⚠️ No labels found in data (expected column: 'FLAG')")
            print("   Model is unsupervised - using anomaly scores only")

    def get_threat_level(self, transaction_dict):
        """Get threat level based on anomaly score"""
        result = self.predict(transaction_dict)
        if not result:
            return 'UNKNOWN'

        if result['is_anomaly']:
            score = abs(result['score'])
            if score > 0.8:
                return 'CRITICAL'
            elif score > 0.6:
                return 'HIGH'
            elif score > 0.4:
                return 'MEDIUM'
            else:
                return 'LOW'
        return 'SAFE'


def main():
    print("="*60)
    print("🤖 ML Anomaly Detector (Ethereum Fraud Dataset)")
    print("="*60)

    detector = MLAnomalyDetector()

    while True:
        print("\nSelect option:")
        print("1. Train new model")
        print("2. Load and evaluate model")
        print("3. Predict on sample transaction")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ")

        if choice == "1":
            detector.train()

        elif choice == "2":
            detector.load()
            detector.evaluate()

        elif choice == "3":
            if not detector.load():
                continue

            print("\nSample transaction features (from dataset):")
            sample = {
                'Sent tnx': 100,
                'Received Tnx': 50,
                'total Ether sent': 10.5,
                'total ether received': 5.2,
                'total transactions (including tnx to create contract': 150,
                'Number of Created Contracts': 0
            }

            result = detector.predict(sample)
            if result:
                print(f"\n📊 Result:")
                print(
                    f"  Is Anomaly: {'🚨 YES' if result['is_anomaly'] else '✅ NO'}")
                print(f"  Anomaly Score: {result['score']:.3f}")
                print(f"  Confidence: {result['confidence']:.3f}")
                print(f"  Threat Level: {detector.get_threat_level(sample)}")

        elif choice == "4":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
