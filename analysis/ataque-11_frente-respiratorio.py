"""Ataque 11 (familias A, B y C) — ¿el frente respiratorio de Lilly existe?

D-011 sacó de "resto" un bloque de especialidades (neumonología, medicina del
sueño y cuidados críticos) que en Lilly pasa de USD 0,01M en 2023 a 1,39M en
2025. D-011 puso una condición explícita: hasta que este red-team corra, ningún
finding puede afirmar el frente.

Hipótesis bajo ataque:
  H1  CRECIMIENTO: el gasto de Lilly en el bloque en 2025 es al menos 10x el de
      2023.
  H2  DOMINIO: en 2025 Lilly destina al bloque al menos 5x lo de Novo.

Familia A — artefactos del dato
  A1  ¿Los profesionales del bloque en 2025 ya estaban, con otra etiqueta? Es el
      ataque que mató frentes falsos antes (ver ataque 09). Reetiquetado puro.
  A2  ¿Los valores NUCC del bloque existen en los cinco años, o la taxonomía
      incorporó "Sleep Medicine" tarde? Si son valores nuevos, el frente es un
      artefacto de la taxonomía y no un movimiento comercial.
  A3  Sin registros disputados.
  A4  Pagos reales, ponderando por Number_of_Payments.

Familia B — sensibilidad a mis decisiones
  B1  D-011 alt: los tres sub-bloques por separado (sueño · neumo · críticos).
  B2  D-011 alt: evaluar el bloque ANTES de NP/PA, la alternativa rechazada.
  B3  D-004 alt: fila entera, sin prorratear.
  B4  D-002 alt: sólo la entidad operativa US.

Familia C — explicaciones alternativas de negocio
  C1  ¿Son unos pocos pagos gigantes? Sin el 1% más caro de cada compañía/año.
  C2  ¿Es el programa de voz otra vez (D-006)? Sólo campo · sólo voz.
  C3  ESCALA: el gasto de Lilly creció en el período; ¿el bloque es aritmética?
      Test: el bloque como porcentaje del crecimiento total de la compañía.
  C4  AMPLITUD: ¿un frente o un panel? Profesionales distintos por año.
  C5  PICO DE LANZAMIENTO: no es testeable con esta ventana y se declara.

Uso:  uv run analysis/ataque-11_frente-respiratorio.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

NOVO_US, LILLY_US = 100000000144, 100000000066

# El bloque de D-011, escrito como predicado para poder variarlo en los ataques.
BLOQUE = ("especialidad_cruda ILIKE '%pulmonary%' OR especialidad_cruda ILIKE '%sleep%' "
          "OR especialidad_cruda ILIKE '%critical care%'")
NP_PA = "Physician Assistants & Advanced Practice Nursing Providers"

CRECIMIENTO_MIN = 10.0   # H1: 2025 / 2023
DOMINIO_MIN = 5.0        # H2: Lilly 2025 / Novo 2025


def serie(con, filtro="TRUE", usd="usd", bloque="especialidad = 'respiratorio y sueño'"):
    """Gasto del bloque por compañía y año, bajo el filtro y la unidad del test."""
    df = con.sql(
        f"""
        SELECT grupo, anio, sum({usd}) AS usd
        FROM glp1 WHERE ({bloque}) AND {filtro}
        GROUP BY 1, 2
        """
    ).df()
    return {(r.grupo, r.anio): r.usd for r in df.itertuples()}


def evaluar(nombre, s):
    l23, l25 = s.get(("lilly", 2023), 0.0), s.get(("lilly", 2025), 0.0)
    n25 = s.get(("novo", 2025), 0.0)
    crec = l25 / l23 if l23 > 0 else float("inf")
    dom = l25 / n25 if n25 > 0 else float("inf")
    h1, h2 = crec >= CRECIMIENTO_MIN, dom >= DOMINIO_MIN
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        Lilly {l23/1e6:.3f}M → {l25/1e6:.3f}M ({crec:.0f}x) · "
          f"Novo 2025 {n25/1e6:.3f}M · dominio {dom:.0f}x")
    return h1, h2


def main() -> None:
    con = conectar()
    print("H1 CRECIMIENTO: Lilly 2025 >= 10x su 2023 en el bloque")
    print("H2 DOMINIO:     Lilly 2025 >= 5x Novo 2025 en el bloque\n")
    r = [("VIGENTE", *evaluar("VIGENTE  la partición de D-011", serie(con)))]

    # ---------------------------------------------------------------- familia A
    print("\nFAMILIA A — artefactos del dato\n")
    print("  A1  ¿de dónde salen los profesionales del bloque en 2025?")
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW clasificados AS
        WITH bloque_2025 AS (
            SELECT DISTINCT receptor_id FROM glp1
            WHERE especialidad = 'respiratorio y sueño' AND anio = 2025
              AND receptor_id IS NOT NULL
        ),
        historia AS (
            SELECT b.receptor_id,
                   count(*) FILTER (g.anio < 2025) AS previos,
                   count(*) FILTER (g.anio < 2025
                       AND g.especialidad = 'respiratorio y sueño') AS previos_bloque,
                   count(*) FILTER (g.anio < 2025
                       AND g.especialidad <> 'respiratorio y sueño') AS previos_otra
            FROM bloque_2025 b LEFT JOIN glp1 g USING (receptor_id)
            GROUP BY 1
        )
        SELECT receptor_id,
               CASE WHEN previos = 0 THEN 'nuevo en el dataset'
                    WHEN previos_otra = 0 THEN 'ya estaba, misma etiqueta'
                    WHEN previos_bloque = 0 THEN 'ya estaba, REETIQUETADO'
                    ELSE 'ya estaba, etiqueta mixta' END AS origen
        FROM historia
        """
    )
    print(con.sql(
        """
        SELECT c.origen, count(DISTINCT c.receptor_id) AS hcps,
               round(sum(g.usd)/1e6, 3) AS musd_2025,
               round(100.0*sum(g.usd)/sum(sum(g.usd)) OVER (), 1) AS pct_del_gasto
        FROM clasificados c
        JOIN glp1 g ON g.receptor_id = c.receptor_id
                   AND g.anio = 2025 AND g.especialidad = 'respiratorio y sueño'
        GROUP BY 1 ORDER BY musd_2025 DESC
        """
    ).df().to_string(index=False))
    print("\n      los REETIQUETADOS, ¿de qué especialidad venían?")
    print(con.sql(
        """
        SELECT g.especialidad AS venia_de, count(DISTINCT g.receptor_id) AS hcps,
               round(sum(g.usd)/1e6, 3) AS musd_previo
        FROM clasificados c
        JOIN glp1 g ON g.receptor_id = c.receptor_id
        WHERE c.origen = 'ya estaba, REETIQUETADO' AND g.anio < 2025
        GROUP BY 1 ORDER BY hcps DESC
        """
    ).df().to_string(index=False))

    print("\n  A2  ¿la taxonomía del bloque existe en los cinco años?")
    print(con.sql(
        f"""
        SELECT especialidad_cruda,
               count(DISTINCT anio) AS anios_presente,
               min(anio) AS primer_anio,
               round(sum(usd)/1e3, 0) AS musd_k
        FROM glp1 WHERE ({BLOQUE})
        GROUP BY 1 HAVING sum(usd) > 20000 ORDER BY musd_k DESC
        """
    ).df().to_string(index=False))

    r.append(("A3", *evaluar(
        "A3  sin registros disputados",
        serie(con, "record_id NOT IN (SELECT Record_ID FROM pagos "
                   "WHERE Dispute_Status_for_Publication)"))))
    r.append(("A4", *evaluar(
        "A4  pagos reales (ponderando por Number_of_Payments)",
        serie(con, usd="usd * n_pagos_agregados"))))

    # ---------------------------------------------------------------- familia B
    print("\nFAMILIA B — sensibilidad a mis decisiones\n")
    for sub, pred in (("sólo medicina del sueño", "especialidad_cruda ILIKE '%sleep%'"),
                      ("sólo neumonología", "especialidad_cruda ILIKE '%pulmonary%'"),
                      ("sólo cuidados críticos", "especialidad_cruda ILIKE '%critical care%'")):
        r.append((f"B1 {sub}", *evaluar(f"B1  D-011 alt: {sub}",
                                        serie(con, bloque=pred))))
    r.append(("B2", *evaluar(
        "B2  D-011 alt: el bloque ANTES de NP/PA (alternativa rechazada)",
        serie(con, bloque=BLOQUE))))
    r.append(("B3", *evaluar(
        "B3  D-004 alt: fila entera, sin prorratear", serie(con, usd="usd_fila"))))
    r.append(("B4", *evaluar(
        "B4  D-002 alt: sólo la entidad operativa US",
        serie(con, f"entidad_id IN ({NOVO_US}, {LILLY_US})"))))

    # ---------------------------------------------------------------- familia C
    print("\nFAMILIA C — explicaciones alternativas de negocio\n")
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW p99 AS
        SELECT grupo, anio, quantile_cont(usd, 0.99) AS corte
        FROM glp1 GROUP BY 1, 2
        """
    )
    r.append(("C1", *evaluar(
        "C1  sin el 1% de pagos más caros de cada compañía/año",
        serie(con, "usd < (SELECT corte FROM p99 p "
                   "WHERE p.grupo = glp1.grupo AND p.anio = glp1.anio)"))))
    r.append(("C2 campo", *evaluar(
        "C2  sólo contacto de campo (D-006)", serie(con, "grupo_naturaleza = 'campo'"))))
    r.append(("C2 voz", *evaluar(
        "C2b sólo el grupo voz (D-006)", serie(con, "grupo_naturaleza = 'voz'"))))

    print("\n  C3  ESCALA — el bloque contra el crecimiento total de cada compañía:")
    print(con.sql(
        """
        WITH tot AS (
            SELECT grupo,
                   sum(usd) FILTER (anio = 2025) - sum(usd) FILTER (anio = 2023) AS crec
            FROM glp1 GROUP BY 1
        ), blo AS (
            SELECT grupo,
                   sum(usd) FILTER (anio = 2025) - sum(usd) FILTER (anio = 2023) AS delta
            FROM glp1 WHERE especialidad = 'respiratorio y sueño' GROUP BY 1
        )
        SELECT b.grupo, round(b.delta/1e6, 3) AS delta_bloque_musd,
               round(t.crec/1e6, 2) AS crecimiento_total_musd,
               round(100.0*b.delta/t.crec, 1) AS pct_del_crecimiento
        FROM blo b JOIN tot t USING (grupo)
        """
    ).df().to_string(index=False))

    print("\n  C4  AMPLITUD — profesionales distintos del bloque por año y naturaleza:")
    print(con.sql(
        """
        SELECT anio,
               count(DISTINCT receptor_id) FILTER (grupo = 'lilly') AS lilly_hcps,
               count(DISTINCT receptor_id) FILTER (grupo = 'lilly'
                     AND grupo_naturaleza = 'voz') AS lilly_hcps_voz,
               count(DISTINCT receptor_id) FILTER (grupo = 'novo') AS novo_hcps
        FROM glp1 WHERE especialidad = 'respiratorio y sueño'
        GROUP BY 1 ORDER BY 1
        """
    ).df().to_string(index=False))

    print("\n  C5  PICO DE LANZAMIENTO — NO TESTEABLE con esta ventana.")
    print("      2025 es el último año disponible: un frente y un pico de")
    print("      lanzamiento son indistinguibles con un solo año de subida.")
    print("      Queda como la hipótesis viva de D-011, a resolver con PY2026.")

    corridos = [x for x in r if x[0] != "VIGENTE"]
    print(f"\nSobre {len(corridos)} tests con veredicto: "
          f"H1 sobrevive {sum(1 for x in corridos if x[1])}/{len(corridos)} · "
          f"H2 sobrevive {sum(1 for x in corridos if x[2])}/{len(corridos)}")


if __name__ == "__main__":
    main()
