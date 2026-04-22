from __future__ import annotations

import warnings
import textwrap
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from .processing import VALOR_RELLENO_CATEGORICO

COLOR_PRINCIPAL: Final[str] = '#E3000F'  # Rojo Univalle (Destacado)
COLOR_SECUNDARIO: Final[str] = '#FBBC04' # Amarillo/Naranja encendido
COLOR_TERCIARIO: Final[str] = '#9333EA' # Violeta alegre
COLOR_CUATERNARIO: Final[str] = '#1A73E8'   # Azul eléctrico
COLOR_QUINARIO: Final[str] = '#34A853'  # Verde vibrante

# Opciones extra (Paletas alternativas):
# - Pastel: ['#FF9AA2', '#FFB7B2', '#FFDAC1', '#E2F0CB']
# - Neon:   ['#00F5D4', '#00BBF9', '#F15BB5', '#9B5DE5']



def configurar_estilo() -> None:
	plt.style.use('seaborn-v0_8-whitegrid')
	plt.rcParams['figure.figsize'] = (11, 7)
	plt.rcParams['axes.titlesize'] = 14
	plt.rcParams['axes.labelsize'] = 11
	plt.rcParams['xtick.labelsize'] = 10
	plt.rcParams['ytick.labelsize'] = 10
	plt.rcParams['figure.dpi'] = 120
	plt.rcParams['savefig.dpi'] = 150
	# Suppress specific future warnings
	warnings.simplefilter(action='ignore', category=FutureWarning)


def guardar_figura(figura: plt.Figure, ruta_archivo: str | Path) -> None:
	ruta_destino = Path(ruta_archivo)
	ruta_destino.parent.mkdir(parents=True, exist_ok=True)
	figura.savefig(ruta_destino, bbox_inches='tight')
	plt.close(figura)


def obtener_paleta_colores(df_plot: pd.DataFrame, multianual: bool) -> dict | str | list:
	"""Asigna el color principal al año más reciente, y tonos grises/azules a los pasados."""
	if not multianual:
		return COLOR_PRINCIPAL
		
	anios = sorted(df_plot['Año de análisis'].unique().tolist())
	paleta = {}
	colores_pasados = [COLOR_SECUNDARIO, COLOR_TERCIARIO, COLOR_CUATERNARIO, COLOR_QUINARIO]
	for idx, anio in enumerate(anios):
		color = COLOR_PRINCIPAL if anio == anios[-1] else colores_pasados[idx % len(colores_pasados)]
		paleta[anio] = color
		paleta[str(anio)] = color
	return paleta


def preparar_dataframe_categorico(
	df: pd.DataFrame,
	columna: str,
	max_categorias: int = 20,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
	multiple_respuesta: bool = False,
	separador: str = ',',
	ordenar_por_nombre: bool = False
) -> tuple[pd.DataFrame, list[str]]:
	df_plot = df.copy()
	
	if multiple_respuesta:
		import re
		# Expandimos filas si la columna tiene valores como "a, b, c"
		df_plot[columna] = df_plot[columna].fillna(valor_relleno_categorico).astype(str)
		# Dividimos por separador (evitando separadores dentro de paréntesis) y expandimos a múltiples filas
		sep_escaped = re.escape(separador)
		patron = rf'\s*{sep_escaped}\s*(?![^()]*\))'
		df_plot[columna] = df_plot[columna].str.split(patron, regex=True)
		df_plot = df_plot.explode(columna)
		
	df_plot[columna] = (
		df_plot[columna]
		.fillna(valor_relleno_categorico)
		.astype(str)
		.str.strip()
		.str.replace(r'\.0$', '', regex=True)
		.replace('', valor_relleno_categorico)
	)

	# Función para envolver texto largo sin perder información
	def _envolver_texto(t):
		if t == valor_relleno_categorico:
			return t
		return "\n".join(textwrap.wrap(str(t), width=80))

	df_plot[columna] = df_plot[columna].apply(_envolver_texto)
	
	# Determinar el top de categorías.
	if ordenar_por_nombre:
		def sort_key(x):
			try:
				return (0, float(x))
			except ValueError:
				return (1, x)

		# Ordenar alfabéticamente/numéricamente de forma inteligente
		top_categorias = sorted(df_plot[columna].unique().tolist(), key=sort_key)
		# Asegurar que el valor de relleno quede al final
		if valor_relleno_categorico in top_categorias:
			top_categorias.remove(valor_relleno_categorico)
			top_categorias.append(valor_relleno_categorico)
		# Limitar a max_categorias si es necesario
		top_categorias = top_categorias[:max_categorias]
	else:
		# Ordenar por frecuencia (comportamiento original)
		counts = df_plot[columna].value_counts()
		top_categorias = counts.head(max_categorias).index.tolist()
	
	df_plot = df_plot[df_plot[columna].isin(top_categorias)]
	return df_plot, top_categorias


