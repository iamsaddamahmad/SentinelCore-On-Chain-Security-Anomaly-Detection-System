# ml_detector.py
# ============================================================
# PHASE 4: TRADITIONAL ML ANOMALY DETECTION (Per-Chain)
# Trains a separate Isolation Forest for each chain
# ============================================================

import os
import json
import argparse

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from config import DATA_DIR, MODELS_DIR, CHAINS
from utils import create_directories, get_timestamp, load_json, save_json


class MLAnomalyDetector:
    """Per-chain ML anomaly detector using Isolation Forest"""

    # Features the model learns from — behavioral, chain-agnostic
    FEATURE_COLUMNS = [
        "value_eth",
        "gas_price_gwei",
        "gas",
        "gas_used",
        "input_length",
        "is_contract",
        "success",
    ]

    def __init__(self, chain_key="ethereum"):
        self.chain_key = chain_key
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = self.FEATURE_COLUMNS
        self.model_stats = {}
        create_directories()

    # ------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------
    def load_data(self, filename=None):
        """Load the most recent CSV for this chain"""
        if filename:
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.exists(filepath):
                print(f"📂 Loading: {filename}")
                return pd.read_csv(filepath)
            print(f"❌ File not found: {filename}")
            return None

        # Find most recent file for this chain
        pattern = f"transactions_{self.chain_key}_"
        csv_files = [
            f for f in os.listdir(DATA_DIR)
            if f.startswith(pattern) and f.endswith(".csv")
        ]

        if not csv_files:
            print(f"❌ No data files found for '{self.chain_key}'")
            print(f"   Run: python data_collector.py --chain {self.chain_key}")
            return None

        latest = sorted(csv_files)[-1]
        print(f"📂 Loading latest for {self.chain_key}: {latest}")
        return pd.read_csv(os.path.join(DATA_DIR, latest))

    # ------------------------------------------------------------
    # FEATURE PREPARATION
    # ------------------------------------------------------------
    def prepare_features(self, df):
        available = [c for c in self.feature_columns if c in df.columns]
        if not available:
            print(
                f"❌ No matching features found. DataFrame has: {list(df.columns)}")
            return None

        print(f"✅ Using features: {available}")
        X = df[available].fillna(0).replace([np.inf, -np.inf], 0)
        return X

    # ------------------------------------------------------------
    # TRAINING
    # ------------------------------------------------------------
    def train(self, data=None, contamination=0.01):
        """Train Isolation Forest for this chain"""
        print(f"\n🧠 Training ML model for '{self.chain_key}'...")

        if data is None:
            data = self.load_data()
            if data is None:
                return False

        X = self.prepare_features(data)
        if X is None or len(X) < 50:
            print(f"❌ Not enough data to train (need at least 50 rows)")
            return False

        print(f"Training samples: {len(X)}")
        print(f"Features: {list(X.columns)}")

        # Scale
        X_scaled = self.scaler.fit_transform(X)

        # Train
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            bootstrap=False,
        )
        self.model.fit(X_scaled)

        # Save with chain-specific names
        model_path = os.path.join(
            MODELS_DIR, f"isolation_forest_{self.chain_key}.pkl")
        scaler_path = os.path.join(MODELS_DIR, f"scaler_{self.chain_key}.pkl")
        features_path = os.path.join(
            MODELS_DIR, f"features_{self.chain_key}.json")

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        with open(features_path, "w") as f:
            json.dump(self.feature_columns, f)

        # Stats
        self.model_stats = {
            "chain": self.chain_key,
            "training_date": get_timestamp(),
            "samples": len(X),
            "features": self.feature_columns,
            "contamination": contamination,
        }
        save_json(self.model_stats,
                  os.path.join(MODELS_DIR, f"model_stats_{self.chain_key}.json"))

        print(f"✅ Model saved: {model_path}")
        print(f"✅ Scaler saved: {scaler_path}")

        self.evaluate(data)
        return True

    # ------------------------------------------------------------
    # LOADING
    # ------------------------------------------------------------
    def load(self):
        """Load trained model for this chain"""
        model_path = os.path.join(
            MODELS_DIR, f"isolation_forest_{self.chain_key}.pkl")
        scaler_path = os.path.join(MODELS_DIR, f"scaler_{self.chain_key}.pkl")

        if not os.path.exists(model_path):
            print(f"❌ Model not found for '{self.chain_key}'. Train it first.")
            return False

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        print(f"✅ ML model loaded for '{self.chain_key}'")
        return True

    # ------------------------------------------------------------
    # PREDICTION
    # ------------------------------------------------------------
    def predict(self, transaction_dict):
        if self.model is None and not self.load():
            return None

        features = []
        for col in self.feature_columns:
            val = transaction_dict.get(col, 0)
            try:
                features.append(float(val))
            except (ValueError, TypeError):
                features.append(0.0)

        import pandas as pd
        X_df = pd.DataFrame([features], columns=self.feature_columns)
        X_scaled = self.scaler.transform(X_df)

        prediction = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]

        return {
            "is_anomaly": bool(prediction == -1),
            "score": float(score),
            "confidence": float(1 / (1 + np.exp(-abs(score)))),
            "chain": self.chain_key,
            "features": dict(zip(self.feature_columns, [float(f) for f in features])),
        }

    # ------------------------------------------------------------
    # EVALUATION
    # ------------------------------------------------------------
    def evaluate(self, data=None):
        if self.model is None and not self.load():
            return

        if data is None:
            data = self.load_data()
            if data is None:
                return

        X = self.prepare_features(data)
        if X is None:
            return

        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)

        anomalies = sum(1 for p in predictions if p == -1)
        total = len(predictions)

        print(f"\n📊 Evaluation ({self.chain_key}):")
        print(f"   Total: {total}")
        print(f"   Anomalies: {anomalies} ({anomalies/total*100:.2f}%)")

    # ------------------------------------------------------------
    # THREAT LEVEL
    # ------------------------------------------------------------
    def get_threat_level(self, transaction_dict):
        result = self.predict(transaction_dict)
        if not result:
            return "UNKNOWN"
        if result["is_anomaly"]:
            score = abs(result["score"])
            if score > 0.8:
                return "CRITICAL"
            elif score > 0.6:
                return "HIGH"
            elif score > 0.4:
                return "MEDIUM"
            return "LOW"
        return "SAFE"


