"""Corte 03 — a qué perfil profesional le paga cada compañía.

Pregunta: el dinero de GLP-1, ¿va al especialista o al canal de volumen? ¿Y las
dos compañías apuestan al mismo perfil?

Decisiones aplicadas: D-001 · D-002 · D-003 · D-004 · D-006 · D-008
(cinco categorías de especialidad, con el tipo mandando en NP/PA).

Cachea agregados chicos en findings/cache/corte-03_especialidades.json. El chart
lee SOLO ese JSON, nunca el parquet.

Uso:  uv run analysis/corte-03_especialidades.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_DESDE, ANIO_HASTA, conectar  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "findings" / "cache"
DESTINO = CACHE / "corte-03_especialidades.json"


def main() -> None:
    con = conectar()

    # Reparto del gasto de cada compañía entre perfiles, y el dinero por cabeza.
    reparto = con.sql(
        """
        SELECT especialidad,
               sum(usd) FILTER (grupo = 'novo')  AS novo_usd,
               sum(usd) FILTER (grupo = 'lilly') AS lilly_usd,
               100.0*sum(usd) FILTER (grupo = 'novo')
                   / sum(sum(usd) FILTER (grupo = 'novo')) OVER ()  AS novo_pct,
               100.0*sum(usd) FILTER (grupo = 'lilly')
                   / sum(sum(usd) FILTER (grupo = 'lilly')) OVER () AS lilly_pct,
               count(DISTINCT receptor_id) AS hcps,
               count(DISTINCT record_id)   AS pagos,
               sum(usd) / count(DISTINCT receptor_id) AS usd_por_hcp
        FROM glp1 WHERE especialidad IS NOT NULL
        GROUP BY 1 ORDER BY novo_usd + lilly_usd DESC
        """
    ).df()

    # ¿El perfil cambia según qué compra el pago? (D-006)
    por_naturaleza = con.sql(
        """
        SELECT especialidad, grupo_naturaleza,
               sum(usd) FILTER (grupo = 'novo')  AS novo_usd,
               sum(usd) FILTER (grupo = 'lilly') AS lilly_usd
        FROM glp1 WHERE especialidad IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    # Evolución: ¿alguien se corrió de perfil dentro de la ventana?
    serie = con.sql(
        """
        SELECT anio, especialidad,
               100.0*sum(usd) FILTER (grupo = 'novo')
                   / sum(sum(usd) FILTER (grupo = 'novo')) OVER (PARTITION BY anio)  AS novo_pct,
               100.0*sum(usd) FILTER (grupo = 'lilly')
                   / sum(sum(usd) FILTER (grupo = 'lilly')) OVER (PARTITION BY anio) AS lilly_pct
        FROM glp1 WHERE especialidad IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    salida = {
        "corte": "03_especialidades",
        "ventana": [ANIO_DESDE, ANIO_HASTA],
        "decisiones": ["D-001", "D-002", "D-003", "D-004", "D-006", "D-008"],
        "reparto": reparto.to_dict("records"),
        "por_naturaleza": por_naturaleza.to_dict("records"),
        "serie": serie.to_dict("records"),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=float))
    print(f"cache → {DESTINO.relative_to(Path.cwd())}\n")

    print("Reparto del gasto por perfil profesional:")
    print(reparto.assign(
        novo_usd=lambda d: (d.novo_usd / 1e6).round(2),
        lilly_usd=lambda d: (d.lilly_usd / 1e6).round(2),
        novo_pct=lambda d: d.novo_pct.round(1),
        lilly_pct=lambda d: d.lilly_pct.round(1),
        usd_por_hcp=lambda d: d.usd_por_hcp.round(0),
    ).to_string(index=False))

    endo = reparto[reparto.especialidad == "endocrinologia"].iloc[0]
    nppa = reparto[reparto.especialidad == "NP/PA"].iloc[0]
    print(f"\nEndocrinología: {endo.hcps:,} profesionales, "
          f"USD {endo.usd_por_hcp:,.0f} por cabeza.")
    print(f"NP/PA:          {nppa.hcps:,} profesionales, "
          f"USD {nppa.usd_por_hcp:,.0f} por cabeza "
          f"({endo.usd_por_hcp/nppa.usd_por_hcp:.0f}x menos).")
    print(f"\nEndocrinología es el {endo.lilly_pct:.1f}% del gasto de Lilly "
          f"y el {endo.novo_pct:.1f}% del de Novo.")


if __name__ == "__main__":
    main()
