"""Adentro del último decil: donde están los honorarios y el 62-80% del dinero.

Por qué hace falta un corte aparte. La tabla de deciles de `05_cruce_pago_receta.py`
muestra una escalera que sube, pero los primeros nueve deciles comparan comidas
con comidas (mediana de USD 7 a USD 108 en Ozempic 2024). El último decil
concentra la mayoría del dinero y es el único lugar donde hay honorarios de
disertante y consultoría. Si la corazonada ("cuanto más cobra, más receta")
vale en algún lado, es acá; y si no vale acá, no vale.

Cuatro cortes, todos sobre (NPI, año, marca) con al menos un pago:

1. `percentiles`: el último decil abierto en p90-95, p95-99, p99-99,9 y el
   0,1% de arriba, con mediana de dinero, mediana de recetas y proporción que
   figura recetando en cada tramo.
2. `por_naturaleza`: parte la población entre quienes cobraron algo de "voz"
   (honorarios de disertante y consultoría, D-006) y quienes sólo cobraron
   "campo" (comidas, viajes, material). Son poblaciones con dos órdenes de
   magnitud de diferencia en el monto por pago, y mezclarlas es lo que hace que
   la escalera de deciles parezca más limpia de lo que es.
3. `cuartiles_dentro_de_voz`: la misma escalera, en cuartiles, corrida sólo
   entre los que cobraron voz. Es el test directo de la corazonada sobre la
   población donde el dinero es un honorario y no un almuerzo.
4. `correlacion`: Spearman entre dinero y recetas, sobre los que figuran
   recetando, para el conjunto y para el subconjunto de voz. Es un número que
   resume la escalera sin esconder que no es monótona; se reporta con su n.

Nada de esto dice dirección: un gradiente es igual de compatible con "el pago
mueve la receta" que con "la compañía le paga a quien ya receta". Eso está
declarado en la hoja de hechos y no se resuelve con estos datos.

Salida: findings/cache/part_d-07_ultimo_decil.json + stdout.

Uso:  uv run analysis/part_d/08_ultimo_decil.py
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-07_ultimo_decil.json"

# El cruce se arma exactamente igual que en 05, importando sus funciones: dos
# definiciones del mismo cruce es la forma más rápida de que dos cortes del
# mismo caso dejen de hablar del mismo universo.
_spec = importlib.util.spec_from_file_location(
    "cruce_pago_receta", Path(__file__).parent / "05_cruce_pago_receta.py"
)
_cruce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cruce)

# Las combinaciones (año, marca) con volumen de los dos lados. Fuera quedan las
# marcas de obesidad, donde Medicare casi no cubre y el cruce mide el borde del
# dataset, no conducta (ver C5 de la hoja).
FOCO = [(2022, "OZEMPIC"), (2022, "TRULICITY"), (2024, "OZEMPIC"), (2024, "MOUNJARO")]


def percentiles(con) -> list[dict]:
    """El último decil abierto: p90-95, p95-99, p99-99,9 y el 0,1% de arriba."""
    return con.sql(
        """
        WITH base AS (
            SELECT anio, marca, npi, usd, usd_voz, recetas, figura_recetando,
                   percent_rank() OVER (PARTITION BY anio, marca ORDER BY usd) AS pr
            FROM cruce WHERE cobro
        ), tramos AS (
            SELECT *, CASE
                       WHEN pr < 0.90   THEN 'p00-90'
                       WHEN pr < 0.95   THEN 'p90-95'
                       WHEN pr < 0.99   THEN 'p95-99'
                       WHEN pr < 0.999  THEN 'p99-99.9'
                       ELSE                  'p99.9-100'
                     END AS tramo
            FROM base
        )
        SELECT anio, marca, tramo,
               count(*)                                  AS npi,
               round(sum(usd), 2)                        AS usd,
               round(median(usd), 2)                     AS mediana_usd,
               round(sum(usd_voz), 2)                    AS usd_voz,
               round(100.0 * count(*) FILTER (usd_voz > 0) / count(*), 1)
                                                         AS pct_con_voz,
               round(median(recetas), 1)                 AS mediana_recetas,
               round(median(recetas) FILTER (figura_recetando), 1)
                                                         AS mediana_recetas_visibles,
               round(100.0 * count(*) FILTER (figura_recetando) / count(*), 1)
                                                         AS pct_figura_recetando
        FROM tramos GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def por_naturaleza(con) -> list[dict]:
    """Voz (honorarios y consultoría) contra campo (comidas y viajes).

    Tres poblaciones y no dos: los que no cobraron nada por esa marca ese año
    entran como control, porque la comparación que importa no es entre los que
    cobran mucho y poco, sino contra los que no cobran.
    """
    return con.sql(
        """
        WITH base AS (
            SELECT anio, marca, npi, usd, usd_voz, recetas, figura_recetando,
                   CASE WHEN NOT cobro     THEN 'sin pago'
                        WHEN usd_voz > 0   THEN 'voz'
                        ELSE                    'solo campo' END AS clase
            FROM cruce
        )
        SELECT anio, marca, clase,
               count(*)                                  AS npi,
               round(sum(usd), 2)                        AS usd,
               round(median(usd), 2)                     AS mediana_usd,
               round(median(recetas) FILTER (figura_recetando), 1)
                                                         AS mediana_recetas_visibles,
               round(avg(recetas) FILTER (figura_recetando), 1)
                                                         AS media_recetas_visibles,
               count(*) FILTER (figura_recetando)        AS n_visibles,
               round(100.0 * count(*) FILTER (figura_recetando) / count(*), 1)
                                                         AS pct_figura_recetando
        FROM base GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def cuartiles_dentro_de_voz(con) -> list[dict]:
    """La escalera corrida sólo entre los que cobraron honorarios.

    Acá el dinero es un honorario en todos los tramos, así que la escalera
    compara lo mismo con lo mismo. Son **cuartiles y no deciles** porque la
    población de voz es de unos pocos cientos por marca y año (383 en Ozempic
    2024): diez tramos de 38 personas serían diez anécdotas. Se pide un mínimo
    de 50 por tramo.
    """
    filtro = " OR ".join(f"(anio = {a} AND marca = '{m}')" for a, m in FOCO)
    return con.sql(
        f"""
        WITH base AS (
            SELECT anio, marca, npi, usd_voz, recetas, figura_recetando,
                   ntile(4) OVER (PARTITION BY anio, marca ORDER BY usd_voz) AS cuartil
            FROM cruce
            WHERE cobro AND usd_voz > 0 AND ({filtro})
        )
        SELECT anio, marca, cuartil,
               count(*)                                  AS npi,
               round(sum(usd_voz), 2)                    AS usd_voz,
               round(median(usd_voz), 2)                 AS mediana_usd_voz,
               round(median(recetas), 1)                 AS mediana_recetas,
               round(median(recetas) FILTER (figura_recetando), 1)
                                                         AS mediana_recetas_visibles,
               round(100.0 * count(*) FILTER (figura_recetando) / count(*), 1)
                                                         AS pct_figura_recetando
        FROM base GROUP BY 1, 2, 3
        HAVING count(*) >= 50
        ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def correlacion(con) -> list[dict]:
    """Spearman entre dinero y recetas, entre los que figuran recetando.

    Sobre rangos y no sobre valores, porque las dos variables tienen colas
    largas. Los **empates se promedian** (`rank() + (repeticiones - 1) / 2`),
    que es la definición correcta de Spearman: `Tot_Clms` tiene miles de
    empates y el rango mínimo de DuckDB los rompe siempre para el mismo lado,
    lo que corre el rho. Se reporta con el n al lado: un rho sin n no dice nada.

    Dos columnas, y la segunda es la que contesta la pregunta de Iván:

    - `spearman_usd`: sobre todos los que cobraron algo, casi todos comidas.
    - `spearman_usd_voz`: **sólo entre los que cobraron honorarios**, contra
      lo que cobraron de honorarios. Es el test directo de "cuanto más cobra,
      más receta" en la única población donde el dinero es un honorario.
    """
    return con.sql(
        """
        WITH v AS (
            SELECT anio, marca, usd, usd_voz, recetas, usd_voz > 0 AS con_voz
            FROM cruce WHERE cobro AND figura_recetando
        ), rangos AS (
            SELECT anio, marca, con_voz,
                   rank() OVER (PARTITION BY anio, marca ORDER BY usd)
                     + (count(*) OVER (PARTITION BY anio, marca, usd) - 1) / 2.0
                                                                       AS rank_usd,
                   rank() OVER (PARTITION BY anio, marca ORDER BY recetas)
                     + (count(*) OVER (PARTITION BY anio, marca, recetas) - 1) / 2.0
                                                                       AS rank_rx,
                   CASE WHEN con_voz THEN
                     rank() OVER (PARTITION BY anio, marca, con_voz ORDER BY usd_voz)
                       + (count(*) OVER (PARTITION BY anio, marca, con_voz, usd_voz) - 1) / 2.0
                   END                                                 AS rank_usd_voz,
                   CASE WHEN con_voz THEN
                     rank() OVER (PARTITION BY anio, marca, con_voz ORDER BY recetas)
                       + (count(*) OVER (PARTITION BY anio, marca, con_voz, recetas) - 1) / 2.0
                   END                                                 AS rank_rx_voz
            FROM v
        )
        SELECT anio, marca,
               count(*)                                      AS n,
               round(corr(rank_usd, rank_rx), 4)             AS spearman_usd,
               count(*) FILTER (con_voz)                     AS n_voz,
               round(corr(rank_usd_voz, rank_rx_voz), 4)     AS spearman_usd_voz
        FROM rangos
        GROUP BY 1, 2 HAVING count(*) >= 1000 ORDER BY 1, 2
        """
    ).df().to_dict("records")


def main() -> int:
    anios = _cruce.anios_disponibles()
    if not anios:
        raise SystemExit(
            "No hay Parquet de Part D en data/parquet/. "
            "Correr antes: uv run analysis/part_d/03_extraer_glp1.py"
        )
    con = _cruce.conectar()
    _cruce.preparar(con, anios)
    salida = {
        "que_mide": (
            "El interior del último decil de dinero, y la partición entre pagos de voz "
            "(honorarios y consultoría) y de campo (comidas y viajes). Ninguno de estos "
            "números dice dirección: un gradiente es compatible con que el pago mueva la "
            "receta y con que la compañía le pague a quien ya receta."
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "anios_procesados": anios,
        "foco_deciles_voz": [list(f) for f in FOCO],
        "percentiles": percentiles(con),
        "por_naturaleza": por_naturaleza(con),
        "cuartiles_dentro_de_voz": cuartiles_dentro_de_voz(con),
        "correlacion": correlacion(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps(
        {k: v for k, v in salida.items() if k in ("percentiles", "correlacion")},
        indent=2, default=str,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
