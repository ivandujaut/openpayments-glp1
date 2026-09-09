"""Los que siguen recetando Trulicity sin cobrar por ella, ¿cobran de Lilly?

Existe para bajar a dato una frase que el borrador afirmaba sin fuente. C5
muestra que Lilly retiró el dinero de Trulicity (de 39.483 profesionales con
pago en 2022 a 2.300 en 2024) mientras 100.299 la seguían recetando sin cobrar
por esa marca. La tentación es escribir que "muchos de ellos cobraron igual de
Lilly, por Mounjaro o Zepbound": es plausible, el cruce lo puede medir, y hasta
que se mida no es un dato.

Mide exactamente eso: de los que figuran recetando Trulicity en 2024 y no
cobraron nada **por Trulicity**, cuántos cobraron algo de Lilly ese mismo año
por cualquiera de sus GLP-1.

Salida: findings/cache/part_d-12_trulicity.json + stdout.

Uso:  uv run analysis/part_d/13_trulicity_reasignados.py
"""

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-12_trulicity.json"

_spec = importlib.util.spec_from_file_location(
    "cruce_pago_receta", Path(__file__).parent / "05_cruce_pago_receta.py"
)
_cruce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cruce)


def reasignados(con) -> dict:
    return con.sql(
        """
        WITH sin_pago_trulicity AS (
            SELECT npi FROM cruce
            WHERE anio = 2024 AND marca = 'TRULICITY'
              AND figura_recetando AND NOT cobro
        ), cobro_lilly AS (
            SELECT DISTINCT npi FROM cruce
            WHERE anio = 2024 AND grupo = 'lilly' AND cobro
        )
        SELECT count(*)                                   AS recetan_sin_cobrar_trulicity,
               count(*) FILTER (l.npi IS NOT NULL)        AS cobraron_de_lilly_por_otra,
               round(100.0 * count(*) FILTER (l.npi IS NOT NULL) / count(*), 1) AS pct,
               count(*) FILTER (l.npi IS NULL)            AS no_cobraron_de_lilly
        FROM sin_pago_trulicity s
        LEFT JOIN cobro_lilly l ON l.npi = s.npi
        """
    ).df().to_dict("records")[0]


def main() -> int:
    con = _cruce.conectar()
    _cruce.preparar(con, _cruce.anios_disponibles())
    salida = {
        "pregunta": (
            "De los que figuran recetando Trulicity en 2024 sin cobrar por Trulicity, "
            "¿cuántos cobraron de Lilly ese año por otro GLP-1?"
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "nota": (
            "'Cobró de Lilly' es cualquier pago prorrateado de Lilly por cualquiera de sus "
            "GLP-1 del caso en 2024, no sólo Mounjaro y Zepbound."
        ),
        **reasignados(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps(salida, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
