"""Verificador: el recorte por API contra el CSV completo, fila por fila.

Por qué existe: `03_extraer_glp1.py` no lee los CSV de "by Provider and Drug"
(3,6 a 4,1 GB por año, ~28 millones de filas), sino que le pide a la API de CMS
el mismo recorte filtrado del lado del servidor. Eso es una decisión de método,
y una decisión de método sin verificar es un supuesto. Este script baja el
supuesto a dato: compara los dos caminos sobre el MISMO año y la MISMA marca.

Qué compara, en tres niveles y en este orden:

1. **Conteo de filas** por (año, marca): la API dijo N, el CSV tiene M.
2. **Agregados** por (año, marca): recetas, costo, NPI distintos, y cuántas
   filas traen `Tot_Clms` o `Tot_Benes` suprimidos.
3. **Fila por fila**, con llave (NPI, Brnd_Name): filas que están en un camino
   y no en el otro, y filas presentes en los dos con `Tot_Clms` distinto.

El CSV es la autoridad: si difieren, manda el archivo publicado (regla 1.2 del
flujo). El script no arregla nada, informa.

Los CSV se leen con DuckDB en streaming (no entran en memoria) y se filtran por
`Brnd_Name` sobre la lista literal de `03_extraer_glp1.py`, importada de ahí
para que no haya dos listas de marcas que se puedan desincronizar.

Salida: findings/cache/part_d-06_verificacion.json + stdout.

Uso:  uv run analysis/part_d/07_verificar_api_vs_csv.py [anio ...]
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
PQ = ROOT / "data" / "parquet"
RAW = ROOT / "data" / "raw" / "part_d"
CACHE = ROOT / "findings" / "cache" / "part_d-06_verificacion.json"

# La lista de marcas se importa del extractor, no se copia: dos listas iguales
# hoy son dos listas distintas en tres meses.
_spec = importlib.util.spec_from_file_location(
    "extraer_glp1", Path(__file__).parent / "03_extraer_glp1.py"
)
_extraer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_extraer)
MARCAS: dict[str, tuple[str, str]] = _extraer.MARCAS

ANIOS = (2021, 2022, 2023, 2024)


def _lista_sql(valores) -> str:
    return "(" + ", ".join("'" + str(v).replace("'", "''") + "'" for v in valores) + ")"


def _preparar(con: duckdb.DuckDBPyConnection, anio: int) -> None:
    csv = RAW / f"npibn_{anio}.csv"
    if not csv.exists():
        raise SystemExit(
            f"Falta {csv}. Correr antes: uv run analysis/part_d/01_descargar_partd.py"
        )
    pq = PQ / f"part_d_glp1_{anio}.parquet"
    if not pq.exists():
        raise SystemExit(
            f"Falta {pq}. Correr antes: uv run analysis/part_d/03_extraer_glp1.py"
        )
    # all_varchar: el CSV trae los valores suprimidos como vacío y algunos años
    # cambian de tipo entre columnas; se castea explícito abajo, igual que hace
    # el extractor con lo que devuelve la API.
    con.sql(
        f"""
        CREATE OR REPLACE VIEW csv_full AS
        SELECT CAST(Prscrbr_NPI AS BIGINT)      AS npi,
               Brnd_Name                        AS marca,
               TRY_CAST(Tot_Clms     AS DOUBLE) AS recetas,
               TRY_CAST(Tot_Drug_Cst AS DOUBLE) AS costo,
               TRY_CAST(Tot_Benes    AS DOUBLE) AS benes
        FROM read_csv('{csv}', all_varchar=true, header=true)
        WHERE Brnd_Name IN {_lista_sql(MARCAS)}
        """
    )
    con.sql(
        f"""
        CREATE OR REPLACE VIEW api AS
        SELECT CAST(Prscrbr_NPI AS BIGINT)      AS npi,
               Brnd_Name                        AS marca,
               TRY_CAST(Tot_Clms     AS DOUBLE) AS recetas,
               TRY_CAST(Tot_Drug_Cst AS DOUBLE) AS costo,
               TRY_CAST(Tot_Benes    AS DOUBLE) AS benes
        FROM read_parquet('{pq}')
        """
    )


def agregados(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Nivel 1 y 2: conteos y sumas por marca, de los dos lados."""
    return con.sql(
        """
        WITH a AS (
            SELECT marca, count(*) AS filas, count(DISTINCT npi) AS npi,
                   sum(recetas) AS recetas, round(sum(costo), 2) AS costo,
                   count(*) FILTER (recetas IS NULL) AS clms_nulos,
                   count(*) FILTER (benes IS NULL)   AS benes_nulos
            FROM api GROUP BY 1
        ), c AS (
            SELECT marca, count(*) AS filas, count(DISTINCT npi) AS npi,
                   sum(recetas) AS recetas, round(sum(costo), 2) AS costo,
                   count(*) FILTER (recetas IS NULL) AS clms_nulos,
                   count(*) FILTER (benes IS NULL)   AS benes_nulos
            FROM csv_full GROUP BY 1
        )
        SELECT coalesce(a.marca, c.marca)             AS marca,
               coalesce(a.filas, 0)                   AS filas_api,
               coalesce(c.filas, 0)                   AS filas_csv,
               coalesce(a.filas, 0) - coalesce(c.filas, 0)       AS dif_filas,
               coalesce(a.npi, 0)                     AS npi_api,
               coalesce(c.npi, 0)                     AS npi_csv,
               coalesce(a.recetas, 0)                 AS recetas_api,
               coalesce(c.recetas, 0)                 AS recetas_csv,
               coalesce(a.recetas, 0) - coalesce(c.recetas, 0)   AS dif_recetas,
               coalesce(a.costo, 0)                   AS costo_api,
               coalesce(c.costo, 0)                   AS costo_csv,
               round(coalesce(a.costo, 0) - coalesce(c.costo, 0), 2) AS dif_costo,
               coalesce(a.clms_nulos, 0)              AS clms_nulos_api,
               coalesce(c.clms_nulos, 0)              AS clms_nulos_csv,
               coalesce(a.benes_nulos, 0)             AS benes_nulos_api,
               coalesce(c.benes_nulos, 0)             AS benes_nulos_csv
        FROM a FULL OUTER JOIN c ON a.marca = c.marca
        ORDER BY 1
        """
    ).df().to_dict("records")


