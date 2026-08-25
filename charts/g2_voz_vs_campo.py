"""g2 — de dónde sale la ventaja de Lilly en dólares.

Nace del ataque 03 (C2) y se formaliza en D-006: al excluir el grupo "voz"
(honorarios de disertante + consultoría), Lilly no supera a Novo en ningún año.
La figura pone los dos paneles uno sobre otro para que se vea que el cruce
desaparece.

Lee SOLO findings/cache/corte-01_carrera.json (bloque voz_vs_campo).

Uso:  uv run charts/g2_voz_vs_campo.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, FG, guardar, nueva_figura_apilada  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-01_carrera.json"

TEXTOS = {
    "es": {
        "titulo": "Toda la ventaja de Lilly en dólares está en los pagos que compran la voz del profesional",
        "subtitulo": ("Pagos por productos GLP-1, 2021–2025. Al excluir honorarios de disertante y consultoría, "
                      "Novo supera a Lilly los cinco años · CMS Open Payments (D-006)"),
        "panel_a": "Pagos que compran\nla voz del profesional",
        "panel_b": "Contacto de campo\n(comidas, viajes, educación)",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "nota": "Millones de USD. Banda gris: años en que Lilly supera a Novo.",
        "archivo": "g2_voz_campo",
    },
    "en": {
        "titulo": "Lilly's entire dollar lead sits in payments that buy the professional's voice",
        "subtitulo": ("GLP-1 product payments, 2021–2025. Excluding speaker and consulting fees, Novo outspends "
                      "Lilly in all five years · CMS Open Payments (D-006)"),
        "panel_a": "Payments buying\nthe professional's voice",
        "panel_b": "Field contact\n(meals, travel, education)",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "nota": "USD millions. Shaded band: years where Lilly outspends Novo.",
        "archivo": "g2_voz_campo.en",
    },
}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    filas = datos["voz_vs_campo"]
    anios = [int(f["anio"]) for f in filas]

    fig, (ax_a, ax_b) = nueva_figura_apilada(t["titulo"], t["subtitulo"], n=2)

    paneles = (
        (ax_a, t["panel_a"],
         [f["novo_voz"] / 1e6 for f in filas],
         [f["lilly_voz"] / 1e6 for f in filas]),
        (ax_b, t["panel_b"],
         [f["novo_campo"] / 1e6 for f in filas],
         [f["lilly_campo"] / 1e6 for f in filas]),
    )
    for ax, etiqueta, novo, lilly in paneles:
        # Banda donde Lilly supera a Novo: en el panel de abajo no hay ninguna,
        # y ese vacío es el hallazgo.
        for a, n, l in zip(anios, novo, lilly):
            if l > n:
                ax.axvspan(a - 0.5, a + 0.5, color=GRAY, alpha=0.13, lw=0)
        for valores, clave, nombre in ((novo, "novo", t["novo"]), (lilly, "lilly", t["lilly"])):
            ax.plot(anios, valores, color=SERIE[clave], lw=2.6, marker="o",
                    ms=5.5, label=nombre, zorder=3)
        ax.set_ylabel(etiqueta, fontsize=10, color=GRAY)
        ax.set_xticks(anios)
        ax.set_ylim(0, 20)
        ax.grid(axis="y", color=GRAY, alpha=0.18, lw=0.8)
        ax.set_axisbelow(True)

    ax_a.legend(frameon=False, loc="upper center", ncol=2, fontsize=11,
                bbox_to_anchor=(0.5, 1.24))
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
    if "voz_vs_campo" not in datos:
        raise SystemExit(
            "El cache no tiene el bloque 'voz_vs_campo'. "
            "Regenerar: uv run analysis/corte-01_carrera.py"
        )
    for locale in TEXTOS:
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
