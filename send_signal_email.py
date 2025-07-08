import os
import logging
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SIGNAL_API_URL = os.getenv("SIGNAL_API_URL")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

def fetch_signals():
    try:
        response = requests.get(SIGNAL_API_URL)
        if response.status_code == 200:
            return response.json().get("signals", [])
        else:
            print(f"❌ Failed to fetch signals: {response.status_code}")
            logging.error(f"Failed to fetch signals: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Failed to fetch signals: {e}")
        logging.error(f"Failed to fetch signals: {e}")
        return []

def format_email_body(signals):
    if not signals:
        return (
            "📭 No trading signals were generated today.\n\n"
            "The AI model analyzed the latest commodity news, but found no high-confidence "
            "opportunities to report at this time.\n\n"
            "Stay tuned — fresh signals are generated daily based on live news and price movements!"
        )
    
    body = "📈 Daily Commodity Signals:\n\n"
    for sig in signals:
        body += (
            f"• {sig.get('commodity', '').capitalize()} - {sig.get('trend')} trend\n"
            f"  Confidence: {sig.get('confidence')}%\n"
            f"  Entry: {sig.get('entry')}, Exit: {sig.get('exit')}, Stop: {sig.get('stop_loss')}\n"
            f"  Reason: {sig.get('reason')}\n"
            f"  7d Change: {sig.get('change_pct')}\n\n"
        )
    return body

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully.")
        logging.info("Email sent successfully.")
    except Exception as e:
        error_msg = f"❌ Failed to send email: {e}"
        print(error_msg)
        logging.error(error_msg)

# Setup logging
logging.basicConfig(
    filename="email_report.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Main routine
if __name__ == "__main__":
    print("🚀 Fetching signals...")
    signals = fetch_signals()
    email_body = format_email_body(signals)
    subject = "📊 Daily Commodity Signal Report"
    send_email(subject, email_body)
