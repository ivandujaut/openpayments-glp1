"""Cuánto no se ve: el detalle por prescriptor contra el total publicado.

Part D publica DOS cosas que deberían dar lo mismo y no dan:

- el archivo de detalle (by Provider and Drug), que excluye todo par
  prescriptor-droga con menos de 11 recetas;
- el dataset de gasto por droga (Part D Spending by Drug), que agrega sobre
  TODOS los PDE sin ese recorte.

La diferencia es exactamente el tamaño de lo que el caso no puede ver. CMS lo
avisa ("summing data in detail file will underestimate the true Part D
totals") pero no publica el número; este check lo mide.

Regla 1.2 del flujo: si el recalculado difiere del publicado, manda el
publicado y se explica la diferencia. Acá los dos son publicados y la
diferencia ES el hallazgo.

Salida: findings/cache/part_d-05_censura.json + stdout.

Uso:  uv run analysis/part_d/06_check_censura.py
"""

import csv
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
PQ = ROOT / "data" / "parquet"
CACHE = ROOT / "findings" / "cache" / "part_d-05_censura.json"

# El dataset de gasto por droga, que da el total publicado contra el que se mide
# la censura del archivo de detalle. Se descarga acá y no se lee de otro repo:
# este script tiene que correr en un clone limpio, que es de lo que sirve
# versionarlo. 5 MB, así que baja en segundos.
GASTO_URL = (
    "https://data.cms.gov/sites/default/files/2026-06/"
    "98218f98-166c-4723-8438-c344a4ef96a6/DSD_PTD_RY26_P04_V10_DY24_BGM.csv"
)
GASTO_SHA256 = "5dcc9d7bd7d7f88d9f6b24485c06d961ed6d70f9aa6deffa50dd47a6854c2a55"
GASTO = ROOT / "data" / "raw" / "part_d" / "partd-spending-by-drug-DY24.csv"


def asegurar_gasto() -> Path:
    """Descarga el CSV de gasto si falta y verifica su sha256 siempre.

    Si el archivo cambia de contenido, corta en vez de seguir con otro dato:
    es la misma regla del manifiesto de `01_descargar_partd.py`.
    """
    import hashlib

    import requests

    if not GASTO.exists():
        GASTO.parent.mkdir(parents=True, exist_ok=True)
        print(f"descargando {GASTO_URL}")
        parcial = GASTO.with_suffix(".parcial")
        with requests.get(GASTO_URL, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(parcial, "wb") as f:
                for trozo in r.iter_content(chunk_size=1 << 20):
                    f.write(trozo)
        parcial.rename(GASTO)
    h = hashlib.sha256()
    with open(GASTO, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    if h.hexdigest() != GASTO_SHA256:
        raise SystemExit(
            f"El sha256 de {GASTO.name} no coincide con el declarado.\n"
            f"  esperado: {GASTO_SHA256}\n  archivo:  {h.hexdigest()}"
        )
    return GASTO

# Marca publicada en el dataset de gasto → marca del caso. Victoza va partida.
GASTO_A_CASO = {
    "Ozempic": "OZEMPIC",
    "Rybelsus": "RYBELSUS",
    "Wegovy": "WEGOVY",
    "Victoza 2-Pak": "VICTOZA",
    "Victoza 3-Pak": "VICTOZA",
    "Xultophy 100-3.6": "XULTOPHY 100/3.6",
    "Mounjaro": "MOUNJARO",
    "Zepbound": "ZEPBOUND",
    "Trulicity": "TRULICITY",
}


def publicado() -> dict[tuple[int, str], int]:
    """Recetas totales por (año, marca del caso), del dataset de gasto."""
    total: dict[tuple[int, str], int] = {}
    with open(asegurar_gasto(), newline="") as f:
        for fila in csv.DictReader(f):
            if fila["Mftr_Name"].strip() != "Overall":
                continue
            marca = GASTO_A_CASO.get(fila["Brnd_Name"].strip())
            if marca is None:
                continue
            for anio in (2021, 2022, 2023, 2024):
                bruto = fila[f"Tot_Clms_{anio}"].strip()
                if bruto:
                    total[(anio, marca)] = total.get((anio, marca), 0) + int(bruto)
    return total


def detalle() -> dict[tuple[int, str], int]:
    con = duckdb.connect()
    filas = con.sql(
        f"""
        SELECT anio, marca_caso AS marca, sum(Tot_Clms) AS recetas
        FROM read_parquet('{PQ}/part_d_glp1_*.parquet', union_by_name=true)
        GROUP BY 1, 2
        """
    ).fetchall()
    return {(int(a), m): int(r) for a, m, r in filas}


def main() -> int:
    pub, det = publicado(), detalle()
    filas = []
    for clave in sorted(det):
        anio, marca = clave
        p = pub.get(clave)
        d = det[clave]
        filas.append(
            {
                "anio": anio,
                "marca": marca,
                "recetas_publicadas": p,
                "recetas_en_detalle": d,
                "diferencia": None if p is None else p - d,
                "pct_no_visible": None if not p else round(100.0 * (p - d) / p, 2),
            }
        )
    anios = sorted({f["anio"] for f in filas})
    resumen = []
    for anio in anios:
        del_anio = [f for f in filas if f["anio"] == anio and f["recetas_publicadas"]]
        tp = sum(f["recetas_publicadas"] for f in del_anio)
        td = sum(f["recetas_en_detalle"] for f in del_anio)
        resumen.append(
            {
                "anio": anio,
                "publicadas": tp,
                "en_detalle": td,
                "no_visibles": tp - td,
                "pct_no_visible": round(100.0 * (tp - td) / tp, 2),
            }
        )
    salida = {
        "que_mide": (
            "recetas que el archivo de detalle no muestra porque el par "
            "prescriptor-droga tiene 10 o menos"
        ),
        "fuente_publicada": "CMS Medicare Part D Spending by Drug, DSD_PTD_RY26_P04_V10_DY24_BGM.csv",
        "fuente_detalle": "CMS Medicare Part D Prescribers by Provider and Drug, recorte GLP-1",
        "por_anio": resumen,
        "por_marca": filas,
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2))
    print(json.dumps(salida, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
