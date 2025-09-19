# Exportar Markdown → Google Docs y Sheets

Este paquete de scripts permite:

- Renderizar bloques Mermaid en archivos Markdown a imágenes (PNG) y reemplazarlos dentro del documento.
- Convertir Markdown a DOCX con formato y subirlo a Google Drive como Google Docs (convertido).
- (Opcional) Extraer tablas Markdown y cargarlas a Google Sheets.

## Requisitos

- Node.js 16+ y npm (para mermaid-cli)
- Python 3.10+
- Pandoc instalado en el sistema (https://pandoc.org/installing.html)
- Credenciales de Google (OAuth de Escritorio) para Drive/Docs/Sheets

### Instalar dependencias

Windows cmd:

```
cd c:\shekina\scripts\export
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
npm install -g @mermaid-js/mermaid-cli
```

Si prefieres no instalar globalmente mermaid-cli, los scripts también intentan usar `npx -y @mermaid-js/mermaid-cli`.

### Configurar Google OAuth

1. Crea un proyecto en Google Cloud y habilita las APIs:
   - Google Drive API
   - Google Docs API
   - (Opcional) Google Sheets API
2. Crea credenciales de tipo "Escritorio" y descarga `credentials.json`.
3. Copia `credentials.json` en `c:\shekina\scripts\export\credentials.json`.
4. La primera ejecución abrirá el navegador para autorizar y guardará `token.json`.

Scopes utilizados:
- Drive: `https://www.googleapis.com/auth/drive.file`
- Docs: `https://www.googleapis.com/auth/documents`
- Sheets (opcional): `https://www.googleapis.com/auth/spreadsheets`

## Uso: Markdown → Google Docs

```
.venv\Scripts\activate
python md_to_gdocs.py --input "c:\\shekina\\docusaurus\\docs\\diseño\\index.md" --title "Diseño del Sistema" --outdir out
```

El script:
- Detecta bloques ```mermaid
- Renderiza cada diagrama a PNG
- Reemplaza el bloque por `![titulo](ruta.png)`
- Convierte el Markdown a DOCX con Pandoc
- Sube el DOCX a Drive como Google Doc convertido y devuelve la URL

Parámetros clave:
- `--input`: ruta de un archivo `.md` o de una carpeta (procesa recursivo)
- `--title`: título del documento a crear en Google Docs
- `--outdir`: carpeta de salida para artefactos intermedios

## Uso opcional: Tablas → Google Sheets

```
.venv\Scripts\activate
python md_tables_to_sheets.py --input "c:\\shekina\\docusaurus\\docs" --sheet-title "Tablas Docs" --spreadsheet-id <ID opcional>
```

- Extrae tablas Markdown y las sube como hojas (una por archivo o por tabla) a un Spreadsheet.
- Si no pasas `--spreadsheet-id`, se crea uno nuevo y se imprime la URL.

## Notas

- Google Docs no soporta SVG de forma nativa en todos los casos; por compatibilidad exportamos PNG.
- Si Pandoc no está instalado, el script fallará con un mensaje claro. Instálalo y reintenta.
- Para Sites, la vía recomendada de interactividad es embeber por iframe la página Docusaurus publicada (Insertar → Insertar → URL).
