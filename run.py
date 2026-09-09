# run.py - Complete Working Version
# ============================================================
# MASTER CONTROLLER - Run everything from one place
# ============================================================

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from config import *


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🔒  ON-CHAIN SECURITY SENTINEL  🔒                      ║
║                                                              ║
║     Complete System with ML + SNN Detection                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def show_menu():
    print("\n" + "="*60)
    print("📋 MAIN MENU")
    print("="*60)
    print("")
    print("   PHASE 1-3: DATA & MONITORING")
    print("   ─────────────────────────────")
    print("   1. 🚀 Run Live Monitor")
    print("   2. 📊 Collect Training Data")
    print("   3. 🔍 Scan Specific Address")
    print("")
    print("   PHASE 4: TRADITIONAL ML")
    print("   ──────────────────────")
    print("   4. 🤖 Train ML Anomaly Detector")
    print("   5. 🧪 Test ML Model")
    print("")
    print("   PHASE 5: SPIKING NEURAL NETWORK (NeuroChain Sentinel)")
    print("   ──────────────────────────────────────────────────────")
    print("   6. 🧠 Build/Train SNN Model")
    print("   7. 🔬 Run SNN Anomaly Detection")
    print("")
    print("   PHASE 6: OCI MULTI-AGENT SYSTEM")
    print("   ──────────────────────────────")
    print("   8. 🤝 Setup OCI Agents")
    print("")
    print("   SYSTEM")
    print("   ──────")
    print("   9. 📋 View Alert Logs")
    print("   10. ⚙️  Check System Status")
    print("   11. ❌ Exit")
    print("="*60)


def run_script(script_name):
    """Run a Python script using the current interpreter"""
    try:
        print(f"\n🔄 Running {script_name}...")
        print("="*50)
        # Use sys.executable to ensure we use the same Python
        result = subprocess.run(
            [sys.executable, script_name], capture_output=False)
        return result.returncode == 0
    except FileNotFoundError:
        print(f"❌ File not found: {script_name}")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def run_script_with_args(script_name, *args):
    """Run a Python script with arguments"""
    try:
        cmd = [sys.executable, script_name] + list(args)
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def check_status():
    """Check system status"""
    print("\n" + "="*60)
    print("🔍 SYSTEM STATUS")
    print("="*60)

    # Check Python environment
    print(f"\n🐍 Python: {sys.executable}")
    print(f"   Version: {sys.version}")

    # Check directories
    print("\n📁 Directories:")
    for d in ['data', 'models', 'logs', 'alerts']:
        exists = "✅" if os.path.exists(d) else "❌"
        print(f"  {exists} {d}/")

    # Check data files
    print("\n📊 Data Files:")
    data_files = [f for f in os.listdir('data') if f.endswith(
        '.csv')] if os.path.exists('data') else []
    if data_files:
        for f in sorted(data_files)[-3:]:
            size = os.path.getsize(os.path.join('data', f)) / 1024
            print(f"  📄 {f} ({size:.1f} KB)")
    else:
        print("  No data files found")

    # Check models
    print("\n🤖 Models:")
    if os.path.exists('models'):
        models = os.listdir('models')
        if models:
            for m in models:
                size = os.path.getsize(os.path.join('models', m)) / 1024
                print(f"  📄 {m} ({size:.1f} KB)")
        else:
            print("  No models found")
    else:
        print("  models/ directory not found")

    # Check alerts
    print("\n🚨 Alerts:")
    if os.path.exists('alerts'):
        alert_files = [f for f in os.listdir('alerts') if f.endswith('.json')]
        if alert_files:
            total_alerts = 0
            for f in alert_files:
                try:
                    with open(os.path.join('alerts', f), 'r') as file:
                        data = json.load(file)
                        total_alerts += len(data)
                except:
                    pass
            print(f"  Total alerts logged: {total_alerts}")
            print(f"  Alert files: {len(alert_files)}")
        else:
            print("  No alerts logged")
    else:
        print("  alerts/ directory not found")

    # Check config
    print("\n⚙️ Configuration:")
    if os.path.exists('config.py'):
        print("  ✅ config.py found")
        print(f"  Monitored addresses: {len(MONITORED_ADDRESSES)}")
        print(f"  Alert threshold: {LARGE_TRANSFER_THRESHOLD_ETH} ETH")
    else:
        print("  ❌ config.py not found")

    print("\n" + "="*60)


