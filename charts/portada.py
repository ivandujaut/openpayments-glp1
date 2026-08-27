"""Portada del caso, a partir del estudio en carbón.

Entrada: `assets/carbon-lapiceras.jpg`, una ilustración en carbón de un puñado
de lapiceras de autoinyección de la clase GLP-1, que es la categoría cuya
promoción mide el caso. No es una fotografía y no documenta nada: es la portada.

Qué hace este script, y por qué cada paso:

1. **Parcha la marca de agua** que el generador deja abajo a la derecha. Se clona
   una zona vecina de la misma sombra en vez de emborronar, que dejaría un
   parche liso adentro de un dibujo con grano.
2. **Extiende el papel** hacia la izquierda hasta el formato de salida. La
   tarjeta del sitio recorta a 1,4 y la imagen social a 1,9, y el título va
   encima: sin ese aire, el recorte se come la mano. Se extiende espejando una
   franja de papel vacío, que no tiene dibujo y por eso no deja costura.
3. Exporta los dos formatos que usa el sitio.

Uso:  uv run charts/portada.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
ORIGEN = ROOT / "assets" / "carbon-lapiceras.jpg"
OUT = ROOT / "figures"

# Caja de la marca de agua en coordenadas del archivo original (1264x843) y
# desplazamiento desde donde se clona el reemplazo: misma sombra, mismo grano.
MARCA = (1180, 754, 1241, 822)
CLON_DX = -78


def papel_color(im: Image.Image) -> tuple[int, int, int]:
    """El blanco cálido del papel, muestreado del borde superior izquierdo."""
    zona = im.crop((0, 0, max(4, im.width // 12), max(4, im.height // 12)))
    px = list(zona.getdata())
    return tuple(round(sum(c[i] for c in px) / len(px)) for i in range(3))


def parche_marca(im: Image.Image) -> Image.Image:
    x0, y0, x1, y1 = MARCA
    fuente = im.crop((x0 + CLON_DX, y0, x1 + CLON_DX, y1))

    # Máscara con bordes suaves: un pegado duro se ve como un rectángulo.
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    d = ImageDraw.Draw(m)
    borde = 10
    d.rounded_rectangle([borde, borde, (x1 - x0) - borde, (y1 - y0) - borde],
                        radius=14, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(borde / 1.6))

    im = im.copy()
    im.paste(fuente, (x0, y0), m)
    return im


# Margen de papel a la derecha del dibujo, en proporción del ancho de salida.
# Sin él, la mano llega pegada al borde y cualquier recorte centrado la corta:
# la tarjeta del sitio recorta a 1,4 y la imagen social a 1,9 desde el centro.
MARGEN_DER = 0.07
# Ancho del disuelto sobre el borde derecho del dibujo, para que no termine en
# un corte duro contra el papel. El degradé de bordes es parte del estilo.
DISUELVE = 0.055


def extender_papel(im: Image.Image, w: int, h: int) -> Image.Image:
    """Lleva el dibujo al formato pedido agregando papel vacío alrededor."""
    margen = round(w * MARGEN_DER)
    # Altura completa: cualquier banda de papel arriba o abajo se ve como un
    # recuadro pegado adentro de la hoja.
    escala = h / im.height
    im = im.resize((round(im.width * escala), h), Image.LANCZOS)
    if im.width + margen > w:  # el dibujo no entra: se recorta por la izquierda,
        sobra = im.width + margen - w  # que es papel vacío
        im = im.crop((sobra, 0, im.width, h))

    # El borde derecho del dibujo se disuelve en el papel con una máscara
    # horizontal, así el corte de la mano no se lee como un tajo.
    ancho_d = max(8, round(im.width * DISUELVE))
    mascara = Image.new("L", im.size, 255)
    dm = ImageDraw.Draw(mascara)
    for k in range(ancho_d):
        dm.line([(im.width - 1 - k, 0), (im.width - 1 - k, im.height)],
                fill=round(255 * (k / ancho_d) ** 0.85))
    papel = Image.new("RGB", im.size, papel_color(im))
    im = Image.composite(im, papel, mascara)

    lienzo = Image.new("RGB", (w, h), papel_color(im))
    x_dibujo = w - margen - im.width
    lienzo.paste(im, (x_dibujo, 0))

    # El margen derecho y lo que falte a la izquierda se rellenan espejando una
    # franja de papel del propio dibujo: mismo tono y mismo grano, sin costura.
    franja = im.crop((0, 0, min(im.width, 200), h))
    espejo = franja.transpose(Image.FLIP_LEFT_RIGHT)
    for x in range(x_dibujo, -1, -franja.width):
        lienzo.paste(espejo.crop((max(0, franja.width - x), 0, franja.width, h)),
                     (max(0, x - franja.width), 0))
    for x in range(w - margen, w, franja.width):
        lienzo.paste(espejo.crop((0, 0, min(franja.width, w - x), h)), (x, 0))

    # El resto es papel liso del mismo tono, sin costura porque no hay trazo.
    return lienzo


def main() -> None:
    base = parche_marca(Image.open(ORIGEN).convert("RGB"))
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre, (w, h) in {"portada": (1600, 900), "portada_apertura": (1600, 1200)}.items():
        destino = OUT / f"{nombre}.jpg"
        extender_papel(base, w, h).save(destino, quality=93)
        print(destino)


if __name__ == "__main__":
    main()
