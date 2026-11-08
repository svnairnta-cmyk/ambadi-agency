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

conn = sqlite3.connect('ambay_agency.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, item_name TEXT UNIQUE, size TEXT, color TEXT, gsm TEXT, unit TEXT, quantity REAL, price REAL, gst REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, bill_no TEXT, item_name TEXT, size TEXT, quantity REAL, unit TEXT, price REAL, gst_percent REAL, gst_amount REAL, total_price REAL, date TEXT, user TEXT, customer TEXT, payment_mode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, reason TEXT, amount REAL, date TEXT, user TEXT, payment_from TEXT)''')
conn.commit()

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

SHOP_NAME = "AMBAY AGENCY"
SHOP_GSTIN = "32ADOPN6536F1ZG"
SHOP_ADDRESS = "Olathanni, Neyyattinkara"
SHOP_PHONE = "9895533445"
YOUR_UPI_ID = "svnairnta-1@oksbi"
YOUR_NAME = "Ambay Agency"

def make_upi_qr(amount):
    upi_link = "upi://pay?pa=" + YOUR_UPI_ID + "&pn=" + YOUR_NAME + "&am=" + str(round(amount, 2)) + "&cu=INR"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

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
    story.append(Paragraph(SHOP_ADDRESS, center_style))
    story.append(Paragraph("Ph: " + SHOP_PHONE + " | GSTIN: " + SHOP_GSTIN, center_style))
    story.append(Paragraph("TAX INVOICE", ParagraphStyle('Tax', parent=center_style, fontName='Helvetica-Bold', fontSize=11)))
    story.append(Paragraph("----------------------------------------------", center_style))
    story.append(Paragraph("<b>Bill No:</b> " + bill_no + " | <b>Date:</b> " + date_str, normal))
    story.append(Paragraph("<b>Customer:</b> " + customer, normal))
    story.append(Paragraph("<b>Billed By:</b> " + staff + " | <b>Payment:</b> " + payment_mode, normal))
    story.append(Spacer(1, 4))
    data = [["#", "Item", "Size", "Qty", "Price", "Total"]]
    for i, it in enumerate(cart, 1):
        data.append([str(i), it['item'], it['size'], str(it['qty']) + " " + it['unit'], str(round(it['price'], 2)), str(round(it['total'], 2))])
    t = Table(data, colWidths=[18, 130, 60, 50, 60, 65])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('FONTSIZE', (0, 0), (-1, -1), 8.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EAF2F8')])]))
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Sub Total: Rs. " + str(round(subtotal, 2)), right_style))
    story.append(Paragraph("CGST: Rs. " + str(round(total_gst / 2, 2)), right_style))
    story.append(Paragraph("SGST: Rs. " + str(round(total_gst / 2, 2)), right_style))
    story.append(Paragraph("Total GST: Rs. " + str(round(total_gst, 2)), right_style))
    story.append(Paragraph("<b>Grand Total: Rs. " + str(round(grand, 2)) + "</b>", ParagraphStyle('BR', parent=right_style, fontName='Helvetica-Bold', fontSize=12)))
    story.append(Paragraph("Paid By: " + payment_mode, right_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Thank You! Visit Again", center_style))
    story.append(Paragraph(SHOP_NAME + " - " + SHOP_PHONE, center_style))
    doc.build(story)
    buffer.seek(0)
    return buffer

users_list = [
    ("owner", "owner123", "Owner"),
    ("staff1", "staff123", "Staff 1"),
    ("staff2", "staff123", "Staff 2"),
    ("staff3", "staff123", "Staff 3"),
    ("staff4", "staff123", "Staff 4"),
]
for u, p, n in users_list:
    try:
        c.execute("INSERT INTO users VALUES (?,?,?)", (u, hash_pass(p), n))
        conn.commit()
    except:
        pass

tarpaulin_stock = [
    ("HDPE Tarpaulin", "Tarpaulin 9x12 Blue", "9x12 ft", "Blue", "120 GSM", "Nos", 100, 450.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 12x15 Blue", "12x15 ft", "Blue", "120 GSM", "Nos", 80, 680.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 15x18 Blue", "15x18 ft", "Blue", "120 GSM", "Nos", 60, 950.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 18x24 Blue", "18x24 ft", "Blue", "120 GSM", "Nos", 40, 1450.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 12x18 Green", "12x18 ft", "Green", "120 GSM", "Nos", 50, 820.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 9x12 Green", "9x12 ft", "Green", "120 GSM", "Nos", 70, 460.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 15x20 Orange", "15x20 ft", "Orange", "150 GSM", "Nos", 45, 1150.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 20x30 Blue Heavy", "20x30 ft", "Blue", "200 GSM", "Nos", 25, 2450.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 12x12 White", "12x12 ft", "White", "120 GSM", "Nos", 60, 620.0, 18.0),
    ("HDPE Tarpaulin", "Tarpaulin 10x10 Black", "10x10 ft", "Black", "150 GSM", "Nos", 55, 550.0, 18.0),
    ("PVC Tarpaulin", "PVC Tarpaulin 12x18 Yellow", "12x18 ft", "Yellow", "350 GSM", "Nos", 30, 1850.0, 18.0),
    ("PVC Tarpaulin", "PVC Tarpaulin 15x20 Green", "15x20 ft", "Green", "350 GSM", "Nos", 20, 2450.0, 18.0),
    ("PVC Tarpaulin", "PVC Tarpaulin 10x15 Blue", "10x15 ft", "Blue", "300 GSM", "Nos", 35, 1450.0, 18.0),
    ("Canvas", "Canvas Tarpaulin 12x15", "12x15 ft", "Brown", "Canvas", "Nos", 20, 2100.0, 18.0),
    ("Canvas", "Canvas Tarpaulin 9x12", "9x12 ft", "Brown", "Canvas", "Nos", 30, 1450.0, 18.0),
    ("Roll / Meter", "Tarpaulin Roll Blue 120 GSM", "Roll", "Blue", "120 GSM", "Meter", 500, 45.0, 18.0),
    ("Roll / Meter", "Tarpaulin Roll Green 150 GSM", "Roll", "Green", "150 GSM", "Meter", 400, 58.0, 18.0),
    ("Roll / Meter", "Tarpaulin Roll White 200 GSM", "Roll", "White", "200 GSM", "Meter", 200, 85.0, 18.0),
    ("Accessories", "Tarpaulin Rope Nylon", "Roll", "White", "-", "Roll", 50, 180.0, 18.0),
    ("Accessories", "Tarpaulin Eyelet Packet", "Packet", "Silver", "-", "Packet", 100, 95.0, 18.0),
    ("Accessories", "Tarpaulin Clip Set", "Set", "Silver", "-", "Set", 80, 120.0, 18.0),
    ("Accessories", "Bungee Cord 1m", "Nos", "Black", "-", "Nos", 100, 35.0, 18.0),
]
for cat, name, size, color, gsm, unit, qty, price, gst in tarpaulin_stock:
    try:
        c.execute("INSERT INTO stock (category, item_name, size, color, gsm, unit, quantity, price, gst) VALUES (?,?,?,?,?,?,?,?,?)", (cat, name, size, color, gsm, unit, qty, price, gst))
        conn.commit()
    except:
        pass

def get_today_summary():
    today_str = datetime.now().strftime("%Y-%m-%d")
    df_sales = pd.read_sql_query("SELECT payment_mode, total_price FROM sales WHERE date LIKE ?", conn, params=(today_str + "%",))
    cash = 0
    upi = 0
    card = 0
    credit = 0
    total_sale = 0
    if not df_sales.empty:
        cash = df_sales[df_sales['payment_mode'] == 'Cash']['total_price'].sum()
        upi = df_sales[df_sales['payment_mode'] == 'UPI']['total_price'].sum()
        card = df_sales[df_sales['payment_mode'] == 'Card']['total_price'].sum()
        credit = df_sales[df_sales['payment_mode'] == 'Credit']['total_price'].sum()
        total_sale = df_sales['total_price'].sum()
    df_exp = pd.read_sql_query("SELECT amount, payment_from FROM expenses WHERE date LIKE ?", conn, params=(today_str + "%",))
    total_exp = 0
    exp_cash = 0
    exp_upi = 0
    if not df_exp.empty:
        total_exp = df_exp['amount'].sum()
        exp_cash = df_exp[df_exp['payment_from'] == 'Cash']['amount'].sum()
        exp_upi = df_exp[df_exp['payment_from'] == 'UPI']['amount'].sum()
    cash_bal = cash - exp_cash
    upi_bal = upi - exp_upi
    balance = total_sale - total_exp
    return cash, upi, card, credit, total_sale, total_exp, cash_bal, upi_bal, balance

st.set_page_config(page_title="Ambay Agency - Billing", layout="wide")
st.title("AMBAY AGENCY - Olathanni, Neyyattinkara")
st.caption("Ph: " + SHOP_PHONE + " | GSTIN: " + SHOP_GSTIN + " | UPI: " + YOUR_UPI_ID)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['name'] = ""
    st.session_state['cart'] = []
    st.session_state['last_bill'] = None

if not st.session_state['logged_in']:
    st.subheader("Login - 5 Perukku")
    st.info("owner / owner123 | staff1 / staff123 | staff2 / staff123 | staff3 / staff123 | staff4 / staff123")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login Cheyyuka"):
        c.execute("SELECT username, name FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
        row = c.fetchone()
        if row:
            st.session_state['logged_in'] = True
            st.session_state['username'] = row[0]
            st.session_state['name'] = row[1]
            st.rerun()
        else:
            st.error("Thattaya Username / Password")
else:
    st.sidebar.write("User: " + st.session_state['name'])
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['cart'] = []
        st.rerun()
    cash, upi, card, credit, total_sale, total_exp, cash_bal, upi_bal, balance = get_today_summary()
    st.subheader("Innu - " + datetime.now().strftime('%d-%m-%Y'))
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Cash", str(round(cash_bal)))
    c2.metric("【entity-GPay¦canonical_name=GPay】 / UPI", str(round(upi_bal)))
    c3.metric("Card", str(round(card)))
    c4.metric("Kadam", str(round(credit)))
    c5.metric("Expense", str(round(total_exp)))
    c6.metric("Balance", str(round(balance, 2)))
    st.divider()
    if st.session_state['username'] == "owner":
        menu = ["Billing", "Stock List", "Stock Cherkkuka", "Chelavu Cherkkuka", "Report", "User Manage"]
    else:
        menu = ["Billing", "Stock List", "Stock Cherkkuka", "Chelavu Cherkkuka", "Report"]
    choice = st.sidebar.selectbox("Menu", menu)
    if choice == "Billing":
        st.subheader("Puthiya Bill")
        customer = st.text_input("Customer Peru / Phone")
        c.execute("SELECT item_name FROM stock WHERE quantity > 0 ORDER BY item_name")
        items = [r[0] for r in c.fetchall()]
        if items:
            sel = st.selectbox("Tarpaulin Thiranjedukkuka", items)
            c.execute("SELECT quantity, price, unit, size, gst FROM stock WHERE item_name=?", (sel,))
            avail, price, unit, size, gst_per = c.fetchone()
            st.write("Stockil Ullathu:")
            st.write(avail)
            st.write("Size:")
            st.write(size)
            st.write("Vila:")
            st.write(price)
            st.write("GST:")
            st.write(gst_per)
            qty = st.number_input("Alavu", min_value=0.5, max_value=float(avail), value=1.0)
            base = qty * price
            gst_amt = base * gst_per / 100
            total = base + gst_amt
            st.write("GST Amount:")
            st.write(gst_amt)
            st.write("Aake:")
            st.write(total)
            if st.button("Cartilekku Cherkkuka"):
                st.session_state['cart'].append({"item": sel, "size": size, "qty": qty, "unit": unit, "price": price, "gst": gst_per, "base": base, "gst_amt": gst_amt, "total": total})
                st.rerun()
            if st.session_state['cart']:
                cdf = pd.DataFrame(st.session_state['cart'])
                st.dataframe(cdf, use_container_width=True)
                subtotal = cdf['base'].sum()
                total_gst = cdf['gst_amt'].sum()
                grand = cdf['total'].sum()
                st.metric("Grand Total", str(round(grand, 2)))
                st.divider()
                st.subheader("Payment Engane?")
                payment_mode = st.radio("Customer Engane Tharum?", ["Cash", "UPI / QR - 【entity-GPay¦canonical_name=GPay】", "Card", "Kadam / Credit"], horizontal=True)
                upi_paid = True
                if "UPI" in payment_mode:
                    st.info("Customer QR Scan Cheyyan Parayu")
                    st.write(grand)
                    qr_buf = make_upi_qr(grand)
                    st.image(qr_buf, width=230)
                    upi_paid = st.checkbox("【entity-GPay¦canonical_name=GPay】 Vanthu, Confirm Cheyyuka")
                elif "Kadam" in payment_mode:
                    st.warning("Ithu Kadam Aayi Rekhappeduthum")
                if st.button("Bill Save Cheyyuka", disabled=("UPI" in payment_mode and not upi_paid)):
                    pm_short = "Cash"
                    if "UPI" in payment_mode:
                        pm_short = "UPI"
                    elif "Card" in payment_mode:
                        pm_short = "Card"
                    elif "Kadam" in payment_mode:
                        pm_short = "Credit"
                    bill_no = datetime.now().strftime("INV-%Y%m%d-%H%M%S")
                    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    today_d = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    for it in st.session_state['cart']:
                        c.execute("UPDATE stock SET quantity = quantity - ? WHERE item_name=?", (it['qty'], it['item']))
                        c.execute("INSERT INTO sales (bill_no, item_name, size, quantity, unit, price, gst_percent, gst_amount, total_price, date, user, customer, payment_mode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (bill_no, it['item'], it['size'], it['qty'], it['unit'], it['price'], it['gst'], it['gst_amt'], it['total'], today, st.session_state['username'], customer, pm_short))
                    conn.commit()
                    pdf = make_pdf(bill_no, customer if customer else "Walk-in Customer", st.session_state['name'], st.session_state['cart'], subtotal, total_gst, grand, today_d, pm_short)
                    st.session_state['last_bill'] = {"bill_no": bill_no, "pdf": pdf.getvalue(), "total": grand, "payment": pm_short}
                    st.session_state['cart'] = []
                    st.success("Bill Poorthiyayi!")
                    st.rerun()
            if st.session_state.get('last_bill'):
                lb = st.session_state['last_bill']
                st.divider()
                st.success("Avashana Bill:")
                st.write(lb['bill_no'])
                st.download_button("PDF Bill Download", data=lb['pdf'], file_name=lb['bill_no'] + ".pdf", mime="application/pdf")
        else:
            st.warning("Stock Illa!")
    elif choice == "Stock List":
        st.subheader("Stock List - Live")
        search = st.text_input("Thirayuka")
        df = pd.read_sql_query("SELECT category as Category, item_name as Sadhanam, size as Size, color as Color, gsm as GSM, quantity as Stock, unit as Unit, price as Vila, gst as GST FROM stock ORDER BY category", conn)
        if search:
            df = df[df['Sadhanam'].str.contains(search, case=False) | df['Size'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True)
        st.write("Aake Stock:")
        st.write(df['Stock'].sum())
    elif choice == "Stock Cherkkuka":
        st.subheader("Stock Cherkkuka")
        cat = st.selectbox("Category", ["HDPE Tarpaulin", "PVC Tarpaulin", "Canvas", "Roll / Meter", "Accessories"])
        name = st.text_input("Sadhnathinte Peru")
        size = st.text_input("Size")
        color = st.selectbox("Color", ["Blue", "Green", "White", "Black", "Orange", "Yellow", "Brown", "Silver"])
        gsm = st.selectbox("GSM", ["120 GSM", "150 GSM", "200 GSM", "300 GSM", "350 GSM", "Canvas"])
        unit = st.selectbox("Unit", ["Nos", "Meter", "Roll", "Packet", "Set"])
        qty = st.number_input("Ethra Cherkkanam?", min_value=0.5, value=10.0)
        price = st.number_input("Vila", min_value=0.0, value=500.0)
        gst = st.selectbox("GST %", [18.0, 12.0, 5.0, 28.0], index=0)
        if st.button("Stockilekku Cherkkuka"):
            if name:
                c.execute("SELECT quantity FROM stock WHERE item_name=?", (name,))
                ex = c.fetchone()
                if ex:
                    c.execute("UPDATE stock SET quantity=?, price=?, gst=? WHERE item_name=?", (ex[0] + qty, price, gst, name))
                    st.success("Pazhaya Stock + Puthiya Stock = Koodi")
                else:
                    c.execute("INSERT INTO stock (category, item_name, size, color, gsm, unit, quantity, price, gst) VALUES (?,?,?,?,?,?,?,?,?)", (cat, name, size, color, gsm, unit, qty, price, gst))
                    st.success("Stock Chertu")
                conn.commit()
            else:
                st.error("Peru Kodukkuka!")
    elif choice == "Chelavu Cherkkuka":
        st.subheader("Innatthe Chelavu")
        reason = st.selectbox("Enthinan Chelavu?", ["Chaya / Bhakshanam", "Petrol / Diesel", "Auto / Loading", "Kada Vadaka", "Current Bill", "Staff Shambalam", "Sadhanam Vangiyathu", "Mattullavar"])
        custom = st.text_input("Vere Enthelum Aanel Ezhuthuka")
        final_reason = custom if custom else reason
        amount = st.number_input("Ethra Roopa?", min_value=1.0, value=100.0)
        pay_from = st.radio("Evidunnu Koduthu?", ["Cash", "UPI - GPay"], horizontal=True)
        pay_short = "Cash" if "Cash" in pay_from else "UPI"
        if st.button("Chelavu Save Cheyyuka"):
            today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO expenses (reason, amount, date, user, payment_from) VALUES (?,?,?,?,?)", (final_reason, amount, today, st.session_state['username'], pay_short))
            conn.commit()
            st.success("Chelavu Save Aayi")
            st.rerun()
        st.divider()
        today_str = datetime.now().strftime("%Y-%m-%d")
        df_exp = pd.read_sql_query("SELECT reason as Karanam, amount as Thuka, payment_from as Evidunnu, user as Ezhuthiyathu, date as Samayam FROM expenses WHERE date LIKE ? ORDER BY date DESC", conn, params=(today_str + "%",))
        st.dataframe(df_exp, use_container_width=True)
    elif choice == "Report":
        st.subheader("Innatthe Final Report")
        st.write("Cash:")
        st.write(cash)
        st.write("GPay:")
        st.write(upi)
        st.write("Card:")
        st.write(card)
        st.write("Kadam:")
        st.write(credit)
        st.write("Aake Vilpana:")
        st.write(total_sale)
        st.write("Aake Chelavu:")
        st.write(total_exp)
        st.success("Balance:")
        st.write(balance)
        df = pd.read_sql_query("SELECT bill_no as BillNo, customer as Customer, item_name as Sadhanam, size as Size, quantity as Alavu, total_price as Aake, payment_mode as Payment, date as Thiyathi, user as Vittayal FROM sales ORDER BY date DESC", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Report Excel Aayi Download", csv, "ambay_sales.csv", "text/csv")
        else:
            st.info("Vilpana Illa")
    elif choice == "User Manage":
        st.subheader("User Manage - Owner Only")
        st.info("Neengal Evide Aayirunthalum Ivide Ninnu Maatam")
        st.write("Ippol Active Aayittullavar")
        df_users = pd.read_sql_query("SELECT username as Username, name as Peru FROM users", conn)
        st.dataframe(df_users, use_container_width=True)
        st.divider()
        st.write("Puthiya Aale Cherkkuka")
        new_user = st.text_input("Puthiya Username")
        new_name = st.text_input("Peru")
        new_pass = st.text_input("Password", type="password")
        if st.button("Puthiya Aale Cherkkuka"):
            if new_user and new_pass:
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (new_user, hash_pass(new_pass), new_name))
                    conn.commit()
                    st.success("Puthiya Aal Chertu")
                    st.rerun()
                except:
                    st.error("Ee Username Nerathe Undu!")
            else:
                st.error("Username + Password Kodukkuka!")
        st.divider()
        st.write("Password Maattuka")
        c.execute("SELECT username FROM users ORDER BY username")
        all_users_list = [r[0] for r in c.fetchall()]
        sel_user_pass = st.selectbox("Aarude Password Maattanam?", all_users_list)
        new_pass2 = st.text_input("Puthiya Password", type="password", key="pass2")
        if st.button("Password Maattuka"):
            if new_pass2:
                c.execute("UPDATE users SET password=? WHERE username=?", (hash_pass(new_pass2), sel_user_pass))
                conn.commit()
                st.success("Password Maati")
            else:
                st.error("Puthiya Password Ezhuthuka!")
        st.divider()
        st.write("Oraale Cancel Cheyyuka")
        st.warning("Ivide Cancel Cheythal Udan Avanu Login Cheyyaan Pattilla")
        c.execute("SELECT username FROM users WHERE username != 'owner' ORDER BY username")
        cancel_list = [r[0] for r in c.fetchall()]
        if cancel_list:
            del_user = st.selectbox("Aareyaanu Ozhivakkanam?", cancel_list)
            if st.button("Cancel Cheyyuka"):
                c.execute("DELETE FROM users WHERE username=?", (del_user,))
                conn.commit()
                st.success("Cancel Aayi")
                st.balloons()
                st.rerun()
        else:
            st.info("Cancel Cheyyaan Vere Aarum Illa")
