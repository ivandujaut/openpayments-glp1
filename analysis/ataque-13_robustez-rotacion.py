"""Ataque 13 — robustez de la rotación (corte 05).

Tres frentes contra los hallazgos preliminares:
  A1. Sensibilidad a D-012: la membresía por >=1 pago, recalculada con umbrales
      de USD 1.000, USD 5.000 y >=2 pagos. Si el orden (Lilly retiene más) o el
      no-disparo del 30% dependen del umbral, el hallazgo muere.
  A2. Orden de salidas de D-015: reasignado se evalúa antes que fichado. Si el
      solapamiento (voz misma Y+1 y también rival Y+1) es material, "nadie
      ficha" es un artefacto del orden.
  A3. Censura a derecha en la permanencia: el promedio de años activos por
      compañía, partido por año de entrada. Si la brecha 2,22 vs 2,69 se
      invierte al comparar cohortes de entrada iguales, el promedio agregado
      no se publica jamás.

Uso:  uv run analysis/ataque-13_robustez-rotacion.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_HASTA, conectar  # noqa: E402


def rotacion(con, filtro_membresia: str, etiqueta: str) -> None:
    con.sql("DROP TABLE IF EXISTS m2")
    con.sql(
        f"""
        CREATE TEMP TABLE m2 AS
        SELECT grupo, anio, receptor_id
        FROM glp1
        WHERE grupo_naturaleza = 'voz' AND receptor_id IS NOT NULL
        GROUP BY 1, 2, 3
        HAVING {filtro_membresia}
        """
    )
    filas = con.sql(
        f"""
        SELECT m.grupo,
               round(avg(100.0 * (1 - r.ok)), 1) AS rotacion_prom
        FROM (
          SELECT m.grupo, m.anio, m.receptor_id,
                 CASE WHEN EXISTS (SELECT 1 FROM m2 r WHERE r.grupo=m.grupo
                      AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id)
                 THEN 1 ELSE 0 END AS ok
          FROM m2 m WHERE m.anio < {ANIO_HASTA}) AS r(grupo, anio, receptor_id, ok)
        JOIN m2 m ON m.grupo=r.grupo AND m.anio=r.anio AND m.receptor_id=r.receptor_id
        GROUP BY 1 ORDER BY 1
        """
    ).fetchall()
    maximo = con.sql(
        f"""
        WITH pares AS (
          SELECT m.grupo, m.anio, count(*) AS n,
                 count(*) FILTER (EXISTS (SELECT 1 FROM m2 r WHERE r.grupo=m.grupo
                      AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id)) AS ret
          FROM m2 m WHERE m.anio < {ANIO_HASTA} GROUP BY 1, 2)
        SELECT grupo, round(max(100.0*(n-ret)/n),1) FROM pares GROUP BY 1 ORDER BY 1
        """
    ).fetchall()
    print(f"  {etiqueta}: promedio {filas} · máximo anual {maximo}")


def main() -> None:
    con = conectar()

    print("A1 · sensibilidad al umbral de membresía (D-012)")
    rotacion(con, "TRUE", ">=1 pago (D-012, la vigente)")
    rotacion(con, "sum(usd) >= 1000", ">= USD 1.000")
    rotacion(con, "sum(usd) >= 5000", ">= USD 5.000")
    rotacion(con, "count(DISTINCT record_id) >= 2", ">=2 pagos")

    print("\nA2 · solapamiento de salidas (misma Y rival a la vez en Y+1)")
    con.sql(
        """
        CREATE TEMP TABLE miembros AS
        SELECT DISTINCT grupo, anio, receptor_id
        FROM glp1 WHERE grupo_naturaleza='voz' AND receptor_id IS NOT NULL
        """
    )
    print(con.sql(
        f"""
        SELECT m.grupo, count(*) AS salen,
               count(*) FILTER (voz_misma AND voz_rival) AS ambas
        FROM (
          SELECT m.grupo, m.receptor_id,
                 EXISTS (SELECT 1 FROM miembros r WHERE r.grupo=m.grupo
                     AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id) AS sigue,
                 EXISTS (SELECT 1 FROM voz_entidades v WHERE v.grupo=m.grupo
                     AND v.anio=m.anio+1 AND v.receptor_id=m.receptor_id) AS voz_misma,
                 EXISTS (SELECT 1 FROM miembros r WHERE r.grupo<>m.grupo
                     AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id) AS voz_rival
          FROM miembros m WHERE m.anio < {ANIO_HASTA}) m(grupo, receptor_id, sigue, voz_misma, voz_rival)
        WHERE NOT sigue GROUP BY 1 ORDER BY 1
        """
    ).fetchall())

    print("\nA3 · permanencia por año de entrada (censura a derecha)")
    print(con.sql(
        """
        WITH pp AS (
          SELECT grupo, receptor_id, min(anio) AS entrada,
                 count(DISTINCT anio) AS anios
          FROM miembros GROUP BY 1, 2)
        SELECT entrada, grupo, count(*) AS hcps, round(avg(anios),2) AS anios_prom
        FROM pp GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).fetchall())


if __name__ == "__main__":
    main()
