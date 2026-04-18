import io
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def generate_excel_report(df: pd.DataFrame) -> io.BytesIO:
    """Generate an Excel report from a transactions dataframe."""
    buffer = io.BytesIO()
    
    # Create an Excel writer object using openpyxl
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Write the dataframe to the sheet
        df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Access the workbook and worksheet to add formatting
        worksheet = writer.sheets['Transactions']
        
        # Auto-adjust column widths
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = adjusted_width
            
    buffer.seek(0)
    return buffer

def generate_pdf_report(df: pd.DataFrame, summary: dict, start_date: datetime, end_date: datetime) -> io.BytesIO:
    """Generate a clean PDF report with metrics and transactions."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    elements = []
    
    # Header
    elements.append(Paragraph("FinSight AI - Financial Report", title_style))
    elements.append(Paragraph(f"Period: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Summary Metrics
    elements.append(Paragraph("Executive Summary", subtitle_style))
    elements.append(Spacer(1, 10))
    
    metrics_data = [
        ["Total Income", "Total Expenses", "Net Cash Flow"],
        [f"Rs. {summary['income']:,.2f}", f"Rs. {summary['expenses']:,.2f}", f"Rs. {summary['net']:,.2f}"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[150, 150, 150])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F4C5C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0f4f8')),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(metrics_table)
    elements.append(Spacer(1, 30))
    
    # Transactions Table
    elements.append(Paragraph("Transaction History", subtitle_style))
    elements.append(Spacer(1, 10))
    
    if not df.empty:
        # Prepare table data
        table_data = [["Date", "Description", "Category", "Amount"]]
        
        # Add up to 100 rows to prevent massive PDFs (can be adjusted)
        for _, row in df.head(100).iterrows():
            date_str = row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], datetime) else str(row['Date'])
            amt_str = f"Rs. {row['Amount']:,.2f}"
            table_data.append([date_str, str(row['Description'])[:40], str(row['Category']), amt_str])
            
        if len(df) > 100:
            table_data.append(["...", "Showing first 100 transactions...", "...", "..."])
            
        tx_table = Table(table_data, colWidths=[80, 250, 120, 80])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        elements.append(tx_table)
    else:
        elements.append(Paragraph("No transactions found for the selected period.", normal_style))
        
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
