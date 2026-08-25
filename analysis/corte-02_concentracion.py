"""Corte 02 — cuán concentrado está el gasto GLP-1 en pocos profesionales.

Nace de una pregunta que dejó abierta el red-team del corte 01: el ataque C1
mostró que si se recorta el 1% de pagos más caros, Lilly supera a Novo también
en 2025. O sea el liderazgo de Novo ese año vive en su cola de pagos grandes.
Este corte pregunta de quién es esa cola.

Métrica: % del gasto que recibe el top 100 de cada compañía, con Gini como
control (D-007). El receptor es Covered_Recipient_Profile_ID; los hospitales
docentes no lo tienen y quedan afuera (43 pagos, USD 75.300, 0,04%).

Decisiones aplicadas: D-001 · D-002 · D-003 · D-004 · D-006 · D-007.

Uso:  uv run analysis/corte-02_concentracion.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_DESDE, ANIO_HASTA, conectar  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "findings" / "cache"
DESTINO = CACHE / "corte-02_concentracion.json"

# Cortes reportados. El titular usa 100 (D-007); los demás muestran que el
# hallazgo no depende de ese N.
TOPS = (10, 50, 100, 500, 1000)


def main() -> None:
    con = conectar()

    # Base: gasto total por profesional y compañía.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW por_hcp AS
        SELECT grupo, receptor_id, sum(usd) AS usd,
               count(DISTINCT record_id) AS pagos,
               sum(usd) FILTER (grupo_naturaleza = 'voz') AS usd_voz
        FROM glp1 WHERE receptor_id IS NOT NULL
        GROUP BY 1, 2
        """
    )
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW rankeado AS
        SELECT *, row_number() OVER (PARTITION BY grupo ORDER BY usd DESC) AS rn,
               row_number() OVER (PARTITION BY grupo ORDER BY usd) AS rn_asc,
               count(*) OVER (PARTITION BY grupo) AS n,
               sum(usd) OVER (PARTITION BY grupo) AS total
        FROM por_hcp
        """
    )

    tops = ", ".join(
        f"round(100.0*sum(usd) FILTER (rn <= {t})/any_value(total), 2) AS top{t}"
        for t in TOPS
    )
    concentracion = con.sql(
        f"""
        SELECT grupo, any_value(n) AS red_hcps,
               round(any_value(total)/1e6, 2) AS musd,
               {tops},
               round(100.0*sum(usd) FILTER (rn <= n*0.01)/any_value(total), 2) AS top1pct,
               -- Gini sobre la distribución completa, orden ascendente.
               round(2.0*sum(rn_asc*usd)/(any_value(n)*any_value(total))
                     - (any_value(n)+1.0)/any_value(n), 4) AS gini,
               round(median(usd), 2) AS mediana_hcp,
               round(max(usd), 2) AS mayor_hcp
        FROM rankeado GROUP BY grupo ORDER BY grupo
        """
    ).df()

    # Curva de Lorenz, submuestreada para que el cache siga siendo chico.
    lorenz = con.sql(
        """
        SELECT grupo, pct_hcp,
               round(max(pct_usd), 4) AS pct_usd
        FROM (
            SELECT grupo,
                   round(100.0*rn/n, 0) AS pct_hcp,
                   100.0*sum(usd) OVER (PARTITION BY grupo ORDER BY usd DESC
                                        ROWS UNBOUNDED PRECEDING)/total AS pct_usd
            FROM rankeado
        ) GROUP BY grupo, pct_hcp ORDER BY grupo, pct_hcp
        """
    ).df()

    # ¿Quiénes son los del top 100? Sin nombres: sólo el perfil del gasto.
    perfil_top = con.sql(
        """
        SELECT grupo,
               round(avg(usd), 0) AS usd_promedio,
               round(min(usd), 0) AS usd_minimo,
               round(avg(pagos), 1) AS pagos_promedio,
               round(100.0*sum(usd_voz)/sum(usd), 1) AS pct_voz
        FROM rankeado WHERE rn <= 100 GROUP BY grupo ORDER BY grupo
        """
    ).df()

    # Concentración DENTRO de cada grupo de naturaleza. La agrega el ataque 06
    # (C3): la concentración de Lilly no es general, vive en su programa de voz,
    # y ahí los dos círculos tienen tamaños muy distintos.
    por_naturaleza = con.sql(
        """
        WITH x AS (SELECT grupo, grupo_naturaleza, receptor_id, sum(usd) AS usd
                   FROM glp1 WHERE receptor_id IS NOT NULL GROUP BY 1, 2, 3),
             r AS (SELECT *,
                          row_number() OVER (PARTITION BY grupo, grupo_naturaleza
                                             ORDER BY usd DESC) rn,
                          count(*) OVER (PARTITION BY grupo, grupo_naturaleza) n,
                          sum(usd) OVER (PARTITION BY grupo, grupo_naturaleza) total
                   FROM x)
        SELECT grupo_naturaleza, grupo,
               any_value(n) AS red_hcps,
               round(any_value(total), 2) AS usd,
               round(any_value(total)/any_value(n), 0) AS usd_por_hcp,
               round(100.0*sum(usd) FILTER (rn <= 100)/any_value(total), 2) AS top100
        FROM r GROUP BY grupo_naturaleza, grupo ORDER BY grupo_naturaleza, grupo
        """
    ).df()

    salida = {
        "corte": "02_concentracion",
        "ventana": [ANIO_DESDE, ANIO_HASTA],
        "decisiones": ["D-001", "D-002", "D-003", "D-004", "D-006", "D-007"],
        "metrica_lider": "% del gasto al top 100 de profesionales (D-007)",
        "concentracion": concentracion.to_dict("records"),
        "lorenz": lorenz.to_dict("records"),
        "perfil_top100": perfil_top.to_dict("records"),
        "por_naturaleza": por_naturaleza.to_dict("records"),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=float))
    print(f"cache → {DESTINO.relative_to(Path.cwd())}\n")

    print("Concentración del gasto GLP-1 por profesional receptor:")
    print(concentracion.to_string(index=False))
    print("\nPerfil del top 100 de cada compañía:")
    print(perfil_top.to_string(index=False))
    print("\nConcentración dentro de cada grupo de naturaleza (D-006):")
    print(por_naturaleza.to_string(index=False))

    l, n = (concentracion.set_index("grupo").top100.get(g) for g in ("lilly", "novo"))
    print(f"\nEl top 100 de Lilly recibe {l:.1f}% de su gasto; el de Novo, {n:.1f}%. "
          f"Lilly concentra {l/n:.2f}x más.")


if __name__ == "__main__":
    main()
