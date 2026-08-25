"""Ataque 04 (familia A) — ¿el corte 02 mide personas o mide identificadores?

Hallazgo bajo ataque:
  H1: Lilly concentra más que Novo (top 100: 35,6% vs 20,4%).
  H2: El top 100 de Lilly acumula ~431 pagos promedio contra ~246 de Novo.

TODA la métrica de concentración descansa en que `Covered_Recipient_Profile_ID`
identifique a una persona de forma estable. Dos formas de que esté mal:

  A1a  Un profesional con VARIOS Profile_ID aparecería fragmentado, y la
       concentración quedaría SUBestimada. Test: buscar Profile_ID distintos
       que compartan NPI.
  A1b  Un Profile_ID que agrupe a MÁS DE UNA persona inflaría la concentración.
       Test: buscar Profile_ID con más de un NPI.
  A1c  Si el NPI es una clave alternativa válida, recalcular todo con NPI tiene
       que dar lo mismo. Es el test que decide.

Uso:  uv run analysis/ataque-04_identidad-receptor.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402


def main() -> None:
    con = conectar()

    # La vista glp1 no expone el NPI: se trae desde `pagos` por record_id.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW glp1_npi AS
        SELECT g.*, p.Covered_Recipient_NPI AS npi
        FROM glp1 g JOIN pagos p ON g.record_id = p.Record_ID
        """
    )

    print("A1a/A1b — ¿la correspondencia Profile_ID ↔ NPI es uno a uno?")
    print(con.sql(
        """
        SELECT
            count(DISTINCT receptor_id)                     AS profile_ids,
            count(DISTINCT npi)                             AS npis,
            count(*) FILTER (npi IS NULL)                   AS filas_sin_npi
        FROM glp1_npi WHERE receptor_id IS NOT NULL
        """
    ).df().to_string(index=False))

    print("\n  Profile_ID que tienen más de un NPI (inflarían la concentración):")
    print(con.sql(
        """
        SELECT count(*) AS profile_ids_con_varios_npi
        FROM (SELECT receptor_id FROM glp1_npi WHERE receptor_id IS NOT NULL
              AND npi IS NOT NULL
              GROUP BY 1 HAVING count(DISTINCT npi) > 1)
        """
    ).df().to_string(index=False))

    print("\n  NPI que aparecen bajo más de un Profile_ID (fragmentarían):")
    print(con.sql(
        """
        SELECT count(*) AS npis_con_varios_profile_id
        FROM (SELECT npi FROM glp1_npi WHERE npi IS NOT NULL
              AND receptor_id IS NOT NULL
              GROUP BY 1 HAVING count(DISTINCT receptor_id) > 1)
        """
    ).df().to_string(index=False))

    print("\nA1c — la misma métrica con NPI como clave, contra Profile_ID:")
    for clave in ("receptor_id", "npi"):
        df = con.sql(
            f"""
            WITH x AS (SELECT grupo, {clave} AS k, sum(usd) AS usd,
                              count(DISTINCT record_id) AS pagos
                       FROM glp1_npi WHERE {clave} IS NOT NULL GROUP BY 1, 2),
                 r AS (SELECT *, row_number() OVER (PARTITION BY grupo ORDER BY usd DESC) rn,
                              count(*) OVER (PARTITION BY grupo) n,
                              sum(usd) OVER (PARTITION BY grupo) total FROM x)
            SELECT grupo, any_value(n) AS red,
                   round(100.0*sum(usd) FILTER (rn <= 100)/any_value(total), 2) AS top100,
                   round(avg(pagos) FILTER (rn <= 100), 1) AS pagos_top100
            FROM r GROUP BY grupo ORDER BY grupo
            """
        ).df()
        print(f"\n  clave = {clave}")
        print(df.to_string(index=False))
        lilly = df[df.grupo == "lilly"].iloc[0]
        novo = df[df.grupo == "novo"].iloc[0]
        h1 = lilly.top100 > novo.top100
        h2 = lilly.pagos_top100 > novo.pagos_top100
        print(f"    {'✓' if h1 else '✗'} H1 (Lilly concentra más: "
              f"{lilly.top100:.2f} vs {novo.top100:.2f}, ratio {lilly.top100/novo.top100:.2f}x)")
        print(f"    {'✓' if h2 else '✗'} H2 (top 100 de Lilly con más pagos: "
              f"{lilly.pagos_top100:.1f} vs {novo.pagos_top100:.1f})")


if __name__ == "__main__":
    main()