def generar_grafica_barras(
	df: pd.DataFrame,
	columna: str,
	titulo: str,
	ruta_salida: str | Path,
	max_categorias: int = 20,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
	orientacion: str = 'h',
	multiple_respuesta: bool = False,
	ordenar_por_nombre: bool = False
) -> Path:
	configurar_estilo()
	df_plot, orden = preparar_dataframe_categorico(
		df, columna, max_categorias, valor_relleno_categorico, multiple_respuesta, ordenar_por_nombre=ordenar_por_nombre
	)

	figura, eje = plt.subplots()
	multianual = 'Año de análisis' in df_plot.columns and df_plot['Año de análisis'].nunique() > 1
	paleta = obtener_paleta_colores(df_plot, multianual)

	if multianual:
		sns.countplot(
			data=df_plot,
			y=columna if orientacion == 'h' else None,
			x=columna if orientacion == 'v' else None,
			hue='Año de análisis',
			order=orden,
			ax=eje,
			palette=paleta
		)
		eje.set_title(f"{titulo} (Comparativo por Año)")
	else:
		sns.countplot(
			data=df_plot,
			y=columna if orientacion == 'h' else None,
			x=columna if orientacion == 'v' else None,
			order=orden,
			ax=eje,
			color=paleta
		)
		eje.set_title(titulo)

	if orientacion == 'h':
		eje.set_xlabel('Cantidad de registros' + ('/opciones' if multiple_respuesta else ''))
		eje.set_ylabel('Categoría')
	else:
		eje.set_ylabel('Cantidad de registros' + ('/opciones' if multiple_respuesta else ''))
		eje.set_xlabel('Categoría')
		# Rotar X ticks si hay muchas
		plt.xticks(rotation=45, ha='right')

	for container in eje.containers:
		eje.bar_label(container, padding=3, fmt='%.0f', fontsize=9)

	# Si es multi de barras agrupadas o algo con legend repetitiva
	if multianual:
		sns.move_legend(eje, "upper right", bbox_to_anchor=(1.15, 1))

	figura.tight_layout()
	ruta_destino = Path(ruta_salida)
	guardar_figura(figura, ruta_destino)
	return ruta_destino


