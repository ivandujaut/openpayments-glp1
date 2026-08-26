# Cada compañía abrió su propio frente, con dos años de diferencia: Novo en cardiología, Lilly en sueño

**Corte 04 — 2026-08-25, recorrido 2026-08-26 por D-011 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: dólares absolutos (D-005) · Red-team: 25 ataques — H2 11/11 · H1 9/11 (depende del pivote) · el frente de Lilly 10/11**

## TL;DR

El corte 03 mostró que el peso de endocrinología en el gasto de las dos
compañías converge: de 30 puntos de brecha en 2023 a 3,2 en 2025. Este corte
mira el mismo período **en dólares absolutos** y encuentra que la convergencia
esconde dos movimientos opuestos.

**Lilly retiró USD 1,85M de endocrinología** —su única categoría en baja— y puso
USD 3,37M más en atención primaria. **Novo creció en todas**, y su mayor salto
fue en un grupo que Lilly casi no toca: **+USD 6,43M en cardiología, nefrología
y gastro/hepatología**, que pasan de 0,96M a 7,39M en dos años.

Ese grupo lo pagan dos productos: **Wegovy (0,15 → 4,35M) y Ozempic (0,75 →
2,87M)**. En el acumulado del período, Novo destina USD 14,74M a esas
especialidades contra 1,46M de Lilly — una relación de **10 a 1**.

**Y Lilly abrió el suyo, dos años después.** La primera versión de este corte
decía que Novo había abierto un frente que Lilly no tenía. Era falso, y el
motivo estaba adentro de la categoría residual: neumonología, medicina del
sueño y cuidados críticos pasan de **USD 0,013M en 2023 a 1,388M en 2025** en
Lilly, contra 0,039M de Novo. Es el **25,7% de todo lo que Lilly sumó** en esos
dos años, y **98,9% es Zepbound**. La categoría se separó en **D-011**, que
reabrió D-009 por la misma razón por la que D-009 había reabierto D-008: "resto"
estaba escondiendo una tendencia.

La simetría es el hallazgo: **en cardiología y afines Novo supera a Lilly 16 a 1
en 2025; en neumonología y sueño, Lilly supera a Novo 36 a 1**. Las dos
compañías se parecen más en proporciones porque se movieron en direcciones
distintas, no porque hagan lo mismo.

**El red-team acotó una de las afirmaciones.** El repliegue de Lilly desde
endocrinología es real desde 2023, pero **no es una tendencia del período
completo**: con 2021 como año base el movimiento se invierte (Lilly +2,32M, Novo
−3,52M). La trayectoria de Novo en endocrinología tiene forma de U —10,60M en
2021, 2,83M en 2023, 7,08M en 2025— así que el corte describe **una reversión
desde un pico, no una dirección sostenida**. Los dos frentes, en cambio,
sobrevivieron sus tests.

**Lo que NO dice:** que el movimiento de Novo sea *por* las nuevas indicaciones
cardiovascular y renal de la semaglutida, ni que el de Lilly sea *por* la
indicación de apnea del sueño de tirzepatida. Son las explicaciones obvias y
encajan en el tiempo, pero **Open Payments no registra indicaciones** y este
archivo no puede probarlo. Las categorías se llaman por la especialidad que
recibe el pago, nunca por la indicación. Ver "Qué me haría cambiar de opinión".

## El gráfico

`figures/g6_movimiento.png` · `figures/g6_movimiento.en.png`

Barras de cambio desde cero entre 2023 y 2025, con los dos frentes arriba: el de
Novo y el de Lilly, uno casi vacío en la compañía contraria. Lilly tiene una sola
barra negativa —endocrinología— y Novo ninguna. La comparación con
`figures/g5_convergencia.png`, que muestra el mismo período en porcentaje, es el
punto del corte: la misma realidad parece convergencia o divergencia según la
unidad.

## Qué es dato y qué es elección mía

