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
    upi_link = f"upi://pay?pa={YOUR_UPI_ID}&pn={YOUR_NAME}&am={amount:.2f}&cu=INR"
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
    story.append(t)
    story.append(Spacer(1,6))
    story.append(Paragraph(f"Sub Total: Rs. {subtotal:,.2f}", right_style))
    story.append(Paragraph(f"CGST (9%): Rs. {total_gst/2:,.2f}", right_style))
    story.append(Paragraph(f"SGST (9%): Rs. {total_gst/2:,.2f}", right_style))
    story.append(Paragraph(f"Total GST: Rs. {total_gst:,.2f}", right_style))
    story.append(Paragraph(f"<b>Grand Total: Rs. {grand:,.2f}</b>", ParagraphStyle('BR', parent=right_style, fontName='Helvetica-Bold', fontSize=12)))
    story.append(Paragraph(f"Paid By: {payment_mode}", right_style))
    story.append(Spacer(1,8))
    story.append(Paragraph("Thank You! Visit Again", center_style))
    story.append(Paragraph(f"{SHOP_NAME} - {SHOP_PHONE}", center_style))
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
    df_sales = pd.read_sql_query("SELECT payment_mode, total_price FROM sales WHERE date LIKE ?", conn, params=(f"{today_str}%",))
    cash = df_sales[df_sales['payment_mode']=='Cash']['total_price'].sum() if not df_sales.empty else 0
    upi = df_sales[df_sales['payment_mode']=='UPI']['total_price'].sum() if not df_sales.empty else 0
    card = df_sales[df_sales['payment_mode']=='Card']['total_price'].sum() if not df_sales.empty else 0
    credit = df_sales[df_sales['payment_mode']=='Credit']['total_price'].sum() if not df_sales.empty else 0
    total_sale = df_sales['total_price'].sum() if not df_sales.empty else 0
    df_exp = pd.read_sql_query("SELECT amount, payment_from FROM expenses WHERE date LIKE ?", conn, params=(f"{today_str}%",))
    total_exp = df_exp['amount'].sum() if not df_exp.empty else 0
    exp_cash = df_exp[df_exp['payment_from']=='Cash']['amount'].sum() if not df_exp.empty else 0
    exp_upi = df_exp[df_exp['payment_from']=='UPI']['amount'].sum() if not df_exp.empty else 0
    cash_bal = cash - exp_cash
    upi_bal = upi - exp_upi
    balance = total_sale - total_exp
    return cash, upi, card, credit, total_sale, total_exp, cash_bal, upi_bal, balance

st.set_page_config(page_title="Ambay Agency - Billing", layout="wide")
st.title("⛺ AMBAY AGENCY - Olathanni, Neyyattinkara")
st.caption(f"Ph: {SHOP_PHONE} | GSTIN: {SHOP_GSTIN} | UPI: {YOUR_UPI_ID}")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['name'] = ""
    st.session_state['cart'] = []
    st.session_state['last_bill'] = None

