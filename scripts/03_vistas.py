"""CLI fino sobre las vistas del caso (la lógica vive en src/vistas.py).

Sirve de smoke test: si esto imprime un conteo, los parquet están donde deben
y la vista `pagos` se crea bien.

Uso:  uv run scripts/03_vistas.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402  (después del bootstrap de path)

if __name__ == "__main__":
    con = conectar()
    print(con.sql("SELECT count(*) AS filas FROM pagos").df())
