from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from src.processing import ErrorValidacionExcel


def _obtener_markdown_y_display() -> tuple[Any, Any]:
    modulo_display = importlib.import_module('IPython.display')
    return modulo_display.Markdown, modulo_display.display


def _obtener_files_colab() -> Any:
    modulo_colab = importlib.import_module('google.colab.files')
    return modulo_colab


def mostrar_titulo(texto: str) -> None:
    Markdown, display = _obtener_markdown_y_display()
    display(Markdown(f'## {texto}'))


def mostrar_mensaje(texto: str) -> None:
    Markdown, display = _obtener_markdown_y_display()
    display(Markdown(texto))




def esta_en_colab() -> bool:
    try:
        importlib.import_module('google.colab')
    except ModuleNotFoundError:
        return False
    return True


def obtener_archivos_subidos_colab() -> list[str]:
    if not esta_en_colab():
        raise RuntimeError(
            'La carga manual automática está diseñada para Google Colab. '
            'Si estás en otro entorno, define las rutas de los archivos manualmente.'
        )

    archivos = _obtener_files_colab().upload()
    if not archivos:
        raise RuntimeError('No se cargó ningún archivo. Por favor selecciona uno o más archivos Excel.')

    return list(archivos.keys())


def descargar_archivo_si_aplica(ruta_archivo: str | Path, descargar: bool = True) -> None:
    if not descargar or not esta_en_colab():
        return

    _obtener_files_colab().download(str(ruta_archivo))


def cargar_archivos_entrada(config: dict) -> list[Path]:
    """Carga los archivos dependiendo del entorno configurado."""
    environment = config.get("ENVIRONMENT", "colab")
    input_path = config.get("INPUT_PATH", "./data/input/")
    archivos = []
    
    if environment == "local":
        mostrar_mensaje(f"Cargando archivos desde entorno local en la ruta: `{input_path}`")
        carpeta_input = Path(input_path)
        
        if not carpeta_input.exists() or not carpeta_input.is_dir():
            raise ErrorValidacionExcel(f"La carpeta '{input_path}' no existe o no es un directorio válido.")
            
        archivos_encontrados = list(carpeta_input.glob("*.xls*"))
        if not archivos_encontrados:
            raise ErrorValidacionExcel(f"No se encontraron archivos Excel (.xlsx o .xls) en la ruta '{input_path}'.")
            
        archivos.extend(archivos_encontrados)
        
    elif environment == "colab":
        mostrar_mensaje("Cargando archivos desde entorno Colab (subida manual)...")
        rutas_colab = obtener_archivos_subidos_colab()
        if not rutas_colab:
            raise ErrorValidacionExcel("No se subieron archivos en Colab.")
        archivos = [Path(r) for r in rutas_colab]
        
    else:
        raise ErrorValidacionExcel(f"Entorno no reconocido: '{environment}'. Use 'colab' o 'local'.")
        
    return archivos