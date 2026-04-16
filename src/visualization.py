from __future__ import annotations

from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from .processing import GRAFICAS_INICIALES, VALOR_RELLENO_CATEGORICO

COLOR_PRINCIPAL: Final[str] = '#1f4e79'
COLOR_SECUNDARIO: Final[str] = '#7aa6c2'


def configurar_estilo() -> None:
	plt.style.use('seaborn-v0_8-whitegrid')
	plt.rcParams['figure.figsize'] = (10, 6)
	plt.rcParams['axes.titlesize'] = 14
	plt.rcParams['axes.labelsize'] = 11
	plt.rcParams['xtick.labelsize'] = 10
	plt.rcParams['ytick.labelsize'] = 10
	plt.rcParams['figure.dpi'] = 120
	plt.rcParams['savefig.dpi'] = 150


def guardar_figura(figura: plt.Figure, ruta_archivo: str | Path) -> None:
	ruta_destino = Path(ruta_archivo)
	ruta_destino.parent.mkdir(parents=True, exist_ok=True)
	figura.savefig(ruta_destino, bbox_inches='tight')
	plt.close(figura)


def preparar_dataframe_categorico(
	df: pd.DataFrame,
	columna: str,
	max_categorias: int = 10,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
) -> tuple[pd.DataFrame, list[str]]:
	df_plot = df.copy()
	df_plot[columna] = (
		df_plot[columna]
		.fillna(valor_relleno_categorico)
		.astype(str)
		.str.strip()
		.replace('', valor_relleno_categorico)
	)
	top_categorias = df_plot[columna].value_counts().head(max_categorias).index.tolist()
	df_plot = df_plot[df_plot[columna].isin(top_categorias)]
	return df_plot, top_categorias


def generar_grafica_barras_horizontales(
	df: pd.DataFrame,
	columna: str,
	titulo: str,
	ruta_salida: str | Path,
	max_categorias: int = 10,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
	color_principal: str = COLOR_PRINCIPAL,
) -> Path:
	configurar_estilo()
	df_plot, orden = preparar_dataframe_categorico(df, columna, max_categorias, valor_relleno_categorico)

	figura, eje = plt.subplots()
	multianual = 'Año de análisis' in df_plot.columns and df_plot['Año de análisis'].nunique() > 1

	if multianual:
		sns.countplot(
			data=df_plot,
			y=columna,
			hue='Año de análisis',
			order=orden,
			ax=eje,
			palette='viridis'
		)
		eje.set_title(f"{titulo} (Comparativo por Año)")
	else:
		sns.countplot(
			data=df_plot,
			y=columna,
			order=orden,
			ax=eje,
			color=color_principal
		)
		eje.set_title(titulo)

	eje.set_xlabel('Cantidad de registros')
	eje.set_ylabel('Categoría')

	for container in eje.containers:
		eje.bar_label(container, padding=3, fmt='%.0f')

	figura.tight_layout()
	ruta_destino = Path(ruta_salida)
	guardar_figura(figura, ruta_destino)
	return ruta_destino


def generar_histograma_edades(
	df: pd.DataFrame,
	ruta_salida: str | Path,
	color_secundario: str = COLOR_SECUNDARIO,
) -> Path:
	configurar_estilo()
	figura, eje = plt.subplots()

	multianual = 'Año de análisis' in df.columns and df['Año de análisis'].nunique() > 1

	if multianual:
		sns.histplot(
			data=df,
			x='Edad',
			hue='Año de análisis',
			multiple='dodge',
			bins=10,
			ax=eje,
			palette='viridis',
			shrink=0.8
		)
		eje.set_title('Distribución de edades (Comparativo por Año)')
	else:
		edades = df['Edad'].dropna()
		sns.histplot(
			data=df,
			x='Edad',
			bins=min(10, max(5, edades.nunique() if not edades.empty else 5)),
			ax=eje,
			color=color_secundario,
			edgecolor='white'
		)
		eje.set_title('Distribución de edades')

	eje.set_xlabel('Edad')
	eje.set_ylabel('Cantidad de registros')
	figura.tight_layout()
	ruta_destino = Path(ruta_salida)
	guardar_figura(figura, ruta_destino)
	return ruta_destino

def generar_tabla_resumen_como_imagen(
	df_resumen: pd.DataFrame,
	ruta_salida: str | Path,
	titulo: str = 'Resumen de calidad de la base',
) -> Path:
	configurar_estilo()
	figura, eje = plt.subplots(figsize=(10, max(2.5, len(df_resumen) * 0.6)))
	eje.axis('off')
	tabla = eje.table(
		cellText=df_resumen.values,
		colLabels=df_resumen.columns,
		cellLoc='left',
		loc='center',
	)
	tabla.auto_set_font_size(False)
	tabla.set_fontsize(10)
	tabla.scale(1, 1.5)
	figura.suptitle(titulo, fontsize=14)
	figura.tight_layout()
	ruta_destino = Path(ruta_salida)
	guardar_figura(figura, ruta_destino)
	return ruta_destino


def generar_salidas_iniciales(
	df_cleaned: pd.DataFrame,
	resumen_calidad: pd.DataFrame,
	carpeta_salida: str | Path,
	graficas_iniciales: list[str] | None = None,
	max_categorias: int = 10,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
) -> list[Path]:
	carpeta_destino = Path(carpeta_salida)
	carpeta_destino.mkdir(parents=True, exist_ok=True)
	rutas_generadas: list[Path] = []

	catalogo = {
		'identidad_genero': ('Identidad de género', 'Distribución por identidad de género', '01_identidad_genero.png'),
		'orientacion_sexual': ('Orientación sexual', 'Distribución por orientacion sexual', '02_orientacion_sexual.png'),
		'estamento': ('Estamento', 'Distribución por estamento', '03_estamento.png'),
		'sede': ('Sede de la Universidad del Valle', 'Distribución por sede', '04_sede.png'),
		'estrato': ('Estrato socioeconómico', 'Distribución por estrato socioeconómico', '05_estrato.png'),
	}

	for clave in graficas_iniciales or GRAFICAS_INICIALES:
		if clave in catalogo:
			columna, titulo, nombre_archivo = catalogo[clave]
			ruta_archivo = carpeta_destino / nombre_archivo
			rutas_generadas.append(
				generar_grafica_barras_horizontales(
					df_cleaned,
					columna,
					titulo,
					ruta_archivo,
					max_categorias=max_categorias,
					valor_relleno_categorico=valor_relleno_categorico,
				)
			)
		elif clave == 'edad':
			ruta_archivo = carpeta_destino / '06_edades.png'
			rutas_generadas.append(generar_histograma_edades(df_cleaned, ruta_archivo))

	ruta_tabla = generar_tabla_resumen_como_imagen(
		resumen_calidad,
		carpeta_destino / '00_resumen_calidad.png',
	)
	rutas_generadas.insert(0, ruta_tabla)
	return rutas_generadas
