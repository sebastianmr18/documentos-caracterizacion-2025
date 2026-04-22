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
	'Déjanos, por favor, tus comentarios, sugerencias y observaciones. Para Campus Diverso es muy importante conocer si tienes inquietudes o aportes adicionales.'
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

# Columnas que pueden estar ausentes en algunos años y NO son requisito mínimo.
# Si faltan en el archivo, se rellenan con VALOR_RELLENO_CATEGORICO (o NaT para fechas).
COLUMNAS_OPCIONALES_CLEANED = [
	'Fecha de nacimiento',                                                                # Ausente en 2024
	'Si eres empleado/a/e o independiente ¿A qué te dedicas específicamente?',           # Ausente en 2024
	'¿Tienes alguna creencia religiosa? ¿Cuál es?',                                      # Ausente en 2023
]

# Columnas que SIEMPRE deben estar en cualquier año (excluye Año de análisis y opcionales).
COLUMNAS_MINIMAS_CLEANED = [
	col for col in COLUMNAS_FINAL_CLEANED
	if col != 'Año de análisis' and col not in COLUMNAS_OPCIONALES_CLEANED
]

# Diccionario de alias conocidos: clave = nombre canónico CLEANED, valor = lista de variantes
# conocidas de otros años (2023/2024) y de esquemas RAW. Se usa como primera capa de
# homologación antes del fuzzy-matching genérico.
ALIAS_COLUMNAS_CLEANED: dict[str, list[str]] = {
	# ------------------------------------------------------------------
	# Variaciones de ITERACIÓN 1 (diferencias entre años CLEANED)
	# ------------------------------------------------------------------
	'Estrato socioeconómico': [
		'Estrato',                          # 2024 simplificado
	],
	'Ciudad, municipio o corregimiento de nacimiento': [
		'Ciudad nacimiento',                # 2024 simplificado
	],
	'Departamento de nacimiento': [
		'Departamento',                     # 2024 simplificado
	],
	'Ciudad, municipio o corregimiento de residencia': [
		'Ciudad residencia',                # 2024 simplificado
	],
	'Zona de residencia': [
		'Zona residencia',                  # 2024 (falta "de")
	],
	'Barrio de residencia': [
		'Barrio residencia',                # 2024 (falta "de")
	],
	'Nombre del programa académico': [
		'Nombre y código del programa académico',   # 2024 ampliado
	],
	'¿Cuál es tu ocupación actual?': [
		'Ocupación',                        # 2024 simplificado
	],
	'¿En los últimos 3 meses has recibido alguno de los siguientes tipos de acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?': [
		'¿Anteriormente, has recibido acompañamiento/orientación de acuerdo con tu situación, experiencia o proceso personal en otro espacio, colectivo, organización privada o servicio de salud?',  # 2024 cambio semántico
	],
	'Redes de apoyo (Identifica ¿con quiénes/qué apoyos cuentas?)': [
		'Redes de apoyo (Identifica con quiénes o con qué apoyos cuentas)',    # 2023 (usa "o" en lugar de "/")
	],
	'Como te enteraste de Campus Diverso': [
		'¿Cómo te enteraste de los servicios de Campus Diverso?',   # 2023 (tiene "servicios" y signos ¿?)
		'Como te enteraste de Campus Diverso',                       # 2024 (sin tilde en "Como", mantener)
		'¿Cómo te enteraste de Campus Diverso?',                    # variante posible
		'Como te enterasta de Campus Diverso',                      # typo en versión CLEANED 2025
	],
	# ------------------------------------------------------------------
	# Variaciones RAW → CLEANED (simplificaciones de preguntas largas)
	# ------------------------------------------------------------------
	'Identidad étnica': [
		'Auto-reconocimiento étnico (Hace referencia al sentido de pertenencia que expresa una persona frente a un colectivo, de acuerdo con su identidad y formas de interactuar en y con el mundo) ',
		'Auto-reconocimiento étnico (Hace referencia al sentido de pertenencia que expresa una persona frente a un colectivo, de acuerdo con su identidad y formas de interactuar en y con el mundo)',
		'Identidad étnica',
	],
	'Grupo poblacional': [
		'¿A qué grupo poblacional perteneces?',
	],
	'Identidad de género': [
		'¿Cuál es tu identidad de géneros? ( es decir, ¿Cómo te vives, sientes, percibes, etc.?)',
		'¿Cuál es tu identidad de géneros? (es decir, ¿Cómo te vives, sientes, percibes, etc.?)',
	],
	'Expresión de género': [
		'Expresión de género (¿Cuál es tu apariencia?/¿cómo te muestras al mundo?)',
	],
	'Orientación sexual': [
		'¿Cuál es tu orientación sexual?  es decir,  ¿Quién/es te gusta(n) o  atrae(n)?',
		'¿Cuál es tu orientación sexual? es decir, ¿Quién/es te gusta(n) o atrae(n)?',
	],
	'Cambio de nombre/sexo en D.I': [
		'¿Has realizado cambio de nombre y/o del componente sexo en tu documento de identidad?',
	],
	'Impedimento cambio D.I': [
		'Si la respuesta a la pregunta anterior fue "NO" o sólo cambiaste uno de los dos componentes, ¿Qué te impidió realizar el cambio?',
		'Si la respuesta a la pregunta anterior fue \'NO\' o sólo cambiaste uno de los dos componentes, ¿Qué te impidió realizar el cambio?',
	],
	'Asesoría cambio D.I': [
		'Por favor indícanos si te gustaría recibir orientación para realizar el cambio de nombre y/o sexo en tu documento de identidad.',
	],
	'Pertenencia a la U': [
		'¿Perteneces a la Universidad del Valle?',
	],
	'Sede de la Universidad del Valle': [
		'Sede de la universidad a la que pertenece',
	],
	'Entidad acompañamiento': [
		'¿En qué tipo de entidad recibiste el acompañamiento?',
	],
	'Profesional acompañante': [
		'¿Qué profesional le brindó la atención?',
	],
	'¿De donde provienen tus ingresos o recursos?': [
		'¿Cuál(es) es/son tu(s) fuente(s) de ingresos?',
	],
}

def _obtener_mapeo_raw_a_cleaned() -> dict[str, str]:
	mapeo: dict[str, str] = {}
	for canonico, aliases in ALIAS_COLUMNAS_CLEANED.items():
		for alias in aliases:
			if alias in COLUMNAS_EXACTAS_RAW:
				mapeo[alias] = canonico
	for col in COLUMNAS_FINAL_CLEANED:
		if col in COLUMNAS_EXACTAS_RAW:
			mapeo[col] = col
	return mapeo

GRAFICAS_COMBINADAS = [
	'edad',
	'estrato',
	'zona_residencia',
	'estado_civil',
	'identidad_etnica',
	'grupo_poblacional',
	'identidad_genero',
	'expresion_genero',
	'orientacion_sexual',
	'cambio_di',
	'asesoria_di',
	'estamento',
	'semestre',
	'ocupacion',
	'acompanamiento',
	'enteraste',
	'entidad_acompanamiento',
	'profesional_acompanante',
	'origen_recursos'
]

GRAFICAS_SEPARADAS = [
	'depto_nacimiento',
	'ciudad_nacimiento',
	'ciudad_residencia',
	'barrio_residencia',
	'impedimento_di',
	'sede_universidad',
	'programa_academico',
	'redes_apoyo',
	'factores_riesgo',
]

TitleCallback = Callable[[str], None]

# ---------------------------------------------------------------------------
# Capa de normalización de valores categóricos
# ---------------------------------------------------------------------------

# Columnas cuyos VALORES serán normalizados semánticamente.
COLUMNAS_VALORES_A_NORMALIZAR: list[str] = [
	'Identidad étnica',
	'Grupo poblacional',
	'Identidad de género',
	'Expresión de género',
	'Orientación sexual',
	'Estamento',
	'Departamento de nacimiento',
	'Ciudad, municipio o corregimiento de nacimiento',
	'Ciudad, municipio o corregimiento de residencia',
]

