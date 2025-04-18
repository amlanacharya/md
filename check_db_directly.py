import sqlite3
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Connect to the database
db_path = os.path.join(current_dir, 'optimus.db')
print(f"Connecting to database at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in the database:")
for table in tables:
    print(f"- {table[0]}")

    # Show schema for each table
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print("  Columns:")
    for column in columns:
        print(f"    {column[1]} ({column[2]})")

    # Show first row of each table
    try:
        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("  First row:")
            print(f"    {row}")
        else:
            print("  Table is empty")
    except sqlite3.Error as e:
        print(f"  Error querying table: {e}")

    print()

# Close the connection
conn.close()
