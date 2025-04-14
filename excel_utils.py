"""
Excel export utilities for the Loan Management System.
"""
import io
import xlsxwriter
from datetime import datetime

def create_excel_workbook():
    """Create an in-memory Excel workbook."""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    return workbook, output

def add_header_formats(workbook):
    """Create and return formatting for Excel headers."""
    header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#3a506b',  # Custom primary color
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    subheader_format = workbook.add_format({
        'bold': True,
        'bg_color': '#e9ecef',  # Light gray
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    return header_format, subheader_format

def add_data_formats(workbook):
    """Create and return formatting for Excel data cells."""
    # Regular data format
    data_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter'
    })

    # Currency format
    currency_format = workbook.add_format({
        'border': 1,
        'num_format': '#,##0.00',
        'align': 'right',
        'valign': 'vcenter'
    })

    # Date format
    date_format = workbook.add_format({
        'border': 1,
        'num_format': 'yyyy-mm-dd',
        'align': 'center',
        'valign': 'vcenter'
    })

    # Status formats with our custom color scheme
    status_formats = {
        'draft': workbook.add_format({
            'border': 1,
            'bg_color': '#6c757d',  # Gray
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter'
        }),
        'pending_checker': workbook.add_format({
            'border': 1,
            'bg_color': '#e9c46a',  # Muted gold
            'align': 'center',
            'valign': 'vcenter'
        }),
        'pending_author': workbook.add_format({
            'border': 1,
            'bg_color': '#81b29a',  # Sage green
            'align': 'center',
            'valign': 'vcenter'
        }),
        'approved': workbook.add_format({
            'border': 1,
            'bg_color': '#588b8b',  # Teal green
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter'
        }),
        'rejected': workbook.add_format({
            'border': 1,
            'bg_color': '#bc6c25',  # Burnt orange
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter'
        })
    }

    return data_format, currency_format, date_format, status_formats

def export_applications_to_excel(applications, filename_prefix, include_checker=False, include_author=False, include_rejection=False):
    """
    Export applications to Excel file.

    Args:
        applications: List of LoanApplication objects
        filename_prefix: Prefix for the filename
        include_checker: Whether to include checker information
        include_author: Whether to include author information
        include_rejection: Whether to include rejection information

    Returns:
        BytesIO object containing the Excel file
    """
    workbook, output = create_excel_workbook()

    # Add worksheet
    worksheet = workbook.add_worksheet('Applications')

    # Add formats
    header_format, subheader_format = add_header_formats(workbook)
    data_format, currency_format, date_format, status_formats = add_data_formats(workbook)

    # Set column widths
    worksheet.set_column('A:A', 15)  # Application ID
    worksheet.set_column('B:B', 20)  # Customer Name
    worksheet.set_column('C:C', 12)  # Product Type
    worksheet.set_column('D:D', 12)  # Loan Amount
    worksheet.set_column('E:E', 12)  # Date
    worksheet.set_column('F:F', 15)  # Branch Location
    worksheet.set_column('G:G', 15)  # Maker
    col_offset = 0

    if include_checker:
        worksheet.set_column('H:H', 15)  # Checker
        col_offset += 1

    if include_author:
        worksheet.set_column(f'{chr(72 + col_offset)}:{chr(72 + col_offset)}', 15)  # Author
        col_offset += 1

    worksheet.set_column(f'{chr(72 + col_offset)}:{chr(72 + col_offset)}', 15)  # Status

    if include_rejection:
        worksheet.set_column(f'{chr(73 + col_offset)}:{chr(73 + col_offset)}', 20)  # Rejected By
        worksheet.set_column(f'{chr(74 + col_offset)}:{chr(74 + col_offset)}', 30)  # Rejection Reason

    # Write headers
    headers = [
        'Application ID', 'Customer Name', 'Product Type', 'Loan Amount',
        'Date', 'Branch Location', 'Maker'
    ]

    if include_checker:
        headers.append('Checker')

    if include_author:
        headers.append('Author')

    headers.append('Status')

    if include_rejection:
        headers.extend(['Rejected By', 'Rejection Reason'])

    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Write data rows
    for row, app in enumerate(applications, start=1):
        col = 0

        # Basic application data
        worksheet.write(row, col, app.application_id, data_format); col += 1
        worksheet.write(row, col, app.customer_name, data_format); col += 1
        worksheet.write(row, col, app.product_type, data_format); col += 1
        worksheet.write(row, col, app.loan_amount, currency_format); col += 1

        # Handle date - convert to datetime object for Excel
        if app.date:
            worksheet.write_datetime(row, col, app.date, date_format)
        else:
            worksheet.write(row, col, '', data_format)
        col += 1

        worksheet.write(row, col, app.branch_location, data_format); col += 1
        worksheet.write(row, col, app.maker, data_format); col += 1

        # Optional checker
        if include_checker:
            worksheet.write(row, col, app.checker or '', data_format); col += 1

        # Optional author
        if include_author:
            worksheet.write(row, col, app.author or '', data_format); col += 1

        # Status with conditional formatting
        status_format = status_formats.get(app.status, data_format)
        status_labels = {
            'draft': 'Draft',
            'pending_checker': 'Pending Checker',
            'pending_author': 'Pending Author',
            'approved': 'Approved',
            'rejected': 'Rejected'
        }
        worksheet.write(row, col, status_labels.get(app.status, app.status), status_format); col += 1

        # Optional rejection information
        if include_rejection and app.status == 'rejected':
            worksheet.write(row, col, app.rejected_by or '', data_format); col += 1
            worksheet.write(row, col, app.rejection_reason or '', data_format)

    # Add summary at the bottom
    summary_row = len(applications) + 2
    worksheet.write(summary_row, 0, 'Total Applications:', subheader_format)
    worksheet.write(summary_row, 1, len(applications), subheader_format)

    # Add timestamp
    timestamp_row = summary_row + 1
    worksheet.write(timestamp_row, 0, 'Generated on:', subheader_format)
    worksheet.write(timestamp_row, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subheader_format)

    # Close the workbook
    workbook.close()

    # Prepare the output
    output.seek(0)

    return output, f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

