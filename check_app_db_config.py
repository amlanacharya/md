from app import app

# Print the database URI
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Check if the database file exists
import os
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
if os.path.exists(db_path):
    print(f"Database file exists at: {db_path}")
    print(f"File size: {os.path.getsize(db_path)} bytes")
else:
    print(f"Database file does not exist at: {db_path}")
