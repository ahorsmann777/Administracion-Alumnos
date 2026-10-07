import re

from .cursos import MES_COLUMN_PREFIX, column_names, sql_type
from .schemas import CursoCreate

TABLA_REGEX = re.compile(r"^[a-z0-9_]+$")


def _slug(nombre):
    s = re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")
    return s or "curso"


def nombre_tabla_curso(curso_id, nombre):
    base = f"curso_{_slug(nombre)}"[:40].rstrip("_")
    return f"{base}_{curso_id}"


def crear_curso(conn, datos: CursoCreate):
    meses = _normalizar_meses(datos.meses)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cursos (nombre, anio, descripcion, tipo_mes, meses)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, tabla
            """,
            (datos.nombre, datos.anio, datos.descripcion, datos.tipo_mes, meses),
        )
        fila = cur.fetchone()
        curso_id = fila["id"]
        tabla = nombre_tabla_curso(curso_id, datos.nombre)
        cur.execute("UPDATE cursos SET tabla = %s WHERE id = %s", (tabla, curso_id))
        _crear_tabla(cur, tabla, datos.tipo_mes, len(meses))
    conn.commit()
    return curso_id, tabla


def _normalizar_meses(meses):
    vistos = []
    for m in meses:
        if not isinstance(m, str) or not m.strip():
            raise ValueError("Cada mes debe ser una etiqueta no vacía.")
        if m in vistos:
            raise ValueError(f"Mes duplicado: {m}")
        vistos.append(m)
    return vistos


def _crear_tabla(cur, tabla, tipo_mes, cantidad):
    if not TABLA_REGEX.match(tabla):
        raise ValueError("Nombre de tabla inválido.")
    cols = ", ".join(
        f"{nombre} {tipo}" for nombre, tipo in zip(column_names(cantidad), [sql_type(tipo_mes)] * cantidad, strict=True)
    )
    cur.execute(
        f"""
        CREATE TABLE {tabla} (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            mail TEXT,
            observaciones TEXT,
            {cols}
        )
        """
    )


def agregar_meses_curso(conn, curso, meses_nuevos):
    meses_nuevos = _normalizar_meses(meses_nuevos)
    existentes = set(curso["meses"])
    nuevos = [m for m in meses_nuevos if m not in existentes]
    if not nuevos:
        raise ValueError("Los meses ya existen en el curso.")
    inicio = len(curso["meses"]) + 1
    with conn.cursor() as cur:
        for offset, m in enumerate(nuevos):
            numero = inicio + offset
            cur.execute(
                f"ALTER TABLE {curso['tabla']} ADD COLUMN {MES_COLUMN_PREFIX}{numero} {sql_type(curso['tipo_mes'])}"
            )
        for m in nuevos:
            cur.execute(
                "UPDATE cursos SET meses = array_append(meses, %s) WHERE id = %s",
                (m, curso["id"]),
            )
    conn.commit()
    return nuevos


def eliminar_curso(conn, curso):
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {curso['tabla']}")
        cur.execute("DELETE FROM cursos WHERE id = %s", (curso["id"],))
    conn.commit()


def obtener_curso(conn, curso_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM cursos WHERE id = %s", (curso_id,))
        return cur.fetchone()


def contar_alumnos(conn, curso):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM {curso['tabla']}")
        return cur.fetchone()["total"]