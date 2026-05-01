"""
Módulo de Visualización.

Se encarga de la configuración gráfica, generación de paletas de colores dinámicas,
y el renderizado de gráficas (KDE, barras combinadas y separadas) usando Matplotlib y Seaborn.
"""
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

# Definición de la identidad visual
COLOR_PRINCIPAL: Final[str] = '#E3000F'  # Rojo Univalle (Destacado)
COLOR_SECUNDARIO: Final[str] = '#FBBC04' # Amarillo/Naranja encendido
COLOR_TERCIARIO: Final[str] = '#9333EA' # Violeta alegre
COLOR_CUATERNARIO: Final[str] = '#1A73E8'   # Azul eléctrico
COLOR_QUINARIO: Final[str] = '#34A853'  # Verde vibrante


def configurar_estilo() -> None:
	"""
	Aplica configuraciones globales de estilo a Matplotlib y Seaborn.
	Asegura consistencia visual en todas las gráficas generadas.
	"""
	plt.style.use('seaborn-v0_8-whitegrid') # Estilo base limpio con cuadrícula tenue
	plt.rcParams['figure.figsize'] = (11, 7) # Tamaño por defecto A4 apaisado
	plt.rcParams['axes.titlesize'] = 14
	plt.rcParams['axes.labelsize'] = 11
	plt.rcParams['xtick.labelsize'] = 10
	plt.rcParams['ytick.labelsize'] = 10
	plt.rcParams['figure.dpi'] = 120
	plt.rcParams['savefig.dpi'] = 150
	
	# Suprimir advertencias futuras de librerías para no ensuciar la consola
	warnings.simplefilter(action='ignore', category=FutureWarning)


def guardar_figura(figura: plt.Figure, ruta_archivo: str | Path) -> None:
	"""
	Guarda el objeto Figure de Matplotlib en disco, gestionando la creación
	de directorios si no existen.

	Parámetros:
		figura (plt.Figure): Instancia de la figura a guardar.
		ruta_archivo (str | Path): Destino de la imagen.
	"""
	ruta_destino = Path(ruta_archivo)
	ruta_destino.parent.mkdir(parents=True, exist_ok=True)
	
	# bbox_inches='tight' recorta los márgenes en blanco excesivos
	figura.savefig(ruta_destino, bbox_inches='tight')
	plt.close(figura) # Liberar memoria crucial para procesamiento en batch


