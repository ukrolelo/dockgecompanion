#!/usr/bin/env python3
"""
Dockge Companion - Interactive Terminal User Interface

A beautiful, interactive terminal interface for managing Docker container digests
with arrow key navigation, real-time status updates, and rollback capabilities.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.simple_tui import SimpleDockgeCompanionTUI

    if __name__ == '__main__':
        tui = SimpleDockgeCompanionTUI()
        tui.run()

except ImportError as e:
    print("❌ Required packages not installed. Please install:")
    print("   pip install rich")
    print(f"\nError details: {e}")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n👋 Goodbye!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)