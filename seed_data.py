from app import app, db, User, LoanApplication, Product, PRODUCT_PL, PRODUCT_TW, PRODUCT_UTW, PRODUCT_UC, ROLE_MAKER, ROLE_CHECKER, ROLE_AUTHOR
from datetime import datetime, timedelta
import random
from seed_products import seed_products

def seed_database():
    with app.app_context():
        # First, seed the products
        seed_products()
        print("Starting database seeding...")

        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing loan applications...")
        LoanApplication.query.delete()
        db.session.commit()

        # Clear existing users
        print("Clearing existing users...")
        User.query.delete()
        db.session.commit()

        # Create 10 maker users
        print("Creating maker users...")
        makers = []
        for i in range(1, 11):
            maker = User(
                username=f"maker{i}",
                email=f"maker{i}@example.com",
                password=f"maker{i}123",
                role=ROLE_MAKER,
                available=True
            )
            db.session.add(maker)
            makers.append(maker)

        # Create 5 checker users with product expertise
        print("Creating checker users...")
        checkers = []
        product_types = [PRODUCT_PL, PRODUCT_TW, PRODUCT_UTW, PRODUCT_UC]
        for i in range(1, 6):
            # Assign product expertise in a round-robin fashion
            product_expertise = product_types[(i-1) % len(product_types)]
            checker = User(
                username=f"checker{i}",
                email=f"checker{i}@example.com",
                password=f"checker{i}123",
                role=ROLE_CHECKER,
                product_expertise=product_expertise,
                available=True if i < 4 else False  # Make some checkers unavailable
            )
            db.session.add(checker)
            checkers.append(checker)

        # Create 3 author users with product expertise
        print("Creating author users...")
        authors = []
        for i in range(1, 4):
            # Assign product expertise in a round-robin fashion
            product_expertise = product_types[(i-1) % len(product_types)]
            author = User(
                username=f"author{i}",
                email=f"author{i}@example.com",
                password=f"author{i}123",
                role=ROLE_AUTHOR,
                product_expertise=product_expertise,
                available=True if i < 3 else False  # Make one author unavailable
            )
            db.session.add(author)
            authors.append(author)

        db.session.commit()

        # Use the first maker, checker, and author for the applications
        maker = makers[0]
        checker = checkers[0]
        author = authors[0]

        # Sample data
        customer_names = [
            "John Smith", "Mary Johnson", "Robert Williams", "Patricia Brown",
            "Michael Jones", "Linda Davis", "William Miller", "Elizabeth Wilson",
            "David Moore", "Barbara Taylor", "Richard Anderson", "Jennifer Thomas",
            "Joseph Jackson", "Susan White", "Charles Harris", "Jessica Martin",
            "Thomas Thompson", "Sarah Garcia", "Christopher Martinez", "Karen Robinson"
        ]

        # Use the new product types
        loan_product_types = [PRODUCT_PL, PRODUCT_TW, PRODUCT_UTW, PRODUCT_UC]

        branch_locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                           "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

        bank_names = ["Chase Bank", "Bank of America", "Wells Fargo", "Citibank", "US Bank"]

        # Create loan applications in different states
        print("Creating loan applications...")

        # 1. Draft applications (5)
        for i in range(5):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(1, 10)),
                application_id=f"APPL-D-{100+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(loan_product_types),
                loan_amount=random.randint(10000, 100000),
                payment_amount=random.randint(5000, 50000),
                processing_fee=random.randint(500, 2000),
                rto=random.randint(100, 500),
                vap_amount=random.randint(200, 1000),
                beneficiary_name=random.choice(customer_names),
                beneficiary_account_number=f"{random.randint(10000000, 99999999)}",
                beneficiary_ifsc=f"IFSC{random.randint(10000, 99999)}",
                bank_name=random.choice(bank_names),
                branch_name=random.choice(branch_locations),
                maker=maker.username,
                maker_id=maker.id,
                status=LoanApplication.STATUS_DRAFT,
                created_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 3))
            )
            db.session.add(loan)

        # 2. Pending Checker applications (5)
        for i in range(5):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(1, 10)),
                application_id=f"APPL-PC-{200+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(loan_product_types),
                loan_amount=random.randint(10000, 100000),
                payment_amount=random.randint(5000, 50000),
                processing_fee=random.randint(500, 2000),
                rto=random.randint(100, 500),
                vap_amount=random.randint(200, 1000),
                beneficiary_name=random.choice(customer_names),
                beneficiary_account_number=f"{random.randint(10000000, 99999999)}",
                beneficiary_ifsc=f"IFSC{random.randint(10000, 99999)}",
                bank_name=random.choice(bank_names),
                branch_name=random.choice(branch_locations),
                maker=maker.username,
                maker_id=maker.id,
                status=LoanApplication.STATUS_PENDING_CHECKER,
                created_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 3)),
                status_changed_at=datetime.now() - timedelta(days=random.randint(0, 2))
            )
            db.session.add(loan)

        # 3. Pending Author applications (5)
        for i in range(5):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(1, 10)),
                application_id=f"APPL-PA-{300+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(loan_product_types),
                loan_amount=random.randint(10000, 100000),
                payment_amount=random.randint(5000, 50000),
                processing_fee=random.randint(500, 2000),
                rto=random.randint(100, 500),
                vap_amount=random.randint(200, 1000),
                beneficiary_name=random.choice(customer_names),
                beneficiary_account_number=f"{random.randint(10000000, 99999999)}",
                beneficiary_ifsc=f"IFSC{random.randint(10000, 99999)}",
                bank_name=random.choice(bank_names),
                branch_name=random.choice(branch_locations),
                maker=maker.username,
                maker_id=maker.id,
                checker=checker.username,
                checker_id=checker.id,
                status=LoanApplication.STATUS_PENDING_AUTHOR,
                created_at=datetime.now() - timedelta(days=random.randint(5, 10)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 4)),
                status_changed_at=datetime.now() - timedelta(days=random.randint(1, 3))
            )
            db.session.add(loan)

        # 4. Approved applications (5)
        for i in range(5):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(10, 20)),
                application_id=f"APPL-A-{400+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(loan_product_types),
                loan_amount=random.randint(10000, 100000),
                payment_amount=random.randint(5000, 50000),
                processing_fee=random.randint(500, 2000),
                rto=random.randint(100, 500),
                vap_amount=random.randint(200, 1000),
                beneficiary_name=random.choice(customer_names),
                beneficiary_account_number=f"{random.randint(10000000, 99999999)}",
                beneficiary_ifsc=f"IFSC{random.randint(10000, 99999)}",
                bank_name=random.choice(bank_names),
                branch_name=random.choice(branch_locations),
                maker=maker.username,
                maker_id=maker.id,
                checker=checker.username,
                checker_id=checker.id,
                author=author.username,
                author_id=author.id,
                status=LoanApplication.STATUS_APPROVED,
                created_at=datetime.now() - timedelta(days=random.randint(10, 15)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                status_changed_at=datetime.now() - timedelta(days=random.randint(1, 5))
            )
            db.session.add(loan)

        # 5. Rejected by Checker applications (3)
        rejection_reasons_checker = [
            "Incomplete documentation provided. Missing proof of income.",
            "Credit score below required threshold for this loan amount.",
            "Inconsistencies found in the application details."
        ]

        for i in range(3):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(5, 15)),
                application_id=f"APPL-RC-{500+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(loan_product_types),
                loan_amount=random.randint(10000, 100000),
                payment_amount=random.randint(5000, 50000),
                processing_fee=random.randint(500, 2000),
                rto=random.randint(100, 500),
                vap_amount=random.randint(200, 1000),
                beneficiary_name=random.choice(customer_names),
                beneficiary_account_number=f"{random.randint(10000000, 99999999)}",
                beneficiary_ifsc=f"IFSC{random.randint(10000, 99999)}",
                bank_name=random.choice(bank_names),
                branch_name=random.choice(branch_locations),
                maker=maker.username,
                maker_id=maker.id,
                checker=checker.username,
                checker_id=checker.id,
                status=LoanApplication.STATUS_REJECTED,
                rejection_reason=rejection_reasons_checker[i],
                rejected_by=checker.username,
                rejected_by_id=checker.id,
                created_at=datetime.now() - timedelta(days=random.randint(5, 10)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 4)),
                status_changed_at=datetime.now() - timedelta(days=random.randint(1, 4))
            )
            db.session.add(loan)

        # 6. Rejected by Author applications (3)
        rejection_reasons_author = [
            "Loan amount exceeds policy limits for the given income level.",
            "High risk assessment based on existing debt obligations.",
            "Beneficiary bank details could not be verified."
        ]

        for i in range(3):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(5, 15)),
                application_id=f"APPL-RA-{600+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(loan_product_types),
                loan_amount=random.randint(10000, 100000),
                payment_amount=random.randint(5000, 50000),
                processing_fee=random.randint(500, 2000),
                rto=random.randint(100, 500),
                vap_amount=random.randint(200, 1000),
                beneficiary_name=random.choice(customer_names),
                beneficiary_account_number=f"{random.randint(10000000, 99999999)}",
                beneficiary_ifsc=f"IFSC{random.randint(10000, 99999)}",
                bank_name=random.choice(bank_names),
                branch_name=random.choice(branch_locations),
                maker=maker.username,
                maker_id=maker.id,
                checker=checker.username,
                checker_id=checker.id,
                author=author.username,
                author_id=author.id,
                status=LoanApplication.STATUS_REJECTED,
                rejection_reason=rejection_reasons_author[i],
                rejected_by=author.username,
                rejected_by_id=author.id,
                created_at=datetime.now() - timedelta(days=random.randint(10, 20)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                status_changed_at=datetime.now() - timedelta(days=random.randint(1, 5))
            )
            db.session.add(loan)

        db.session.commit()
        print(f"Database seeding completed. Added {5+5+5+5+3+3}=26 loan applications.")
        print(f"Created 10 makers, 5 checkers, and 3 authors with various product expertise.")

if __name__ == "__main__":
    seed_database()
