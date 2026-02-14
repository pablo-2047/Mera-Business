"""
PDF Invoice Generator for Bharat Biz-Agent
Generates professional invoices with business details
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os


def generate_invoice_pdf(
    invoice_data: dict,
    business_info: dict = None,
    output_path: str = None
) -> str:
    """
    Generate a professional PDF invoice
    
    Args:
        invoice_data: Dict with invoice details (invoice_number, customer_name, items, etc.)
        business_info: Dict with business details (name, address, phone, gstin, etc.)
        output_path: Where to save the PDF (default: /mnt/user-data/outputs/)
        
    Returns:
        Path to generated PDF file
    """
    
    # Default business info if not provided
    if not business_info:
        business_info = {
            'name': 'Electronics Paradise',
            'address': 'Shop No. 12, Main Market, Lucknow - 226001',
            'phone': '+91-9876543210',
            'email': 'contact@electronicsparadise.in',
            'gstin': '09AAAAA0000A1Z5',
            'logo': None  # Optional: path to logo image
        }
    
    # Generate output path
    if not output_path:
        os.makedirs('/mnt/user-data/outputs', exist_ok=True)
        output_path = f"/mnt/user-data/outputs/Invoice_{invoice_data['invoice_number']}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Business Header
    business_header = [
        [Paragraph(f"<b>{business_info['name']}</b>", heading_style)],
        [Paragraph(business_info['address'], normal_style)],
        [Paragraph(f"Phone: {business_info['phone']} | Email: {business_info.get('email', 'N/A')}", normal_style)],
        [Paragraph(f"<b>GSTIN:</b> {business_info.get('gstin', 'N/A')}", normal_style)]
    ]
    
    business_table = Table(business_header, colWidths=[6*inch])
    business_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(business_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Invoice Details Header
    invoice_date = datetime.fromisoformat(invoice_data.get('invoice_date', datetime.now().isoformat())).strftime('%d/%m/%Y')
    
    invoice_details = [
        ['Invoice Number:', invoice_data['invoice_number'], 'Date:', invoice_date],
        ['Customer Name:', invoice_data['customer_name'], 'Payment Mode:', invoice_data.get('payment_mode', 'Pending')]
    ]
    
    details_table = Table(invoice_details, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Items Table
    items_data = [
        ['#', 'Product', 'Qty', 'Unit', 'Rate', 'GST %', 'Amount']
    ]
    
    # Add items
    for idx, item in enumerate(invoice_data.get('items', []), 1):
        items_data.append([
            str(idx),
            item.get('product_name', 'N/A'),
            str(item.get('quantity', 0)),
            item.get('unit', 'piece'),
            f"₹{item.get('rate', 0):,.2f}",
            f"{item.get('gst_rate', 18)}%",
            f"₹{item.get('amount', 0):,.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[0.4*inch, 2.2*inch, 0.6*inch, 0.8*inch, 1*inch, 0.7*inch, 1.3*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # column
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Qty column
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Unit column
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Amount columns
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Totals
    subtotal = invoice_data.get('subtotal', 0)
    gst_amount = invoice_data.get('gst_amount', 0)
    total_amount = invoice_data.get('total_amount', 0)
    
    totals_data = [
        ['', '', '', '', 'Subtotal:', f"₹{subtotal:,.2f}"],
        ['', '', '', '', f'GST:', f"₹{gst_amount:,.2f}"],
        ['', '', '', '', 'Total Amount:', f"₹{total_amount:,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[0.4*inch, 2.2*inch, 0.6*inch, 0.8*inch, 1*inch, 1.3*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
        ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, 0), (5, -1), 11),
        ('LINEABOVE', (4, 0), (5, 0), 0.5, colors.grey),
        ('LINEABOVE', (4, 2), (5, 2), 2, colors.HexColor('#3f51b5')),
        ('BACKGROUND', (4, 2), (5, 2), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (4, 2), (5, 2), colors.HexColor('#1a237e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Amount in words
    amount_words = number_to_words(int(total_amount))
    story.append(Paragraph(f"<b>Amount in Words:</b> {amount_words} Rupees Only", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Notes
    if invoice_data.get('notes'):
        story.append(Paragraph(f"<b>Notes:</b> {invoice_data['notes']}", normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=normal_style,
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Thank you for your business!", footer_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%d/%m/%Y %I:%M %p')}", footer_style))
    
    # Build PDF
    doc.build(story)
    
    return output_path


def number_to_words(num: int) -> str:
    """Convert number to words (Indian numbering system)"""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    
    if num == 0:
        return 'Zero'
    
    def convert_hundreds(n):
        if n == 0:
            return ''
        elif n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')
        else:
            return ones[n // 100] + ' Hundred' + (' ' + convert_hundreds(n % 100) if n % 100 != 0 else '')
    
    # Indian numbering: Crore, Lakh, Thousand, Hundred
    crore = num // 10000000
    lakh = (num % 10000000) // 100000
    thousand = (num % 100000) // 1000
    hundred = num % 1000
    
    result = []
    
    if crore:
        result.append(convert_hundreds(crore) + ' Crore')
    if lakh:
        result.append(convert_hundreds(lakh) + ' Lakh')
    if thousand:
        result.append(convert_hundreds(thousand) + ' Thousand')
    if hundred:
        result.append(convert_hundreds(hundred))
    
    return ' '.join(result)


# Add this function to database.py or create a wrapper
def create_invoice_with_pdf(customer_name: str, items: list, **kwargs) -> dict:
    """
    Create invoice and generate PDF
    
    Wrapper around database.create_invoice that also generates PDF
    """
    from database import create_invoice as db_create_invoice, get_db_connection
    
    # Create invoice in database
    invoice = db_create_invoice(customer_name, items, **kwargs)
    
    # Get complete invoice details with items
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM invoices WHERE id = ?
    """, (invoice['id'],))
    invoice_data = dict(cursor.fetchone())
    
    # Get items
    cursor.execute("""
        SELECT * FROM invoice_items WHERE invoice_id = ?
    """, (invoice['id'],))
    invoice_items = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Add items to invoice data
    invoice_data['items'] = invoice_items
    
    # Generate PDF
    pdf_path = generate_invoice_pdf(invoice_data)
    invoice_data['pdf_path'] = pdf_path
    
    return invoice_data


if __name__ == "__main__":
    # Test PDF generation
    sample_invoice = {
        'invoice_number': 'INV20260203001',
        'customer_name': 'Ramesh Kumar',
        'invoice_date': datetime.now().isoformat(),
        'payment_mode': 'UPI',
        'items': [
            {
                'product_name': 'Vivo V29',
                'quantity': 1,
                'unit': 'piece',
                'rate': 29999,
                'gst_rate': 18,
                'amount': 29999
            }
        ],
        'subtotal': 29999,
        'gst_amount': 5399.82,
        'total_amount': 35398.82,
        'notes': 'Thank you for your purchase!'
    }
    
    pdf_file = generate_invoice_pdf(sample_invoice, output_path='sample_invoice.pdf')
    print(f"✅ Sample PDF generated: {pdf_file}")
