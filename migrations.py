from app import app, db, LoanApplication
from datetime import datetime

def run_migrations():
    with app.app_context():
        # Check if the database needs to be updated
        try:
            # Try to access the new columns
            test = LoanApplication.query.first()
            if test:
                # Check if the new columns exist
                test.rejection_reason
                test.rejected_by
                test.rejected_by_id
                test.created_at
                test.updated_at
                test.status_changed_at
                print("Database schema is up to date.")
                return
        except Exception as e:
            print(f"Database needs migration: {e}")

        # Add new columns to the LoanApplication table
        try:
            # Create a backup of the database first
            print("Creating database backup...")
            import shutil
            import os
            from datetime import datetime

            backup_file = f"optimus_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2('optimus.db', backup_file)
            print(f"Backup created: {backup_file}")

            # Add new columns
            print("Adding new columns to the database...")

            # Add rejection tracking columns
            db.engine.execute('ALTER TABLE loan_application ADD COLUMN rejection_reason TEXT')
            db.engine.execute('ALTER TABLE loan_application ADD COLUMN rejected_by VARCHAR(64)')
            db.engine.execute('ALTER TABLE loan_application ADD COLUMN rejected_by_id INTEGER REFERENCES user(id)')

            # Add timestamp columns
            db.engine.execute('ALTER TABLE loan_application ADD COLUMN created_at DATETIME')
            db.engine.execute('ALTER TABLE loan_application ADD COLUMN updated_at DATETIME')
            db.engine.execute('ALTER TABLE loan_application ADD COLUMN status_changed_at DATETIME')

            # Initialize the timestamp fields with current time
            now = datetime.utcnow()
            db.engine.execute(f"UPDATE loan_application SET created_at = '{now}', updated_at = '{now}'")

            print("Migration completed successfully.")
        except Exception as e:
            print(f"Error during migration: {e}")
            print("Please restore from backup if needed.")

if __name__ == "__main__":
    run_migrations()
