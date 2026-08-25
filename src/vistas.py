"""Vistas DuckDB del caso: capa única de nombres y filtros sobre los parquet.

Todo corte de analysis/ consulta estas vistas, nunca los parquet crudos, para
que las reglas (entidades, productos, ventana) vivan en UN solo lugar y estén
atadas a sus decisiones D-NNN.

Vive en src/ (no en scripts/) porque es librería, no paso del pipeline: la
importan los cortes, los charts y 04_checks. El CLI fino está en
scripts/03_vistas.py.

Uso:  from src.vistas import conectar  →  con = conectar()
      con.sql("SELECT * FROM glp1")
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
PQ = ROOT / "data" / "parquet"

# D-001: ventana temporal de la serie. PY2021 es el primer año con
# non-physician practitioners como covered recipients; cruzar esa ruptura
# mezcla cambio legal con cambio de mercado.
ANIO_DESDE, ANIO_HASTA = 2021, 2025

# D-002: la pertenencia se define por ID de la entidad que PAGA
# (Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID), nunca por
# coincidencia de texto sobre la razón social: un ILIKE '%novo%' captura
# Novocure, PolyNovo y Novonate, que no tienen relación con Novo Nordisk.
# Alcance: grupo corporativo completo.
ENTIDADES: dict[str, tuple[int, ...]] = {
    "novo": (
        100000000144,  # Novo Nordisk Inc
        100000000163,  # Novo Nordisk AS
        100000000155,  # Novo Nordisk Health Care AG
        100000196804,  # Novo Nordisk US R&D / Research Center Seattle
    ),
    "lilly": (
        100000000066,  # Lilly USA, LLC
        100000000088,  # Eli Lilly and Company
        100000000331,  # Eli Lilly Export S.A. Puerto Rico Branch
    ),
}

# Quedan FUERA por decisión, no por olvido (ver D-002): Avid Radiopharmaceuticals
# (100000005383) e ImClone Systems (100000000063) son subsidiarias de Lilly con
# nombre propio, sin aporte a GLP-1. El check contra Submitting en 04_checks las
# vuelve a exponer en cada corrida para que la exclusión siga siendo consciente.

# D-003: la clase GLP-1 del caso. Clave = nombre normalizado a MAYÚSCULAS; el
# NDC es verificación, no clave. La normalización no es cosmética: Rybelsus
# aparece escrito de dos formas y un match sensible a mayúsculas pierde el 24%.
# "GLP-1" se usa en sentido COMERCIAL: tirzepatida (Mounjaro, Zepbound) es un
# agonista dual GIP/GLP-1, no un GLP-1 puro, y se incluye porque define el
# mercado. Es la simplificación más atacable del caso y el writeup debe decirlo.
GLP1: dict[str, dict[str, str]] = {
    "OZEMPIC": {"ndc": "0169-4132-12", "grupo": "novo", "molecula": "semaglutida", "area": "Diabetes"},
    "RYBELSUS": {"ndc": "0169-4303-13", "grupo": "novo", "molecula": "semaglutida", "area": "Diabetes"},
    "WEGOVY": {"ndc": "0169-4525-14", "grupo": "novo", "molecula": "semaglutida", "area": "Obesity"},
    "SAXENDA": {"ndc": "0169-2800-15", "grupo": "novo", "molecula": "liraglutida", "area": "Obesity"},
    "VICTOZA": {"ndc": "0169-4060-12", "grupo": "novo", "molecula": "liraglutida", "area": "Diabetes"},
    "XULTOPHY 100/3.6": {"ndc": "0169-2911-15", "grupo": "novo", "molecula": "degludec + liraglutida", "area": "Diabetes"},
    "MOUNJARO": {"ndc": "0002-1506-80", "grupo": "lilly", "molecula": "tirzepatida", "area": "Diabetes"},
    "ZEPBOUND": {"ndc": "0002-2457-80", "grupo": "lilly", "molecula": "tirzepatida", "area": "Obesity"},
    "TRULICITY": {"ndc": "0002-1433-80", "grupo": "lilly", "molecula": "dulaglutida", "area": "Diabetes"},
}

N_SLOTS = 5  # el dataset declara hasta 5 productos por fila

_COL_NOMBRE = "Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_{i}"
_COL_NDC = "Associated_Drug_or_Biological_NDC_{i}"


def _sql_lista(valores) -> str:
    """Literal SQL de una lista, con las comillas simples escapadas."""
    return "(" + ", ".join("'" + str(v).replace("'", "''") + "'" for v in valores) + ")"


def conectar() -> duckdb.DuckDBPyConnection:
    """Conexión con las vistas `pagos` y `glp1` listas.

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
    _crear_vista_glp1(con)
    return con


