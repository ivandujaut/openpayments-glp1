"""Ataque 03 (familia C) — ¿otro mecanismo produce el mismo gráfico?

Hallazgo bajo ataque:
  H1: Lilly > Novo en DÓLARES en 2023 y 2024.
  H2: Novo > Lilly en CANTIDAD DE PAGOS los cinco años.

  C1  Un puñado de pagos gigantes mueve el agregado. Si al sacar el 1% más caro
      de cada compañía la inversión desaparece, H1 habla de unos pocos contratos,
      no de una estrategia. Test: recortar el percentil 99 y recalcular.
  C2  EL ATAQUE QUE MÁS DUELE. Si H1 desaparece al excluir el grupo "voz"
      (honorarios de disertante + consultoría, D-006), el hallazgo no es sobre
      "la carrera" sino sobre un tipo de pago, y el título miente por
      generalización.
  C3  Mix de lanzamientos: Mounjaro sale en 2022 y Zepbound en noviembre de 2023.
      El gasto de Lilly en 2023-2024 podría ser sólo el pico de lanzamiento, un
      mecanismo distinto a "Lilly invirtió más". No mata H1, lo explica: test
      descriptivo que descompone el gasto de Lilly por producto y año.

Uso:  uv run analysis/ataque-03_explicaciones-negocio.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

# C2 originalmente separaba sólo "disertante". D-006 formalizó la partición
# correcta (voz = honorarios + consultoría), y el ataque pasa a usarla: el
# resultado no cambia, pero deja de haber una regla improvisada acá.


def evaluar(nombre: str, df) -> tuple[bool, bool]:
    lilly = [int(f.anio) for f in df.itertuples() if f.lilly_usd > f.novo_usd]
    novo = [int(f.anio) for f in df.itertuples() if f.novo_pagos > f.lilly_pagos]
    h1, h2 = lilly == [2023, 2024], len(novo) == len(df)
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        USD: Lilly gana en {lilly or 'ningún año'} · "
          f"pagos: Novo gana en {len(novo)}/{len(df)} años")
    return h1, h2


def serie(con, filtro: str = "TRUE"):
    return con.sql(
        f"""
        SELECT anio,
               sum(usd) FILTER (grupo = 'novo')   AS novo_usd,
               sum(usd) FILTER (grupo = 'lilly')  AS lilly_usd,
               count(DISTINCT record_id) FILTER (grupo = 'novo')  AS novo_pagos,
               count(DISTINCT record_id) FILTER (grupo = 'lilly') AS lilly_pagos
        FROM glp1 WHERE {filtro} GROUP BY 1 ORDER BY 1
        """
    ).df()


def main() -> None:
    con = conectar()
    print("H1: Lilly > Novo en USD exactamente en 2023 y 2024")
    print("H2: Novo > Lilly en cantidad de pagos los 5 años\n")
    r = []

    r.append(evaluar("VIGENTE  todas las filas", serie(con)))

    # C1: fuera el 1% más caro de cada compañía y año.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW sin_cola AS
        WITH corte AS (
            SELECT anio, grupo, quantile_cont(usd_fila, 0.99) AS p99
            FROM (SELECT DISTINCT record_id, anio, grupo, usd_fila FROM glp1)
            GROUP BY 1, 2
        )
        SELECT g.* FROM glp1 g JOIN corte c
          ON g.anio = c.anio AND g.grupo = c.grupo
        WHERE g.usd_fila <= c.p99
        """
    )
    df_c1 = con.sql(
        """
        SELECT anio,
               sum(usd) FILTER (grupo = 'novo')   AS novo_usd,
               sum(usd) FILTER (grupo = 'lilly')  AS lilly_usd,
               count(DISTINCT record_id) FILTER (grupo = 'novo')  AS novo_pagos,
               count(DISTINCT record_id) FILTER (grupo = 'lilly') AS lilly_pagos
        FROM sin_cola GROUP BY 1 ORDER BY 1
        """
    ).df()
    r.append(evaluar("C1  sin el 1% de pagos más caros de cada compañía/año", df_c1))

    # C2: el ataque que más duele.
    r.append(evaluar("C2  SIN el grupo 'voz' (disertante + consultoría, D-006)",
                     serie(con, "grupo_naturaleza = 'campo'")))
    r.append(evaluar("C2b sólo el grupo 'voz'",
                     serie(con, "grupo_naturaleza = 'voz'")))

    # C3: descriptivo, no binario — de dónde sale el gasto de Lilly.
    print("\n  C3  gasto de Lilly por producto y año (USD, para ver si 2023-24 "
          "es pico de lanzamiento):")
    print(con.sql(
        """
        SELECT producto,
               round(sum(usd) FILTER (anio = 2021)/1e6, 2) AS "2021",
               round(sum(usd) FILTER (anio = 2022)/1e6, 2) AS "2022",
               round(sum(usd) FILTER (anio = 2023)/1e6, 2) AS "2023",
               round(sum(usd) FILTER (anio = 2024)/1e6, 2) AS "2024",
               round(sum(usd) FILTER (anio = 2025)/1e6, 2) AS "2025"
        FROM glp1 WHERE grupo = 'lilly' GROUP BY 1 ORDER BY 4 DESC
        """
    ).df().to_string(index=False))
    print("\n  Y el de Novo, para comparar:")
    print(con.sql(
        """
        SELECT producto,
               round(sum(usd) FILTER (anio = 2021)/1e6, 2) AS "2021",
               round(sum(usd) FILTER (anio = 2022)/1e6, 2) AS "2022",
               round(sum(usd) FILTER (anio = 2023)/1e6, 2) AS "2023",
               round(sum(usd) FILTER (anio = 2024)/1e6, 2) AS "2024",
               round(sum(usd) FILTER (anio = 2025)/1e6, 2) AS "2025"
        FROM glp1 WHERE grupo = 'novo' GROUP BY 1 ORDER BY 4 DESC
        """
    ).df().to_string(index=False))

    alt = r[1:]
    print(f"\nSobre {len(alt)} explicaciones alternativas: "
          f"H1 sobrevive {sum(x[0] for x in alt)}/{len(alt)} · "
          f"H2 sobrevive {sum(x[1] for x in alt)}/{len(alt)}")


if __name__ == "__main__":
    main()
