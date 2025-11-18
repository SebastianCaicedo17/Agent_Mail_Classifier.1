from groq import Groq
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dev convenience
    def load_dotenv(*args, **kwargs):
        """Fallback si python-dotenv est absent."""
        return None
from pathlib import Path
import os

_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")

def email_reader(raw_emails: str) -> str:
    """
    Classe une ou plusieurs conversations email et renvoie un JSON formaté.

    Parameters
    ----------
    raw_emails : str
        Texte brut des emails (sujet + contenu). Sépare chaque email par une ligne vide.

    Returns
    -------
    str
        Réponse complète générée par Groq (JSON sous forme de chaîne). 
        Est également affichée en streaming dans la console.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY est manquant. "
            "Définis la variable d'environnement ou ajoute-la dans .env."
        )

    client = Groq(api_key=api_key)

    system_prompt = (
        "Tu es un agent de tri et de priorisation d'emails. "
        "Tu dois évaluer chaque email reçu et attribuer l'un des 5 niveaux "
        "de priorité suivants : Critique, Élevée, Modérée, Faible, Anodine."
        "Tu dois classer également ces mails en 5 types: Problème technique informatique, Demande administrative, Problème d’accès / authentification, Demande de support utilisateur, Bug ou dysfonctionnement d’un service."
    )

    user_prompt = f"""
Tu dois renvoyer ta réponse en JSON strictement valide, au format :
{{
    "type": "",
    "Sujet": "",
    "priorite": "",
    "Synthèse": ""
}}

Voici les emails à analyser :
{raw_emails.strip()}
""".strip()

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_completion_tokens=2048,
        top_p=0.9,
        reasoning_effort="medium",
        stream=True,
        stop=None,
    )

    response = []
    for chunk in completion:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="")
        response.append(delta)

    return "".join(response).strip()