if not st.session_state['logged_in']:
    st.subheader("🔑 ലോഗിൻ - 5 പേർക്ക്")
    st.info("owner / owner123  |  staff1 / staff123  |  staff2 / staff123  |  staff3 / staff123  |  staff4 / staff123")
    u = st.text_input("യൂസർനെയിം")
    p = st.text_input("പാസ്‌വേഡ്", type="password")
    if st.button("ലോഗിൻ ചെയ്യുക"):
        c.execute("SELECT username, name FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
        row = c.fetchone()
        if row:
            st.session_state['logged_in'] = True
            st.session_state['username'] = row[0]
            st.session_state['name'] = row[1]
            st.rerun()
        else:
            st.error("തെറ്റായ യൂസർനെയിം / പാസ്‌വേഡ്")
else:
    st.sidebar.write(f"👤 {st.session_state['name']} | 🟢 ലൈവ്")
    st.sidebar.write(f"{SHOP_NAME}\n{SHOP_ADDRESS}")
    if st.sidebar.button("ലോഗ് ഔട്ട്"):
        st.session_state['logged_in'] = False
        st.session_state['cart'] = []
        st.rerun()
    cash, upi, card, credit, total_sale, total_exp, cash_bal, upi_bal, balance = get_today_summary()
    st.subheader(f"📅 ഇന്ന് - {datetime.now().strftime('%d-%m-%Y')}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💵 Cash", f"₹{cash_bal:,.0f}", f"വിൽപ്പന ₹{cash:,.0f}")
    c2.metric("📱 【entity-GPay¦canonical_name=GPay】 / UPI", f"₹{upi_bal:,.0f}", f"വിൽപ്പന ₹{upi:,.0f}")
    c3.metric("💳 Card", f"₹{card:,.0f}")
    c4.metric("📒 കടം", f"₹{credit:,.0f}")
    c5.metric("🧾 Expense", f"₹{total_exp:,.0f}", delta=f"-₹{total_exp:,.0f}", delta_color="inverse")
    c6.metric("💰 Balance", f"₹{balance:,.2f}", f"ആകെ ₹{total_sale:,.0f}")
    st.divider()
    if st.session_state['username'] == "owner":
        menu = ["🧾 ബില്ലിംഗ്", "📦 സ്റ്റോക്ക് ലിസ്റ്റ്", "➕ സ്റ്റോക്ക് ചേർക്കുക", "🧾 ചെലവ് ചേർക്കുക", "📈 റിപ്പോർട്ട്", "👤 യൂസർ മാനേജ്"]
    else:
        menu = ["🧾 ബില്ലിംഗ്", "📦 സ്റ്റോക്ക് ലിസ്റ്റ്", "➕ സ്റ്റോക്ക് ചേർക്കുക", "🧾 ചെലവ് ചേർക്കുക", "📈 റിപ്പോർട്ട്"]
    choice = st.sidebar.selectbox("മെനു", menu)
    if choice == "🧾 ബില്ലിംഗ്":
        st.subheader("🧾 പുതിയ ബിൽ")
        customer = st.text_input("കസ്റ്റമർ പേര് / ഫോൺ", placeholder="ഉദാ: രാജേഷ് - 98955...")
        c.execute("SELECT item_name FROM stock WHERE quantity > 0 ORDER BY item_name")
        items = [r[0] for r in c.fetchall()]
        if items:
            sel = st.selectbox("ടാർപ്പോളിൻ തിരഞ്ഞെടുക്കുക", items)
            c.execute("SELECT quantity, price, unit, size, gst FROM stock WHERE item_name=?", (sel,))
            avail, price, unit, size, gst_per = c.fetchone()
            st.write(f"സ്റ്റോക്കിൽ ഉള്ളത്: **{avail} {unit}** | സൈസ്: **{size}** | വില: **₹{price}** | GST: **{gst_per}%**")
            qty = st.number_input(f"അളവ് ({unit})", min_value=0.5, max_value=float(avail), value=1.0)
            base = qty*price
            gst_amt = base*gst_per/100
            total = base+gst_amt
            st.write(f"GST: ₹{gst_amt:.2f} | ആകെ: **₹{total:.2f}**")
            if st.button("കാർട്ടിലേക്ക് ചേർക്കുക"):
                st.session_state['cart'].append({"item": sel, "size": size, "qty": qty, "unit": unit, "price": price, "gst": gst_per, "base": base, "gst_amt": gst_amt, "total": total})
                st.rerun()
            if st.session_state['cart']:
                cdf = pd.DataFrame(st.session_state['cart'])
                st.dataframe(cdf, use_container_width=True)
                subtotal = cdf['base'].sum()
                total_gst = cdf['gst_amt'].sum()
                grand = cdf['total'].sum()
                st.metric("Grand Total (GST സഹിതം)", f"₹{grand:,.2f}")
                st.divider()
                st.subheader("💰 പേയ്‌മെന്റ് എങ്ങനെ?")
                payment_mode = st.radio("കസ്റ്റമർ എങ്ങനെ തരും?", ["💵 Cash - കാശ്", "📱 UPI / QR - GPay", "💳 Card - കാർഡ്", "📒 കടം / Credit - പിന്നെ തരും"], horizontal=True)
                upi_paid = True
                if "UPI" in payment_mode:
                    st.info(f"കസ്റ്റമറോട് ഈ QR സ്കാൻ ചെയ്യാൻ പറയൂ - ₹{grand:,.2f} to {YOUR_UPI_ID}")
                    qr_buf = make_upi_qr(grand)
                    st.image(qr_buf, width=230, caption=f"Pay ₹{grand:,.2f} to {YOUR_UPI_ID}")
                    upi_paid = st.checkbox("✅ GPay വന്നു, കൺഫേം ചെയ്യുക")
                elif "കടം" in payment_mode:
                    st.warning("⚠️ ഇത് കടം ആയി രേഖപ്പെടുത്തും.")
                if st.button("✅ ബിൽ സേവ് ചെയ്യുക", disabled=("UPI" in payment_mode and not upi_paid)):
                    pm_short = "Cash" if "Cash" in payment_mode else "UPI" if "UPI" in payment_mode else "Card" if "Card" in payment_mode else "Credit"
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
                    st.success(f"ബിൽ പൂർത്തിയായി! {bill_no} | {pm_short} ₹{grand:,.2f} | സ്റ്റോക്ക് കുറഞ്ഞു.")
                    st.rerun()
            if st.session_state.get('last_bill'):
                lb = st.session_state['last_bill']
                st.divider()
                st.success(f"✅ അവസാന ബിൽ: {lb['bill_no']} - ₹{lb['total']:,.2f} - {lb['payment']}")
                st.download_button("🖨️ PDF ബിൽ ഡൗൺലോഡ് / പ്രിന്റ് ചെയ്യുക", data=lb['pdf'], file_name=f"{lb['bill_no']}.pdf", mime="application/pdf")
        else:
            st.warning("സ്റ്റോക്ക് ഇല്ല!")
    elif choice == "📦 സ്റ്റോക്ക് ലിസ്റ്റ്":
        st.subheader("📦 സ്റ്റോക്ക് ലിസ്റ്റ് - ലൈവ്")
        search = st.text_input("🔍 തിരയുക - ഉദാ: 12x15, Blue")
        df = pd.read_sql_query("SELECT category as 'കാറ്റഗറി', item_name as 'സാധനം', size as 'സൈസ്', color as 'കളർ', gsm as 'GSM', quantity as 'സ്റ്റോക്ക്', unit as 'യൂണിറ്റ്', price as 'വില ₹', gst as 'GST %' FROM stock ORDER BY category", conn)
        if search:
            df = df[df['സാധനം'].str.contains(search, case=False) | df['സൈസ്'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True)
        st.metric("ആകെ സ്റ്റോക്ക്", f"{df['സ്റ്റോക്ക്'].sum():,.0f}")
        low = df[df['സ്റ്റോക്ക്'] <= 10]
        if not low.empty:
            st.warning(f"⚠️ സ്റ്റോക്ക് തീരാറായി: {', '.join(low['സാധനം'].tolist())}")
    elif choice == "➕ സ്റ്റോക്ക് ചേർക്കുക":
        st.subheader("➕ സ്റ്റോക്ക് ചേർക്കുക - എത്ര വേണമെങ്കിലും")
        cat = st.selectbox("കാറ്റഗറി", ["HDPE Tarpaulin", "PVC Tarpaulin", "Canvas", "Roll / Meter", "Accessories"])
        name = st.text_input("സാധനത്തിന്റെ പേര് - ഉദാ: Tarpaulin 12x15 Blue")
        size = st.text_input("സൈസ് - ഉദാ: 12x15 ft")
        color = st.selectbox("കളർ", ["Blue", "Green", "White", "Black", "Orange", "Yellow", "Brown", "Silver"])
        gsm = st.selectbox("GSM", ["120 GSM", "150 GSM", "200 GSM", "300 GSM", "350 GSM", "Canvas"])
        unit = st.selectbox("യൂണിറ്റ്", ["Nos", "Meter", "Roll", "Packet", "Set"])
        qty = st.number_input("എത്ര ചേർക്കണം?", min_value=0.5, value=10.0)
        price = st.number_input("വില ₹ (GST ഇല്ലാതെ)", min_value=0.0, value=500.0)
        gst = st.selectbox("GST %", [18.0, 12.0, 5.0, 28.0], index=0)
        if st.button("സ്റ്റോക്കിലേക്ക് ചേർക്കുക"):
            if name:
                c.execute("SELECT quantity FROM stock WHERE item_name=?", (name,))
                ex = c.fetchone()
                if ex:
                    c.execute("UPDATE stock SET quantity=?, price=?, gst=? WHERE item_name=?", (ex[0]+qty, price, gst, name))
                    st.success(f"പഴയത് {ex[0]} + പുതിയത് {qty} = ആകെ {ex[0]+qty}")
                else:
                    c.execute("INSERT INTO stock (category, item_name, size, color, gsm, unit, quantity, price, gst) VALUES (?,?,?,?,?,?,?,?,?)", (cat, name, size, color, gsm, unit, qty, price, gst))
                    st.success(f"'{name}' - {qty} {unit} ചേർത്തു.")
                conn.commit()
            else:
                st.error("പേര് കൊടുക്കുക!")
    elif choice == "🧾 ചെലവ് ചേർക്കുക":
        st.subheader("🧾 ഇന്നത്തെ ചെലവ്")
        reason = st.selectbox("എന്തിനാണ് ചെലവ്?", ["ചായ / ഭക്ഷണം", "പെട്രോൾ / ഡീസൽ", "ഓട്ടോ / ലോഡിംഗ്", "കട വാടക", "കറന്റ് ബിൽ", "സ്റ്റാഫ് ശമ്പളം", "സാധനം വാങ്ങിയത്", "മറ്റുള്ളവ"])
        custom = st.text_input("വേറെ എന്തെങ്കിലും ആണെങ്കിൽ എഴുതുക")
        final_reason = custom if custom else reason
        amount = st.number_input("എത്ര രൂപ?", min_value=1.0, value=100.0)
        pay_from = st.radio("എവിടെ നിന്ന് കൊടുത്തു?", ["Cash - പെട്ടിയിൽ നിന്ന്", "UPI - GPay-ൽ നിന്ന്"], horizontal=True)
        pay_short = "Cash" if "Cash" in pay_from else "UPI"
        if st.button("✅ ചെലവ് സേവ് ചെയ്യുക"):
            today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO expenses (reason, amount, date, user, payment_from) VALUES (?,?,?,?,?)", (final_reason, amount, today, st.session_state['username'], pay_short))
            conn.commit()
            st.success(f"ചെലവ് ₹{amount} സേവ് ആയി. Balance കുറഞ്ഞു.")
            st.rerun()
        st.divider()
        today_str = datetime.now().strftime("%Y-%m-%d")
        df_exp = pd.read_sql_query("SELECT reason as 'കാരണം', amount as 'തുക ₹', payment_from as 'എവിടെ നിന്ന്', user as 'എഴുതിയത്', date as 'സമയം' FROM expenses WHERE date LIKE ? ORDER BY date DESC", conn, params=(f"{today_str}%",))
        st.dataframe(df_exp, use_container_width=True)
    elif choice == "📈 റിപ്പോർട്ട്":
        st.subheader("📈 ഇന്നത്തെ ഫൈനൽ റിപ്പോർട്ട്")
        st.write(f"**Cash വിൽപ്പന:** ₹{cash:,.2f} | **GPay:** ₹{upi:,.2f} | **Card:** ₹{card:,.2f} | **കടം:** ₹{credit:,.2f}")
        st.write(f"**ആകെ വിൽപ്പന:** ₹{total_sale:,.2f} | **ആകെ ചെലവ്:** ₹{total_exp:
