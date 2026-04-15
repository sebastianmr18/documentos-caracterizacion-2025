from __future__ import annotations

import difflib
import re
import unicodedata
from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd

VALOR_RELLENO_CATEGORICO = 'Sin dato'

COLUMNAS_EXACTAS_RAW = [
	'Marca temporal',
	'Dirección de correo electrónico',
	'¿Acepta el almacenamiento y tratamiento de sus datos personales  de acuerdo con las políticas institucionales?',
	'Fecha de diligenciamiento',
	'¿Cómo te gusta ser llamado/a/e?  (puedes escribir tu nombre identitario o de preferencia, NO necesariamente el nombre legal)',
	'Nombres y apellidos (como aparecen en el documento de identificación)',
	'Tipo de documento de identidad',
	'Número de documento de identidad (Solo el número sin puntos, comas o espacios)',
	'Fecha de nacimiento',
	'Estrato socioeconómico',
	'Ciudad, municipio o corregimiento de nacimiento',
	'Departamento de nacimiento',
	'País de nacimiento',
	'Ciudad, municipio o corregimiento de residencia',
	'Zona de residencia',
	'Dirección de residencia',
	'Barrio de residencia',
	'Comuna a la que pertenece su barrio (si su municipio tiene comunas)',
	'Teléfono fijo o celular',
	'Estado civil',
	'Auto-reconocimiento étnico (Hace referencia al sentido de pertenencia que expresa una persona frente a un colectivo, de acuerdo con su identidad y formas de interactuar en y con el mundo) ',
	'¿A qué grupo poblacional perteneces?',
	'¿Cuáles son tus pronombres?',
	'¿Cuál es tu identidad de géneros? ( es decir, ¿Cómo te vives, sientes, percibes, etc.?)',
	'Expresión de género (¿Cuál es tu apariencia?/¿cómo te muestras al mundo?)',
	'¿Cuál es tu orientación sexual?  es decir,  ¿Quién/es te gusta(n) o  atrae(n)?',
	'¿Has realizado cambio de nombre y/o del componente sexo en tu documento de identidad?',
	'Si la respuesta a la pregunta anterior fue "NO" o sólo cambiaste uno de los dos componentes, ¿Qué te impidió realizar el cambio?',
	'Por favor indícanos si te gustaría recibir orientación para realizar el cambio de nombre y/o sexo en tu documento de identidad.',
	'¿Perteneces a la Universidad del Valle?',
	'Estamento',
	'Sede de la universidad a la que pertenece',
	'Nombre del programa académico',
	'Código de estudiante (escribir sin los dos primeros dígitos EJ: 1424550)',
	'Semestre académico',
	'¿Cuál es tu ocupación actual?',
	'¿Tienes EPS?',
	'¿Cuál es tu EPS?',
	'¿Qué régimen es tu EPS?',
	'Si eres empleado/a/e o independiente ¿A qué te dedicas específicamente?',
	'¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?',
	'¿En qué tipo de entidad recibiste el acompañamiento?',
	'¿Qué profesional le brindó la atención?',
	'En una escala de 1 a 5, siendo 1 muy desagradable y 5 muy agradable, califica el acompañamiento/orientación que recibiste (si no has recibido ningún tipo de orientación omite esta pregunta)',
	'Por favor cuéntanos por qué elegiste la opción anterior para calificar la experiencia de acompañamiento (opcional)',
	'¿Qué tipo de actividades sueles realizar en tu tiempo libre? ',
	'¿Qué actividades específicas realizas en tu tiempo libre?',
	'¿Cuál(es) es/son tu(s) fuente(s) de ingresos?',
	'¿Con quién(es) vives?',
	'En una escala del  1 al 5, ¿Cómo consideras que es la relación con tu familia?',
	'Por favor indicar nombre de una persona de confianza o representante legal en caso de no poder establecer contacto contigo',
	'Por favor, indícanos el relacionamiento/vínculo que tienes con esta persona referida como de  confianza o representante legal',
	'Por favor indicar el número de contacto (teléfono fijo o celular) del representante legal o la persona de confianza registrada en la pregunta anterior en caso de no poder establecer contacto contigo',
	'Redes de apoyo (Identifica con quiénes o con qué apoyos cuentas)',
	'Factores de riesgo (identifica aquello que puede estar poniéndote en riesgo)',
	'¿Tienes alguna creencia religiosa? ¿Cuál es?',
	'Si respondiste "Si" a la pregunta anterior, ¿Cuál es tu creencia?',
	'Para el encuentro inicial con Campus Diverso ¿te gustaría que tuviera lugar con un(a) profesional de un área específica? Esta opción está sujeta a la disponibilidad de les profesionales.',
	'¿Cómo te enteraste de los servicios de Campus Diverso?',
	'Déjanos, por favor, tus comentarios, sugerencias y observaciones. Para Campus Diverso es muy importante conocer si tienes inquietudes o aportes adicionales.',
	'Unnamed: 60',
	'Unnamed: 61',
	'Convención',
]

