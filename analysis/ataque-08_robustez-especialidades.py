"""Ataque 08 (familias A, B y C) — ¿el corte 03 sobrevive a todo lo demás?

Hallazgo bajo ataque:
  H1: Endocrinología recibe mucho más por cabeza que NP/PA (12.129 vs 293).
  H2: Lilly destina más de su gasto a endocrinología que Novo (43,6% vs 31,5%).

  A4  Los profesionales con especialidad ambigua (declarados distinto por cada
      compañía, ver ataque 07) podrían sostener H2. Test: excluirlos.
  A5  ¿La brecha vive en un solo año? Test: recalcular año por año.
  B1  D-008 alt: la regla de prioridad inversa (un NP de primaria cuenta como
      primaria, no como NP/PA). Mueve USD 18,21M.
  B2  D-004 alt: fila entera en vez de prorrateo.
  B3  D-002 alt: sólo la entidad operativa US.
  C1  ¿Es un subproducto del corte 01? Si la brecha vive sólo en los pagos que
      compran la voz del profesional, el corte 03 no agrega nada. Test: mirar
      sólo contacto de campo.
  C2  ¿Es efecto de lanzamiento? Test: sólo los productos que existían antes de
      la ventana (excluye Mounjaro, Zepbound; Wegovy sale en 2021).

Uso:  uv run analysis/ataque-08_robustez-especialidades.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

NOVO_US, LILLY_US = 100000000144, 100000000066
PREEXISTENTES = ("OZEMPIC", "RYBELSUS", "SAXENDA", "VICTOZA", "TRULICITY", "XULTOPHY 100/3.6")


def reparto(con, filtro="TRUE", usd="usd", especialidad="especialidad"):
    return con.sql(
        f"""
        SELECT {especialidad} AS esp,
               100.0*sum({usd}) FILTER (grupo = 'novo')
                   / sum(sum({usd}) FILTER (grupo = 'novo')) OVER ()  AS novo_pct,
               100.0*sum({usd}) FILTER (grupo = 'lilly')
                   / sum(sum({usd}) FILTER (grupo = 'lilly')) OVER () AS lilly_pct,
               sum({usd}) / nullif(count(DISTINCT receptor_id), 0) AS usd_por_hcp
        FROM glp1 WHERE {especialidad} IS NOT NULL AND {filtro}
        GROUP BY 1
        """
    ).df()


def evaluar(nombre: str, df) -> tuple[bool, bool]:
    try:
        endo = df[df.esp == "endocrinologia"].iloc[0]
        nppa = df[df.esp == "NP/PA"].iloc[0]
    except IndexError:
        print(f"  ??  sin datos   {nombre}")
        return False, False
    h1 = endo.usd_por_hcp > nppa.usd_por_hcp
    h2 = endo.lilly_pct > endo.novo_pct
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        endo/NP-PA por cabeza: {endo.usd_por_hcp:,.0f} vs {nppa.usd_por_hcp:,.0f} "
          f"({endo.usd_por_hcp/nppa.usd_por_hcp:.0f}x) · "
          f"endo Lilly {endo.lilly_pct:.1f}% vs Novo {endo.novo_pct:.1f}%")
    return h1, h2


def main() -> None:
    con = conectar()
    print("H1: endocrinología recibe más por cabeza que NP/PA")
    print("H2: Lilly destina más % a endocrinología que Novo\n")
    r = []

    r.append(evaluar("VIGENTE", reparto(con)))

    # A4: fuera los profesionales que las dos compañías declaran distinto.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW ambiguos AS
        SELECT receptor_id FROM glp1
        WHERE receptor_id IS NOT NULL AND especialidad IS NOT NULL
        GROUP BY 1 HAVING count(DISTINCT especialidad) > 1
        """
    )
    n_amb, usd_amb = con.sql(
        """
        SELECT count(DISTINCT g.receptor_id), sum(g.usd)/1e6
        FROM glp1 g JOIN ambiguos a USING (receptor_id)
        """
    ).fetchone()
    print(f"\n  A4 — profesionales con especialidad ambigua: {n_amb:,} "
          f"(USD {usd_amb:.2f}M, {100*usd_amb/180.18:.1f}% del gasto)")
    r.append(evaluar("A4  excluyendo ambiguos",
                     reparto(con, "receptor_id NOT IN (SELECT receptor_id FROM ambiguos)")))

    print("\n  A5 — año por año:")
    for anio in range(2021, 2026):
        r.append(evaluar(f"A5  sólo {anio}", reparto(con, f"anio = {anio}")))

    print()
    # B1: regla de prioridad inversa — la especialidad clínica manda sobre el tipo.
    inversa = """CASE
        WHEN especialidad_cruda ILIKE '%endocrin%' THEN 'endocrinologia'
        WHEN especialidad_cruda ILIKE '%obesity medicine%' THEN 'medicina de obesidad'
        WHEN especialidad_cruda LIKE '%|Family%' OR especialidad_cruda LIKE '%|Primary Care%'
          OR especialidad_cruda LIKE '%|Adult Health%'
          OR especialidad_cruda LIKE 'Allopathic%|General Practice%'
          OR especialidad_cruda = 'Allopathic & Osteopathic Physicians|Internal Medicine'
            THEN 'primaria'
        WHEN especialidad_cruda LIKE 'Physician Assistants%' THEN 'NP/PA'
        ELSE 'resto' END"""
    r.append(evaluar("B1  D-008 alt: la especialidad clínica manda sobre el tipo",
                     reparto(con, especialidad=inversa)))
    r.append(evaluar("B2  D-004 alt: fila entera, sin prorratear", reparto(con, usd="usd_fila")))
    r.append(evaluar("B3  D-002 alt: sólo entidad operativa US",
                     reparto(con, f"entidad_id IN ({NOVO_US}, {LILLY_US})")))

    print()
    r.append(evaluar("C1  sólo contacto de campo (¿es subproducto del corte 01?)",
                     reparto(con, "grupo_naturaleza = 'campo'")))
    r.append(evaluar("C1b sólo el grupo 'voz'", reparto(con, "grupo_naturaleza = 'voz'")))
    pre = "(" + ", ".join(f"'{p}'" for p in PREEXISTENTES) + ")"
    r.append(evaluar("C2  sólo productos previos a la ventana", reparto(con, f"producto IN {pre}")))

    alt = r[1:]
    print(f"\nSobre {len(alt)} tests: H1 sobrevive {sum(h1 for h1, _ in alt)}/{len(alt)} · "
          f"H2 sobrevive {sum(h2 for _, h2 in alt)}/{len(alt)}")


if __name__ == "__main__":
    main()
