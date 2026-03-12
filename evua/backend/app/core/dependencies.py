"""
Dependency Injection helpers for FastAPI.
"""
from typing import Annotated

from fastapi import Depends

from .config import Settings, get_settings

# Readable alias used in route type hints
SettingsDep = Annotated[Settings, Depends(get_settings)]
