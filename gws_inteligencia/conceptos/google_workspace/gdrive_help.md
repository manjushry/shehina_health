# Google Drive Desktop → cómo obtener el fileId de un archivo local

Objetivo: Dado un archivo accesible localmente por Google Drive for desktop, obtener su ID de Google Drive sin abrir un navegador.

## 1) Archivos nativos de Google (Docs/Sheets/Slides)

Cuando el archivo es nativo (Google Docs/Sheets/Slides), en Windows aparece como un pequeño archivo local con extensión `.gdoc`, `.gsheet`, `.gslides`, etc. El contenido de ese archivo es un JSON mínimo, por ejemplo:

```
{
  "url": "https://docs.google.com/document/d/1ABCDEFghiJKLmnopQRstuVWxyz12345/edit",
  "resource_id": "document:1ABCDEFghiJKLmnopQRstuVWxyz12345",
  "doc_id": "1ABCDEFghiJKLmnopQRstuVWxyz12345",
  "title": "MiDocumento"
}
```

Estrategia: leer el archivo `.gdoc|.gsheet|.gslides` y extraer `doc_id` o parsear el `url` (el segmento `/d/<ID>/`).
- Ventaja: no requiere API, ni navegador. Es inmediato.
- Implementación: utilitario en Python que abra el JSON y retorne el ID.

## 2) Atajos/links locales (.url, .website)

Algunos accesos directos generados por Drive o por el usuario son archivos `.url` (formato INI) con una línea `URL=...`. Basta con parsear esa línea y extraer el ID como en el caso anterior.

## 3) Rutas bajo “.shortcut-targets-by-id” (carpetas enlazadas)

Google Drive for desktop crea rutas del estilo:

```
G:\\.shortcut-targets-by-id\\<folderId>\\subcarpetas\\archivo.ext
```

Donde `<folderId>` es un ID real de Drive. Si tu archivo vive bajo esa ruta:
- Extrae `<folderId>` del path.
- Para un archivo NO nativo (ej. PDF), usa la API de Drive v3 para resolver la ruta por nombres:
  1. Parte del `<folderId>` como padre actual.
  2. Para cada segmento de carpeta `nombre`, realiza `files.list(q="name='nombre' and '<padre>' in parents and mimeType='application/vnd.google-apps.folder'")` y avanza el padre.
  3. Para el último segmento (archivo), `files.list(q="name='archivo.ext' and '<padre>' in parents")` y toma su `id`.
- Consideraciones:
  - Puede haber nombres duplicados; idealmente usar también `mimeType`/`size`/`md5Checksum` para desambiguar.
  - Este método requiere autenticación con Drive API.

## 4) Rutas bajo “My Drive” o “Shared drives” sin `.shortcut-targets-by-id`

- “Mi unidad” no expone directamente el ID en la ruta local. En este caso:
  - Opción A (recomendada): obtener primero el ID de la carpeta raíz (myDrive) usando la API y luego resolver por segmentos como en el punto 3.
  - Opción B: si el archivo es nativo (Doc/Sheet/Slide), intenta leer `.gdoc/.gsheet/.gslides` asociado (si lo hay) y extraer su URL.

## 5) ¿Abrir el navegador para extraer el ID?

No es necesario y es frágil. Es preferible:
- Leer `.gdoc/.gsheet/.gslides` (JSON) o `.url` (INI), o
- Resolver la ruta con Drive API.

## 6) API: ¿Se puede leer “links locales”?

La API de Drive no “lee” enlaces locales per se; opera con IDs/nombres/parents dentro del espacio Drive. Por eso, el enfoque más eficiente es:
- Si es Google-nativo: parsear el archivo local `.gdoc/.gsheet/.gslides`.
- Si no, usar `.shortcut-targets-by-id/<folderId>` y resolver por nombres con la API.

## 7) Recomendaciones prácticas para el repo

- Crear utilitario `mirror/gdrive_path_utils.py` con funciones:
  - `extract_id_from_gdoc_file(path)` → str
  - `extract_folder_id_from_shortcut_path(path)` → Optional[str]
  - `resolve_drive_path_to_id(drive_api, folder_id, path_segments)` → str
- Mantener credenciales en `.secrets/` y configurar `GOOGLE_APPLICATION_CREDENTIALS`.
- Evitar automatizar navegadores para este caso.

Con esto tendrás un proceso robusto y eficiente para obtener IDs sin “bomba atómica”.
