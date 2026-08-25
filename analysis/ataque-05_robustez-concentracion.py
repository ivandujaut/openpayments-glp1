"""Ataque 05 (familias A y B) — ¿la concentración es artefacto o elección mía?

Hallazgo bajo ataque:
  H1: Lilly concentra más que Novo (top 100: 35,6% vs 20,4%).
  H2: El top 100 de Lilly acumula ~431 pagos promedio contra ~246 de Novo.

Familia A — artefactos del dato:
  A2  Todo el corte es acumulado 2021–2025. Si la brecha vive en un solo año,
      el hallazgo es otro. Test: recalcular año por año.
  A3  Los 431 vs 246 pagos cuentan FILAS; una fila puede agregar varios pagos.
      Test: ponderar por Number_of_Payments_Included_in_Total_Amount.
  A4  La ruptura NPP: si Lilly y Novo usan NP/PA en proporciones distintas, la
      concentración podría venir de ahí. Test: sólo médicos.

Familia B — sensibilidad a decisiones:
  B1  D-002: ¿sobrevive con sólo la entidad operativa US?
  B2  D-004: ¿sobrevive contando la fila entera en vez de prorratear?
  B3  D-007: ¿sobrevive con las métricas rechazadas (top 1% y Gini)?

Uso:  uv run analysis/ataque-05_robustez-concentracion.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

NOVO_US, LILLY_US = 100000000144, 100000000066


def concentracion(con, filtro="TRUE", usd="usd", pagos="count(DISTINCT record_id)"):
    """% al top 100 y pagos promedio del top 100, por compañía."""
    return con.sql(
        f"""
        WITH x AS (SELECT grupo, receptor_id, sum({usd}) AS usd, {pagos} AS pagos
                   FROM glp1 WHERE receptor_id IS NOT NULL AND {filtro}
                   GROUP BY 1, 2),
             r AS (SELECT *, row_number() OVER (PARTITION BY grupo ORDER BY usd DESC) rn,
                          sum(usd) OVER (PARTITION BY grupo) total FROM x)
        SELECT grupo,
               round(100.0*sum(usd) FILTER (rn <= 100)/any_value(total), 2) AS top100,
               round(avg(pagos) FILTER (rn <= 100), 1) AS pagos_top100
        FROM r GROUP BY grupo ORDER BY grupo
        """
    ).df()


def evaluar(nombre: str, df) -> tuple[bool, bool]:
    try:
        l = df[df.grupo == "lilly"].iloc[0]
        n = df[df.grupo == "novo"].iloc[0]
    except IndexError:
        print(f"  ??  sin datos   {nombre}")
        return False, False
    h1, h2 = l.top100 > n.top100, l.pagos_top100 > n.pagos_top100
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        top100 L={l.top100:.2f} N={n.top100:.2f} ({l.top100/n.top100:.2f}x) · "
          f"pagos L={l.pagos_top100:.0f} N={n.pagos_top100:.0f}")
    return h1, h2


def main() -> None:
    con = conectar()
    print("H1: Lilly concentra más que Novo (% al top 100)")
    print("H2: El top 100 de Lilly acumula más pagos que el de Novo\n")
    r = []

    r.append(evaluar("VIGENTE", concentracion(con)))

    print("\n  A2 — año por año (el corte publica el acumulado):")
    for anio in range(2021, 2026):
        r.append(evaluar(f"A2  sólo {anio}", concentracion(con, f"anio = {anio}")))

    print()
    r.append(evaluar("A3  pagos ponderados por Number_of_Payments",
                     concentracion(con, pagos="sum(n_pagos_agregados)")))
    r.append(evaluar("A4  sólo médicos (excluye NP/PA)",
                     concentracion(con, "tipo_receptor = 'Covered Recipient Physician'")))
    r.append(evaluar("B1  D-002 alt: sólo entidad operativa US",
                     concentracion(con, f"entidad_id IN ({NOVO_US}, {LILLY_US})")))
    r.append(evaluar("B2  D-004 alt: fila entera, sin prorratear",
                     concentracion(con, usd="usd_fila")))

    print("\n  B3 — D-007 alt: las métricas que la decisión rechazó")
    df = con.sql(
        """
        WITH x AS (SELECT grupo, receptor_id, sum(usd) AS usd FROM glp1
                   WHERE receptor_id IS NOT NULL GROUP BY 1, 2),
             r AS (SELECT *, row_number() OVER (PARTITION BY grupo ORDER BY usd DESC) rn,
                          row_number() OVER (PARTITION BY grupo ORDER BY usd) rn_asc,
                          count(*) OVER (PARTITION BY grupo) n,
                          sum(usd) OVER (PARTITION BY grupo) total FROM x)
        SELECT grupo,
               round(100.0*sum(usd) FILTER (rn <= n*0.01)/any_value(total), 2) AS top1pct,
               round(2.0*sum(rn_asc*usd)/(any_value(n)*any_value(total))
                     - (any_value(n)+1.0)/any_value(n), 4) AS gini
        FROM r GROUP BY grupo ORDER BY grupo
        """
    ).df()
    print(df.to_string(index=False))
    l, n = df[df.grupo == "lilly"].iloc[0], df[df.grupo == "novo"].iloc[0]
    b3 = l.top1pct > n.top1pct and l.gini > n.gini
    print(f"    {'✓' if b3 else '✗'} las dos métricas rechazadas ordenan igual "
          f"(top1%: {l.top1pct:.2f} vs {n.top1pct:.2f} · gini: {l.gini:.4f} vs {n.gini:.4f})")
    r.append((b3, b3))

    alt = r[1:]  # r[0] es la corrida vigente, no un ataque
    print(f"\nSobre {len(alt)} tests: H1 sobrevive {sum(h1 for h1, _ in alt)}/{len(alt)} · "
          f"H2 sobrevive {sum(h2 for _, h2 in alt)}/{len(alt)}")


if __name__ == "__main__":
    main()
