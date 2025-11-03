# main.py
import streamlit as st
import pywhatkit
import imaplib
import email
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from PyPDF2 import PdfReader

# -------------------------------
# PIN LOCK
# -------------------------------
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
            st.error("Wrong PIN!")
    st.stop()

# -------------------------------
# Configuration
# -------------------------------
accounts = [
    {"email": "youraccount@gmail.com", "app_password": "your_app_password"}
]
notify_number = "+923001234567"
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

# -------------------------------
# Dynamic AI Reply (simple)
# -------------------------------
def ai_generate_reply(email_body, sender, subject):
    snippet = email_body[:50].replace("\n", " ")
    summary = snippet if len(snippet) < 100 else snippet[:97]+"..."
    return f"Reply to {sender} about '{subject}': AI suggests -> '{summary}'"

# -------------------------------
# Read Unread Emails
# -------------------------------
def read_unread_emails(account_email, account_password):
    messages = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(account_email, account_password)
        mail.select("inbox")
        result, data = mail.search(None, 'UNSEEN')
        mail_ids = data[0].split()
        for mail_id in mail_ids:
            result, msg_data = mail.fetch(mail_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = msg["subject"]
            sender = msg["from"]
            body = ""
            attachments = []
            if msg.is_multipart():
                for part in msg.get_payload():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                    elif part.get('Content-Disposition'):
                        filename = part.get_filename()
                        if filename:
                            data = part.get_payload(decode=True)
                            file_path = attachment_folder / filename
                            with open(file_path, "wb") as f:
                                f.write(data)
                            attachments.append(str(file_path))
            else:
                body = msg.get_payload(decode=True).decode()
            messages.append({
                "subject": subject,
                "sender": sender,
                "body": body,
                "attachments": attachments
            })
        mail.logout()
    except Exception as e:
        st.error(f"Email error for {account_email}: {e}")
    return messages

# -------------------------------
# WhatsApp Notification
# -------------------------------
def notify_user(reply_text):
    try:
        pywhatkit.sendwhatmsg_instantly(notify_number, reply_text)
        st.success(f"Notification sent to {notify_number}")
    except Exception as e:
        st.error(f"WhatsApp error: {e}")

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📧💬 SmartAutoDesk AI - Multi-Sender Email & Automation Hub")

log = load_log()
total_processed = len(log)

if st.button("Check & Process All Emails"):
    new_count = 0
    for account in accounts:
        emails = read_unread_emails(account["email"], account["app_password"])
        if not emails:
            st.info(f"No unread emails in {account['email']}")
        for e in emails:
            already_done = any(log_item["subject"] == e["subject"] and log_item["sender"] == e["sender"] for log_item in log)
            if already_done:
                continue

            reply = ai_generate_reply(e["body"], e["sender"], e["subject"])
            notify_user(reply)

            log.append({
                "timestamp": str(datetime.now()),
                "sender": e["sender"],
                "subject": e["subject"],
                "reply": reply,
                "attachments": e["attachments"]
            })
            st.write(f"✅ Processed: {e['sender']} | {e['subject']} | Attachments: {len(e['attachments'])}")
            new_count += 1
    save_log(log)
    st.success(f"All emails processed! New emails handled: {new_count}")

# -------------------------------
# Stats & Last 5 processed emails
# -------------------------------
st.subheader("📊 Stats")
st.write(f"Total processed emails: {total_processed}")
st.write(f"Newly processed emails: {len(log) - total_processed}")
st.write(f"Total attachments downloaded: {sum(len(e['attachments']) for e in log)}")

st.subheader("📝 Last 5 AI replies")
if log:
    for entry in log[-5:]:
        with st.expander(f"{entry['timestamp']} | {entry['sender']} | {entry['subject']}"):
            st.write(f"💡 AI Reply: {entry['reply']}")
            if entry['attachments']:
                st.write(f"📎 Attachments: {', '.join(entry['attachments'])}")
else:
    st.info("No emails processed yet.")

# -------------------------------
# Daily summary (last 24h)
# -------------------------------
if st.button("Show 24h AI Summary"):
    st.subheader("📅 Last 24h AI replies")
    last24 = []
    for entry in log:
        ts = datetime.fromisoformat(entry["timestamp"])
        if ts >= datetime.now() - timedelta(days=1):
            last24.append(entry)
    if last24:
        for e in last24:
            with st.expander(f"{e['timestamp']} | {e['sender']} | {e['subject']}"):
                st.write(f"💡 AI Reply: {e['reply']}")
                if e['attachments']:
                    st.write(f"📎 Attachments: {', '.join(e['attachments'])}")
    else:
        st.info("No emails processed in the last 24h.")

# -------------------------------
# Follow-up Reminder
# -------------------------------
st.subheader("⏰ Follow-up Reminder (Emails >2 days old)")
old_emails = [e for e in log if datetime.fromisoformat(e["timestamp"]) < datetime.now() - timedelta(days=2)]
if old_emails:
    for e in old_emails:
        st.warning(f"{e['timestamp']} | {e['sender']} | {e['subject']} - Follow-up needed")
else:
    st.info("No follow-ups needed.")