def view_alerts():
    """View alert logs"""
    alert_files = [f for f in os.listdir('alerts') if f.startswith(
        'alerts_')] if os.path.exists('alerts') else []

    if not alert_files:
        print("No alerts found.")
        input("\nPress Enter to continue...")
        return

    print("\n📋 ALERT LOGS")
    print("="*60)

    for i, f in enumerate(sorted(alert_files, reverse=True)):
        print(f"{i+1}. {f}")

    choice = input("\nSelect file to view (or press Enter to skip): ")

    if choice:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(alert_files):
                filepath = os.path.join('alerts', sorted(
                    alert_files, reverse=True)[idx])
                with open(filepath, 'r') as f:
                    data = json.load(f)

                print(f"\n📄 {filepath}")
                print(f"Total alerts: {len(data)}")
                print("\nRecent alerts:")

                for alert in data[-5:]:
                    print(f"\n{alert.get('timestamp', 'N/A')}")
                    print(
                        f"  Type: {alert.get('alert', {}).get('type', 'Unknown')}")
                    print(
                        f"  Details: {alert.get('alert', {}).get('details', 'No details')}")
                    tx = alert.get('transaction', {})
                    print(f"  Value: {tx.get('value_eth', 0):.4f} ETH")
        except (ValueError, IndexError, json.JSONDecodeError) as e:
            print(f"Error reading file: {e}")

    input("\nPress Enter to continue...")


def main():
    while True:
        clear_screen()
        show_banner()
        show_menu()

        choice = input("\nEnter choice (1-11): ")

        if choice == "1":
            print("\n🚀 Starting Live Monitor...")
            if run_script("monitor.py"):
                print("\n✅ Monitor session completed.")
            else:
                print("\n❌ Monitor failed to run properly.")
            input("\nPress Enter to continue...")

        elif choice == "2":
            run_script("data_collector.py")

        elif choice == "3":
            address = input("Enter Ethereum address: ")
            if address:
                # Create a temp script
                with open("temp_scan.py", "w") as f:
                    f.write(f"""
from monitor import SecurityMonitor
import sys
try:
    monitor = SecurityMonitor()
    monitor.scan_address("{address}")
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
""")
                run_script("temp_scan.py")
                try:
                    os.remove("temp_scan.py")
                except:
                    pass
            input("\nPress Enter to continue...")

        elif choice == "4":
            run_script("ml_detector.py")

        elif choice == "5":
            run_script("ml_detector.py")

        elif choice == "6":
            run_script("snn_detector.py")

        elif choice == "7":
            run_script("snn_detector.py")

        elif choice == "8":
            print("\n🤝 OCI MULTI-AGENT SETUP")
            print("="*60)
            print("To setup OCI (Multi-Agent System):")
            print("\n1. Clone the repository:")
            print("   git clone https://github.com/oxdev6/COI.git")
            print("\n2. Install dependencies:")
            print("   cd COI")
            print("   pnpm i")
            print("\n3. Configure environment:")
            print("   cp .env.example .env")
            print("   # Edit .env with your API keys")
            print("\n4. Run the system:")
            print("   pnpm dev")
            print("\n5. Use commands:")
            print("   !oci status - Check monitoring status")
            print("   !oci explain <txHash> - Get explanation")
            input("\nPress Enter to continue...")

        elif choice == "9":
            view_alerts()

        elif choice == "10":
            check_status()
            input("\nPress Enter to continue...")

        elif choice == "11":
            print("\nGoodbye! 👋")
            break

        else:
            print("Invalid choice!")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("\nPress Enter to exit...")
