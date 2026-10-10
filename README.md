# API de Administración de Alumnos en desarrollo #

Web API (FastAPI + PostgreSQL) para administrar alumnos por curso. Cada curso
se materializa como una **tabla propia** en PostgreSQL con columnas `Nombre`,
`Mail`, `mes1..mesN`, `Observaciones`. La cantidad de columnas `mes` y su tipo
de dato (`numeric`, `boolean` o `date`) se definen al crear el curso desde un
**calendario interactivo** en la interfaz web.

## Requisitos

- Python 3.10+
- PostgreSQL 14 (servicio activo en `127.0.0.1:5432`)

## Configuración de la base de datos

La API conecta con el rol `alumnos_api` en la base `alumnos`. Si todavía no
existen, créalos una sola vez (desde un usuario con privilegios de superusuario):

```sql
CREATE ROLE alumnos_api LOGIN PASSWORD 'alumnos_api_2026*';
CREATE DATABASE alumnos OWNER alumnos_api;
```

La cadena de conexión se configura en el archivo `.env`
(ver `.env.example`). Los metadatos de los cursos se guardan en la tabla
`cursos` y cada curso crea su propia tabla `curso_<nombre>_<id>`.

## Ejecución

```bash
./run.sh
```

o manualmente:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r backend/requirements.txt
./.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

- Interfaz web: http://127.0.0.1:8000/
- Documentación OpenAPI (swagger): http://127.0.0.1:8000/docs

## Endpoints principales

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET / POST | `/api/cursos` | Listar / crear curso |
| GET / PATCH / DELETE | `/api/cursos/{id}` | Detalle, editar o eliminar curso (al crear/agregar `meses` se crean columnas `mes1..mesN`) |
| GET / POST | `/api/cursos/{id}/alumnos` | Listar (búsqueda y paginación) / dar de alta alumno |
| GET / PATCH / DELETE | `/api/cursos/{id}/alumnos/{alumno_id}` | Detalle, editar o eliminar alumno |
| GET | `/api/cursos/{id}/alumnos/export.csv` | Exportar el curso a CSV |

Los valores de `mes1..mesN` en el body se envían como objeto: `{ "mes": { "mes1": 9.5, "mes2": null } }`.
Para cursos tipo `boolean` se acepta `true/false`, y para `date` el formato `AAAA-MM-DD`.

## Estructura

```
backend/app/
  main.py        # App FastAPI + inicialización de la tabla `cursos`
  config.py      # Lectura de .env
  db.py          # Conexión PostgreSQL
  servicio.py    # DDL dinámico de tablas por curso
  cursos.py      # Helpers de validación de columnas mes
  schemas.py     # Modelos Pydantic
  routers/       # Endpoints de cursos y alumnos
frontend/        # UI simple (HTML/CSS/JS) servida por FastAPI
```# Administracion-Alumnos