def generar_grafica_kde_edades(
	df: pd.DataFrame,
	ruta_salida: str | Path,
) -> Path:
	configurar_estilo()
	figura, eje = plt.subplots(figsize=(10, 6))

	multianual = 'Año de análisis' in df.columns and df['Año de análisis'].nunique() > 1
	df_plot = df.dropna(subset=['Edad']).copy()
	df_plot['Edad'] = pd.to_numeric(df_plot['Edad'], errors='coerce').dropna()

	if df_plot.empty:
		# Dummy empty plot si no hay edades validas
		eje.text(0.5, 0.5, 'Sin datos de edad', ha='center', va='center')
		guardar_figura(figura, ruta_salida)
		return Path(ruta_salida)

	paleta = obtener_paleta_colores(df_plot, multianual)

	if multianual:
		# Calcular medias por año para la leyenda
		medias = df_plot.groupby('Año de análisis')['Edad'].mean()
		anios_originales = sorted(medias.index.tolist())
		
		# Crear el mapeo de nombres y el orden explícito de la leyenda
		mapa_nombres = {
			anio: f"{anio} (Media de edad={medias[anio]:.1f})" 
			for anio in anios_originales
		}
		hue_order = [mapa_nombres[a] for a in anios_originales]
		
		# Aplicamos el mapeo al dataframe
		df_plot['Año de análisis'] = df_plot['Año de análisis'].map(mapa_nombres)
		
		# Regeneramos paleta con los nuevos nombres para mantener consistencia de colores
		paleta_con_media = obtener_paleta_colores(df_plot, multianual)

		sns.kdeplot(
			data=df_plot,
			x='Edad',
			hue='Año de análisis',
			hue_order=hue_order,
			fill=True,
			common_norm=False,
			alpha=0.4,
			linewidth=2,
			palette=paleta_con_media,
			ax=eje
		)
		eje.set_title('Distribución de densidad de Edades (Comparativo multianual)')
		sns.move_legend(eje, "upper right")
	else:
		media_total = df_plot['Edad'].mean()
		sns.kdeplot(
			data=df_plot,
			x='Edad',
			fill=True,
			color=COLOR_PRINCIPAL,
			alpha=0.6,
			ax=eje,
			label=f'Población (μ={media_total:.1f})'
		)
		eje.set_title('Distribución de Edades')
		eje.legend()

	eje.set_xlabel('Edad')
	eje.set_ylabel('Densidad')
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


