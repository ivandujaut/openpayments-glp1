"""g6 — adónde movió cada compañía su gasto entre 2023 y 2025.

Nace del corte 04. La convergencia que mostró g5 es en PORCENTAJE; en dólares
absolutos las dos compañías se mueven en direcciones distintas. Barras de delta
desde cero: Lilly tiene una sola barra negativa (endocrinología) y Novo ninguna.

Lee SOLO findings/cache/corte-04_convergencia.json.

Uso:  uv run charts/g6_movimiento.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, FG, guardar, nueva_figura  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-04_convergencia.json"

ORDEN = ["emergentes", "endocrinologia", "primaria", "NP/PA",
         "medicina de obesidad", "resto"]

TEXTOS = {
    "es": {
        "titulo": "Novo abrió un frente nuevo; Lilly se replegó al médico generalista",
        "subtitulo": ("Cambio en el gasto anual en GLP-1 entre 2023 y 2025, por perfil del profesional. "
                      "Endocrinología es lo único que cae, y sólo en Lilly · CMS Open Payments"),
        "etiquetas": {
            "emergentes": "Cardiología, nefrología,\ngastro/hepatología",
            "endocrinologia": "Endocrinología",
            "primaria": "Atención primaria\n(médico)",
            "NP/PA": "Enfermería y\nasistentes médicos",
            "medicina de obesidad": "Medicina\nde obesidad",
            "resto": "Resto",
        },
        "xlabel": "Cambio en millones de USD, 2023 → 2025",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "nota": ("2023 es el pico de divergencia entre ambas. El grupo emergente lo pagan Wegovy "
                 "(0,15 → 4,35M) y Ozempic (0,75 → 2,87M); que sea por sus nuevas indicaciones es hipótesis, no dato."),
        "archivo": "g6_movimiento",
    },
    "en": {
        "titulo": "Novo opened a new front; Lilly fell back on the generalist physician",
        "subtitulo": ("Change in annual GLP-1 spending between 2023 and 2025, by professional profile. "
                      "Endocrinology is the only category that falls, and only at Lilly · CMS Open Payments"),
        "etiquetas": {
            "emergentes": "Cardiology, nephrology,\ngastro/hepatology",
            "endocrinologia": "Endocrinology",
            "primaria": "Primary care\n(physician)",
            "NP/PA": "Nurse practitioners\nand physician assistants",
            "medicina de obesidad": "Obesity\nmedicine",
            "resto": "Other",
        },
        "xlabel": "Change in USD millions, 2023 → 2025",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "nota": ("2023 is the peak of divergence. The emerging group is paid by Wegovy (0.15 → 4.35M) "
                 "and Ozempic (0.75 → 2.87M); attributing it to their new indications is a hypothesis, not data."),
        "archivo": "g6_movimiento.en",
    },
}


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    por = {(f["grupo"], f["especialidad"]): f for f in datos["movimiento"]}
    filas = [e for e in ORDEN if ("novo", e) in por or ("lilly", e) in por]

    fig, ax = nueva_figura(t["titulo"], t["subtitulo"])
    fig.subplots_adjust(left=0.20, right=0.95)
    y = range(len(filas))
    alto = 0.38

    for desp, clave, nombre in ((alto / 2, "novo", t["novo"]), (-alto / 2, "lilly", t["lilly"])):
        deltas = [por.get((clave, e), {}).get("delta", 0) / 1e6 for e in filas]
        ax.barh([i + desp for i in y], deltas, alto, color=SERIE[clave],
                label=nombre, zorder=3)
        for i, d in zip(y, deltas):
            if abs(d) < 0.01:
                continue
            signo = "+" if d > 0 else "−"
            ax.annotate(f"{signo}{abs(d):.2f}".replace(".", "," if locale == "es" else "."),
                        (d, i + desp), textcoords="offset points",
                        xytext=(5 if d > 0 else -5, -3),
                        ha="left" if d > 0 else "right",
                        fontsize=9.5, color=SERIE[clave], fontweight="bold")

    ax.axvline(0, color=FG, lw=1.1, zorder=4)
    ax.set_yticks(list(y))
    ax.set_yticklabels([t["etiquetas"][e] for e in filas], fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlabel(t["xlabel"], fontsize=10.5, color=GRAY)
    ax.set_xlim(-3.2, 7.8)
    ax.grid(axis="x", color=GRAY, alpha=0.18, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right", fontsize=11)

    fig.text(0.08, 0.032, t["nota"], fontsize=9, color=GRAY, ha="left")
    fig.text(0.96, 0.032, "ivandujaut.com", fontsize=9.5, color=FG, ha="right", alpha=0.55)
    return guardar(fig, t["archivo"])


def main() -> None:
    if not CACHE.exists():
        raise SystemExit(
            f"No hay cache en {CACHE}. "
            "Correr primero: uv run analysis/corte-04_convergencia.py"
        )
    datos = json.loads(CACHE.read_text())
    for locale in TEXTOS:
        print(f"{locale} → {dibujar(datos, locale).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