def obtener_paleta_colores(df_plot: pd.DataFrame, multianual: bool) -> dict | str | list:
	"""
	Genera y asigna una paleta de colores dinámicamente según los años presentes.
	El año más reciente siempre recibe el COLOR_PRINCIPAL (Rojo).

	Parámetros:
		df_plot (pd.DataFrame): DataFrame filtrado listo para graficar.
		multianual (bool): Indica si hay más de un año presente.

	Retorna:
		dict | str | list: Un diccionario {año: color} si es multianual, 
		                   o un string (color base) si no lo es.
	"""
	if not multianual:
		return COLOR_PRINCIPAL
		
	# Extraer y ordenar años para asignar siempre el rojo al último (más reciente)
	anios = sorted(df_plot['Año de análisis'].unique().tolist())
	paleta = {}
	colores_pasados = [COLOR_SECUNDARIO, COLOR_TERCIARIO, COLOR_CUATERNARIO, COLOR_QUINARIO]
	
	for idx, anio in enumerate(anios):
		# El último año de la lista ordenada se lleva el color corporativo principal
		color = COLOR_PRINCIPAL if anio == anios[-1] else colores_pasados[idx % len(colores_pasados)]
		# Guardamos en la paleta tanto el int como el str para evitar problemas de tipos en sns.countplot
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
	"""
	Acondiciona un DataFrame para ser graficado mediante conteos categóricos.
	Resuelve celdas vacías, gestiona respuestas de selección múltiple (expandiendo filas)
	y calcula el "Top N" de categorías.

	Parámetros:
		df (pd.DataFrame): Datos crudos procesados.
		columna (str): Nombre de la columna a tabular.
		max_categorias (int): Límite visual de barras a mostrar.
		valor_relleno_categorico (str): Texto a mostrar en celdas vacías.
		multiple_respuesta (bool): Si es True, hace split de la celda usando `separador`.
		separador (str): Delimitador para respuestas múltiples.
		ordenar_por_nombre (bool): Si es True, ordena semánticamente (ej: Estrato 1 al 6).

	Retorna:
		tuple[pd.DataFrame, list[str]]: DataFrame listo para Seaborn y el orden final de las categorías.
	"""
	df_plot = df.copy()
	
	if multiple_respuesta:
		import re
		df_plot[columna] = df_plot[columna].fillna(valor_relleno_categorico).astype(str)
		# Regex avanzado: Divide por separador PERO ignora los separadores que estén dentro de paréntesis
		sep_escaped = re.escape(separador)
		patron = rf'\s*{sep_escaped}\s*(?![^()]*\))'
		df_plot[columna] = df_plot[columna].str.split(patron, regex=True)
		# explode() multiplica las filas: si alguien responde "A, B", genera una fila para A y otra para B
		df_plot = df_plot.explode(columna)
		
	# Limpieza estándar de cadenas antes de tabular
	df_plot[columna] = (
		df_plot[columna]
		.fillna(valor_relleno_categorico)
		.astype(str)
		.str.strip()
		.str.replace(r'\.0$', '', regex=True) # Elimina ceros decimales residuales de pandas (.0)
		.replace('', valor_relleno_categorico)
	)

	# Subrutina para agregar saltos de línea y evitar que las etiquetas tapen el gráfico
	def _envolver_texto(t):
		if t == valor_relleno_categorico:
			return t
		return "\n".join(textwrap.wrap(str(t), width=80))

	df_plot[columna] = df_plot[columna].apply(_envolver_texto)
	
	# Determinación del Top N y ordenamiento
	if ordenar_por_nombre:
		# Ordenamiento inteligente (sort_key): Si la cadena empieza por un número (ej: Estrato "1"),
		# lo convierte a float y ordena numéricamente. Si no, ordena alfabéticamente.
		def sort_key(x):
			try:
				return (0, float(x))
			except ValueError:
				return (1, x)

		top_categorias = sorted(df_plot[columna].unique().tolist(), key=sort_key)
		# Garantizamos que el valor "Sin dato" siempre quede al final visualmente
		if valor_relleno_categorico in top_categorias:
			top_categorias.remove(valor_relleno_categorico)
			top_categorias.append(valor_relleno_categorico)
		
		top_categorias = top_categorias[:max_categorias]
	else:
		# Ordenamiento por frecuencia (Mayor a menor)
		counts = df_plot[columna].value_counts()
		top_categorias = counts.head(max_categorias).index.tolist()
	
	# Filtramos el dataframe final dejando solo el Top N seleccionado
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
	"""
	Orquesta la creación de una gráfica de barras de conteo absoluto, 
	soportando automáticamente el desglose multianual.

	Parámetros:
		df (pd.DataFrame): Datos procesados.
		columna (str): Variable a graficar.
		titulo (str): Título visible del gráfico.
		ruta_salida (str | Path): Dónde se guardará el .png.
		max_categorias (int): Top máximo a pintar.
		valor_relleno_categorico (str): Etiqueta para vacíos.
		orientacion (str): 'h' para barras horizontales, 'v' para verticales.
		multiple_respuesta (bool): Indica si la columna tiene respuestas delimitadas por coma.
		ordenar_por_nombre (bool): Fuerza el ordenamiento semántico/numérico sobre el frecuencial.

	Retorna:
		Path: La ruta del archivo guardado.
	"""
	configurar_estilo()
	df_plot, orden = preparar_dataframe_categorico(
		df, columna, max_categorias, valor_relleno_categorico, multiple_respuesta, ordenar_por_nombre=ordenar_por_nombre
	)

	figura, eje = plt.subplots()
	# Detectar si la data tiene múltiples años para usar "hue" en seaborn
	multianual = 'Año de análisis' in df_plot.columns and df_plot['Año de análisis'].nunique() > 1
	paleta = obtener_paleta_colores(df_plot, multianual)

	if multianual:
		# sns.countplot divide automáticamente la categoría por año gracias a `hue`
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

	# Etiquetas dinámicas dependiendo de la orientación y el tipo de respuesta
	label_cantidad = 'Cantidad de registros' + ('/opciones' if multiple_respuesta else '')
	if orientacion == 'h':
		eje.set_xlabel(label_cantidad)
		eje.set_ylabel('Categoría')
	else:
		eje.set_ylabel(label_cantidad)
		eje.set_xlabel('Categoría')
		plt.xticks(rotation=45, ha='right')

	# Agrega los números precisos sobre/al lado de cada barra
	for container in eje.containers:
		eje.bar_label(container, padding=3, fmt='%.0f', fontsize=9)

	if multianual:
		# Si la leyenda interfiere con el gráfico, se mueve hacia la derecha
		sns.move_legend(eje, "upper right", bbox_to_anchor=(1.15, 1))

	figura.tight_layout()
	ruta_destino = Path(ruta_salida)
	guardar_figura(figura, ruta_destino)
	return ruta_destino


