# App de Autómatas

Aplicación de escritorio para construir, editar, simular y convertir **autómatas finitos deterministas (AFD)** y **autómatas finitos no deterministas (AFN)** sin transiciones ε. Está desarrollada en Python 3.12 con PySide6 y sigue una separación MVC entre dominio, interfaz y controladores.

## Funcionalidades

- Creación gráfica de estados y transiciones mediante mouse.
- Estados iniciales y de aceptación, incluyendo estados que cumplen ambas funciones.
- AFD y AFN sin transiciones ε.
- Agrupación de varios símbolos sobre una misma transición.
- Renombrado, eliminación y movimiento de estados.
- Edición y eliminación de transiciones.
- Zoom con la rueda del mouse y paneo del lienzo.
- Tema claro y oscuro con identidad visual morado/dorado.
- Validación estructural antes de simular.
- Simulación paso a paso, reproducción automática, pausa y reinicio.
- Visualización de caminos válidos y recorridos descartados durante la simulación.
- Conversión AFN → AFD mediante construcción de subconjuntos.
- Tabla de transiciones del AFD generado.
- Vista pedagógica **Ver Proceso** para recorrer la conversión paso a paso.
- Guardado y carga de autómatas en JSON, incluyendo posiciones gráficas.

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

El proyecto fija sus dependencias mediante `pyproject.toml` y `uv.lock`; no utiliza `requirements.txt`.

## Instalación

Clona el repositorio y sincroniza el entorno:

```bash
uv sync
```

Ejecuta la aplicación:

```bash
uv run app-automatas
```

## Uso básico

### Construir un autómata

1. Elige **AFD** o **AFN** antes de crear estados.
2. Define el alfabeto, por ejemplo `a, b` o `0, 1`.
3. Usa la herramienta **Estado** y haz clic sobre el lienzo.
4. Con **Seleccionar**, marca el estado inicial y los estados de aceptación desde el panel izquierdo.
5. Usa **Transición**, selecciona origen y destino y luego el símbolo.
6. Mueve los estados libremente; las flechas se actualizan automáticamente.

En un AFD no se permite más de un destino para la misma combinación `estado + símbolo`. En un AFN sí se permiten múltiples destinos. Las transiciones ε no están soportadas.

### Navegación del lienzo

- **Rueda del mouse:** zoom.
- **Seleccionar + arrastrar espacio vacío:** mover el área de trabajo.
- **Botón central + arrastrar:** mover el área con cualquier herramienta activa.

### Simulación

Escribe una cadena en el panel inferior y pulsa **Iniciar**. Puedes usar:

- **Siguiente paso** para avanzar manualmente.
- **Reproducir** para animación automática.
- **Pausar** para detenerla temporalmente.
- **Reiniciar** para volver al estado inicial con la misma cadena.

La cadena vacía se representa en la interfaz como **Vacía**. Un AFD incompleto es válido; si durante la simulación falta una transición para el símbolo actual, la cadena se rechaza.

### Conversión AFN → AFD

Al editar un AFN se habilita el botón de conversión. La conversión:

- conserva intacto el AFN original;
- construye un AFD equivalente por subconjuntos;
- abre el resultado en una ventana independiente;
- muestra la tabla de transiciones a la derecha;
- permite **Ver Proceso** para consultar la tabla original, expansión de conjuntos, renombrado `k0, k1, ...` y AFD final alcanzable.

## Guardar y abrir

La toolbar incluye:

- **Abrir** (`Ctrl+O`)
- **Guardar** (`Ctrl+S`)

Los documentos usan JSON. Se almacenan el tipo de autómata, alfabeto, estados, posición de cada estado, estado inicial, estados de aceptación y transiciones.

Ejemplo simplificado:

```json
{
  "format": "app-automatas",
  "version": 1,
  "automaton_type": "AFD",
  "alphabet": ["0", "1"],
  "states": [
    {
      "id": "q0",
      "is_initial": true,
      "is_accepting": false,
      "x": 250.0,
      "y": 200.0
    }
  ],
  "transitions": []
}
```

El cargador valida el archivo antes de reemplazar el documento actual y muestra un mensaje amigable si el JSON está corrupto o no respeta las reglas de la aplicación.

## Tests

Ejecutar toda la suite:

```bash
uv run pytest
```

Ejecutar tests con cobertura en terminal:

```bash
uv run pytest --cov=app_automatas --cov-report=term-missing
```

Generar reporte HTML:

```bash
uv run pytest --cov=app_automatas --cov-report=html
```

Luego abre `htmlcov/index.html` en el navegador.

## Arquitectura

```text
src/app_automatas/
├── controller/     # Coordinación entre dominio y UI
├── model/          # State, Transition, Automaton, DFA, NFA y sesión
├── services/       # Simulación, validación, conversión y persistencia
├── theme/          # Paletas y stylesheet centralizados
└── view/           # Ventana, canvas, diálogos y widgets PySide6
```

La lógica de autómatas, simulación, conversión y persistencia está desacoplada de PySide6 para poder probarla sin depender de la interfaz gráfica.

## Estructura del JSON

El formato actual usa `"version": 1`. Los archivos de otras aplicaciones o versiones no compatibles se rechazan en lugar de intentar interpretarlos silenciosamente.

## Desarrollo

No se debe versionar `.venv`, `.coverage`, `htmlcov/`, cachés de Python ni artefactos de build; ya están incluidos en `.gitignore`.
