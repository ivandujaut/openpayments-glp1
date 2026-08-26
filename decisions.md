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
6. ~~**Agrupación de especialidades**~~ → resuelta en **D-008** (cinco
   categorías con prioridad explícita; el tipo manda en NP/PA).
   *(Fuera de esta cola original se resolvieron: **D-006**, agrupación de
   naturalezas de pago, tras el red-team del corte 01; y **D-007**, métrica de
   concentración por receptor, al abrir el corte 02.)*
7. ~~**Dólares nominales vs. deflactados.**~~ → resuelta en **D-010**
   (nominales, con el punto de quiebre publicado).
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

## D-007 — Concentración del gasto: top 100 como métrica, Gini como control  (2026-08-25)
- **Decisión:** la concentración del gasto entre profesionales receptores se mide
  con el **porcentaje que recibe el top 100 de cada compañía**, y se controla con
  el **índice de Gini** sobre la distribución completa. El receptor es
  `Covered_Recipient_Profile_ID`; los pagos sin ese ID quedan afuera.

  ```
             red HCPs   top 100   Gini
  Lilly       152.493     35,6%   0,8846
  Novo        209.450     20,4%   0,8549
  ```

- **Por qué el top 100 y no el top 1%:** las redes tienen tamaños muy distintos.
  El 1% de Lilly son 1.525 profesionales y el de Novo 2.095, así que esa métrica
  **mezcla concentración con alcance**: parte de la brecha sería sólo que Novo
  reparte entre más gente. El top 100 compara a las mismas cien personas en las
  dos compañías, que es la comparación honesta.

- **El N es arbitrario, y por eso se verificó antes de elegirlo.** Porcentaje del
  gasto al top N:

  ```
          top 10  top 50  top 100  top 500  top 1000
  Lilly      5,2    21,1     35,6     72,2      73,6
  Novo       2,8    11,8     20,4     54,2      62,8
  ```

  Lilly concentra más en los cinco cortes. El hallazgo no depende de N; se
  publica el top 100 por legibilidad, no porque sea el único que funciona.

- **Exclusión documentada:** los hospitales docentes no tienen
  `Covered_Recipient_Profile_ID` y quedan fuera de toda métrica de concentración.
  En GLP-1 son **43 pagos y USD 75.300** (0,04% del total): la exclusión es
  inocua, pero se declara para que no se confunda con un filtro deliberado.

- **Alternativas rechazadas:**
  - *Cuota del top 1% de cada red* (Lilly 74,3% vs. Novo 64,9%). Es la métrica
    más citada en la literatura, pero acá confunde dos cosas distintas. Se
    reporta en el finding como dato secundario, nunca como titular.
  - *Sólo Gini.* Sin umbrales arbitrarios y sensible a toda la curva, pero una
    brecha de 0,8846 contra 0,8549 no comunica nada a un lector general. Queda
    como control de robustez, que es donde rinde.

- **Qué la invalidaría:**
  - Que las redes se emparejen en tamaño: ahí el top 1% dejaría de estar sesgado
    y sería preferible por comparabilidad con la literatura.
  - Que aparezca concentración a nivel entidad y no persona (por ejemplo, muchos
    profesionales de una misma institución), que el `Profile_ID` no captura.
  - Que los hospitales docentes pasen a pesar en GLP-1: hoy son 0,04%.

- **Scripts afectados:** `analysis/corte-02_concentracion.py`,
  `charts/g3_concentracion.py`, `findings/corte-02_concentracion.md`.
- **Estado:** vigente

## D-008 — Agrupación de especialidades: cinco categorías, el tipo manda en NP/PA  (2026-08-25)
- **Decisión:** `Covered_Recipient_Specialty_1` se agrupa en cinco categorías,
  evaluadas **en este orden** (la primera que matchea gana):

  ```
  1. endocrinología       especialidad contiene 'endocrin'
  2. medicina de obesidad especialidad contiene 'obesity medicine'
  3. NP/PA                nivel 1 = 'Physician Assistants & Advanced Practice
                          Nursing Providers'
  4. primaria (médico)    Family Medicine · General Practice · Internal Medicine
                          sin subespecialidad
  5. resto                todo lo demás
  ```

  La taxonomía de CMS es NUCC jerárquica de dos o tres niveles separados por `|`
  (340 valores distintos en la ventana). El nivel 1 es tipo de proveedor; los
  niveles 2 y 3, la especialidad.

- **La regla de prioridad es la decisión, y no es neutral.** "NP/PA" es un tipo
  de proveedor mientras "endocrinología" y "primaria" son especialidades: un
  enfermero de Family Medicine podría caer en dos categorías. Se elige que el
  **tipo mande**, así que ese caso cuenta como NP/PA. Eso mueve **USD 18,21M**
  (NP/PA con subespecialidad Family, Primary Care o Adult Health) que en otra
  regla serían "primaria". Sin esa regla escrita, dos implementaciones del mismo
  criterio darían números distintos.

