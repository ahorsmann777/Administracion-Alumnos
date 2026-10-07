TIPO_MES = ("numeric", "boolean", "date")

MES_COLUMN_PREFIX = "mes"


def column_names(cantidad):
    return [f"{MES_COLUMN_PREFIX}{i}" for i in range(1, cantidad + 1)]


def sql_type(tipo_mes):
    return {"numeric": "DOUBLE PRECISION", "boolean": "BOOLEAN", "date": "DATE"}[tipo_mes]


def normalize_mes_value(tipo_mes, value):
    if value is None:
        return None
    if tipo_mes == "numeric":
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError("Los valores de tipo 'numeric' deben ser números.")
    if tipo_mes == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("true", "1", "si", "sí", "s"):
                return True
            if v in ("false", "0", "no", "n"):
                return False
        raise ValueError("Los valores de tipo 'boolean' deben ser verdadero/falso.")
    if tipo_mes == "date":
        if isinstance(value, str):
            try:
                from datetime import date

                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("Los valores de tipo 'date' deben usar el formato AAAA-MM-DD.")
        if hasattr(value, "isoformat"):
            return value
        raise ValueError("Los valores de tipo 'date' deben usar el formato AAAA-MM-DD.")
    raise ValueError(f"Tipo de mes '{tipo_mes}' no soportado.")


def serialize_mes_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, (int, float)):
        return value
    return str(value)