| Elemento | Tipo | Fuente / Decisión |
|---|---|---|
| Gasto por año, compañía y perfil | dato | `analysis/corte-04_convergencia.py` |
| Producto asociado a cada pago | dato | `Name_of_Drug_..._1..5` |
| 2023 como año pivote | elección | del corte: es el pico de divergencia según el ataque 08 |
| Dólares absolutos como unidad líder | elección | **D-005** — el % converge y los USD divergen; el corte muestra ambos |
| Agrupar cardio + nefro + gastro/hepato | elección | **D-009**, que reabrió D-008 |
| Agrupar neumo + sueño + cuidados críticos | elección | **D-011**, que reabrió D-009; se evalúa después de NP/PA |
| Los nombres "emergentes" y "respiratorio y sueño" | **interpretación** | mías, declaradas en D-009 y D-011: el dato dice a qué especialidad se paga, no por qué indicación |
| Ventana, entidades, productos, prorrateo | elección | **D-001** · **D-002** · **D-003** · **D-004** |

## Números

Todos salen de `analysis/corte-04_convergencia.py` →
`findings/cache/corte-04_convergencia.json`.

**Movimiento entre 2023 y 2025, en USD millones**

| Perfil | Lilly 2023 → 2025 | Δ | Novo 2023 → 2025 | Δ |
|---|---|---|---|---|
| Cardio/nefro/gastro | 0,05 → 0,45 | +0,39 | 0,96 → 7,39 | **+6,43** |
| Neumo/sueño/críticos | 0,01 → 1,39 | **+1,38** | 0,03 → 0,04 | +0,01 |
| Endocrinología | 7,21 → 5,36 | **−1,85** | 2,83 → 7,08 | +4,25 |
| Atención primaria | 3,69 → 7,05 | **+3,37** | 4,82 → 7,18 | +2,35 |
| Enfermería y asistentes | 2,58 → 2,70 | +0,13 | 3,82 → 5,91 | +2,09 |
| Medicina de obesidad | 0,00 → 0,48 | +0,48 | 0,19 → 0,41 | +0,21 |
| Resto | 0,42 → 1,87 | +1,45 | 0,46 → 0,86 | +0,40 |

*(Las cifras de atención primaria y de "resto" cambiaron respecto de la primera
versión del corte porque **D-011** movió a su categoría la medicina del sueño
—que estaba repartida entre las dos— y el bloque respiratorio completo.)*

**El frente nuevo, por producto** (gasto a cardiólogos, nefrólogos y
gastroenterólogos)

| Producto | Compañía | 2023 | 2025 | Total del período |
|---|---|---|---|---|
| Wegovy | Novo | 0,15 | **4,35** | 5,33 |
| Ozempic | Novo | 0,75 | **2,87** | 7,80 |
| Zepbound | Lilly | 0,00 | 0,41 | 0,64 |
| Rybelsus | Novo | 0,06 | 0,04 | 1,06 |
| Mounjaro | Lilly | 0,05 | 0,03 | 0,27 |

Acumulado del período en esas especialidades: **Novo USD 14,74M · Lilly USD
1,46M**, sobre 16.714 profesionales.

**El detalle interno** (ambas compañías, USD millones)

| | 2021 | 2023 | 2025 | Total | Profesionales |
|---|---|---|---|---|---|
| Cardiología | 2,04 | 0,87 | 4,71 | 12,43 | 9.806 |
| Gastro/hepatología | 0,05 | 0,09 | 2,19 | 2,62 | 3.815 |
| Nefrología | 0,04 | 0,05 | 0,94 | 1,15 | 3.093 |

**El otro frente** — neumonología, medicina del sueño y cuidados críticos, en
USD miles (`analysis/ataque-11_frente-respiratorio.py`)

| Sub-bloque | Lilly 2023 | Lilly 2024 | Lilly 2025 | Novo 2025 |
|---|---|---|---|---|
| Medicina del sueño | 5 | 70 | **726** | 21 |
| Cuidados críticos | 2 | 1 | **343** | 7 |
| Neumonología | 7 | 58 | **320** | 13 |

Los tres saltan el mismo año, en la misma compañía y con el mismo producto:
**Zepbound aporta USD 1,373M de los 1,388M de Lilly en 2025 (98,9%)**. La
amplitud también cambia de escala: los profesionales del bloque en Lilly pasan de
171 en 2023 y 196 en 2024 a **1.523 en 2025**.

## Intenté matarlo

**25 ataques con test corrido.** Sobre el movimiento y el frente de Novo: 3
estructurales y 11 sobre las hipótesis (H2 11/11 · H1 9/11). Sobre el frente de
Lilly, que llegó con D-011: 11 con veredicto y 3 descriptivos (H3 10/11 · H4
10/11). Scripts: `analysis/ataque-09_frente-nuevo.py` ·
`ataque-10_robustez-convergencia.py` · `ataque-11_frente-respiratorio.py`.

- **H1**: entre el pivote y 2025, Lilly redujo su gasto en endocrinología y Novo
  lo aumentó.
- **H2**: Novo destina mucho más que Lilly al grupo emergente.
- **H3**: el gasto de Lilly en el bloque respiratorio en 2025 es al menos 10x el
  de 2023.
- **H4**: en 2025 Lilly destina al bloque al menos 5x lo de Novo.

### El ataque crítico: ¿el frente nuevo es nuevo, o es reetiquetado? (pasa)

El corte 03 encontró que un 3,70% de los profesionales cambia de especialidad
declarada entre años. Si los "cardiólogos de 2025" fueran los mismos de antes con
otra etiqueta, el frente no existiría. Clasificando cada profesional del grupo
emergente en 2025 por su historia previa:

| Origen | Profesionales | USD 2025 | % del gasto |
|---|---|---|---|
| Ya estaba, **misma etiqueta** | 25.111 | 5,94M | **75,9%** |
| **Nuevo** en el dataset | 10.679 | 1,81M | 23,0% |
| Ya estaba, **reetiquetado** | 535 | 0,06M | **0,7%** |
| Ya estaba, etiqueta mixta | 500 | 0,03M | 0,4% |

**El reetiquetado es el 0,7% del gasto.** Y del crecimiento 2023→2025, USD 5,08M
de ~6,4M vienen de profesionales que ya estaban declarados en esas
especialidades. Lo nuevo no es la etiqueta: es que esos cardiólogos empezaron a
recibir pagos por GLP-1. Los 535 reetiquetados venían de primaria (135), resto
(27) y endocrinología (4) — cifras irrelevantes.

### Familia B — sensibilidad a mis decisiones (6/6 sobrevive)

| Ataque | Resultado |
|---|---|
| B1 D-009 alt: sólo cardiología como bloque | ✓ H1 ✓ H2 |
| B1 D-009 alt: cardiología / nefrología / gastro por separado | ✓ H1 ✓ H2 en las tres |
| B2 D-004 alt: fila entera, sin prorratear | ✓ H1 ✓ H2 (Novo 7,45M vs Lilly 0,47M) |
| B3 D-002 alt: sólo entidad operativa US | ✓ H1 ✓ H2 (Novo 7,36M vs Lilly 0,44M) |

La partición de D-009 no fabrica nada: cualquiera de las tres especialidades por
separado da el mismo resultado.

### Familia C — explicaciones alternativas

| Ataque | Resultado |
|---|---|
| C1 normalizar por escala | ✓ — ver abajo |
| C2 pivote 2021 | **✗ H1** — se invierte (Lilly +2,32M, Novo −3,52M) |
| C2 pivote 2022 | **✗ H1** — ambas bajan (Lilly −1,65M, Novo −4,25M) |
| C2 pivote 2024 | ✓ H1 ✓ H2 |
| C3 sólo contacto de campo | ✓ H1 ✓ H2 (Novo 1,36M vs Lilly 0,08M) |
| C3b sólo el grupo "voz" | ✓ H1 ✓ H2 (Novo 6,03M vs Lilly 0,37M) |

**C1 descarta el efecto de escala y de paso afila el hallazgo.** El gasto total de
Novo creció más que el de Lilly, así que "creció en todo" podía ser aritmética.
Normalizando cada delta por el crecimiento total de su compañía:

| Compañía | Categoría | % del crecimiento total |
|---|---|---|
| Novo | **Emergentes** | **+40,8%** |
| Novo | Endocrinología | +27,0% |
| Lilly | **Atención primaria** | **+63,1%** |
| Lilly | Resto | +27,1% |
| Lilly | **Respiratorio y sueño** | **+25,7%** |
| Lilly | **Endocrinología** | **−34,6%** |

No es escala: la **composición** del crecimiento es distinta. Cuatro de cada diez
dólares nuevos de Novo fueron al frente emergente; casi dos de cada tres dólares
nuevos de Lilly fueron a atención primaria y uno de cada cuatro al bloque
respiratorio, financiados en parte por el recorte en endocrinología.

**C2 mató H1 en dos de tres pivotes, y eso reformula el hallazgo.** Con 2021 como
base, Novo *bajó* en endocrinología y Lilly *subió*. La serie de Novo tiene forma
de U (10,60M → 2,83M → 7,08M), así que el corte describe una **reversión desde el
piso de 2023**, no una tendencia del período. El pivote 2023 no es arbitrario —es
el pico de divergencia que encontró el ataque 08— pero elegirlo determina el
signo, y eso queda declarado.

**C3 es la primera vez en el caso que un hallazgo sobrevive en las dos mitades.**
Los cortes 02 y 03 tenían su diferencia entre compañías concentrada en los pagos
de "voz". Acá no: el frente emergente aparece también en contacto de campo (Novo
1,36M contra Lilly 0,08M). Es un movimiento comercial completo, no un programa de
disertantes.

### El frente de Lilly, atacado aparte (ataque 11)

**H3 sobrevivió 10/11 · H4 10/11.** Vigente: Lilly 0,013M → 1,388M (**106x**),
Novo 0,039M en 2025 (**dominio 36x**).

**El ataque crítico, otra vez el reetiquetado** — clasificando cada profesional
del bloque en 2025 por su historia previa:

| Origen | Profesionales | USD 2025 | % del gasto |
|---|---|---|---|
| **Nuevo** en el dataset | 1.342 | 1,164M | **81,5%** |
| Ya estaba, misma etiqueta | 289 | 0,193M | 13,5% |
| Ya estaba, **reetiquetado** | 112 | 0,068M | **4,8%** |
| Ya estaba, etiqueta mixta | 17 | 0,002M | 0,2% |

Los 112 reetiquetados venían de primaria (72) y NP/PA (30). **Y el contraste con
el frente de Novo es el hallazgo secundario:** aquel era 75,9% gente que ya
estaba con la misma etiqueta; éste es 81,5% profesionales que **nunca habían
recibido un pago por GLP-1**. Novo empezó a pagarle a cardiólogos que ya estaban
en el registro; Lilly trajo gente nueva.

| Ataque | Resultado |
|---|---|
| A2 taxonomía: ¿"Sleep Medicine" es un valor NUCC nuevo? | los cinco valores existen desde 2021 — **no es artefacto de taxonomía** |
| A3 sin registros disputados | ✓ H3 ✓ H4 (idéntico) |
| A4 pagos reales, ponderando por `Number_of_Payments` | ✓ H3 ✓ H4 (idéntico) |
| B1 D-011 alt: sueño / neumo / críticos por separado | ✓ H3 ✓ H4 en las tres (157x · 46x · 169x) |
| B2 D-011 alt: el bloque antes de NP/PA (la alternativa rechazada) | ✓ H3 ✓ H4 (102x) |
| B3 D-004 alt: fila entera, sin prorratear | ✓ H3 ✓ H4 (96x) |
| B4 D-002 alt: sólo entidad operativa US | ✓ H3 ✓ H4 (120x) |
| C1 sin el 1% de pagos más caros | ✓ H3 ✓ H4 (63x · dominio 26x) |
| C2 sólo contacto de campo | **✗ H3 ✗ H4** — 8x y dominio 4,4x |
| C2b sólo el grupo "voz" | ✓ H3 ✓ H4 (0 → 1,286M · dominio 82x) |

**B1 es más fuerte que en D-009:** los tres sub-bloques aguantan por separado, así
que la partición no fabrica el hallazgo. En D-009 aislar cardiología lo
fragmentaba.

**C2 es el único fallo y marca el límite del hallazgo.** En contacto de campo el
frente crece 8x (contra el umbral de 10) y el dominio cae a 4,4x (contra 5):
rozan el corte, así que la lectura honesta es que en campo el frente es **débil,
no inexistente**. En voz, en cambio, va de cero a 1,286M sobre **41
profesionales**. **Esto rompe la simetría con el frente de Novo**, que sí
sobrevive en las dos mitades: el de Lilly es, por ahora, un programa de
disertantes.

**Lo que no se pudo testear y se declara:** con 2025 como último año disponible,
**un frente y un pico de lanzamiento son indistinguibles**. El ataque lo deja
anotado como pendiente en vez de declararlo sobreviviente.

## Qué me haría cambiar de opinión

- **Que el frente de Lilly sea un pico de lanzamiento.** Es la hipótesis viva
  que dejó D-011 y el único test que el ataque 11 no pudo correr: sube un solo
  año. Si PY2026 lo muestra volviendo a los valores de 2023-2024, la categoría
  queda describiendo un año y no un frente.
- **Que el frente de Lilly siga siendo sólo voz.** Hoy 1,286M de 1,388M son
  honorarios de disertante y consultoría sobre 41 profesionales. Si en PY2026 no
  aparece en contacto de campo, es un programa de opinión y no un movimiento
  comercial, y el paralelo con el frente de Novo deja de valer.
- **Que el pivote deje de sostenerse.** Es la debilidad confirmada del corte:
  H1 vale desde 2023 y se invierte con base 2021. Si PY2026 muestra a Novo
  bajando de nuevo en endocrinología, la lectura correcta pasa a ser "oscilación"
  y no "reversión".
- Ya **no** me haría cambiar de opinión que los cardiólogos sean reetiquetados:
  quedó descartado (0,7% del gasto). Ni la escala: normalizando por el
  crecimiento de cada compañía, la composición sigue siendo distinta. Ni la
  partición de D-009: las tres especialidades por separado dan lo mismo.
- **Sobre la causa:** la coincidencia temporal con las nuevas indicaciones de
  semaglutida es fuerte, pero probarla exige una fuente externa — el calendario
  de aprobaciones de la FDA. Con Open Payments solo, "Novo paga más a
  cardiólogos desde 2024" es lo máximo que se puede afirmar. Lo mismo, palabra
  por palabra, para "Lilly paga más a neumonólogos y especialistas del sueño
  desde 2025": la indicación de apnea es la explicación obvia y **no está en el
  dato**.
- Ya **no** me haría cambiar de opinión que el frente de Lilly sea reetiquetado
  (4,8% del gasto), ni que sea un artefacto de la taxonomía (los cinco valores
  NUCC existen desde 2021), ni que dependa de la partición de D-011 (los tres
  sub-bloques aguantan solos).
- Que CMS publique un refresh que reexprese algún año de la ventana.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP descargados el
  2026-08-25; sha256 en `scripts/checksums.txt`.
- Reconciliación en `findings/checks.md`: 36 comparaciones, Δ = 0,00%.
- **Alcance del check:** cubre el universo de General Payments y el volumen de
  filas de Novo y Lilly. El reparto por especialidad y producto es cálculo propio
  reproducible bajo D-002/D-003/D-004/D-009/D-011; CMS no publica agregados por
  especialidad contra los cuales cerrarlo.
