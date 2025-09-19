import argparse
import re
from pathlib import Path
from typing import List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

TABLE_RE = re.compile(r"\n\|(?:(?:[^\n]|\n(?!\n))+?)\|\n", re.MULTILINE)


def ensure_auth(creds_dir: Path) -> Credentials:
    creds = None
    token_path = creds_dir / 'token.json'
    cred_path = creds_dir / 'credentials.json'
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds


def parse_table(md_table: str) -> List[List[str]]:
    lines = [ln.strip() for ln in md_table.strip().splitlines()]
    # Remove separator line (---|---)
    if len(lines) >= 2 and set(lines[1].replace('|', '').replace('-', '').strip()) == set():
        del lines[1]
    rows = []
    for ln in lines:
        if not ln.startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip('|').split('|')]
        rows.append(cells)
    return rows


def main():
    parser = argparse.ArgumentParser(description='Subir tablas Markdown a Google Sheets')
    parser.add_argument('--input', required=True, help='Ruta de archivo .md o carpeta a procesar')
    parser.add_argument('--sheet-title', required=True, help='Título del Spreadsheet')
    parser.add_argument('--spreadsheet-id', help='Spreadsheet existente (opcional)')
    parser.add_argument('--creds', default='c:/shekina/scripts/export', help='Directorio con credentials.json/token.json')
    args = parser.parse_args()

    in_path = Path(args.input)
    md_files: List[Path] = []
    if in_path.is_file():
        md_files = [in_path]
    else:
        md_files = [p for p in in_path.rglob('*.md')]

    creds = ensure_auth(Path(args.creds))
    sheets = build('sheets', 'v4', credentials=creds)
    drive = build('drive', 'v3', credentials=creds)

    spreadsheet_id = args.spreadsheet_id
    if not spreadsheet_id:
        spreadsheet = sheets.spreadsheets().create(body={'properties': {'title': args.sheet_title}}).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        # Compartir con el usuario actual (implícito en Drive, opcional)
    print('Spreadsheet:', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    # Agrega una hoja por archivo MD encontrado con la primera tabla del archivo (simple)
    for md in md_files:
        text = md.read_text(encoding='utf-8')
        match = TABLE_RE.search(text)
        if not match:
            continue
        table_md = match.group(0)
        values = parse_table(table_md)
        sheet_title = md.stem[:99]
        # Add sheet
        requests = [{'addSheet': {'properties': {'title': sheet_title}}}]
        sheets.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
        # Write values
        range_name = f"{sheet_title}!A1"
        body = {'values': values}
        sheets.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption='RAW', body=body).execute()
        print('Tabla subida desde', md)


if __name__ == '__main__':
    main()
