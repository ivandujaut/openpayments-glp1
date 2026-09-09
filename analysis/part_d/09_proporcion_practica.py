"""El GLP-1 como proporción de la práctica, no sólo en volumen absoluto.

Por qué hace falta. Todos los cortes anteriores comparan recetas de GLP-1 entre
médicos, y el que receta más GLP-1 puede ser simplemente el que receta más de
todo: un internista con 4.000 recetas de Medicare al año va a tener más Ozempic
que uno con 400 sin que eso diga nada sobre el pago. El archivo "by Provider"
publica el total de recetas de cada prescriptor, que es el denominador que
faltaba.

Dos preguntas que sólo se pueden contestar con el denominador:

1. `share_por_clase`: entre los que figuran recetando Ozempic (o Mounjaro),
   ¿qué proporción de su práctica de Medicare es esa marca, según cobren
   honorarios, sólo comidas o nada? Si el share sube igual que el volumen, el
   pago va con un cambio de mezcla; si sólo sube el volumen, va con el tamaño
   del consultorio.
2. `tamano_de_practica`: la mediana de recetas totales de cada clase. Es el
   control directo: si los que cobran honorarios ya son los de práctica más
   grande, buena parte de la brecha de volumen es tamaño y no marca.

Fuente: CMS Medicare Part D Prescribers by Provider (`npi_<anio>.csv`,
sha256 en `checksums_partd.txt`). Es el archivo agregado por prescriptor, sin
apertura por droga, y su `Tot_Clms` incluye TODA la Part D del prescriptor, no
sólo GLP-1. Ojo con el mismo umbral de la otra tabla: el archivo por prescriptor
excluye a quien tuvo menos de 11 recetas en total.

Salida: findings/cache/part_d-08_proporcion.json + stdout.

Uso:  uv run analysis/part_d/09_proporcion_practica.py
"""

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "part_d"
CACHE = ROOT / "findings" / "cache" / "part_d-08_proporcion.json"

_spec = importlib.util.spec_from_file_location(
    "cruce_pago_receta", Path(__file__).parent / "05_cruce_pago_receta.py"
)
_cruce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cruce)

FOCO = [(2022, "OZEMPIC"), (2022, "TRULICITY"), (2024, "OZEMPIC"), (2024, "MOUNJARO")]


def preparar_practica(con, anios: list[int]) -> None:
    archivos = [RAW / f"npi_{a}.csv" for a in anios]
    faltan = [f.name for f in archivos if not f.exists()]
    if faltan:
        raise SystemExit(
            f"Faltan {', '.join(faltan)} en {RAW}. "
            "Correr antes: uv run analysis/part_d/01_descargar_partd.py"
        )
    piezas = " UNION ALL ".join(
        f"""
        SELECT CAST(Prscrbr_NPI AS BIGINT)      AS npi,
               {a}                              AS anio,
               Prscrbr_Type                     AS especialidad,
               TRY_CAST(Tot_Clms AS DOUBLE)     AS recetas_totales,
               TRY_CAST(Tot_Drug_Cst AS DOUBLE) AS costo_total
        FROM read_csv('{RAW}/npi_{a}.csv', all_varchar=true, header=true)
        """
        for a in anios
    )
    con.sql(f"CREATE VIEW practica AS {piezas}")


def cobertura(con) -> list[dict]:
    """Cuántos de los prescriptores del cruce aparecen en el archivo agregado.

    No es un trámite: si una parte grande no apareciera, el denominador estaría
    sesgado y los shares de abajo no se podrían usar.
    """
    return con.sql(
        """
        SELECT c.anio,
               count(DISTINCT c.npi)                                  AS npi_en_cruce,
               count(DISTINCT c.npi) FILTER (p.npi IS NOT NULL)       AS con_practica,
               round(100.0 * count(DISTINCT c.npi) FILTER (p.npi IS NOT NULL)
                     / count(DISTINCT c.npi), 2)                      AS pct
        FROM (SELECT DISTINCT npi, anio FROM cruce WHERE figura_recetando) c
        LEFT JOIN practica p ON p.npi = c.npi AND p.anio = c.anio
        GROUP BY 1 ORDER BY 1
        """
    ).df().to_dict("records")


def share_por_clase(con) -> list[dict]:
    """Share de la marca en la práctica total, por clase de pago.

    Sólo sobre quienes figuran recetando la marca Y aparecen en el archivo
    agregado: sin denominador no hay share, y rellenarlo con un supuesto sería
    inventar el dato que este corte existe para medir.
    """
    filtro = " OR ".join(f"(c.anio = {a} AND c.marca = '{m}')" for a, m in FOCO)
    return con.sql(
        f"""
        WITH base AS (
            SELECT c.anio, c.marca, c.recetas, p.recetas_totales,
                   100.0 * c.recetas / p.recetas_totales AS share,
                   CASE WHEN NOT c.cobro     THEN 'sin pago'
                        WHEN c.usd_voz > 0   THEN 'voz'
                        ELSE                      'solo campo' END AS clase
            FROM cruce c
            JOIN practica p ON p.npi = c.npi AND p.anio = c.anio
            WHERE c.figura_recetando AND p.recetas_totales > 0 AND ({filtro})
        )
        SELECT anio, marca, clase,
               count(*)                            AS n,
               round(median(recetas), 1)           AS mediana_recetas_marca,
               round(median(recetas_totales), 1)   AS mediana_recetas_totales,
               round(median(share), 2)             AS mediana_share_pct,
               round(avg(share), 2)                AS media_share_pct
        FROM base GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def tamano_de_practica(con) -> list[dict]:
    """El control: ¿los que cobran ya tienen la práctica más grande?"""
    filtro = " OR ".join(f"(c.anio = {a} AND c.marca = '{m}')" for a, m in FOCO)
    return con.sql(
        f"""
        WITH base AS (
            SELECT c.anio, c.marca, p.recetas_totales, p.costo_total,
                   CASE WHEN NOT c.cobro     THEN 'sin pago'
                        WHEN c.usd_voz > 0   THEN 'voz'
                        ELSE                      'solo campo' END AS clase
            FROM cruce c
            JOIN practica p ON p.npi = c.npi AND p.anio = c.anio
            WHERE c.figura_recetando AND ({filtro})
        )
        SELECT anio, marca, clase,
               count(*)                                 AS n,
               round(median(recetas_totales), 1)        AS mediana_practica,
               round(quantile_cont(recetas_totales, 0.25), 1) AS p25_practica,
               round(quantile_cont(recetas_totales, 0.75), 1) AS p75_practica,
               round(median(costo_total), 2)            AS mediana_costo_practica
        FROM base GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def main() -> int:
    anios = _cruce.anios_disponibles()
    con = _cruce.conectar()
    _cruce.preparar(con, anios)
    preparar_practica(con, anios)
    salida = {
        "que_mide": (
            "El GLP-1 como proporción de la práctica de Medicare de cada prescriptor, "
            "usando el archivo 'by Provider' como denominador. Separa 'receta más' de "
            "'tiene el consultorio más grande'."
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "cobertura_denominador": cobertura(con),
        "share_por_clase": share_por_clase(con),
        "tamano_de_practica": tamano_de_practica(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps(salida, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
