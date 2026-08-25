"""Corte 01 — la carrera Novo vs. Lilly en GLP-1, 2021–2025.

Pregunta: ¿quién invirtió más en promoción de GLP-1 ante profesionales de la
salud, y cómo evolucionó la ventaja?

La respuesta depende de la unidad, y esa es la novedad del corte (D-005): en
dólares Lilly pasa al frente en 2023 y 2024; en cantidad de pagos Novo lidera
los cinco años. El corte calcula ambas y no subordina ninguna.

Decisiones aplicadas: D-001 (ventana 2021–2025) · D-002 (entidades por ID) ·
D-003 (nueve productos) · D-004 (prorrateo) · D-005 (ambas unidades) ·
D-006 (naturalezas agrupadas en voz / campo).

Cachea agregados chicos en findings/cache/corte-01_carrera.json. El chart lee
SOLO ese JSON, nunca el parquet.

Uso:  uv run analysis/corte-01_carrera.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_DESDE, ANIO_HASTA, conectar  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "findings" / "cache"
DESTINO = CACHE / "corte-01_carrera.json"


def main() -> None:
    con = conectar()

    # Serie principal: las dos unidades, por año y compañía.
    serie = con.sql(
        """
        SELECT anio,
               sum(usd) FILTER (grupo = 'novo')                  AS novo_usd,
               sum(usd) FILTER (grupo = 'lilly')                 AS lilly_usd,
               count(DISTINCT record_id) FILTER (grupo = 'novo')  AS novo_pagos,
               count(DISTINCT record_id) FILTER (grupo = 'lilly') AS lilly_pagos,
               -- receptor_id es null para hospitales docentes; acá mide
               -- profesionales alcanzados, no entidades.
               count(DISTINCT receptor_id) FILTER (grupo = 'novo')  AS novo_hcp,
               count(DISTINCT receptor_id) FILTER (grupo = 'lilly') AS lilly_hcp
        FROM glp1 GROUP BY 1 ORDER BY 1
        """
    ).df()

    # Por qué divergen: las dos poblaciones de pago, con su monto típico.
    naturaleza = con.sql(
        """
        SELECT naturaleza,
               sum(usd) FILTER (grupo = 'novo')                   AS novo_usd,
               sum(usd) FILTER (grupo = 'lilly')                  AS lilly_usd,
               count(DISTINCT record_id) FILTER (grupo = 'novo')  AS novo_pagos,
               count(DISTINCT record_id) FILTER (grupo = 'lilly') AS lilly_pagos
        FROM glp1 GROUP BY 1
        HAVING sum(usd) > 0 ORDER BY sum(usd) DESC LIMIT 6
        """
    ).df()

    # Descomposición voz / campo (D-006). Nació del ataque 03 (C2): la ventaja
    # de Lilly en dólares vive entera en "voz", y la figura tiene que poder
    # mostrarlo sin volver al parquet.
    voz_campo = con.sql(
        """
        SELECT anio,
               sum(usd) FILTER (grupo = 'novo'  AND grupo_naturaleza = 'voz')   AS novo_voz,
               sum(usd) FILTER (grupo = 'lilly' AND grupo_naturaleza = 'voz')   AS lilly_voz,
               sum(usd) FILTER (grupo = 'novo'  AND grupo_naturaleza = 'campo') AS novo_campo,
               sum(usd) FILTER (grupo = 'lilly' AND grupo_naturaleza = 'campo') AS lilly_campo,
               count(DISTINCT record_id) FILTER (grupo = 'novo'  AND grupo_naturaleza = 'voz') AS novo_voz_n,
               count(DISTINCT record_id) FILTER (grupo = 'lilly' AND grupo_naturaleza = 'voz') AS lilly_voz_n
        FROM glp1 GROUP BY 1 ORDER BY 1
        """
    ).df()

    # Desglose por producto: quién aporta a cada lado de la carrera.
    producto = con.sql(
        """
        SELECT producto, any_value(grupo) AS grupo, anio,
               sum(usd) AS usd, count(DISTINCT record_id) AS pagos
        FROM glp1 GROUP BY producto, anio ORDER BY producto, anio
        """
    ).df()

    salida = {
        "corte": "01_carrera",
        "ventana": [ANIO_DESDE, ANIO_HASTA],
        "decisiones": ["D-001", "D-002", "D-003", "D-004", "D-005", "D-006"],
        "unidad_lider": "ninguna: el hallazgo es la divergencia (D-005)",
        "serie": serie.to_dict("records"),
        "ratios": [
            {
                "anio": int(f.anio),
                "usd": round(f.novo_usd / f.lilly_usd, 4),
                "pagos": round(f.novo_pagos / f.lilly_pagos, 4),
                "hcp": round(f.novo_hcp / f.lilly_hcp, 4),
            }
            for f in serie.itertuples()
        ],
        "naturaleza": naturaleza.to_dict("records"),
        "voz_vs_campo": voz_campo.to_dict("records"),
        "producto": producto.to_dict("records"),
        "totales": {
            "novo_usd": float(serie.novo_usd.sum()),
            "lilly_usd": float(serie.lilly_usd.sum()),
            "novo_pagos": int(serie.novo_pagos.sum()),
            "lilly_pagos": int(serie.lilly_pagos.sum()),
        },
    }

    CACHE.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=float))
    print(f"cache → {DESTINO.relative_to(Path.cwd())}")

    print("\nLa carrera en las dos unidades:")
    print(f"{'año':>6}{'Novo USD':>14}{'Lilly USD':>14}{'ratio':>8}"
          f"{'Novo pagos':>13}{'Lilly pagos':>13}{'ratio':>8}")
    for f, r in zip(serie.itertuples(), salida["ratios"]):
        lider_usd = "N" if r["usd"] > 1 else "L"
        lider_pag = "N" if r["pagos"] > 1 else "L"
        print(f"{int(f.anio):>6}{f.novo_usd:>14,.0f}{f.lilly_usd:>14,.0f}"
              f"{r['usd']:>7.2f}{lider_usd}"
              f"{f.novo_pagos:>13,}{f.lilly_pagos:>13,}{r['pagos']:>7.2f}{lider_pag}")

    invertidos = [r["anio"] for r in salida["ratios"]
                  if (r["usd"] > 1) != (r["pagos"] > 1)]
    print(f"\nAños en que las dos unidades dan ganadores distintos: "
          f"{invertidos or 'ninguno'}")


if __name__ == "__main__":
    main()
