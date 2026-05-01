"""
Módulo de Exportación.

Este módulo se encarga de empaquetar y guardar los resultados del procesamiento,
incluyendo la generación de documentos PDF con gráficas, archivos comprimidos ZIP
con todos los resultados, y la exportación de DataFrames limpios a formato Excel.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


def asegurar_carpeta_salida(carpeta_salida: str | Path) -> Path:
    """
    Crea la carpeta de salida y sus padres si no existen.

    Parámetros:
        carpeta_salida (str | Path): Ruta de la carpeta a crear o verificar.

    Retorna:
        Path: Objeto Path apuntando a la carpeta de salida asegurada.
    """
    ruta = Path(carpeta_salida)
    # Se asegura de crear los directorios necesarios (parents=True) sin error si ya existen
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def exportar_figuras_a_pdf(rutas_imagenes: list[str | Path], ruta_pdf: str | Path) -> Path:
    """
    Toma una lista de rutas de imágenes y las compila en un único documento PDF.

    Parámetros:
        rutas_imagenes (list[str | Path]): Lista de rutas de las imágenes generadas (.png).
        ruta_pdf (str | Path): Ruta donde se guardará el archivo PDF resultante.

    Retorna:
        Path: Ruta final del PDF generado.
    """
    ruta_destino = Path(ruta_pdf)
    
    # Abortar operación si no hay nada que exportar
    if not rutas_imagenes:
        print('No hay imágenes para exportar al PDF.')
        return ruta_destino

    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    
    # Abrimos el contexto del PDF para agregar páginas progresivamente
    with PdfPages(ruta_destino) as pdf:
        for ruta_imagen in rutas_imagenes:
            imagen = plt.imread(ruta_imagen)
            # Se usa el tamaño estándar A4 apaisado: 11.69 x 8.27 pulgadas
            figura = plt.figure(figsize=(11.69, 8.27))
            
            # Dibujamos la imagen completa en la figura
            plt.imshow(imagen)
            plt.axis('off')  # Quitamos los ejes para que sea presentación limpia
            
            # Guardamos la figura como una nueva página en el PDF
            pdf.savefig(figura, bbox_inches='tight')
            plt.close(figura) # Liberar memoria de matplotlib
            
    return ruta_destino


def crear_zip_resultados(carpeta_salida: str | Path, nombre_zip: str = 'resultados_caracterizacion_zip') -> Path:
    """
    Comprime todos los archivos dentro de la carpeta de salida en un único archivo ZIP.

    Parámetros:
        carpeta_salida (str | Path): Carpeta que contiene los archivos a comprimir.
        nombre_zip (str): Nombre base del archivo ZIP que se generará.

    Retorna:
        Path: Ruta final del archivo ZIP.
    """
    carpeta_destino = Path(carpeta_salida)
    # Ubicar el ZIP un nivel arriba de la carpeta de imágenes para evitar anidamientos extraños
    ruta_zip = carpeta_destino.parent / f'{nombre_zip}.zip'

    # Evita conflictos eliminando el archivo anterior si existe
    if ruta_zip.exists():
        ruta_zip.unlink()

    # Recopilar lista de archivos regulares (excluyendo cualquier .zip previamente creado)
    archivos_a_incluir = [
        ruta for ruta in sorted(carpeta_destino.iterdir())
        if ruta.is_file() and ruta.suffix.lower() != '.zip'
    ]

    # Crear el ZIP utilizando compresión DEFLATED estándar
    with zipfile.ZipFile(ruta_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as archivo_zip:
        for ruta_archivo in archivos_a_incluir:
            # Escribir el archivo sin la ruta absoluta (usando solo el nombre para que quede plano en el ZIP)
            archivo_zip.write(ruta_archivo, arcname=ruta_archivo.name)

    return ruta_zip


def exportar_dataframe_cleaned_a_excel(
    df_cleaned: pd.DataFrame,
    ruta_salida: str | Path,
    formato_fecha_preferido: str = '%d/%m/%Y',
) -> Path:
    """
    Exporta el DataFrame de datos limpios a un archivo de Excel,
    formateando correctamente las columnas de fechas antes de escribir.

    Parámetros:
        df_cleaned (pd.DataFrame): El DataFrame resultante tras la limpieza.
        ruta_salida (str | Path): Dónde guardar el archivo Excel resultante.
        formato_fecha_preferido (str): Formato de fecha strftime a utilizar (por defecto DD/MM/YYYY).

    Retorna:
        Path: Ruta del archivo Excel exportado.
    """
    ruta_destino = Path(ruta_salida)
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    
    # Trabajar con una copia para evitar modificar el DataFrame en memoria original
    df_exportacion = df_cleaned.copy()
    
    # Convertir fechas de objeto datetime a string usando el formato preferido para consistencia visual en Excel
    if 'Fecha de nacimiento' in df_exportacion.columns:
        df_exportacion['Fecha de nacimiento'] = df_exportacion['Fecha de nacimiento'].dt.strftime(formato_fecha_preferido)
        
    df_exportacion.to_excel(ruta_destino, index=False)
    return ruta_destino
