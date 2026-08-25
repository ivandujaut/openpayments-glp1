"""Estilo único de figuras del caso Open Payments GLP-1.

Fuente de verdad de paleta, tipografía y formato. Toda figura del caso se crea
con `nueva_figura()` y se persiste con `guardar()`, desde un script de charts/.
Prohibido matplotlib suelto: si una figura no nace acá, no es del caso.

Paleta heredada de los casos del sitio (ivandujaut.com). Colores de serie FIJOS
para toda la serie de contenido: Novo = AZUL, Lilly = AMBAR. No rotarlos jamás:
la consistencia visual es parte de la identidad de la serie.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# --- Paleta (idéntica a los scripts del sitio) ---------------------------------
FG = "#111111"
GRAY = "#8a8a8a"
BG = "#f8f9fa"
AZUL = "#2f74dd"        # Novo Nordisk
AMBAR = "#c2571a"       # Eli Lilly
BAJA = "#e8663c"
ALZA = "#17a673"
GRIS_AZUL_1 = "#b8c4d4"
GRIS_AZUL_2 = "#9aa5b1"

SERIE = {"novo": AZUL, "lilly": AMBAR}

# --- Formato (idéntico a los PNG del sitio) -------------------------------------
W, H, DPI = 1495, 886, 100
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"


def _aplicar_rc() -> None:
    """rcParams compartidos por todas las figuras del caso."""
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "text.color": FG,
            "axes.edgecolor": GRAY,
            "axes.labelcolor": FG,
            "xtick.color": GRAY,
            "ytick.color": GRAY,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def nueva_figura(titulo: str, subtitulo: str | None = None):
    """Figura estándar del caso: 1495x886, DejaVu Sans, fondo BG.

    El título es un message title: dice el hallazgo, no describe los ejes.
    """
    _aplicar_rc()
    fig, ax = plt.subplots(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    fig.text(0.06, 0.955, titulo, fontsize=17, fontweight="bold", color=FG, ha="left")
    if subtitulo:
        fig.text(0.06, 0.915, subtitulo, fontsize=11.5, color=GRAY, ha="left")
    fig.subplots_adjust(top=0.84, left=0.08, right=0.96, bottom=0.11)
    return fig, ax


def nueva_figura_apilada(titulo: str, subtitulo: str | None = None, n: int = 2):
    """Como `nueva_figura`, pero con n paneles apilados que comparten eje x.

    Existe para los cortes cuyo hallazgo es que dos unidades se contradicen
    (D-005): poner una arriba de la otra deja la contradicción a la vista sin
    obligar a un eje secundario, que siempre miente sobre las magnitudes.

    Mismo formato fijo W x H que `nueva_figura`: la identidad visual no cambia
    por tener más paneles.
    """
    _aplicar_rc()
    fig, axes = plt.subplots(
        n, 1, figsize=(W / DPI, H / DPI), dpi=DPI, sharex=True
    )
    fig.patch.set_facecolor(BG)
    for ax in axes:
        ax.set_facecolor(BG)
    fig.text(0.06, 0.955, titulo, fontsize=17, fontweight="bold", color=FG, ha="left")
    if subtitulo:
        fig.text(0.06, 0.915, subtitulo, fontsize=11.5, color=GRAY, ha="left")
    fig.subplots_adjust(top=0.84, left=0.08, right=0.96, bottom=0.11, hspace=0.28)
    return fig, axes


def guardar(fig, nombre: str) -> Path:
    """Persiste a figures/<nombre>.png. Convención: gN_<nombre>[.en].png.

    SIN bbox_inches="tight": el recorte automático descarta el margen que
    `nueva_figura` reserva para el título y hace que cada PNG salga de un
    tamaño distinto según cuánto ocupe su contenido. Acá el formato es fijo
    (W x H) y eso es parte de la identidad visual de la serie: todas las
    figuras del caso miden lo mismo y el título arranca en el mismo lugar.
    """
    OUT.mkdir(exist_ok=True)
    destino = OUT / f"{nombre}.png"
    fig.savefig(destino, facecolor=BG, dpi=DPI)
    plt.close(fig)
    return destino


def miles(n: float, locale: str = "es") -> str:
    """Separador de miles por locale: 12.345 en es · 12,345 en en."""
    s = f"{n:,.0f}"
    return s.replace(",", ".") if locale == "es" else s
