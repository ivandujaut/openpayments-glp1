"""Descarga reproducible de CMS Open Payments (General Payments).

Regla del caso: data/ nunca se commitea; este script + checksums.txt SON la
reproducibilidad. Las URLs exactas de cada Program Year se resuelven UNA vez
con /browse en openpaymentsdata.cms.gov y quedan registradas acá con fecha.

checksums.txt es un MANIFIESTO, no un log: una línea por año, reescrita entera
en cada corrida. Si un año ya está anotado, el sha256 recalculado tiene que
coincidir; si no coincide, se corta. Un ZIP que cambió bajo los pies invalida
todo número ya publicado sobre ese año.

Uso:  uv run scripts/01_descargar.py [anio ...]   (sin args: todos los YEARS)
"""

import hashlib
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CHECKSUMS = Path(__file__).parent / "checksums.txt"
CABECERA = (
    "# Manifiesto de descarga. Columnas separadas por tab: anio, sha256, url\n"
    "# Regenerable con: uv run scripts/01_descargar.py\n"
)

# Capturadas el 2026-08-25 de openpaymentsdata.cms.gov/datasets/download
# (Dataset Downloads). El sufijo del nombre es el sello de publicación de CMS:
# P06302026 = publicado 2026-06-30, _06032026 = datos al 2026-06-03. Ese sello
# cambia en cada refresh anual de CMS: si cambia, cambian las URLs y saltan los
# checksums del manifiesto — que es exactamente lo que queremos que pase.
# Cada ZIP es el año completo (General + Research + Ownership); 02_convertir
# extrae solo el CSV OP_DTL_GNRL. Tamaños al día de captura: 2021 869 MB,
# 2022 998 MB, 2023 1.2 GB, 2024 1.2 GB, 2025 1.3 GB (~5.5 GB en total).
URLS: dict[int, str] = {
    # D-014: 2017-2020 solo para el ataque de censura; 2016 no esta disponible
    # (CMS lo retiro de la publicacion activa). 2017-2018 sobreviven bajo el
    # sello P01302025; 2019-2020 bajo el vigente.
    2017: "https://download.cms.gov/openpayments/PGYR2017_P01302025_01212025.zip",
    2018: "https://download.cms.gov/openpayments/PGYR2018_P01302025_01212025.zip",
    2019: "https://download.cms.gov/openpayments/PGYR2019_P06302026_06032026.zip",
    2020: "https://download.cms.gov/openpayments/PGYR2020_P06302026_06032026.zip",
    2021: "https://download.cms.gov/openpayments/PGYR2021_P06302026_06032026.zip",
    2022: "https://download.cms.gov/openpayments/PGYR2022_P06302026_06032026.zip",
    2023: "https://download.cms.gov/openpayments/PGYR2023_P06302026_06032026.zip",
    2024: "https://download.cms.gov/openpayments/PGYR2024_P06302026_06032026.zip",
    2025: "https://download.cms.gov/openpayments/PGYR2025_P06302026_06032026.zip",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_manifiesto() -> dict[int, tuple[str, str]]:
    """anio → (sha256, url). Devuelve {} si todavía no hay manifiesto."""
    if not CHECKSUMS.exists():
        return {}
    registro: dict[int, tuple[str, str]] = {}
    for linea in CHECKSUMS.read_text().splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        anio, digest, url = linea.split("\t")
        registro[int(anio)] = (digest, url)
    return registro


def anotar(anio: int, digest: str, url: str) -> None:
    """Reescribe el manifiesto completo: una sola línea por año, ordenado."""
    registro = leer_manifiesto()
    registro[anio] = (digest, url)
    with open(CHECKSUMS, "w") as f:
        f.write(CABECERA)
        for a in sorted(registro):
            d, u = registro[a]
            f.write(f"{a}\t{d}\t{u}\n")


def descargar(anio: int) -> None:
    url = URLS.get(anio)
    if not url:
        sys.exit(f"Sin URL registrada para PY{anio}: completar URLS primero.")
    RAW.mkdir(parents=True, exist_ok=True)
    destino = RAW / f"PGYR{anio}.zip"
    if destino.exists():
        print(f"PY{anio}: ya existe, verificando checksum…")
    else:
        print(f"PY{anio}: descargando…")
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    digest = sha256(destino)
    esperado = leer_manifiesto().get(anio)
    if esperado is None:
        anotar(anio, digest, url)
        print(f"PY{anio}: sha256={digest[:16]}… anotado en checksums.txt")
        return
    if esperado[0] != digest:
        sys.exit(
            f"PY{anio}: CHECKSUM NO COINCIDE.\n"
            f"  manifiesto: {esperado[0]}\n"
            f"  archivo:    {digest}\n"
            "El ZIP cambió respecto del que produjo los números publicados "
            "(refresh de CMS, descarga corrupta o URL distinta). Frenar: revisar "
            "la fuente y, si el cambio es legítimo, borrar la línea del año en "
            "checksums.txt y rehacer los checks de ese año."
        )
    print(f"PY{anio}: sha256={digest[:16]}… verificado contra el manifiesto")


if __name__ == "__main__":
    anios = [int(a) for a in sys.argv[1:]] or sorted(URLS)
    if not anios:
        sys.exit(
            "No hay años que descargar: completar el dict URLS con los ZIP "
            "anuales del Dataset Download Page de openpaymentsdata.cms.gov."
        )
    for a in anios:
        descargar(a)
