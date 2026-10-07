import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .db import get_conn
from .routers import alumnos, cursos

app = FastAPI(title="API de Alumnos", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _inicializar_bd():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cursos (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    anio INTEGER,
                    descripcion TEXT,
                    tipo_mes TEXT NOT NULL CHECK (tipo_mes IN ('numeric', 'boolean', 'date')),
                    meses TEXT[] NOT NULL,
                    tabla TEXT UNIQUE,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def _startup():
    _inicializar_bd()


app.include_router(cursos.router)
app.include_router(alumnos.router)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse(url="/ui/")


if os.path.isdir(FRONTEND_DIR):
    app.mount("/ui/", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")