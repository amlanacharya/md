from app import app, db, User
from datetime import datetime

def run_user_migrations():
    with app.app_context():
        # Check if the database needs to be updated
        try:
            # Try to access the new columns
            test = User.query.first()
            if test:
                # Check if the new columns exist
                test.product_expertise
                test.available
                print("User table schema is up to date.")
                return
        except Exception as e:
            print(f"User table needs migration: {e}")
            
        # Add new columns to the User table
        try:
            # Create a backup of the database first
            print("Creating database backup...")
            import shutil
            import os
            from datetime import datetime
            
            backup_file = f"loan_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2('loan_management.db', backup_file)
            print(f"Backup created: {backup_file}")
            
            # Add new columns
            print("Adding new columns to the User table...")
            
            # Add product expertise and availability columns
            db.engine.execute('ALTER TABLE user ADD COLUMN product_expertise VARCHAR(10)')
            db.engine.execute('ALTER TABLE user ADD COLUMN available BOOLEAN DEFAULT 1')
            
            print("User table migration completed successfully.")
        except Exception as e:
            print(f"Error during migration: {e}")
            print("Please restore from backup if needed.")

if __name__ == "__main__":
    run_user_migrations()
