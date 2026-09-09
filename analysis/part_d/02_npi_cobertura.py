"""¿Se puede cruzar Open Payments con Part D por NPI? Medición, no supuesto.

La metodología oficial de Part D (CMS, abril 2026, MUP_DPR_RY26_20260421) dice
textualmente que "NPIs are not available in the Open Payments data and thus
merges must be conducted using text-string identification fields such as name
and address". Los Parquet de PY2021-2025 SÍ traen una columna
`Covered_Recipient_NPI`. Una de las dos cosas está desactualizada, y de cuál
sea depende que el caso exista.

Este corte no interpreta: cuenta. Por año y por grupo, cuántos pagos GLP-1
traen NPI no nulo, cuánto dinero representan, y cuántos NPI distintos hay.

Salida: JSON a findings/cache/part_d-01_npi_cobertura.json + stdout.

Uso:  uv run analysis/part_d/02_npi_cobertura.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.vistas import conectar  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-01_npi_cobertura.json"


def cobertura_por_anio(con) -> list[dict]:
    """Pagos GLP-1 con y sin NPI, por año. Unidad: Record_ID (no par
    record-producto), para no contar dos veces un pago multi-producto."""
    return con.sql(
        """
        WITH uno_por_pago AS (
            SELECT DISTINCT ON (g.record_id)
                   g.record_id, g.anio, g.usd_fila, p.Covered_Recipient_NPI AS npi
            FROM glp1 g
            JOIN pagos p ON p.Record_ID = g.record_id
        )
        SELECT anio,
               count(*)                                        AS pagos,
               count(npi)                                      AS pagos_con_npi,
               round(100.0 * count(npi) / count(*), 2)         AS pct_pagos_con_npi,
               round(sum(usd_fila), 2)                         AS usd,
               round(sum(CASE WHEN npi IS NOT NULL THEN usd_fila ELSE 0 END), 2)
                                                               AS usd_con_npi,
               round(100.0 * sum(CASE WHEN npi IS NOT NULL THEN usd_fila ELSE 0 END)
                     / sum(usd_fila), 2)                       AS pct_usd_con_npi,
               count(DISTINCT npi)                             AS npi_distintos
        FROM uno_por_pago
        GROUP BY anio ORDER BY anio
        """
    ).df().to_dict("records")


def cobertura_por_tipo(con) -> list[dict]:
    """Dónde falta el NPI: por tipo de receptor (individuo vs. entidad)."""
    return con.sql(
        """
        WITH uno_por_pago AS (
            SELECT DISTINCT ON (g.record_id)
                   g.record_id, g.tipo_receptor, g.usd_fila,
                   p.Covered_Recipient_NPI AS npi
            FROM glp1 g
            JOIN pagos p ON p.Record_ID = g.record_id
        )
        SELECT coalesce(tipo_receptor, '(nulo)')        AS tipo_receptor,
               count(*)                                 AS pagos,
               count(npi)                               AS pagos_con_npi,
               round(100.0 * count(npi) / count(*), 2)  AS pct_con_npi,
               round(sum(usd_fila), 2)                  AS usd
        FROM uno_por_pago
        GROUP BY 1 ORDER BY usd DESC
        """
    ).df().to_dict("records")


def receptores_unicos(con) -> dict:
    """Universo de receptores GLP-1 con NPI: el lado izquierdo del cruce.

    Un receptor puede cobrar en varios años; se cuenta el NPI una vez y se
    suma todo su dinero GLP-1 prorrateado (D-004).
    """
    fila = con.sql(
        """
        WITH uno_por_pago AS (
            SELECT DISTINCT ON (g.record_id)
                   g.record_id, g.receptor_id, g.usd_fila,
                   p.Covered_Recipient_NPI AS npi
            FROM glp1 g
            JOIN pagos p ON p.Record_ID = g.record_id
        )
        SELECT count(DISTINCT npi)                              AS npi_unicos,
               count(DISTINCT receptor_id)                      AS profile_id_unicos,
               round(sum(CASE WHEN npi IS NOT NULL THEN usd_fila ELSE 0 END), 2)
                                                                AS usd_con_npi,
               round(sum(usd_fila), 2)                          AS usd_total
        FROM uno_por_pago
        """
    ).df().to_dict("records")[0]
    # ¿Un NPI puede tener más de un Profile_ID, o al revés? Si la relación no
    # es 1:1 el cruce por NPI puede duplicar dinero, y hay que saberlo antes.
    fila["pares_npi_profile"] = int(
        con.sql(
            """
            WITH uno_por_pago AS (
                SELECT DISTINCT ON (g.record_id)
                       g.record_id, g.receptor_id, p.Covered_Recipient_NPI AS npi
                FROM glp1 g JOIN pagos p ON p.Record_ID = g.record_id
            )
            SELECT count(*) FROM (
                SELECT DISTINCT npi, receptor_id FROM uno_por_pago
                WHERE npi IS NOT NULL AND receptor_id IS NOT NULL
            )
            """
        ).fetchone()[0]
    )
    return fila


def main() -> int:
    con = conectar()
    salida = {
        "fuente": "CMS Open Payments General Payments PY2021-2025, parquet locales",
        "por_anio": cobertura_por_anio(con),
        "por_tipo_receptor": cobertura_por_tipo(con),
        "receptores": receptores_unicos(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps(salida, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
