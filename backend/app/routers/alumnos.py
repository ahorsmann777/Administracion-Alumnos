import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..cursos import column_names, normalize_mes_value, serialize_mes_value
from ..db import get_db
from ..schemas import AlumnoIn, AlumnoUpdate
from ..servicio import obtener_curso

router = APIRouter(prefix="/api/cursos/{curso_id}/alumnos", tags=["alumnos"])


def _get_curso(conn, curso_id):
    curso = obtener_curso(conn, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado.")
    return curso


def _columnas_mes(curso):
    return column_names(len(curso["meses"]))


def _alumno_a_dict(fila, curso):
    mes = {nombre: serialize_mes_value(fila[nombre]) for nombre in _columnas_mes(curso)}
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "mail": fila["mail"],
        "observaciones": fila["observaciones"],
        "mes": mes,
    }


def _traer_alumno(conn, curso, alumno_id, raw=False):
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {curso['tabla']} WHERE id = %s", (alumno_id,))
        fila = cur.fetchone()
    if not fila:
        raise HTTPException(status_code=404, detail="Alumno no encontrado.")
    return fila if raw else _alumno_a_dict(fila, curso)


def _validar_mes(curso, mes):
    nombres = _columnas_mes(curso)
    validas = set(nombres)
    for clave, valor in (mes or {}).items():
        if clave not in validas:
            raise ValueError(f"Columna mes inválida: {clave}. Válidas: {', '.join(nombres)}")
        normalize_mes_value(curso["tipo_mes"], valor)
    return nombres


def _validar_mes_http(curso, mes):
    try:
        return _validar_mes(curso, mes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("")
def listar_alumnos(
    curso_id: int,
    conn=Depends(get_db),
    buscar: str | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=50, ge=1, le=200),
):
    curso = _get_curso(conn, curso_id)
    donde = ""
    params = []
    if buscar:
        donde = " WHERE nombre ILIKE %s OR mail ILIKE %s"
        params = [f"%{buscar}%", f"%{buscar}%"]
    offset = (pagina - 1) * limite
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM {curso['tabla']}{donde}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"SELECT * FROM {curso['tabla']}{donde} ORDER BY id LIMIT %s OFFSET %s",
            params + [limite, offset],
        )
        filas = cur.fetchall()
    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "items": [_alumno_a_dict(f, curso) for f in filas],
    }


@router.get("/export.csv")
def exportar_csv(curso_id: int, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["\ufeffNombre", "Mail", *curso["meses"], "Observaciones"])
    nombres = _columnas_mes(curso)
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT nombre, mail, observaciones, {', '.join(nombres)} FROM {curso['tabla']} ORDER BY id"
        )
        for fila in cur.fetchall():
            writer.writerow(
                [
                    fila["nombre"],
                    fila["mail"],
                    *[serialize_mes_value(fila[n]) for n in nombres],
                    fila["observaciones"],
                ]
            )
    buffer.seek(0)
    nombre_archivo = curso["nombre"].replace(" ", "_")
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="alumnos_{nombre_archivo}.csv"'},
    )


@router.post("", status_code=201)
def crear_alumno(curso_id: int, datos: AlumnoIn, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    nombres = _validar_mes_http(curso, datos.mes)
    valores_mes = [normalize_mes_value(curso["tipo_mes"], datos.mes.get(n)) for n in nombres]
    placeholders = ", ".join(["%s"] * len(nombres))
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {curso['tabla']} (nombre, mail, observaciones, {', '.join(nombres)})
            VALUES (%s, %s, %s, {placeholders})
            RETURNING id
            """,
            (datos.nombre, datos.mail, datos.observaciones, *valores_mes),
        )
        nuevo_id = cur.fetchone()["id"]
    conn.commit()
    return _traer_alumno(conn, curso, nuevo_id)


@router.get("/{alumno_id}")
def detalle_alumno(curso_id: int, alumno_id: int, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    return _traer_alumno(conn, curso, alumno_id)


@router.patch("/{alumno_id}")
def actualizar_alumno(curso_id: int, alumno_id: int, datos: AlumnoUpdate, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    nombres = _validar_mes_http(curso, datos.mes)
    campos, valores = [], []
    if datos.nombre is not None:
        campos.append("nombre = %s")
        valores.append(datos.nombre)
    if datos.mail is not None:
        campos.append("mail = %s")
        valores.append(datos.mail)
    if datos.observaciones is not None:
        campos.append("observaciones = %s")
        valores.append(datos.observaciones)
    for nombre in nombres:
        if nombre in (datos.mes or {}):
            campos.append(f"{nombre} = %s")
            valores.append(normalize_mes_value(curso["tipo_mes"], datos.mes[nombre]))
    if not campos:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar.")
    valores.append(alumno_id)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE {curso['tabla']} SET {', '.join(campos)} WHERE id = %s", valores)
    conn.commit()
    return _traer_alumno(conn, curso, alumno_id)


@router.delete("/{alumno_id}", status_code=204)
def eliminar_alumno(curso_id: int, alumno_id: int, conn=Depends(get_db)):
    curso = _get_curso(conn, curso_id)
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {curso['tabla']} WHERE id = %s", (alumno_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alumno no encontrado.")
    conn.commit()