# Mapa semántico: { columna_cleaned: { valor_canonico: [variante1, ...] } }
# Las variantes se comparan normalizadas (sin tildes, minúsculas, sin espacios
# extra) mediante normalizar_texto(). El valor canónico se escribe tal cual.
MAPA_NORMALIZACION_SEMANTICA: dict[str, dict[str, list[str]]] = {
	# --- Identidad étnica ---
	'Identidad étnica': {
		'Indígena': ['indígena', 'indigena'],
		'Mestizo/a/e': ['mestizo/a/e', 'mestiza', 'mestizo'],
		'NARP (Negro/a/e, Afrodescendiente, Raizal, Palenquero/a/e)': [
			'narp (negro/a/e, afrodescendiente, raizal, palenquero/a/e)',
			'narp',
		],
		'Ningún grupo étnico': [
			'ningún grupo étnico',
			'ningun grupo etnico',
			'sin pertenencia étnica',
			'sin pertenencia etnica',
			'ninguna',
			'ninguno',
		],
	},
	# --- Grupo poblacional ---
	'Grupo poblacional': {
		'Afrodescendiente o negro/a/e': ['afrodescendiente o negro/a/e'],
		'Campesino/a/e': ['campesino/a/e'],
		'Indígena': ['indígena', 'indigena'],
		'LGBTIQ+': ['lgbtiq+', 'lgtbiq+', 'lgbtq+', 'lgtb'],
		'Migrante': ['migrante'],
		'No aplica': ['no aplica', 'no aplica,', 'ninguno', 'ninguna'],
		'Personas con capacidad diversa o "discapacidad"': [
			'personas con capacidad diversa o "discapacidad"',
			'personas con capacidad diversa o discapacidad',
			'discapacidad',
		],
		'Víctima del conflicto armado': [
			'víctima del conflicto armado',
			'victima del conflicto armado',
		],
	},
	# --- Identidad de género ---
	'Identidad de género': {
		'Bigénero': ['bigenero', 'bigénero'],
		'Hombre Trans': [
			'hombre trans (persona trans que se identifica como hombre)',
			'hombre trans',
		],
		'Hombre Cisgénero': [
			'hombre cisgénero',
			'hombre cisgenero',
			'hombre cisgenero (persona que se identifica con su genero masculino asignado al nacer)',
			'hombre cisgenero (persona se que identifica con su genero masculino asignado al nacer)',
		],
		'Mujer Trans': [
			'mujer trans (persona trans que se identifica como mujer)',
			'mujer trans',
		],
		'Mujer Cisgénero': [
			'mujer cisgenero',
			'mujer cisgénero',
			'mujer cisgenero (persona que se identifica con su genero femenino asignado al nacer)',
			'mujer cisgenero (persona se que identifica con su genero femenino asignado al nacer)',
			'mujer',
		],
		'No binario/a/e / queer / género fluido': [
			'no binario/a/e /queer/genero fluido',
			'no binario/a/e / queer / genero fluido',
			'no binario/a/e /queer/género fluido',
			'no binari',
		],
		'Transfemenina': [
			'transfemenina (persona trans que se indentifica con las feminidades)',
			'transfemenina',
		],
		'Transmasculina': [
			'tranmasculina (persona trans que se indentifica con las masculinidades)',
			'transmasculina',
			'tranmasculina',
		],
		'Prefiero no mencionarlo': ['prefiero no mencionarlo', 'prefiero no decirlo'],
	},
	# --- Expresión de género ---
	'Expresión de género': {
		'Femenina/o/e': ['femenina/o/e', 'femenina'],
		'Masculina/o/e': [
			'masculina/o/e',
			'masculina',
			'masculino',
			#'masculino y femenino',
			#'a veces femenina, a veces masculina',
		],
		'No binario/a/e / queer / género fluido': [
			'no binario/a/e/ queer/ genero fluido',
			'no binaria/ queer/ genero fluido',
			'no binaria/queer',
			'no binaria',
			'masculino y femenino', # TODO: Revisar si es correcto que vay aquí
			'a veces femenina, a veces masculina',
		],
		'Prefiero no mencionarlo': ['prefiero no mencionarlo'],
	},
	# --- Orientación sexual ---
	'Orientación sexual': {
		'Androsexual': ['androsexual'],
		'Bisexual': [
			'bisexual (persona que se siente atraida por hombres y mujeres)',
			'bisexual',
		],
		'Gay': [
			'gay (hombre que se siente atraido por otro hombre)',
			'gay',
		],
		'Heterosexual': [
			'heterosexual (mujer u hombre que se siente atraida/o por personas del genero o el sexo opuesto)',
			'heterosexual',
		],
		'Lesbiana': [
			'lesbiana (mujer que se siente atraida por otra mujer)',
			'lesbiana',
		],
		'Pansexual': [
			'pansexual (persona que se siente atraida por otras personas sin ninguna categorizacion)',
			'pansexual',
		],
		'Queer': ['queer (no categorizo mi orientacion sexual)', 'queer'],
		'Prefiero no mencionarlo': ['prefiero no mencionarlo', 'prefiero no decirlo'],
	},
	# --- Estamento ---
	'Estamento': {
		'Estudiante de pregrado': ['estudiante de pregrado'],
		'Estudiante de posgrado': ['estudiante de posgrado'],
		'Monitor/a/e': [
			'monitor/a/e pregrado',
			'monitor/a/e',
			'monitor pregrado',
			'monitor',
		],
		'Administrativo/a/e': ['administrativo/a/e', 'administrativo'],
		'No aplica': ['no aplica', 'ninguno'],
	},
	# --- Departamento de nacimiento ---
	'Departamento de nacimiento': {
		'Valle del Cauca': ['valle del cauca', 'valle'],
		'Bogotá D.C.': ['bogota', 'bogotá'],
		'Nariño': ['narino', 'nariño', 'ñariño'],
		'Cauca': ['cauca'],
		'Cundinamarca': ['cundinamarca'],
		'Boyacá': ['boyaca', 'boyacá'],
		'Atlántico': ['atlantico', 'atlántico'],
		'Bolívar': ['bolivar', 'bolívar'],
		'Antioquia': ['antioquia'],
		'Huila': ['huila'],
		'Putumayo': ['putumayo'],
		'Norte de Santander': ['norte de santander'],
		'Tolima': ['tolima'],
		'Risaralda': ['risaralda'],
	},
	# --- Ciudad de nacimiento ---
	'Ciudad, municipio o corregimiento de nacimiento': {
		'Cali': ['cali', 'cali, valle del cauca'],
		'Tuluá': ['tulua', 'tulúa', 'tuluá', 'tulúa, valle del cauca', 'tuluá, valle del cauca'],
		'Palmira': ['palmira', 'palmira, valle del cauca'],
		'Popayán': ['popayan', 'popayán', 'popayán, cauca', 'propayan cauca'],
		'Ipiales': ['ipiales', 'ipiales, nariño', 'ipiales, narino'],
		'Pasto': ['pasto', 'pasto, nariño', 'pasto, narino'],
		'Barranquilla': ['barranquilla', 'barranquilla, atlántico', 'barranquilla, atlantico'],
		'Bogotá': ['bogota', 'bogotá', 'bogota, cundinamarca'],
		'Miranda': ['miranda', 'miranda, cauca'],
	},
	# --- Ciudad de residencia ---
	'Ciudad, municipio o corregimiento de residencia': {
		'Cali': ['cali', 'cali, valle del cauca'],
		'Tuluá': ['tulua', 'tuluá', 'tulua, valle del cauca', 'tuluá, valle del cauca'],
		'Jamundí': ['jamundi', 'jamundí'],
		'Guacarí': ['guacari', 'guacarí'],
		'Florida': ['florida', 'florida valle'],
	},
}


