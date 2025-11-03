# main.py
import streamlit as st
import pywhatkit
import imaplib
import email
from datetime import datetime
import time

# -------------------------------
# AI reply placeholder function
# -------------------------------
def ai_generate_reply(message):
    """
    Replace this with your local AI model (GPT4All / Llama)
    For now it returns a simple reply.
    """
    if "invoice" in message.lower():
        return "Got your invoice, processing now."
    elif "report" in message.lower():
        return "Report received. I will review it shortly."
    else:
        return "Thank you for your message!"

# -------------------------------
# Email automation function
# -------------------------------
def read_unread_emails():
    EMAIL_USER = st.secrets.get("EMAIL_USER", "youremail@gmail.com")
    EMAIL_PASS = st.secrets.get("EMAIL_PASS", "your_app_password")
    messages = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
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
            if msg.is_multipart():
                for part in msg.get_payload():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()
            messages.append({
                "subject": subject,
                "sender": sender,
                "body": body
            })
        mail.logout()
    except Exception as e:
        st.error(f"Email error: {e}")
    return messages

# -------------------------------
# WhatsApp send function
# -------------------------------
def send_whatsapp_message(number, message):
    try:
        pywhatkit.sendwhatmsg_instantly(number, message)
        st.success(f"Message sent to {number}")
    except Exception as e:
        st.error(f"WhatsApp error: {e}")

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📧💬 SmartAutoDesk AI (Starter)")

st.subheader("Email Automation")
if st.button("Check & Process Unread Emails"):
    emails = read_unread_emails()
    if not emails:
        st.info("No unread emails found.")
    else:
        for e in emails:
            st.write(f"📧 From: {e['sender']}")
            st.write(f"Subject: {e['subject']}")
            st.write(f"Body: {e['body']}")
            reply = ai_generate_reply(e["body"])
            st.write(f"🤖 AI Reply: {reply}")
            # Example: send AI reply via WhatsApp
            send_whatsapp_message("+923001234567", reply)  # Replace with your number

st.subheader("WhatsApp Automation")
msg_number = st.text_input("Recipient Number (+countrycode):")
msg_text = st.text_area("Message Text:")
if st.button("Send WhatsApp Message"):
    if msg_number and msg_text:
        send_whatsapp_message(msg_number, msg_text)
    else:
        st.warning("Please enter both number and message.")