COLUMNAS_OBLIGATORIAS_RAW = [
	'Fecha de diligenciamiento',
	'Fecha de nacimiento',
	'Estrato socioeconómico',
	'Ciudad, municipio o corregimiento de nacimiento',
	'Departamento de nacimiento',
	'País de nacimiento',
	'Ciudad, municipio o corregimiento de residencia',
	'Zona de residencia',
	'Barrio de residencia',
	'Estado civil',
	'Auto-reconocimiento étnico (Hace referencia al sentido de pertenencia que expresa una persona frente a un colectivo, de acuerdo con su identidad y formas de interactuar en y con el mundo) ',
	'¿A qué grupo poblacional perteneces?',
	'¿Cuál es tu identidad de géneros? ( es decir, ¿Cómo te vives, sientes, percibes, etc.?)',
	'Expresión de género (¿Cuál es tu apariencia?/¿cómo te muestras al mundo?)',
	'¿Cuál es tu orientación sexual?  es decir,  ¿Quién/es te gusta(n) o  atrae(n)?',
	'¿Has realizado cambio de nombre y/o del componente sexo en tu documento de identidad?',
	'Si la respuesta a la pregunta anterior fue "NO" o sólo cambiaste uno de los dos componentes, ¿Qué te impidió realizar el cambio?',
	'Por favor indícanos si te gustaría recibir orientación para realizar el cambio de nombre y/o sexo en tu documento de identidad.',
	'¿Perteneces a la Universidad del Valle?',
	'Estamento',
	'Sede de la universidad a la que pertenece',
	'Nombre del programa académico',
	'Semestre académico',
	'¿Cuál es tu ocupación actual?',
	'Si eres empleado/a/e o independiente ¿A qué te dedicas específicamente?',
	'¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?',
	'¿En qué tipo de entidad recibiste el acompañamiento?',
	'¿Qué profesional le brindó la atención?',
	'¿Cuál(es) es/son tu(s) fuente(s) de ingresos?',
	'¿Con quién(es) vives?',
	'Redes de apoyo (Identifica con quiénes o con qué apoyos cuentas)',
	'Factores de riesgo (identifica aquello que puede estar poniéndote en riesgo)',
	'¿Tienes alguna creencia religiosa? ¿Cuál es?',
	'¿Cómo te enteraste de los servicios de Campus Diverso?',
]

