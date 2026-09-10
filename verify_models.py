# verify_models.py
import json
import os

import joblib

print("="*60)
print("🔍 Verifying Model Files")
print("="*60)

# Check if files exist
files = [
    'isolation_forest.pkl',
    'scaler.pkl',
    'features.json',
    'model_stats.json'
]

model_dir = 'models/'

for file in files:
    path = os.path.join(model_dir, file)
    if os.path.exists(path):
        size = os.path.getsize(path) / 1024
        print(f"✅ {file} - {size:.2f} KB")
    else:
        print(f"❌ {file} - MISSING")

print("\n" + "="*60)

# Load and inspect each file
try:
    # 1. Check features
    with open('models/features.json', 'r') as f:
        features = json.load(f)
    print(f"\n📋 Features ({len(features)}):")
    for i, f in enumerate(features[:5]):
        print(f"   {i+1}. {f}")
    if len(features) > 5:
        print(f"   ... and {len(features)-5} more")

    # 2. Check model stats
    with open('models/model_stats.json', 'r') as f:
        stats = json.load(f)
    print("\n📊 Model Stats:")
    print(f"   Training Date: {stats.get('training_date', 'Unknown')}")
    print(f"   Samples: {stats.get('samples', 'Unknown')}")
    print(f"   Contamination: {stats.get('contamination', 'Unknown')}")

    # 3. Check model
    model = joblib.load('models/isolation_forest.pkl')
    print("\n🧠 Model Info:")
    print(f"   Type: {type(model).__name__}")
    print(f"   Estimators: {model.n_estimators}")

    # 4. Check scaler
    scaler = joblib.load('models/scaler.pkl')
    print("\n📊 Scaler Info:")
    print(f"   Type: {type(scaler).__name__}")
    print(
        f"   Features: {scaler.mean_.shape[0] if hasattr(scaler, 'mean_') else 'Unknown'}")

except Exception as e:
    print(f"\n❌ Error loading files: {e}")

print("\n" + "="*60)
print("✅ Verification complete!")