class ErrorValidacionExcel(Exception):
	"""Error controlado para mostrar mensajes claros al usuario."""


def _emit_title(title_callback: TitleCallback | None, texto: str) -> None:
	if title_callback is not None:
		title_callback(texto)


def lanzar_error_validacion(mensaje: str) -> None:
	raise ErrorValidacionExcel(mensaje)


def _resolver_valor_semantico(
	valor_normalizado: str,
	mapping: dict[str, list[str]],
) -> str | None:
	"""Busca valor_normalizado en las listas de variantes del mapping.

	Retorna el valor canónico si encuentra coincidencia exacta o de prefijo.
	Las variantes del mapa también se comparan normalizadas.
	"""
	for canonico, variantes in mapping.items():
		for variante in variantes:
			variante_norm = normalizar_texto(variante)
			if valor_normalizado == variante_norm:
				return canonico
			# Coincidencia de prefijo: útil para respuestas multi-opción
			# como "Bisexual, Queer (no categorizo...)"
			if valor_normalizado.startswith(variante_norm):
				return canonico
	return None


def normalizar_valores_categoricos(
	df: pd.DataFrame,
	columnas: list[str] | None = None,
	mapa: dict[str, dict[str, list[str]]] | None = None,
	valor_desconocido: str | None = None,
	title_callback: TitleCallback | None = None,
) -> pd.DataFrame:
	"""Normaliza semánticamente los valores categóricos de las columnas indicadas.

	Proceso por celda:
	1. Limpieza básica: strip + normalizar_texto (sin tildes, minúsculas).
	2. Búsqueda en el mapa semántico → valor canónico.
	3. Si no hay coincidencia:
	   - Conserva el valor con limpieza básica (default).
	   - O sustituye por valor_desconocido si se indica uno.

	Los NaN / vacíos se dejan intactos para que limpiar_texto_categorico
	los gestione después con VALOR_RELLENO_CATEGORICO.

	Args:
		df: DataFrame a normalizar (se opera sobre una copia).
		columnas: Columnas a procesar. Default: COLUMNAS_VALORES_A_NORMALIZAR.
		mapa: Mapa semántico. Default: MAPA_NORMALIZACION_SEMANTICA.
		valor_desconocido: Texto de reemplazo para valores no reconocidos.
		                    Si es None se conserva el valor original limpio.
		title_callback: Función para imprimir títulos en la UI.

	Returns:
		Copia del DataFrame con las columnas normalizadas.
	"""
	if columnas is None:
		columnas = COLUMNAS_VALORES_A_NORMALIZAR
	if mapa is None:
		mapa = MAPA_NORMALIZACION_SEMANTICA

	df_out = df.copy()
	desconocidos_por_columna: dict[str, set[str]] = {}

	for columna in columnas:
		if columna not in df_out.columns:
			continue

		mapping_col = mapa.get(columna, {})
		desconocidos: set[str] = set()

		def _resolver_celda(valor: object, _mapping: dict[str, list[str]] = mapping_col, _desc: set[str] = desconocidos) -> object:
			if pd.isna(valor):
				return valor
			texto = str(valor).strip()
			if not texto:
				return valor
			valor_norm = normalizar_texto(texto)
			if _mapping:
				canonico = _resolver_valor_semantico(valor_norm, _mapping)
				if canonico is not None:
					return canonico
				_desc.add(texto)
				return valor_desconocido if valor_desconocido is not None else texto
			# Sin mapa → solo limpieza básica
			return texto

		df_out[columna] = df_out[columna].apply(_resolver_celda)

		if desconocidos:
			desconocidos_por_columna[columna] = desconocidos

	if desconocidos_por_columna:
		_emit_title(title_callback, 'Valores no reconocidos en normalización semántica')
		print(
			'Advertencia: los siguientes valores no estaban en el mapa de normalización '
			'y se conservaron tal cual (revisar si deben agregarse al mapa):'
		)
		for col, vals in desconocidos_por_columna.items():
			print(f'  [{col}]')
			for v in sorted(vals):
				print(f"    - '{v}'")

	return df_out


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


