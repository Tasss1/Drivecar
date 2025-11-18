import pickle
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_service():
    # Загружаем pickle токен
    with open('token.pickle', 'rb') as token_file:
        creds = pickle.load(token_file)
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_email(to, subject, body):
    service = get_service()
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    service.users().messages().send(userId='me', body=body).execute()
