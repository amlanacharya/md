import sqlite3
import os
import sys

def update_workflow_mode(mode):
    if mode not in ['auto', 'manual']:
        print(f"Error: Mode must be 'auto' or 'manual', got '{mode}'")
        return False
        
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Connect to the database
    db_path = os.path.join(current_dir, 'optimus.db')
    print(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the system_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
        if not cursor.fetchone():
            print("Creating system_config table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Check if WORKFLOW_MODE exists
        cursor.execute("SELECT * FROM system_config WHERE key='WORKFLOW_MODE'")
        if cursor.fetchone():
            # Update existing record
            print(f"Updating WORKFLOW_MODE to '{mode}'...")
            cursor.execute("UPDATE system_config SET value=? WHERE key='WORKFLOW_MODE'", (mode,))
        else:
            # Insert new record
            print(f"Inserting WORKFLOW_MODE with value '{mode}'...")
            cursor.execute(
                "INSERT INTO system_config (key, value, description) VALUES (?, ?, ?)",
                ('WORKFLOW_MODE', mode, 'Workflow mode: auto (bypass author) or manual (include author)')
            )
        
        # Commit changes
        conn.commit()
        
        # Verify the change
        cursor.execute("SELECT value FROM system_config WHERE key='WORKFLOW_MODE'")
        result = cursor.fetchone()
        if result and result[0] == mode:
            print(f"Successfully set WORKFLOW_MODE to '{mode}'")
            return True
        else:
            print(f"Failed to set WORKFLOW_MODE to '{mode}'")
            return False
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['auto', 'manual']:
        print("Usage: python fix_workflow_mode.py [auto|manual]")
        sys.exit(1)
    
    mode = sys.argv[1]
    if update_workflow_mode(mode):
        print("Done!")
        sys.exit(0)
    else:
        print("Failed to update workflow mode")
        sys.exit(1)