def _construir_mapa_alias_normalizado() -> dict[str, str]:
	"""Construye un mapa {alias_normalizado: canonico} desde ALIAS_COLUMNAS_CLEANED."""
	mapa: dict[str, str] = {}
	for canonico, aliases in ALIAS_COLUMNAS_CLEANED.items():
		for alias in aliases:
			mapa[normalizar_texto(alias)] = canonico
		# El propio nombre canónico también es un alias de sí mismo
		mapa[normalizar_texto(canonico)] = canonico
	return mapa


# Columnas que SOLO aparecen en archivos RAW y nunca en CLEANED.
# Su presencia es suficiente para identificar un archivo como RAW.
_INDICADORES_RAW = {
	'Marca temporal',
	'Dirección de correo electrónico',
}


def detectar_tipo_base(df: pd.DataFrame) -> str:
	"""Detecta si el DataFrame es 'raw', 'cleaned' o 'desconocido'.

	- 'raw': contiene todas las columnas obligatorias RAW (subconjunto) o
	         al menos los indicadores exclusivos RAW.
	- 'cleaned': contiene las columnas mínimas CLEANED (con o sin resolución
	             de aliases).
	- 'desconocido': no satisface ningún criterio.
	"""
	columnas_actuales = obtener_columnas_df_raw(df)
	columnas_actuales_normalizadas = set(normalizar_lista_columnas(columnas_actuales))

	# 1. Discriminador rápido RAW: columnas que solo existen en archivos RAW
	indicadores_norm = {normalizar_texto(c) for c in _INDICADORES_RAW}
	if indicadores_norm.issubset(columnas_actuales_normalizadas):
		return 'raw'

	# 2. Verificar RAW completo: columnas obligatorias RAW como subconjunto
	columnas_obligatorias_raw_normalizadas = set(normalizar_lista_columnas(COLUMNAS_OBLIGATORIAS_RAW))
	if columnas_obligatorias_raw_normalizadas.issubset(columnas_actuales_normalizadas):
		return 'raw'

	# 3. Verificar cleaned con coincidencia exacta normalizada
	columnas_cleaned_minimas_normalizadas = set(normalizar_lista_columnas(COLUMNAS_MINIMAS_CLEANED))
	if columnas_cleaned_minimas_normalizadas.issubset(columnas_actuales_normalizadas):
		return 'cleaned'

	# 4. Intentar resolución vía alias: si tras renombrar con el diccionario de alias
	#    las columnas mínimas quedan cubiertas, es cleaned.
	mapa_alias = _construir_mapa_alias_normalizado()
	columnas_resueltas = set()
	for col_norm in columnas_actuales_normalizadas:
		canonica = mapa_alias.get(col_norm)
		if canonica:
			columnas_resueltas.add(normalizar_texto(canonica))
		else:
			columnas_resueltas.add(col_norm)

	if columnas_cleaned_minimas_normalizadas.issubset(columnas_resueltas):
		return 'cleaned'

	return 'desconocido'