COLUMNAS_FINAL_CLEANED = [
	'Año de análisis',
	'Fecha de nacimiento',
	'Edad',
	'Estrato socioeconómico',
	'Ciudad, municipio o corregimiento de nacimiento',
	'Departamento de nacimiento',
	'País de nacimiento',
	'Ciudad, municipio o corregimiento de residencia',
	'Zona de residencia',
	'Barrio de residencia',
	'Estado civil',
	'Identidad étnica',
	'Grupo poblacional',
	'Identidad de género',
	'Expresión de género',
	'Orientación sexual',
	'Cambio de nombre/sexo en D.I',
	'Impedimento cambio D.I',
	'Asesoría cambio D.I',
	'Pertenencia a la U',
	'Estamento',
	'Sede de la Universidad del Valle',
	'Nombre del programa académico',
	'Semestre académico',
	'¿Cuál es tu ocupación actual?',
	'Si eres empleado/a/e o independiente ¿A qué te dedicas específicamente?',
	'¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?',
	'Entidad acompañamiento',
	'Profesional acompañante',
	'¿De donde provienen tus ingresos o recursos?',
	'¿Con quién(es) vives?',
	'Redes de apoyo (Identifica ¿con quiénes/qué apoyos cuentas?)',
	'Factores de riesgo (identifica aquello que puede estar poniéndote en riesgo)',
	'¿Tienes alguna creencia religiosa? ¿Cuál es?',
	'Como te enteraste de Campus Diverso',
]

COLUMNAS_MINIMAS_CLEANED = COLUMNAS_FINAL_CLEANED[1:]

MAPEO_COLUMNAS_CLEANED = {
	'Fecha de nacimiento': 'Fecha de nacimiento',
	'Estrato socioeconómico': 'Estrato socioeconómico',
	'Ciudad, municipio o corregimiento de nacimiento': 'Ciudad, municipio o corregimiento de nacimiento',
	'Departamento de nacimiento': 'Departamento de nacimiento',
	'País de nacimiento': 'País de nacimiento',
	'Ciudad, municipio o corregimiento de residencia': 'Ciudad, municipio o corregimiento de residencia',
	'Zona de residencia': 'Zona de residencia',
	'Barrio de residencia': 'Barrio de residencia',
	'Estado civil': 'Estado civil',
	'Auto-reconocimiento étnico (Hace referencia al sentido de pertenencia que expresa una persona frente a un colectivo, de acuerdo con su identidad y formas de interactuar en y con el mundo) ': 'Identidad étnica',
	'¿A qué grupo poblacional perteneces?': 'Grupo poblacional',
	'¿Cuál es tu identidad de géneros? ( es decir, ¿Cómo te vives, sientes, percibes, etc.?)': 'Identidad de género',
	'Expresión de género (¿Cuál es tu apariencia?/¿cómo te muestras al mundo?)': 'Expresión de género',
	'¿Cuál es tu orientación sexual?  es decir,  ¿Quién/es te gusta(n) o  atrae(n)?': 'Orientación sexual',
	'¿Has realizado cambio de nombre y/o del componente sexo en tu documento de identidad?': 'Cambio de nombre/sexo en D.I',
	'Si la respuesta a la pregunta anterior fue "NO" o sólo cambiaste uno de los dos componentes, ¿Qué te impidió realizar el cambio?': 'Impedimento cambio D.I',
	'Por favor indícanos si te gustaría recibir orientación para realizar el cambio de nombre y/o sexo en tu documento de identidad.': 'Asesoría cambio D.I',
	'¿Perteneces a la Universidad del Valle?': 'Pertenencia a la U',
	'Estamento': 'Estamento',
	'Sede de la universidad a la que pertenece': 'Sede de la Universidad del Valle',
	'Nombre del programa académico': 'Nombre del programa académico',
	'Semestre académico': 'Semestre académico',
	'¿Cuál es tu ocupación actual?': '¿Cuál es tu ocupación actual?',
	'Si eres empleado/a/e o independiente ¿A qué te dedicas específicamente?': 'Si eres empleado/a/e o independiente ¿A qué te dedicas específicamente?',
	'¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?': '¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?',
	'¿En qué tipo de entidad recibiste el acompañamiento?': 'Entidad acompañamiento',
	'¿Qué profesional le brindó la atención?': 'Profesional acompañante',
	'¿Cuál(es) es/son tu(s) fuente(s) de ingresos?': '¿De donde provienen tus ingresos o recursos?',
	'¿Con quién(es) vives?': '¿Con quién(es) vives?',
	'Redes de apoyo (Identifica con quiénes o con qué apoyos cuentas)': 'Redes de apoyo (Identifica ¿con quiénes/qué apoyos cuentas?)',
	'Factores de riesgo (identifica aquello que puede estar poniéndote en riesgo)': 'Factores de riesgo (identifica aquello que puede estar poniéndote en riesgo)',
	'¿Tienes alguna creencia religiosa? ¿Cuál es?': '¿Tienes alguna creencia religiosa? ¿Cuál es?',
	'¿Cómo te enteraste de los servicios de Campus Diverso?': 'Como te enteraste de Campus Diverso',
}

