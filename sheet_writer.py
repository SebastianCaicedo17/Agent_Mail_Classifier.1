from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dev convenience
    def load_dotenv(*args, **kwargs):
        return None


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CLIENT_SECRET_PRIMARY = PROJECT_ROOT / "client_secret.json"
CLIENT_SECRET_FALLBACK = PROJECT_ROOT / "token.json"
TOKEN_SHEETS_PATH = PROJECT_ROOT / "token_sheets.json"

DEFAULT_TAB = "Autres"
CATEGORY_TABS = {
    "problème technique informatique": "Problème technique informatique",
    "probleme technique informatique": "Problème technique informatique",
    "demande administrative": "Demande administrative",
    "problème d’accès / authentification": "Problème d’accès / authentification",
    "probleme d’accès / authentification": "Problème d’accès / authentification",
    "probleme d'acces / authentification": "Problème d’accès / authentification",
    "demande de support utilisateur": "Demande de support utilisateur",
    "bug ou dysfonctionnement d’un service": "Bug ou dysfonctionnement d’un service",
    "bug ou dysfonctionnement d'un service": "Bug ou dysfonctionnement d’un service",
}


def _load_credentials() -> Credentials:
    creds: Optional[Credentials] = None
    if TOKEN_SHEETS_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_SHEETS_PATH), SHEETS_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        client_secret_path = (
            CLIENT_SECRET_PRIMARY
            if CLIENT_SECRET_PRIMARY.exists()
            else CLIENT_SECRET_FALLBACK
        )
        if not client_secret_path.exists():
            raise FileNotFoundError(
                "Client secret introuvable. "
                f"Attendu à {CLIENT_SECRET_PRIMARY} ou {CLIENT_SECRET_FALLBACK}."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SHEETS_SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_SHEETS_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


def normalize_category(category: Optional[str]) -> str:
    if not category:
        return DEFAULT_TAB

    normalized = category.strip().casefold()
    return CATEGORY_TABS.get(normalized, DEFAULT_TAB)


class SheetTicketWriter:
    def __init__(self, spreadsheet_id: Optional[str] = None):
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEET_ID")
        if not self.spreadsheet_id:
            raise RuntimeError(
                "GOOGLE_SHEET_ID est manquant. "
                "Ajoute-le à ton environnement ou au fichier .env."
            )
        self.service = build("sheets", "v4", credentials=_load_credentials())

    def append_ticket(self, ticket: Dict[str, str]) -> None:
        tab_name = normalize_category(ticket.get("type"))
        urgency = ticket.get("priorite") or ""
        values = [[ticket.get("Sujet", ""), urgency, ticket.get("Synthèse") or ticket.get("Synthese", "")]]

        body = {"values": values}
        target_range = f"{tab_name}!A:C"

        try:
            (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.spreadsheet_id,
                    range=target_range,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )
        except HttpError as err:
            raise RuntimeError(f"Échec de l'écriture dans Google Sheets ({tab_name})") from err

