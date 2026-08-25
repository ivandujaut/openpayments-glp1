"""Reconciliación contra los agregados oficiales de CMS (skill /reconciliar).

Los valores OFICIALES se cargan UNA vez, a mano, desde la página de agregados
de CMS, con URL y fecha de captura al lado. Cualquier Δ > 1% detiene el
análisis (regla de la skill).

Uso:  uv run scripts/04_checks.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402  (después del bootstrap de path)

# TODO(primera sesión): completar desde la fuente con /browse.
# Formato: anio: {"total_usd": float, "total_n": int, "fuente": "URL (capturada AAAA-MM-DD)"}
OFICIALES: dict[int, dict] = {
    # 2025: {"total_usd": 14_670_000_000.0, "total_n": 17_070_000,
    #        "fuente": "https://... (capturada 2026-08-XX)"},
}

TOLERANCIA = 0.01


def main() -> None:
    if not OFICIALES:
        raise SystemExit("Completar OFICIALES antes de reconciliar (con /browse).")
    con = conectar()
    propios = con.sql(
        """
        SELECT regexp_extract(filename, '(\\d{4})', 1)::INT AS anio,
               sum(Total_Amount_of_Payment_USDollars) AS total_usd,
               count(*) AS total_n
        FROM pagos GROUP BY 1 ORDER BY 1
        """
    ).df()
    rojo = False
    print(f"{'métrica':<28}{'propio':>18}{'oficial':>18}{'Δ%':>8}")
    for _, fila in propios.iterrows():
        of = OFICIALES.get(int(fila.anio))
        if not of:
            continue
        for k, mio in (("total_usd", fila.total_usd), ("total_n", fila.total_n)):
            delta = (mio - of[k]) / of[k]
            marca = "" if abs(delta) <= TOLERANCIA else "  ← ROJO"
            rojo = rojo or abs(delta) > TOLERANCIA
            print(f"PY{int(fila.anio)} {k:<22}{mio:>18,.0f}{of[k]:>18,.0f}{delta:>7.2%}{marca}")
    print("\nEstado:", "🔴 DETENER: listar hipótesis (ver skill)" if rojo else "🟢 verde")


if __name__ == "__main__":
    main()