def fila_por_fila(con: duckdb.DuckDBPyConnection) -> dict:
    """Nivel 3: la llave (NPI, marca) de un lado contra el otro.

    Devuelve los conteos y, si hay diferencias, hasta veinte ejemplos de cada
    clase: no sirve un 'hay 300 filas distintas' sin poder mirar tres.
    """
    con.sql(
        """
        CREATE OR REPLACE VIEW par AS
        SELECT coalesce(a.npi, c.npi)     AS npi,
               coalesce(a.marca, c.marca) AS marca,
               a.recetas                  AS recetas_api,
               c.recetas                  AS recetas_csv,
               a.npi IS NOT NULL          AS en_api,
               c.npi IS NOT NULL          AS en_csv
        FROM api a FULL OUTER JOIN csv_full c
          ON a.npi = c.npi AND a.marca = c.marca
        """
    )
    conteos = con.sql(
        """
        SELECT count(*)                                        AS pares,
               count(*) FILTER (en_api AND NOT en_csv)          AS solo_api,
               count(*) FILTER (en_csv AND NOT en_api)          AS solo_csv,
               count(*) FILTER (en_api AND en_csv
                    AND recetas_api IS DISTINCT FROM recetas_csv) AS recetas_distintas
        FROM par
        """
    ).df().to_dict("records")[0]
    ejemplos = {}
    for clase, filtro in (
        ("solo_api", "en_api AND NOT en_csv"),
        ("solo_csv", "en_csv AND NOT en_api"),
        ("recetas_distintas",
         "en_api AND en_csv AND recetas_api IS DISTINCT FROM recetas_csv"),
    ):
        if conteos[clase]:
            ejemplos[clase] = con.sql(
                f"SELECT * FROM par WHERE {filtro} LIMIT 20"
            ).df().to_dict("records")
    return {"conteos": conteos, "ejemplos": ejemplos}


def verificar_anio(anio: int) -> dict:
    con = duckdb.connect()
    _preparar(con, anio)
    agr = agregados(con)
    fxf = fila_por_fila(con)
    ok = (
        all(a["dif_filas"] == 0 and a["dif_recetas"] == 0 and abs(a["dif_costo"]) < 0.01
            for a in agr)
        and fxf["conteos"]["solo_api"] == 0
        and fxf["conteos"]["solo_csv"] == 0
        and fxf["conteos"]["recetas_distintas"] == 0
    )
    con.close()
    return {"anio": anio, "identico": bool(ok), "por_marca": agr, "fila_por_fila": fxf}


def main(anios) -> int:
    resultados = [verificar_anio(a) for a in anios]
    salida = {
        "que_compara": (
            "El recorte GLP-1 pedido a la API de CMS (data/parquet/part_d_glp1_<anio>.parquet) "
            "contra el mismo recorte hecho sobre el CSV completo publicado "
            "(data/raw/part_d/npibn_<anio>.csv, sha256 en checksums_partd.txt). "
            "En caso de diferencia manda el CSV."
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "todos_identicos": all(r["identico"] for r in resultados),
        "por_anio": resultados,
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    for r in resultados:
        estado = "IDENTICO" if r["identico"] else "DIFIERE"
        c = r["fila_por_fila"]["conteos"]
        print(
            f"{r['anio']}: {estado} · {c['pares']:,} pares · "
            f"solo API {c['solo_api']} · solo CSV {c['solo_csv']} · "
            f"recetas distintas {c['recetas_distintas']}"
        )
        for m in r["por_marca"]:
            if m["dif_filas"] or m["dif_recetas"] or abs(m["dif_costo"]) >= 0.01:
                print(
                    f"    {m['marca']}: filas {m['filas_api']} vs {m['filas_csv']}, "
                    f"recetas {m['recetas_api']} vs {m['recetas_csv']}, "
                    f"costo dif {m['dif_costo']}"
                )
    print(f"\nTodos idénticos: {salida['todos_identicos']}")
    return 0 if salida["todos_identicos"] else 1


if __name__ == "__main__":
    raise SystemExit(main([int(a) for a in sys.argv[1:]] or ANIOS))
