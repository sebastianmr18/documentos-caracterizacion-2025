from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def ejecutar_comando(comando: list[str], carpeta_trabajo: Path | None = None) -> subprocess.CompletedProcess[str]:
    print(f"[DEBUG] Ejecutando: {' '.join(comando)} (en {carpeta_trabajo or 'actual'})")
    resultado = subprocess.run(
        comando,
        cwd=str(carpeta_trabajo) if carpeta_trabajo else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if resultado.returncode != 0:
        print(f"[ERROR] Error al ejecutar comando: {resultado.stderr.strip()}")
    return resultado


def validar_estructura_repo(repo_root: Path) -> None:
    print(f"[DEBUG] Validando estructura de repositorio en: {repo_root}")
    rutas_obligatorias = [
        repo_root / 'src',
        repo_root / 'src' / '__init__.py',
        repo_root / 'src' / 'processing.py',
        repo_root / 'src' / 'visualization.py',
        repo_root / 'src' / 'export.py',
        repo_root / 'src' / 'ui.py',
    ]

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
    print(f"[DEBUG] Resolviendo carpeta de repositorio (usar_github={usar_github})")
    
    if repo_root is not None and not usar_github:
        print(f"[DEBUG] Usando repo_root proporcionado: {repo_root}")
        return repo_root

    if not usar_github:
        print("[DEBUG] No se usa GitHub y repo_root es None.")
        raise RuntimeError(
            'No se encontro un repo local con carpeta src/. '
            'Activa USAR_GITHUB_COMO_FUENTE o ejecuta el notebook dentro del repositorio.'
        )

    if not github_url.strip():
        raise RuntimeError(
            'Debes definir GITHUB_REPO_URL cuando USAR_GITHUB_COMO_FUENTE=True.'
        )

    if github_dirname.strip():
        res = workdir / github_dirname.strip()
        print(f"[DEBUG] Carpeta definida manualmente: {res}")
        return res

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
    print("=== Iniciando Preparación del Repositorio ===")
    
    repo_objetivo = resolver_carpeta_repo(
        repo_root, usar_github, github_url, github_dirname, workdir
    )

    if not usar_github:
        print(f"[INFO] Usando repositorio local en: {repo_objetivo}")
        validar_estructura_repo(repo_objetivo)
        return repo_objetivo

    git_version = ejecutar_comando(['git', '--version'])
    if git_version.returncode != 0:
        raise RuntimeError('No se encontro el comando git en el entorno.')

    if not repo_objetivo.exists():
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
        print(f"[INFO] Actualizando repositorio local ({github_branch}) en: {repo_objetivo}")
        fetch_result = ejecutar_comando(['git', 'fetch', 'origin'], carpeta_trabajo=repo_objetivo)
        if fetch_result.returncode == 0:
            pull_result = ejecutar_comando(['git', 'pull', 'origin', github_branch], carpeta_trabajo=repo_objetivo)
            if pull_result.returncode != 0:
                 print("[WARN] No fue posible realizar el pull. Continuando con versión local.")
        else:
            print("[WARN] No fue posible realizar el fetch. Continuando con versión local.")

    validar_estructura_repo(repo_objetivo)

    if instalar_dependencias:
        requirements_path = repo_objetivo / 'requirements.txt'
        if requirements_path.exists():
            print(f"[INFO] Instalando dependencias desde: {requirements_path}")
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

    if str(repo_objetivo) not in sys.path:
        print(f"[DEBUG] Agregando {repo_objetivo} a sys.path")
        sys.path.insert(0, str(repo_objetivo))

    print(f"=== Repositorio listo en: {repo_objetivo} ===\n")
    return repo_objetivo
