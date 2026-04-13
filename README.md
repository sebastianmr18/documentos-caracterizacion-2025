# Documentos de Caracterización 2025

Repositorio fuente con los archivos de procesamiento y visualización para bases de caracterización de Campus Diverso, orientado a equipos no técnicos que trabajan con archivos Excel.

## Descripción

Este proyecto toma una base en Excel con un esquema esperado, valida su estructura, estandariza encabezados, limpia datos y genera salidas listas para análisis y socialización:

- Base cleaned en Excel (**si se requiere**, ya que se puede subir la base de datos directamente del formulario o ya limpia)
- Reporte consolidado de las gráficas en PDF
- Gráficas en PNG guardadas individualmente en un ZIP

El flujo está pensado para ejecutarse desde notebook (Google Colab o Jupyter), manteniendo la lógica de negocio modularizada en `src/`.

## Problema Que Resuelve

Facilita la caracterización anual sin depender de procesos manuales repetitivos, reduciendo errores de estructura y acelerando la generación de reportes visuales para toma de decisiones.

## Tecnologías Utilizadas

- Lenguaje: Python 3
- Análisis de datos: `pandas`, `numpy`
- Visualización: `matplotlib`
- Entrada/salida Excel: `openpyxl`, `xlrd`
- Entorno interactivo: `ipython`, notebooks (`.ipynb`)
- Exportación de imágenes/PDF: `pillow`, `matplotlib.backends.backend_pdf`

Dependencias declaradas en `requirements.txt`.

## Estructura Del Proyecto

```text
.
├── README.md
├── requirements.txt
├── notebooks/
│   ├── Automatizacion_Graficas_Caracterizacion.ipynb
│   ├── Automatizacion_Graficas_Caracterizacion - copia.ipynb
│   ├── automatizacion_graficas_caracterizacion.py
│   └── plantilla_orquestador_modular.py
└── src/
    ├── __init__.py
    ├── processing.py
    ├── visualization.py
    ├── export.py
    └── ui.py
````

## Componentes Principales

### `src/processing.py`

* Validación de esquema raw/cleaned
* Homologación de encabezados
* Filtrado por año de diligenciamiento
* Limpieza y construcción de `df_cleaned`
* Resumen de calidad

### `src/visualization.py`

* Generación de gráficas de distribución
* Histograma de edades
* Tabla de resumen como imagen

### `src/export.py`

* Exportación de base cleaned a Excel
* Consolidación de PNG en PDF
* Creación de ZIP de resultados

### `src/ui.py`

* Utilidades de interfaz para notebooks/Colab
* Mensajes, carga de archivo y descargas

### `notebooks/plantilla_orquestador_modular.py`

* Plantilla de orquestación por celdas
* Recomendada como base para ejecución modular

## Instalación

1. Clonar repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd documentos-caracterizacion-2025
```

2. Crear y activar entorno virtual (recomendado):

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Abrir notebook

* Opción A: usar `notebooks/Automatizacion_Graficas_Caracterizacion.ipynb`
* Opción B: crear un `.ipynb` propio a partir de `notebooks/plantilla_orquestador_modular.py`

## Uso

### Flujo Recomendado (Notebook)

1. Configurar parámetros generales:

   * `ANIO_ANALISIS`
   * `NOMBRE_ARCHIVO_ENTRADA`

2. Cargar archivo Excel (`raw` o `cleaned` con estructura válida).

3. Ejecutar celdas en orden.

4. Revisar salidas generadas:

   * `base_cleaned_caracterizacion_<anio>.xlsx`
   * `*.png`
   * `reporte_graficas_caracterizacion_<anio>.pdf`
   * `resultados_caracterizacion_<anio>.zip`

## Ejemplo Básico De Orquestación (Python)

```python
from pathlib import Path
import pandas as pd

from src.processing import (
    detectar_tipo_base,
    construir_dataframe_cleaned,
    crear_resumen_calidad,
)
from src.visualization import generar_salidas_iniciales
from src.export import asegurar_carpeta_salida, exportar_dataframe_cleaned_a_excel

ANIO_ANALISIS = 2025
ruta_excel = Path("entrada.xlsx")

df = pd.read_excel(ruta_excel, sheet_name=0)

tipo_base = detectar_tipo_base(df)
df_cleaned = construir_dataframe_cleaned(df, tipo_base, ANIO_ANALISIS)
resumen = crear_resumen_calidad(df, df_cleaned, tipo_base)

salida = asegurar_carpeta_salida(f"salidas_caracterizacion_{ANIO_ANALISIS}")

exportar_dataframe_cleaned_a_excel(
    df_cleaned,
    salida / f"base_cleaned_caracterizacion_{ANIO_ANALISIS}.xlsx"
)

generar_salidas_iniciales(df_cleaned, resumen, salida)
```

## Variables De Entorno

Actualmente el proyecto no requiere variables de entorno obligatorias para funcionar.

Configuraciones operativas (año, rutas, nombres de salida, flags de debug/descarga) se definen como constantes dentro del notebook/orquestador.

Si deseas externalizar configuración en el futuro, puedes migrar esos parámetros a variables de entorno sin alterar los módulos de `src/`.

## Scripts Disponibles

Este repositorio define los requisitos en `requirements.txt`.

Comandos equivalentes usados en el proyecto:

* Instalar dependencias:

```bash
pip install -r requirements.txt
```

* Ejecutar plantilla de orquestador como script:

```bash
python notebooks/plantilla_orquestador_modular.py
```

* Abrir notebook localmente:

```bash
jupyter notebook
```

* Abrir notebook en la nube (Colab): desde la interfaz web.

## Arquitectura

Arquitectura modular orientada a orquestación:

1. Capa de entrada y UI (`src/ui.py`, notebook): carga de archivo, mensajes y descargas.
2. Capa de procesamiento (`src/processing.py`): validaciones de esquema, transformaciones y calidad.
3. Capa de visualización (`src/visualization.py`): construcción de gráficas y tabla resumen.
4. Capa de exportación (`src/export.py`): persistencia de artefactos (Excel, PDF, ZIP).

Principio clave: el notebook coordina; la lógica de negocio vive en `src/`.

## Contribución

1. Crear una rama desde `main`.
2. Mantener la lógica en `src/` y usar notebooks solo para orquestar.
3. Conservar tipado, nombres explícitos y mensajes de validación claros.
4. Verificar que el flujo funcione con un Excel de prueba representativo.
5. Abrir Pull Request con descripción de cambios y evidencia de resultados.

## Licencia

No hay una licencia definida actualmente en el repositorio.

Si se requiere distribución formal, agrega un archivo `LICENSE` (por ejemplo, MIT o Apache-2.0) y actualiza esta sección.

## Notas Adicionales

* El proceso depende de un esquema de columnas estricto para bases `raw` y `cleaned`.
* Si faltan columnas obligatorias o el orden/estructura no coincide, el flujo se detiene con errores de validación explícitos.
* El filtrado por año se realiza con la columna `Fecha de diligenciamiento`.
* El proyecto está optimizado para uso en Google Colab/Jupyter; la funcionalidad de subida/descarga automática depende del entorno Colab.