def generar_grafica_kde_edades(
	df: pd.DataFrame,
	ruta_salida: str | Path,
) -> Path:
	"""
	Genera una curva de densidad Kernel (KDE) para ilustrar la distribución continua de edades.
	Si el dataset es multianual, solapa múltiples campanas e incluye la media en la leyenda.

	Parámetros:
		df (pd.DataFrame): Datos limpios (se asume que existe la columna 'Edad').
		ruta_salida (str | Path): Archivo destino.

	Retorna:
		Path: Ruta final del gráfico generado.
	"""
	configurar_estilo()
	figura, eje = plt.subplots(figsize=(10, 6))

	multianual = 'Año de análisis' in df.columns and df['Año de análisis'].nunique() > 1
	df_plot = df.dropna(subset=['Edad']).copy()
	# Forzar tipo numérico y descartar anomalías
	df_plot['Edad'] = pd.to_numeric(df_plot['Edad'], errors='coerce').dropna()

	if df_plot.empty:
		# Fallback de gracia si la columna existe pero está toda en blanco
		eje.text(0.5, 0.5, 'Sin datos de edad', ha='center', va='center')
		guardar_figura(figura, ruta_salida)
		return Path(ruta_salida)

	paleta = obtener_paleta_colores(df_plot, multianual)

	if multianual:
		# Para aportar más valor, se calcula el promedio por año y se incrusta en la leyenda
		medias = df_plot.groupby('Año de análisis')['Edad'].mean()
		anios_originales = sorted(medias.index.tolist())
		
		# Generamos un mapeo: 2024 -> "2024 (Media de edad=23.5)"
		mapa_nombres = {
			anio: f"{anio} (Media de edad={medias[anio]:.1f})" 
			for anio in anios_originales
		}
		hue_order = [mapa_nombres[a] for a in anios_originales]
		
		df_plot['Año de análisis'] = df_plot['Año de análisis'].map(mapa_nombres)
		
		# Re-generar paleta usando el nuevo texto con medias
		paleta_con_media = obtener_paleta_colores(df_plot, multianual)

		sns.kdeplot(
			data=df_plot,
			x='Edad',
			hue='Año de análisis',
			hue_order=hue_order,
			fill=True,
			common_norm=False, # Evita que las curvas de años diferentes colapsen en altura
			alpha=0.4,
			linewidth=2,
			palette=paleta_con_media,
			ax=eje
		)
		eje.set_title('Distribución de densidad de Edades (Comparativo multianual)')
		sns.move_legend(eje, "upper right")
	else:
		# Comportamiento estándar mono-anual
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
	"""
	Toma un DataFrame con métricas de calidad y lo convierte en una imagen PNG plana.

	Parámetros:
		df_resumen (pd.DataFrame): DataFrame tabulado listo para impresión visual.
		ruta_salida (str | Path): Archivo destino.
		titulo (str): Encabezado de la imagen.

	Retorna:
		Path: Ruta de la tabla imagen guardada.
	"""
	configurar_estilo()
	# Cálculo de altura dinámica para no achatar tablas con muchas filas
	figura, eje = plt.subplots(figsize=(10, max(2.5, len(df_resumen) * 0.6)))
	eje.axis('off') # Se borra todo el lienzo tradicional (ejes xy)
	
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
	"""
	Punto de entrada principal para generar todas las gráficas agrupadas o comparativas
	(combinadas) según el catálogo predefinido. 

	Si existen varios años, crea diagramas de barras superpuestos.

	Parámetros:
		df_cleaned (pd.DataFrame): Data consolidada y limpia.
		resumen_calidad (pd.DataFrame): Datos de QA para pintar la primera imagen resumen.
		carpeta_salida (str | Path): Directorio raíz destino.
		graficas_activas (list[str] | None): Lista opcional para filtrar cuáles gráficas generar.
		max_categorias (int): Top para tabulados.
		valor_relleno_categorico (str): String por defecto de nulos.

	Retorna:
		list[Path]: Rutas de todas las imágenes generadas.
	"""
	carpeta_destino = Path(carpeta_salida)
	carpeta_destino.mkdir(parents=True, exist_ok=True)
	rutas_generadas: list[Path] = []

	# Catálogo maestro. Estructura: (Tipo_Generador, Columna_Origen, Titulo, Nombre_Archivo, Orientacion)
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

	# 1. El primer paso siempre es crear la tabla de resumen de calidad
	ruta_tabla = generar_tabla_resumen_como_imagen(resumen_calidad, carpeta_destino / 'resumen_calidad.png')
	rutas_generadas.append(ruta_tabla)

	# 2. Iterar sobre el catálogo y delegar la renderización a la función correcta
	for clave, cfg in CATALOGO_COMBINADAS.items():
		if graficas_activas and clave not in graficas_activas:
			continue
			
		tipo = cfg[0]
		ruta_archivo = carpeta_destino / cfg[3] if len(cfg) >= 4 else carpeta_destino / f'{clave}.png'
		
		# Proteger cada generación con un try/except general.
		# Así, si falla (e.g. columna eliminada en el dataset original), el reporte PDF
		# sigue creándose con el resto de gráficas funcionales.
		try:
			if tipo == 'kde':
				rutas_generadas.append(generar_grafica_kde_edades(df_cleaned, ruta_archivo))
			elif tipo == 'bar':
				col = cfg[1]
				tit = cfg[2]
				ori = cfg[4]
				if col in df_cleaned.columns:
					# Variables ordinales puras (estrato, semestre) siempre van ordenadas por nombre, no frecuencia
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
	"""
	Renderiza una variable categórica pero, a diferencia de la combinada,
	crea un archivo de imagen *distinto* y *aislado* para cada año, 
	recalculando el Top N específico de ese período.

	Parámetros:
		df (pd.DataFrame): Datos limpios.
		columna (str): Variable a graficar (ej: "Barrio").
		titulo (str): Encabezado de la imagen.
		ruta_salida (str | Path): Ruta base (se le concatenará el sufijo _2024, etc).
		max_categorias (int): Límite visual de barras a mostrar por gráfica.
		valor_relleno_categorico (str): Etiqueta para vacíos.
		multiple_respuesta (bool): Indica si hay comas o separadores en la respuesta.
		ordenar_por_nombre (bool): Si ordena alfabéticamente/numéricamente en lugar de frecuencialmente.

	Retorna:
		list[Path]: Lista de rutas de los gráficos de barras generados.
	"""
	configurar_estilo()
	rutas_salida = []
	
	# Usamos un paso global solo para detectar qué años existen y la paleta de colores global
	df_plot_global, _ = preparar_dataframe_categorico(
		df, columna, max_categorias, valor_relleno_categorico, multiple_respuesta, ordenar_por_nombre=ordenar_por_nombre
	)

	multianual = 'Año de análisis' in df_plot_global.columns and df_plot_global['Año de análisis'].nunique() > 1

	if multianual:
		anios = sorted(df_plot_global['Año de análisis'].unique())
		paleta = obtener_paleta_colores(df_plot_global, multianual)
		
		# Bucle iterativo: Filtramos dataframe por año y generamos figura separada
		for anio in anios:
			df_anio = df[df['Año de análisis'] == anio].copy()
			# Calculamos las categorías TOP específicamente en este subconjunto de datos (comportamiento "local")
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
			
			# Alterar nombre de archivo insertando el año
			ruta_base = Path(ruta_salida)
			ruta_año = ruta_base.parent / f"{ruta_base.stem}_{anio}{ruta_base.suffix}"
			guardar_figura(figura, ruta_año)
			rutas_salida.append(ruta_año)
	else:
		# Comportamiento tradicional sin división anual
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
	"""
	Itera sobre el catálogo de gráficas separadas y desencadena la renderización.
	Este bloque es ideal para variables con altísima cardinalidad (Ej: Barrios, Ciudades)
	donde un gráfico combinado sería incomprensible visualmente.

	Parámetros:
		df_cleaned (pd.DataFrame): Base consolidada.
		carpeta_salida (str | Path): Carpeta destino.
		graficas_activas (list[str] | None): Filtro opcional.
		max_categorias (int): Top visible.
		valor_relleno_categorico (str): Texto default para vacíos.

	Retorna:
		list[Path]: Lista plana de rutas creadas (pueden ser muchas más que en combinadas 
		            debido a la multiplicación por año).
	"""
	carpeta_destino = Path(carpeta_salida)
	carpeta_destino.mkdir(parents=True, exist_ok=True)
	rutas_generadas: list[Path] = []

	# (Columna_Data, Titulo, ArchivoBase, Requiere_Multiple_Respuesta)
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
		
		# Protección ante la posible ausencia de columnas en DataFrames
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
