import streamlit as st
import imaplib, email, os, json, random, smtplib
from email.mime.text import MIMEText
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ==========================
# 🎯 CONFIGURATION
# ==========================
st.set_page_config(page_title="SmartAutoDesk AI", page_icon="🤖", layout="wide")

GMAIL_EMAIL = st.secrets["GMAIL_EMAIL"]
GMAIL_APP_PASS = st.secrets["GMAIL_APP_PASS"]
DEFAULT_PIN = st.secrets["APP_PIN"]

PIN_FILE = "pin_data.json"
OTP_FILE = "otp_data.json"

# ==========================
# 🌈 Glass Effect Styling
# ==========================
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }
    div[data-testid="stHeader"] {background: rgba(255,255,255,0);}
    .glass-box {
        background: rgba(255,255,255,0.1);
        padding: 25px;
        border-radius: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 30px rgba(0,0,0,0.3);
    }
    input, textarea {
        background: rgba(255,255,255,0.15)!important;
        color: white!important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 🔐 PIN Handling
# ==========================
if not os.path.exists(PIN_FILE):
    with open(PIN_FILE, "w") as f:
        json.dump({"pin": DEFAULT_PIN}, f)

with open(PIN_FILE, "r") as f:
    saved_pin = json.load(f).get("pin", DEFAULT_PIN)

# ==========================
# ✉️ Forgot PIN (OTP System)
# ==========================
def send_otp_email(to_email, otp):
    msg = MIMEText(f"Your SmartAutoDesk AI OTP is: {otp}")
    msg["Subject"] = "🔐 SmartAutoDesk AI - OTP Verification"
    msg["From"] = GMAIL_EMAIL
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_EMAIL, GMAIL_APP_PASS)
        server.send_message(msg)

# ==========================
# 🚪 Login Section
# ==========================
st.title("📧🤖 SmartAutoDesk AI - Automation Hub")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.container():
        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.subheader("🔑 Secure Login")
        entered_pin = st.text_input("Enter PIN", type="password")
        col1, col2 = st.columns(2)
        if col1.button("Login"):
            if entered_pin == saved_pin:
                st.session_state.authenticated = True
                st.success("✅ Access granted!")
            else:
                st.error("❌ Incorrect PIN.")
        if col2.button("Forgot PIN?"):
            otp = str(random.randint(100000, 999999))
            with open(OTP_FILE, "w") as f:
                json.dump({"otp": otp, "timestamp": datetime.now().isoformat()}, f)
            send_otp_email(GMAIL_EMAIL, otp)
            st.info("📩 OTP sent to your Gmail. Please check your inbox.")

        st.markdown('</div>', unsafe_allow_html=True)
else:
    # ==========================
    # 📊 Main Dashboard
    # ==========================
    st.markdown('<div class="glass-box">', unsafe_allow_html=True)
    st.success(f"Welcome, {GMAIL_EMAIL} 👋")

    st.subheader("📨 Email Processing Dashboard")

    total_emails = random.randint(50, 80)
    processed_today = random.randint(5, 10)
    st.metric("Total Emails Processed", total_emails)
    st.metric("Processed Today", processed_today)

    data = pd.DataFrame({
        "Date": pd.date_range(datetime.now() - timedelta(days=6), periods=7),
        "Emails": [random.randint(5, 20) for _ in range(7)]
    })
    st.line_chart(data, x="Date", y="Emails")

    st.markdown('</div>', unsafe_allow_html=True)

    # ==========================
    # 🧮 Change PIN
    # ==========================
    st.markdown('<div class="glass-box">', unsafe_allow_html=True)
    st.subheader("🔐 Change PIN")

    with st.expander("Customize Access PIN"):
        current_pin = st.text_input("Enter Current PIN", type="password")
        new_pin = st.text_input("Enter New PIN", type="password")
        confirm_pin = st.text_input("Confirm New PIN", type="password")

        if st.button("Update PIN"):
            if current_pin != saved_pin:
                st.error("❌ Current PIN incorrect.")
            elif new_pin != confirm_pin:
                st.warning("⚠️ New PINs do not match.")
            elif len(new_pin) < 4:
                st.warning("⚠️ PIN must be at least 4 digits.")
            else:
                with open(PIN_FILE, "w") as f:
                    json.dump({"pin": new_pin}, f)
                st.success("✅ PIN updated successfully! Reload app to apply.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ==========================
    # 🧾 Verify OTP to Reset PIN
    # ==========================
    if os.path.exists(OTP_FILE):
        with open(OTP_FILE, "r") as f:
            otp_data = json.load(f)

        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.subheader("🔁 Reset PIN using OTP")
        entered_otp = st.text_input("Enter OTP from email", type="password")
        new_pin_reset = st.text_input("New PIN", type="password")

        if st.button("Verify & Reset PIN"):
            if entered_otp == otp_data.get("otp"):
                with open(PIN_FILE, "w") as f:
                    json.dump({"pin": new_pin_reset}, f)
                os.remove(OTP_FILE)
                st.success("✅ PIN reset successfully! Please log in again.")
                st.session_state.authenticated = False
            else:
                st.error("❌ Invalid OTP.")
        st.markdown('</div>', unsafe_allow_html=True)
