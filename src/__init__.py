"""
Módulo principal del paquete `src`.

Este archivo inicializa el paquete y gestiona la importación diferida (lazy loading)
de los submódulos principales (`export`, `processing`, `ui`, `visualization`)
para optimizar los tiempos de carga y evitar importaciones circulares.
"""
from __future__ import annotations

import importlib
from types import ModuleType

# Define explícitamente los submódulos públicos disponibles en el paquete.
__all__ = ['export', 'processing', 'ui', 'visualization']


def __getattr__(name: str) -> ModuleType:
    """
    Gestiona la importación dinámica de submódulos (Lazy Loading).

    Parámetros:
        name (str): Nombre del submódulo a importar.

    Retorna:
        ModuleType: El módulo importado dinámicamente.

    Lanza:
        AttributeError: Si el módulo solicitado no está definido en `__all__`.
    """
    # Verifica si el módulo solicitado es parte de la API pública
    if name in __all__:
        # Importa el módulo solo en el momento en que es requerido
        return importlib.import_module(f'{__name__}.{name}')
    
    # Lanza error si se intenta acceder a un atributo no definido
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')