def homologar_columnas(
	df: pd.DataFrame,
	columnas_esperadas: Sequence[str],
	umbral_fuzzy: float = 0.60,
	title_callback: TitleCallback | None = None,
) -> tuple[pd.DataFrame, list[tuple[str, str]], list[str]]:
	"""Renombra columnas del df al nombre canónico usando tres capas en orden:
	1. Coincidencia normalizada exacta.
	2. Diccionario de alias conocidos (ALIAS_COLUMNAS_CLEANED).
	3. Fuzzy matching como fallback.
	"""
	columnas_actuales = obtener_columnas_df_raw(df)

	# Mapa esperado: normalizado -> canónico
	columnas_esperadas_normalizadas = {
		normalizar_texto(columna): columna for columna in columnas_esperadas
	}

	# Mapa alias: alias_normalizado -> canónico (solo para columnas que están en columnas_esperadas)
	mapa_alias_global = _construir_mapa_alias_normalizado()
	mapa_alias_filtrado: dict[str, str] = {
		alias_norm: canonico
		for alias_norm, canonico in mapa_alias_global.items()
		if canonico in columnas_esperadas
	}

	renombres: dict[str, str] = {}
	columnas_sin_equivalencia: list[str] = []

	for columna_actual in columnas_actuales:
		columna_normalizada = normalizar_texto(columna_actual)

		# Capa 1: coincidencia exacta normalizada
		columna_canonica = columnas_esperadas_normalizadas.get(columna_normalizada)

		# Capa 2: alias conocidos
		if not columna_canonica:
			columna_canonica = mapa_alias_filtrado.get(columna_normalizada)
			if columna_canonica and columna_canonica not in columnas_esperadas:
				columna_canonica = None  # alias no aplica a este esquema

		# Capa 3: fuzzy matching genérico
		if not columna_canonica:
			coincidencias = difflib.get_close_matches(
				columna_normalizada,
				list(columnas_esperadas_normalizadas.keys()),
				n=1,
				cutoff=umbral_fuzzy,
			)
			if coincidencias:
				columna_canonica = columnas_esperadas_normalizadas[coincidencias[0]]

		if columna_canonica:
			if columna_canonica not in renombres.values():  # Evitar mapear dos col. al mismo target
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





