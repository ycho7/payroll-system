from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
import models
import io
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from datetime import date
import re


def generate_payroll_slip_pdf(employee, company, payroll):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    elements = []
    styles = getSampleStyleSheet()

    # ===================== STYLES =====================
    style_company = ParagraphStyle(
        "Company",
        fontSize=16,
        leading=18,
        fontName="Helvetica-Bold"
    )

    style_title = ParagraphStyle(
        "Title",
        fontSize=11,
        fontName="Helvetica-Bold",
        alignment=TA_RIGHT
    )

    style_section = ParagraphStyle(
        "Section",
        fontSize=10,
        fontName="Helvetica-Bold",
        spaceAfter=6
    )

    style_cell_l = ParagraphStyle(
        "CellL",
        fontSize=9,
        alignment=TA_LEFT
    )

    style_cell_r = ParagraphStyle(
        "CellR",
        fontSize=9,
        alignment=TA_RIGHT
    )

    style_footer = ParagraphStyle(
        "Footer",
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )

    def fmt(val):
        return "{:,.2f}".format(val or 0)

    # ===================== HEADER =====================
    header = Table(
        [[
            Paragraph(company.name, style_company),
            Paragraph("PAYSLIP", style_title)
        ]],
        colWidths=[120 * mm, 50 * mm]
    )

    header.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(header)
    elements.append(Spacer(1, 12))

    # ===================== EMPLOYEE INFO =====================
    info_data = [
        ["Employee Name", employee.full_name],
        ["IC / Passport", getattr(employee, "ic_number", "-")],
        ["Payroll Period", payroll.month_year],
    ]

    info_table = Table(info_data, colWidths=[45 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # ===================== EMPLOYEE EARNINGS & DEDUCTIONS =====================
    elements.append(Paragraph("EMPLOYEE EARNINGS & DEDUCTIONS", style_section))

    earnings = []
    deductions = []

    if payroll.basic_salary:
        earnings.append(("Basic Salary", fmt(payroll.basic_salary)))
    if payroll.fixed_allowance or payroll.additional_allowance:
        allowance = payroll.fixed_allowance + payroll.additional_allowance
        earnings.append(("Allowance", fmt(allowance)))
    if payroll.bonus:
        earnings.append(("Bonus", fmt(payroll.bonus)))
    if payroll.profit_sharing:
        earnings.append(("Profit Sharing", fmt(payroll.profit_sharing)))

    if payroll.epf_employee:
        deductions.append(("EPF (Employee)", f"-{fmt(payroll.epf_employee)}"))
    if payroll.socso_employee:
        deductions.append(("SOCSO (Employee)", f"-{fmt(payroll.socso_employee)}"))
    if payroll.eis_employee:
        deductions.append(("EIS (Employee)", f"-{fmt(payroll.eis_employee)}"))
    if payroll.salary_advanced:
        deductions.append(("Salary Advanced", f"-{fmt(payroll.salary_advanced)}"))

    rows = [[
        Paragraph("<b>EARNINGS</b>", style_cell_l), "",
        Paragraph("<b>DEDUCTIONS</b>", style_cell_l), ""
    ]]

    max_len = max(len(earnings), len(deductions))
    for i in range(max_len):
        e = earnings[i] if i < len(earnings) else ("", "")
        d = deductions[i] if i < len(deductions) else ("", "")
        rows.append([
            Paragraph(e[0], style_cell_l),
            Paragraph(e[1], style_cell_r),
            Paragraph(d[0], style_cell_l),
            Paragraph(d[1], style_cell_r),
        ])

    ed_table = Table(
        rows,
        colWidths=[70 * mm, 25 * mm, 70 * mm, 25 * mm]
    )

    ed_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(ed_table)
    elements.append(Spacer(1, 8))

    # ===================== TOTALS =====================
    total_deductions = (
        (payroll.epf_employee or 0) +
        (payroll.socso_employee or 0) +
        (payroll.eis_employee or 0) +
        (payroll.salary_advanced or 0)
    )

    totals_table = Table(
        [[
            "TOTAL EARNINGS", fmt(payroll.gross),
            "TOTAL DEDUCTIONS", f"-{fmt(total_deductions)}"
        ]],
        colWidths=[70 * mm, 25 * mm, 70 * mm, 25 * mm]
    )

    totals_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("ALIGN", (3, 0), (3, 0), "RIGHT"),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 12))

    # ===================== NET PAY (ALIGNED TO DEDUCTIONS) =====================
    net_table = Table(
        [["NET PAY", "MYR", fmt(payroll.net_pay)]],
        colWidths=[55 * mm, 12 * mm, 28 * mm]
    )

    net_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    net_container = Table(
        [["", net_table]],
        colWidths=[95 * mm, 95 * mm]
    )

    elements.append(net_container)

    # ===================== EMPLOYER CONTRIBUTIONS =====================
    employer_rows = []

    if getattr(payroll, "epf_employer", 0):
        employer_rows.append(("EPF (Employer)", fmt(payroll.epf_employer)))
    if getattr(payroll, "socso_employer", 0):
        employer_rows.append(("SOCSO (Employer)", fmt(payroll.socso_employer)))
    if getattr(payroll, "eis_employer", 0):
        employer_rows.append(("EIS (Employer)", fmt(payroll.eis_employer)))

    if employer_rows:
            elements.append(Spacer(1, 14))
            elements.append(Paragraph("<b>EMPLOYER CONTRIBUTIONS</b>", style_section))

            # 1. Create the actual data table
            employer_data_table = Table(
                employer_rows,
                colWidths=[45 * mm, 30 * mm]
            )

            employer_data_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))

            # 2. Wrap it in a full-width container table (190mm total width)
            # We put the data in the first column and leave the second column empty
            employer_container = Table(
                [[employer_data_table, ""]], 
                colWidths=[75 * mm, 115 * mm], # 75 + 115 = 190mm (Standard A4 content width)
                hAlign='LEFT'
            )
            
            employer_container.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            elements.append(employer_container)

    # ===================== FOOTER =====================
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "This is a computer-generated payslip. No signature is required.",
        style_footer
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def get_ea_records(db, employee_id, year):
    # Retrieve all records for the employee in the specific year
    # Assumes month_year is stored as 'YYYY-MM'
    records = db.query(models.PayrollRecord).filter(
        models.PayrollRecord.employee_id == employee_id,
        models.PayrollRecord.month_year.like(f"{year}-%")
    ).all()

    if not records:
        return None

    employee = db.query(models.Employee).get(employee_id)
    company = db.query(models.Company).filter(models.Company.id == employee.company_id).first()

    return {
        "year": year,
        "id": employee.id,
        "full_name": employee.full_name,
        "job_title": employee.job_title,
        "ic_no": employee.ic_number,
        "epf_no": employee.kwsp_number,
        "socso_no": employee.socso_number,
        "tin_number": employee.tin_number,
        "gross_salary": sum(r.basic_salary + r.fixed_allowance + r.additional_allowance + r.profit_sharing for r in records),
        "bonus": sum(r.bonus for r in records),
        "epf": sum(r.epf_employee for r in records),
        "socso_eis": sum(r.socso_employee + r.eis_employee for r in records),
        "pcb": 0,
        "company_name": company.name,
        "e_number": company.e_number,
        "address" : company.address,
        "phone_no": company.phone_no,
        "authorized_officer": company.authorized_officer,
        "officer_designation": company.officer_designation,
        "marital_status": employee.marital_status,
        "number_of_kids": employee.number_of_kids,
        "end_date": employee.end_date,
        "join_date": employee.join_date,
    }

