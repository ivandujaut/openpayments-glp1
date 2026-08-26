"""Ataque 10 (familias B y C) — ¿el corte 04 sobrevive a decisiones y a escala?

Hallazgo bajo ataque:
  H1: entre el pivote y 2025, Lilly REDUJO su gasto en endocrinología y Novo lo
      aumentó.
  H2: Novo destina mucho más que Lilly al grupo emergente.

  B1  D-009 alt: ¿y si el bloque emergente fuera sólo cardiología, o las tres
      especialidades por separado?
  B2  D-004 alt: fila entera en vez de prorrateo.
  B3  D-002 alt: sólo la entidad operativa US.
  C1  ESCALA. El gasto total de Novo creció más que el de Lilly en el período,
      así que "Novo creció en todo" podría ser aritmética. Test: normalizar cada
      delta por el crecimiento total de su compañía.
  C2  PIVOTE. 2023 es una elección del corte (el pico de divergencia). Test:
      repetir con 2021, 2022 y 2024 como año base.
  C3  ¿Es "voz" otra vez? Los cortes 02 y 03 encontraron que la diferencia entre
      compañías vive en los pagos de disertante. Test: sólo contacto de campo.

Uso:  uv run analysis/ataque-10_robustez-convergencia.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

NOVO_US, LILLY_US = 100000000144, 100000000066
EMERGENTES_SQL = ("especialidad_cruda ILIKE '%cardio%' OR especialidad_cruda ILIKE '%nephro%' "
                  "OR especialidad_cruda ILIKE '%gastroenter%' OR especialidad_cruda ILIKE '%hepatol%'")


def deltas(con, pivote=2023, filtro="TRUE", usd="usd", esp="especialidad"):
    return con.sql(
        f"""
        SELECT grupo, {esp} AS esp,
               sum({usd}) FILTER (anio = {pivote}) AS ini,
               sum({usd}) FILTER (anio = 2025)     AS fin,
               sum({usd}) FILTER (anio = 2025) - sum({usd}) FILTER (anio = {pivote}) AS delta
        FROM glp1 WHERE {esp} IS NOT NULL AND {filtro}
        GROUP BY 1, 2
        """
    ).df()


def evaluar(nombre, df, col_emergente="emergentes"):
    def get(g, e, c="delta"):
        sub = df[(df.grupo == g) & (df.esp == e)]
        return float(sub.iloc[0][c]) if len(sub) else 0.0

    h1 = get("lilly", "endocrinologia") < 0 < get("novo", "endocrinologia")
    novo_em, lilly_em = get("novo", col_emergente, "fin"), get("lilly", col_emergente, "fin")
    h2 = novo_em > lilly_em
    print(f"  {'✓' if h1 else '✗'} H1  {'✓' if h2 else '✗'} H2   {nombre}")
    print(f"        Δendo: Lilly {get('lilly','endocrinologia')/1e6:+.2f}M · "
          f"Novo {get('novo','endocrinologia')/1e6:+.2f}M · "
          f"emergente 2025: Novo {novo_em/1e6:.2f}M vs Lilly {lilly_em/1e6:.2f}M")
    return h1, h2


def main() -> None:
    con = conectar()
    print("H1: Lilly reduce endocrinología, Novo la aumenta")
    print("H2: Novo destina más que Lilly al grupo emergente\n")
    r = []

    r.append(evaluar("VIGENTE (pivote 2023)", deltas(con)))

    print("\n  B1 — D-009 alt: otras particiones del bloque emergente")
    solo_cardio = ("CASE WHEN especialidad_cruda ILIKE '%cardio%' THEN 'emergentes' "
                   "ELSE especialidad END")
    r.append(evaluar("B1  sólo cardiología como bloque", deltas(con, esp=solo_cardio)))
    for nombre, patron in (("cardiología", "%cardio%"), ("nefrología", "%nephro%"),
                           ("gastro/hepato", "%gastroenter%")):
        esp = f"CASE WHEN especialidad_cruda ILIKE '{patron}' THEN 'emergentes' ELSE especialidad END"
        r.append(evaluar(f"B1  sólo {nombre} por separado", deltas(con, esp=esp)))

    print()
    r.append(evaluar("B2  D-004 alt: fila entera", deltas(con, usd="usd_fila")))
    r.append(evaluar("B3  D-002 alt: sólo entidad operativa US",
                     deltas(con, filtro=f"entidad_id IN ({NOVO_US}, {LILLY_US})")))

    print("\n  C1 — ESCALA: los deltas normalizados por el crecimiento total de cada compañía")
    print(con.sql(
        """
        WITH tot AS (
            SELECT grupo,
                   sum(usd) FILTER (anio = 2023) AS ini,
                   sum(usd) FILTER (anio = 2025) AS fin
            FROM glp1 GROUP BY 1
        ),
        porcat AS (
            SELECT grupo, especialidad,
                   sum(usd) FILTER (anio = 2025) - sum(usd) FILTER (anio = 2023) AS delta
            FROM glp1 WHERE especialidad IS NOT NULL GROUP BY 1, 2
        )
        SELECT p.grupo, p.especialidad,
               round(p.delta/1e6, 2) AS delta_musd,
               round(100.0*p.delta/(t.fin - t.ini), 1) AS pct_del_crecimiento
        FROM porcat p JOIN tot t USING (grupo)
        ORDER BY p.grupo, pct_del_crecimiento DESC
        """
    ).df().to_string(index=False))

    print("\n  C2 — PIVOTE: repetir con otros años base")
    for pivote in (2021, 2022, 2024):
        r.append(evaluar(f"C2  pivote {pivote}", deltas(con, pivote=pivote)))

    print()
    r.append(evaluar("C3  sólo contacto de campo",
                     deltas(con, filtro="grupo_naturaleza = 'campo'")))
    r.append(evaluar("C3b sólo el grupo 'voz'",
                     deltas(con, filtro="grupo_naturaleza = 'voz'")))

    alt = r[1:]
    print(f"\nSobre {len(alt)} tests: H1 sobrevive {sum(h1 for h1, _ in alt)}/{len(alt)} · "
          f"H2 sobrevive {sum(h2 for _, h2 in alt)}/{len(alt)}")


if __name__ == "__main__":
    main()
