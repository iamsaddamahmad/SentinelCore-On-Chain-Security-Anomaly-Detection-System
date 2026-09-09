# test_model.py
from ml_detector import MLAnomalyDetector
import pandas as pd
import numpy as np

# Load the trained model
detector = MLAnomalyDetector()
detector.load()

print("="*60)
print("🔬 Testing ML Model with Various Transaction Patterns")
print("="*60)

# Test cases from the dataset
test_cases = [
    {
        'name': 'Normal Transaction',
        'tx': {
            'Sent tnx': 10,
            'Received Tnx': 5,
            'Number of Created Contracts': 0,
            'Unique Received From Addresses': 3,
            'Unique Sent To Addresses': 2,
            'min value received': 0.1,
            'max value received ': 0.5,
            'avg val received': 0.3,
            'min val sent': 0.05,
            'max val sent': 0.2,
            'avg val sent': 0.1,
            'total transactions (including tnx to create contract': 15,
            'total Ether sent': 1.5,
            'total ether received': 0.8,
            'total ether balance': 0.3
        }
    },
    {
        'name': 'Suspicious - High Volume',
        'tx': {
            'Sent tnx': 1000,
            'Received Tnx': 10,
            'Number of Created Contracts': 0,
            'Unique Received From Addresses': 5,
            'Unique Sent To Addresses': 500,
            'min value received': 0.001,
            'max value received ': 0.1,
            'avg val received': 0.05,
            'min val sent': 0.001,
            'max val sent': 50.0,
            'avg val sent': 25.0,
            'total transactions (including tnx to create contract': 1010,
            'total Ether sent': 500.0,
            'total ether received': 1.0,
            'total ether balance': -499.0
        }
    },
    {
        'name': 'Suspicious - Many Contracts Created',
        'tx': {
            'Sent tnx': 50,
            'Received Tnx': 5,
            'Number of Created Contracts': 25,
            'Unique Received From Addresses': 2,
            'Unique Sent To Addresses': 10,
            'min value received': 0.1,
            'max value received ': 0.5,
            'avg val received': 0.3,
            'min val sent': 0.01,
            'max val sent': 0.1,
            'avg val sent': 0.05,
            'total transactions (including tnx to create contract': 75,
            'total Ether sent': 2.5,
            'total ether received': 1.0,
            'total ether balance': -1.5
        }
    },
    {
        'name': 'Normal - Active Wallet',
        'tx': {
            'Sent tnx': 200,
            'Received Tnx': 180,
            'Number of Created Contracts': 0,
            'Unique Received From Addresses': 100,
            'Unique Sent To Addresses': 90,
            'min value received': 0.001,
            'max value received ': 10.0,
            'avg val received': 2.5,
            'min val sent': 0.001,
            'max val sent': 8.0,
            'avg val sent': 1.8,
            'total transactions (including tnx to create contract': 380,
            'total Ether sent': 150.0,
            'total ether received': 200.0,
            'total ether balance': 50.0
        }
    },
    {
        'name': 'Highly Suspicious - Wash Trading Pattern',
        'tx': {
            'Sent tnx': 5000,
            'Received Tnx': 5000,
            'Number of Created Contracts': 0,
            'Unique Received From Addresses': 3,
            'Unique Sent To Addresses': 3,
            'min value received': 0.01,
            'max value received ': 0.01,
            'avg val received': 0.01,
            'min val sent': 0.01,
            'max val sent': 0.01,
            'avg val sent': 0.01,
            'total transactions (including tnx to create contract': 10000,
            'total Ether sent': 50.0,
            'total ether received': 50.0,
            'total ether balance': 0.0
        }
    }
]

print("\n📊 Test Results:")
print("="*60)

for test in test_cases:
    result = detector.predict(test['tx'])

    # Determine threat level
    threat = detector.get_threat_level(test['tx'])

    # Color coding
    status = "✅ SAFE" if not result['is_anomaly'] else "🚨 ANOMALY"

    print(f"\n{test['name']}:")
    print(f"  Status: {status}")
    print(f"  Threat Level: {threat}")
    print(f"  Anomaly Score: {result['score']:.3f}")
    print(f"  Confidence: {result['confidence']:.3f}")

    # Show which features contributed (top 3)
    if result['features']:
        features = sorted(result['features'].items(),
                          key=lambda x: abs(x[1]), reverse=True)[:3]
        print(
            f"  Key Features: {', '.join([f'{f}: {v:.2f}' for f, v in features])}")

print("\n" + "="*60)
print("💡 Interpretation:")
print("  - ANOMALY = Transaction pattern looks suspicious")
print("  - SAFE = Transaction pattern looks normal")
print("  - Higher confidence = More certain prediction")
print("="*60)
