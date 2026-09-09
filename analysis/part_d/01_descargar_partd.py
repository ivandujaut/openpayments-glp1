"""Descarga reproducible de Medicare Part D Prescribers (CMS).

Segundo caso de la familia GLP-1 (`glp1-quien-receta`): el otro lado del cruce.
Open Payments dice cuánto cobró cada NPI; Part D dice cuánto recetó. La llave
es el NPI.

Misma regla que `scripts/01_descargar.py`: data/ nunca se commitea, este script
más `checksums_partd.txt` SON la reproducibilidad. El manifiesto se reescribe
entero en cada corrida; si un archivo ya anotado cambia de sha256, se corta.

Dos datasets, uno por archivo y año:

- NPIBN ("by Provider and Drug"): una fila por prescriptor y droga. Es el que
  trae las recetas de cada GLP-1.
- NPI ("by Provider"): una fila por prescriptor. Trae el total de la práctica,
  necesario para medir el GLP-1 como proporción y no sólo en volumen.

URLs capturadas el 2026-09-08 de https://data.cms.gov/data.json (catálogo DCAT
oficial de CMS), campo `distribution[].downloadURL` de los datasets
9552739e-3d05-4c1b-8eff-ecabf391e2e5 y 14d8e8a9-7e9b-4370-a044-bf97c46b4b44.

Ventana: 2021-2024. El techo NO es una elección: **2024 es el año más nuevo que
CMS publica de Part D** (Data Year 2024, release year 2026), mientras Open
Payments ya publica PY2025. El rezago de un año es un límite del caso y se
declara en la hoja de hechos.

Uso:  uv run analysis/part_d/01_descargar_partd.py [anio ...]
"""

import hashlib
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "part_d"
CHECKSUMS = Path(__file__).parent / "checksums_partd.txt"
CABECERA = (
    "# Manifiesto de descarga de Medicare Part D Prescribers.\n"
    "# Columnas separadas por tab: clave, sha256, url\n"
    "# Regenerable con: uv run analysis/part_d/01_descargar_partd.py\n"
)

# by Provider and Drug (NPIBN): prescriptor x droga
URLS_NPIBN: dict[int, str] = {
    2021: "https://data.cms.gov/sites/default/files/2024-05/43359391-e7fa-40b9-9bd4-5dc295e18712/MUP_DPR_RY24_P04_V10_DY21_NPIBN.csv",
    2022: "https://data.cms.gov/sites/default/files/2024-05/18f82097-61a6-4889-9941-9a0b6ad7523c/MUP_DPR_RY24_P04_V10_DY22_NPIBN.csv",
    2023: "https://data.cms.gov/sites/default/files/2025-04/0d5915ce-002c-4d87-bde8-24ffb08bb6cc/MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv",
    2024: "https://data.cms.gov/sites/default/files/2026-05/0ae165f4-eb44-495d-8cac-67f4571b6b83/MUP_DPR_RY26_P04_V10_DY24_NPIBN.csv",
}

# by Provider (NPI): total de la práctica de cada prescriptor
URLS_NPI: dict[int, str] = {
    2021: "https://data.cms.gov/sites/default/files/2026-08/a8cb773f-4a79-42de-b7ad-83da254416bf/mup_dpr_ry23_p04_v20_dy21_npi.csv",
    2022: "https://data.cms.gov/sites/default/files/2026-08/0cdbfc0d-257d-4eb0-bcc8-71e5462ec320/mup_dpr_ry24_p04_v20_dy22_npi.csv",
    2023: "https://data.cms.gov/sites/default/files/2026-08/7f74c86e-ca81-4255-8951-3275c4361241/mup_dpr_ry25_p04_v20_dy23_npi.csv",
    2024: "https://data.cms.gov/sites/default/files/2026-08/373e45e5-33ec-452c-9302-a4bdbc203459/mup_dpr_ry26_p04_v20_dy24_npi.csv",
}

ANIOS = sorted(URLS_NPIBN)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_manifiesto() -> dict[str, tuple[str, str]]:
    if not CHECKSUMS.exists():
        return {}
    registro: dict[str, tuple[str, str]] = {}
    for linea in CHECKSUMS.read_text().splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        clave, digest, url = linea.split("\t")
        registro[clave] = (digest, url)
    return registro


def escribir_manifiesto(registro: dict[str, tuple[str, str]]) -> None:
    lineas = [CABECERA]
    for clave in sorted(registro):
        digest, url = registro[clave]
        lineas.append(f"{clave}\t{digest}\t{url}\n")
    CHECKSUMS.write_text("".join(lineas))


def descargar(url: str, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(parcial, "wb") as f:
            for trozo in r.iter_content(chunk_size=1 << 20):
                f.write(trozo)
    parcial.rename(destino)


def main(anios: list[int]) -> int:
    registro = leer_manifiesto()
    for anio in anios:
        for etiqueta, urls in (("npibn", URLS_NPIBN), ("npi", URLS_NPI)):
            clave = f"{etiqueta}_{anio}"
            url = urls[anio]
            destino = RAW / f"{clave}.csv"
            if not destino.exists():
                print(f"[{clave}] descargando {url}")
                descargar(url, destino)
            digest = sha256(destino)
            if clave in registro and registro[clave][0] != digest:
                print(
                    f"[{clave}] ABORTA: sha256 no coincide con el manifiesto.\n"
                    f"  manifiesto: {registro[clave][0]}\n"
                    f"  archivo:    {digest}",
                    file=sys.stderr,
                )
                return 1
            registro[clave] = (digest, url)
            mb = destino.stat().st_size / (1 << 20)
            print(f"[{clave}] ok  {mb:,.0f} MB  sha256={digest[:16]}...")
    escribir_manifiesto(registro)
    return 0


if __name__ == "__main__":
    pedidos = [int(a) for a in sys.argv[1:]] or ANIOS
    raise SystemExit(main(pedidos))