- **Endocrinología no genera conflicto:** es prácticamente exclusiva de médicos
  (247.067 pagos de `Allopathic & Osteopathic Physicians` contra 3 de
  `Nursing Service Providers`). La prioridad 1 no le quita nada a nadie.

- **Por qué la especialidad y no el tipo de proveedor como eje principal:** el
  tipo casi no separa a las compañías (Novo destina 78,1% a médicos, Lilly
  83,8%), mientras la especialidad sí: **endocrinología es el 43,6% del gasto de
  Lilly contra el 31,5% del de Novo**, doce puntos de diferencia.

- **El dato que la agrupación deja ver:** 5.367 endocrinólogos reciben USD
  65,09M y 120.145 NP/PA reciben USD 35,24M. Son **USD 12.128 por endocrinólogo
  contra USD 293 por NP/PA**, un factor de 40.

- **Alternativas rechazadas:**
  - *Dos dimensiones cruzadas* (tipo × especialidad). Es la correcta desde el
    punto de vista lógico: cada fila cae en una sola celda y no hace falta regla
    de prioridad. Se rechaza por costo de lectura — 8 a 10 celdas vuelven la
    figura densa para lo que agrega, dado que endocrinología ya no se solapa. Si
    un corte futuro necesita ver "NP/PA de primaria" como grupo propio, esta
    decisión debe reabrirse.
  - *Sólo especialidad clínica*, ignorando el tipo. Más limpio conceptualmente,
    pero pierde el canal NP/PA, que es donde Novo más se diferencia (21,8% de su
    gasto contra 16,0% de Lilly) y que vale 4x menos por cabeza.

- **Qué la invalidaría:**
  - Que aparezcan NP/PA con especialidad de endocrinología en volumen: hoy son
    3 pagos y la prioridad 1 los mandaría a endocrinología, no a NP/PA.
  - Que CMS cambie la taxonomía NUCC o su formato jerárquico entre años (los
    cinco años actuales comparten esquema; verificado en la carga).
  - Que el caso pase a preguntar por canal de promoción y no por perfil clínico:
    ahí el tipo de proveedor debería ser el eje y no el desempate.

- **Scripts afectados:** `src/vistas.py` (la columna `especialidad` vive acá),
  `analysis/corte-03_especialidades.py`, `charts/g4_especialidades.py`.
- **Estado:** **superada por D-009** (2026-08-25). El texto queda intacto: la
  historia no se edita. Lo que cambia es que "resto" se parte para dejar ver las
  especialidades emergentes; las otras cuatro categorías y la regla de prioridad
  siguen exactamente igual.

## D-009 — Reapertura de D-008: sacar las especialidades emergentes de "resto"  (2026-08-25)
- **Reabre:** **D-008**, que queda superada. Las cuatro primeras categorías y la
  regla de prioridad **no cambian**; lo único que cambia es que la categoría
  residual se parte en dos.
- **Decisión:** a las cinco categorías de D-008 se les agrega una sexta,
  evaluada **después** de endocrinología y medicina de obesidad y **antes** de
  NP/PA:

  ```
  1. endocrinología          especialidad contiene 'endocrin'
  2. medicina de obesidad    especialidad contiene 'obesity medicine'
  3. emergentes              contiene 'cardio' · 'nephro' · 'gastroenter' · 'hepatol'
  4. NP/PA                   nivel 1 = 'Physician Assistants & Advanced Practice…'
  5. primaria (médico)       Family Medicine · General Practice · Internal Medicine
                             sin subespecialidad
  6. resto                   todo lo demás
  ```

- **Por qué se reabre:** "resto" dejó de ser residual. Contiene tres
  especialidades que crecen juntas y fuerte, y esconderlas impedía nombrar el
  hallazgo del corte 04.

  ```
  bloque             2021   2023   2025   total   profesionales
  cardiología        2,04   0,87   4,71   12,43M          9.806
  gastro/hepatología 0,05   0,09   2,19    2,62M          3.815
  nefrología         0,04   0,05   0,94    1,15M          3.093
  ```

  Juntas pasan de **3,7% del gasto en 2023 a 16,3% en 2025**. Con la partición,
  "resto" cae de USD 24,41M a 8,21M y deja de mezclar una tendencia con un cajón.

- **Por qué las tres juntas y no separadas:** crecen en los mismos años, con los
  mismos dos productos y casi enteramente de una sola compañía — en 2025, Novo
  7,39M contra Lilly 0,45M, pagados con Wegovy (4,35M) y Ozempic (2,87M). Es un
  fenómeno único, no tres coincidencias. Separarlas lo fragmenta en tres cifras
  chicas que ninguna sostiene el hallazgo sola.

- **El nombre es una interpretación mía y hay que decirlo.** El dato dice que
  crece el pago a cardiólogos, nefrólogos y gastroenterólogos. Que sea **por** las
  nuevas indicaciones cardiovascular y renal de semaglutida es una hipótesis
  plausible y **no testeada con este archivo**: Open Payments no registra
  indicaciones. Todo finding que use la categoría debe llamarla por lo que es
  —un grupo de especialidades— y presentar la causa como hipótesis.

