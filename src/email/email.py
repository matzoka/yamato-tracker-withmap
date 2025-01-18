import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.getenv('GMAIL_USER')
EMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')

def send_email(subject, body, to_email=None):
    """Send email notification"""
    if to_email is None:
        if NOTIFICATION_EMAIL is None:
            raise ValueError("通知先メールアドレスが設定されていません。.envファイルにNOTIFICATION_EMAILを設定してください")
        to_email = NOTIFICATION_EMAIL

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        st.success("メールが送信されました")
    except Exception as e:
        st.error(f"メール送信エラー: {e}")
        st.info("""
        メールが送信できない場合、以下の設定を確認してください：
        1. Gmailの設定で「低セキュリティなアプリのアクセス」を有効にする
        2. .envファイルのGMAIL_PASSWORDが正しいアプリパスワードか確認する
        3. メールがスパムフォルダに入っていないか確認する
        """)
