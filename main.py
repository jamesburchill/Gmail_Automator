#  Copyright (c) 2025 - JamesBurchill.com - See LICENSE for details, otherwise All Rights Reserved
#  File Location: /Users/jamesburchill/Documents/DEV/Gmail_Automator/main.py
#  Last Updated: 3/14/25, 5:33 PM

import csv
import logging
import os
import random
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from email_template import EMAIL_SUBJECT, EMAIL_BODY

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_FILE = os.path.join(DATA_DIR, "email_log.txt")
SENT_EMAILS_FILE = os.path.join(DATA_DIR, "sent_emails.txt")

# Clean the log file before each run
with open(LOG_FILE, 'w'):
    pass

# Set up logging to file and console
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not all([SMTP_SERVER, SMTP_PORT, EMAIL_ACCOUNT, EMAIL_PASSWORD]):
    raise ValueError("SMTP configuration is incomplete. Please check your environment variables.")

CSV_FILE = os.path.join(DATA_DIR, "email-list.csv")

if not all([EMAIL_SUBJECT, EMAIL_BODY]):
    raise ValueError("Email subject and body must be provided in the environment variables.")

EMAIL_INTERVAL = random.randint(240, 360)
RANDOMIZE_DELAY = True
RETRY_COUNT = 3


def send_email(to_email):
    attempt = 0
    while attempt < RETRY_COUNT:
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ACCOUNT
            msg["To"] = to_email
            msg["Subject"] = EMAIL_SUBJECT
            msg.attach(MIMEText(EMAIL_BODY, "plain"))

            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ACCOUNT, to_email, msg.as_string())

            logging.info(f"✅ Email sent to: {to_email}")
            return True
        except Exception as e:
            attempt += 1
            logging.error(f"❌ Attempt {attempt}: Error sending email to {to_email}: {e}")
            if attempt < RETRY_COUNT:
                time.sleep(5)
            else:
                logging.error(f"❌ Failed to send email to {to_email} after {RETRY_COUNT} attempts.")
                return False


def read_emails_from_csv(csv_file):
    emails = []
    try:
        with open(csv_file, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0]:
                    emails.append(row[0].strip())
    except Exception as e:
        logging.error(f"❌ Error reading CSV file: {e}")
    return emails


def read_sent_emails(sent_emails_file):
    sent_emails = set()
    if os.path.exists(sent_emails_file):
        with open(sent_emails_file, "r", encoding="utf-8") as file:
            for line in file:
                sent_emails.add(line.strip())
    return sent_emails


def write_sent_email(sent_emails_file, email):
    with open(sent_emails_file, "a", encoding="utf-8") as file:
        file.write(email + "\n")


if __name__ == "__main__":
    reset_sent_emails = input("Do you want to reset the sent emails list? (yes/no): ").strip().lower()
    if reset_sent_emails == 'yes':
        with open(SENT_EMAILS_FILE, 'w'):
            pass
        logging.info("✅ Sent emails list has been reset.")

    email_list = read_emails_from_csv(CSV_FILE)
    sent_emails = read_sent_emails(SENT_EMAILS_FILE)

    if not email_list:
        logging.error("❌ No email addresses found in the CSV file.")
    else:
        logging.info(f"📨 {len(email_list)} emails found. Starting email dispatch...")

        for email in email_list:
            if email in sent_emails:
                logging.info(f"⏩ Skipping already sent email: {email}")
                continue

            if send_email(email):
                write_sent_email(SENT_EMAILS_FILE, email)
                delay = EMAIL_INTERVAL
                if RANDOMIZE_DELAY:
                    delay += random.randint(-30, 30)
                logging.info(f"⏳ Waiting {delay // 60} minutes before sending the next email...")
                time.sleep(delay)
