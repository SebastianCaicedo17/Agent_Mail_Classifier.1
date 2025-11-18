import json
from json import JSONDecodeError
from typing import Any, Dict

from read_mail import fetch_all_emails
from groq_agent import email_reader
from sheet_updater import write_ticket_to_sheet


def extract_json_block(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Réponse Groq sans JSON exploitable.")
    return json.loads(cleaned[start : end + 1])


def main():
    mails = fetch_all_emails(max_results=50)

    for mail in mails:
        classification_raw = email_reader(mail["body"])
        try:
            classification = extract_json_block(classification_raw)
        except (JSONDecodeError, ValueError) as err:
            print(f"Impossible de parser la sortie Groq pour {mail['id']}: {err}")
            continue

        ticket_payload = write_ticket_to_sheet(mail, classification)
        print(f"Ticket {ticket_payload.get('id')} enregistré (priorité {ticket_payload.get('priorite')}).")


if __name__ == "__main__":
    main()