- **Alternativas rechazadas:**
  - *Sólo cardiología como categoría propia.* Más conservador y sin
    interpretación: cardiología es una especialidad reconocible y pesa 12,43M
    contra 3,77M de las otras dos. Se rechaza porque deja invisibles a
    nefrología (crece 20x) y gastro/hepatología (44x), que son la parte más
    dinámica del fenómeno.
  - *No reabrir, y describir el contenido de "resto" en el texto del corte 04.*
    Evita tocar los cortes ya cerrados, pero publica un desglose sin decisión que
    lo respalde: exactamente el bug de proceso que hubo que corregir en D-006.

- **Qué la invalidaría:**
  - Que aparezca una cuarta especialidad con el mismo patrón: la categoría se
    volvería elástica y habría que decidir si se agrega o si el criterio cambia.
  - Que se demuestre que el crecimiento en cardiología no tiene relación con las
    nuevas indicaciones — no invalidaría la partición, pero sí el nombre.
  - Que el caso pase a preguntar por especialidades individuales y no por
    bloques.

- **Impacto en lo ya publicado:** el corte 03 y su red-team se recorren con la
  categoría nueva. El hallazgo central del corte 03 (endocrinología contra NP/PA)
  no se toca: ninguna de las tres especialidades emergentes estaba en esas
  categorías.

- **Scripts afectados:** `src/vistas.py`, `analysis/corte-03_especialidades.py`,
  `analysis/ataque-08_robustez-especialidades.py`, `charts/g4_especialidades.py`,
  `analysis/corte-04_*`, `findings/corte-03_especialidades.md`.
- **Estado:** vigente

## D-010 — Dólares nominales, con el punto de quiebre publicado  (2026-08-25)
- **Decisión:** todas las cifras del caso van en **USD corrientes, sin
  deflactar**, y la sección de límites lo declara con esas palabras. Donde el
  deflactor puede cambiar el signo de una afirmación, el finding publica **el
  deflactor que la anula** en vez de resolverla con una fuente externa.

- **La sensibilidad, calculada antes de decidir** — deflactor que invertiría
  cada afirmación temporal del caso:

  ```
  afirmación                              se anula con deflactor
  Novo gastó más en 2025 que en 2021        1,174   ← plausible
  Lilly creció 224% entre 2021 y 2025       3,242
  Lilly redujo endocrinología 2023→2025     ya es negativo; deflactar lo refuerza
  Novo aumentó endocrinología 2023→2025     2,505
  Novo creció en el frente emergente        7,703
  ```

  **Una sola afirmación es frágil**, y es secundaria: el crecimiento nominal de
  Novo (+17,4% entre 2021 y 2025) se anula con 17,4% de inflación acumulada en
  cuatro años, que está dentro del rango del período. Las otras cuatro
  necesitarían deflactores de 2,5x a 7,7x: imposibles.

- **Consecuencia operativa:** el finding del corte 01 y la sección de límites del
  writeup dicen que en términos reales el gasto de Novo entre 2021 y 2025 es
  **aproximadamente plano, no creciente**. Con eso, la afirmación deja de ser
  refutable: se declara su propia fragilidad.

- **Por qué las comparaciones centrales no se ven afectadas:** el caso compara
  Novo contra Lilly **dentro del mismo año**, donde el deflactor se cancela por
  construcción. Las comparaciones temporales que sostienen hallazgos tienen
  magnitudes que lo empequeñecen (el frente emergente crece 7,7x en dos años).

- **Alternativas rechazadas:**
  - *Nominal a secas, sin nota.* Más simple, pero deja en pie la afirmación
    frágil sin señalarla — en un caso que publica 59 ataques, esconder la única
    debilidad barata de encontrar sería incoherente.
  - *Deflactar todo.* No cambia ninguna conclusión salvo la de Novo, y cuesta:
    traer el CPI **a mano** (BLS bloquea automatización y FRED no sirve el CSV
    por la vía de `/browse`), decidir qué índice usar — CPI-U general, PCE o un
    índice de precios médicos, que son tres decisiones distintas con resultados
    distintos — y rehacer los cuatro cortes con sus red-teams. Precio alto por un
    cambio que se puede declarar en una línea.

- **Qué la invalidaría:**
  - Que el caso incorpore una serie más larga: en diez años el deflactor deja de
    ser despreciable en todas las comparaciones, no sólo en una.
  - Que aparezca una afirmación nueva con punto de quiebre menor a ~1,20.
  - Que el caso pase a comparar contra magnitudes externas en dólares
    (facturación, mercado), donde la unidad tiene que ser la misma que la fuente.

- **Nota de sourcing:** si alguna vez se deflacta, el índice **no es obvio**.
  CPI-U mide precios al consumidor; el gasto promocional farmacéutico no sigue
  esa canasta. Elegir índice sería su propia decisión, no un detalle técnico.

- **Scripts afectados:** ninguno — es una decisión sobre cómo se declaran las
  cifras, no sobre cómo se calculan. Afecta `findings/corte-01_carrera.md` (nota
  de sensibilidad) y la sección de límites del writeup.
- **Estado:** vigente
