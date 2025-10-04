import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

def send_api_expiry_alert(subject, body, to_email):
    # You may want to store these in your Django settings securely
    gmail_user = getattr(settings, 'ALERT_GMAIL_USER', None)
    gmail_password = getattr(settings, 'ALERT_GMAIL_PASSWORD', None)
    if not gmail_user or not gmail_password:
        print('Gmail credentials not set in settings.')
        return False
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        text = msg.as_string()
        server.sendmail(gmail_user, to_email, text)
        server.quit()
        print('Alert email sent successfully!')
        return True
    except Exception as e:
        print(f'Failed to send alert email: {e}')
        return False