GRAFICAS_INICIALES = [
	'identidad_genero',
	'orientacion_sexual',
	'estamento',
	'sede',
	'estrato',
	'edad',
]

TitleCallback = Callable[[str], None]


class ErrorValidacionExcel(Exception):
	"""Error controlado para mostrar mensajes claros al usuario."""


def _emit_title(title_callback: TitleCallback | None, texto: str) -> None:
	if title_callback is not None:
		title_callback(texto)


def lanzar_error_validacion(mensaje: str) -> None:
	raise ErrorValidacionExcel(mensaje)


def normalizar_texto(texto: object) -> str:
	if texto is None:
		return ''
	texto_normalizado = str(texto).strip()
	texto_normalizado = unicodedata.normalize('NFKD', texto_normalizado)
	texto_normalizado = ''.join(
		caracter
		for caracter in texto_normalizado
		if not unicodedata.combining(caracter)
	)
	texto_normalizado = re.sub(r'\s+', ' ', texto_normalizado)
	return texto_normalizado.lower()


def obtener_columnas_df_raw(df: pd.DataFrame) -> list[str]:
	return [str(columna) for columna in df.columns.tolist()]


def normalizar_lista_columnas(columnas: Sequence[object]) -> list[str]:
	return [normalizar_texto(columna) for columna in columnas]


def mostrar_debug_columnas_df_raw(df: pd.DataFrame, titulo: str = 'Debug de columnas detectadas en df_raw', title_callback: TitleCallback | None = None) -> None:
	columnas_actuales = obtener_columnas_df_raw(df)
	_emit_title(title_callback, titulo)
	print(f'Se detectaron {len(columnas_actuales)} columnas en el Excel cargado:')
	for indice, columna in enumerate(columnas_actuales, start=1):
		print(f'{indice}. {columna}')


def resumir_diferencias_con_esquema(df: pd.DataFrame, columnas_esperadas: Sequence[str], nombre_esquema: str) -> dict[str, list[str] | str]:
	columnas_actuales = obtener_columnas_df_raw(df)
	mapa_actual = {normalizar_texto(columna): columna for columna in columnas_actuales}
	mapa_esperado = {normalizar_texto(columna): columna for columna in columnas_esperadas}

	faltantes = [
		mapa_esperado[columna_normalizada]
		for columna_normalizada in mapa_esperado
		if columna_normalizada not in mapa_actual
	]
	adicionales = [
		mapa_actual[columna_normalizada]
		for columna_normalizada in mapa_actual
		if columna_normalizada not in mapa_esperado
	]
	coincidencias = [
		mapa_esperado[columna_normalizada]
		for columna_normalizada in mapa_esperado
		if columna_normalizada in mapa_actual
	]

	return {
		'nombre_esquema': nombre_esquema,
		'coincidencias': coincidencias,
		'faltantes': faltantes,
		'adicionales': adicionales,
	}


