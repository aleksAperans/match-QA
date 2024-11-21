# pdf_generator.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor
from io import BytesIO
import traceback

def create_pie_chart(data, labels, title, width=3*inch, height=2*inch):
    print(f"Creating pie chart: {title}")
    print(f"Data: {data}")
    print(f"Labels: {labels}")

    drawing = Drawing(width, height)
    pc = Pie()
    pc.x = width/2
    pc.y = height/2
    pc.width = min(width, height) * 0.75
    pc.height = pc.width
    pc.data = data
    pc.labels = labels

    pc.slices.strokeWidth = 0.5
    pc.slices.strokeColor = HexColor(0xFFFFFF)

    # Use some predefined colors
    colors = [HexColor("#FF6B6B"), HexColor("#4ECDC4"), HexColor("#45B7D1"),
              HexColor("#FFA07A"), HexColor("#98D8C8")]
    for i, color in enumerate(colors[:len(data)]):
        pc.slices[i].fillColor = color

    drawing.add(pc)

    # Add title as a string instead of a Paragraph
    drawing.add(String(width/2, height-10, title,
                       fontSize=10,
                       textAnchor='middle'))

    return drawing

def generate_pdf_report(summary, country_summary, name_quality, address_quality):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements = []

        styles = getSampleStyleSheet()

        # Modify existing Title style
        styles['Title'].fontSize = 24
        styles['Title'].alignment = 1
        styles['Title'].spaceAfter = 0.3*inch

        # Create new styles
        styles.add(ParagraphStyle(name='Subtitle',
                                  parent=styles['Title'],
                                  fontSize=18,
                                  alignment=1,
                                  spaceAfter=0.2*inch))

        styles.add(ParagraphStyle(name='SectionTitle',
                                  parent=styles['Heading2'],
                                  fontSize=14,
                                  alignment=0,
                                  spaceBefore=0.2*inch,
                                  spaceAfter=0.1*inch))

        # Header
        elements.append(Paragraph("Match Resolution Report", styles['Title']))
        elements.append(Paragraph("Summary and Quality Analysis", styles['Subtitle']))

        # Horizontal Line
        d = Drawing(500, 1)
        d.add(Line(0, 0, 500, 0))
        elements.append(d)
        elements.append(Spacer(1, 0.2*inch))

        # Summary
        elements.append(Paragraph("Summary", styles['SectionTitle']))
        summary_data = [
            ["Total Records", str(summary['total_rows'])],
            ["Strong Matches", f"{summary['strong_matches']} ({summary['strong_matches_percent']:.1f}%)"],
            ["Weak Matches", f"{summary['weak_matches']} ({summary['weak_matches_percent']:.1f}%)"],
            ["No Matches", f"{summary['no_matches']} ({summary['no_matches_percent']:.1f}%)"],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        # Summary Pie Chart
        summary_pie_data = [summary['strong_matches'], summary['weak_matches'], summary['no_matches']]
        summary_pie_labels = ['Strong', 'Weak', 'No Match']
        print("Creating summary pie chart")
        summary_pie = create_pie_chart(summary_pie_data, summary_pie_labels, "Match Distribution")

        # Combine table and pie chart
        summary_elements = [summary_table, summary_pie]
        summary_combined = Table([summary_elements], colWidths=[4*inch, 3*inch])
        elements.append(summary_combined)
        elements.append(Spacer(1, 0.2*inch))

        # Country Summary
        elements.append(Paragraph("Country Summary", styles['SectionTitle']))
        country_data = [["Country", "Strong", "Weak", "No Match", "Total"]]
        for country, data in country_summary.items():
            country_data.append([
                country,
                f"{data['strong']} ({data['strong_percent']:.1f}%)",
                f"{data['weak']} ({data['weak_percent']:.1f}%)",
                f"{data['no_match']} ({data['no_match_percent']:.1f}%)",
                str(data['total'])
            ])
        country_table = Table(country_data, colWidths=[1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1*inch])
        country_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(country_table)
        elements.append(Spacer(1, 0.2*inch))

        # Name Quality Details
        elements.append(Paragraph("Name Quality Details", styles['SectionTitle']))
        for match_type in ['Strong Matches', 'Weak Matches']:
            elements.append(Paragraph(f"{match_type} - high quality match name", styles['Heading4']))
            name_data = [["True", "False", "N/A", "Total"]]
            data = name_quality[match_type.lower().replace(' ', '_')]
            name_data.append([
                f"{data['true']} ({data['true_percent']:.1f}%)",
                f"{data['false']} ({data['false_percent']:.1f}%)",
                f"{data['na']} ({data['na_percent']:.1f}%)",
                f"{data['total']} (100%)"
            ])
            name_table = Table(name_data, colWidths=[1.6*inch, 1.6*inch, 1.6*inch, 1.6*inch])
            name_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            # Name Quality Pie Chart
            name_pie_data = [data['true'], data['false'], data['na']]
            name_pie_labels = ['True', 'False', 'N/A']
            name_pie = create_pie_chart(name_pie_data, name_pie_labels, f"{match_type} - High Quality Name Distribution")

            # Combine table and pie chart
            name_elements = [name_table, name_pie]
            name_combined = Table([name_elements], colWidths=[4*inch, 3*inch])
            elements.append(name_combined)
            elements.append(Spacer(1, 0.1*inch))

        # Address Quality Details
        elements.append(Paragraph("Address Quality Details", styles['SectionTitle']))
        address_data = [["High", "Medium", "Low", "N/A", "Total"]]
        address_data.append([
            f"{address_quality['high']} ({address_quality['high_percent']:.1f}%)",
            f"{address_quality['medium']} ({address_quality['medium_percent']:.1f}%)",
            f"{address_quality['low']} ({address_quality['low_percent']:.1f}%)",
            f"{address_quality['na']} ({address_quality['na_percent']:.1f}%)",
            f"{address_quality['total']} (100%)"
        ])
        address_table = Table(address_data, colWidths=[1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        address_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        # Address Quality Pie Chart
        address_pie_data = [address_quality['high'], address_quality['medium'], address_quality['low'], address_quality['na']]
        address_pie_labels = ['High', 'Medium', 'Low', 'N/A']
        address_pie = create_pie_chart(address_pie_data, address_pie_labels, "Address Quality Distribution")

        # Combine table and pie chart
        address_elements = [address_table, address_pie]
        address_combined = Table([address_elements], colWidths=[4*inch, 3*inch])
        elements.append(address_combined)

        # Footer
        def add_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.drawString(inch, 0.5 * inch, f"Page {canvas.getPageNumber()}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        print(f"Error in generate_pdf_report: {str(e)}")
        traceback.print_exc()
        raise
