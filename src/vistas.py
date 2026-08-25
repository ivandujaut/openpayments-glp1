"""Vistas DuckDB del caso: capa única de nombres y filtros sobre los parquet.

Todo corte de analysis/ consulta estas vistas, nunca los parquet crudos, para
que las reglas (entidades, productos, ventana) vivan en UN solo lugar y estén
atadas a sus decisiones D-NNN.

Vive en src/ (no en scripts/) porque es librería, no paso del pipeline: la
importan los cortes, los charts y 04_checks. El CLI fino está en
scripts/03_vistas.py.

Uso:  from src.vistas import conectar  →  con = conectar()
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
PQ = ROOT / "data" / "parquet"

# D-002 (pendiente): razones sociales que cuentan como cada entidad.
# Completar DESPUÉS de listar las candidatas reales del dato y correr /decidir.
ENTIDADES: dict[str, list[str]] = {
    "novo": [],   # p. ej. ["Novo Nordisk Inc", ...]  ← desde el dato + D-002
    "lilly": [],  # p. ej. ["Eli Lilly and Company", ...]
}

# D-003 (pendiente): productos GLP-1 que entran al caso (nombre y/o NDC).
PRODUCTOS_GLP1: list[str] = []  # p. ej. ["OZEMPIC", "WEGOVY", "MOUNJARO", ...]


def conectar() -> duckdb.DuckDBPyConnection:
    """Conexión con la vista `pagos` lista. Corta si todavía no hay parquet.

    El guard vive acá y no en el CLI porque todo corte y todo chart entra por
    esta función: el mensaje útil tiene que llegarles a todos, no solo a
    scripts/03_vistas.py.
    """
    if not sorted(PQ.glob("general_*.parquet")):
        raise SystemExit(
            f"No hay parquet en {PQ}. "
            "Correr primero: uv run scripts/02_convertir_parquet.py [anio ...]"
        )
    con = duckdb.connect()
    con.sql(
        f"""
        CREATE VIEW pagos AS
        SELECT * FROM read_parquet('{PQ}/general_*.parquet',
                                   union_by_name=true, filename=true)
        """
    )
    # Vista glp1: se define recién cuando D-002/D-003/D-004 estén registradas.
    # TODO(primera sesión): crearla acá, referenciando esas decisiones.
    return con
