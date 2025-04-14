# init_db.py
# This script initializes the database with the auth tables
# and creates default users for each role

from app import app, db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default users if they don't exist
        if User.query.filter_by(username='admin').first() is None:
            admin = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='author'
            )
            db.session.add(admin)
        
        if User.query.filter_by(username='checker').first() is None:
            checker = User(
                username='checker',
                email='checker@example.com',
                password='admin123',
                role='checker'
            )
            db.session.add(checker)
            
        if User.query.filter_by(username='maker').first() is None:
            maker = User(
                username='maker',
                email='maker@example.com',
                password='admin123',
                role='maker'
            )
            db.session.add(maker)
        
        # Commit changes
        db.session.commit()
        
        print("Database initialized with default users!")
        print("Admin - Username: admin, Password: adminpassword")
        print("Checker - Username: checker, Password: checkerpassword")
        print("Maker - Username: maker, Password: makerpassword")



if __name__ == '__main__':
    init_db()