# ================================================================
# CLI ENTRY POINT
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Per-chain ML anomaly detector")
    parser.add_argument("--chain", choices=list(CHAINS.keys()), default="ethereum",
                        help="Which chain to train/evaluate")
    parser.add_argument("--train", action="store_true", help="Train the model")
    parser.add_argument("--evaluate", action="store_true",
                        help="Evaluate the model")
    parser.add_argument("--test", action="store_true",
                        help="Test with a sample tx")
    args = parser.parse_args()

    detector = MLAnomalyDetector(chain_key=args.chain)

    if args.train:
        detector.train()
    elif args.evaluate:
        if detector.load():
            detector.evaluate()
    elif args.test:
        if detector.load():
            sample = {
                "value_eth": 1000.0,
                "gas_price_gwei": 500.0,
                "gas": 100000,
                "gas_used": 80000,
                "input_length": 1000,
                "is_contract": 0,
                "success": 1,
            }
            result = detector.predict(sample)
            print(f"\n📊 Test result ({args.chain}):")
            print(f"   Anomaly: {result['is_anomaly']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Threat: {detector.get_threat_level(sample)}")
    else:
        # Interactive menu
        print("=" * 60)
        print(f"🤖 ML Anomaly Detector — {CHAINS[args.chain]['name']}")
        print("=" * 60)
        print("\n1. Train model")
        print("2. Load + evaluate")
        print("3. Test with sample")
        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            detector.train()
        elif choice == "2":
            if detector.load():
                detector.evaluate()
        elif choice == "3":
            if detector.load():
                sample = {
                    "value_eth": 1000.0, "gas_price_gwei": 500.0,
                    "gas": 100000, "gas_used": 80000,
                    "input_length": 1000, "is_contract": 0, "success": 1,
                }
                result = detector.predict(sample)
                print(f"\n📊 Result: anomaly={result['is_anomaly']}, "
                      f"score={result['score']:.3f}")


if __name__ == "__main__":
    main()
