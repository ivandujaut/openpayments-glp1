"""Verifica que cada número publicado en findings/ salga del cache vigente.

Por qué existe: los findings se editan cuando un ataque cambia un hallazgo o
cuando se reabre una decisión. Ya pasó una vez — D-009 dejó desactualizada la
tabla del corte 03 — y nada garantiza que no vuelva a pasar. Este script fija
las cifras que los findings citan y las compara contra findings/cache/*.json.

No reemplaza a 04_checks.py: aquel cierra el dato propio contra CMS; éste cierra
el texto publicado contra el dato propio. Son los dos extremos de la cadena.

Cada aserción declara: corte, qué cifra, el valor que dice el finding, y cómo se
recalcula desde el cache. Si el finding cambia un número sin que cambie el
cache (o al revés), acá salta.

Uso:  uv run scripts/05_verificar_findings.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache"
FINDINGS = ROOT / "findings"
# Un finding que dice "0,45M" no afirma 450.000 exactos: afirma 445.000–455.000.
# Comparar eso con una tolerancia porcentual da falsos positivos justo en las
# cifras chicas. Cada aserción declara la PRECISIÓN con que el finding cita el
# número, y se compara contra media unidad de ese último dígito.
PREC_MILLON_2DEC = 5_000    # el finding cita "X,XXM"
PREC_CENTAVO = 0.005        # el finding cita el número completo
PREC_ENTERO = 0.5           # el finding cita un entero exacto
PREC_1DEC = 0.05            # el finding cita "XX,X%" o "XXX,X"
PREC_4DEC = 0.00005         # gini


def cargar(nombre: str) -> dict:
    ruta = CACHE / f"{nombre}.json"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Correr los cortes de analysis/ primero.")
    return json.loads(ruta.read_text())


def buscar(filas, **claves):
    """Primera fila del cache que matchea todas las claves."""
    for f in filas:
        if all(f.get(k) == v for k, v in claves.items()):
            return f
    raise KeyError(f"sin fila para {claves}")


def aserciones() -> list[tuple[str, str, float, float, float]]:
    """(corte, etiqueta, valor citado, valor del cache, precisión de la cita)."""
    a = []

    # ---------- corte 01 ----------
    c1 = cargar("corte-01_carrera")
    t = c1["totales"]
    a += [
        ("01", "Novo total USD", 111_050_245.29, t["novo_usd"], PREC_CENTAVO),
        ("01", "Lilly total USD", 69_132_487.30, t["lilly_usd"], PREC_CENTAVO),
        ("01", "Novo pagos", 2_212_503, t["novo_pagos"], PREC_ENTERO),
        ("01", "Lilly pagos", 1_165_279, t["lilly_pagos"], PREC_ENTERO),
    ]
    s21 = buscar(c1["serie"], anio=2021)
    s25 = buscar(c1["serie"], anio=2025)
    a += [
        ("01", "Novo USD 2021", 24_606_070, s21["novo_usd"], PREC_ENTERO),
        ("01", "Lilly USD 2021", 5_954_237, s21["lilly_usd"], PREC_ENTERO),
        ("01", "Novo USD 2025", 28_897_541, s25["novo_usd"], PREC_ENTERO),
        ("01", "Lilly USD 2025", 19_303_449, s25["lilly_usd"], PREC_ENTERO),
        ("01", "Novo HCPs 2025", 114_861, s25["novo_hcp"], PREC_ENTERO),
        ("01", "Lilly HCPs 2025", 79_526, s25["lilly_hcp"], PREC_ENTERO),
    ]
    v21 = buscar(c1["voz_vs_campo"], anio=2021)
    v25 = buscar(c1["voz_vs_campo"], anio=2025)
    a += [
        ("01", "pagos voz Lilly 2021", 6_521, v21["lilly_voz_n"], PREC_ENTERO),
        ("01", "pagos voz Lilly 2025", 12_604, v25["lilly_voz_n"], PREC_ENTERO),
        ("01", "pagos voz Novo 2021", 7_361, v21["novo_voz_n"], PREC_ENTERO),
        ("01", "pagos voz Novo 2025", 5_201, v25["novo_voz_n"], PREC_ENTERO),
    ]
    # Los cinco años, no sólo los extremos: esta tabla ya se desactualizó una vez
    # entera (cuando D-006 movió consultoría de campo a voz) y el verificador
    # sólo miraba 2025.
    tabla_voz_campo = {
        2021: (15.19, 4.57, 9.41, 1.38),
        2022: (17.69, 8.66, 11.16, 3.37),
        2023: (5.48, 8.79, 7.64, 5.17),
        2024: (6.86, 11.98, 8.71, 5.90),
        2025: (16.51, 14.42, 12.39, 4.88),
    }
    for anio, (nv, lv, nc, lc) in tabla_voz_campo.items():
        f = buscar(c1["voz_vs_campo"], anio=anio)
        a += [
            ("01", f"voz Novo {anio}", nv * 1e6, f["novo_voz"], PREC_MILLON_2DEC),
            ("01", f"voz Lilly {anio}", lv * 1e6, f["lilly_voz"], PREC_MILLON_2DEC),
            ("01", f"campo Novo {anio}", nc * 1e6, f["novo_campo"], PREC_MILLON_2DEC),
            ("01", f"campo Lilly {anio}", lc * 1e6, f["lilly_campo"], PREC_MILLON_2DEC),
        ]

    # Nota de sensibilidad al deflactor (D-010): el punto de quiebre publicado
    # tiene que seguir siendo el que sale del dato.
    a += [
        ("01", "crecimiento nominal Novo 21→25 (%)", 17.4,
         100 * (s25["novo_usd"] / s21["novo_usd"] - 1), PREC_1DEC),
        ("01", "deflactor de quiebre Novo", 1.174,
         s25["novo_usd"] / s21["novo_usd"], 0.0005),
        ("01", "crecimiento nominal Lilly 21→25 (%)", 224.2,
         100 * (s25["lilly_usd"] / s21["lilly_usd"] - 1), PREC_1DEC),
        ("01", "deflactor de quiebre Lilly", 3.242,
         s25["lilly_usd"] / s21["lilly_usd"], 0.0005),
    ]

    # ---------- corte 02 ----------
    c2 = cargar("corte-02_concentracion")
    cl = buscar(c2["concentracion"], grupo="lilly")
    cn = buscar(c2["concentracion"], grupo="novo")
    a += [
        ("02", "red Lilly", 152_493, cl["red_hcps"], PREC_ENTERO),
        ("02", "red Novo", 209_450, cn["red_hcps"], PREC_ENTERO),
        ("02", "top100 Lilly", 35.64, cl["top100"], PREC_MILLON_2DEC*0+0.005),
        ("02", "top100 Novo", 20.44, cn["top100"], PREC_MILLON_2DEC*0+0.005),
        ("02", "gini Lilly", 0.8846, cl["gini"], PREC_4DEC),
        ("02", "gini Novo", 0.8549, cn["gini"], PREC_4DEC),
        ("02", "mediana Lilly", 60.55, cl["mediana_hcp"], PREC_CENTAVO),
        ("02", "mediana Novo", 94.37, cn["mediana_hcp"], PREC_CENTAVO),
        ("02", "mayor Lilly", 403_511.38, cl["mayor_hcp"], PREC_CENTAVO),
        ("02", "mayor Novo", 358_682.84, cn["mayor_hcp"], PREC_CENTAVO),
        ("02", "Novo total USD (sin hosp.)", 110.97e6, cn["musd"] * 1e6, PREC_MILLON_2DEC),
    ]
    pl = buscar(c2["perfil_top100"], grupo="lilly")
    pn = buscar(c2["perfil_top100"], grupo="novo")
    a += [
        ("02", "top100 Lilly promedio", 246_402, pl["usd_promedio"], PREC_ENTERO),
        ("02", "top100 Novo promedio", 226_796, pn["usd_promedio"], PREC_ENTERO),
        ("02", "umbral top100 Lilly", 172_608, pl["usd_minimo"], PREC_ENTERO),
        ("02", "umbral top100 Novo", 172_768, pn["usd_minimo"], PREC_ENTERO),
        ("02", "pagos top100 Lilly", 431.3, pl["pagos_promedio"], PREC_1DEC),
        ("02", "pagos top100 Novo", 246.4, pn["pagos_promedio"], PREC_1DEC),
    ]
    vl = buscar(c2["por_naturaleza"], grupo_naturaleza="voz", grupo="lilly")
    vn = buscar(c2["por_naturaleza"], grupo_naturaleza="voz", grupo="novo")
    kl = buscar(c2["por_naturaleza"], grupo_naturaleza="campo", grupo="lilly")
    kn = buscar(c2["por_naturaleza"], grupo_naturaleza="campo", grupo="novo")
    a += [
        ("02", "círculo voz Lilly", 657, vl["red_hcps"], PREC_ENTERO),
        ("02", "círculo voz Novo", 1_139, vn["red_hcps"], PREC_ENTERO),
        ("02", "USD voz Lilly", 48.42e6, vl["usd"], PREC_MILLON_2DEC),
        ("02", "USD voz Novo", 61.73e6, vn["usd"], PREC_MILLON_2DEC),
        ("02", "USD/HCP voz Lilly", 73_700, vl["usd_por_hcp"], PREC_ENTERO),
        ("02", "USD/HCP voz Novo", 54_193, vn["usd_por_hcp"], PREC_ENTERO),
        ("02", "top100 voz Lilly", 49.06, vl["top100"], 0.005),
        ("02", "top100 voz Novo", 32.11, vn["top100"], 0.005),
        ("02", "top100 campo Lilly", 4.77, kl["top100"], 0.005),
        ("02", "top100 campo Novo", 6.72, kn["top100"], 0.005),
        ("02", "USD campo Lilly", 20.71e6, kl["usd"], PREC_MILLON_2DEC),
        ("02", "USD campo Novo", 49.25e6, kn["usd"], PREC_MILLON_2DEC),
    ]

    # ---------- corte 03 ----------
    c3 = cargar("corte-03_especialidades")
    endo = buscar(c3["reparto"], especialidad="endocrinologia")
    nppa = buscar(c3["reparto"], especialidad="NP/PA")
    emer = buscar(c3["reparto"], especialidad="emergentes")
    prim = buscar(c3["reparto"], especialidad="primaria")
    rest = buscar(c3["reparto"], especialidad="resto")
    a += [
        ("03", "endo HCPs", 5_367, endo["hcps"], PREC_ENTERO),
        ("03", "endo USD/HCP", 12_129, endo["usd_por_hcp"], PREC_ENTERO),
        ("03", "endo USD total", 65.10e6, endo["novo_usd"] + endo["lilly_usd"], PREC_MILLON_2DEC),
        ("03", "endo % Lilly", 43.6, endo["lilly_pct"], PREC_1DEC),
        ("03", "endo % Novo", 31.5, endo["novo_pct"], PREC_1DEC),
        ("03", "NP/PA HCPs", 120_145, nppa["hcps"], PREC_ENTERO),
        ("03", "NP/PA USD/HCP", 293, nppa["usd_por_hcp"], PREC_ENTERO),
        ("03", "NP/PA USD total", 35.25e6, nppa["novo_usd"] + nppa["lilly_usd"], PREC_MILLON_2DEC),
        ("03", "emergentes Novo USD", 14.74e6, emer["novo_usd"], PREC_MILLON_2DEC),
        ("03", "emergentes Lilly USD", 1.46e6, emer["lilly_usd"], PREC_MILLON_2DEC),
        ("03", "emergentes HCPs", 16_714, emer["hcps"], PREC_ENTERO),
        ("03", "primaria HCPs", 82_994, prim["hcps"], PREC_ENTERO),
        ("03", "resto HCPs", 28_227, rest["hcps"], PREC_ENTERO),
    ]
    for anio, lilly_pct, novo_pct in ((2021, 51.1, 43.1), (2023, 51.6, 21.6), (2025, 27.8, 24.5)):
        f = buscar(c3["serie"], anio=anio, especialidad="endocrinologia")
        a += [
            ("03", f"endo % Lilly {anio}", lilly_pct, f["lilly_pct"], PREC_1DEC),
            ("03", f"endo % Novo {anio}", novo_pct, f["novo_pct"], PREC_1DEC),
        ]

    # ---------- corte 04 ----------
    c4 = cargar("corte-04_convergencia")
    m = c4["movimiento"]
    a += [
        ("04", "Δ endo Lilly", -1.85e6, buscar(m, grupo="lilly", especialidad="endocrinologia")["delta"], PREC_MILLON_2DEC),
        ("04", "Δ endo Novo", 4.25e6, buscar(m, grupo="novo", especialidad="endocrinologia")["delta"], PREC_MILLON_2DEC),
        ("04", "Δ primaria Lilly", 3.59e6, buscar(m, grupo="lilly", especialidad="primaria")["delta"], PREC_MILLON_2DEC),
        ("04", "Δ emergentes Novo", 6.43e6, buscar(m, grupo="novo", especialidad="emergentes")["delta"], PREC_MILLON_2DEC),
        ("04", "emergentes Novo 2025", 7.39e6, buscar(m, grupo="novo", especialidad="emergentes")["usd_final"], PREC_MILLON_2DEC),
        ("04", "emergentes Lilly 2025", 0.45e6, buscar(m, grupo="lilly", especialidad="emergentes")["usd_final"], PREC_MILLON_2DEC),
        ("04", "emergentes Novo 2023", 0.96e6, buscar(m, grupo="novo", especialidad="emergentes")["usd_pivote"], PREC_MILLON_2DEC),
    ]
    wegovy = buscar(c4["emergentes_por_producto"], producto="WEGOVY")
    ozempic = buscar(c4["emergentes_por_producto"], producto="OZEMPIC")
    a += [
        ("04", "Wegovy emergentes 2023", 0.15e6, wegovy["usd_2023"], PREC_MILLON_2DEC),
        ("04", "Wegovy emergentes 2025", 4.35e6, wegovy["usd_2025"], PREC_MILLON_2DEC),
        ("04", "Ozempic emergentes 2023", 0.75e6, ozempic["usd_2023"], PREC_MILLON_2DEC),
        ("04", "Ozempic emergentes 2025", 2.87e6, ozempic["usd_2025"], PREC_MILLON_2DEC),
    ]
    return a


def coherencia_entre_findings() -> list[str]:
    """Contradicciones que ningún cache detecta porque cruzan cortes."""
    avisos = []
    c1, c2, c3 = (cargar(n) for n in ("corte-01_carrera", "corte-02_concentracion",
                                      "corte-03_especialidades"))

    # El corte 02 excluye hospitales docentes (sin Profile_ID); el 01 no. La
    # diferencia tiene que ser exactamente eso y el finding 02 la declara.
    novo_01 = c1["totales"]["novo_usd"]
    novo_02 = buscar(c2["concentracion"], grupo="novo")["musd"] * 1e6
    delta = novo_01 - novo_02
    if not 60_000 < delta < 90_000:
        avisos.append(f"corte 01 vs 02: Novo difiere en USD {delta:,.0f}; "
                      "el finding 02 lo atribuye a hospitales docentes (~75.300)")

    # El total por especialidad (corte 03) debe cerrar contra el total del 01
    # salvo por los pagos sin especialidad.
    for grupo, total in (("novo", c1["totales"]["novo_usd"]),
                         ("lilly", c1["totales"]["lilly_usd"])):
        suma = sum(f[f"{grupo}_usd"] or 0 for f in c3["reparto"])
        if abs(suma - total) / total > 0.01:
            avisos.append(f"corte 03 vs 01: {grupo} suma {suma:,.0f} por especialidad "
                          f"contra {total:,.0f} del total ({100*(suma-total)/total:+.2f}%)")
    return avisos


def findings_citan_decisiones_vigentes() -> list[str]:
    """Un finding no debería citar una decisión superada sin decir que lo está."""
    avisos = []
    texto = (ROOT / "decisions.md").read_text()
    # Partir por entrada: un .*? que cruce bloques marca como superada la
    # primera decisión del archivo en vez de la que corresponde.
    bloques = re.split(r"\n## (?=D-\d+)", texto)
    superadas = set()
    for b in bloques:
        m = re.match(r"(D-\d+)", b)
        if m and re.search(r"- \*\*Estado:\*\* \*\*superada", b):
            superadas.add(m.group(1))
    for f in sorted(FINDINGS.glob("corte-0[1-9]_*.md")):
        t = f.read_text()
        for d in superadas:
            aclarado = any(w in t for w in ("reabr", "reabierta", "superada"))
            if d in t and not aclarado:
                avisos.append(f"{f.name} cita {d}, que está superada, sin aclararlo")
    return avisos


def main() -> None:
    filas = aserciones()
    rojo = 0
    print(f"{'corte':<7}{'cifra':<32}{'finding':>18}{'cache':>18}{'|Δ|':>14}")
    for corte, etiqueta, citado, real, prec in filas:
        real = float(real or 0)
        # El finding cita con una precisión declarada; sólo es error si la
        # diferencia supera media unidad de ese último dígito.
        fuera = abs(citado - real) > prec
        rojo += fuera
        print(f"{corte:<7}{etiqueta:<32}{citado:>18,.2f}{real:>18,.2f}"
              f"{abs(citado-real):>14,.2f}{'  ← ROJO' if fuera else ''}")

    print(f"\n{len(filas)} cifras verificadas · {rojo} discrepancias")

    for titulo, avisos in (("Coherencia entre cortes", coherencia_entre_findings()),
                           ("Decisiones citadas", findings_citan_decisiones_vigentes())):
        print(f"\n{titulo}: ", end="")
        print("sin observaciones" if not avisos else "")
        for a in avisos:
            print(f"  ⚠ {a}")
        rojo += len(avisos)

    print("\nEstado:", "🔴 hay findings desalineados" if rojo else "🟢 verde")
    sys.exit(1 if rojo else 0)


if __name__ == "__main__":
    main()
