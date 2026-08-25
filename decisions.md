# Registro de decisiones — la materia prima de "qué es dato y qué es elección mía"

Formato: entradas D-NNN inmutables. Reabrir = entrada nueva que referencia la
vieja. Toda decisión se registra vía `/decidir` ANTES de implementarse.

## Pendientes (cola para la primera sesión, en orden; se deciden mirando el dato real)

1. ~~**Ventana temporal de la serie**~~ → resuelta en **D-001** (2021–2025).
2. ~~**Regla de entidades**~~ → resuelta en **D-002** (lista de IDs, grupo
   corporativo completo, con check contra `Submitting`).
3. ~~**Lista de productos GLP-1 y matching**~~ → resuelta en **D-003** (nueve
   productos, nombre normalizado como clave, NDC como check).
4. ~~**Regla de asignación en pagos multi-producto**~~ → resuelta en **D-004**
   (prorrateo en partes iguales entre todos los productos declarados).
5. ~~**Unidad primaria por corte**~~ → resuelta en **D-005** (ambas siempre;
   cada finding declara su líder. En el corte 01 el hallazgo es la divergencia).
6. **Agrupación de especialidades**: qué taxonomías caen en "endocrinología",
   "atención primaria", "NP/PA" y "resto".
   *(La agrupación de naturalezas de pago, que no estaba en esta cola, se
   resolvió en **D-006** tras el red-team del corte 01.)*
7. **Dólares nominales vs. deflactados.**
8. **Filas con `Date_of_Payment` corrupta**: 75 filas de PY2024 traen
   `11/30/0002` en el CSV de CMS (USD 307.571,82; fabricantes de dispositivos,
   ninguno Novo ni Lilly). El error es de la fuente, no de la conversión.
   ¿Se excluyen de todo corte, se excluyen solo de los cortes temporales, o se
   dejan? Afecta totales anuales de control y cualquier agregación por trimestre.

## Decisiones

## D-001 — Ventana temporal de la serie: 2021–2025  (2026-08-25)
- **Decisión:** la serie del caso son los Program Years 2021 a 2025 inclusive.
  Todo corte, figura y check opera sobre esa ventana; los años anteriores no se
  descargan ni se citan.
- **Alternativas rechazadas:**
  - *Serie histórica completa con panel partido en 2021.* Rechazada por el costo
    de arrastrar un asterisco permanente en cada figura y por reescribir todo
    corte para operar en dos paneles, sin ganancia para la pregunta del caso.
  - *2019–2025 con la ruptura marcada.* Rechazada por lo mismo en menor escala:
    agrega dos años de contexto pre-Wegovy a cambio de meter la ruptura NPP
    adentro de la serie.
- **Motivo (mirando el dato, no de memoria):** PY2021 es el primer año en que
  los non-physician practitioners son covered recipients. Aparecen de golpe con
  3.578.840 filas (31% del año) y llegan a 5.966.664 (37%) en 2025. Cruzar ese
  corte mezcla un cambio legal con un cambio de mercado, y lo hace justo sobre
  el segmento que más pesa en GLP-1: NP y PA son prescriptores centrales de la
  clase. La ventana elegida además contiene la carrera entera — Wegovy aparece
  en 2021 (35.904 filas), Mounjaro en 2022 (139.760), Zepbound en 2023 (6.867,
  186.426 para 2025) — y el traspaso interno de Lilly, con Trulicity cayendo de
  153.190 a 74. No se pierde nada de la historia que el caso quiere contar.
  (Los conteos por producto son de una consulta ILIKE cruda exploratoria, NO la
  regla de matching: esa es D-003.)
- **Qué la invalidaría:**
  - Que el caso pase a preguntar por la era Trulicity/Victoza, que queda afuera.
  - Que se demuestre que la incorporación de NPP en 2021 fue marginal en GLP-1,
    lo que quitaría el motivo principal del corte.
  - Un refresh de CMS que reexprese los años previos con la definición nueva de
    covered recipient, eliminando la ruptura.
