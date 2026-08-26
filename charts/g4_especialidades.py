"""g4 — a qué perfil profesional le paga cada compañía.

Barras horizontales por perfil, con el tamaño de cada población y el dinero por
cabeza anotados a la derecha: el hallazgo es la desproporción entre cuánta gente
hay en cada grupo y cuánto recibe.

Lee SOLO findings/cache/corte-03_especialidades.json.

Uso:  uv run charts/g4_especialidades.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.figstyle import SERIE, GRAY, FG, guardar, nueva_figura  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache" / "corte-03_especialidades.json"

# D-009 agregó "emergentes" y D-011 "respiratorio y sueño"; ninguna de las dos
# llegó a este chart en su momento y la figura publicada omitía una categoría de
# USD 16,20M. La lista se ordena como la tabla del finding.
ORDEN = ["endocrinologia", "primaria", "NP/PA", "emergentes",
         "medicina de obesidad", "respiratorio y sueño", "resto"]

TEXTOS = {
    "es": {
        "titulo": "5.367 endocrinólogos reciben casi el doble que 120.145 enfermeros y asistentes",
        "subtitulo": ("Gasto en GLP-1 por perfil del profesional que recibe el pago, 2021–2025. "
                      "Lilly destina el 44% a endocrinología; Novo, el 31% · CMS Open Payments"),
        "etiquetas": {
            "endocrinologia": "Endocrinología",
            "primaria": "Atención primaria\n(médico)",
            "NP/PA": "Enfermería y\nasistentes médicos",
            "emergentes": "Cardiología, nefrología,\ngastro/hepatología",
            "medicina de obesidad": "Medicina\nde obesidad",
            "respiratorio y sueño": "Neumonología, sueño\ny cuidados críticos",
            "resto": "Resto",
        },
        "xlabel": "Millones de USD",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "cabecera": "profesionales · USD por cabeza",
        "nota": ("Categorías de D-008, reabierta por D-009 y D-011, evaluadas en orden: un NP o PA "
                 "cuenta como tal aunque su subespecialidad sea de neumonología o atención primaria."),
        "archivo": "g4_especialidades",
    },
    "en": {
        "titulo": "5,367 endocrinologists receive nearly twice as much as 120,145 nurses and PAs",
        "subtitulo": ("GLP-1 spending by profile of the professional receiving the payment, 2021–2025. "
                      "Lilly puts 44% into endocrinology; Novo, 31% · CMS Open Payments"),
        "etiquetas": {
            "endocrinologia": "Endocrinology",
            "primaria": "Primary care\n(physician)",
            "NP/PA": "Nurse practitioners\nand physician assistants",
            "emergentes": "Cardiology, nephrology,\ngastro/hepatology",
            "medicina de obesidad": "Obesity\nmedicine",
            "respiratorio y sueño": "Pulmonology, sleep\nand critical care",
            "resto": "Other",
        },
        "xlabel": "USD millions",
        "novo": "Novo Nordisk",
        "lilly": "Eli Lilly",
        "cabecera": "professionals · USD per head",
        "nota": ("D-008 categories, reopened by D-009 and D-011, evaluated in order: an NP or PA counts "
                 "as such even when their subspecialty is pulmonology or primary care."),
        "archivo": "g4_especialidades.en",
    },
}


def miles_loc(n: float, locale: str) -> str:
    return f"{n:,.0f}".replace(",", ".") if locale == "es" else f"{n:,.0f}"


def dibujar(datos: dict, locale: str) -> Path:
    t = TEXTOS[locale]
    por_esp = {f["especialidad"]: f for f in datos["reparto"]}
    filas = [por_esp[e] for e in ORDEN if e in por_esp]

    fig, ax = nueva_figura(t["titulo"], t["subtitulo"])
    # Las etiquetas de perfil son largas y de dos líneas: el margen izquierdo
    # por defecto (0.08) las recorta. La columna derecha también necesita aire.
    fig.subplots_adjust(left=0.155, right=0.80)
    y = range(len(filas))
    alto = 0.38

    for desp, clave, nombre in ((alto / 2, "novo", t["novo"]), (-alto / 2, "lilly", t["lilly"])):
        valores = [f[f"{clave}_usd"] / 1e6 for f in filas]
        ax.barh([i + desp for i in y], valores, alto, color=SERIE[clave],
                label=nombre, zorder=3)
        for i, v in zip(y, valores):
            ax.annotate(f"{v:.1f}".replace(".", "," if locale == "es" else "."),
                        (v, i + desp), textcoords="offset points", xytext=(4, -3),
                        fontsize=9.5, color=SERIE[clave], fontweight="bold")

    ax.set_yticks(list(y))
    ax.set_yticklabels([t["etiquetas"][f["especialidad"]] for f in filas], fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlabel(t["xlabel"], fontsize=10.5, color=GRAY)
    ax.set_xlim(0, 52)
    ax.grid(axis="x", color=GRAY, alpha=0.18, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="center right", fontsize=11)

    # Columna derecha: cuánta gente hay y cuánto recibe cada uno. Es el contraste
    # que la barra sola no muestra.
    ax.annotate(t["cabecera"], (1.02, 1.03), xycoords="axes fraction",
                ha="left", fontsize=9, color=GRAY, style="italic")
    for i, f in zip(y, filas):
        ax.annotate(f"{miles_loc(f['hcps'], locale)} · {miles_loc(f['usd_por_hcp'], locale)}",
                    (1.02, i), xycoords=("axes fraction", "data"),
                    ha="left", va="center", fontsize=10, color=FG)

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
