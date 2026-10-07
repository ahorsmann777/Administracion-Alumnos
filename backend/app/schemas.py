from typing import Any, Optional

from pydantic import BaseModel, Field


class CursoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    tipo_mes: str
    meses: list[str] = Field(min_length=1, description="Etiquetas de columnas mes (ej. Marzo 2026)")


class CursoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    agregar_meses: Optional[list[str]] = None


class CursoOut(BaseModel):
    id: int
    nombre: str
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    tipo_mes: str
    meses: list[str]
    tabla: str
    creado_en: str
    cantidad_alumnos: int = 0


class AlumnoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    mail: Optional[str] = None
    observaciones: Optional[str] = None
    mes: dict[str, Any] = Field(default_factory=dict)


class AlumnoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    mail: Optional[str] = None
    observaciones: Optional[str] = None
    mes: Optional[dict[str, Any]] = None