"""g5 — la brecha en endocrinología se está cerrando.

Nace del ataque 08 (A5): el acumulado del corte 03 esconde una convergencia
fuerte. La diferencia entre compañías en el peso de endocrinología pasó de 30
puntos en 2023 a 3,2 en 2025.

Lee SOLO findings/cache/corte-03_especialidades.json (bloque serie).

Uso:  uv run charts/g5_convergencia.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, FG, guardar, nueva_figura  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-03_especialidades.json"

TEXTOS = {
    "es": {
        "titulo": "La apuesta de Lilly a los endocrinólogos se desinfló: de 30 puntos de ventaja a 3",
        "subtitulo": ("Porcentaje del gasto anual en GLP-1 que cada compañía destina a endocrinología, "
                      "2021–2025 · CMS Open Payments"),
        "ylabel": "% del gasto anual de la compañía",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "brecha": "brecha",
        "nota": ("El corte 03 publica el acumulado del período (Lilly 43,6% · Novo 31,5%), que esconde "
                 "esta trayectoria. El pico de divergencia es 2023."),
        "archivo": "g5_convergencia",
    },
    "en": {
        "titulo": "Lilly's bet on endocrinologists deflated: from a 30-point lead to 3",
        "subtitulo": ("Share of each company's annual GLP-1 spending going to endocrinology, "
                      "2021–2025 · CMS Open Payments"),
        "ylabel": "% of company's annual spending",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "brecha": "gap",
        "nota": ("Cut 03 reports the period total (Lilly 43.6% · Novo 31.5%), which hides this path. "
                 "Divergence peaks in 2023."),
        "archivo": "g5_convergencia.en",
    },
}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    filas = [f for f in datos["serie"] if f["especialidad"] == "endocrinologia"]
    filas.sort(key=lambda f: f["anio"])
    anios = [int(f["anio"]) for f in filas]
    novo = [f["novo_pct"] for f in filas]
    lilly = [f["lilly_pct"] for f in filas]

    fig, ax = nueva_figura(t["titulo"], t["subtitulo"])

    # La brecha, sombreada: es el sujeto de la figura.
    ax.fill_between(anios, novo, lilly, color=GRAY, alpha=0.16, lw=0, zorder=1)
    for valores, clave, nombre in ((novo, "novo", t["novo"]), (lilly, "lilly", t["lilly"])):
        ax.plot(anios, valores, color=SERIE[clave], lw=2.8, marker="o", ms=6,
                label=nombre, zorder=3)
        for x, v in zip(anios, valores):
            ax.annotate(f"{v:.1f}".replace(".", "," if locale == "es" else "."),
                        (x, v), textcoords="offset points",
                        xytext=(0, 9 if clave == "lilly" else -16),
                        ha="center", fontsize=10, color=SERIE[clave], fontweight="bold")

    # Anotar la brecha en el pico y en el final.
    for x, n, l in zip(anios, novo, lilly):
        if x in (2023, 2025):
            ax.annotate(f"{t['brecha']} {abs(l-n):.1f}".replace(".", "," if locale == "es" else "."),
                        (x, (n + l) / 2), ha="center", va="center", fontsize=10,
                        color=FG, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.35", fc="#f8f9fa", ec=GRAY, lw=0.7))

    ax.set_xticks(anios)
    ax.set_ylabel(t["ylabel"], fontsize=10.5, color=GRAY)
    ax.set_ylim(0, 68)
    ax.grid(axis="y", color=GRAY, alpha=0.18, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right", fontsize=11)

    fig.text(0.08, 0.032, t["nota"], fontsize=9, color=GRAY, ha="left")
    fig.text(0.96, 0.032, "ivandujaut.com", fontsize=9.5, color=FG, ha="right", alpha=0.55)
    return guardar(fig, t["archivo"])


def main() -> None:
    if not CACHE.exists():
        raise SystemExit(
            f"No hay cache en {CACHE}. "
            "Correr primero: uv run analysis/corte-03_especialidades.py"
        )
    datos = json.loads(CACHE.read_text())
    for locale in TEXTOS:
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