def _crear_vista_glp1(con: duckdb.DuckDBPyConnection) -> None:
    """Vista `glp1`: UNA FILA POR (Record_ID, producto GLP-1).

    Aplica D-001 (ventana), D-002 (entidades), D-003 (productos) y D-004
    (prorrateo). Ojo con la granularidad: un pago que declara dos GLP-1 aparece
    como dos filas, cada una con su parte del monto. `sum(usd)` da el total
    prorrateado sin duplicar; para contar PAGOS y no pares, usar
    `count(DISTINCT record_id)`.
    """
    ids = ENTIDADES["novo"] + ENTIDADES["lilly"]
    nombres = ", ".join(f"upper({_COL_NOMBRE.format(i=i)})" for i in range(1, N_SLOTS + 1))
    todos = ", ".join(_COL_NOMBRE.format(i=i) for i in range(1, N_SLOTS + 1))
    lista_glp1 = _sql_lista(GLP1)
    casos_grupo = " ".join(
        f"WHEN {_sql_lista([p])[1:-1]} THEN '{d['grupo']}'" for p, d in GLP1.items()
    )
    casos_area = " ".join(
        f"WHEN {_sql_lista([p])[1:-1]} THEN '{d['area']}'" for p, d in GLP1.items()
    )
    casos_mol = " ".join(
        f"WHEN {_sql_lista([p])[1:-1]} THEN '{d['molecula']}'" for p, d in GLP1.items()
    )

    con.sql(
        f"""
        CREATE VIEW glp1 AS
        WITH base AS (
            SELECT
                Record_ID                                   AS record_id,
                Program_Year                                AS anio,
                Date_of_Payment                             AS fecha,
                Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID AS entidad_id,
                Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name AS entidad,
                Nature_of_Payment_or_Transfer_of_Value      AS naturaleza,
                Covered_Recipient_Type                      AS tipo_receptor,
                Covered_Recipient_Specialty_1               AS especialidad_cruda,
                Covered_Recipient_Profile_ID                AS receptor_id,
                Recipient_State                             AS estado,
                Number_of_Payments_Included_in_Total_Amount AS n_pagos_agregados,
                Total_Amount_of_Payment_USDollars           AS usd_fila,
                -- D-004: el denominador del prorrateo son TODOS los productos
                -- declarados, no solo los GLP-1: una comida que cubre Ozempic
                -- y Jardiance aporta la mitad a GLP-1, no el total.
                len(list_filter([{todos}], x -> x IS NOT NULL)) AS n_productos,
                list_filter([{nombres}], x -> x IN {lista_glp1}) AS productos_glp1
            FROM pagos
            WHERE Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID IN {ids}
              AND Program_Year BETWEEN {ANIO_DESDE} AND {ANIO_HASTA}
        )
        SELECT
            b.record_id, b.anio, b.fecha,
            p.producto,
            CASE p.producto {casos_grupo} END AS grupo,
            CASE p.producto {casos_mol}   END AS molecula,
            CASE p.producto {casos_area}  END AS indicacion,
            b.usd_fila / b.n_productos          AS usd,
            b.usd_fila, b.n_productos,
            len(b.productos_glp1)               AS n_glp1_en_fila,
            b.entidad_id, b.entidad, b.naturaleza, b.tipo_receptor,
            b.especialidad_cruda, b.receptor_id, b.estado, b.n_pagos_agregados
        FROM base b, UNNEST(b.productos_glp1) AS p(producto)
        """
    )
