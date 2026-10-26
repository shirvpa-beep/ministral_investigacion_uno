# Proyecto de inferencia local con Ministral 3 8B

## 1. Descripción del proyecto

Este proyecto implementa un sistema de inferencia local utilizando el modelo de lenguaje Ministral 3 8B, ejecutado mediante Ollama y controlado desde un script desarrollado en Python.

El objetivo es evaluar el funcionamiento del modelo mediante una suite de 10 prompts que cubren diferentes tareas: generación de texto, resumen, corrección ortográfica, traducción, programación y razonamiento lógico.

El sistema registra métricas de ejecución y guarda los resultados en archivos JSON y CSV para facilitar su análisis posterior.

## 2. Tecnologías utilizadas

- Python 3.12.15.
- Ollama para ejecutar el modelo de lenguaje.
- Ministral 3 8B Instruct, versión cuantizada Q4_K_M.
- Biblioteca `requests` para realizar solicitudes HTTP.
- Docker para construir y ejecutar el entorno de inferencia.
- Archivos JSON y CSV para almacenar los resultados.

## 3. Requisitos previos

- Windows 11 o un sistema compatible.
- Python 3.12.
- Ollama instalado y en ejecución.
- Docker Desktop instalado y funcionando.
- El modelo `ministral-3:8b-instruct-2512-q4_K_M` descargado en Ollama.

Para descargar el modelo si todavía no está instalado:

```powershell
ollama pull ministral-3:8b-instruct-2512-q4_K_M
```

Verificar que esté disponible:

```powershell
ollama list
```

## 4. Estructura del proyecto

```text
ministral_investigacion_uno/
├── src/
│   └── inference.py
├── prompts/
│   └── suite.json
├── results/
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

La carpeta `results/` contiene los resultados generados durante las pruebas. Los entornos virtuales y los archivos temporales se excluyen del control de versiones mediante `.gitignore`.

## 5. Instalación y ejecución local

Desde la carpeta raíz del proyecto, crear y activar un entorno virtual si todavía no existe:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Verificar que Ollama esté disponible y ejecutar la suite:

```powershell
python .\src\inference.py --suite .\prompts\suite.json --output-dir .\results
```

El script ejecuta los prompts definidos en `prompts/suite.json` y guarda los resultados en archivos JSON y CSV dentro de la carpeta indicada.

## 6. Parámetros disponibles

El programa permite configurar los siguientes argumentos:

| Parámetro | Descripción |
|---|---|
| `--model` | Nombre del modelo de Ollama. |
| `--prompt` | Texto de un prompt escrito directamente en la terminal. |
| `--prompt-file` | Ruta de un archivo de texto con un prompt. |
| `--suite` | Ruta del archivo JSON que contiene varios prompts. |
| `--temperature` | Temperatura de generación; valor predeterminado: 0.7. |
| `--max-tokens` | Máximo de tokens generados; valor predeterminado: 256. |
| `--output-dir` | Carpeta de salida; valor predeterminado: `results`. |

Ejemplo para ejecutar la suite con temperatura 0.2 y un máximo de 256 tokens:

```powershell
python .\src\inference.py --suite .\prompts\suite.json --temperature 0.2 --max-tokens 256 --output-dir .\results
```

Para comparar configuraciones, se recomienda guardar cada ejecución en una carpeta distinta.

## 7. Métricas registradas

El sistema registra, entre otros, los siguientes datos:

- Identificador, categoría y tarea del prompt.
- Texto de entrada y respuesta generada.
- Cantidad de tokens generados.
- Tiempo total de la solicitud.
- Velocidad de generación en tokens por segundo.
- Estimación del tiempo hasta el primer token (TTFT).
- Temperatura, máximo de tokens, estado y posibles errores.

**Nota:** el TTFT se estima a partir del tiempo de evaluación del prompt informado por Ollama; no corresponde a una medición directa del tiempo hasta el primer token.

## 8. Ejecución con Docker

Construir la imagen desde la carpeta raíz:

```powershell
docker build -t ministral-inferencia:1.0 .
```

Verificar la imagen creada:

```powershell
docker images
```

Preparar una carpeta para los resultados:

```powershell
New-Item -ItemType Directory -Force .\results\docker
```

Ejecutar el contenedor y conservar los resultados en la carpeta local:

```powershell
docker run --rm -v "${PWD}\results\docker:/app/results" ministral-inferencia:1.0
```

El contenedor utiliza `host.docker.internal` para comunicarse con Ollama ejecutándose en el equipo anfitrión.

Antes de ejecutar el contenedor, Ollama debe estar iniciado y el modelo requerido debe estar disponible. El modelo no se copia dentro de la imagen Docker: permanece administrado por Ollama en el equipo anfitrión.

La imagen utiliza una versión fija de Python, instala las dependencias en capas separadas, configura un usuario no root y excluye archivos innecesarios mediante `.dockerignore`.

## 9. Archivos de resultados

Las ejecuciones producen archivos con nombres que incluyen la fecha y hora:

- `resultados_YYYYMMDD_HHMMSS.json`
- `resultados_YYYYMMDD_HHMMSS.csv`

Estos archivos permiten consultar las respuestas, revisar errores y comparar métricas entre ejecuciones.

## 10. Consideraciones y limitaciones

- La velocidad de generación depende del hardware, la configuración y la carga del equipo.
- La ejecución local requiere recursos suficientes de memoria y almacenamiento.
- El TTFT registrado es una estimación basada en la evaluación del prompt.
- Los resultados deben interpretarse considerando que una sola ejecución puede no representar el rendimiento habitual.
- Para comparar temperaturas u otras configuraciones, deben mantenerse iguales los demás parámetros y documentarse las condiciones de prueba.

## 11. Autoría y propósito académico

Proyecto desarrollado con fines académicos para estudiar la ejecución local de modelos de lenguaje, medir su rendimiento mediante un conjunto de pruebas reproducibles y documentar el uso de Docker como mecanismo de empaquetado del entorno de inferencia.



## 12. Problemas encontrados y soluciones

| Problema | Solución aplicada |
|---|---|
| El entorno de Python presentó dificultades para ejecutar el intérprete. | Se utilizó directamente el intérprete de Python del entorno virtual del proyecto. |
| Faltaba la biblioteca `requests`. | Se instaló la dependencia y se registró en `requirements.txt`. |
| Ollama no estaba disponible al intentar realizar solicitudes. | Se verificó que el servicio estuviera ejecutándose y que el modelo estuviera instalado. |
| El archivo `suite.json` se creó inicialmente como una carpeta. | Se corrigió la estructura para utilizar un archivo JSON válido con los prompts de prueba. |
| Docker Desktop indicó que WSL no estaba instalado. | Se instaló WSL y se verificó el funcionamiento de Docker. |
| El contenedor necesitaba comunicarse con Ollama ejecutándose en Windows. | Se configuró `OLLAMA_URL` para utilizar `host.docker.internal`. |
| Era necesario evitar copiar archivos innecesarios a la imagen Docker. | Se creó `.dockerignore` para excluir entornos virtuales, resultados, archivos temporales y otros elementos. |
| Git no se reconocía inicialmente como comando en PowerShell. | Se verificó la instalación de Git y se utilizó su ejecutable mediante la ruta correspondiente. |