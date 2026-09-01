"""Ataque 14 — explicaciones de negocio contra "Lilly retiene más" (corte 05).

  B1. Composición: si los endocrinólogos persisten más en las DOS compañías y
      Lilly tiene más endocrinólogos, la retención extra sería mezcla, no
      gestión. Retención por categoría de especialidad y compañía.
  B2. La plata compra la retención: retención por banda de gasto anual por
      cabeza. Si a gasto igual la brecha desaparece, Lilly no retiene mejor,
      paga más.
  B3. El recorte de Novo: su rotación alta de 2021-2023 coincide con el recorte
      documentado de su programa de voz (corte 01). Rotación contra el cambio
      del presupuesto de voz del año siguiente.

Uso:  uv run analysis/ataque-14_negocio-rotacion.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_HASTA, conectar  # noqa: E402


def main() -> None:
    con = conectar()
    con.sql(
        """
        CREATE TEMP TABLE base AS
        SELECT grupo, anio, receptor_id, sum(usd) AS usd,
               any_value(especialidad) AS especialidad
        FROM glp1 WHERE grupo_naturaleza='voz' AND receptor_id IS NOT NULL
        GROUP BY 1, 2, 3
        """
    )
    con.sql(
        f"""
        CREATE TEMP TABLE pares AS
        SELECT b.*, CASE WHEN EXISTS (SELECT 1 FROM base r WHERE r.grupo=b.grupo
               AND r.anio=b.anio+1 AND r.receptor_id=b.receptor_id)
               THEN 1 ELSE 0 END AS retenido
        FROM base b WHERE b.anio < {ANIO_HASTA}
        """
    )

    print("B1 · retención por especialidad (profesional-años, retención %)")
    print(con.sql(
        """
        SELECT especialidad, grupo, count(*) AS pa,
               round(100.0*avg(retenido),1) AS ret
        FROM pares WHERE especialidad IN ('endocrinologia','primaria','NP/PA')
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).fetchall())
    print("  estandarizada (mezcla de Lilly aplicada a las tasas de Novo):")
    print(con.sql(
        """
        WITH mezcla AS (SELECT especialidad, count(*) AS w FROM pares
                        WHERE grupo='lilly' GROUP BY 1),
             tasas AS (SELECT especialidad, grupo, avg(retenido) AS r FROM pares GROUP BY 1,2)
        SELECT round(100.0*sum(m.w*t.r)/sum(m.w),1) AS novo_estandarizada
        FROM mezcla m JOIN tasas t ON t.especialidad IS NOT DISTINCT FROM m.especialidad
        WHERE t.grupo='novo'
        """
    ).fetchall(), "· cruda lilly:", con.sql(
        "SELECT round(100.0*avg(retenido),1) FROM pares WHERE grupo='lilly'").fetchall())

    print("\nB2 · retención por banda de gasto anual por cabeza")
    print(con.sql(
        """
        SELECT CASE WHEN usd < 5000 THEN 'a <5k'
                    WHEN usd < 25000 THEN 'b 5-25k'
                    WHEN usd < 75000 THEN 'c 25-75k'
                    ELSE 'd 75k+' END AS banda,
               grupo, count(*) AS pa, round(100.0*avg(retenido),1) AS ret
        FROM pares GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).fetchall())

    print("\nB2b · cuartiles propios de cada compañía (gradiente interno)")
    print(con.sql(
        """
        WITH q AS (SELECT grupo, retenido, usd,
                          ntile(4) OVER (PARTITION BY grupo ORDER BY usd) AS cuartil
                   FROM pares)
        SELECT cuartil, grupo, count(*) AS pa, round(100.0*avg(retenido),1) AS ret,
               round(median(usd)) AS usd_mediana
        FROM q GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).fetchall())

    print("\nB2c · condición de muerte de D-016: cortes a la mitad y al doble")
    for nombre, c1, c2, c3 in (("mitad", 2500, 12500, 37500),
                               ("D-016", 5000, 25000, 75000),
                               ("doble", 10000, 50000, 150000)):
        print(f"  cortes {nombre}:", con.sql(
            f"""
            SELECT CASE WHEN usd < {c1} THEN 'baja' WHEN usd < {c2} THEN 'media'
                        WHEN usd < {c3} THEN 'alta' ELSE 'tope' END AS banda,
                   grupo, round(100.0*avg(retenido),1) AS ret
            FROM pares GROUP BY 1, 2 ORDER BY 1, 2
            """
        ).fetchall())

    print("\nB3 · rotación vs cambio del presupuesto de voz del año siguiente")
    print(con.sql(
        f"""
        WITH presu AS (SELECT grupo, anio, sum(usd) AS usd FROM base GROUP BY 1,2),
             rot AS (SELECT grupo, anio, round(100.0*(1-avg(retenido)),1) AS rotacion
                     FROM pares GROUP BY 1,2)
        SELECT r.grupo, r.anio, r.rotacion,
               round(100.0*(p2.usd-p1.usd)/p1.usd,1) AS delta_presu_pct
        FROM rot r
        JOIN presu p1 ON p1.grupo=r.grupo AND p1.anio=r.anio
        JOIN presu p2 ON p2.grupo=r.grupo AND p2.anio=r.anio+1
        ORDER BY 1, 2
        """
    ).fetchall())


if __name__ == "__main__":
    main()