def mostrar_debug_validacion_tipo_base(df: pd.DataFrame, title_callback: TitleCallback | None = None) -> None:
	_emit_title(title_callback, 'Debug de validación del tipo de base')

	for esquema, columnas_esperadas in [
		('raw', COLUMNAS_EXACTAS_RAW),
		('cleaned (mínimas)', COLUMNAS_MINIMAS_CLEANED),
	]:
		resumen = resumir_diferencias_con_esquema(df, columnas_esperadas, esquema)
		print(f"Comparación contra esquema {esquema}:")
		print(f"- Coincidencias detectadas: {len(resumen['coincidencias'])} de {len(columnas_esperadas)}")

		faltantes = resumen['faltantes']
		adicionales = resumen['adicionales']

		if faltantes:
			print('- Columnas faltantes:')
			for columna in faltantes:
				print(f'  - {columna}')
		else:
			print('- Columnas faltantes: ninguna')

		if adicionales:
			print('- Columnas adicionales o no reconocidas:')
			for columna in adicionales:
				print(f'  - {columna}')
		else:
			print('- Columnas adicionales o no reconocidas: ninguna')

		print('')


def detectar_tipo_base(df: pd.DataFrame) -> str:
	columnas_actuales_normalizadas = set(normalizar_lista_columnas(obtener_columnas_df_raw(df)))
	columnas_raw_normalizadas = normalizar_lista_columnas(COLUMNAS_EXACTAS_RAW)
	columnas_cleaned_minimas_normalizadas = set(normalizar_lista_columnas(COLUMNAS_MINIMAS_CLEANED))

	if normalizar_lista_columnas(obtener_columnas_df_raw(df)) == columnas_raw_normalizadas:
		return 'raw'
	if columnas_cleaned_minimas_normalizadas.issubset(columnas_actuales_normalizadas):
		return 'cleaned'
	return 'desconocido'


def homologar_columnas(
	df: pd.DataFrame,
	columnas_esperadas: Sequence[str],
	umbral_fuzzy: float = 0.60,
	title_callback: TitleCallback | None = None,
) -> tuple[pd.DataFrame, list[tuple[str, str]], list[str]]:
	columnas_actuales = obtener_columnas_df_raw(df)
	
	columnas_esperadas_normalizadas = {
		normalizar_texto(columna): columna for columna in columnas_esperadas
	}

	renombres: dict[str, str] = {}
	columnas_sin_equivalencia: list[str] = []

	for columna_actual in columnas_actuales:
		columna_normalizada = normalizar_texto(columna_actual)
		columna_canonica = columnas_esperadas_normalizadas.get(columna_normalizada)
		
		# Regularización Fuzzy si no existe coincidencia exacta
		if not columna_canonica:
			coincidencias = difflib.get_close_matches(
				columna_normalizada, 
				list(columnas_esperadas_normalizadas.keys()), 
				n=1, 
				cutoff=umbral_fuzzy
			)
			if coincidencias:
				columna_canonica = columnas_esperadas_normalizadas[coincidencias[0]]
				
		if columna_canonica:
			if columna_canonica not in renombres.values(): # Evitar mapear dos columnas al mismo target
				renombres[columna_actual] = columna_canonica
			else:
				columnas_sin_equivalencia.append(columna_actual)
		else:
			columnas_sin_equivalencia.append(columna_actual)

	df_homologado = df.rename(columns=renombres).copy()

	cambios = [
		(original, nuevo)
		for original, nuevo in renombres.items()
		if original != nuevo
	]

	if cambios:
		_emit_title(title_callback, 'Homologación automática de encabezados')
		print('Se ajustaron automáticamente estas columnas para que coincidan con la estructura esperada:')
		for original, nuevo in cambios:
			print(f"- '{original}' -> '{nuevo}'")

	return df_homologado, cambios, columnas_sin_equivalencia


def limpiar_columnas_unnamed(df: pd.DataFrame) -> pd.DataFrame:
	columnas_validas = [col for col in df.columns if not str(col).startswith('Unnamed:')]
	return df.loc[:, columnas_validas].copy()