- **Scripts afectados:** `scripts/01_descargar.py` (dict `URLS`, ya restringido a
  2021–2025), `scripts/04_checks.py`, todo `analysis/corte-NN_*.py`.
- **Estado:** vigente

## D-002 — Regla de entidades: Novo y Lilly por lista de IDs  (2026-08-25)
- **Decisión:** la pertenencia a "Novo" o "Lilly" se define por una lista
  explícita de `Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID`,
  con alcance de **grupo corporativo completo**. Nunca por coincidencia de texto
  sobre el nombre.

  ```
  NOVO  = {100000000144 Novo Nordisk Inc
           100000000163 Novo Nordisk AS
           100000000155 Novo Nordisk Health Care AG
           100000196804 Novo Nordisk US R&D / Research Center Seattle}
  LILLY = {100000000066 Lilly USA, LLC
           100000000088 Eli Lilly and Company
           100000000331 Eli Lilly Export S.A. Puerto Rico Branch}
  ```

  Acompaña un **check obligatorio**: filas cuyo
  `Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name` pertenece a
  cualquiera de los dos grupos pero cuyo `Making_Payment_ID` no está en la lista.
  Hoy devuelve 154 filas (USD 1,65M) y debe revisarse ante cada refresh de CMS:
  es el detector de filiales nuevas.

- **Exclusiones deliberadas, con ID para que no se relitiguen:**
  - *Subsidiarias de Lilly con nombre propio*, que el check expone y quedan
    afuera del grupo: `100000005383` Avid Radiopharmaceuticals (113 filas,
    USD 0,28M) y `100000000063` ImClone Systems (41 filas, USD 1,37M). Aporte a
    GLP-1: cero. Se excluyen porque el alcance elegido es el grupo declarado, no
    el árbol societario completo.
  - *Falsos positivos por texto*, que un `ILIKE '%novo%'` capturaría (34.648
    filas ajenas): `100000005413` Novocure Inc., `100000971857` Novocure GmbH,
    `100000010836` Novocure Israel Ltd, `100000196803` PolyNovo North America,
    `100000756812` Novonate Inc, `100000461813` NovoSource LLC. Ninguna tiene
    relación con Novo Nordisk.

- **Alternativas rechazadas:**
  - *Agrupar por `Submitting_Name`.* Consolida las tres entidades Lilly sin
    esfuerzo (Lilly USA declara bajo Eli Lilly and Company en 2.213.056 de sus
    2.214.109 filas) y captura Avid e ImClone, pero el campo **no tiene ID**:
    obliga a matchear texto, con los falsos positivos de arriba. Se conserva
    como eje de verificación, no como clave.
  - *Solo entidad operativa US* (Novo Nordisk Inc / Lilly USA). Rechazada porque
    el caso pregunta por dos compañías. Dejaría afuera USD 70,81M de Novo
    Nordisk AS, casi todos ajenos a GLP-1.

- **Por qué la regla no fabrica el resultado:** filtrando por GLP-1, grupo
  completo vs. solo entidad US da Novo 111,11M vs 110,76M y Lilly 70,78M vs
  70,20M — menos de 1% de diferencia. El hallazgo GLP-1 es robusto a esta
  decisión, y el writeup puede afirmarlo mostrando ambos números.

- **Trampa narrativa que esta decisión deja al descubierto:** el ranking se
  invierte según el recorte. En GLP-1 Novo supera a Lilly (111,11M vs 70,78M);
  en pagos corporativos totales, Lilly supera a Novo (227,82M vs 217,94M).
  Ninguna frase del caso puede decir "X gasta más que Y" sin decir en qué.

- **Qué la invalidaría:**
  - Que CMS reasigne IDs o fusione entidades en un refresh (el check lo detecta).
  - Que aparezca una filial de Novo o Lilly que pague GLP-1 y no esté en la
    lista; hoy el filtro GLP-1 devuelve exactamente cinco entidades, todas
    listadas.
  - Que el caso cambie a preguntar por el árbol societario completo, no por el
    grupo declarado ante CMS: ahí entrarían Avid e ImClone.