def generar_graficas_combinadas(
	df_cleaned: pd.DataFrame,
	resumen_calidad: pd.DataFrame,
	carpeta_salida: str | Path,
	graficas_activas: list[str] | None = None,
	max_categorias: int = 20,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
) -> list[Path]:
	carpeta_destino = Path(carpeta_salida)
	carpeta_destino.mkdir(parents=True, exist_ok=True)
	rutas_generadas: list[Path] = []

	# (Clave: (Tipo_Generador, Columna, Titulo, Nombre_Archivo, Orientacion, kwargs))
	CATALOGO_COMBINADAS = {
		'edad': ('kde', '', '', '00_distribucion_edades.png'),
		'estrato': ('bar', 'Estrato socioeconómico', 'Distribución por Estrato', '01_estrato_socioeconomico.png', 'v'),
		'zona_residencia': ('bar', 'Zona de residencia', 'Residencia Urbana vs Rural', '02_zona_residencia.png', 'v'),
		'estado_civil': ('bar', 'Estado civil', 'Estado civil de la población', '03_estado_civil.png', 'v'),
		'identidad_etnica': ('bar', 'Identidad étnica', 'Distribución de Identidad étnica', '04_identidad_etnica.png', 'h'),
		'grupo_poblacional': ('bar', 'Grupo poblacional', 'Pertenencia a grupos poblacionales', '05_grupo_poblacional.png', 'h'),
		'identidad_genero': ('bar', 'Identidad de género', 'Distribución de Identidad de género', '06_identidad_genero.png', 'h'),
		'expresion_genero': ('bar', 'Expresión de género', 'Diversidad en Expresión de género', '07_expresion_genero.png', 'h'),
		'orientacion_sexual': ('bar', 'Orientación sexual', 'Diversidad en Orientación sexual', '08_orientacion_sexual.png', 'h'),
		'cambio_di': ('bar', 'Cambio de nombre/sexo en D.I', 'Realizaron cambio legal en D.I', '09_cambio_di.png', 'v'),
		'asesoria_di': ('bar', 'Asesoría cambio D.I', 'Interés en recibir asesoría para D.I', '10_asesoria_di.png', 'v'),
		'estamento': ('bar', 'Estamento', 'Distribución por Estamento', '11_estamento.png', 'h'),
		'semestre': ('bar', 'Semestre académico', 'Distribución por Semestre Académico', '12_semestre_academico.png', 'v'),
		'ocupacion': ('bar', '¿Cuál es tu ocupación actual?', 'Ocupación principal actual', '13_ocupacion.png', 'h'),
		'acompanamiento': ('bar_multiple', '¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?', 'Tipos de acompañamiento recibido', '14_acompanamiento.png', 'h'),
		'enteraste': ('bar_multiple', 'Como te enteraste de Campus Diverso', 'Tasa de difusión de Campus Diverso', '15_enteraste.png', 'h'),
		'entidad_acompanamiento': ('bar', 'Entidad acompañamiento', 'Entidad del acompañamiento recibido', '25_entidad_acompanamiento.png', 'h'),
		'profesional_acompanante': ('bar', 'Profesional acompañante', 'Profesional que brindó el acompañamiento', '26_profesional_acompanante.png', 'h'),
		'origen_recursos': ('bar', '¿De donde provienen tus ingresos o recursos?', 'Origen de ingresos o recursos', '27_origen_recursos.png', 'h')
	}

	# Generar tabla
	ruta_tabla = generar_tabla_resumen_como_imagen(resumen_calidad, carpeta_destino / 'resumen_calidad.png')
	rutas_generadas.append(ruta_tabla)

	for clave, cfg in CATALOGO_COMBINADAS.items():
		if graficas_activas and clave not in graficas_activas:
			continue
			
		tipo = cfg[0]
		ruta_archivo = carpeta_destino / cfg[3] if len(cfg) >= 4 else carpeta_destino / f'{clave}.png'
		
		# Proteger cada generación con un try/except para que no rompa el flujo por una columna ausente/vacía
		try:
			if tipo == 'kde':
				rutas_generadas.append(generar_grafica_kde_edades(df_cleaned, ruta_archivo))
			elif tipo == 'bar':
				col = cfg[1]
				tit = cfg[2]
				ori = cfg[4]
				if col in df_cleaned.columns:
					# Estrato y semestre se ordenan por valor numérico implícito
					orden_nombre = (clave in ['estrato', 'semestre'])
					rutas_generadas.append(generar_grafica_barras(df_cleaned, col, tit, ruta_archivo, max_categorias, valor_relleno_categorico, ori, False, ordenar_por_nombre=orden_nombre))
			elif tipo == 'bar_multiple':
				col = cfg[1]
				tit = cfg[2]
				ori = cfg[4]
				if col in df_cleaned.columns:
					rutas_generadas.append(generar_grafica_barras(df_cleaned, col, tit, ruta_archivo, max_categorias, valor_relleno_categorico, ori, True))
		except Exception as e:
			print(f"Advertencia: No se pudo generar gráfica '{clave}': {e}")

	return rutas_generadas


