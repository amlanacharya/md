#!/usr/bin/env python
"""
Database-Level Workflow Mode Checker

This script directly queries the SQLite database to check the current workflow mode.
It bypasses the application logic and ORM to provide a reliable way to verify the
actual value stored in the database.
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_workflow_mode():
    """Check the workflow mode directly in the database."""
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Connect to the database
    db_path = os.path.join(current_dir, 'optimus.db')
    print(f"Database path: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the system_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
        if not cursor.fetchone():
            print("Error: system_config table does not exist in the database.")
            return
        
        # Query the workflow mode
        cursor.execute("SELECT value, updated_at FROM system_config WHERE key='WORKFLOW_MODE'")
        result = cursor.fetchone()
        
        if not result:
            print("Error: WORKFLOW_MODE configuration not found in the database.")
            return
        
        mode = result[0]
        updated_at = result[1]
        
        # Print the result with formatting
        print("\n" + "="*50)
        print(f"CURRENT WORKFLOW MODE: {mode.upper()}")
        print("="*50)
        print(f"Last updated: {updated_at}")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print what this means
        if mode.lower() == 'auto':
            print("\nIn AUTO mode:")
            print("- Applications bypass the Author stage")
            print("- Checker approval directly sets status to APPROVED")
            print("- Author-related features are hidden in the UI")
        else:
            print("\nIn MANUAL mode:")
            print("- Applications go through all three stages: Maker → Checker → Author")
            print("- Checker approval sets status to PENDING_AUTHOR")
            print("- Author approval is required for final approval")
        
        print("\nTo change the mode, use one of these methods:")
        print("1. UI: Administration > Configuration Management")
        print("2. Command line: python fix_workflow_mode.py [auto|manual]")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_workflow_mode()
