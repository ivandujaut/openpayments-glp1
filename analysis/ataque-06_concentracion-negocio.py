"""Ataque 06 (familia C) — ¿otro mecanismo explica la concentración de Lilly?

Hallazgo bajo ataque:
  H1: Lilly concentra más que Novo (top 100: 35,6% vs 20,4%).
  H2: El top 100 de Lilly acumula ~431 pagos promedio contra ~246 de Novo.

  C1  TAMAÑO DE RED. Novo llega a 209.450 profesionales y Lilly a 152.493. Con
      una cola larga de gente que sólo recibió una comida, el denominador de
      Novo se infla y su top 100 pesa menos por construcción. Test: recortar las
      dos redes al mismo tamaño (los N mejores pagos de cada una) y recalcular.
  C2  MIX DE LANZAMIENTOS. Mounjaro (2022) y Zepbound (2023) se lanzaron dentro
      de la ventana; un lanzamiento concentra gasto en pocos líderes de opinión.
      Si al excluir los productos lanzados en la ventana la brecha desaparece,
      el hallazgo es sobre lanzamientos, no sobre estrategia.
  C3  ES SÓLO "VOZ". El 96,4% del gasto del top 100 de Lilly es del grupo voz
      (D-006). Si al mirar sólo el contacto de campo la brecha desaparece, el
      hallazgo ya está contado por el corte 01 y este corte no agrega nada.

Uso:  uv run analysis/ataque-06_concentracion-negocio.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

# Productos lanzados dentro de la ventana 2021–2025 (C2).
LANZADOS_EN_VENTANA = ("MOUNJARO", "ZEPBOUND", "WEGOVY")


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


def concentracion(con, filtro="TRUE", recorte_red: int | None = None):
    """% al top 100. Con recorte_red, ambas redes se truncan a ese tamaño."""
    corte = f"WHERE rn_red <= {recorte_red}" if recorte_red else ""
    return con.sql(
        f"""
        WITH x AS (SELECT grupo, receptor_id, sum(usd) AS usd,
                          count(DISTINCT record_id) AS pagos
                   FROM glp1 WHERE receptor_id IS NOT NULL AND {filtro}
                   GROUP BY 1, 2),
             red AS (SELECT *, row_number() OVER (PARTITION BY grupo ORDER BY usd DESC) rn_red
                     FROM x),
             recortada AS (SELECT * FROM red {corte}),
             r AS (SELECT *, row_number() OVER (PARTITION BY grupo ORDER BY usd DESC) rn,
                          sum(usd) OVER (PARTITION BY grupo) total FROM recortada)
        SELECT grupo,
               round(100.0*sum(usd) FILTER (rn <= 100)/any_value(total), 2) AS top100,
               round(avg(pagos) FILTER (rn <= 100), 1) AS pagos_top100
        FROM r GROUP BY grupo ORDER BY grupo
        """
    ).df()


def main() -> None:
    con = conectar()
    print("H1: Lilly concentra más que Novo (% al top 100)")
    print("H2: El top 100 de Lilly acumula más pagos que el de Novo\n")
    r = []

    r.append(evaluar("VIGENTE", concentracion(con)))

    print("\n  C1 — redes recortadas al mismo tamaño:")
    for n_red in (1_000, 10_000, 50_000, 152_493):
        r.append(evaluar(f"C1  las {n_red:,} mejor pagas de cada compañía",
                         concentracion(con, recorte_red=n_red)))

    print()
    lanzados = "(" + ", ".join(f"'{p}'" for p in LANZADOS_EN_VENTANA) + ")"
    r.append(evaluar("C2  sin productos lanzados en la ventana (Mounjaro, Zepbound, Wegovy)",
                     concentracion(con, f"producto NOT IN {lanzados}")))
    r.append(evaluar("C3  sólo contacto de campo (excluye el grupo 'voz')",
                     concentracion(con, "grupo_naturaleza = 'campo'")))
    r.append(evaluar("C3b sólo el grupo 'voz'",
                     concentracion(con, "grupo_naturaleza = 'voz'")))

    alt = r[1:]
    print(f"\nSobre {len(alt)} tests: H1 sobrevive {sum(h1 for h1, _ in alt)}/{len(alt)} · "
          f"H2 sobrevive {sum(h2 for _, h2 in alt)}/{len(alt)}")


if __name__ == "__main__":
    main()
