import os
import imaplib
import email
from email.policy import default
import re
from typing import Any, List
from core.ports.input_adapter import IInputAdapter

class EmailAdapter(IInputAdapter):
    def process(self, raw_data: Any = None) -> List[str]:
        # raw_data is ignored, we pull from env vars
        username = os.getenv("IMAP_USERNAME")
        password = os.getenv("IMAP_PASSWORD")
        server = os.getenv("IMAP_SERVER")
        folder = os.getenv("IMAP_FOLDER", "INBOX")

        if not all([username, password, server]):
            raise ValueError("IMAP credentials (IMAP_USERNAME, IMAP_PASSWORD, IMAP_SERVER) are missing from environment variables.")

        extracted_payloads = []
        try:
            mail = imaplib.IMAP4_SSL(server)
            mail.login(username, password)
            mail.select(folder)

            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                mail.logout()
                return []

            email_ids = messages[0].split()
            for eid in email_ids:
                res, msg_data = mail.fetch(eid, '(RFC822)')
                if res != 'OK':
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1], policy=default)
                        
                        # Extract plain text body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    body = part.get_payload(decode=True)
                                    if isinstance(body, bytes):
                                        body = body.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                                    break
                        else:
                            if msg.get_content_type() == "text/plain":
                                body = msg.get_payload(decode=True)
                                if isinstance(body, bytes):
                                    body = body.decode(msg.get_content_charset() or 'utf-8', errors='ignore')

                        if not body:
                            # Fallback if only HTML is present (strip tags roughly)
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/html":
                                        html = part.get_payload(decode=True)
                                        if isinstance(html, bytes):
                                            html = html.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                                        body = re.sub(r'<[^>]+>', ' ', html)
                                        break
                            elif msg.get_content_type() == "text/html":
                                html = msg.get_payload(decode=True)
                                if isinstance(html, bytes):
                                    html = html.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
                                body = re.sub(r'<[^>]+>', ' ', html)

                        if body:
                            extracted_payloads.append(body.strip())
                            
            mail.logout()
        except Exception as e:
            raise ValueError(f"Email sync failed: {e}")

        return extracted_payloads
