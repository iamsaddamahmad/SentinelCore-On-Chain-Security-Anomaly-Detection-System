# check_data.py
import pandas as pd
import os
from config import DATA_DIR

# Check if file exists
filepath = os.path.join(DATA_DIR, 'transaction_dataset.csv')

if os.path.exists(filepath):
    df = pd.read_csv(filepath)
    print(f"✅ Dataset loaded successfully!")
    print(f"📊 Shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    print("\n" + "="*60)

    # The label column is 'FLAG' in this dataset
    # FLAG: 1 = Fraudulent, 0 = Legitimate
    print(f"📈 Fraudulent transactions (FLAG=1): {df['FLAG'].sum()}")
    print(f"📉 Legitimate transactions (FLAG=0): {len(df) - df['FLAG'].sum()}")

    print("\n📊 Data Statistics:")
    print(f"   Total Addresses: {df['Address'].nunique()}")
    print(f"   Total Transactions: {df['Sent tnx'].sum():.0f}")
    print(f"   Total Ether Sent: {df['total Ether sent'].sum():.2f}")
    print(f"   Total Ether Received: {df['total ether received'].sum():.2f}")

    print(f"\n📝 First 5 rows:")
    print(df[['Address', 'FLAG', 'Sent tnx',
          'Received Tnx', 'total Ether sent']].head())

    # Save column mapping for reference
    print("\n💡 Key Columns for ML Training:")
    print("   Label: FLAG (1=fraud, 0=legitimate)")
    print("   Features: Sent tnx, Received Tnx, total Ether sent, total ether received, etc.")

else:
    print(f"❌ File not found at: {filepath}")
    print("Please download the dataset and place it here.")
