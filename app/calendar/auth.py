"""One-time local OAuth setup: python -m app.calendar.auth"""
from pathlib import Path
from app.config import settings
from app.calendar.service import SCOPES

def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise SystemExit("Install optional dependencies first: pip install -r requirements-calendar.txt") from exc
    credentials_path = Path(settings.GOOGLE_CALENDAR_CREDENTIALS).expanduser()
    token_path = Path(settings.GOOGLE_CALENDAR_TOKEN).expanduser()
    if not credentials_path.is_file():
        raise SystemExit(f"OAuth credentials file not found: {credentials_path}\nCreate an OAuth Client ID of type Desktop app in Google Cloud Console, enable Google Calendar API, and save the JSON there.")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"Google Calendar authorization saved locally to: {token_path}")

if __name__ == "__main__":
    main()