def generar_grafica_separada_barras(
	df: pd.DataFrame,
	columna: str,
	titulo: str,
	ruta_salida: str | Path,
	max_categorias: int = 20,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
	multiple_respuesta: bool = False,
	ordenar_por_nombre: bool = False
) -> list[Path]:
	configurar_estilo()
	rutas_salida = []
	df_plot_global, _ = preparar_dataframe_categorico(
		df, columna, max_categorias, valor_relleno_categorico, multiple_respuesta, ordenar_por_nombre=ordenar_por_nombre
	)

	multianual = 'Año de análisis' in df_plot_global.columns and df_plot_global['Año de análisis'].nunique() > 1

	if multianual:
		anios = sorted(df_plot_global['Año de análisis'].unique())
		paleta = obtener_paleta_colores(df_plot_global, multianual)
		
		for anio in anios:
			df_anio = df[df['Año de análisis'] == anio].copy()
			df_plot, orden = preparar_dataframe_categorico(
				df_anio, columna, max_categorias, valor_relleno_categorico, multiple_respuesta, ordenar_por_nombre=ordenar_por_nombre
			)
			
			figura, eje = plt.subplots(figsize=(8, 5))
			if df_plot.empty:
				eje.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
			else:
				sns.countplot(
					data=df_plot,
					y=columna,
					order=orden,
					ax=eje,
					color=paleta.get(anio, COLOR_SECUNDARIO)
				)
				for container in eje.containers:
					eje.bar_label(container, padding=3, fmt='%.0f', fontsize=9)
					
			eje.set_title(f"{titulo} - {anio}")
			eje.set_xlabel('Cantidad de registros')
			eje.set_ylabel('')
			figura.tight_layout()
			
			ruta_base = Path(ruta_salida)
			ruta_año = ruta_base.parent / f"{ruta_base.stem}_{anio}{ruta_base.suffix}"
			guardar_figura(figura, ruta_año)
			rutas_salida.append(ruta_año)
	else:
		df_plot, orden = preparar_dataframe_categorico(
			df, columna, max_categorias, valor_relleno_categorico, multiple_respuesta, ordenar_por_nombre=ordenar_por_nombre
		)
		figura, eje = plt.subplots(figsize=(8, 5))
		if df_plot.empty:
			eje.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
		else:
			sns.countplot(
				data=df_plot,
				y=columna,
				order=orden,
				ax=eje,
				color=COLOR_PRINCIPAL
			)
			for container in eje.containers:
				eje.bar_label(container, padding=3, fmt='%.0f', fontsize=9)
		eje.set_title(titulo)
		eje.set_xlabel('Cantidad de registros')
		eje.set_ylabel('')
		figura.tight_layout()
		ruta_destino = Path(ruta_salida)
		guardar_figura(figura, ruta_destino)
		rutas_salida.append(ruta_destino)

	return rutas_salida


def generar_graficas_separadas(
	df_cleaned: pd.DataFrame,
	carpeta_salida: str | Path,
	graficas_activas: list[str] | None = None,
	max_categorias: int = 20,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
) -> list[Path]:
	carpeta_destino = Path(carpeta_salida)
	carpeta_destino.mkdir(parents=True, exist_ok=True)
	rutas_generadas: list[Path] = []

	CATALOGO_SEPARADAS = {
		'depto_nacimiento': ('Departamento de nacimiento', 'Top Departamentos de Nacimiento', '16_depto_nacimiento.png', False),
		'ciudad_nacimiento': ('Ciudad, municipio o corregimiento de nacimiento', 'Top Ciudades de Nacimiento', '17_ciudad_nacimiento.png', False),
		'ciudad_residencia': ('Ciudad, municipio o corregimiento de residencia', 'Top Ciudades de Residencia', '18_ciudad_residencia.png', False),
		'barrio_residencia': ('Barrio de residencia', 'Top Barrios de Residencia', '24_barrio_residencia.png', False),
		'impedimento_di': ('Impedimento cambio D.I', 'Impedimentos para cambio legal de D.I', '19_impedimento_di.png', False),
		'sede_universidad': ('Sede de la Universidad del Valle', 'Sede de la Universidad', '20_sede_universidad.png', False),
		'programa_academico': ('Nombre del programa académico', 'Top Programas Académicos', '21_programa_academico.png', False),
		'redes_apoyo': ('Redes de apoyo (Identifica ¿con quiénes/qué apoyos cuentas?)', 'Principales Redes de Apoyo', '22_redes_apoyo.png', True),
		'factores_riesgo': ('Factores de riesgo (identifica aquello que puede estar poniéndote en riesgo)', 'Principales Factores de Riesgo', '23_factores_riesgo.png', True)
	}

	for clave, cfg in CATALOGO_SEPARADAS.items():
		if graficas_activas and clave not in graficas_activas:
			continue
			
		col = cfg[0]
		tit = cfg[1]
		ruta_archivo = carpeta_destino / cfg[2]
		multi = cfg[3]
		
		try:
			if col in df_cleaned.columns:
				rutas_generadas.extend(
					generar_grafica_separada_barras(
						df_cleaned, col, tit, ruta_archivo, max_categorias, valor_relleno_categorico, multi, False
					)
				)
		except Exception as e:
			print(f"Advertencia: No se pudo generar gráfica separada '{clave}': {e}")

	return rutas_generadas
