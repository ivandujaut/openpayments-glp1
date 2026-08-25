"""Ataque 07 (familia A) — ¿la especialidad declarada es estable?

Hallazgo bajo ataque:
  H1: Endocrinología recibe mucho más por cabeza que NP/PA (12.129 vs 293).
  H2: Lilly destina más de su gasto a endocrinología que Novo (43,6% vs 31,5%).

`Covered_Recipient_Specialty_1` lo declara el REPORTANTE, no el profesional. Tres
formas de que el corte 03 sea un artefacto de reporte:

  A1  Un mismo profesional declarado con distintas especialidades en AÑOS
      distintos. Fragmenta la métrica por cabeza.
  A2  EL PEOR CASO: un mismo profesional declarado distinto por CADA COMPAÑÍA.
      Si Lilly tiende a declarar "endocrinología" donde Novo declara "primaria",
      H2 mide estilos de reporte y no estrategias comerciales.
  A3  Si la taxonomía cambió entre años, las categorías de D-008 no son
      comparables a lo largo de la ventana.

Uso:  uv run analysis/ataque-07_estabilidad-especialidad.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402


def main() -> None:
    con = conectar()

    print("A1 — ¿un mismo profesional cambia de especialidad entre años?")
    print(con.sql(
        """
        SELECT count(*) AS hcps_con_pagos_en_2omas_anios,
               count(*) FILTER (n_especialidades > 1) AS cambian_de_especialidad,
               round(100.0*count(*) FILTER (n_especialidades > 1)/count(*), 2) AS pct
        FROM (
            SELECT receptor_id,
                   count(DISTINCT anio) AS n_anios,
                   count(DISTINCT especialidad) AS n_especialidades
            FROM glp1 WHERE receptor_id IS NOT NULL AND especialidad IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT anio) > 1
        )
        """
    ).df().to_string(index=False))

    print("\nA2 — EL PEOR CASO: ¿el mismo profesional, declarado distinto por cada compañía?")
    print(con.sql(
        """
        SELECT count(*) AS hcps_pagados_por_ambas,
               count(*) FILTER (n_especialidades > 1) AS declarados_distinto,
               round(100.0*count(*) FILTER (n_especialidades > 1)/count(*), 2) AS pct
        FROM (
            SELECT receptor_id,
                   count(DISTINCT especialidad) AS n_especialidades
            FROM glp1 WHERE receptor_id IS NOT NULL AND especialidad IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT grupo) = 2
        )
        """
    ).df().to_string(index=False))

    print("\n  Si los hay, ¿en qué dirección? (Lilly declara endocrino donde Novo no, o al revés)")
    print(con.sql(
        """
        WITH ambas AS (
            SELECT receptor_id FROM glp1
            WHERE receptor_id IS NOT NULL AND especialidad IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT grupo) = 2
                          AND count(DISTINCT especialidad) > 1
        ),
        por_grupo AS (
            SELECT g.receptor_id, g.grupo, any_value(g.especialidad) AS esp
            FROM glp1 g JOIN ambas a USING (receptor_id)
            WHERE g.especialidad IS NOT NULL
            GROUP BY 1, 2
        )
        SELECT n.esp AS novo_declara, l.esp AS lilly_declara, count(*) AS hcps
        FROM por_grupo n JOIN por_grupo l USING (receptor_id)
        WHERE n.grupo = 'novo' AND l.grupo = 'lilly' AND n.esp <> l.esp
        GROUP BY 1, 2 ORDER BY hcps DESC LIMIT 8
        """
    ).df().to_string(index=False))

    print("\nA3 — ¿la taxonomía cambió entre años?")
    print(con.sql(
        """
        SELECT anio, count(DISTINCT especialidad_cruda) AS taxonomias,
               count(DISTINCT especialidad) AS categorias_d008
        FROM glp1 WHERE especialidad_cruda IS NOT NULL
        GROUP BY 1 ORDER BY 1
        """
    ).df().to_string(index=False))

    print("\n  Taxonomías que aparecen en unos años y no en otros:")
    print(con.sql(
        """
        SELECT count(*) AS taxonomias_no_presentes_en_los_5_anios
        FROM (SELECT especialidad_cruda FROM glp1 WHERE especialidad_cruda IS NOT NULL
              GROUP BY 1 HAVING count(DISTINCT anio) < 5)
        """
    ).df().to_string(index=False))


if __name__ == "__main__":
    main()