def create_ea_overlay(data):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", 9)

    LEFT = 26 * mm
    TOP  = 297 * mm - (18 * mm)

    def pos(x_mm, y_mm_from_top):
        return LEFT + x_mm * mm, TOP - y_mm_from_top * mm

    # ======================
    # HEADER
    # ======================

    # x, y = pos(8, 2)
    # raw_id = data.get("id", 0)
    # formatted_id = f"EA{int(raw_id):05d}"
    # can.drawString(x, y, formatted_id)  

    x, y = pos(8, 7)
    can.drawString(x, y, data.get('e_number', ''))  

    x, y = pos(122, 2)
    can.drawString(x, y, data.get('tin_number', ''))  

    x, y = pos(103.5, 7.5)
    can.drawString(x, y, data.get('year', ''))  

    # ======================
    # SECTION A
    # ======================
    x, y = pos(75, 23)
    can.drawString(x, y, data.get('full_name', ''))  # A1

    x, y = pos(27, 28)
    can.drawString(x, y, data.get('job_title', ''))  # A2

    x, y = pos(27, 33)
    can.drawString(x, y, data.get('ic_no', ''))  # A4

    x, y = pos(27, 38)
    can.drawString(x, y, data.get('epf_no', ''))  # A6

    x, y = pos(130, 38)
    can.drawString(x, y, data.get('socso_no', ''))  # A7

    if data.get('number_of_kids') > 0:
        x, y = pos(40, 47)
        can.drawString(x, y, f"{data.get('number_of_kids')}")

    if data.get('end_date') and data.get('year') in str(data.get('end_date')):
        x, y = pos(130, 48)
        can.drawString(x, y, data.get('join_date', '').strftime('%d/%m/%Y'))
        x, y = pos(130, 53)
        can.drawString(x, y, data.get('end_date', '').strftime('%d/%m/%Y'))
    elif data.get('join_date') and data.get('year') in str(data.get('join_date')):
        x, y = pos(130, 48)
        can.drawString(x, y, data.get('join_date', '').strftime('%d/%m/%Y'))

    # ======================
    # SECTION B
    # ======================
    x, y = pos(165, 71)
    can.drawRightString(x, y, f"{data.get('gross_salary',0):,.2f}")  # B1a

    x, y = pos(165, 76)
    can.drawRightString(x, y, f"{data.get('bonus',0):,.2f}")  # B1b

    x, y = pos(165, 81)
    can.drawRightString(x, y, f"{data.get('other_allowance',0):,.2f}")  # B1c

    x, y = pos(165, 86)
    can.drawRightString(x, y, f"{0:,.2f}")  # B1d

    x, y = pos(165, 91)
    can.drawRightString(x, y, f"{0:,.2f}")  # B1e

    x, y = pos(165, 96)
    can.drawRightString(x, y, f"{0:,.2f}")  # B1f

    x, y = pos(165, 111)
    can.drawRightString(x, y, f"{0:,.2f}")  # B2

    x, y = pos(165, 116)
    can.drawRightString(x, y, f"{0:,.2f}")  # B3

    x, y = pos(165, 121)
    can.drawRightString(x, y, f"{0:,.2f}")  # B4

    x, y = pos(165, 126)
    can.drawRightString(x, y, f"{0:,.2f}")  # B5

    x, y = pos(165, 131)
    can.drawRightString(x, y, f"{0:,.2f}")  # B6

    # ======================
    # SECTION C
    # ======================
    x, y = pos(165, 144)
    can.drawRightString(x, y, f"{0:,.2f}")  # C1

    x, y = pos(165, 149)
    can.drawRightString(x, y, f"{0:,.2f}")  # C2

    x, y = pos(165, 156)
    can.drawRightString(x, y, f"{0:,.2f}")  # TOTAL

    # ======================
    # SECTION D
    # ======================
    x, y = pos(165, 168)
    can.drawRightString(x, y, f"{0:,.2f}")  # D1

    x, y = pos(165, 173)
    can.drawRightString(x, y, f"{0:,.2f}")  # D2

    x, y = pos(165, 178)
    can.drawRightString(x, y, f"{0:,.2f}")  # D3

    x, y = pos(165, 183)
    can.drawRightString(x, y, f"{0:,.2f}")  # D4

    if data.get('number_of_kids') > 0:
        tax_exemption = data.get('number_of_kids') * 2000
        x, y = pos(165, 201)
        can.drawRightString(x, y, f"{tax_exemption:,.2f}")  # D6

    # ======================
    # SECTION E
    # ======================
    x, y = pos(75, 215)
    can.drawRightString(x, y, 'KWSP')  # E1

    x, y = pos(165, 219)
    can.drawRightString(x, y, f"{data.get('epf',0):,.2f}")  # E1

    x, y = pos(165, 224)
    can.drawRightString(x, y, f"{data.get('socso_eis',0):,.2f}")  # E2

    # ======================
    # SECTION F
    # ======================
    x, y = pos(165, 232)
    can.drawRightString(x, y, f"{0:,.2f}")  # F

    # ======================
    # Officer (LEFT aligned)
    # ======================
    x, y = pos(92, 245)
    can.drawString(x, y, f"{data.get('authorized_officer', '-')}")

    x, y = pos(92, 250)
    can.drawString(x, y, f"{data.get('officer_designation', '-')}")

    # Ensure address is a string and not None to avoid AttributeError
    address = data.get("address") or ""

    line1 = address
    line2 = ""

    if "," in address:
        # Find the midpoint of the string
        mid_point = len(address) // 2
        
        # Get indices of all commas
        commas = [i for i, char in enumerate(address) if char == ","]
        
        if commas:
            # Find the comma closest to the middle of the address
            best_comma = min(commas, key=lambda x: abs(x - mid_point))
            
            # Split at that comma
            line1 = address[:best_comma].strip()
            line2 = address[best_comma + 1:].strip() # +1 skips the comma itself

    x, y = pos(92, 255)
    can.drawString(x, y, line1)
    if line2:
        x, y = pos(92, 260) 
        can.drawString(x, y, line2)

    x, y = pos(92, 264)
    can.drawString(x, y, f"{data.get('phone_no', '-')}")

    # ======================
    # Date
    # ======================
    x, y = pos(5, 264)
    today_str = date.today().strftime("%Y/%m/%d")
    can.drawString(x, y, f"{today_str}") 

    can.save()
    packet.seek(0)
    return packet




def merge_with_template(overlay_packet, template_filename="EA_FORM_2025.pdf"):
    try:
        # Load the official template you uploaded
        template_pdf = PdfReader(open(template_filename, "rb"))
        overlay_pdf = PdfReader(overlay_packet)
        
        output = PdfWriter()
        
        # Merge the first page of the template with our data overlay
        page = template_pdf.pages[0]
        page.merge_page(overlay_pdf.pages[0])
        output.add_page(page)
        
        return output
    except FileNotFoundError:
        print(f"Error: {template_filename} not found in the project directory.")
        return None

def generate_ea_pdf(db, employee_id: int, year: str):
    data = get_ea_records(db, employee_id, year)
    if not data:
        return None, None  # ← skip condition

    name = data["full_name"]
    company_name = data["company_name"]

    overlay = create_ea_overlay(data)
    final_pdf = merge_with_template(overlay)

    output_stream = io.BytesIO()
    final_pdf.write(output_stream)
    output_stream.seek(0)

    return output_stream, name, company_name