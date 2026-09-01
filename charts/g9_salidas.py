"""g9 — las tres salidas: nadie ficha, y el éxodo de Novo fue su recorte.

Composición de las salidas del programa de voz (D-015): reasignado a otras
drogas de la casa, fichado por el rival, o afuera. Lee SOLO
findings/cache/corte-05_rotacion.json.

Uso:  uv run charts/g9_salidas.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src.figstyle import GRAY, GRIS_AZUL_1, GRIS_AZUL_2, BAJA, guardar, nueva_figura_apilada  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-05_rotacion.json"

TEXTOS = {
    "es": {
        "titulo": "Las salidas casi nunca van al rival",
        "subtitulo": ("Composición de las salidas anuales del programa de voz GLP-1 (D-015), "
                      "2021–2025 · CMS Open Payments"),
        "series": {"afuera": "afuera de la voz", "reasignados": "reasignado a otras drogas de la casa",
                   "fichados": "fichado por el rival"},
        "panel": {"novo": "Novo Nordisk", "lilly": "Eli Lilly"},
        "nota": ("Barras en personas. El recorte del 69% del gasto de voz de Novo es el par 2022→23; "
                 "el fichaje nunca pasa de 15 personas."),
        "archivo": "g9_salidas",
    },
    "en": {
        "titulo": "Exits almost never go to the rival",
        "subtitulo": ("Composition of annual exits from the GLP-1 speaker program (D-015), "
                      "2021–2025 · CMS Open Payments"),
        "series": {"afuera": "out of voice work", "reasignados": "reassigned to other house drugs",
                   "fichados": "signed by the rival"},
        "panel": {"novo": "Novo Nordisk", "lilly": "Eli Lilly"},
        "nota": ("Bars are people. Novo's 69% voice-budget cut is the 2022→23 pair; "
                 "rival signings never exceed 15 people."),
        "archivo": "g9_salidas.en",
    },
}

COLORES = {"afuera": GRIS_AZUL_2, "reasignados": GRIS_AZUL_1, "fichados": BAJA}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    fig, axes = nueva_figura_apilada(t["titulo"], t["subtitulo"], n=2)
    for ax, grupo in zip(axes, ("novo", "lilly")):
        filas = sorted((f for f in datos["retencion"] if f["grupo"] == grupo),
                       key=lambda f: f["anio"])
        anios = [f"{int(f['anio'])}→{int(f['anio'])+1-2000}" for f in filas]
        base = np.zeros(len(filas))
        for clave in ("afuera", "reasignados", "fichados"):
            vals = np.array([f[clave] for f in filas], dtype=float)
            ax.bar(anios, vals, 0.55, bottom=base, color=COLORES[clave],
                   label=t["series"][clave] if grupo == "novo" else None)
            base += vals
        for xi, total in zip(anios, base):
            ax.text(xi, total + 4, str(int(total)), ha="center", fontsize=10.5,
                    fontweight="bold", color=GRAY)
        ax.set_ylim(0, 215)
        ax.text(0.99, 0.82, t["panel"][grupo], transform=ax.transAxes,
                ha="right", fontsize=12, fontweight="bold", color=GRAY)
    axes[0].legend(frameon=False, fontsize=10, loc="upper center", ncol=3)
    fig.text(0.06, 0.03, t["nota"], fontsize=9.5, color=GRAY)
    fig.text(0.96, 0.03, "ivandujaut.com", fontsize=9.5, color=GRAY, ha="right")
    return guardar(fig, t["archivo"])


def main() -> None:
    datos = json.loads(CACHE.read_text())
    for locale in ("es", "en"):
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
