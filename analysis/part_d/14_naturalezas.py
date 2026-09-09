"""¿De qué está hecho cada tipo de pago? La respuesta decide cómo se los nombra.

El caso parte los pagos en dos grupos, "voz" (honorarios de disertante y
consultoría) y "campo" (todo lo demás). El nombre "campo" es interno y no sirve
para un lector; la pregunta es qué palabra usar en el texto, y esa palabra tiene
que salir de la composición real, no de una intuición.

Importa porque "viáticos" y "comida" describen cosas distintas. Un viático es un
reembolso a alguien que viajó. Una comida declarada en Open Payments es, casi
siempre, el representante que lleva el almuerzo al consultorio para conseguir
unos minutos con el médico: el médico no se movió de su lugar de trabajo.

Salida: findings/cache/part_d-13_naturalezas.json + stdout.

Uso:  uv run analysis/part_d/14_naturalezas.py
"""

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-13_naturalezas.json"

_spec = importlib.util.spec_from_file_location(
    "cruce_pago_receta", Path(__file__).parent / "05_cruce_pago_receta.py"
)
_cruce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cruce)

ANIOS = (2021, 2022, 2023, 2024)


def por_naturaleza(con) -> list[dict]:
    """Un pago es un Record_ID, no un par record-producto: un pago que declara
    dos GLP-1 se cuenta una vez. El monto sí va prorrateado (D-004)."""
    lista = ", ".join(str(a) for a in ANIOS)
    return con.sql(
        f"""
        SELECT anio,
               naturaleza,
               grupo_naturaleza,
               count(DISTINCT record_id)                     AS pagos,
               round(100.0 * count(DISTINCT record_id)
                     / sum(count(DISTINCT record_id)) OVER (PARTITION BY anio), 2) AS pct_pagos,
               round(sum(usd), 2)                            AS usd,
               round(100.0 * sum(usd) / sum(sum(usd)) OVER (PARTITION BY anio), 2) AS pct_usd,
               round(median(usd_fila), 2)                    AS mediana_usd_del_pago
        FROM glp1
        WHERE anio IN ({lista})
        GROUP BY 1, 2, 3
        ORDER BY anio, pagos DESC
        """
    ).df().to_dict("records")


def main() -> int:
    con = _cruce.conectar()
    salida = {
        "pregunta": (
            "¿Qué proporción de los pagos de GLP-1 es cada naturaleza, en cantidad y en "
            "dinero? Decide con qué palabra nombrar cada grupo en el texto."
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "nota": (
            "'pagos' cuenta Record_ID distintos, así que un pago que declara dos GLP-1 no se "
            "cuenta dos veces. 'mediana_usd_del_pago' es sobre el monto de la fila sin "
            "prorratear, porque la pregunta es cuánto vale un pago, no cuánto se le atribuye "
            "a un producto."
        ),
        "por_naturaleza": por_naturaleza(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    for r in salida["por_naturaleza"]:
        if r["anio"] != 2024:
            continue
        print(
            f"{r['naturaleza'][:62]:62} {r['pct_pagos']:>6}% de los pagos · "
            f"{r['pct_usd']:>6}% del dinero · mediana USD {r['mediana_usd_del_pago']:,.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
