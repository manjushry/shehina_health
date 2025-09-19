# Instalación y Configuración de Ambientes

## Instalación y configuración de Docusaurus

### Requisitos previos
- Node.js y npm instalados
- Acceso a terminal (cmd, PowerShell, bash)

### Pasos para instalar Docusaurus
1. Instala Node.js desde https://nodejs.org/en/download/
2. Verifica la instalación:
   ```sh
   node --version
   npm --version
   ```
3. Navega a la carpeta raíz del proyecto:
   ```sh
   cd c:\shekina
   ```
4. Instala Docusaurus:
   ```sh
   npx create-docusaurus@latest docusaurus classic
   cd docusaurus
   npm install --save @docusaurus/theme-mermaid
   ```
5. Configura el plugin Mermaid en `docusaurus.config.js` o `docusaurus.config.ts`:
   ```js
   themes: ['@docusaurus/theme-mermaid'],
   markdown: { mermaid: true },
   ```
6. Inicia el servidor:
   ```sh
   npm run start
   ```
7. Accede a la documentación en [http://localhost:3000](http://localhost:3000)

---

## Clase Alef: Instalador de Ambientes

La clase `Alef` permite instalar y configurar componentes clave del entorno de desarrollo (Docker, Conda, Docusaurus, etc.) de forma automatizada y multiplataforma.

### Ejemplo de clase Alef (Python)
```python
import subprocess
import sys
import platform

class Alef:
  def install_node(self):
    if platform.system() == 'Windows':
      print('Descarga Node.js manualmente desde https://nodejs.org/en/download/')
    else:
      subprocess.run(['sudo', 'apt', 'install', 'nodejs', 'npm'])

  def install_docusaurus(self, path):
    subprocess.run(['npx', 'create-docusaurus@latest', path, 'classic'])
    subprocess.run(['npm', 'install', '--save', '@docusaurus/theme-mermaid'], cwd=path)

  def install_conda(self):
    print('Descarga Miniconda manualmente desde https://docs.conda.io/en/latest/miniconda.html')

  def install_docker(self):
    if platform.system() == 'Windows':
      print('Descarga Docker Desktop manualmente desde https://www.docker.com/products/docker-desktop/')
    else:
      subprocess.run(['sudo', 'apt', 'install', 'docker.io'])

  def setup_environment(self):
    self.install_node()
    self.install_docusaurus('docusaurus')
    self.install_conda()
    self.install_docker()

if __name__ == '__main__':
  alef = Alef()
  alef.setup_environment()
```

### Notas
- Para Windows, algunas instalaciones requieren pasos manuales (Node.js, Docker Desktop, Miniconda).
- Puedes ampliar la clase Alef para instalar otros componentes y gestionar ambientes en Mac/Linux.
- El objetivo es automatizar la construcción primaria del entorno para facilitar la descarga y uso del repositorio desde GitHub.

---

Actualiza este documento cada vez que se agregue un nuevo componente o herramienta relevante para el equipo.
# Configuración del ambiente de desarrollo para Shekina

## Activación automática del entorno Conda en VS Code

Para asegurar que todas las terminales y scripts usen el entorno correcto (`shekina`), configura VS Code para activar el entorno automáticamente al abrir una terminal:

### Pasos
1. Abre la configuración de VS Code (`Ctrl+,`).
2. Busca: `Terminal > Integrated > Profiles: Windows`.
3. Haz clic en “Editar en settings.json” para agregar un perfil personalizado.
4. Agrega el siguiente bloque en tu `settings.json`:
   ```json
   "terminal.integrated.profiles.windows": {
     "Shekina Conda": {
       "path": "C:\\Windows\\System32\\cmd.exe",
       "args": ["/K", "conda activate shekina"]
     }
   },
   "terminal.integrated.defaultProfile.windows": "Shekina Conda"
   ```
5. Guarda los cambios y abre una nueva terminal en VS Code. Debería aparecer automáticamente con el entorno `(shekina)` activado.

---

## Importancia de documentar los procesos de desarrollo
- Permite que cualquier colaborador configure su ambiente de forma rápida y sin errores.
- Facilita la reproducibilidad y la colaboración en equipos ágiles.
- Evita problemas de dependencias y versiones.
- Deja registro claro de las decisiones técnicas y facilita la incorporación de nuevos miembros.

---

## Otros tips de configuración ágil
- Selecciona el intérprete de Python correcto en VS Code (`Python: Select Interpreter`).
- Mantén actualizado el archivo `environment.yml`.
- Documenta cualquier configuración especial en esta sección.

---

Esta sección debe actualizarse cada vez que se agregue una nueva herramienta, entorno o tip relevante para el equipo Shekina.
