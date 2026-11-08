import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
from io import BytesIO
import qrcode
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ================= DATABASE =================
conn = sqlite3.connect('ambay_agency.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, item_name TEXT UNIQUE, size TEXT, color TEXT, gsm TEXT, unit TEXT, quantity REAL, price REAL, gst REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, bill_no TEXT, item_name TEXT, size TEXT, quantity REAL, unit TEXT, price REAL, gst_percent REAL, gst_amount REAL, total_price REAL, date TEXT, user TEXT, customer TEXT, payment_mode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, reason TEXT, amount REAL, date TEXT, user TEXT, payment_from TEXT)''')
conn.commit()

def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()

# ================= നിങ്ങളുടെ കടയുടെ വിവരങ്ങൾ =================
SHOP_NAME = "AMBAY AGENCY"
SHOP_GSTIN = "32ADOPN6536F1ZG"
SHOP_ADDRESS = "Olathanni, Neyyattinkara"
SHOP_PHONE = "9895533445"
YOUR_UPI_ID = "svnairnta-1@oksbi"
YOUR_NAME = "Ambay Agency"

# ================= QR CODE =================
def make_upi_qr(amount):
    upi_link = f"upi://pay?pa={YOUR_UPI_ID}&pn={YOUR_NAME}&am={amount:.2f}&cu=INR"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(upi_link); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0); return buf

# ================= PDF BILL =================
def make_pdf(bill_no, customer, staff, cart, subtotal, total_gst, grand, date_str, payment_mode):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, topMargin=12*mm, bottomMargin=12*mm, leftMargin=10*mm, rightMargin=10*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=18, alignment=TA_CENTER, spaceAfter=1)
    center_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, spaceAfter=1)
    normal = ParagraphStyle('N', parent=styles['Normal'], fontSize=9, spaceAfter=2)
    right_style = ParagraphStyle('R', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT, spaceAfter=2)
    story = []
    story.append(Paragraph(SHOP_NAME, title_style))
    story.append(Paragraph(f"{SHOP_ADDRESS}", center_style))
    story.append(Paragraph(f"Ph: {SHOP_PHONE} | GSTIN: {SHOP_GSTIN}", center_style))
    story.append(Paragraph("TAX INVOICE", ParagraphStyle('Tax', parent=center_style, fontName='Helvetica-Bold', fontSize=11)))
    story.append(Paragraph("----------------------------------------------", center_style))
    story.append(Paragraph(f"<b>Bill No:</b> {bill_no} &nbsp;&nbsp; <b>Date:</b> {date_str}", normal))
    story.append(Paragraph(f"<b>Customer:</b> {customer}", normal))
    story.append(Paragraph(f"<b>Billed By:</b> {staff} &nbsp;&nbsp; <b>Payment:</b> {payment_mode}", normal))
    story.append(Spacer(1, 4))
    data = [["#", "Item", "Size", "Qty", "Price", "Total"]]
    for i, it in enumerate(cart, 1):
        data.append([str(i), it['item'], it['size'], f"{it['qty']} {it['unit']}", f"{it['price']:.2f}", f"{it['total']:.2f}"])
    t = Table(data, colWidths=[18, 130, 60, 50, 60, 65])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1f4e79')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),8.5),('BOTTOMPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#EAF2F8')])]))
    story.append(t); story.append(Spacer(1,6))
    story.append(Paragraph(f"Sub Total: Rs. {subtotal:,.2f}", right_style))
    story.append(Paragraph(f"CGST (9%): Rs. {total_gst/2:,.2f}", right_style))
    story.append(Paragraph(f"SGST (9%): Rs. {total_gst/2:,.2f}", right_style))
    story.append(Paragraph(f"Total GST: Rs. {total_gst:,.2f}", right_style))
    story.append(Paragraph(f"<b>Grand Total: Rs. {grand:,.2f}</b>", ParagraphStyle('BR', parent=right_style, fontName='Helvetica-Bold', fontSize=12)))
    story.append(Paragraph(f"Paid By: {payment_mode}", right_style))
    story.append(Spacer(1,8))
    story.append(Paragraph("Thank You! Visit Again", center_style))
    story.append(Paragraph(f"{SHOP_NAME} - {SHOP_PHONE}", center_style))
    story.append(Paragraph("Goods once sold will not be taken back.", center_style))
    doc.build(story); buffer.seek(0); return buffer

# ================= 5 USERS =================
users_list = [
    ("owner", "owner123", "Owner"),
    ("staff1", "staff123", "Staff 1"),
    ("staff2", "staff123", "Staff 2"),
    ("staff3", "staff123", "Staff 3"),
    ("staff4", "staff123", "Staff 4"),
]
for u, p, n in users_list:
