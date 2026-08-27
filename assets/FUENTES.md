# Insumos de imagen

Fotografías que usan los scripts de `charts/`. Se versionan porque sin ellas la
figura no se puede regenerar, y regenerable es la condición de todo lo que
publica este repo.

## carbon-lapiceras.jpg

- **Qué es:** una **ilustración** en carbón sobre papel: una mano sosteniendo un
  puñado de lapiceras de autoinyección de la clase GLP-1, que es la categoría
  cuya promoción mide el caso. Es la portada, no evidencia.
- **Cómo se hizo:** generada con Gemini el 2026-08-27 a partir de una imagen de
  referencia, con el prompt de estudio en carbón que fija el estilo de esta
  familia de casos (papel blanco cálido, sin partículas sueltas, degradé hacia
  los bordes, sin color).
- **No es una fotografía.** El `alt` del caso lo dice con esas palabras, para que
  nadie la lea como un registro de algo que ocurrió.
- **Post-proceso:** `charts/portada.py` parcha la marca de agua del generador,
  extiende el papel y exporta los dos formatos del sitio. Regenerable.

## pen-ozempic.jpg

- **Qué es:** una lapicera precargada de Ozempic (semaglutida, Novo Nordisk),
  uno de los nueve productos de la clase GLP-1 que define D-003.
- **Fuente:** Wikimedia Commons, `File:Ozempic® 3ml.jpg`.
- **URL:** https://upload.wikimedia.org/wikipedia/commons/f/f5/Ozempic%C2%AE_3ml.jpg
- **Autoría:** HualinXMN. **Licencia:** CC BY-SA 4.0.
- **Capturada:** 2026-08-26. 4624x3008, JPEG.

## pen-mounjaro.jpg

- **Qué es:** una lapicera KwikPen de Mounjaro (tirzepatida, Eli Lilly), el
  producto que más gasto promocional concentra del lado de Lilly en la ventana.
- **Fuente:** Wikimedia Commons,
  `File:Lilly mounjaro KwikPen Tirzepatid 5 mg per dose rate-9441.jpg`.
- **URL:** https://upload.wikimedia.org/wikipedia/commons/d/db/Lilly_mounjaro_KwikPen_Tirzepatid_5_mg_per_dose_rate-9441.jpg
- **Autoría:** Raimond Spekking. **Licencia:** CC BY-SA 4.0.
- **Capturada:** 2026-08-26. 5036x1970, JPEG.

## Qué implica la licencia

Las dos son CC BY-SA 4.0, así que **la portada que las combina hereda esa
licencia** y tiene que dar crédito. El pie de la figura y el `alt` del caso
llevan los dos nombres y la licencia. No es una restricción incómoda: es el
mismo trato que este repo le pide a quien use sus datos.

## Qué NO son estas fotos

Fotos de producto, nada más. No documentan un pago, un evento ni una relación
comercial, y no son evidencia de nada de lo que el caso afirma. La evidencia es
el archivo de CMS; esto es la portada.

## Descartada

- `sala-auditorio.jpg`, un auditorio vacío con atril (WordPress Photo Directory,
  CC0, https://pd.w.org/2025/01/5176786995811e4a8.19715501-2048x1366.jpg). Se
  usó en una versión previa de la portada, con la proporción del corte 03
  dibujada encima. Se descartó: la sala no tenía relación con el análisis y a
  tamaño de tarjeta no se leía.
