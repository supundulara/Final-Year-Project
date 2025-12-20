#!/bin/bash
# scripts/quick_start.sh
# Quick start script for GNN dataset generation

echo "======================================================================"
echo "  GNN Dataset Generation - Quick Start"
echo "======================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run with sudo"
    echo "Usage: sudo bash scripts/quick_start.sh"
    exit 1
fi

echo "✓ Running as root"
echo ""

# Check if ovs-testcontroller is running
echo "🔍 Checking OpenFlow controller..."
if pgrep -f "ovs-testcontroller" > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":6653 "; then
    echo "✓ Controller is running (port 6653 active)"
else
    echo "⚠️  Controller not running, starting it..."
    ovs-testcontroller ptcp:6653 > /dev/null 2>&1 &
    sleep 2
    if pgrep -f "ovs-testcontroller" > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":6653 "; then
        echo "✓ Controller started"
    else
        echo "❌ Failed to start controller"
        echo "Please install: sudo apt install openvswitch-testcontroller"
        exit 1
    fi
fi
echo ""

# Clean up any previous Mininet state
echo "🧹 Cleaning up previous Mininet state..."
mn -c > /dev/null 2>&1
echo "✓ Cleanup complete"
echo ""

# Show menu
echo "======================================================================"
echo "  What would you like to do?"
echo "======================================================================"
echo ""
echo "1) Quick test (single scenario, 3 cameras, ~1 minute)"
echo "2) Quick dataset (3 scenarios, ~5 minutes)"
echo "3) Full dataset (16 scenarios, ~20 minutes)"
echo "4) Validate existing dataset"
echo "5) Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "Running quick test..."
        $(which python3) scripts/test_dataset_generation.py
        ;;
    2)
        echo ""
        echo "Generating quick dataset (3 scenarios)..."
        $(which python3) scripts/generate_dataset.py --quick
        ;;
    3)
        echo ""
        echo "Generating full dataset (16 scenarios)..."
        echo "⚠️  This will take approximately 20 minutes"
        read -p "Continue? (y/n): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            $(which python3) scripts/generate_dataset.py
        else
            echo "Cancelled."
        fi
        ;;
    4)
        echo ""
        echo "Validating dataset..."
        $(which python3) scripts/generate_dataset.py --validate
        ;;
    5)
        echo ""
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
echo "  Done!"
echo "======================================================================"
echo ""
echo "📁 Dataset location: data/dataset/"
echo "📖 Documentation: DATASET_README.md"
echo ""
echo "Next steps:"
echo "  - Inspect data: head data/dataset/nodes.csv"
echo "  - Load in Python: pd.read_csv('data/dataset/nodes.csv')"
echo "  - Start training your GNN!"
echo ""
