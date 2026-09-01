"""CSV (dentro del ZIP anual) → Parquet por año, vía DuckDB.

Se conservan TODAS las columnas tal cual vienen: la selección y el renombrado
ocurren en las vistas (03), nunca en la conversión. Al final imprime el esquema
del último año convertido, para compararlo contra los campos esperados.

Campos que el análisis espera encontrar (verificar contra el esquema real):
  Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name
  Total_Amount_of_Payment_USDollars · Date_of_Payment
  Nature_of_Payment_or_Transfer_of_Value
  Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1..5
  Associated_Drug_or_Biological_NDC_1..5
  Covered_Recipient_Specialty_1 · Covered_Recipient_Type
  Recipient_State · Record_ID · Dispute_Status_for_Publication

Uso:  uv run scripts/02_convertir_parquet.py [anio ...]
"""

import sys
import zipfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PQ = ROOT / "data" / "parquet"


def convertir(anio: int) -> None:
    zip_path = RAW / f"PGYR{anio}.zip"
    PQ.mkdir(parents=True, exist_ok=True)
    destino = PQ / f"general_{anio}.parquet"
    if destino.exists():
        print(f"PY{anio}: parquet ya existe, salteando.")
        return
    # El ZIP anual trae varios CSV; el de General Payments es el que empieza
    # con OP_DTL_GNRL. Se extrae solo ese.
    with zipfile.ZipFile(zip_path) as z:
        nombre = next(n for n in z.namelist() if "GNRL" in n.upper())
        print(f"PY{anio}: extrayendo {nombre}…")
        z.extract(nombre, RAW)
    csv_path = RAW / nombre
    print(f"PY{anio}: convirtiendo a parquet…")
    duckdb.sql(
        f"""
        COPY (SELECT * FROM read_csv('{csv_path}', header=true,
                                     all_varchar=false, sample_size=200000,
                                     types={{'Recipient_Postal_Code': 'VARCHAR',
                                             'Recipient_Zip_Code': 'VARCHAR'}}))
        TO '{destino}' (FORMAT parquet, COMPRESSION zstd)
        """
    )
    csv_path.unlink()  # el CSV extraído no se conserva: el ZIP + parquet alcanzan
    print(f"PY{anio}: listo → {destino.name}")


if __name__ == "__main__":
    anios = [int(a) for a in sys.argv[1:]] or sorted(
        int(p.stem[4:]) for p in RAW.glob("PGYR*.zip")
    )
    if not anios:
        sys.exit(
            f"No hay ZIP para convertir en {RAW}. "
            "Correr primero: uv run scripts/01_descargar.py [anio ...]"
        )
    for a in anios:
        convertir(a)
    ultimo = PQ / f"general_{anios[-1]}.parquet"
    print("\nEsquema del último año convertido:")
    print(duckdb.sql(f"DESCRIBE SELECT * FROM '{ultimo}'").df().to_string())