- **Scripts afectados:** `src/vistas.py` (las constantes NOVO/LILLY viven acá),
  `scripts/04_checks.py` (el check contra `Submitting`), todo
  `analysis/corte-NN_*.py`.
- **Estado:** vigente

## D-003 — Clase GLP-1 y regla de matching de productos  (2026-08-25)
- **Decisión:** la clase GLP-1 del caso son estos nueve productos, identificados
  por el **nombre normalizado a mayúsculas** en cualquiera de las cinco columnas
  `Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1..5`:

  ```
  NOVO   OZEMPIC          Diabetes  0169-4132-12   semaglutida SC
         RYBELSUS         Diabetes  0169-4303-13   semaglutida oral
         WEGOVY           Obesity   0169-4525-14   semaglutida SC
         SAXENDA          Obesity   0169-2800-15   liraglutida
         VICTOZA          Diabetes  0169-4060-12   liraglutida
         XULTOPHY 100/3.6 Diabetes  0169-2911-15   degludec + liraglutida
  LILLY  MOUNJARO         Diabetes  0002-1506-80   tirzepatida
         ZEPBOUND         Obesity   0002-2457-80   tirzepatida
         TRULICITY        Diabetes  0002-1433-80   dulaglutida
  ```

  **La normalización no es cosmética:** Rybelsus aparece escrito `Rybelsus`
  (1.084.395 menciones) y `RYBELSUS` (350.163). Un match sensible a mayúsculas
  pierde el 24% del producto.

  Acompaña un **check obligatorio**: cada uno de los nueve nombres debe seguir
  teniendo exactamente **un** `Associated_Drug_or_Biological_NDC` distinto, el
  listado arriba. Si un producto pasa a tener dos NDC, o un NDC cambia, hay un
  renombre o una presentación nueva y la lista debe revisarse antes de publicar.

- **"GLP-1" se usa en sentido comercial, no farmacológico.** Tirzepatida
  (Mounjaro, Zepbound) es un agonista **dual GIP/GLP-1**, no un GLP-1 puro. Se
  incluye porque compite en la misma categoría y define el mercado; excluirla
  dejaría a Lilly con un solo producto en declive. El writeup debe decir esto
  explícitamente: es la simplificación más atacable del caso.

- **El área terapéutica clasifica, no incluye.** `Product_Category_or_
  Therapeutic_Area` separa la indicación diabetes vs. obesidad de la misma
  molécula (Ozempic/Wegovy son ambos semaglutida; Mounjaro/Zepbound, tirzepatida)
  y por eso se conserva. **Nunca** se usa como criterio de inclusión: filtrar por
  `Diabetes` metería Jardiance (497.164 menciones, un SGLT2) y toda la línea de
  insulinas.

- **Alternativas rechazadas:**
  - *GLP-1 estricto por mecanismo*, excluyendo tirzepatida. Farmacológicamente
    correcto, pero deja a Lilly con 295.760 menciones contra 3.581.602 de Novo:
    vacía la comparación que el caso plantea.
  - *Solo la generación actual*, excluyendo Victoza, Saxenda, Trulicity y
    Xultophy. Rechazada porque se pierde el traspaso de portafolio de Lilly, con
    Trulicity cayendo de 295.760 menciones a 74 mientras Mounjaro y Zepbound
    crecen: es parte de la historia, no ruido.
  - *NDC como clave, nombre como check.* Sería simétrico con D-002, que usa el
    ID como clave. Se rechaza porque acá el nombre es limpio y estable (nueve
    valores, un NDC cada uno, 100% poblado) y una lista de NDC no se puede
    auditar a simple vista. El NDC queda como verificación.

- **Qué la invalidaría:**
  - Que un producto pase a tener más de un NDC, o que aparezca una presentación
    nueva bajo otro nombre (el check lo detecta).
  - El lanzamiento de un GLP-1 nuevo de Novo o Lilly dentro de la ventana: la
    lista es cerrada y no lo capturaría solo.
  - Que el caso pase a preguntar por farmacología y no por competencia
    comercial: ahí tirzepatida saldría de la clase.