def export_distribution_to_excel(applications_by_user, filename_prefix, role_type):
    """
    Export distribution data to Excel with grouping by user.

    Args:
        applications_by_user: Dictionary mapping usernames to lists of applications
        filename_prefix: Prefix for the filename
        role_type: 'checker' or 'author'

    Returns:
        BytesIO object containing the Excel file
    """
    workbook, output = create_excel_workbook()

    # Add worksheet
    worksheet = workbook.add_worksheet('Distribution')

    # Add formats
    header_format, subheader_format = add_header_formats(workbook)
    data_format, currency_format, date_format, status_formats = add_data_formats(workbook)

    # Set column widths
    worksheet.set_column('A:A', 15)  # Application ID
    worksheet.set_column('B:B', 20)  # Customer Name
    worksheet.set_column('C:C', 12)  # Product Type
    worksheet.set_column('D:D', 12)  # Loan Amount
    worksheet.set_column('E:E', 12)  # Date
    worksheet.set_column('F:F', 15)  # Branch Location
    worksheet.set_column('G:G', 15)  # Maker
    worksheet.set_column('H:H', 15)  # Status

    # Write headers
    headers = [
        'Application ID', 'Customer Name', 'Product Type', 'Loan Amount',
        'Date', 'Branch Location', 'Maker', 'Status'
    ]

    # Current row for writing data
    current_row = 0

    # For each user, write their applications
    for username, applications in applications_by_user.items():
        # Write user header
        worksheet.merge_range(current_row, 0, current_row, len(headers) - 1,
                             f"{role_type.capitalize()}: {username} ({len(applications)} applications)",
                             subheader_format)
        current_row += 1

        # Write column headers for this group
        for col, header in enumerate(headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1

        # Write application data
        for app in applications:
            col = 0

            # Basic application data
            worksheet.write(current_row, col, app.application_id, data_format); col += 1
            worksheet.write(current_row, col, app.customer_name, data_format); col += 1
            worksheet.write(current_row, col, app.product_type, data_format); col += 1
            worksheet.write(current_row, col, app.loan_amount, currency_format); col += 1

            # Handle date
            if app.date:
                worksheet.write_datetime(current_row, col, app.date, date_format)
            else:
                worksheet.write(current_row, col, '', data_format)
            col += 1

            worksheet.write(current_row, col, app.branch_location, data_format); col += 1
            worksheet.write(current_row, col, app.maker, data_format); col += 1

            # Status with conditional formatting
            status_format = status_formats.get(app.status, data_format)
            status_labels = {
                'draft': 'Draft',
                'pending_checker': 'Pending Checker',
                'pending_author': 'Pending Author',
                'approved': 'Approved',
                'rejected': 'Rejected'
            }
            worksheet.write(current_row, col, status_labels.get(app.status, app.status), status_format)

            current_row += 1

        # Add a blank row between users
        current_row += 1

    # Add summary at the bottom
    total_applications = sum(len(apps) for apps in applications_by_user.values())
    worksheet.write(current_row, 0, 'Total Applications:', subheader_format)
    worksheet.write(current_row, 1, total_applications, subheader_format)
    current_row += 1

    # Add timestamp
    worksheet.write(current_row, 0, 'Generated on:', subheader_format)
    worksheet.write(current_row, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subheader_format)

    # Add a summary worksheet
    summary_sheet = workbook.add_worksheet('Summary')

    # Set column widths
    summary_sheet.set_column('A:A', 20)  # Username
    summary_sheet.set_column('B:B', 15)  # Application Count

    # Write headers
    summary_sheet.write(0, 0, f"{role_type.capitalize()} Name", header_format)
    summary_sheet.write(0, 1, "Assigned Applications", header_format)

    # Write summary data
    for i, (username, applications) in enumerate(applications_by_user.items(), start=1):
        summary_sheet.write(i, 0, username, data_format)
        summary_sheet.write(i, 1, len(applications), data_format)

    # Add total row
    total_row = len(applications_by_user) + 1
    summary_sheet.write(total_row, 0, "Total", subheader_format)
    summary_sheet.write(total_row, 1, total_applications, subheader_format)

    # Close the workbook
    workbook.close()

    # Prepare the output
    output.seek(0)

    return output, f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"


def export_productivity_report_to_excel(productivity_data):
    """
    Export productivity report to Excel showing how many cases each user has handled.

    Args:
        productivity_data: Dictionary with role types as keys and lists of user productivity data as values
                          Format: {
                              'maker': [{'username': 'user1', 'count': 10}, ...],
                              'checker': [{'username': 'user2', 'count': 5}, ...],
                              'author': [{'username': 'user3', 'count': 3}, ...]
                          }

    Returns:
        BytesIO object containing the Excel file
    """
    workbook, output = create_excel_workbook()

    # Add formats
    header_format, subheader_format = add_header_formats(workbook)
    data_format, currency_format, date_format, status_formats = add_data_formats(workbook)

    # Create a worksheet for the productivity report
    worksheet = workbook.add_worksheet('Productivity Report')

    # Set column widths
    worksheet.set_column('A:A', 20)  # Username
    worksheet.set_column('B:B', 15)  # Role
    worksheet.set_column('C:C', 15)  # Cases Count

    # Write title
    worksheet.merge_range('A1:C1', 'User Productivity Report', header_format)

    # Write headers
    headers = ['Username', 'Role', 'Cases Handled']
    for col, header in enumerate(headers):
        worksheet.write(1, col, header, header_format)

    # Current row for writing data
    current_row = 2
    role_totals = {}

    # Write data for each role type
    for role_type, users_data in productivity_data.items():
        # Sort users by count in descending order
        users_data.sort(key=lambda x: x['count'], reverse=True)

        # Calculate total for this role
        role_total = sum(user['count'] for user in users_data)
        role_totals[role_type] = role_total

        # Write role header
        worksheet.merge_range(current_row, 0, current_row, 2,
                            f"{role_type.capitalize()} Users", subheader_format)
        current_row += 1

        # Write user data
        for user_data in users_data:
            worksheet.write(current_row, 0, user_data['username'], data_format)
            worksheet.write(current_row, 1, role_type.capitalize(), data_format)
            worksheet.write(current_row, 2, user_data['count'], data_format)
            current_row += 1

        # Write role total
        worksheet.write(current_row, 0, f"Total {role_type.capitalize()} Cases:", subheader_format)
        worksheet.write(current_row, 2, role_total, subheader_format)
        current_row += 2  # Add extra space between roles

    # Add summary worksheet
    summary_sheet = workbook.add_worksheet('Summary')

    # Set column widths
    summary_sheet.set_column('A:A', 20)  # Role
    summary_sheet.set_column('B:B', 15)  # Total Cases

    # Write title
    summary_sheet.merge_range('A1:B1', 'Productivity Summary by Role', header_format)

    # Write headers
    summary_sheet.write(1, 0, 'Role', header_format)
    summary_sheet.write(1, 1, 'Total Cases Handled', header_format)

    # Write summary data
    row = 2
    for role_type, total in role_totals.items():
        summary_sheet.write(row, 0, role_type.capitalize(), data_format)
        summary_sheet.write(row, 1, total, data_format)
        row += 1

    # Add grand total
    grand_total = sum(role_totals.values())
    summary_sheet.write(row, 0, 'Grand Total', subheader_format)
    summary_sheet.write(row, 1, grand_total, subheader_format)

    # Add timestamp
    summary_sheet.write(row + 2, 0, 'Generated on:', subheader_format)
    summary_sheet.write(row + 2, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), subheader_format)

    # Close the workbook
    workbook.close()

    # Prepare the output
    output.seek(0)

    return output, f"productivity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
