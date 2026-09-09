"""¿El dinero y las recetas hablan del mismo mercado?

Medicare tiene vedada por ley la cobertura de drogas para bajar de peso, y eso
se ve en el dato: Saxenda no tiene ni una fila en Part D en ningún año, Zepbound
tiene 353 recetas en 2024 y Wegovy aparece recién en 2023 con 142.

Del otro lado, el caso padre mostró que el gasto de Novo y Lilly se corrió hacia
obesidad. Si la plata de Open Payments está en las marcas que Medicare no cubre,
el cruce compara dos mercados con la misma etiqueta.

Este corte mide exactamente eso: qué proporción del dinero GLP-1 prorrateado
(D-004) de 2021-2024 corresponde a marcas con recetas en Part D, y qué
proporción a las tres de obesidad.

Salida: findings/cache/part_d-03_solapamiento.json + stdout.

Uso:  uv run analysis/part_d/04_solapamiento_mercado.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.vistas import conectar  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-03_solapamiento.json"

# Las tres marcas cuya indicación es obesidad (D-003 ya las etiqueta 'Obesity').
# Se listan explícitas igual, porque la afirmación del corte es sobre estas tres
# y no sobre lo que diga un campo derivado.
OBESIDAD = ("WEGOVY", "ZEPBOUND", "SAXENDA")

# Ventana común con Part D: 2021-2024. PY2025 existe del lado del pago y no
# tiene contraparte de recetas.
ANIO_HASTA_COMUN = 2024


def por_producto(con) -> list[dict]:
    return con.sql(
        f"""
        SELECT producto, grupo,
               round(sum(usd), 2)                     AS usd,
               count(DISTINCT record_id)              AS pagos,
               producto IN {OBESIDAD}                 AS es_obesidad
        FROM glp1
        WHERE anio <= {ANIO_HASTA_COMUN}
        GROUP BY 1, 2 ORDER BY usd DESC
        """
    ).df().to_dict("records")


def por_anio_indicacion(con) -> list[dict]:
    return con.sql(
        f"""
        SELECT anio,
               round(sum(CASE WHEN producto IN {OBESIDAD} THEN usd ELSE 0 END), 2)
                                                       AS usd_obesidad,
               round(sum(CASE WHEN producto IN {OBESIDAD} THEN 0 ELSE usd END), 2)
                                                       AS usd_diabetes,
               round(100.0 * sum(CASE WHEN producto IN {OBESIDAD} THEN usd ELSE 0 END)
                     / sum(usd), 2)                    AS pct_obesidad
        FROM glp1
        WHERE anio <= {ANIO_HASTA_COMUN}
        GROUP BY anio ORDER BY anio
        """
    ).df().to_dict("records")


def totales(con) -> dict:
    return con.sql(
        f"""
        SELECT round(sum(usd), 2)                      AS usd_ventana_comun,
               round(sum(CASE WHEN producto IN {OBESIDAD} THEN usd ELSE 0 END), 2)
                                                       AS usd_obesidad,
               round(100.0 * sum(CASE WHEN producto IN {OBESIDAD} THEN usd ELSE 0 END)
                     / sum(usd), 2)                    AS pct_obesidad
        FROM glp1 WHERE anio <= {ANIO_HASTA_COMUN}
        """
    ).df().to_dict("records")[0]


def main() -> int:
    con = conectar()
    salida = {
        "ventana": f"2021-{ANIO_HASTA_COMUN} (la común con Part D)",
        "marcas_obesidad": list(OBESIDAD),
        "totales": totales(con),
        "por_anio": por_anio_indicacion(con),
        "por_producto": por_producto(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps(salida, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
