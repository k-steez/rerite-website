from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rerite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Database model
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_subscribed = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)

# Create database tables
with app.app_context():
    db.create_all()

def verify_recaptcha(token):
    """Verify reCAPTCHA token"""
    secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': secret_key,
            'response': token
        }
    )
    return response.json()['success']

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    
    # Verify reCAPTCHA
    if not verify_recaptcha(data.get('recaptcha_token')):
        return jsonify({'error': 'Invalid reCAPTCHA'}), 400
    
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Check if email already exists
    if Subscriber.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already subscribed'}), 400
    
    # Create new subscriber
    subscriber = Subscriber(email=email)
    db.session.add(subscriber)
    db.session.commit()
    
    # Send welcome email
    try:
        msg = Message(
            'Welcome to ReRite UG!',
            recipients=[email]
        )
        msg.body = f'''Welcome to ReRite UG!

Thank you for your interest in joining our intellectual community. We're excited to have you on board!

Best regards,
The ReRite UG Team'''
        mail.send(msg)
        
        # Send notification to admin
        admin_msg = Message(
            'New ReRite UG Subscriber',
            recipients=[os.getenv('ADMIN_EMAIL')]
        )
        admin_msg.body = f'New subscriber: {email}'
        mail.send(admin_msg)
        
    except Exception as e:
        print(f"Error sending email: {e}")
        # Continue even if email fails
    
    return jsonify({'message': 'Successfully subscribed!'}), 200

if __name__ == '__main__':
    app.run(debug=True) 