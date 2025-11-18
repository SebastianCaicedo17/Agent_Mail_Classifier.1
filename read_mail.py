import base64
from typing import Dict, List

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = "token.json"


def _decode_body(payload: Dict) -> str:
    """Décode le contenu text/plain d'un message Gmail."""
    if not payload:
        return ""

    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")

    body = payload.get("body", {})
    data = body.get("data")
    if data:
        return _decode(data)

    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return _decode(data)
    return ""


def fetch_all_emails(max_results: int = 549) -> List[Dict[str, str]]:
    """
    Retourne une liste de dictionnaires représentant les derniers emails Gmail.

    Chaque élément contient l'id, l'expéditeur, le sujet, un extrait et le corps décodé.
    """
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])

    emails: List[Dict[str, str]] = []
    for message in messages:
        msg_data = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(Sans objet)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Expéditeur inconnu)")

        emails.append(
            {
                "id": message["id"],
                "from": sender,
                "subject": subject,
                "snippet": msg_data.get("snippet", ""),
                "body": _decode_body(payload),
            }
        )

    return emails


if __name__ == "__main__":
    mails = fetch_all_emails(max_results=50)
    for mail in mails:
        print(f"De : {mail['from']}")
        print(f"Sujet : {mail['subject']}")
        print(f"Extrait : {mail['snippet']}")
        print(f"Corps : {mail['body'][:300]}...")
        print("-" * 40)
