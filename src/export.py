from __future__ import annotations

import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


def asegurar_carpeta_salida(carpeta_salida: str | Path) -> Path:
	ruta = Path(carpeta_salida)
	ruta.mkdir(parents=True, exist_ok=True)
	return ruta


def exportar_figuras_a_pdf(rutas_imagenes: list[str | Path], ruta_pdf: str | Path) -> Path:
	ruta_destino = Path(ruta_pdf)
	if not rutas_imagenes:
		print('No hay imágenes para exportar al PDF.')
		return ruta_destino

	ruta_destino.parent.mkdir(parents=True, exist_ok=True)
	with PdfPages(ruta_destino) as pdf:
		for ruta_imagen in rutas_imagenes:
			imagen = plt.imread(ruta_imagen)
			figura = plt.figure(figsize=(11.69, 8.27))
			plt.imshow(imagen)
			plt.axis('off')
			pdf.savefig(figura, bbox_inches='tight')
			plt.close(figura)
	return ruta_destino


def crear_zip_resultados(carpeta_salida: str | Path, nombre_zip: str = 'resultados_caracterizacion_zip') -> Path:
	carpeta_destino = Path(carpeta_salida)
	ruta_zip = carpeta_destino.parent / f'{nombre_zip}.zip'

	if ruta_zip.exists():
		ruta_zip.unlink()

	archivos_a_incluir = [
		ruta for ruta in sorted(carpeta_destino.iterdir())
		if ruta.is_file() and ruta.suffix.lower() != '.zip'
	]

	with zipfile.ZipFile(ruta_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as archivo_zip:
		for ruta_archivo in archivos_a_incluir:
			archivo_zip.write(ruta_archivo, arcname=ruta_archivo.name)

	return ruta_zip


def exportar_dataframe_cleaned_a_excel(
	df_cleaned: pd.DataFrame,
	ruta_salida: str | Path,
	formato_fecha_preferido: str = '%d/%m/%Y',
) -> Path:
	ruta_destino = Path(ruta_salida)
	ruta_destino.parent.mkdir(parents=True, exist_ok=True)
	df_exportacion = df_cleaned.copy()
	if 'Fecha de nacimiento' in df_exportacion.columns:
		df_exportacion['Fecha de nacimiento'] = df_exportacion['Fecha de nacimiento'].dt.strftime(formato_fecha_preferido)
	df_exportacion.to_excel(ruta_destino, index=False)
	return ruta_destino


def generar_salidas_finales(
	rutas_png: list[str | Path],
	ruta_pdf: str | Path,
	ruta_zip: str | Path,
	carpeta_fuente: str | Path,
) -> tuple[Path, Path]:
	ruta_pdf_final = exportar_figuras_a_pdf(rutas_png, ruta_pdf)
	carpeta = Path(carpeta_fuente)
	nombre_zip = Path(ruta_zip).stem
	ruta_zip_final = crear_zip_resultados(carpeta, nombre_zip=nombre_zip)
	return ruta_pdf_final, ruta_zip_final