- **Scripts afectados:** `src/vistas.py` (la lista de nueve y sus NDC viven acá),
  `scripts/04_checks.py` (el check nombre↔NDC), todo `analysis/corte-NN_*.py`.
- **Estado:** vigente

## D-004 — Asignación en pagos multi-producto: prorrateo  (2026-08-25)
- **Decisión:** el monto de una fila se divide en **partes iguales entre todos
  los productos declarados** en ella (`Name_of_Drug_..._1..5` no nulos), y a la
  clase GLP-1 le corresponde solo la parte de los productos GLP-1. Una comida de
  USD 15 que declara Ozempic y Jardiance aporta USD 7,50 a GLP-1, no USD 15.

  Resultado con la regla aplicada (2021–2025, USD millones):

  ```
  MOUNJARO  43,58 (Lilly)   ZEPBOUND  17,28 (Lilly)   VICTOZA   0,64 (Novo)
  OZEMPIC   42,22 (Novo)    TRULICITY  8,27 (Lilly)   XULTOPHY  0,01 (Novo)
  RYBELSUS  35,78 (Novo)    SAXENDA    6,60 (Novo)
  WEGOVY    25,81 (Novo)
                          Novo 111,05  ·  Lilly 69,13
  ```

- **Por qué la decisión importa menos de lo que parece, y dónde importa mucho:**
  - Para el corte **Novo vs. Lilly es indiferente**: las co-menciones nunca
    cruzan compañías (Ozempic+Rybelsus, Mounjaro+Zepbound, Mounjaro+Trulicity,
    Saxenda+Wegovy son todas intra-compañía), así que la fila entera va a la
    compañía correcta con cualquier regla. Novo gana en las tres; solo cambia el
    margen (1,73x contando entero, 1,57x prorrateando).
  - Para el **ranking por producto decide el titular**: contando la fila entera
    para cada producto, el #1 es Ozempic (52,57M). Prorrateando, el #1 es
    Mounjaro. Misma data, dos titulares opuestos. **Ninguna figura por producto
    puede publicarse sin declarar esta regla.**

- **Naturaleza de las filas multi-producto:** 1.352.408 filas declaran
  Ozempic+Rybelsus con un monto promedio de USD 15, y 231.959 declaran
  Mounjaro+Zepbound con promedio USD 18. Son comidas en las que el
  representante presenta dos productos, no pagos grandes ambiguos. El 83,8% de
  los dólares GLP-1 está en filas mono-producto, donde no hay nada que asignar.

- **Alternativas rechazadas:**
  - *Fila entera a cada producto mencionado.* Refleja que el pago promocionó
    ambos, pero **duplica dinero**: la suma por producto da 208,24M contra un
    total real de 181,90M (+14,5%), concentrado justo en Ozempic y Rybelsus por
    las 1,35M de comidas compartidas. Los subtotales dejan de ser sumables.
  - *Solo el producto del primer slot.* Simple y sin duplicación, pero descarta
    USD 1,22M de filas donde el GLP-1 aparece en un slot posterior, y castiga a
    Zepbound (17,72 → 14,81, −16%) por un artefacto de orden de carga.
  - *Prorrateo solo entre los GLP-1 de la fila*, atribuyendo la fila entera a la
    clase. Da 181,90M en vez de 180,18M. Rechazada porque sobreestima en las
    filas mixtas: si un pago cubre un GLP-1 y un producto ajeno, no es todo
    gasto GLP-1. La diferencia es USD 1.714.588 (0,94%).

