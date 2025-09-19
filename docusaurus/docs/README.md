# Instalación y Activación del Ambiente

## 1. Conda (Python)
- Instala Miniconda o Anaconda.
- Crea el entorno:
  ```sh
  conda env create -f environment.yml
  conda activate shekina
  ```
- Instala dependencias adicionales si es necesario:
  ```sh
  pip install -r requirements.txt
  ```

## 2. Docker
- Instala Docker Desktop desde https://www.docker.com/products/docker-desktop/
- Verifica que Docker esté corriendo y que puedas ver contenedores e imágenes.
- Usa Docker para servicios como PostgreSQL, Node.js, etc.

## 3. Docusaurus (Documentación Web)

- Instala Docusaurus en la raíz del proyecto (no crees la carpeta manualmente):
  ```sh
  cd c:\shekina
  npx create-docusaurus@latest docusaurus classic
  cd docusaurus
  npm start
  ```
- Accede a la documentación en tu navegador en [http://localhost:3000](http://localhost:3000)

**Nota:** Si la carpeta ya existe, bórrala primero con:
  ```sh
  rmdir /s /q c:\shekina\docusaurus
  ```

## 4. Firewall y Puertos
- Si no puedes acceder a la documentación, verifica el firewall:
  - Abre "Firewall de Windows con seguridad avanzada" (`wf.msc`).
  - Ve a "Reglas de entrada" y agrega una regla para permitir el puerto 3000 (o el que uses):
    - Nueva regla > Puerto > TCP > 3000 > Permitir la conexión > Todos los perfiles > Nombre descriptivo.
- Puedes cambiar el puerto externo usando el parámetro `-p` en Docker, por ejemplo:
  ```sh
  docker run -it --rm -p 8080:3000 ...
  ```
  y acceder en [http://localhost:8080](http://localhost:8080)

## 5. Edición y Migración de Documentos
- Edita los archivos Markdown en `c:\shekina\docusaurus\docs` usando VS Code.
- Puedes migrar tu documentación previa copiando los archivos desde la carpeta `docs` del proyecto.
- Para diagramas Mermaid, instala el plugin:
  ```sh
  npm install @docusaurus/theme-mermaid
  ```
  y agrégalo en `docusaurus.config.js`:
  ```js
  themes: ['@docusaurus/theme-mermaid'],
  ```

---


## 6. Vulnerabilidades conocidas en Docusaurus

> Al instalar el tema Mermaid (`@docusaurus/theme-mermaid`) y otros plugins, se detectan vulnerabilidades moderadas en dependencias como `webpack-dev-server`.
> Actualmente, no existe solución oficial.
> **Recomendación:**
> - Revisa periódicamente con `npm audit` y actualiza dependencias cuando haya fixes disponibles.
> - No expongas el servidor de documentación a internet sin protección.
> - Consulta el reporte de `npm audit` para detalles.

## 7. Comparativa de gestores de épicas y roadmap

| Gestor         | Gratuito | Integración GitHub | Épicas/Roadmap | Facilidad de uso | Asignación de responsables |
|----------------|----------|--------------------|----------------|------------------|---------------------------|
| Jira           | Sí (limitado) | Sí                | Sí            | Media/Alta       | Sí                        |
| GitHub Projects| Sí       | Nativo             | Sí             | Muy alta         | Sí                        |
| Trello         | Sí       | Parcial (Power-Up) | Simulado       | Muy alta         | Sí                        |
| ClickUp        | Sí       | Sí                 | Sí             | Alta             | Sí                        |
| Asana          | Sí       | Parcial            | Sí             | Alta             | Sí                        |
| Linear         | Sí       | Sí                 | Sí             | Alta             | Sí                        |

**Recomendación:** Si ya usas GitHub, comienza con GitHub Projects. Para equipos grandes o más funciones, Jira es el estándar.

**Notas:**
- Si tienes problemas de acceso, revisa el mapeo de puertos y el firewall.
- El ambiente es reproducible y portable usando Docker y Conda.
- Documenta cualquier paso adicional o configuración especial en este README.
