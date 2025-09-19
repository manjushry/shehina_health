import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

import pypandoc
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/documents',
]

MERMAID_BLOCK_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL | re.IGNORECASE)


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


def run_mermaid_cli(mmd_code: str, out_png: Path):
    # Prefer global mmdc, fallback to npx
    tmp_mmd = out_png.with_suffix('.mmd')
    tmp_mmd.write_text(mmd_code, encoding='utf-8')
    try_cmds = [
        ['mmdc', '-i', str(tmp_mmd), '-o', str(out_png)],
        ['npx', '-y', '@mermaid-js/mermaid-cli', '-i', str(tmp_mmd), '-o', str(out_png)],
    ]
    last_err = None
    for cmd in try_cmds:
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return
        except subprocess.CalledProcessError as e:
            last_err = e
    raise RuntimeError(f"No se pudo ejecutar mermaid-cli: {last_err}")


def replace_mermaid_with_images(md_text: str, workdir: Path) -> str:
    images: List[Path] = []
    def _repl(match):
        code = match.group(1)
        img_path = workdir / f"mermaid_{len(images)+1}.png"
        run_mermaid_cli(code, img_path)
        images.append(img_path)
        return f"![diagrama]({img_path.as_posix()})\n"
    return MERMAID_BLOCK_RE.sub(_repl, md_text)


def md_to_docx(md_path: Path, out_docx: Path) -> Path:
    pypandoc.convert_file(
        str(md_path),
        'docx',
        outputfile=str(out_docx),
        extra_args=['--wrap=none']
    )
    return out_docx


def upload_docx_as_google_doc(drive, docx_path: Path, title: str) -> str:
    media = MediaFileUpload(str(docx_path), mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
    }
    file = drive.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    return file['webViewLink']


def main():
    parser = argparse.ArgumentParser(description='Convertir Markdown a Google Docs renderizando Mermaid a imágenes')
    parser.add_argument('--input', required=True, help='Ruta de archivo .md o carpeta a procesar')
    parser.add_argument('--title', required=True, help='Título del documento en Google Docs')
    parser.add_argument('--outdir', default='out', help='Directorio de salida para artefactos temporales')
    parser.add_argument('--creds', default='c:/shekina/scripts/export', help='Directorio con credentials.json/token.json')
    args = parser.parse_args()

    in_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    creds_dir = Path(args.creds)

    md_files: List[Path] = []
    if in_path.is_file():
        md_files = [in_path]
    else:
        md_files = [p for p in in_path.rglob('*.md')]

    if not md_files:
        print('No se encontraron archivos Markdown')
        return

    creds = ensure_auth(creds_dir)
    drive = build('drive', 'v3', credentials=creds)

    # Por simplicidad: si es un solo archivo, subimos un único Doc; si son varios, concatenamos
    concatenated = ''
    for md_file in md_files:
        text = md_file.read_text(encoding='utf-8')
        text_processed = replace_mermaid_with_images(text, outdir)
        # Agrega título por archivo si hay múltiples
        if len(md_files) > 1:
            concatenated += f"\n\n# {md_file.stem}\n\n" + text_processed
        else:
            concatenated = text_processed

    tmp_md = outdir / 'merged.md'
    tmp_md.write_text(concatenated, encoding='utf-8')

    docx_path = outdir / 'documento.docx'
    md_to_docx(tmp_md, docx_path)

    link = upload_docx_as_google_doc(drive, docx_path, args.title)
    print('Documento creado:', link)


if __name__ == '__main__':
    main()