def validar_columnas_exactas_df_raw(df: pd.DataFrame, columnas_esperadas: Sequence[str] = COLUMNAS_EXACTAS_RAW) -> None:
	columnas_actuales = obtener_columnas_df_raw(df)

	if columnas_actuales == list(columnas_esperadas):
		print('La estructura exacta de columnas de df_raw coincide con lo esperado.')
		return

	faltantes = [col for col in columnas_esperadas if col not in columnas_actuales]
	adicionales = [col for col in columnas_actuales if col not in columnas_esperadas]

	diferencias_orden: list[str] = []
	for indice, (esperada, actual) in enumerate(zip(columnas_esperadas, columnas_actuales), start=1):
		if esperada != actual:
			diferencias_orden.append(
				f"Posición {indice}: se esperaba '{esperada}' y se encontró '{actual}'"
			)
		if len(diferencias_orden) == 5:
			break

	mensaje = 'La estructura exacta de columnas de df_raw no coincide con la versión esperada.'

	if faltantes:
		mensaje += f"\n- Columnas faltantes: {', '.join([repr(col) for col in faltantes])}"
	if adicionales:
		mensaje += f"\n- Columnas adicionales: {', '.join([repr(col) for col in adicionales])}"
	if diferencias_orden:
		mensaje += '\n- Primeras diferencias de orden detectadas:'
		for diferencia in diferencias_orden:
			mensaje += f'\n  {diferencia}'

	mensaje += '\n- Columnas detectadas actualmente en df_raw:'
	for indice, columna in enumerate(columnas_actuales, start=1):
		mensaje += f'\n  {indice}. {columna}'

	lanzar_error_validacion(mensaje)


def validar_esquema_cleaned_minimo(df: pd.DataFrame, columnas_esperadas: Sequence[str] = COLUMNAS_MINIMAS_CLEANED) -> None:
	columnas_actuales = obtener_columnas_df_raw(df)
	faltantes = [col for col in columnas_esperadas if col not in columnas_actuales]

	if not faltantes:
		print('La estructura base de columnas de la versión cleaned coincide con lo esperado (se incluyen todas las requeridas).')
		adicionales = [col for col in columnas_actuales if col not in columnas_esperadas and col != "Año de análisis"]
		if adicionales:
			print('\nNota: Se detectaron columnas accesorias (las cuales serán omitidas de la salida estandarizada):')
			for col in adicionales:
				print(f"  - {col}")
		return

	mensaje = f"La estructura de la base de datos es inválida. Faltan {len(faltantes)} columnas requeridas del esquema CLEANED:"
	for col in faltantes:
		mensaje += f"\n- '{col}'"

	lanzar_error_validacion(mensaje)


def validar_columnas_obligatorias(df: pd.DataFrame, columnas_obligatorias: Sequence[str] = COLUMNAS_OBLIGATORIAS_RAW) -> None:
	columnas_faltantes = [col for col in columnas_obligatorias if col not in df.columns]
	if columnas_faltantes:
		faltantes_texto = ', '.join([f"'{col}'" for col in columnas_faltantes])
		lanzar_error_validacion(
			f'El archivo no tiene la estructura esperada. Faltan las columnas: {faltantes_texto}.'
		)


def advertir_columnas_adicionales(df: pd.DataFrame, columnas_referencia: Sequence[str]) -> None:
	adicionales = [col for col in df.columns if col not in columnas_referencia]
	if adicionales:
		print('Advertencia: se encontraron columnas adicionales que no se usarán directamente:')
		for columna in adicionales:
			print(f' - {columna}')


def convertir_a_fecha(serie: pd.Series, nombre_columna: str) -> pd.Series:
	serie_convertida = pd.to_datetime(serie, errors='coerce', dayfirst=True)
	nulos_generados = int(serie.notna().sum() - serie_convertida.notna().sum())
	if nulos_generados > 0:
		print(
			f"Advertencia: {nulos_generados} valor(es) de la columna '{nombre_columna}' no pudieron convertirse a fecha."
		)
	return serie_convertida


