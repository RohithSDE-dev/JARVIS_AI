import smtplib
import ollama
from email.message import EmailMessage
from pymongo import MongoClient
from thefuzz import process

class CommEngine:
    def __init__(self, mongo_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client['jarvis_memory']
        self.contacts = self.db['contacts']
        
        # Email Config
        self.email_user = "example@gmail.com"
        self.email_pass = "password"

    def save_contact(self, name, email):
        """Standardizes and saves contact to MongoDB."""
        clean_name = name.strip().lower()
        self.contacts.update_one(
            {"name": clean_name},
            {"$set": {"name": clean_name, "email": email.strip()}},
            upsert=True
        )
        return f"Database updated: {name} linked to {email}."

    def get_contact_by_name(self, name):
        """Fuzzy search to find contacts even with slight misspellings."""
        all_contacts = list(self.contacts.find({}, {"name": 1, "email": 1}))
        if not all_contacts:
            return None
        
        names = [c['name'] for c in all_contacts]
        # match[0] is the string, match[1] is the score
        match = process.extractOne(name.lower().strip(), names)
        
        if match and match[1] > 75: # Slightly higher threshold for accuracy
            return self.contacts.find_one({"name": match[0]})
        return None

    def generate_refined_body(self, recipient_name, subject, hints):
        """Uses Ollama to turn rough notes into a tactical, professional draft."""
        prompt = (f"Recipient: {recipient_name}\n"
                  f"Subject: {subject}\n"
                  f"Notes: {hints}\n\n"
                  "Task: Convert notes into a professional, concise email. "
                  "Include a formal greeting and sign as 'Rohith K'. "
                  "Output ONLY the email body.")
        try:
            response = ollama.chat(model='qwen2.5:7b', messages=[
                {'role': 'system', 'content': 'You are JARVIS, a professional tactical assistant.'},
                {'role': 'user', 'content': prompt}
            ])
            return response['message']['content'].strip()
        except Exception:
            return f"Dear {recipient_name},\n\nRegarding {subject}: {hints}\n\nBest regards,\nRohith K"

    def send_email(self, recipient_email, recipient_name, subject, hints=None):
        """Refines content and transmits via SMTP_SSL."""
        final_body = self.generate_refined_body(recipient_name, subject, hints or "General inquiry.")
        
        msg = EmailMessage()
        msg.set_content(final_body)
        msg['Subject'] = subject
        msg['From'] = self.email_user
        msg['To'] = recipient_email

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.email_user, self.email_pass)
                smtp.send_message(msg)
            return f"Transmission to {recipient_name} successful."
        except Exception as e:
            return f"Communication breach: {str(e)}"
