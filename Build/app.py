from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from amazon_scraper import get_product_details
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=True)

def send_email(email, subject, message):
    # Configure your SMTP server and login details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "your-email@gmail.com"
    smtp_password = "your-password"

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, email, text)
        logger.debug(f"Email sent to {email} with subject: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
    finally:
        server.quit()

def price_tracker(app):
    with app.app_context():
        while True:
            products = Product.query.all()
            for product in products:
                try:
                    details = get_product_details(product.url)
                    logger.debug(f"Tracked product {details['name']} with new price: {details['price']}")
                    if details['price'] != product.price:
                        product.price = details['price']
                        db.session.commit()
                        send_email(product.email, "Price Alert!", f"Price of {product.name} has changed to {product.price}")
                except Exception as e:
                    logger.error(f"Error tracking price for {product.url}: {e}")
            time.sleep(3600)  # Check every hour

tracker_started = False

@app.before_request
def activate_job():
    global tracker_started
    if not tracker_started:
        thread = threading.Thread(target=price_tracker, args=(app,))
        thread.start()
        tracker_started = True
        logger.debug("Price tracker thread started")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    url = request.form['url']
    email = request.form['email']
    logger.debug(f"Received URL: {url} and email: {email}")
    try:
        details = get_product_details(url)
    except ValueError as e:
        logger.error(f"Error getting product details: {e}")
        flash(str(e), 'danger')
        return redirect(url_for('index'))
    
    new_product = Product(url=url, email=email, name=details['name'], price=details['price'])
    db.session.add(new_product)
    db.session.commit()
    logger.debug(f"Added product: {details['name']} with price: {details['price']}")
    flash(f'Successfully added {details["name"]} to tracking list.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)