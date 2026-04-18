#!/usr/bin/env python3
"""
Create a sample PDF bank statement for testing
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime, timedelta

def create_sample_pdf():
    """Create a sample bank statement PDF"""
    doc = SimpleDocTemplate("sample_bank_statement.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Title
    title_style = styles['Heading1']
    title = Paragraph("BANK STATEMENT", title_style)
    elements.append(title)
    
    # Account info
    account_info = [
        ["Account Number:", "1234567890"],
        ["Account Holder:", "Demo User"],
        ["Statement Period:", "April 2026"],
        ["Statement Date:", datetime.now().strftime("%B %d, %Y")]
    ]
    
    account_table = Table(account_info, colWidths=[2*inch, 3*inch])
    account_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(account_table)
    elements.append(Spacer(1, 20))
    
    # Transactions
    transactions = [
        ["Date", "Description", "Amount"],
        ["2026-04-01", "Salary Credit", "85000.00"],
        ["2026-04-02", "Grocery Store", "-2500.00"],
        ["2026-04-03", "Electricity Bill", "-1200.00"],
        ["2026-04-04", "Restaurant", "-800.00"],
        ["2026-04-05", "Fuel Station", "-2000.00"],
        ["2026-04-06", "Online Shopping", "-3500.00"],
        ["2026-04-07", "Medical Store", "-500.00"],
        ["2026-04-08", "Movie Tickets", "-600.00"],
        ["2026-04-09", "Mobile Recharge", "-299.00"],
        ["2026-04-10", "Cash Withdrawal", "-5000.00"],
    ]
    
    # Header row
    header_data = [transactions[0]]
    header_table = Table(header_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    
    # Transaction rows
    for i, row in enumerate(transactions[1:], 1):
        row_data = [row]
        color = colors.lightgrey if i % 2 == 0 else colors.white
        row_table = Table(row_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
        row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, -1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(row_table)
    
    # Summary
    elements.append(Spacer(1, 20))
    summary_style = styles['Heading2']
    summary_title = Paragraph("Summary", summary_style)
    elements.append(summary_title)
    
    summary_data = [
        ["Total Credits:", "85000.00"],
        ["Total Debits:", "-16399.00"],
        ["Net Balance:", "68601.00"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 1), (-1, 1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(summary_table)
    
    # Build the document
    doc.build(elements)
    print("Sample PDF bank statement created: sample_bank_statement.pdf")

if __name__ == "__main__":
    create_sample_pdf()
