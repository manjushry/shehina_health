```markdown
Genera la documentación para las siguientes clases de Python en formato Markdown, para ser usada en Docusaurus. Para cada clase, incluye:

1.  **Nombre de la Clase y Descripción Breve:**
    - Título con el nombre de la clase.
    - Párrafo que resuma su propósito principal y el contexto de uso en el framework.
2.  **Diagrama de Clases (Mermaid):**
    - Diagrama de clases en formato Mermaid (`classDiagram`) mostrando:
        * La clase principal.
        * Sus atributos (propiedades).
        * Sus métodos (funciones).
        * Relaciones de herencia o composición (si aplica).
    - Usa las mejores prácticas visuales para claridad y navegabilidad.
3.  **Atributos:**
    - Tabla con los atributos más importantes, columnas:
        * Atributo
        * Descripción
        * Tipo
        * Reglas / Notas
        * Métodos que lo gestionan
4.  **Métodos Principales:**
    - Tabla con los métodos más importantes, columnas:
        * Método
        * Descripción
        * Parámetros
        * Ejemplo de uso
5.  **Ejemplo de Uso:**
    - Bloque de código en Python mostrando cómo instanciar y usar la clase, cubriendo los métodos principales.
    - Incluye comentarios explicativos en el ejemplo para resaltar pasos clave.
6.  **Versiones y cambios:**
    - Sección que indique el archivo de historial de cambios (CHANGELOG) relevante para la clase.
7.  **Diagrama de Secuencia (opcional):**
    - Si la clase tiene métodos clave que interactúan entre sí o con otras clases, incluye un diagrama de secuencia Mermaid (`sequenceDiagram`).
    - Ejemplo concreto: documenta el flujo de interacción entre métodos como `save()`, `validate()`, y `notify()` si existen.
8.  **Notas de diseño:**
    - Documenta decisiones arquitectónicas, patrones utilizados, consideraciones especiales o limitaciones.
9.  **Referencias cruzadas:**
    - Incluye enlaces a módulos, clases o documentación relacionada para mejorar el contexto y la navegabilidad.

**En el archivo diseño/index.md:**

- Coloca el diagrama general de clases del sistema (Mermaid).
- Incluye una tabla de componentes principales con descripción y vínculo directo a la documentación de cada clase.
- Asegura que cada clase tenga su propia subcarpeta y archivo index.md con la estructura anterior.
- Los vínculos deben ser navegables y claros para el usuario.

**Clases a Documentar:**

*   `AlchemistPrime`
*   `Aleya`
*   `BereshitSQL`
*   `DaathGraph`
*   `Mirror`
*   `Shekina`

**Mejores Prácticas para Mermaid y Markdown:**

*   Usa `classDiagram` para iniciar el diagrama de clases.
*   Define la clase con `class NombreClase { ... }`.
*   Define atributos con `+atributo`.
*   Define métodos con `+metodo(params)`.
*   Usa `<|--` para indicar herencia y `o--` para composición.
*   Para diagramas de secuencia, usa `sequenceDiagram` y muestra la interacción entre instancias y métodos clave. Ejemplo:
    ```mermaid
    sequenceDiagram
    participant User
    participant Aleya
    User->>Aleya: create()
    Aleya->>Aleya: validate()
    Aleya->>User: return result
    ```
*   Mantén los diagramas y tablas visualmente claros y alineados con la navegación del sistema.
*   Utiliza archivos independientes y subcarpetas para cada clase, permitiendo modularidad y ejemplos extensibles.
*   Incluye enlaces lógicos en el menú lateral para cada clase dentro de la sección de diseño.
*   Documenta los principios de modularidad, versionado y buenas prácticas de integración.
*   Mantén la documentación actualizada con cada cambio relevante en el código.

**Checklist antes de finalizar la documentación:**

- [ ] ¿Incluiste el diagrama de clases y el de secuencia (si aplica)?
- [ ] ¿Las tablas de atributos y métodos están completas y claras?
- [ ] ¿El ejemplo de uso tiene comentarios explicativos?
- [ ] ¿Agregaste notas de diseño y referencias cruzadas?
- [ ] ¿El historial de cambios está referenciado?
- [ ] ¿La navegación y los enlaces funcionan correctamente?
```
