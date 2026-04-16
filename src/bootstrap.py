from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def ejecutar_comando(comando: list[str], carpeta_trabajo: Path | None = None) -> subprocess.CompletedProcess[str]:
    resultado = subprocess.run(
        comando,
        cwd=str(carpeta_trabajo) if carpeta_trabajo else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return resultado


def validar_estructura_repo(repo_root: Path) -> None:
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
        faltantes_texto = '\n'.join(f'- {ruta}' for ruta in faltantes)
        raise RuntimeError(
            'El repositorio descargado no tiene la arquitectura modular esperada.\n'
            f'{faltantes_texto}'
        )


def resolver_carpeta_repo(
    repo_root: Path | None,
    usar_github: bool,
    github_url: str,
    github_dirname: str,
    workdir: Path
) -> Path:
    if repo_root is not None and not usar_github:
        return repo_root

    if not usar_github:
        raise RuntimeError(
            'No se encontro un repo local con carpeta src/. '
            'Activa USAR_GITHUB_COMO_FUENTE o ejecuta el notebook dentro del repositorio.'
        )

    if not github_url.strip():
        raise RuntimeError(
            'Debes definir GITHUB_REPO_URL cuando USAR_GITHUB_COMO_FUENTE=True.'
        )

    if github_dirname.strip():
        return workdir / github_dirname.strip()

    nombre_repo = github_url.rstrip('/').split('/')[-1]
    if nombre_repo.endswith('.git'):
        nombre_repo = nombre_repo[:-4]
    return workdir / nombre_repo


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
    repo_objetivo = resolver_carpeta_repo(
        repo_root, usar_github, github_url, github_dirname, workdir
    )

    if not usar_github:
        if repo_objetivo is None:
            raise RuntimeError(
                'No se encontro un repo local con carpeta src/. '
                'Activa USAR_GITHUB_COMO_FUENTE o ejecuta el notebook dentro del repositorio.'
            )
        validar_estructura_repo(repo_objetivo)
        return repo_objetivo

    git_version = ejecutar_comando(['git', '--version'])
    if git_version.returncode != 0:
        raise RuntimeError(
            'No se encontro el comando git en el entorno. '
            'Instalalo antes de ejecutar el bootstrap desde GitHub.'
        )

    if not repo_objetivo.exists():
        print(f'Clonando repositorio desde GitHub en: {repo_objetivo}')
        clone_result = ejecutar_comando(
            ['git', 'clone', '--branch', github_branch, github_url, str(repo_objetivo)]
        )
        if clone_result.returncode != 0:
            raise RuntimeError(
                'No fue posible clonar el repositorio desde GitHub.\n'
                f'{clone_result.stderr.strip() or clone_result.stdout.strip()}'
            )
    elif (repo_objetivo / '.git').exists() and actualizar:
        print(f'Actualizando repositorio local: {repo_objetivo}')
        fetch_result = ejecutar_comando(['git', 'fetch', 'origin'], carpeta_trabajo=repo_objetivo)
        if fetch_result.returncode != 0:
            raise RuntimeError(
                'No fue posible consultar cambios remotos del repositorio.\n'
                f'{fetch_result.stderr.strip() or fetch_result.stdout.strip()}'
            )

        pull_result = ejecutar_comando(['git', 'pull', 'origin', github_branch], carpeta_trabajo=repo_objetivo)
        if pull_result.returncode != 0:
            raise RuntimeError(
                'No fue posible actualizar el repositorio local.\n'
                f'{pull_result.stderr.strip() or pull_result.stdout.strip()}'
            )

    validar_estructura_repo(repo_objetivo)

    if instalar_dependencias:
        requirements_path = repo_objetivo / 'requirements.txt'
        if not requirements_path.exists():
            raise RuntimeError(
                'Se solicito instalar dependencias, pero el repositorio no contiene requirements.txt.'
            )

        print(f'Instalando dependencias desde: {requirements_path}')
        install_result = ejecutar_comando(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)],
            carpeta_trabajo=repo_objetivo,
        )
        if install_result.returncode != 0:
            raise RuntimeError(
                'No fue posible instalar las dependencias del repositorio.\n'
                f'{install_result.stderr.strip() or install_result.stdout.strip()}'
            )

        print(
            'Dependencias instaladas. Si el entorno no reconoce paquetes nuevos, '
            'reinicia el kernel antes de continuar.'
        )

    if str(repo_objetivo) not in sys.path:
        sys.path.insert(0, str(repo_objetivo))

    return repo_objetivo
