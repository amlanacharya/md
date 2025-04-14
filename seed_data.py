from app import app, db, User, LoanApplication
from datetime import datetime, timedelta
import random

def seed_database():
    with app.app_context():
        print("Starting database seeding...")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing loan applications...")
        LoanApplication.query.delete()
        db.session.commit()
        
        # Get existing users or create them if they don't exist
        maker = User.query.filter_by(role='maker').first()
        checker = User.query.filter_by(role='checker').first()
        author = User.query.filter_by(role='author').first()
        
        if not maker:
            maker = User(username='maker', email='maker@example.com', password='maker123', role='maker')
            db.session.add(maker)
        
        if not checker:
            checker = User(username='checker', email='checker@example.com', password='checker123', role='checker')
            db.session.add(checker)
        
        if not author:
            author = User(username='author', email='author@example.com', password='author123', role='author')
            db.session.add(author)
        
        db.session.commit()
        
        # Sample data
        customer_names = [
            "John Smith", "Mary Johnson", "Robert Williams", "Patricia Brown", 
            "Michael Jones", "Linda Davis", "William Miller", "Elizabeth Wilson",
            "David Moore", "Barbara Taylor", "Richard Anderson", "Jennifer Thomas",
            "Joseph Jackson", "Susan White", "Charles Harris", "Jessica Martin",
            "Thomas Thompson", "Sarah Garcia", "Christopher Martinez", "Karen Robinson"
        ]
        
        product_types = ["Car Loan", "Home Loan", "Personal Loan", "Education Loan", "Business Loan"]
        
        branch_locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
                           "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
        
        bank_names = ["Chase Bank", "Bank of America", "Wells Fargo", "Citibank", "US Bank"]
        
        # Create loan applications in different states
        print("Creating loan applications...")
        
        # 1. Draft applications (5)
        for i in range(5):
            loan = LoanApplication(
                date=datetime.now().date() - timedelta(days=random.randint(1, 10)),
                application_id=f"DRAFT-{100+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(product_types),
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
                application_id=f"PENDING-CHK-{200+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(product_types),
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
                application_id=f"PENDING-AUTH-{300+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(product_types),
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
                application_id=f"APPROVED-{400+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(product_types),
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
                application_id=f"REJ-CHK-{500+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(product_types),
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
                application_id=f"REJ-AUTH-{600+i}",
                customer_name=random.choice(customer_names),
                dealer_code=f"D{random.randint(1000, 9999)}",
                scheme_name=f"Scheme {random.randint(1, 5)}",
                branch_location=random.choice(branch_locations),
                product_type=random.choice(product_types),
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

if __name__ == "__main__":
    seed_database()