- **Nota de implementación, no cosmética:** en SQL `NULL IN (lista)` devuelve
  NULL, no FALSE. Contar los slots GLP-1 de una fila con
  `(upper(col) IN lista)::INT` anula la suma entera en las 4.739.295 filas que
  tienen algún slot vacío, y el filtro descarta casi todo **en silencio**. Hay
  que envolver en `IS TRUE` (o `coalesce(..., false)`). Este error se cometió al
  explorar D-004 y se detectó sólo porque el resultado no cerraba con los
  conteos de D-003: sin ese control cruzado habría pasado inadvertido.

- **Qué la invalidaría:**
  - Que CMS agregue un campo con el reparto real del monto entre productos: ahí
    el prorrateo deja de ser necesario y pasa a ser incorrecto.
  - Que aparezcan co-menciones que crucen compañías, lo que volvería la regla
    relevante también para el corte Novo vs. Lilly.
  - Que el caso pase a analizar el gasto por evento y no por producto.

- **Scripts afectados:** `src/vistas.py` (la vista GLP-1 aplica el prorrateo),
  todo `analysis/corte-NN_*.py`, toda figura desagregada por producto.
- **Estado:** vigente

## D-005 — Unidad primaria: la divergencia no se resuelve, se muestra  (2026-08-25)
- **Decisión:** dólares y cantidad de pagos se calculan **siempre**, y ningún
  corte subordina una a la otra por defecto. Cada finding **declara en su
  encabezado** cuál lidera su narrativa y por qué. Para el corte 01 (la carrera)
  la unidad líder es **ninguna de las dos por separado: el hallazgo es que se
  contradicen**, y la figura muestra ambas series en paralelo.

- **El dato que fuerza la decisión** — ratio Novo/Lilly por año y unidad:

  ```
  año    en USD              en cantidad de pagos
  2021   4,13x               2,88x
  2022   2,40x               2,37x
  2023   0,94x  ← Lilly      1,58x  ← Novo
  2024   0,87x  ← Lilly      1,37x  ← Novo
  2025   1,50x               1,92x
  ```

  En dólares Lilly pasa al frente en 2023 y 2024. En cantidad de pagos Novo
  lidera los cinco años sin excepción. Elegir una unidad en silencio fabrica un
  titular; son dos preguntas distintas, no dos formas de la misma.

- **Por qué divergen (la razón es estructural, no un artefacto):** el dato tiene
  dos poblaciones con órdenes de magnitud distintos.

  ```
  honorarios de disertante   59% de los dólares ·  2,1% de los pagos
                             Novo USD 2.243/pago · Lilly USD 1.026/pago
  comidas                    35% de los dólares · 96,7% de los pagos
                             ~USD 20/pago en ambas compañías
  ```

  Contar **dólares** mide inversión y lo domina el programa de disertantes, unos
  pocos miles de profesionales de alto perfil. Contar **pagos** mide alcance en
  terreno y lo dominan millones de comidas. La divergencia 2023–2024 aparece
  porque el monto promedio por pago de Novo cae de USD 60,96 a USD 30,86
  mientras Lilly se sostiene entre 52 y 57: Novo mantuvo el volumen de contactos
  y recortó lo caro.

- **Alternativas rechazadas:**
  - *Dólares lidera siempre.* Es la unidad de la prensa y de "gasto
    promocional", pero da el titular "Lilly superó a Novo en 2023-2024"
    ocultando que Novo nunca perdió alcance. El 59% del peso lo ponen 72.563
    pagos sobre 3.377.782.
  - *Cantidad de pagos lidera siempre.* Da el titular "Novo lideró los cinco
    años" y esconde que Lilly invirtió más en 2023-2024. Además hace pesar igual
    una comida de USD 12 y un honorario de USD 50.000.

- **Qué la invalidaría:**
  - Que las dos unidades dejen de contradecirse en toda la ventana: ahí el corte
    01 pierde su hallazgo y la unidad líder pasa a ser una elección de
    conveniencia.
  - Que se demuestre que los honorarios de disertante y las comidas no son
    poblaciones separables, lo que quitaría la explicación estructural.
  - Un corte cuya pregunta sea inequívocamente de una sola unidad (por ejemplo
    "cuántos profesionales alcanzó cada compañía"), donde forzar las dos series
    sería ruido.

