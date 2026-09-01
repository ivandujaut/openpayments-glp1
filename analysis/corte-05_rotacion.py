"""Corte 05 — cuánto dura la relación de voz: rotación, salidas y permanencia.

Nace del experimento que el caso publicado dejó fijado: "cuántos de los 657
profesionales del programa de Lilly siguen ahí tres años después", con su
descarte escrito antes de correr nada (rotación anual > 30% = el modelo
concentrado es más frágil de lo que muestra el acumulado).

Unidad líder: profesionales (membresía D-012); los dólares acompañan para el
costo de reemplazo. Las dos cohortes de D-013 se calculan separadas: la anual
manda para la rotación, la acumulada responde al caso madre.

Decisiones aplicadas: D-001 · D-002 · D-003 · D-006 · D-012 · D-013 · D-015.
(D-004 no aplica a la membresía: pertenece quien cobró voz GLP-1, sin prorratear
personas; los dólares sí llegan prorrateados desde la vista glp1.)

Uso:  uv run analysis/corte-05_rotacion.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import ANIO_DESDE, ANIO_HASTA, conectar  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "findings" / "cache"
DESTINO = CACHE / "corte-05_rotacion.json"


def main() -> None:
    con = conectar()

    # Membresía anual (D-012): un profesional-año-grupo con >=1 pago de voz GLP-1.
    con.sql(
        """
        CREATE TEMP TABLE miembros AS
        SELECT DISTINCT grupo, anio, receptor_id
        FROM glp1
        WHERE grupo_naturaleza = 'voz' AND receptor_id IS NOT NULL
        """
    )

    cohortes = con.sql(
        """
        SELECT g.grupo, g.anio,
               count(DISTINCT g.receptor_id)              AS hcps,
               sum(g.usd)                                  AS usd,
               count(DISTINCT g.record_id)                 AS pagos
        FROM glp1 g
        WHERE g.grupo_naturaleza = 'voz' AND g.receptor_id IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    # Rotación año a año con las tres salidas de D-015, en orden (a) → (b) → (c).
    retencion = con.sql(
        f"""
        WITH pares AS (
            SELECT m.grupo, m.anio, m.receptor_id,
                   EXISTS (SELECT 1 FROM miembros r WHERE r.grupo = m.grupo
                           AND r.anio = m.anio + 1
                           AND r.receptor_id = m.receptor_id)         AS retenido,
                   EXISTS (SELECT 1 FROM voz_entidades v WHERE v.grupo = m.grupo
                           AND v.anio = m.anio + 1
                           AND v.receptor_id = m.receptor_id)         AS voz_misma,
                   EXISTS (SELECT 1 FROM miembros r WHERE r.grupo <> m.grupo
                           AND r.anio = m.anio + 1
                           AND r.receptor_id = m.receptor_id)         AS voz_rival
            FROM miembros m WHERE m.anio < {ANIO_HASTA}
        )
        SELECT grupo, anio,
               count(*)                                              AS miembros,
               count(*) FILTER (retenido)                            AS retenidos,
               count(*) FILTER (NOT retenido AND voz_misma)          AS reasignados,
               count(*) FILTER (NOT retenido AND NOT voz_misma
                                AND voz_rival)                       AS fichados,
               count(*) FILTER (NOT retenido AND NOT voz_misma
                                AND NOT voz_rival)                   AS afuera,
               round(100.0 * (count(*) - count(*) FILTER (retenido))
                     / count(*), 1)                                  AS rotacion_pct
        FROM pares GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    # Cohorte acumulada (D-013): el círculo del caso madre, con su matriz de
    # actividad por año y la permanencia (años activos en la ventana).
    acumulada = con.sql(
        """
        WITH por_persona AS (
            SELECT grupo, receptor_id,
                   count(DISTINCT anio)  AS anios_activo,
                   min(anio)             AS primer_anio,
                   max(anio)             AS ultimo_anio
            FROM miembros GROUP BY 1, 2
        )
        SELECT grupo,
               count(*)                                        AS circulo,
               round(avg(anios_activo), 2)                     AS anios_activo_prom,
               count(*) FILTER (anios_activo = 1)              AS un_solo_anio,
               count(*) FILTER (anios_activo = 5)              AS los_cinco,
               count(*) FILTER (primer_anio = 2021
                                AND ultimo_anio = 2025)        AS de_punta_a_punta
        FROM por_persona GROUP BY 1 ORDER BY 1
        """
    ).df()

    permanencia = con.sql(
        """
        WITH por_persona AS (
            SELECT grupo, receptor_id, count(DISTINCT anio) AS anios_activo
            FROM miembros GROUP BY 1, 2)
        SELECT grupo, anios_activo, count(*) AS hcps
        FROM por_persona GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    # El experimento del caso madre, literal: de los miembros de cada año,
    # cuántos siguen activos tres años después.
    tres_anios = con.sql(
        f"""
        SELECT m.grupo, m.anio,
               count(*) AS miembros,
               count(*) FILTER (EXISTS (SELECT 1 FROM miembros r
                    WHERE r.grupo = m.grupo AND r.anio = m.anio + 3
                      AND r.receptor_id = m.receptor_id))      AS activos_3_despues,
               round(100.0 * count(*) FILTER (EXISTS (SELECT 1 FROM miembros r
                    WHERE r.grupo = m.grupo AND r.anio = m.anio + 3
                      AND r.receptor_id = m.receptor_id)) / count(*), 1) AS pct
        FROM miembros m WHERE m.anio + 3 <= {ANIO_HASTA}
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    # Costo de reemplazo (P5): dólares de voz a nuevos vs retenidos por año.
    # 2021 queda censurado a izquierda y no se reparte (D-014 lo ataca aparte).
    gasto = con.sql(
        f"""
        WITH usd_py AS (
            SELECT grupo, anio, receptor_id, sum(usd) AS usd
            FROM glp1 WHERE grupo_naturaleza = 'voz' AND receptor_id IS NOT NULL
            GROUP BY 1, 2, 3)
        SELECT u.grupo, u.anio,
               sum(u.usd) FILTER (EXISTS (SELECT 1 FROM miembros r
                    WHERE r.grupo = u.grupo AND r.anio = u.anio - 1
                      AND r.receptor_id = u.receptor_id))      AS usd_retenidos,
               sum(u.usd) FILTER (NOT EXISTS (SELECT 1 FROM miembros r
                    WHERE r.grupo = u.grupo AND r.anio = u.anio - 1
                      AND r.receptor_id = u.receptor_id))      AS usd_nuevos
        FROM usd_py u WHERE u.anio > {ANIO_DESDE}
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    # D-016: las bandas fijas del hallazgo principal. Comparación a igual
    # inversión; los cuartiles propios quedan en el ataque 14 como robustez.
    bandas = con.sql(
        f"""
        WITH pa AS (
            SELECT b.grupo, b.anio, b.receptor_id, sum(b.usd) AS usd,
                   CASE WHEN EXISTS (SELECT 1 FROM miembros r WHERE r.grupo=b.grupo
                        AND r.anio=b.anio+1 AND r.receptor_id=b.receptor_id)
                   THEN 1 ELSE 0 END AS ret
            FROM glp1 b
            WHERE b.grupo_naturaleza='voz' AND b.receptor_id IS NOT NULL
              AND b.anio < {ANIO_HASTA}
            GROUP BY 1, 2, 3)
        SELECT CASE WHEN usd < 5000 THEN 'a <5k'
                    WHEN usd < 25000 THEN 'b 5-25k'
                    WHEN usd < 75000 THEN 'c 25-75k'
                    ELSE 'd 75k+' END AS banda,
               grupo, count(*) AS prof_anios,
               round(100.0*avg(ret), 1) AS retencion_pct
        FROM pa GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df()

    salida = {
        "corte": "05_rotacion",
        "ventana": [ANIO_DESDE, ANIO_HASTA],
        "decisiones": ["D-001", "D-002", "D-003", "D-006", "D-012", "D-013", "D-015", "D-016"],
        "unidad_lider": "profesionales (membresía D-012); dólares para costo de reemplazo",
        "cohortes": cohortes.to_dict("records"),
        "retencion": retencion.to_dict("records"),
        "acumulada": acumulada.to_dict("records"),
        "permanencia": permanencia.to_dict("records"),
        "tres_anios": tres_anios.to_dict("records"),
        "gasto_nuevos_vs_retenidos": gasto.to_dict("records"),
        "retencion_por_banda": bandas.to_dict("records"),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=float))
    print(f"cache → {DESTINO.relative_to(Path.cwd())}\n")

    # Conciliación contra el corte 02: el círculo acumulado tiene que dar
    # exactamente 657 (Lilly) y 1.139 (Novo) o hay un error de definición.
    print("Círculo acumulado (control contra corte 02: 657 / 1.139):")
    for f in acumulada.itertuples():
        print(f"  {f.grupo:<6} {f.circulo:>6}  · promedio {f.anios_activo_prom} años "
              f"activo · un solo año: {f.un_solo_anio} · los cinco: {f.los_cinco}")

    print("\nRotación anual (descarte publicado: > 30%):")
    for f in retencion.itertuples():
        print(f"  {f.grupo:<6} {f.anio}→{f.anio+1}  miembros {f.miembros:>4} · "
              f"rotación {f.rotacion_pct:>5}%  (reasignados {f.reasignados}, "
              f"fichados {f.fichados}, afuera {f.afuera})")

    print("\nActivos tres años después:")
    for f in tres_anios.itertuples():
        print(f"  {f.grupo:<6} cohorte {f.anio}: {f.miembros} → {f.activos_3_despues} "
              f"en {f.anio+3} ({f.pct}%)")


if __name__ == "__main__":
    main()
