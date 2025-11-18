from __future__ import annotations

from typing import Dict, Optional

from sheet_writer import SheetTicketWriter

_writer: Optional[SheetTicketWriter] = None


def _get_writer() -> SheetTicketWriter:
    global _writer
    if _writer is None:
        _writer = SheetTicketWriter()
    return _writer


def build_ticket(mail: Dict[str, str], classification: Dict[str, str]) -> Dict[str, str]:
    return {
        "id": mail.get("id"),
        "from": mail.get("from"),
        "Sujet": classification.get("Sujet") or mail.get("subject"),
        "type": classification.get("type"),
        "priorite": classification.get("priorite"),
        "Synthèse": classification.get("Synthèse") or classification.get("Synthese"),
        "snippet": mail.get("snippet"),
        "body": mail.get("body"),
    }


def write_ticket_to_sheet(mail: Dict[str, str], classification: Dict[str, str]) -> Dict[str, str]:
    ticket = build_ticket(mail, classification)
    _get_writer().append_ticket(ticket)
    return ticket