def filtrar_registros_por_anio_diligenciamiento(
	df: pd.DataFrame,
	anio_analisis: int,
	title_callback: TitleCallback | None = None,
) -> pd.DataFrame:
	if 'Fecha de diligenciamiento' not in df.columns:
		lanzar_error_validacion(
			"No se encontró la columna 'Fecha de diligenciamiento', necesaria para filtrar el año de análisis."
		)

	df_filtrado = df.copy()
	df_filtrado['Fecha de diligenciamiento'] = convertir_a_fecha(
		df_filtrado['Fecha de diligenciamiento'],
		'Fecha de diligenciamiento',
	)

	total_inicial = len(df_filtrado)
	registros_sin_fecha = int(df_filtrado['Fecha de diligenciamiento'].isna().sum())
	mascara_anio = df_filtrado['Fecha de diligenciamiento'].dt.year.eq(anio_analisis)
	registros_fuera_de_anio = int((df_filtrado['Fecha de diligenciamiento'].notna() & ~mascara_anio).sum())

	df_filtrado = df_filtrado.loc[mascara_anio.fillna(False)].copy()

	if registros_sin_fecha > 0 or registros_fuera_de_anio > 0:
		_emit_title(title_callback, 'Filtro por año de diligenciamiento')
		print(f'Año de análisis configurado: {anio_analisis}')
		print(f'Registros originales: {total_inicial}')
		print(f'Registros excluidos por fecha inválida o vacía: {registros_sin_fecha}')
		print(f'Registros excluidos por pertenecer a otro año: {registros_fuera_de_anio}')
		print(f'Registros que continúan en el proceso: {len(df_filtrado)}')

	if df_filtrado.empty:
		lanzar_error_validacion(
			f'No quedaron registros para procesar después de filtrar la columna Fecha de diligenciamiento por el año {anio_analisis}.'
		)

	return df_filtrado


def calcular_edad_desde_fecha_nacimiento(serie_fechas: pd.Series, anio_referencia: int) -> pd.Series:
	fecha_corte = pd.Timestamp(year=anio_referencia, month=12, day=31)
	edades = ((fecha_corte - serie_fechas).dt.days / 365.25).apply(
		lambda valor: int(valor) if pd.notna(valor) and valor >= 0 else np.nan
	)
	return edades


def limpiar_texto_categorico(valor: object, valor_relleno: str = VALOR_RELLENO_CATEGORICO) -> str:
	if pd.isna(valor):
		return valor_relleno
	texto = str(valor).strip()
	if not texto:
		return valor_relleno
	texto = re.sub(r'\s+', ' ', texto)
	return texto


def mostrar_resumen_dataframe(df: pd.DataFrame, nombre: str = 'DataFrame') -> None:
	print(f'{nombre}: {df.shape[0]} filas y {df.shape[1]} columnas')
	print('Primeras columnas detectadas:')
	for columna in df.columns[:10]:
		print(f' - {columna}')


def validar_esquema_raw(df_raw: pd.DataFrame, title_callback: TitleCallback | None = None) -> None:
	_emit_title(title_callback, 'Validación del esquema raw')
	validar_columnas_exactas_df_raw(df_raw, COLUMNAS_EXACTAS_RAW)
	validar_columnas_obligatorias(df_raw, COLUMNAS_OBLIGATORIAS_RAW)
	advertir_columnas_adicionales(df_raw, COLUMNAS_OBLIGATORIAS_RAW)
	print('La estructura mínima y exacta del archivo raw es válida.')


def validar_esquema_cleaned(df_cleaned: pd.DataFrame, title_callback: TitleCallback | None = None) -> None:
	_emit_title(title_callback, 'Validación del esquema cleaned')
	validar_esquema_cleaned_minimo(df_cleaned, COLUMNAS_MINIMAS_CLEANED)
	print('La estructura del archivo cleaned es válida (contiene las columnas mínimas).')


