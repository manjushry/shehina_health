# Google Workspace (GSuite) Config

- Este folder contiene configuración para integrar con Drive/Sheets/Docs.
- No colocar credenciales reales aquí. Use `.secrets/google-service-account.json` y la variable de entorno:
  - En Windows CMD:
    set GOOGLE_APPLICATION_CREDENTIALS=C:\shekina\.secrets\google-service-account.json

## Archivos
- `config_google_workspace.yml`: configuración de rutas locales (links a Google Drive), opciones de enlace, flags.
- `google_workspace.json` (privado/ignorado): mapea IDs de documentos a archivos mock (para pruebas offline).
- `credentials_google.json`: NO versionar. Si accidentalmente se sube, rotar de inmediato la clave en GCP.

## Recomendación
- Mantener `config/gws/google_workspace.json` (privado, ignorado) para IDs (spreadsheet/doc/folder).
- Usar `src/mirror/backend_gsuite.py` como capa de acceso.

## Despliegue API-first

### Problema: Drive Desktop sincronización lenta
Si Drive Desktop está lento sincronizando, puedes usar `deploy_to_gdrive.py` para mover tu estructura local directamente a Google Drive usando APIs:

```cmd
# Dry-run (recomendado primero): ve el plan sin cambios
python deploy_to_gdrive.py --source C:\ruta\a\carpeta\local --dry-run

# Apply: crea carpetas/docs reales en Drive
python deploy_to_gdrive.py --source C:\ruta\a\carpeta\local --apply
```

### Qué hace el deployer:
1. **Backup automático**: Si ya existe una carpeta real en `local_link_path`, la mueve a backup timestamped.
2. **Junction/symlink**: Crea enlace hacia tu carpeta de Drive Desktop usando `apply_gws_config()`.
3. **Recrear en Drive**: Crea estructura de carpetas + convierte .md a Google Docs + sube binarios.
4. **Resultado**: Tu estructura queda en la nube inmediatamente, Drive Desktop sincroniza cuando quiera.

### Requisitos para --apply:
- Variable `GOOGLE_APPLICATION_CREDENTIALS` apuntando a Service Account JSON con permisos Drive + Docs.
- El Service Account debe tener acceso a la carpeta destino en Drive (compartida o My Drive).
