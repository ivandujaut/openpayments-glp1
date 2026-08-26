"""Corte 04 — la convergencia de 2025: adónde se movió cada compañía.

Nace del red-team del corte 03 (ataque 08, A5): el peso de endocrinología en el
gasto de Lilly y Novo converge de 30 puntos de brecha en 2023 a 3,3 en 2025.
Este corte pregunta qué hay detrás de esa convergencia — y la respuesta es que
no convergieron haciendo lo mismo.

Unidad líder: dólares absolutos (D-005). El porcentaje muestra la convergencia
pero esconde su mecanismo: en proporciones dos compañías pueden acercarse
mientras se mueven en direcciones opuestas, que es exactamente lo que pasa acá.

Decisiones aplicadas: D-001 · D-002 · D-003 · D-004 · D-006 · D-009.

Uso:  uv run analysis/corte-04_convergencia.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_DESDE, ANIO_HASTA, conectar  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "findings" / "cache"
DESTINO = CACHE / "corte-04_convergencia.json"
PIVOTE = 2023  # año del pico de divergencia, según el ataque 08


def main() -> None:
    con = conectar()

    # Trayectoria en dólares absolutos: la convergencia en % esconde el sentido.
    trayectoria = con.sql(
        """
        SELECT grupo, especialidad, anio, sum(usd) AS usd,
               count(DISTINCT receptor_id) AS hcps
        FROM glp1 WHERE especialidad IS NOT NULL
        GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
        """
    ).df()

    # El movimiento entre el pico de divergencia y el final de la ventana.
    movimiento = con.sql(
        f"""
        SELECT grupo, especialidad,
               sum(usd) FILTER (anio = {PIVOTE})    AS usd_pivote,
               sum(usd) FILTER (anio = {ANIO_HASTA}) AS usd_final,
               sum(usd) FILTER (anio = {ANIO_HASTA})
                   - sum(usd) FILTER (anio = {PIVOTE}) AS delta
        FROM glp1 WHERE especialidad IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, delta DESC
        """
    ).df()

    # Quién paga las especialidades emergentes, y con qué producto.
    emergentes = con.sql(
        """
        SELECT producto, any_value(grupo) AS grupo,
               sum(usd) FILTER (anio = 2023) AS usd_2023,
               sum(usd) FILTER (anio = 2025) AS usd_2025,
               sum(usd) AS usd_total
        FROM glp1 WHERE especialidad = 'emergentes'
        GROUP BY producto HAVING sum(usd) > 100000
        ORDER BY usd_2025 DESC
        """
    ).df()

    salida = {
        "corte": "04_convergencia",
        "ventana": [ANIO_DESDE, ANIO_HASTA],
        "pivote": PIVOTE,
        "decisiones": ["D-001", "D-002", "D-003", "D-004", "D-006", "D-009"],
        "unidad_lider": "dólares absolutos (D-005): el % converge, los USD divergen",
        "trayectoria": trayectoria.to_dict("records"),
        "movimiento": movimiento.to_dict("records"),
        "emergentes_por_producto": emergentes.to_dict("records"),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=float))
    print(f"cache → {DESTINO.relative_to(Path.cwd())}\n")

    print(f"Movimiento en USD entre {PIVOTE} (pico de divergencia) y {ANIO_HASTA}:")
    for grupo in ("lilly", "novo"):
        sub = movimiento[movimiento.grupo == grupo]
        print(f"\n  {grupo.upper()}")
        for f in sub.itertuples():
            signo = "+" if f.delta >= 0 else "−"
            print(f"    {f.especialidad:<22} {f.usd_pivote/1e6:>6.2f} → "
                  f"{f.usd_final/1e6:>6.2f}   {signo}{abs(f.delta)/1e6:.2f}M")

    print("\nEspecialidades emergentes, por producto (USD M):")
    print(emergentes.assign(
        usd_2023=lambda d: (d.usd_2023 / 1e6).round(2),
        usd_2025=lambda d: (d.usd_2025 / 1e6).round(2),
        usd_total=lambda d: (d.usd_total / 1e6).round(2),
    ).to_string(index=False))


if __name__ == "__main__":
    main()
