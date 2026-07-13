import os
import imaplib
import email
from email.policy import default
import re
from typing import Any, List
from core.ports.input_adapter import IInputAdapter, RawPayload

class EmailAdapter(IInputAdapter):
    def collect(self, **kwargs) -> List[RawPayload]:
        username = os.getenv("IMAP_USERNAME")
        password = os.getenv("IMAP_PASSWORD")
        server = os.getenv("IMAP_SERVER")
        port = int(os.getenv("IMAP_PORT", "993"))
        folder = os.getenv("IMAP_FOLDER", "INBOX")

        if not all([username, password, server]):
            raise ValueError("IMAP credentials (IMAP_USERNAME, IMAP_PASSWORD, IMAP_SERVER) are missing from environment variables.")

        subject_filter = kwargs.get("subject_filter")

        # Always default to UNSEEN to prevent downloading the entire mailbox.
        search_criteria = ['UNSEEN']
        if subject_filter:
            search_criteria.extend(['SUBJECT', f'"{subject_filter}"'])

        extracted_payloads = []
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            mail.select(folder)

            # Search emails
            search_args = ' '.join(search_criteria)
            status, messages = mail.uid('SEARCH', None, search_args)
            if status != 'OK' or not messages[0]:
                return []

            email_ids = messages[0].split()
            for eid in email_ids:
                res, msg_data = mail.uid('FETCH', eid, '(RFC822)')
                if res != 'OK':
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1], policy=default)
                        
                        message_id = msg.get("Message-ID", f"unknown_{eid.decode('utf-8')}")
                        message_id = message_id.strip("<>")
                        sender = str(msg.get("From", ""))
                        subject = str(msg.get("Subject", ""))
                        date = str(msg.get("Date", ""))
                        
                        metadata = {
                            "message_id": message_id,
                            "imap_uid": eid.decode('utf-8'),
                            "sender": sender,
                            "subject": subject,
                            "date": date,
                            "attachments": []
                        }

                        # Extract plain text body and save attachments
                        body = ""
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            
                            if "attachment" in content_disposition:
                                if part.get_content_maintype() == 'application' and part.get_content_subtype() == 'pdf':
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        os.makedirs("data/inbox", exist_ok=True)
                                        attachment_path = f"data/inbox/email_{message_id}_attachment.pdf"
                                        with open(attachment_path, "wb") as f:
                                            f.write(payload)
                                        metadata["attachments"].append(attachment_path)
                                continue

                            if not body and content_type == "text/plain":
                                extracted = part.get_payload(decode=True)
                                if isinstance(extracted, bytes):
                                    extracted = extracted.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                                body = extracted
                        
                        if not body:
                            # Fallback if only HTML is present
                            for part in msg.walk():
                                if part.get_content_type() == "text/html":
                                    html = part.get_payload(decode=True)
                                    if isinstance(html, bytes):
                                        html = html.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                                    body = re.sub(r'<[^>]+>', ' ', html)
                                    break

                        if body:
                            extracted_payloads.append({
                                "source": "email",
                                "metadata": metadata,
                                "content": body.strip()
                            })
                            # Ensure we don't accidentally mark as read because of fetch
                            mail.uid('STORE', eid, '-FLAGS', '\\Seen')
                                
        except Exception as e:
            raise ValueError(f"Email sync failed: {e}")
        finally:
            if mail:
                try:
                    mail.close()
                except Exception:
                    pass
                try:
                    mail.logout()
                except Exception:
                    pass

        return extracted_payloads

    def acknowledge(self, payload: RawPayload) -> None:
        uid = payload.get("metadata", {}).get("imap_uid")
        if not uid:
            return
            
        username = os.getenv("IMAP_USERNAME")
        password = os.getenv("IMAP_PASSWORD")
        server = os.getenv("IMAP_SERVER")
        port = int(os.getenv("IMAP_PORT", "993"))
        folder = os.getenv("IMAP_FOLDER", "INBOX")

        mail = None
        try:
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            mail.select(folder)
            mail.uid('STORE', uid.encode('utf-8'), '+FLAGS', '\\Seen')
        except Exception:
            pass
        finally:
            if mail:
                try:
                    mail.close()
                except Exception:
                    pass
                try:
                    mail.logout()
                except Exception:
                    pass
