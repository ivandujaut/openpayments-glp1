"""g1 — la carrera Novo vs. Lilly, en las dos unidades que se contradicen.

Lee SOLO findings/cache/corte-01_carrera.json. Si falta un número, se amplía el
corte (analysis/corte-01_carrera.py), nunca se consulta el parquet desde acá.

Exporta las dos versiones desde el mismo script: g1_carrera.png (es) y
g1_carrera.en.png (en). Un solo lugar donde cambiar el diseño.

Uso:  uv run charts/g1_carrera.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, FG, guardar, miles, nueva_figura_apilada  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-01_carrera.json"

TEXTOS = {
    "es": {
        "titulo": "En dólares Lilly pasó al frente en 2023 y 2024. En cantidad de pagos, nunca.",
        "subtitulo": ("Pagos de Novo Nordisk y Eli Lilly a profesionales de la salud por productos GLP-1, "
                      "2021–2025 · CMS Open Payments (General Payments)"),
        "panel_usd": "Millones de USD",
        "panel_pagos": "Cantidad de pagos (miles)",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "nota": "Zona sombreada: años en que cada unidad da un ganador distinto.",
        "archivo": "g1_carrera",
    },
    "en": {
        "titulo": "In dollars, Lilly led in 2023 and 2024. In number of payments, never.",
        "subtitulo": ("Novo Nordisk and Eli Lilly payments to healthcare professionals for GLP-1 products, "
                      "2021–2025 · CMS Open Payments (General Payments)"),
        "panel_usd": "USD millions",
        "panel_pagos": "Number of payments (thousands)",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "nota": "Shaded band: years where each unit yields a different winner.",
        "archivo": "g1_carrera.en",
    },
}


def numero(valor: float, decimales: int, locale: str) -> str:
    """Formato numérico por locale: 1.234,5 en es · 1,234.5 en en."""
    if decimales == 0:
        return miles(valor, locale)
    entero, _, fraccion = f"{valor:,.{decimales}f}".partition(".")
    coma, punto = (".", ",") if locale == "es" else (",", ".")
    return entero.replace(",", coma) + punto + fraccion


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    serie = datos["serie"]
    anios = [int(f["anio"]) for f in serie]
    invertidos = [r["anio"] for r in datos["ratios"]
                  if (r["usd"] > 1) != (r["pagos"] > 1)]

    fig, (ax_usd, ax_pag) = nueva_figura_apilada(t["titulo"], t["subtitulo"], n=2)

    paneles = (
        (ax_usd, t["panel_usd"], [f["novo_usd"] / 1e6 for f in serie],
         [f["lilly_usd"] / 1e6 for f in serie], 1),
        (ax_pag, t["panel_pagos"], [f["novo_pagos"] / 1e3 for f in serie],
         [f["lilly_pagos"] / 1e3 for f in serie], 0),
    )
    for ax, etiqueta, novo, lilly, decimales in paneles:
        # La banda va primero: queda detrás de las líneas.
        for a in invertidos:
            ax.axvspan(a - 0.5, a + 0.5, color=GRAY, alpha=0.13, lw=0)
        for valores, clave, nombre in ((novo, "novo", t["novo"]), (lilly, "lilly", t["lilly"])):
            ax.plot(anios, valores, color=SERIE[clave], lw=2.6, marker="o",
                    ms=5.5, label=nombre, zorder=3)
        ax.set_ylabel(etiqueta, fontsize=10.5, color=GRAY)
        ax.set_xticks(anios)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color=GRAY, alpha=0.18, lw=0.8)
        ax.set_axisbelow(True)
        # Etiqueta de valor en el último punto de cada serie.
        for valores, clave in ((novo, "novo"), (lilly, "lilly")):
            ax.annotate(numero(valores[-1], decimales, locale),
                        (anios[-1], valores[-1]), textcoords="offset points",
                        xytext=(9, -3), fontsize=10.5, color=SERIE[clave],
                        fontweight="bold")

    ax_usd.legend(frameon=False, loc="upper center", ncol=2, fontsize=11,
                  bbox_to_anchor=(0.5, 1.22))
    fig.text(0.08, 0.035, t["nota"], fontsize=9.5, color=GRAY, ha="left")
    fig.text(0.96, 0.035, "ivandujaut.com", fontsize=9.5, color=FG, ha="right", alpha=0.55)
    return guardar(fig, t["archivo"])


def main() -> None:
    if not CACHE.exists():
        raise SystemExit(
            f"No hay cache en {CACHE}. "
            "Correr primero: uv run analysis/corte-01_carrera.py"
        )
    datos = json.loads(CACHE.read_text())
    for locale in TEXTOS:
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
