"""
Módulo de Inicialización (Bootstrap).

Proporciona utilidades para preparar y asegurar que el entorno de ejecución 
esté correctamente configurado. Permite descargar o actualizar el repositorio 
desde GitHub, instalar dependencias y validar que la estructura de carpetas
y archivos sea la correcta para el análisis.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def ejecutar_comando(comando: list[str], carpeta_trabajo: Path | None = None) -> subprocess.CompletedProcess[str]:
    """
    Ejecuta un comando en el sistema operativo capturando su salida.

    Parámetros:
        comando (list[str]): Lista de strings que representan el comando y sus argumentos.
        carpeta_trabajo (Path | None): Directorio donde se ejecutará el comando. Si es None,
                                       usa el directorio actual.

    Retorna:
        subprocess.CompletedProcess[str]: Resultado de la ejecución con stdout, stderr y código de retorno.
    """
    print(f"[DEBUG] Ejecutando: {' '.join(comando)} (en {carpeta_trabajo or 'actual'})")
    resultado = subprocess.run(
        comando,
        cwd=str(carpeta_trabajo) if carpeta_trabajo else None,
        capture_output=True,
        text=True,
        check=False, # No lanza excepción si falla, permite control manual del error
    )
    # Si el código de retorno no es 0 (éxito), reporta el error
    if resultado.returncode != 0:
        print(f"[ERROR] Error al ejecutar comando: {resultado.stderr.strip()}")
    return resultado


def validar_estructura_repo(repo_root: Path) -> None:
    """
    Verifica que la carpeta indicada contenga la arquitectura modular base requerida.

    Parámetros:
        repo_root (Path): Ruta raíz del repositorio a validar.

    Lanza:
        RuntimeError: Si falta alguno de los archivos o directorios obligatorios.
    """
    print(f"[DEBUG] Validando estructura de repositorio en: {repo_root}")
    
    # Definición explícita de las rutas críticas del proyecto
    rutas_obligatorias = [
        repo_root / 'src',
        repo_root / 'src' / '__init__.py',
        repo_root / 'src' / 'processing.py',
        repo_root / 'src' / 'visualization.py',
        repo_root / 'src' / 'export.py',
        repo_root / 'src' / 'ui.py',
    ]

    # Recolectar rutas que no existen en el sistema de archivos
    faltantes = [ruta for ruta in rutas_obligatorias if not ruta.exists()]
    if faltantes:
        print(f"[ERROR] Estructura incompleta. Faltan {len(faltantes)} elementos.")
        faltantes_texto = '\n'.join(f'- {ruta}' for ruta in faltantes)
        raise RuntimeError(
            'El repositorio descargado no tiene la arquitectura modular esperada.\n'
            f'{faltantes_texto}'
        )
    print("[DEBUG] Estructura de repositorio validada con éxito.")


def resolver_carpeta_repo(
    repo_root: Path | None,
    usar_github: bool,
    github_url: str,
    github_dirname: str,
    workdir: Path
) -> Path:
    """
    Determina la ruta final donde residirá el código fuente, dependiendo de 
    la configuración (local o GitHub) y de parámetros manuales.

    Parámetros:
        repo_root (Path | None): Ruta proporcionada manualmente o None.
        usar_github (bool): Si es True, ignora repo_root y busca la carpeta asociada al clon.
        github_url (str): URL del repositorio.
        github_dirname (str): Nombre explícito de la carpeta a usar (opcional).
        workdir (Path): Directorio de trabajo base donde se alojará el repo.

    Retorna:
        Path: Ruta absoluta donde se encuentra o deberá encontrarse el repositorio.

    Lanza:
        RuntimeError: Si faltan datos o las configuraciones son incompatibles.
    """
    print(f"[DEBUG] Resolviendo carpeta de repositorio (usar_github={usar_github})")
    
    # Caso 1: Uso netamente local con ruta ya provista
    if repo_root is not None and not usar_github:
        print(f"[DEBUG] Usando repo_root proporcionado: {repo_root}")
        return repo_root

    # Caso 2: Sin ruta y sin github (error de configuración)
    if not usar_github:
        print("[DEBUG] No se usa GitHub y repo_root es None.")
        raise RuntimeError(
            'No se encontro un repo local con carpeta src/. '
            'Activa USAR_GITHUB_COMO_FUENTE o ejecuta el notebook dentro del repositorio.'
        )

    # Validar URL cuando se activa GitHub
    if not github_url.strip():
        raise RuntimeError(
            'Debes definir GITHUB_REPO_URL cuando USAR_GITHUB_COMO_FUENTE=True.'
        )

    # Caso 3: Nombre de carpeta explícito proveído por el usuario
    if github_dirname.strip():
        res = workdir / github_dirname.strip()
        print(f"[DEBUG] Carpeta definida manualmente: {res}")
        return res

    # Caso 4: Inferir el nombre de la carpeta a partir de la URL (ej: /user/repo.git -> repo)
    nombre_repo = github_url.rstrip('/').split('/')[-1]
    if nombre_repo.endswith('.git'):
        nombre_repo = nombre_repo[:-4]
    
    res = workdir / nombre_repo
    print(f"[DEBUG] Carpeta resuelta desde URL: {res}")
    return res


def preparar_repo_desde_github(
    repo_root: Path | None,
    usar_github: bool,
    github_url: str,
    github_branch: str,
    github_dirname: str,
    actualizar: bool,
    instalar_dependencias: bool,
    workdir: Path
) -> Path:
    """
    Orquesta todo el proceso de preparación: resolución de rutas, clonado,
    actualización (fetch/pull), instalación de dependencias y configuración del PYTHONPATH.

    Parámetros:
        repo_root (Path | None): Ruta pre-existente, si aplica.
        usar_github (bool): Define si interactuamos con repos remotos.
        github_url (str): URL a clonar.
        github_branch (str): Rama a utilizar (ej. 'main').
        github_dirname (str): Sobrescribir nombre de carpeta destino.
        actualizar (bool): Intenta hacer git pull si el repo ya existe.
        instalar_dependencias (bool): Instala requirements.txt si existe.
        workdir (Path): Directorio base operativo.

    Retorna:
        Path: Ruta final del repositorio listo para ser importado.

    Lanza:
        RuntimeError: En caso de errores irreparables de clonado o sin instalación local de git.
    """
    print("=== Iniciando Preparación del Repositorio ===")
    
    # 1. Resolver ruta objetivo
    repo_objetivo = resolver_carpeta_repo(
        repo_root, usar_github, github_url, github_dirname, workdir
    )

    # 2. Si no es GitHub, solo validamos que lo local sirva y terminamos
    if not usar_github:
        print(f"[INFO] Usando repositorio local en: {repo_objetivo}")
        validar_estructura_repo(repo_objetivo)
        return repo_objetivo

    # 3. Validar existencia de git en sistema
    git_version = ejecutar_comando(['git', '--version'])
    if git_version.returncode != 0:
        raise RuntimeError('No se encontro el comando git en el entorno.')

    # 4. Lógica de clonado o actualización
    if not repo_objetivo.exists():
        # Clonación en frío
        print(f"[INFO] Clonando repositorio desde GitHub ({github_branch}) en: {repo_objetivo}")
        clone_result = ejecutar_comando(
            ['git', 'clone', '--branch', github_branch, github_url, str(repo_objetivo)]
        )
        if clone_result.returncode != 0:
            raise RuntimeError(
                'No fue posible clonar el repositorio desde GitHub.\n'
                f'{clone_result.stderr.strip()}'
            )
    elif (repo_objetivo / '.git').exists() and actualizar:
        # Actualización de repositorio existente (fetch -> pull)
        print(f"[INFO] Actualizando repositorio local ({github_branch}) en: {repo_objetivo}")
        fetch_result = ejecutar_comando(['git', 'fetch', 'origin'], carpeta_trabajo=repo_objetivo)
        if fetch_result.returncode == 0:
            pull_result = ejecutar_comando(['git', 'pull', 'origin', github_branch], carpeta_trabajo=repo_objetivo)
            if pull_result.returncode != 0:
                 print("[WARN] No fue posible realizar el pull. Continuando con versión local.")
        else:
            print("[WARN] No fue posible realizar el fetch. Continuando con versión local.")

    # 5. Garantizar que se descargó la estructura correcta
    validar_estructura_repo(repo_objetivo)

    # 6. Instalar dependencias si fue solicitado
    if instalar_dependencias:
        requirements_path = repo_objetivo / 'requirements.txt'
        if requirements_path.exists():
            print(f"[INFO] Instalando dependencias desde: {requirements_path}")
            # pip install -r requirements.txt a través de sys.executable asegura compatibilidad de entorno
            install_result = ejecutar_comando(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)],
                carpeta_trabajo=repo_objetivo,
            )
            if install_result.returncode == 0:
                print("[DEBUG] Dependencias instaladas con éxito.")
            else:
                print(f"[WARN] Hubo problemas instalando dependencias: {install_result.stderr.strip()}")
        else:
            print("[DEBUG] No se encontró requirements.txt. Omitiendo instalación.")

    # 7. Modificar sys.path para permitir "import src.processing" desde cualquier lado
    if str(repo_objetivo) not in sys.path:
        print(f"[DEBUG] Agregando {repo_objetivo} a sys.path")
        sys.path.insert(0, str(repo_objetivo))

    print(f"=== Repositorio listo en: {repo_objetivo} ===\n")
    return repo_objetivo
