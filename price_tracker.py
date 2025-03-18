import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logging.basicConfig(level=logging.DEBUG)

# Function to check price using Selenium for dynamic content
def check_price(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service('K:\\amazon-price-tracker\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)

        # Wait for the price element to load
        price_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'a-price-whole'))
        )

        price_text = price_element.text.replace(',', '').strip()
        price = float(price_text)

        logging.info(f"Price found: ₹{price}")
        return price

    except Exception as e:
        logging.error(f"Error checking price: {str(e)}")
        raise

    finally:
        driver.quit()

# Function to send email (supports both Gmail and Outlook)
def send_email(to_email, subject, body):
    smtp_server = os.environ.get("SMTP_SERVER")  # smtp.gmail.com or smtp.office365.com
    port = os.environ.get("SMTP_PORT", 587)
    sender_email = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")

    if not smtp_server or not sender_email or not password:
        logging.error("Missing email configuration")
        raise ValueError("Email credentials not properly configured")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        logging.debug("Establishing SMTP connection...")
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(message)
        server.quit()

        logging.info(f"Email successfully sent to {to_email}")

    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP Authentication failed: {str(e)}")
        raise ValueError("Failed to authenticate with SMTP server. Check your credentials.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {str(e)}")
        raise

# Function to send welcome email
def send_welcome_email(to_email, product_url):
    subject = "Product Tracking Confirmation"
    body = f"""
    Thank you for using Amazon Price Tracker!

    We have successfully added the following product to our tracking system:
    {product_url}

    You will receive email notifications when the price changes.

    Best regards,
    Amazon Price Tracker Team
    """
    send_email(to_email, subject, body)

# Function to send price change alert
def send_price_alert(to_email, product_url, old_price, new_price, min_price=None, max_price=None):
    threshold_message = ""
    if min_price and new_price <= min_price:
        threshold_message = f"\nThe price has dropped below your minimum threshold of ₹{min_price:.2f}!"
    if max_price and new_price >= max_price:
        threshold_message = f"\nThe price has exceeded your maximum threshold of ₹{max_price:.2f}!"

    subject = "Amazon Price Alert!"
    body = f"""
    Price changed for your tracked product!

    Product URL: {product_url}
    Old Price: ₹{old_price:.2f}
    New Price: ₹{new_price:.2f}{threshold_message}

    Check it out now!
    """
    send_email(to_email, subject, body)
