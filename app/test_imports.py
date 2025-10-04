#!/usr/bin/env python3
"""Test script to check if all imports work correctly."""

try:
    from main import app
    print("Main app imported successfully")
    print(f"App title: {app.title}")
    print("All imports working correctly!")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
