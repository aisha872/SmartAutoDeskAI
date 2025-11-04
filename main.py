# SmartAutoDesk AI - cloud-safe final main.py
import streamlit as st
import imaplib
import email
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader

# ---------------------------------
# Safe import for pywhatkit (WhatsApp)
# ---------------------------------
try:
    if not os.environ.get("STREAMLIT_CLOUD"):
        import pywhatkit
    else:
        pywhatkit = None
except Exception:
    pywhatkit = None

# ---------------------------------
# PIN Lock
# ---------------------------------
APP_PIN = st.secrets.get("APP_PIN", "1234")
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pin = st.text_input("Enter PIN to unlock SmartAutoDesk AI", type="password")
    if st.button("Unlock"):
        if pin == APP_PIN:
            st.session_state.auth = True
            st.experimental_rerun()
        else:
            st.error("❌ Wrong PIN!")
    st.stop()

# ---------------------------------
# Gmail Configuration (use your App Password via secrets)
# ---------------------------------
accounts = [
    {
        "email": st.secrets.get("GMAIL_EMAIL", "your_email@gmail.com"),
        "app_password": st.secrets.get("GMAIL_APP_PASS", "")
    }
]

notify_number = st.secrets.get("NOTIFY_NUMBER", "+923001234567")
log_file = "email_log.json"
attachment_folder = Path("Attachments")
attachment_folder.mkdir(exist_ok=True)

if not os.path.exists(log_file):
    with open(log_file, "w") as f:
        json.dump([], f)

def load_log():
    with open(log_file, "r") as f:
        return json.load(f)

def save_log(log):
    with open(log_file, "w") as f:
        json.dump(log, f, indent=2)

# ---------------------------------
# AI Reply Generator (simple placeholder)
# ---------------------------------
def ai_generate_reply(email_body, sender, subject):
    snippet = (email_body or "")[:120].replace("\n", " ")
    summary = snippet if len(snippet) < 140 else snippet[:137] + "..."
    return f"Reply to {sender} about '{subject}': AI suggests -> '{summary}'"

# ---------------------------------
# Read Unread Emails
# ---------------------------------
def read_unread_emails(account_email, account_password):
    messages = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(account_email, account_password)
        mail.select("inbox")
        result, data = mail.search(None, 'UNSEEN')
        mail_ids = data[0].split() if data and data[0] else []

        for mail_id in mail_ids:
            result, msg_data = mail.fetch(mail_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = msg.get("subject", "(no subject)")
            sender = msg.get("from", "(no sender)")
            body = ""
            attachments = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_dispo = str(part.get("Content-Disposition") or "")
                    ctype = part.get_content_type()
                    if ctype == "text/plain" and "attachment" not in content_dispo:
                        try:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            body = str(part.get_payload(decode=True))
                    elif "attachment" in content_dispo:
                        filename = part.get_filename()
                        if filename:
                            data = part.get_payload(decode=True)
                            file_path = attachment_folder / filename
                            with open(file_path, "wb") as f:
                                f.write(data)
                            attachments.append(str(file_path))
            else:
                try:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                except Exception:
                    body = str(msg.get_payload())

            messages.append({
                "subject": subject,
                "sender": sender,
                "body": body,
                "attachments": attachments
            })
        mail.logout()
    except Exception as e:
        st.error(f"📧 Email error for {account_email}: {e}")
    return messages

# ---------------------------------
# WhatsApp Notification (Safe)
# ---------------------------------
def notify_user(reply_text):
    if not pywhatkit:
        st.info("📱 WhatsApp notifications disabled (cloud-safe mode)")
        return
    try:
        pywhatkit.sendwhatmsg_instantly(notify_number, reply_text)
        st.success(f"✅ Notification sent to {notify_number}")
    except Exception as e:
        st.error(f"⚠️ WhatsApp error: {e}")

# ---------------------------------
# Streamlit App Interface
# ---------------------------------
st.set_page_config(page_title="SmartAutoDesk AI", page_icon="📧")
st.title("📧🤖 SmartAutoDesk AI - Automation Hub")

log = load_log()
initial_count = len(log)

if st.button("Check & Process Emails"):
    new_count = 0
    for account in accounts:
        if not account.get("email") or not account.get("app_password"):
            st.warning("Gmail credentials not set in secrets. Please add GMAIL_EMAIL and GMAIL_APP_PASS.")
            continue

        emails = read_unread_emails(account["email"], account["app_password"])
        if not emails:
            st.info(f"No unread emails in {account['email']}")
        for e in emails:
            if any(item["subject"] == e["subject"] and item["sender"] == e["sender"] for item in log):
                continue
            reply = ai_generate_reply(e["body"], e["sender"], e["subject"])
            notify_user(reply)
            log.append({
                "timestamp": datetime.now().isoformat(),
                "sender": e["sender"],
                "subject": e["subject"],
                "reply": reply,
                "attachments": e["attachments"]
            })
            st.write(f"✅ Processed: {e['sender']} | {e['subject']} | Attachments: {len(e['attachments'])}")
            new_count += 1
    save_log(log)
    st.success(f"📨 All emails processed! New: {new_count}")

# ---------------------------------
# Stats and Charts
# ---------------------------------
st.subheader("📊 Email Processing Stats")
st.write(f"Total processed: {len(log)}")
st.write(f"Previously processed (before current run): {initial_count}")

if log:
    df = pd.DataFrame(log)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    st.subheader("📈 Emails Over Time")
    try:
        emails_over_time = df.groupby(df['timestamp'].dt.date).size()
        st.line_chart(emails_over_time)
    except Exception:
        st.info("Not enough data for time-series chart yet.")

    st.subheader("📎 Attachments Count")
    all_attachments = []
    for sub in df['attachments'].dropna():
        if isinstance(sub, list):
            all_attachments.extend(sub)
    all_paths = [Path(a) for a in all_attachments]
    extensions = [p.suffix.lower() for p in all_paths if p.exists()]
    if extensions:
        ext_count = pd.Series(extensions).value_counts()
        st.bar_chart(ext_count)
    else:
        st.info("No attachments found.")

    st.subheader("👥 Top Senders")
    try:
        st.bar_chart(df['sender'].value_counts())
    except Exception:
        st.info("Not enough sender data to show chart.")
else:
    st.info("No data yet. Click 'Check & Process Emails' first.")
