"""Ataque 01 (familia B) — ¿el corte 01 sobrevive a mis propias decisiones?

Hallazgo bajo ataque:
  H1: Lilly > Novo en DÓLARES en 2023 y 2024.
  H2: Novo > Lilly en CANTIDAD DE PAGOS los cinco años.

Hipótesis de muerte: H1 y H2 son artefactos de D-002 (alcance societario),
D-003 (qué productos entran) y D-004 (prorrateo). Si al usar las alternativas
que esas decisiones rechazaron el resultado cambia, el hallazgo es mío, no del
mercado.

Cada variante reconstruye el agregado desde `pagos` con OTRA regla, no desde la
vista `glp1`, que ya tiene las decisiones vigentes horneadas.

Uso:  uv run analysis/ataque-01_sensibilidad-decisiones.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ENTIDADES, GLP1, N_SLOTS, conectar  # noqa: E402

NOVO_US = (100000000144,)          # D-002 alternativa: sólo entidad operativa
LILLY_US = (100000000066,)
LEGACY = ("VICTOZA", "SAXENDA", "TRULICITY", "XULTOPHY 100/3.6")


def sql_lista(valores) -> str:
    return "(" + ", ".join("'" + str(v).replace("'", "''") + "'" for v in valores) + ")"


def agregar(con, novo_ids, lilly_ids, productos, reparto: str):
    """Serie anual con reglas parametrizadas.

    reparto: 'prorrateo' (D-004 vigente) · 'entero' (fila entera a cada
    producto) · 'slot1' (sólo el primer producto declarado).
    """
    nombres = ", ".join(f"upper(Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_{i})"
                        for i in range(1, N_SLOTS + 1))
    todos = ", ".join(f"Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_{i}"
                      for i in range(1, N_SLOTS + 1))
    lista = sql_lista(productos)
    ids = tuple(novo_ids) + tuple(lilly_ids)

    if reparto == "slot1":
        # Sólo cuenta si el PRIMER producto declarado es GLP-1.
        cond = f"upper(Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1) IN {lista}"
        usd = "Total_Amount_of_Payment_USDollars"
    else:
        cond = f"len(list_filter([{nombres}], x -> x IN {lista})) > 0"
        usd = ("Total_Amount_of_Payment_USDollars"
               if reparto == "entero" else
               f"""Total_Amount_of_Payment_USDollars
                   * len(list_distinct(list_filter([{nombres}], x -> x IN {lista})))
                   / len(list_filter([{todos}], x -> x IS NOT NULL))""")

    return con.sql(
        f"""
        SELECT Program_Year AS anio,
               sum({usd}) FILTER (Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID
                                  IN {tuple(novo_ids) if len(novo_ids) > 1 else f"({novo_ids[0]})"})  AS novo_usd,
               sum({usd}) FILTER (Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID
                                  IN {tuple(lilly_ids) if len(lilly_ids) > 1 else f"({lilly_ids[0]})"}) AS lilly_usd,
               count(*) FILTER (Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID
                                IN {tuple(novo_ids) if len(novo_ids) > 1 else f"({novo_ids[0]})"})     AS novo_pagos,
               count(*) FILTER (Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID
                                IN {tuple(lilly_ids) if len(lilly_ids) > 1 else f"({lilly_ids[0]})"})  AS lilly_pagos
        FROM pagos
        WHERE Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID IN {ids}
          AND {cond}
        GROUP BY 1 ORDER BY 1
        """
    ).df()


def evaluar(nombre: str, df) -> tuple[bool, bool, str]:
    """Devuelve (H1 sobrevive, H2 sobrevive, detalle)."""
    lilly_gana = [int(f.anio) for f in df.itertuples() if f.lilly_usd > f.novo_usd]
    novo_gana_pagos = [int(f.anio) for f in df.itertuples() if f.novo_pagos > f.lilly_pagos]
    h1 = lilly_gana == [2023, 2024]
    h2 = len(novo_gana_pagos) == len(df)
    detalle = (f"USD: Lilly gana en {lilly_gana or 'ningún año'} · "
               f"pagos: Novo gana en {len(novo_gana_pagos)}/{len(df)} años")
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        {detalle}")
    return h1, h2, detalle


def main() -> None:
    con = conectar()
    todos_prod = list(GLP1)
    sin_legacy = [p for p in todos_prod if p not in LEGACY]

    variantes = [
        ("VIGENTE  D-002 grupo completo · D-003 nueve · D-004 prorrateo",
         ENTIDADES["novo"], ENTIDADES["lilly"], todos_prod, "prorrateo"),
        ("D-002 alt  sólo entidad operativa US",
         NOVO_US, LILLY_US, todos_prod, "prorrateo"),
        ("D-004 alt  fila entera a cada producto",
         ENTIDADES["novo"], ENTIDADES["lilly"], todos_prod, "entero"),
        ("D-004 alt  sólo el primer producto declarado",
         ENTIDADES["novo"], ENTIDADES["lilly"], todos_prod, "slot1"),
        ("D-003 alt  sin legacy (Victoza, Saxenda, Trulicity, Xultophy)",
         ENTIDADES["novo"], ENTIDADES["lilly"], sin_legacy, "prorrateo"),
    ]

    print("H1: Lilly > Novo en USD exactamente en 2023 y 2024")
    print("H2: Novo > Lilly en cantidad de pagos los 5 años\n")
    resultados = []
    for nombre, n_ids, l_ids, prods, reparto in variantes:
        df = agregar(con, n_ids, l_ids, prods, reparto)
        resultados.append((nombre, *evaluar(nombre, df)))

    alternativas = resultados[1:]
    h1_ok = sum(r[1] for r in alternativas)
    h2_ok = sum(r[2] for r in alternativas)
    print(f"\nSobre {len(alternativas)} alternativas rechazadas: "
          f"H1 sobrevive {h1_ok}/{len(alternativas)} · H2 sobrevive {h2_ok}/{len(alternativas)}")


if __name__ == "__main__":
    main()
