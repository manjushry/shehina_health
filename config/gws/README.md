# Google Workspace (GSuite) Config

- Este folder contiene configuración para integrar con Drive/Sheets/Docs.
- No colocar credenciales reales aquí. Use `.secrets/google-service-account.json` y la variable de entorno:
  - En Windows CMD:
    set GOOGLE_APPLICATION_CREDENTIALS=C:\shekina\.secrets\google-service-account.json

## Archivos
- `config.yml`: configuración de rutas locales (links a Google Drive), opciones de enlace, flags.
- `credentials_google.json`: NO versionar. Si accidentalmente se sube, rotar de inmediato la clave en GCP.

## Recomendación
- Mantener `config/google_workspace.json` (privado, ignorado) para IDs (spreadsheet/doc/folder).
- Usar `src/mirror/backend_gsuite.py` como capa de acceso.
