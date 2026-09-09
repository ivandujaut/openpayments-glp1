"""Extrae de Part D sólo las filas de los GLP-1 del caso, por año.

Por qué no se lee el CSV entero: cada año de "by Provider and Drug" pesa más
de 1 GB y trae ~28 millones de filas (DY2024: 28.023.892). La API de CMS
filtra del lado del servidor por `Brnd_Name`, que es exactamente el recorte que
hace falta. Es el MISMO dataset publicado, no otra fuente: el CSV completo se
descarga igual con `01_descargar_partd.py` y `04_verificar_api_vs_csv.py`
compara los dos caminos fila por fila. Hasta que esa comparación exista, todo
número de acá se declara pendiente de verificación en la hoja de hechos.

Marcas, no genéricos. `Gnrc_Name = 'Liraglutide'` mezcla Victoza (Novo) con el
liraglutide genérico de Teva y Hikma, que no es de ninguno de los dos
anfitriones. La clave es la marca.

Dos marcas del caso padre NO existen igual en Part D y hay que decirlo:

- **Saxenda no aparece en ningún año.** Es liraglutida sólo para obesidad, y
  Medicare tiene prohibido por ley cubrir drogas para bajar de peso. Se cae del
  cruce entera.
- **Victoza se publica partida en dos presentaciones** ("Victoza 2-Pak" y
  "Victoza 3-Pak"), y **Xultophy lleva guion** ("Xultophy 100-3.6") donde Open
  Payments usa barra ("Xultophy 100/3.6"). Se reconcilian acá, no en el corte.

Salida: un Parquet por año en data/parquet/part_d_glp1_<anio>.parquet, más un
resumen JSON en findings/cache/part_d-02_extraccion.json.

Uso:  uv run analysis/part_d/03_extraer_glp1.py [anio ...]
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
PQ = ROOT / "data" / "parquet"
CACHE = ROOT / "findings" / "cache" / "part_d-02_extraccion.json"

# Endpoints de datos por año, del catálogo DCAT oficial
# (https://data.cms.gov/data.json, dataset 9552739e-3d05-4c1b-8eff-ecabf391e2e5,
# distribution[].accessURL de formato API). Capturados el 2026-09-08.
API: dict[int, str] = {
    2021: "https://data.cms.gov/data-api/v1/dataset/f68114ed-f854-4ffc-9c6e-ed78b5e2f8d0/data",
    2022: "https://data.cms.gov/data-api/v1/dataset/b101b457-ffa4-49bb-8fd9-27c1266086e2/data",
    2023: "https://data.cms.gov/data-api/v1/dataset/e54db557-cd82-4e91-a0fe-61aad5865d69/data",
    2024: "https://data.cms.gov/data-api/v1/dataset/d5aa71a8-dcc0-4570-8bcf-bd39deac69fe/data",
}

# Marca en Part D → (marca del caso padre, grupo). El nombre de la izquierda es
# literal del dataset de CMS; el de la derecha es la clave de src/vistas.py.
MARCAS: dict[str, tuple[str, str]] = {
    "Ozempic": ("OZEMPIC", "novo"),
    "Rybelsus": ("RYBELSUS", "novo"),
    "Wegovy": ("WEGOVY", "novo"),
    "Victoza 2-Pak": ("VICTOZA", "novo"),
    "Victoza 3-Pak": ("VICTOZA", "novo"),
    "Xultophy 100-3.6": ("XULTOPHY 100/3.6", "novo"),
    "Mounjaro": ("MOUNJARO", "lilly"),
    "Zepbound": ("ZEPBOUND", "lilly"),
    "Trulicity": ("TRULICITY", "lilly"),
}

PAGINA = 5000
ANIOS = sorted(API)


def _stats(url: str, marca: str) -> int:
    r = requests.get(
        f"{url}/stats", params={"filter[Brnd_Name]": marca}, timeout=120
    )
    r.raise_for_status()
    return int(r.json()["found_rows"])


def _paginar(url: str, marca: str, esperadas: int) -> list[dict]:
    filas: list[dict] = []
    offset = 0
    while offset < esperadas:
        r = requests.get(
            url,
            params={
                "filter[Brnd_Name]": marca,
                "size": PAGINA,
                "offset": offset,
            },
            timeout=180,
        )
        r.raise_for_status()
        lote = r.json()
        if not lote:
            break
        filas.extend(lote)
        offset += len(lote)
        time.sleep(0.2)  # cortesía con la API pública
    return filas


def extraer_anio(anio: int) -> dict:
    url = API[anio]
    destino = PQ / f"part_d_glp1_{anio}.parquet"
    partes: list[pd.DataFrame] = []
    detalle: dict[str, int] = {}
    for marca in MARCAS:
        esperadas = _stats(url, marca)
        detalle[marca] = esperadas
        if esperadas == 0:
            print(f"  [{anio}] {marca}: 0 filas (la marca no existe en este año)")
            continue
        filas = _paginar(url, marca, esperadas)
        if len(filas) != esperadas:
            raise SystemExit(
                f"[{anio}] {marca}: la API declaró {esperadas} filas y devolvió "
                f"{len(filas)}. Se corta: una extracción incompleta no entra."
            )
        df = pd.DataFrame(filas)
        partes.append(df)
        print(f"  [{anio}] {marca}: {len(df):,} filas")
    if not partes:
        return {"anio": anio, "filas": 0, "por_marca": detalle}
    todo = pd.concat(partes, ignore_index=True)
    todo["anio"] = anio
    todo["marca_caso"] = todo["Brnd_Name"].map(lambda b: MARCAS[b][0])
    todo["grupo"] = todo["Brnd_Name"].map(lambda b: MARCAS[b][1])
    # Todas las métricas llegan como texto (la API devuelve JSON de strings) y
    # el vacío es la supresión de CMS (valores 1 a 10), no un cero: queda NaN a
    # propósito, para que sumar no lo confunda con ausencia de recetas.
    for col in (
        "Tot_Clms", "Tot_30day_Fills", "Tot_Day_Suply", "Tot_Drug_Cst",
        "Tot_Benes", "GE65_Tot_Clms", "GE65_Tot_30day_Fills",
        "GE65_Tot_Drug_Cst", "GE65_Tot_Day_Suply", "GE65_Tot_Benes",
    ):
        if col in todo:
            todo[col] = pd.to_numeric(todo[col], errors="coerce")
    todo["Prscrbr_NPI"] = pd.to_numeric(todo["Prscrbr_NPI"], errors="coerce").astype("Int64")
    destino.parent.mkdir(parents=True, exist_ok=True)
    todo.to_parquet(destino, index=False)
    return {
        "anio": anio,
        "filas": int(len(todo)),
        "npi_distintos": int(todo["Prscrbr_NPI"].nunique()),
        "recetas": int(todo["Tot_Clms"].sum()),
        "costo_usd": round(float(todo["Tot_Drug_Cst"].sum()), 2),
        "filas_con_benes_suprimidos": int(todo["Tot_Benes"].isna().sum()),
        "por_marca": detalle,
        "archivo": str(destino.relative_to(ROOT)),
    }


def main(anios: list[int]) -> int:
    salida = {
        "fuente": "CMS Medicare Part D Prescribers by Provider and Drug, API filtrada por Brnd_Name",
        "capturado": time.strftime("%Y-%m-%d"),
        "por_anio": [extraer_anio(a) for a in anios],
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    previo = json.loads(CACHE.read_text()) if CACHE.exists() else {"por_anio": []}
    por_anio = {d["anio"]: d for d in previo.get("por_anio", [])}
    por_anio.update({d["anio"]: d for d in salida["por_anio"]})
    salida["por_anio"] = [por_anio[a] for a in sorted(por_anio)]
    CACHE.write_text(json.dumps(salida, indent=2))
    print(json.dumps(salida["por_anio"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main([int(a) for a in sys.argv[1:]] or ANIOS))
