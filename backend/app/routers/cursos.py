from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictRow

from ..db import get_db
from ..cursos import TIPO_MES
from ..schemas import CursoCreate, CursoOut, CursoUpdate
from ..servicio import (
    agregar_meses_curso,
    contar_alumnos,
    crear_curso,
    eliminar_curso,
    obtener_curso,
)

router = APIRouter(prefix="/api/cursos", tags=["cursos"])


def _out(curso: RealDictRow, cantidad_alumnos: int = 0) -> CursoOut:
    return CursoOut(
        id=curso["id"],
        nombre=curso["nombre"],
        anio=curso["anio"],
        descripcion=curso["descripcion"],
        tipo_mes=curso["tipo_mes"],
        meses=list(curso["meses"]),
        tabla=curso["tabla"],
        creado_en=curso["creado_en"].isoformat(),
        cantidad_alumnos=cantidad_alumnos,
    )


def _get_curso(conn, curso_id):
    curso = obtener_curso(conn, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado.")
    return curso


@router.get("", response_model=list[CursoOut])
def listar_cursos(conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM cursos ORDER BY id DESC")
        cursos = cur.fetchall()
    salida = []
    for c in cursos:
        salida.append(_out(c, contar_alumnos(conn, c)))
    return salida


@router.post("", response_model=CursoOut, status_code=201)
def crear( datos: CursoCreate, conn=Depends(get_db)):
    if datos.tipo_mes not in TIPO_MES:
        raise HTTPException(status_code=422, detail=f"tipo_mes debe ser uno de: {', '.join(TIPO_MES)}")
    try:
        curso_id, tabla = crear_curso(conn, datos)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    curso = obtener_curso(conn, curso_id)
    return _out(curso)


@router.get("/{curso_id}", response_model=CursoOut)
def detalle(curso_id: int, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    return _out(curso, contar_alumnos(conn, curso))


@router.patch("/{curso_id}", response_model=CursoOut)
def actualizar(curso_id: int, datos: CursoUpdate, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    campos, valores = [], []
    if datos.nombre is not None:
        campos.append("nombre = %s")
        valores.append(datos.nombre)
    if datos.anio is not None:
        campos.append("anio = %s")
        valores.append(datos.anio)
    if datos.descripcion is not None:
        campos.append("descripcion = %s")
        valores.append(datos.descripcion)
    if campos:
        set_sql = ", ".join(campos)
        valores.append(curso_id)
        with conn.cursor() as cur:
            cur.execute(f"UPDATE cursos SET {set_sql} WHERE id = %s", valores)
        conn.commit()
    if datos.agregar_meses:
        try:
            agregar_meses_curso(conn, curso, datos.agregar_meses)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    curso = _get_curso(conn, curso_id)
    return _out(curso, contar_alumnos(conn, curso))


@router.delete("/{curso_id}", status_code=204)
def eliminar(curso_id: int, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    eliminar_curso(conn, curso)