- **Consecuencia operativa:** el encabezado de todo finding lleva la unidad
  líder declarada, junto a la fecha de datos y el estado de checks. Un finding
  sin unidad declarada está incompleto.

- **Scripts afectados:** `analysis/corte-01_carrera.py` y todo corte posterior,
  `charts/g1_carrera.py`, `findings/corte-00-plantilla.md` (el encabezado suma
  la unidad líder).
- **Estado:** vigente

## D-006 — Naturalezas de pago: voz del profesional vs. contacto de campo  (2026-08-25)
- **Decisión:** las seis naturalezas que aparecen en GLP-1 se agrupan en dos,
  según **qué compra el pago**:

  ```
  voz    Compensation for services other than consulting (disertante)
         Consulting Fee
         → USD 110,15M en 74.271 pagos · USD 1.483 por pago
  campo  Food and Beverage · Travel and Lodging · Education
         Space rental or facility fees (teaching hospital only)
         → USD 70,04M en 3.303.511 pagos · USD 21 por pago
  ```

  "Voz" compra tiempo y palabra del profesional; "campo" es contacto y logística.
  La partición separa dos poblaciones que difieren en dos órdenes de magnitud
  por pago, no dos etiquetas administrativas de CMS.

- **Origen, que es lo que la vuelve necesaria:** esta separación se implementó
  ANTES de registrarse, en el ataque 03 (C2) del corte 01, con una partición
  distinta y peor: sólo disertante contra todo lo demás. Eso es un bug de
  proceso — la regla dura del caso es que toda decisión analítica pasa por
  `/decidir` antes. Esta entrada lo cierra y corrige la partición.

- **Por qué la partición del ataque estaba mal:** dejaba `Consulting Fee` del
  lado de las comidas. Consultoría cuesta **USD 2.212 por pago**, más que los
  honorarios de disertante (USD 1.466) y 116 veces más que una comida (USD 19).
  Agruparla con las comidas sólo pasaba desapercibido porque es chica (2,1% de
  los dólares); conceptualmente compra exactamente lo mismo que un honorario.

- **El hallazgo del corte 01 NO depende de esta decisión.** Excluyendo el grupo
  "voz", los ratios Novo/Lilly por año son 6,80 · 3,31 · 1,48 · 1,48 · 2,54;
  excluyendo sólo disertante, 7,24 · 3,45 · 1,51 · 1,46 · 2,56; mirando sólo
  comidas, 5,93 · 2,78 · 1,47 · 1,43 · 2,31. **Novo gana los cinco años en las
  tres particiones.** Se eligió la defendible porque no costaba nada.

- **Alternativas rechazadas:**
  - *Disertante vs. resto* (la del ataque). Rechazada por arbitraria: separa por
    etiqueta y no por naturaleza económica del pago, y esconde consultoría entre
    las comidas.
  - *Sin agrupar, las seis por separado.* Máxima transparencia y cero
    interpretación, pero traslada al lector el trabajo de ver que dos poblaciones
    distintas conviven en el agregado, que es justamente el hallazgo del corte 01.
    Las seis siguen reportándose en `findings/cache/corte-01_carrera.json`: la
    agrupación no borra el detalle, lo resume.

- **Qué la invalidaría:**
  - Que aparezca una naturaleza nueva en la ventana y no caiga limpio en ninguno
    de los dos grupos (hoy son exactamente seis).
  - Que `Consulting Fee` deje de comportarse como los honorarios — por ejemplo,
    si su monto típico cayera al orden de las comidas.
  - Que el caso pase a preguntar por las categorías regulatorias de CMS y no por
    la función comercial del pago.

- **Scripts afectados:** `src/vistas.py` (la columna `grupo_naturaleza` vive
  acá), `analysis/corte-01_carrera.py`, `analysis/ataque-03_explicaciones-negocio.py`,
  `charts/g2_disertantes.py`, `findings/corte-01_carrera.md`.
- **Estado:** vigente
