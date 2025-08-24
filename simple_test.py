#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing basic imports...")
try:
    import config
    print("[OK] config imported")
except Exception as e:
    print(f"[ERROR] config import failed: {e}")

try:
    from services.notion_service import notion_service
    print("[OK] notion_service imported")
except Exception as e:
    print(f"[ERROR] notion_service import failed: {e}")

try:
    from services.machine_manager import machine_manager
    print("[OK] machine_manager imported")
except Exception as e:
    print(f"[ERROR] machine_manager import failed: {e}")

print("Basic import test completed.")