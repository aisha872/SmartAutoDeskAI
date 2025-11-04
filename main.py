# SmartAutoDesk AI - Pro Edition
import streamlit as st
import imaplib, email, os, json
from datetime import datetime
from pathlib import Path
import pandas as pd
from transformers import pipeline

# ---------------------------------
# 🔒 PIN Lock
# ---------------------------------
APP_PIN = st.secrets.get("APP_PIN", "1234")
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 SmartAutoDesk AI Login")
    pin = st.text_input("Enter PIN to Unlock", type="password")
    if st.button("Unlock"):
        if pin == APP_PIN:
            st.session_state.auth = True
            st.success("✅ Access Granted!")
            st.experimental_rerun()
        else:
            st.error("❌ Wrong PIN!")
    st.stop()

# ---------------------------------
# 🌈 Page Settings
# ---------------------------------
st.set_page_config(page_title="SmartAutoDesk AI", page_icon="🤖", layout="wide")
st.markdown(
    """
    <style>
    .big-title { font-size:42px; font-weight:800; color:#00C6FF; text-align:center; }
    .subtitle { font-size:18px; text-align:center; color:#777; }
    .card {
        background-color:#f9f9ff;
        padding:20px;
        border-radius:20px;
        box-shadow:0 4px 10px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<p class='big-title'>📧 SmartAutoDesk AI — Pro Edition</p>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Your intelligent Gmail automation and analytics dashboard</p>", unsafe_allow_html=True)
st.divider()

# ---------------------------------
# 📩 Gmail Configuration
# ---------------------------------
GMAIL_EMAIL = st.secrets.get("GMAIL_EMAIL")
GMAIL_APP_PASS = st.secrets.get("GMAIL_APP_PASS")
if not GMAIL_EMAIL or not GMAIL_APP_PASS:
    st.error("⚠️ Gmail credentials missing in secrets.toml!")
    st.stop()

# ---------------------------------
# 🧠 AI Email Categorizer (Hugging Face)
# ---------------------------------
st.sidebar.header("🧠 AI Settings")
st.sidebar.info("Smart email categorization enabled using Hugging Face.")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
CATEGORIES = ["Work", "Finance", "Promotions", "Personal", "Urgent", "Education", "Newsletter"]

def categorize_email(subject, body):
    text = (subject or "") + " " + (body or "")[:300]
    result = classifier(text, CATEGORIES)
    return result["labels"][0]

# ---------------------------------
# 📬 Fetch Emails (Unread)
# ---------------------------------
def read_unread_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_EMAIL, GMAIL_APP_PASS)
        mail.select("inbox")
        result, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()
        messages = []

        for mail_id in mail_ids:
            result, msg_data = mail.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = msg.get("subject", "(No Subject)")
            sender = msg.get("from", "(Unknown Sender)")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode(errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            category = categorize_email(subject, body)
            messages.append({
                "sender": sender,
                "subject": subject,
                "body": body[:300],
                "category": category,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        mail.logout()
        return messages
    except Exception as e:
        st.error(f"📧 Error reading emails: {e}")
        return []

# ---------------------------------
# 📊 Display & Analytics
# ---------------------------------
st.sidebar.subheader("📊 Dashboard Options")
show_summary = st.sidebar.checkbox("Show Email Summary Table", value=True)
show_chart = st.sidebar.checkbox("Show Category Distribution", value=True)

if st.button("🔍 Fetch & Categorize Emails"):
    with st.spinner("Reading & Categorizing emails..."):
        emails = read_unread_emails()
        if not emails:
            st.warning("No unread emails found!")
        else:
            st.success(f"✅ {len(emails)} new emails categorized!")
            df = pd.DataFrame(emails)

            if show_summary:
                st.markdown("### 📋 Email Summary")
                st.dataframe(df[["timestamp", "sender", "subject", "category"]])

            if show_chart:
                st.markdown("### 📈 Category Distribution")
                cat_chart = df["category"].value_counts()
                st.bar_chart(cat_chart)

            with st.expander("📥 View Full Email Details"):
                for e in emails:
                    st.markdown(
                        f"""
                        <div class="card">
                        <b>📩 From:</b> {e['sender']}<br>
                        <b>🧾 Subject:</b> {e['subject']}<br>
                        <b>🏷 Category:</b> <span style='color:#008CFF'>{e['category']}</span><br>
                        <b>🕒 Time:</b> {e['timestamp']}<br><br>
                        <b>📄 Preview:</b><br>{e['body']}
                        </div><br>
                        """,
                        unsafe_allow_html=True
                    )