def validar_esquema_cleaned_minimo(
	df: pd.DataFrame,
	columnas_minimas: Sequence[str] = COLUMNAS_MINIMAS_CLEANED,
	columnas_opcionales: Sequence[str] = COLUMNAS_OPCIONALES_CLEANED,
) -> None:
	"""Valida que el DataFrame contenga todas las columnas mínimas obligatorias.
	Las columnas opcionales generan un aviso si faltan pero NO interrumpen el flujo.
	"""
	columnas_actuales = set(obtener_columnas_df_raw(df))

	# Columnas mínimas obligatorias
	faltantes_obligatorias = [col for col in columnas_minimas if col not in columnas_actuales]
	if faltantes_obligatorias:
		mensaje = f"La base de datos es inválida. Faltan {len(faltantes_obligatorias)} columnas obligatorias del esquema CLEANED:"
		for col in faltantes_obligatorias:
			mensaje += f"\n- '{col}'"
		lanzar_error_validacion(mensaje)

	print('Columnas obligatorias: todas presentes ✓')

	# Columnas opcionales: aviso si faltan
	faltantes_opcionales = [col for col in columnas_opcionales if col not in columnas_actuales]
	if faltantes_opcionales:
		print(f'Aviso: Las siguientes {len(faltantes_opcionales)} columna(s) opcionales no están en el archivo y se rellenarán con \'Sin dato\'/')
		for col in faltantes_opcionales:
			print(f"  - '{col}'")

	# Columnas extras no reconocidas (informativo)
	todas_conocidas = set(columnas_minimas) | set(columnas_opcionales) | {'Año de análisis'}
	adicionales = [col for col in columnas_actuales if col not in todas_conocidas]
	if adicionales:
		print(f'Nota: Se omitirán {len(adicionales)} columnas no reconocidas de la salida:')
		for col in adicionales:
			print(f"  - {col}")


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
	"""Valida que el DataFrame RAW contenga todas las columnas obligatorias.
	No exige orden exacto ni columnas adicionales específicas (como Unnamed:60, Convención).
	"""
	_emit_title(title_callback, 'Validación del esquema raw')
	validar_columnas_obligatorias(df_raw, COLUMNAS_OBLIGATORIAS_RAW)
	advertir_columnas_adicionales(df_raw, COLUMNAS_OBLIGATORIAS_RAW)
	print('La estructura mínima del archivo raw es válida (todas las columnas obligatorias presentes).')


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
		# Rellenar columnas opcionales ausentes antes de procesar
		for col_opc in COLUMNAS_OPCIONALES_CLEANED:
			if col_opc not in df_cleaned.columns:
				df_cleaned[col_opc] = valor_relleno_categorico
		# Convertir fecha de nacimiento si existe y no es relleno
		if 'Fecha de nacimiento' in df_cleaned.columns:
			df_cleaned['Fecha de nacimiento'] = convertir_a_fecha(
				df_cleaned['Fecha de nacimiento'],
				'Fecha de nacimiento',
			)
		df_cleaned['Edad'] = pd.to_numeric(df_cleaned['Edad'], errors='coerce')
	else:
		df = limpiar_columnas_unnamed(df_entrada.copy())

		mapeo_raw_a_cleaned = _obtener_mapeo_raw_a_cleaned()
		# Para bases raw, las columnas opcionales del MAPEO también pueden estar ausentes
		columnas_raw_obligatorias = {
			col for col in mapeo_raw_a_cleaned
			if mapeo_raw_a_cleaned[col] not in COLUMNAS_OPCIONALES_CLEANED
		}
		for columna in columnas_raw_obligatorias:
			if columna not in df.columns:
				lanzar_error_validacion(
					f"No es posible construir la base limpia porque falta la columna obligatoria '{columna}'."
				)

		# Construir df_cleaned con las columnas disponibles del mapeo
		columnas_mapeo_disponibles = {k: v for k, v in mapeo_raw_a_cleaned.items() if k in df.columns}
		df_cleaned = df[list(columnas_mapeo_disponibles.keys())].rename(columns=columnas_mapeo_disponibles)

		# Rellenar columnas opcionales ausentes
		for col_opc in COLUMNAS_OPCIONALES_CLEANED:
			if col_opc not in df_cleaned.columns:
				df_cleaned[col_opc] = valor_relleno_categorico

		if 'Fecha de nacimiento' in df_cleaned.columns:
			df_cleaned['Fecha de nacimiento'] = convertir_a_fecha(
				df_cleaned['Fecha de nacimiento'],
				'Fecha de nacimiento',
			)
		df_cleaned['Edad'] = calcular_edad_desde_fecha_nacimiento(
			df_cleaned.get('Fecha de nacimiento', pd.Series(dtype='object')),
			año_calculado,
		)

	columnas_categoricas = [
		columna for columna in df_cleaned.columns
		if columna not in ['Fecha de nacimiento', 'Edad', 'Marca temporal', 'Año de análisis']
	]

	for columna in columnas_categoricas:
		# Solamente aplica limpieza de texto si la columna pertenecerá al output
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

	# --- Normalización semántica de valores categóricos ---
	df_cleaned = normalizar_valores_categoricos(
		df_cleaned,
		title_callback=title_callback,
	)

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
