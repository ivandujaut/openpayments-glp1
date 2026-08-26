"""Ataque 09 (familia A) — ¿el frente nuevo es nuevo, o es reetiquetado?

Hallazgo bajo ataque:
  H1: Lilly redujo su gasto en endocrinología entre 2023 y 2025 (−1,85M) mientras
      Novo lo aumentó (+4,25M).
  H2: Novo destina mucho más que Lilly al grupo emergente (14,74M vs 1,46M).

El corte 03 ya encontró que un 3,64% de los profesionales cambia de especialidad
declarada entre años. Si los "cardiólogos de 2025" son en realidad los mismos
profesionales que antes se declaraban de otra forma, el frente nuevo es un
artefacto de reporte y no un movimiento comercial.

  A1  ¿Los profesionales del grupo emergente en 2025 ya recibían pagos antes?
      Si son nuevos en el dataset, el frente es genuino.
  A2  De los que ya estaban, ¿estaban declarados en OTRA especialidad?
      Ese es el reetiquetado puro.
  A3  ¿Cuánto del crecimiento de 2023→2025 aporta cada grupo (nuevos, mismos con
      misma etiqueta, mismos reetiquetados)? Es el test que decide.

Uso:  uv run analysis/ataque-09_frente-nuevo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402


def main() -> None:
    con = conectar()

    # Cada profesional del grupo emergente en 2025, clasificado por su historia.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW clasificados AS
        WITH emergentes_2025 AS (
            SELECT DISTINCT receptor_id FROM glp1
            WHERE especialidad = 'emergentes' AND anio = 2025
              AND receptor_id IS NOT NULL
        ),
        historia AS (
            SELECT e.receptor_id,
                   count(*) FILTER (g.anio < 2025)                        AS pagos_previos,
                   count(*) FILTER (g.anio < 2025
                                    AND g.especialidad = 'emergentes')    AS previos_emergente,
                   count(*) FILTER (g.anio < 2025
                                    AND g.especialidad <> 'emergentes')   AS previos_otra
            FROM emergentes_2025 e LEFT JOIN glp1 g USING (receptor_id)
            GROUP BY 1
        )
        SELECT receptor_id,
               CASE
                   WHEN pagos_previos = 0 THEN 'nuevo en el dataset'
                   WHEN previos_otra = 0 THEN 'ya estaba, misma etiqueta'
                   WHEN previos_emergente = 0 THEN 'ya estaba, REETIQUETADO'
                   ELSE 'ya estaba, etiqueta mixta'
               END AS origen
        FROM historia
        """
    )

    print("A1/A2 — de dónde salen los profesionales del grupo emergente en 2025:")
    print(con.sql(
        """
        SELECT c.origen, count(*) AS hcps,
               round(sum(g.usd)/1e6, 2) AS musd_2025,
               round(100.0*sum(g.usd)/sum(sum(g.usd)) OVER (), 1) AS pct_del_gasto
        FROM clasificados c
        JOIN glp1 g ON g.receptor_id = c.receptor_id
                   AND g.anio = 2025 AND g.especialidad = 'emergentes'
        GROUP BY 1 ORDER BY musd_2025 DESC
        """
    ).df().to_string(index=False))

    print("\nA3 — el crecimiento 2023→2025 del grupo emergente, por origen:")
    print(con.sql(
        """
        SELECT c.origen,
               round(sum(g.usd) FILTER (g.anio = 2023)/1e6, 2) AS musd_2023,
               round(sum(g.usd) FILTER (g.anio = 2025)/1e6, 2) AS musd_2025,
               round((sum(g.usd) FILTER (g.anio = 2025)
                      - sum(g.usd) FILTER (g.anio = 2023))/1e6, 2) AS delta
        FROM clasificados c
        JOIN glp1 g ON g.receptor_id = c.receptor_id AND g.especialidad = 'emergentes'
        GROUP BY 1 ORDER BY delta DESC
        """
    ).df().to_string(index=False))

    print("\n  Los REETIQUETADOS, ¿de qué especialidad venían?")
    print(con.sql(
        """
        SELECT g.especialidad AS venia_de, count(DISTINCT g.receptor_id) AS hcps,
               round(sum(g.usd)/1e6, 2) AS musd_previo
        FROM clasificados c
        JOIN glp1 g ON g.receptor_id = c.receptor_id
        WHERE c.origen = 'ya estaba, REETIQUETADO' AND g.anio < 2025
        GROUP BY 1 ORDER BY hcps DESC
        """
    ).df().to_string(index=False))


if __name__ == "__main__":
    main()
