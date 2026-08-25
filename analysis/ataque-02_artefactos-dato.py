"""Ataque 02 (familia A) — ¿el corte 01 es un artefacto del dato de CMS?

Hallazgo bajo ataque:
  H1: Lilly > Novo en DÓLARES en 2023 y 2024.
  H2: Novo > Lilly en CANTIDAD DE PAGOS los cinco años.

Cuatro hipótesis de muerte, cada una con su test:
  A1  La composición de receptores difiere entre compañías y H2 sólo existe por
      los NP/PA que entraron al registro en 2021. Test: recalcular con médicos
      solamente.
  A2  Registros disputados o con publicación demorada inflan un lado.
      Test: excluirlos y recalcular.
  A3  "Cantidad de pagos" cuenta FILAS, pero una fila puede agregar varios pagos
      (Number_of_Payments_Included_in_Total_Amount). Si Lilly agrega más por
      fila, H2 se cae al contar pagos reales. Test: ponderar por esa columna.
  A4  D-003 no matchea alguna variante de escritura y pierde producto de un lado.
      Test: listar productos de Novo/Lilly en áreas Diabetes/Obesity que NO
      estén en la lista, y ver si alguno es un GLP-1 disfrazado.

Uso:  uv run analysis/ataque-02_artefactos-dato.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import GLP1, conectar  # noqa: E402


def evaluar(nombre: str, df) -> tuple[bool, bool]:
    lilly_gana = [int(f.anio) for f in df.itertuples() if f.lilly_usd > f.novo_usd]
    novo_pagos = [int(f.anio) for f in df.itertuples() if f.novo_pagos > f.lilly_pagos]
    h1, h2 = lilly_gana == [2023, 2024], len(novo_pagos) == len(df)
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        USD: Lilly gana en {lilly_gana or 'ningún año'} · "
          f"pagos: Novo gana en {len(novo_pagos)}/{len(df)} años")
    return h1, h2


def serie(con, filtro: str = "TRUE"):
    """Serie anual desde la vista glp1, que tiene una fila por (pago, producto).

    `sum(usd)` es correcto tal cual (el prorrateo ya reparte), pero los pagos
    exigen count(DISTINCT record_id): contar filas duplicaría los multi-producto.
    """
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


def serie_pagos_reales(con):
    """A3: pondera por Number_of_Payments_Included_in_Total_Amount.

    Colapsa primero a un registro por record_id — si no, una fila que declara
    dos GLP-1 aportaría su n_pagos_agregados dos veces.
    """
    return con.sql(
        """
        WITH unicos AS (
            SELECT DISTINCT record_id, anio, grupo, usd_fila, n_pagos_agregados
            FROM glp1
        )
        SELECT anio,
               sum(usd_fila) FILTER (grupo = 'novo')  AS novo_usd,
               sum(usd_fila) FILTER (grupo = 'lilly') AS lilly_usd,
               sum(n_pagos_agregados) FILTER (grupo = 'novo')  AS novo_pagos,
               sum(n_pagos_agregados) FILTER (grupo = 'lilly') AS lilly_pagos
        FROM unicos GROUP BY 1 ORDER BY 1
        """
    ).df()


def main() -> None:
    con = conectar()
    print("H1: Lilly > Novo en USD exactamente en 2023 y 2024")
    print("H2: Novo > Lilly en cantidad de pagos los 5 años\n")
    r = []

    r.append(("VIGENTE", *evaluar("VIGENTE  todas las filas", serie(con))))
    r.append(("A1", *evaluar(
        "A1  sólo médicos (excluye NP/PA y hospitales docentes)",
        serie(con, "tipo_receptor = 'Covered Recipient Physician'"))))
    r.append(("A2", *evaluar(
        "A2  sin disputados",
        serie(con, "record_id NOT IN (SELECT Record_ID FROM pagos "
                   "WHERE Dispute_Status_for_Publication)"))))
    r.append(("A3", *evaluar(
        "A3  pagos reales, ponderando por Number_of_Payments",
        serie_pagos_reales(con))))

    # A4: productos de Novo/Lilly en áreas GLP-1 que la lista NO captura.
    print("\n  A4  productos en Diabetes/Obesity fuera de la lista de D-003:")
    lista = "(" + ", ".join(f"'{p}'" for p in GLP1) + ")"
    u = " UNION ALL ".join(
        f"""SELECT upper(Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_{i}) prod,
                   Product_Category_or_Therapeutic_Area_{i} area,
                   Associated_Drug_or_Biological_NDC_{i} ndc
            FROM pagos
            WHERE Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID IN
                  (100000000144,100000000163,100000000155,100000196804,
                   100000000066,100000000088,100000000331)
              AND Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_{i} IS NOT NULL"""
        for i in range(1, 6))
    fuera = con.sql(
        f"""SELECT prod, any_value(area) area, any_value(ndc) ndc, count(*) menciones
            FROM ({u}) WHERE area IN ('Diabetes','Obesity') AND prod NOT IN {lista}
            GROUP BY 1 ORDER BY menciones DESC"""
    ).df()
    print(fuera.to_string(index=False))
    print("\n  Revisión manual: ninguno de estos es un agonista GLP-1 —\n"
          "  son SGLT2 (Jardiance, Synjardy, Trijardy, Glyxambi), DPP-4\n"
          "  (Tradjenta, Jentadueto), insulinas y glucagón de rescate.")

    alt = r[1:]
    print(f"\nSobre {len(alt)} artefactos testeados: "
          f"H1 sobrevive {sum(x[1] for x in alt)}/{len(alt)} · "
          f"H2 sobrevive {sum(x[2] for x in alt)}/{len(alt)}")


if __name__ == "__main__":
    main()
