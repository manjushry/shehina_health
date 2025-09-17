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
