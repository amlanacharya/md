from app import app, db, User, ROLE_MAKER, ROLE_CHECKER, ROLE_AUTHOR

def list_users_by_role():
    with app.app_context():
        # Get all users grouped by role
        makers = User.query.filter_by(role=ROLE_MAKER).all()
        checkers = User.query.filter_by(role=ROLE_CHECKER).all()
        authors = User.query.filter_by(role=ROLE_AUTHOR).all()
        
        # Print makers
        print("\n=== MAKERS ===")
        if makers:
            for maker in makers:
                print(f"ID: {maker.id}, Username: {maker.username}, Email: {maker.email}, Available: {maker.available}")
        else:
            print("No makers found.")
            
        # Print checkers
        print("\n=== CHECKERS ===")
        if checkers:
            for checker in checkers:
                print(f"ID: {checker.id}, Username: {checker.username}, Email: {checker.email}, Available: {checker.available}")
        else:
            print("No checkers found.")
            
        # Print authors
        print("\n=== AUTHORS ===")
        if authors:
            for author in authors:
                print(f"ID: {author.id}, Username: {author.username}, Email: {author.email}, Available: {author.available}")
        else:
            print("No authors found.")

if __name__ == "__main__":
    list_users_by_role()
