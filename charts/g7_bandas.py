"""g7 — la tesis del caso rotación: la retención se compra.

Retención año-a-año por banda fija de gasto anual por cabeza (D-016). A igual
inversión, Novo retiene igual o mejor en las bandas bajas; arriba de USD 25.000
nadie se va. Lee SOLO findings/cache/corte-05_rotacion.json.

Uso:  uv run charts/g7_bandas.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src.figstyle import SERIE, GRAY, FG, guardar, nueva_figura  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-05_rotacion.json"
ORDEN = ["a <5k", "b 5-25k", "c 25-75k", "d 75k+"]

TEXTOS = {
    "es": {
        "titulo": "La retención se compra: arriba de USD 25.000 al año no se va casi nadie",
        "subtitulo": ("Retención año a año del programa de voz GLP-1 por banda de gasto anual "
                      "por cabeza, 2021–2025 · CMS Open Payments (D-016)"),
        "ylabel": "% que sigue en el programa al año siguiente",
        "bandas": ["menos de\nUSD 5.000", "5 a 25 mil", "25 a 75 mil", "75 mil o más"],
        "novo": "Novo Nordisk", "lilly": "Eli Lilly",
        "nota": ("Cada barra anota sus profesional-años. La brecha agregada de retención "
                 "(82,2% Lilly · 79,2% Novo) nace de dónde estaciona cada una la plata, no de estas barras."),
        "archivo": "g7_bandas",
    },
    "en": {
        "titulo": "Retention is bought: above USD 25,000 a year almost nobody leaves",
        "subtitulo": ("Year-over-year retention in the GLP-1 speaker program by annual "
                      "spend-per-head band, 2021–2025 · CMS Open Payments (D-016)"),
        "ylabel": "% still in the program the next year",
        "bandas": ["under\nUSD 5,000", "5 to 25k", "25 to 75k", "75k or more"],
        "novo": "Novo Nordisk", "lilly": "Eli Lilly",
        "nota": ("Each bar notes its professional-years. The aggregate retention gap "
                 "(82.2% Lilly · 79.2% Novo) comes from where each parks the money, not from these bars."),
        "archivo": "g7_bandas.en",
    },
}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    filas = {(f["banda"], f["grupo"]): f for f in datos["retencion_por_banda"]}
    x = np.arange(len(ORDEN))
    ancho = 0.38

    fig, ax = nueva_figura(t["titulo"], t["subtitulo"])
    for despl, grupo in ((-ancho / 2, "novo"), (ancho / 2, "lilly")):
        vals = [filas[(b, grupo)]["retencion_pct"] for b in ORDEN]
        pas = [int(filas[(b, grupo)]["prof_anios"]) for b in ORDEN]
        barras = ax.bar(x + despl, vals, ancho, color=SERIE[grupo], label=t[grupo])
        for xi, v, pa in zip(x + despl, vals, pas):
            sep = "." if locale == "es" else ","
            v_txt = f"{v:.1f}".replace(".", ",") if locale == "es" else f"{v:.1f}"
            ax.text(xi, v + 1.5, v_txt, ha="center", fontsize=11,
                    fontweight="bold", color=SERIE[grupo])
            ax.text(xi, 3, f"{pa:,}".replace(",", sep), ha="center", fontsize=9,
                    color="white", fontweight="bold")

    ax.set_xticks(x, t["bandas"], fontsize=11)
    ax.set_ylabel(t["ylabel"], fontsize=11, color=GRAY)
    ax.set_ylim(0, 108)
    ax.legend(frameon=False, fontsize=11, loc="upper left")
    fig.text(0.06, 0.03, t["nota"], fontsize=9.5, color=GRAY)
    fig.text(0.96, 0.03, "ivandujaut.com", fontsize=9.5, color=GRAY, ha="right")
    return guardar(fig, t["archivo"])


def main() -> None:
    datos = json.loads(CACHE.read_text())
    for locale in ("es", "en"):
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
