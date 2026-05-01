"""
Módulo de Interfaz de Usuario (UI) y Carga de Archivos.

Este módulo proporciona funciones para interactuar con el usuario, ya sea mostrando
mensajes formateados en Markdown o gestionando la carga y descarga de archivos,
con soporte dual para entornos locales y Google Colab.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from src.processing import ErrorValidacionExcel


def _obtener_markdown_y_display() -> tuple[Any, Any]:
    """
    Importa dinámicamente utilidades de visualización de IPython.

    Retorna:
        tuple[Any, Any]: Referencias a la clase Markdown y la función display de IPython.
    """
    modulo_display = importlib.import_module('IPython.display')
    return modulo_display.Markdown, modulo_display.display


def _obtener_files_colab() -> Any:
    """
    Importa dinámicamente el módulo de manejo de archivos de Google Colab.

    Retorna:
        Any: El módulo `google.colab.files`.
    """
    modulo_colab = importlib.import_module('google.colab.files')
    return modulo_colab


def mostrar_titulo(texto: str) -> None:
    """
    Muestra un texto formateado como título de nivel 2 (##) usando Markdown en la interfaz.

    Parámetros:
        texto (str): El texto del título a mostrar.
    """
    Markdown, display = _obtener_markdown_y_display()
    display(Markdown(f'## {texto}'))


def mostrar_mensaje(texto: str) -> None:
    """
    Muestra un texto formateado en Markdown estándar en la interfaz.

    Parámetros:
        texto (str): El mensaje a mostrar.
    """
    Markdown, display = _obtener_markdown_y_display()
    display(Markdown(texto))


def esta_en_colab() -> bool:
    """
    Detecta si el código se está ejecutando dentro de un entorno de Google Colab.

    Retorna:
        bool: True si está en Colab, False en caso contrario.
    """
    try:
        # Intenta importar el módulo específico de colab
        importlib.import_module('google.colab')
    except ModuleNotFoundError:
        return False
    return True


def obtener_archivos_subidos_colab() -> list[str]:
    """
    Despliega la interfaz nativa de carga de archivos en Google Colab y retorna sus rutas.

    Retorna:
        list[str]: Lista con los nombres (rutas relativas) de los archivos cargados.

    Lanza:
        RuntimeError: Si no se está en Colab o si el usuario cancela la subida sin seleccionar archivos.
    """
    # Verifica que el entorno soporte esta funcionalidad
    if not esta_en_colab():
        raise RuntimeError(
            'La carga automática está diseñada para Google Colab. '
            'Si estás en otro entorno, define las rutas de los archivos manualmente.'
        )

    # Llama al widget de subida de Colab
    archivos = _obtener_files_colab().upload()
    
    # Valida que efectivamente se hayan seleccionado archivos
    if not archivos:
        raise RuntimeError('No se cargó ningún archivo. Por favor selecciona uno o más archivos Excel.')

    return list(archivos.keys())


def descargar_archivo_si_aplica(ruta_archivo: str | Path, descargar: bool = True) -> None:
    """
    Descarga un archivo local a la máquina del usuario si se está ejecutando en Colab.

    Parámetros:
        ruta_archivo (str | Path): Ruta local del archivo a descargar.
        descargar (bool): Bandera que indica si se debe proceder con la descarga.
    """
    # Si no se solicitó la descarga o no se está en Colab, simplemente ignora la acción
    if not descargar or not esta_en_colab():
        return

    _obtener_files_colab().download(str(ruta_archivo))


def cargar_archivos_entrada(config: dict) -> list[Path]:
    """
    Resuelve y obtiene las rutas de los archivos de entrada basándose en la configuración del entorno.

    Si el entorno es 'local', busca archivos Excel en el directorio especificado.
    Si el entorno es 'colab', despliega el prompt para que el usuario los suba.

    Parámetros:
        config (dict): Diccionario de configuración con claves 'ENVIRONMENT' y 'INPUT_PATH'.

    Retorna:
        list[Path]: Lista de objetos Path apuntando a los archivos de entrada válidos.

    Lanza:
        ErrorValidacionExcel: Si hay errores con las rutas locales, si no se suben archivos
                              en Colab, o si el entorno no es reconocido.
    """
    environment = config.get("ENVIRONMENT", "colab")
    input_path = config.get("INPUT_PATH", "./data/input/")
    archivos = []
    
    if environment == "local":
        mostrar_mensaje(f"Cargando archivos desde entorno local en la ruta: `{input_path}`")
        carpeta_input = Path(input_path)
        
        # Validar que el directorio exista
        if not carpeta_input.exists() or not carpeta_input.is_dir():
            raise ErrorValidacionExcel(f"La carpeta '{input_path}' no existe o no es un directorio válido.")
            
        # Buscar archivos con extensión Excel (.xls o .xlsx)
        archivos_encontrados = list(carpeta_input.glob("*.xls*"))
        if not archivos_encontrados:
            raise ErrorValidacionExcel(f"No se encontraron archivos Excel (.xlsx o .xls) en la ruta '{input_path}'.")
            
        archivos.extend(archivos_encontrados)
        
    elif environment == "colab":
        mostrar_mensaje("Cargando archivos desde entorno Colab (subida manual)...")
        # Iniciar proceso de subida en la nube
        rutas_colab = obtener_archivos_subidos_colab()
        if not rutas_colab:
            raise ErrorValidacionExcel("No se subieron archivos en Colab.")
        archivos = [Path(r) for r in rutas_colab]
        
    else:
        # Prevención de configuraciones inválidas
        raise ErrorValidacionExcel(f"Entorno no reconocido: '{environment}'. Use 'colab' o 'local'.")
        
    return archivos