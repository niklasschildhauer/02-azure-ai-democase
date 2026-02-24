#!/usr/bin/env python3
"""
Generate realistic insurance claim form PDFs for fraud detection workshop
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib import colors
import os


def create_claim_pdf(filepath, data):
    """Generate a professional insurance claim form PDF"""

    # Create document
    pdf = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#003366'),
        alignment=TA_CENTER,
        spaceAfter=3,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=15
    )

    section_style = ParagraphStyle(
        'Section',
        fontSize=11,
        textColor=white,
        backColor=HexColor('#003366'),
        fontName='Helvetica-Bold',
        spaceAfter=8,
        spaceBefore=12,
        leftIndent=5,
        leading=14
    )

    normal = styles['Normal']
    normal.fontSize = 8.5
    normal.leading = 12

    # Header
    story.append(Paragraph("SAFEGUARD INSURANCE COMPANY", title_style))
    story.append(Paragraph(
        "Auto Insurance Claim Form | Claims Department: 1-800-555-CLAIM | claims@safeguardins.com",
        subtitle_style
    ))

    # Claim info box
    claim_box = [
        [
            Paragraph('<b>Claim Number:</b>', normal),
            Paragraph(data['claim_number'], normal),
            Paragraph('<b>Date Filed:</b>', normal),
            Paragraph(data['date_filed'], normal)
        ],
        [
            Paragraph('<b>Status:</b>', normal),
            Paragraph(data['status'], normal),
            Paragraph('<b>Claim Type:</b>', normal),
            Paragraph(data['claim_type'], normal)
        ]
    ]

    t = Table(claim_box, colWidths=[28*mm, 48*mm, 28*mm, 48*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F5F5F5')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 1: Policy holder
    story.append(Paragraph("  SECTION 1: POLICY HOLDER INFORMATION", section_style))

    policy_info = [
        [
            Paragraph('<b>Full Name:</b>', normal),
            Paragraph(data['name'], normal),
            Paragraph('<b>Policy Number:</b>', normal),
            Paragraph(data['policy_number'], normal)
        ],
        [
            Paragraph('<b>Address:</b>', normal),
            Paragraph(data['address'], normal),
            Paragraph('<b>Policy Start Date:</b>', normal),
            Paragraph(data['policy_start'], normal)
        ],
        [
            Paragraph('<b>Phone:</b>', normal),
            Paragraph(data['phone'], normal),
            Paragraph('<b>Email:</b>', normal),
            Paragraph(data['email'], normal)
        ],
        [
            Paragraph('<b>Coverage Type:</b>', normal),
            Paragraph(data['coverage_type'], normal),
            '', ''
        ]
    ]

    t = Table(policy_info, colWidths=[32*mm, 58*mm, 32*mm, 30*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Section 2: Vehicle
    story.append(Paragraph("  SECTION 2: VEHICLE INFORMATION", section_style))

    vehicle_info = [[
        Paragraph('<b>Vehicle:</b>', normal),
        Paragraph(data['vehicle'], normal),
        Paragraph('<b>VIN:</b>', normal),
        Paragraph(data['vin'], normal)
    ]]

    t = Table(vehicle_info, colWidths=[32*mm, 58*mm, 32*mm, 30*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Section 3: Incident
    story.append(Paragraph("  SECTION 3: INCIDENT DETAILS", section_style))

    incident_info = [
        [
            Paragraph('<b>Date of Incident:</b>', normal),
            Paragraph(data['incident_date'], normal),
            Paragraph('<b>Time:</b>', normal),
            Paragraph(data['incident_time'], normal)
        ],
        [
            Paragraph('<b>Location:</b>', normal),
            Paragraph(data['incident_location'], normal),
            '', ''
        ],
        [
            Paragraph('<b>Weather:</b>', normal),
            Paragraph(data['weather'], normal),
            '', ''
        ],
        [
            Paragraph('<b>Police Report:</b>', normal),
            Paragraph(data['police_report'], normal),
            Paragraph('<b>Report #:</b>', normal),
            Paragraph(data['police_number'], normal)
        ]
    ]

    t = Table(incident_info, colWidths=[32*mm, 58*mm, 32*mm, 30*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Description
    desc_data = [
        [Paragraph('<b>Description of Incident:</b>', normal)],
        [Paragraph(data['description'], normal)]
    ]

    t = Table(desc_data, colWidths=[152*mm])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#F5F5F5')),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Section 4: Repair
    story.append(Paragraph("  SECTION 4: REPAIR ESTIMATE & INVOICE", section_style))

    repair_header = [
        [Paragraph('<b>Repair Shop:</b>', normal), Paragraph(data['repair_shop'], normal)],
        [Paragraph('<b>Address:</b>', normal), Paragraph(data['shop_address'], normal)],
        [Paragraph('<b>Phone:</b>', normal), Paragraph(data['shop_phone'], normal)],
        [Paragraph('<b>Invoice Number:</b>', normal), Paragraph(data['invoice_number'], normal)],
        [Paragraph('<b>Invoice Date:</b>', normal), Paragraph(data['invoice_date'], normal)]
    ]

    t = Table(repair_header, colWidths=[35*mm, 117*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Repair items table
    repair_table_data = [[
        Paragraph('<b>Description</b>', normal),
        Paragraph('<b>Qty</b>', normal),
        Paragraph('<b>Unit Price</b>', normal),
        Paragraph('<b>Total</b>', normal)
    ]]

    for item in data['repair_items']:
        repair_table_data.append([
            Paragraph(item[0], normal),
            Paragraph(item[1], normal),
            Paragraph(item[2], normal),
            Paragraph(item[3], normal)
        ])

    t = Table(repair_table_data, colWidths=[80*mm, 18*mm, 27*mm, 27*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

    # Totals
    totals_data = []
    for total in data['totals']:
        totals_data.append([
            Paragraph(f'<b>{total[0]}</b>', normal),
            Paragraph(f'<b>{total[1]}</b>', normal)
        ])

    t = Table(totals_data, colWidths=[125*mm, 27*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, black),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, black),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 5: Documents
    story.append(Paragraph("  SECTION 5: SUPPORTING DOCUMENTATION", section_style))

    docs_data = [[
        Paragraph('<b>Document Type</b>', normal),
        Paragraph('<b>Status</b>', normal)
    ]]

    for doc in data['documents']:
        docs_data.append([
            Paragraph(doc[0], normal),
            Paragraph(doc[1], normal)
        ])

    t = Table(docs_data, colWidths=[105*mm, 47*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7.5,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        leading=10
    )

    footer = f"""
    <b>DECLARATION:</b> I declare that the information provided in this claim is true and accurate to the best of my knowledge.<br/>
    I understand that providing false information may result in denial of this claim and/or policy cancellation.<br/><br/>
    Claimant Signature: ________________________________  Date: {data['date_filed']}<br/><br/>
    <b>Safeguard Insurance Company</b> | PO Box 9876, Columbus, OH 43216 | Phone: 1-800-555-CLAIM<br/>
    www.safeguardinsurance.com | Email: claims@safeguardins.com
    """
    story.append(Paragraph(footer, footer_style))

    # Build PDF
    pdf.build(story)
    print(f"✅ Created: {os.path.basename(filepath)}")


# Legitimate claim data
legitimate = {
    'claim_number': 'CLM-2026-001847',
    'date_filed': 'February 10, 2026',
    'status': 'Under Review',
    'claim_type': 'Collision - Third Party',
    'name': 'Sarah Mitchell',
    'policy_number': 'POL-847593-AUTO',
    'address': '1523 Riverside Drive, Columbus, OH 43215',
    'phone': '(614) 555-2347',
    'email': 'sarah.mitchell@email.com',
    'policy_start': 'June 15, 2024',
    'coverage_type': 'Full Coverage - $500 Deductible',
    'vehicle': '2023 Honda Civic',
    'vin': '2HGFC2F59NH123456',
    'incident_date': 'February 5, 2026',
    'incident_time': '2:30 PM',
    'incident_location': '1247 Oak Street, Shopping Center Parking Lot, Columbus, OH 43215',
    'weather': 'Clear, dry conditions',
    'police_report': 'Yes',
    'police_number': 'CPD-2026-002341',
    'description': 'I was parked in a marked parking space at the grocery store when a 2021 Toyota Camry backed out of an adjacent space and struck my vehicle. The other driver did not see my car and backed directly into my front passenger door while my vehicle was stationary and unoccupied. The impact caused significant damage to the door panel and surrounding area. The other driver immediately stopped, exited their vehicle, and we exchanged insurance information. The driver accepted full responsibility for the accident. A security guard who was on duty in the parking lot witnessed the entire incident and provided a written statement. I called the police who arrived within 15 minutes and filed an official accident report. There were no injuries to any parties involved.',
    'repair_shop': 'Precision Auto Repair LLC',
    'shop_address': '892 Industrial Parkway, Columbus, OH 43228',
    'shop_phone': '(614) 555-8800',
    'invoice_number': 'INV-2026-0589',
    'invoice_date': 'February 8, 2026',
    'repair_items': [
        ['Front passenger door assembly (OEM Honda replacement part)', '1', '$1,850.00', '$1,850.00'],
        ['Automotive paint matching and refinishing (Honda paint code B-593P)', '1', '$950.00', '$950.00'],
        ['Door alignment, fitting, and adjustment', '1', '$425.00', '$425.00'],
        ['Door handle assembly with integrated electronics', '1', '$185.00', '$185.00'],
        ['Labor: Mechanical and body work (8.5 hours @ $95.00/hour)', '8.5', '$95.00', '$807.50'],
    ],
    'totals': [
        ['Subtotal:', '$4,217.50'],
        ['Sales Tax (6.75%):', '$284.68'],
        ['TOTAL CLAIM AMOUNT:', '$4,502.18'],
    ],
    'documents': [
        ['Police Report - CPD-2026-002341', 'Attached'],
        ['Photographs of vehicle damage (taken 02/05/2026)', 'Attached'],
        ['Witness statement - Parking lot security guard', 'Attached'],
        ['Third party driver insurance information', 'Attached'],
        ['Repair shop detailed estimate and invoice', 'Attached'],
    ]
}

# Suspicious claim data
suspicious = {
    'claim_number': 'CLM-2026-002156',
    'date_filed': 'February 12, 2026',
    'status': 'Under Review',
    'claim_type': 'Collision - Single Vehicle',
    'name': 'Michael Torres',
    'policy_number': 'POL-394728-AUTO',
    'address': '847 County Line Road, Apartment 3B, Grove City, OH 43123',
    'phone': '(614) 555-8765',
    'email': 'm.torres.1983@email.com',
    'policy_start': 'November 20, 2025',
    'coverage_type': 'Full Coverage - $250 Deductible',
    'vehicle': '2022 Ford F-150 XLT',
    'vin': '1FTFW1E85NFA12345',
    'incident_date': 'January 28, 2026',  # But invoice is dated January 26!
    'incident_time': '7:45 PM',
    'incident_location': 'Highway 71 North, approximately 2 miles north of Exit 47, rural area',
    'weather': 'Heavy rain, poor visibility',
    'police_report': 'No',
    'police_number': 'Not filed',
    'description': 'I was driving northbound on Highway 71 in heavy rain when a deer suddenly ran onto the roadway from the right side. I swerved to avoid striking the animal and lost control of my vehicle. My truck struck the metal guardrail on the right shoulder of the highway, causing damage to the front end including the bumper, hood, and right headlight assembly. There were no other vehicles involved in the incident and no witnesses present. After the impact, I was able to safely move my vehicle to the shoulder and assess the damage. The truck was still drivable so I drove it home that evening. I contacted my insurance company a few days later to file this claim.',
    'repair_shop': 'QuickFix Auto Services',
    'shop_address': '4521 County Road 18, Grove City, OH 43123',
    'shop_phone': '(614) 555-9900',
    'invoice_number': 'QF-2026-00847',
    'invoice_date': 'January 26, 2026',  # RED FLAG: 2 days BEFORE incident!
    'repair_items': [
        ['Front bumper assembly replacement with mounting hardware', '1', '$2,450.00', '$2,450.00'],
        ['Hood panel replacement and installation', '1', '$1,950.00', '$1,950.00'],
        ['Right front headlight assembly (LED type)', '1', '$875.00', '$875.00'],
        ['Front right quarter panel repair and bodywork', '1', '$1,485.00', '$1,485.00'],
        ['Paint matching and full refinishing work', '1', '$1,680.00', '$1,680.00'],
        ['Front suspension alignment check and adjustment', '1', '$650.00', '$650.00'],
        ['Labor: Body work and mechanical repairs (14 hours @ $125.00/hour)', '14', '$125.00', '$1,750.00'],
    ],
    'totals': [
        ['Subtotal:', '$10,840.00'],
        ['Sales Tax (7.00%):', '$758.80'],  # Wrong tax rate
        ['TOTAL CLAIM AMOUNT:', '$11,598.80'],
    ],
    'documents': [
        ['Police Report', 'Not Available - Not filed'],
        ['Photographs of vehicle damage (taken 02/02/2026)', 'Attached'],
        ['Witness statements', 'None available'],
        ['Repair shop detailed estimate and invoice', 'Attached'],
    ]
}


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    claims_dir = os.path.join(script_dir, 'sample-data', 'claims')

    print("\n" + "="*70)
    print("GENERATING INSURANCE CLAIM FORMS")
    print("="*70 + "\n")

    create_claim_pdf(os.path.join(claims_dir, 'legitimate-claim.pdf'), legitimate)
    create_claim_pdf(os.path.join(claims_dir, 'suspicious-claim.pdf'), suspicious)

    print("\n" + "="*70)
    print("✅ CLAIM FORMS GENERATED SUCCESSFULLY")
    print("="*70)
    print("\nBoth forms use identical professional formatting.")
    print("\n🔍 Fraud indicators in suspicious claim:")
    print("   • Invoice date Jan 26 vs. Incident date Jan 28 (IMPOSSIBLE!)")
    print("   • Labor rate $125/hr (market rate: $85-95/hr) - 30% overcharge")
    print("   • Total claim $11,599 (should be ~$7,500) - 50% inflation")
    print("   • Wrong tax rate: 7.00% (Columbus area: 6.75%)")
    print("   • No police report for highway accident")
    print("   • Recent policy (Nov 2025, claim Feb 2026)")
    print("   • Vendor 'QuickFix Auto Services' appears in multiple claims")
    print("="*70 + "\n")
