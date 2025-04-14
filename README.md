# Loan Management System

A comprehensive loan management system with approval workflows, real-time updates, and multi-user support.

## Features

- Multi-role support (Maker, Checker, Author)
- Approval/Rejection workflow
- Real-time status updates
- Pagination and filtering
- Dashboard with statistics
- Mobile-responsive design

## Setup Instructions

### 1. Run Database Migrations

Before using the new features, you need to run the database migration script to add the new fields:

```bash
python migrations.py
```

This will:
- Create a backup of your current database
- Add new columns for rejection tracking and timestamps
- Initialize the timestamp fields

### 2. Seed the Database with Demo Data (Optional)

To populate the database with sample data for demonstration purposes:

```bash
python seed_data.py
```

This will create 26 loan applications in various states:
- 5 Draft applications
- 5 Pending Checker applications
- 5 Pending Author applications
- 5 Approved applications
- 3 Applications rejected by Checker
- 3 Applications rejected by Author

### 3. Run the Application

Start the Flask application:

```bash
python app.py
```

The application will be available at http://localhost:5000

## Default Users

The system comes with three default users:

1. **Maker**
   - Username: maker
   - Password: maker123
   - Role: Maker (creates loan applications)

2. **Checker**
   - Username: checker
   - Password: checker123
   - Role: Checker (first level of approval)

3. **Author**
   - Username: admin
   - Password: admin123
   - Role: Author (final approval and user management)

## Workflow

1. **Maker** creates a loan application
2. **Checker** reviews and approves/rejects the application
3. If approved by Checker, **Author** gives final approval or rejection
4. Rejection reasons are stored and visible to all users

## Real-time Updates

The system includes real-time status updates:
- Status changes are reflected immediately for all users
- Notifications appear when applications are updated
- Dashboard statistics update in real-time

## Filtering and Searching

- Filter applications by status (Draft, Pending Checker, Pending Author, Approved, Rejected)
- Search by customer name, application ID, or product type
- Pagination for handling large numbers of applications
