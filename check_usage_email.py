import requests
import os
import smtplib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.mime.text import MIMEText

load_dotenv()

# === ENVIRONMENT VARIABLES ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your Gmail App Password
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# === USAGE FUNCTIONS ===
def get_usage():
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    end = datetime.utcnow().date()
    start = end - timedelta(days=30)
    url = f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start}&end_date={end}"
    res = requests.get(url, headers=headers)
    usage = res.json().get("total_usage", 0)
    return usage / 100  # convert cents to dollars

def get_subscription():
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    url = "https://api.openai.com/v1/dashboard/billing/subscription"
    res = requests.get(url, headers=headers)
    data = res.json()
    return data["hard_limit_usd"]

# === EMAIL FUNCTION ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

# === MAIN LOGIC ===
def main():
    try:
        used = get_usage()
        limit = get_subscription()
        pct = used / limit * 100

        status = f"✅ Usage is under control.\n\nUsed: ${used:.2f} / ${limit:.2f} ({pct:.1f}%)"
        if pct >= 90:
            status = f"🚨 CRITICAL: You’ve used {pct:.1f}% of your quota!"
        elif pct >= 70:
            status = f"⚠️ Warning: You’ve used {pct:.1f}% of your quota."

        send_email("OpenAI Usage Alert", status)
        print("✅ Email sent:", status)

    except Exception as e:
        send_email("OpenAI Monitor Error", f"❌ Error occurred:\n{e}")
        print("❌ Failed:", e)

if __name__ == "__main__":
    main()