def construir_dataframe_cleaned(
	df_entrada: pd.DataFrame,
	tipo_base: str,
	anio_analisis: int,
	valor_relleno_categorico: str = VALOR_RELLENO_CATEGORICO,
	title_callback: TitleCallback | None = None,
) -> pd.DataFrame:
	_emit_title(title_callback, 'Limpieza y transformación')

	# Extraer o determinar 'Año de análisis'
	# Se da prioridad a la columna "Marca temporal" (si existe) convirtiendo a fecha y usando el primer año válido encontrado.
	año_calculado = anio_analisis
	if 'Marca temporal' in df_entrada.columns:
		m_temporal = pd.to_datetime(df_entrada['Marca temporal'], errors='coerce', dayfirst=True)
		años_validos = m_temporal.dt.year.dropna()
		if not años_validos.empty:
			año_calculado = int(años_validos.mode().iloc[0]) # Usar el año más frecuente como el calculado para todo el archivo

	if tipo_base == 'cleaned':
		df_cleaned = df_entrada.copy()
		df_cleaned['Fecha de nacimiento'] = convertir_a_fecha(
			df_cleaned['Fecha de nacimiento'],
			'Fecha de nacimiento',
		)
		df_cleaned['Edad'] = pd.to_numeric(df_cleaned['Edad'], errors='coerce')
	else:
		df = limpiar_columnas_unnamed(df_entrada.copy())

		for columna in MAPEO_COLUMNAS_CLEANED:
			if columna not in df.columns:
				lanzar_error_validacion(
					f"No es posible construir la base limpia porque falta la columna '{columna}'."
				)

		df_cleaned = df[list(MAPEO_COLUMNAS_CLEANED.keys())].rename(columns=MAPEO_COLUMNAS_CLEANED)
		df_cleaned['Fecha de nacimiento'] = convertir_a_fecha(
			df_cleaned['Fecha de nacimiento'],
			'Fecha de nacimiento',
		)
		df_cleaned['Edad'] = calcular_edad_desde_fecha_nacimiento(
			df_cleaned['Fecha de nacimiento'],
			año_calculado,
		)

	columnas_categoricas = [
		columna for columna in df_cleaned.columns
		if columna not in ['Fecha de nacimiento', 'Edad', 'Marca temporal', 'Año de análisis']
	]

	for columna in columnas_categoricas:
		# Solamente aplica limpieza de texto si la columna de hecho pertenecerá al output
		if columna in COLUMNAS_FINAL_CLEANED:
			df_cleaned[columna] = df_cleaned[columna].apply(
				lambda valor: limpiar_texto_categorico(valor, valor_relleno_categorico)
			)

	if 'Semestre académico' in df_cleaned.columns:
		df_cleaned['Semestre académico'] = pd.to_numeric(
			df_cleaned['Semestre académico'],
			errors='coerce',
		)

	if 'Año de análisis' not in df_cleaned.columns:
		df_cleaned['Año de análisis'] = año_calculado

	df_cleaned = df_cleaned[COLUMNAS_FINAL_CLEANED].copy()

	print('Transformación finalizada.')
	mostrar_resumen_dataframe(df_cleaned, nombre='Base cleaned')
	return df_cleaned


def crear_resumen_calidad(df_entrada: pd.DataFrame, df_cleaned: pd.DataFrame, tipo_base: str) -> pd.DataFrame:
	etiqueta_base = 'base raw filtrada' if tipo_base == 'raw' else 'base cleaned cargada'
	resumen = pd.DataFrame(
		{
			'Indicador': [
				f'Filas en {etiqueta_base}',
				f'Columnas en {etiqueta_base}',
				'Filas en base cleaned final',
				'Columnas en base cleaned final',
				'Registros con fecha de nacimiento válida',
				'Registros con edad calculada o válida',
			],
			'Valor': [
				int(df_entrada.shape[0]),
				int(df_entrada.shape[1]),
				int(df_cleaned.shape[0]),
				int(df_cleaned.shape[1]),
				int(df_cleaned['Fecha de nacimiento'].notna().sum()),
				int(df_cleaned['Edad'].notna().sum()),
			],
		}
	)
	return resumen
