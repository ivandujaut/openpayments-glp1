"""g3 — cuánto del gasto GLP-1 se concentra en los primeros profesionales.

Barras agrupadas por corte (top 10 a top 1000), que es la forma legible de
mostrar concentración: una curva de Lorenz sube casi vertical en el primer 1% y
deja el resto plano, ilegible en escala lineal.

Lee SOLO findings/cache/corte-02_concentracion.json.

Uso:  uv run charts/g3_concentracion.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, FG, guardar, nueva_figura  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-02_concentracion.json"
TOPS = (10, 50, 100, 500, 1000)

TEXTOS = {
    "es": {
        "titulo": "Cien médicos concentran el 36% de lo que Lilly gasta en GLP-1; en Novo, el 20%",
        "subtitulo": ("Porcentaje del gasto en productos GLP-1 que recibe el top N de profesionales de cada "
                      "compañía, 2021–2025 · CMS Open Payments"),
        "ylabel": "% del gasto de la compañía",
        "xlabel": "Profesionales mejor pagos de cada compañía",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "eje": ["top 10", "top 50", "top 100", "top 500", "top 1.000"],
        "nota": ("Red de Novo: 209.450 profesionales · Lilly: 152.493. Gini 0,855 y 0,885. "
                 "El top 100 es la métrica líder (D-007); los demás cortes muestran que el orden no depende de N."),
        "archivo": "g3_concentracion",
    },
    "en": {
        "titulo": "One hundred doctors take 36% of Lilly's GLP-1 spending; at Novo, 20%",
        "subtitulo": ("Share of GLP-1 product spending going to each company's top N healthcare professionals, "
                      "2021–2025 · CMS Open Payments"),
        "ylabel": "% of company spending",
        "xlabel": "Each company's highest-paid professionals",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "eje": ["top 10", "top 50", "top 100", "top 500", "top 1,000"],
        "nota": ("Novo's network: 209,450 professionals · Lilly's: 152,493. Gini 0.855 and 0.885. "
                 "Top 100 is the lead metric (D-007); the other cuts show the ordering does not depend on N."),
        "archivo": "g3_concentracion.en",
    },
}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    por_grupo = {f["grupo"]: f for f in datos["concentracion"]}

    fig, ax = nueva_figura(t["titulo"], t["subtitulo"])
    x = range(len(TOPS))
    ancho = 0.38

    for desp, clave, nombre in ((-ancho / 2, "novo", t["novo"]), (ancho / 2, "lilly", t["lilly"])):
        valores = [por_grupo[clave][f"top{n}"] for n in TOPS]
        posiciones = [i + desp for i in x]
        ax.bar(posiciones, valores, ancho, color=SERIE[clave], label=nombre, zorder=3)
        for px, v in zip(posiciones, valores):
            ax.annotate(f"{v:.1f}".replace(".", "," if locale == "es" else "."),
                        (px, v), textcoords="offset points", xytext=(0, 4),
                        ha="center", fontsize=9.5, color=SERIE[clave], fontweight="bold")

    # El top 100 es la métrica líder: se marca sin gritar.
    ax.axvspan(2 - 0.5, 2 + 0.5, color=GRAY, alpha=0.11, lw=0, zorder=0)

    ax.set_xticks(list(x))
    ax.set_xticklabels(t["eje"])
    ax.set_ylabel(t["ylabel"], fontsize=10.5, color=GRAY)
    ax.set_xlabel(t["xlabel"], fontsize=10.5, color=GRAY, labelpad=10)
    ax.set_ylim(0, 82)
    ax.grid(axis="y", color=GRAY, alpha=0.18, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=11)

    fig.text(0.08, 0.032, t["nota"], fontsize=9, color=GRAY, ha="left")
    fig.text(0.96, 0.032, "ivandujaut.com", fontsize=9.5, color=FG, ha="right", alpha=0.55)
    return guardar(fig, t["archivo"])


def main() -> None:
    if not CACHE.exists():
        raise SystemExit(
            f"No hay cache en {CACHE}. "
            "Correr primero: uv run analysis/corte-02_concentracion.py"
        )
    datos = json.loads(CACHE.read_text())
    for locale in TEXTOS:
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
