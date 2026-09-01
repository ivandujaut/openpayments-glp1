"""g8 — la promesa del caso madre, cumplida: la rotación contra el descarte.

Rotación anual del programa de voz por compañía, con la línea del criterio de
descarte publicado (30%). Lee SOLO findings/cache/corte-05_rotacion.json.

Uso:  uv run charts/g8_descarte.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, BAJA, guardar, nueva_figura  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-05_rotacion.json"

TEXTOS = {
    "es": {
        "titulo": "El límite que dejé escrito era 30% de rotación anual. Nadie lo tocó",
        "subtitulo": ("Rotación año a año del programa de voz GLP-1 (membresía D-012), "
                      "2021–2025 · CMS Open Payments"),
        "ylabel": "% del programa que no sigue al año siguiente",
        "novo": "Novo Nordisk", "lilly": "Eli Lilly",
        "descarte": "límite publicado: 30%",
        "nota": ("El límite quedó escrito en el caso anterior, antes de correr este análisis. "
                 "El pico de Novo (28,4%) es el año previo a su recorte del gasto de voz."),
        "archivo": "g8_descarte",
    },
    "en": {
        "titulo": "The limit I put in writing was 30% annual turnover. Nobody touched it",
        "subtitulo": ("Year-over-year turnover of the GLP-1 speaker program (D-012 membership), "
                      "2021–2025 · CMS Open Payments"),
        "ylabel": "% of the program gone the next year",
        "novo": "Novo Nordisk", "lilly": "Eli Lilly",
        "descarte": "published limit: 30%",
        "nota": ("The limit was written down in the previous case, before this analysis ran. "
                 "Novo's peak (28.4%) is the year before its voice-budget cut."),
        "archivo": "g8_descarte.en",
    },
}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    fig, ax = nueva_figura(t["titulo"], t["subtitulo"])
    for grupo in ("novo", "lilly"):
        filas = sorted((f for f in datos["retencion"] if f["grupo"] == grupo),
                       key=lambda f: f["anio"])
        anios = [f"{int(f['anio'])}→{int(f['anio'])+1-2000}" for f in filas]
        vals = [f["rotacion_pct"] for f in filas]
        ax.plot(anios, vals, marker="o", lw=3, ms=8, color=SERIE[grupo], label=t[grupo])
        for xi, v in zip(anios, vals):
            v_txt = f"{v:.1f}".replace(".", ",") if locale == "es" else f"{v:.1f}"
            ax.annotate(v_txt, (xi, v), textcoords="offset points", xytext=(0, 12),
                        ha="center", fontsize=11, fontweight="bold", color=SERIE[grupo])
    ax.axhline(30, color=BAJA, lw=2, ls="--")
    ax.text(0.02, 30.8, t["descarte"], fontsize=11, color=BAJA,
            transform=ax.get_yaxis_transform())
    ax.set_ylabel(t["ylabel"], fontsize=11, color=GRAY)
    ax.set_ylim(0, 36)
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    fig.text(0.06, 0.03, t["nota"], fontsize=9.5, color=GRAY)
    fig.text(0.96, 0.03, "ivandujaut.com", fontsize=9.5, color=GRAY, ha="right")
    return guardar(fig, t["archivo"])


def main() -> None:
    datos = json.loads(CACHE.read_text())
    for locale in ("es", "en"):
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
