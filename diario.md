# Diario de sesiones

Formato por entrada (una por sesión, al cierre):

## AAAA-MM-DD — <objetivo del día>
- **Se decidió:** (referencias D-NNN o "nada")
- **Se produjo:** (scripts, findings, figuras)
- **Quedó abierto:**
- **Próximo paso concreto:**

---

## 2026-08-25 — arranque del entorno y saneamiento del pipeline

- **Se decidió:** nada. La cola de `decisions.md` sigue intacta: ninguna D-NNN
  registrada, ninguna implementada. Las elecciones de esta sesión fueron de
  layout y entorno, no analíticas — `conectar()` vive en `src/vistas.py` (los
  scripts numerados no son importables), `uv` instalado por Homebrew en vez del
  `curl | sh` de ARRANQUE, rama `main`.
- **Se produjo:**
  - Entorno: `uv` 0.12.5, `uv sync` → `.venv/` + `uv.lock` (21 paquetes).
    Pasos 1 y 2 de ARRANQUE cerrados.
  - Cinco arreglos en el pipeline, todos verificados corriendo:
    `04_checks.py` importaba `scripts.vistas`, módulo inexistente y no
    importable por empezar con dígito → `conectar()` mudado a `src/vistas.py`
    (con bootstrap de `sys.path` en los entry points) · `02_convertir` reventaba
    con `IndexError` si `data/raw` estaba vacío · `checksums.txt` era un log que
    duplicaba líneas y nunca comparaba nada → ahora es manifiesto y corta ante
    mismatch · `conectar()` tiraba traceback crudo sin parquet ·
    `figstyle.guardar()` usaba `bbox_inches="tight"`, que daba PNGs de tamaño
    variable (1376x811, 1390x811) en vez del 1495x886 declarado.
  - `findings/checks.md` creado, con la definición de vigencia de un check que
    la skill `/reconciliar` nombra en su paso 6 pero no definía.
  - Git: `7f4bfc3` (estado inicial) y `6b0dfb2` (`data/` se versiona vacía).
- **Quedó abierto:**
  - `pandas` resolvió a 3.0.5 con el `>=2.2` del pyproject. Decidir si se pinea
    a `<3` o si el primer corte se escribe contra pandas 3.
  - Repo público desde el día uno o privado hasta la pieza 3 (paso 3 de
    ARRANQUE): la pieza 1 promete código abierto en cámara.
  - `URLS` y `OFICIALES` siguen vacíos; sin ellos no hay dato ni reconciliación.
- **Próximo paso concreto:** paso 4 de ARRANQUE — con `/browse`, capturar las
  URLs de los ZIP anuales PY2021–PY2025 en openpaymentsdata.cms.gov y completar
  `URLS` en `scripts/01_descargar.py` con la fecha de captura en comentario.

---

## 2026-08-25 — carga de la serie completa y las primeras cuatro decisiones

- **Se decidió:** D-001 a D-004, todas mirando el dato, ninguna de memoria.
  - **D-001 · ventana temporal 2021–2025.** PY2021 es el primer año con
    non-physician practitioners como covered recipients: entran de golpe con
    3.578.840 filas (31% del año) y llegan al 37% en 2025. Cruzar esa ruptura
    mezcla cambio legal con cambio de mercado, justo sobre el segmento que más
    pesa en GLP-1. La ventana además contiene la carrera entera (Wegovy 2021,
    Mounjaro 2022, Zepbound 2023).
  - **D-002 · entidades por lista de IDs**, grupo corporativo completo, con
    check contra `Submitting`. Un `ILIKE '%novo%'` habría metido 34.648 filas de
    Novocure, PolyNovo y Novonate; y 154 filas que Eli Lilly reporta las paga
    Avid o ImClone, invisibles a cualquier patrón sobre "lilly".
  - **D-003 · nueve productos**, nombre normalizado como clave y NDC como check.
    Rybelsus aparece escrito de dos formas: sin normalizar se pierde el 24%.
    Se incluye tirzepatida (Mounjaro, Zepbound) pese a ser dual GIP/GLP-1:
    queda registrado que "GLP-1" se usa en sentido comercial.
  - **D-004 · prorrateo** en partes iguales entre todos los productos de la
    fila. Es la decisión que más mueve el resultado: contando la fila entera
    para cada producto el #1 es Ozempic (52,57M), prorrateando el #1 es
    Mounjaro. Mismo dato, dos titulares.
- **Se produjo:**
  - Pasos 4 y 5 de ARRANQUE cerrados. `URLS` completo en `01_descargar.py` con
    fecha de captura y el sello de publicación de CMS documentado
    (`P06302026_06032026`, el mismo para los cinco años).
  - Serie completa en `data/parquet/`: 71.245.399 filas, 5 años,
    `Record_ID` único por año, cero nulos en monto/fecha/pagador.
    `scripts/checksums.txt` con los cinco sha256.
  - Esquema real contrastado contra el docstring de `02_convertir_parquet.py`:
    los 19 campos esperados existen con nombre exacto. **91 columnas idénticas
    en los cinco años** — el riesgo de inferencia de tipos por muestreo que se
    había marcado no se materializó.
  - Resultado preliminar con las cuatro reglas aplicadas (USD millones,
    2021–2025): Mounjaro 43,58 · Ozempic 42,22 · Rybelsus 35,78 · Wegovy 25,81 ·
    Zepbound 17,28 · Trulicity 8,27 · Saxenda 6,60. **Novo 111,05 · Lilly 69,13.**
- **Hallazgos que sobreviven a las decisiones (para el writeup):**
  - **El resultado Novo vs. Lilly es robusto a D-002 y a D-004.** El alcance
    societario cambia el total en menos del 1% dentro de GLP-1, y las
    co-menciones de productos nunca cruzan compañías, así que ninguna regla de
    asignación cambia el ganador. Se puede publicar la regla junto con la prueba
    de que el hallazgo no depende de ella.
  - **El ranking se invierte según el recorte.** En GLP-1 Novo supera a Lilly;
    en pagos corporativos totales, Lilly supera a Novo (227,82M vs 217,94M).
    Ninguna frase puede decir "X gasta más que Y" sin decir en qué.
  - **75 filas de PY2024 traen `Date_of_Payment = 0002-11-30`** (USD 307.571,82).
    Verificado contra el CSV crudo: el ZIP de CMS literalmente dice `11/30/0002`.
    El error es de la fuente, no de la conversión. Entró como ítem 8 de la cola.
  - **Un error propio, registrado en D-004 porque es reincidente por diseño:**
    en SQL `NULL IN (lista)` devuelve NULL, no FALSE. Contar slots GLP-1 sin
    envolver en `IS TRUE` anula la suma en 4.739.295 filas y descarta el filtro
    en silencio. Se detectó sólo porque el resultado no cerraba contra los
    conteos de D-003.
- **Quedó abierto:**
  - **`src/vistas.py` sigue sin implementar D-002/D-003/D-004**: `ENTIDADES` y
    `PRODUCTOS_GLP1` están vacías y la vista `glp1` no existe. Las decisiones
    están registradas pero no codificadas; los números preliminares de arriba
    salieron de consultas ad hoc, no de la vista. Implementar es el próximo paso.
  - **No hay checks corribles todavía.** `OFICIALES` en `04_checks.py` sigue
    vacío, así que `/reconciliar` no puede correr: no hay verde ni rojo, hay un
    check no cargable. Ningún número de esta sesión está reconciliado contra
    CMS y ninguno debe publicarse hasta que lo esté.
  - Cuatro decisiones en cola: D-005 (unidad primaria), D-006 (especialidades),
    D-007 (nominales vs. deflactados), D-008 (filas con fecha corrupta).
  - Sigue sin resolver de la sesión anterior: `pandas` en 3.0.5, y repo público
    o privado hasta la pieza 3.
- **Próximo paso concreto:** implementar D-002/D-003/D-004 en `src/vistas.py`
  (constantes + vista `glp1` con el prorrateo), y reproducir con la vista los
  números preliminares de esta entrada. Si no coinciden, la vista está mal.

---

## 2026-08-25 — corte 01 y su red-team: el ataque reescribió el hallazgo

- **Se decidió:** **D-005 · unidad primaria.** Dólares y pagos se calculan
  siempre y cada finding declara cuál lidera; en el corte 01 no lidera ninguna
  porque el hallazgo era que se contradicen. Se frenó antes de escribir el corte:
  tocaba una decisión no registrada.
- **Se produjo:**
  - `analysis/corte-01_carrera.py` → `findings/cache/corte-01_carrera.json`
  - `charts/g1_carrera.py` → `figures/g1_carrera[.en].png`
  - `charts/g2_disertantes.py` → `figures/g2_disertantes[.en].png`
  - `findings/corte-01_carrera.md`
  - Tres scripts de ataque: `ataque-01_sensibilidad-decisiones.py`,
    `ataque-02_artefactos-dato.py`, `ataque-03_explicaciones-negocio.py`
  - `src/figstyle.py` suma `nueva_figura_apilada()` y extrae `_aplicar_rc()`
  - Reconciliación: `OFICIALES` completo, `04_checks.py` de 10 a 36
    comparaciones, todas Δ = 0,00%. Registrada en `findings/checks.md`.
- **El ataque mató el titular, y eso fue lo más valioso del día.** El corte salió
  diciendo "en dólares Lilly pasó al frente en 2023 y 2024". El ataque C2
  (excluir honorarios de disertante) mostró que sin esa naturaleza **Novo supera
  a Lilly los cinco años**, con ratios de 1,46x a 7,24x. La ventaja de Lilly no
  era "invirtió más": era "invirtió más en un programa". Lilly casi duplicó sus
  pagos de disertante (6.517 → 12.485) mientras Novo redujo los suyos
  (6.809 → 4.898). Título, TL;DR y figura principal reescritos; g2 nació del
  ataque y es ahora el gráfico que manda.
- **Resultado del red-team:** 10 ataques con test corrido. H1 (Lilly gana en
  dólares en 2023-24) sobrevivió 8/10; H2 (Novo gana en pagos los 5 años)
  sobrevivió 9/10. H1 cae en las dos familias que preguntan de dónde viene la
  ventaja, que es donde importa. Sensibilidad a mis decisiones: 4/4 en ambas
  hipótesis — ninguna alternativa rechazada en D-002/D-003/D-004 cambia el
  resultado.
- **Quedó abierto:**
  - **Hallazgo colateral sin explotar (ataque C1):** al recortar el 1% de pagos
    más caros, Lilly supera a Novo también en **2025**. El liderazgo de Novo ese
    año depende de su cola de pagos grandes; en el cuerpo de la distribución
    Lilly ya estaba arriba. Merece corte propio.
  - **La separación disertante/resto es una elección sin D-NNN.** Nació del
    ataque, no de una decisión registrada. Si el corte se publica, necesita la
    suya.
  - La hipótesis de la escasez de semaglutida sigue sin testear y exige una
    fuente fuera de Open Payments.
  - Cola: D-006 (especialidades), D-007 (deflactar), D-008 (75 filas con fecha
    corrupta de PY2024).
  - De antes: `pandas` en 3.0.5 sin pinear.
- **Próximo paso concreto:** registrar la decisión que falta sobre separar
  honorarios de disertante del resto (es la que sostiene el titular actual), y
  recién después evaluar `/derivar` o el corte sobre la cola de pagos grandes
  que abrió C1.
- **Cerrado en la misma sesión:** ver la entrada siguiente (D-006).

---

## 2026-08-25 — D-006: cerrar la decisión que el ataque había improvisado

- **Se decidió:** **D-006 · naturalezas de pago agrupadas en "voz" y "campo".**
  Voz = honorarios de disertante + consultoría (110,15M en 74.271 pagos, USD
  1.483 por pago). Campo = comidas, viajes, educación, alquiler (70,04M en
  3.303.511 pagos, USD 21 por pago). Se agrupa por **qué compra el pago**, no
  por la etiqueta administrativa de CMS.
- **Por qué existía la deuda:** el ataque 03 del corte 01 separó "disertante vs.
  resto" sin pasar por `/decidir`. Eso es un bug de proceso según la regla dura
  del caso, y quedó anotado como tal en la propia D-006.
- **Y la improvisación además estaba mal.** Dejaba `Consulting Fee` del lado de
  las comidas. Consultoría cuesta **USD 2.212 por pago** — más que un honorario
  de disertante (1.466) y 116 veces más que una comida (19). Sólo pasaba
  desapercibido porque es chica: 2,1% de los dólares.
- **El hallazgo no dependía de la partición**, y eso se verificó antes de
  elegir: ratios Novo/Lilly excluyendo cada grupo — sólo disertante
  (7,24 · 3,45 · 1,51 · 1,46 · 2,56), voz completa
  (6,80 · 3,31 · 1,48 · 1,48 · 2,54), sólo comidas
  (5,93 · 2,78 · 1,47 · 1,43 · 2,31). Novo gana los cinco años en las tres. Se
  eligió la defendible porque no costaba nada.
- **Se produjo:** `grupo_naturaleza` en `src/vistas.py` (la regla vive en un
  solo lugar); corte, ataque 03, figura y finding migrados a D-006;
  `g2_disertantes` renombrada a `g2_voz_campo`; el cache pasa de
  `disertante_vs_resto` a `voz_vs_campo`. Ataques recorridos: mismo resultado
  (H1 8/10, H2 9/10).
- **Dato nuevo que salió al migrar:** con el grupo completo, el contraste de
  estrategias es más nítido. Novo pasó de 7.361 a 5.201 pagos de "voz" y Lilly
  de 6.521 a 12.604. **Novo paga menos veces y más caro; Lilly, más veces y más
  barato.**
- **Quedó abierto:** lo mismo que la entrada anterior — el corte sobre la cola
  de pagos grandes que abrió C1 (Lilly supera a Novo también en 2025 al recortar
  el 1% más caro), la hipótesis de escasez sin testear, y la cola D-007
  (especialidades), D-008 (deflactar), D-009 (75 filas con fecha corrupta).
- **Próximo paso concreto:** el corte 02 sobre la cola de pagos grandes, que es
  donde C1 dejó la pregunta abierta: si el liderazgo de Novo en 2025 vive en un
  puñado de pagos, ¿cuántos son y a quién van?

---

## 2026-08-25 — corte 02: la concentración que dejó abierta C1

- **Se decidió:** **D-007 · métrica de concentración.** El titular usa el % del
  gasto que recibe el **top 100** de profesionales de cada compañía; el **Gini**
  queda como control. Se frenó antes de implementar: definir "pago grande" o
  "concentración" es un umbral, y los umbrales pasan por `/decidir`.
- **Por qué no el top 1%, que era lo natural:** las redes tienen tamaños muy
  distintos (Novo 209.450 profesionales, Lilly 152.493), así que el 1% compara
  2.095 personas contra 1.525. Esa métrica **mezcla concentración con alcance**.
  El top 100 compara a las mismas cien personas. Verificado antes de elegir que
  el orden no depende de N: Lilly concentra más en top 10, 50, 100, 500 y 1.000.
- **Se produjo:** `analysis/corte-02_concentracion.py`,
  `charts/g3_concentracion.py`, `figures/g3_concentracion[.en].png`,
  `findings/corte-02_concentracion.md`.
- **El hallazgo:** el gasto está extremadamente concentrado en ambas, pero
  **Lilly concentra 1,74x más**: sus cien profesionales mejor pagos reciben el
  **35,6%** de todo su gasto GLP-1, contra **20,4%** en Novo. Gini 0,885 vs
  0,855.
- **Lo más interesante no es el dinero sino el ritmo.** Entrar al top 100 cuesta
  casi lo mismo en las dos (USD 172.608 en Lilly, USD 172.768 en Novo), pero los
  cien de Lilly acumulan **431 pagos promedio contra 246 de Novo**. Cifras
  parecidas, casi el doble de contactos. Encaja con lo que ya había mostrado
  D-006: Novo paga menos veces y más caro; Lilly, más veces y más barato. La
  misma estrategia aparece ahora en la cabeza de la distribución.
- **Cierra el hilo de C1:** el ataque del corte 01 mostró que al recortar el 1%
  de pagos más caros Lilly superaba a Novo también en 2025, o sea que el
  liderazgo de Novo vivía en su cola. La cola existe en las dos; la de Lilly es
  más pesada.
- **Quedó abierto:**
  - **El corte 02 no tiene red-team todavía.** Cinco ataques ya listados en el
    finding; el más peligroso es si `Profile_ID` identifica personas de forma
    estable, porque toda la métrica descansa en eso. Contrastarlo contra
    `Covered_Recipient_NPI`.
  - Todos los números del corte 02 son del acumulado 2021–2025: falta ver si la
    brecha se sostiene año a año.
  - Cola: D-008 (especialidades), D-009 (deflactar), D-010 (75 filas con fecha
    corrupta de PY2024).
  - La hipótesis de escasez de semaglutida sigue sin testear.
  - Cinco commits locales sin pushear.
- **Próximo paso concreto:** `/atacar corte-02`, empezando por el test de
  `Profile_ID` contra `NPI`. Sin eso, la cifra de concentración no se publica.
- **Cerrado en la misma sesión:** ver la entrada siguiente (red-team del 02).

---

## 2026-08-25 — red-team del corte 02: el ataque refinó el hallazgo

- **Se decidió:** nada. Ninguna decisión nueva; los ataques usaron D-002, D-004,
  D-006 y D-007 ya registradas, y sus alternativas rechazadas.
- **Se produjo:** `analysis/ataque-04_identidad-receptor.py`,
  `ataque-05_robustez-concentracion.py`, `ataque-06_concentracion-negocio.py`.
  El corte 02 se amplió con el bloque `por_naturaleza` para que los números que
  el finding cita salgan del corte y no de una consulta suelta.
- **Resultado: 20 ataques con test corrido. H1 sobrevivió 19/20, H2 18/20.**
- **El ataque crítico pasó limpio.** Toda la métrica descansaba en que
  `Covered_Recipient_Profile_ID` identifique una persona estable. Contrastado
  contra `Covered_Recipient_NPI`: **cero** Profile_ID con varios NPI, **cero**
  NPI bajo varios Profile_ID, y recalcular todo con NPI da 35,65 vs 20,46 —
  ratio 1,74x idéntico. La métrica mide personas.
- **C1 era la explicación alternativa más plausible y falló.** Novo llega a 37%
  más profesionales, así que su denominador podía diluir el top 100 por
  construcción. Emparejando las redes a 1.000, 10.000, 50.000 y 152.493, Lilly
  sigue concentrando más (1,49x a 1,73x). No es artefacto de alcance.
- **C3 invirtió el signo y encontró algo mejor que la métrica original.** Mirando
  sólo contacto de campo, **Novo concentra más que Lilly** (6,72% vs 4,77%). La
  concentración de Lilly no es un rasgo general de su gasto: vive entera en su
  programa de voz. Y ahí está el dato más nítido del corte: **Lilly reparte USD
  48,42M entre 657 profesionales; Novo reparte USD 61,73M entre 1.139.** El club
  de Lilly es la mitad de grande y cobra un tercio más por cabeza (USD 73.700
  contra 54.193).
- **Dos fallos, ambos informativos:**
  - **H2 falla en 2021**: ese año el top 100 de Novo acumulaba más pagos que el
    de Lilly (80 vs 64). Lilly construyó su programa dentro de la ventana — de
    64 pagos promedio en 2021 a 118 en 2024. El patrón no precede al período.
  - **C2 quedó no concluyente y se publica como tal.** Al excluir Mounjaro,
    Zepbound y Wegovy para testear el efecto lanzamiento, a Lilly le queda sólo
    Trulicity (8,27M) contra 85,25M de Novo: la muestra se degenera y el 2,68x
    que arroja no significa nada. Un test limpio exige otro diseño (excluir sólo
    el año de lanzamiento de cada producto) y queda pendiente.
- **Quedó abierto:**
  - El test limpio del efecto lanzamiento que C2 no logró ser.
  - Concentración institucional: el `Profile_ID` cuenta como independientes a
    profesionales de un mismo centro; una red aparentemente dispersa podría ser
    un puñado de instituciones.
  - Cola: D-008 (especialidades), D-009 (deflactar), D-010 (75 filas con fecha
    corrupta de PY2024).
  - La hipótesis de escasez de semaglutida sigue sin testear.
  - Siete commits locales sin pushear.
- **Próximo paso concreto:** los dos cortes tienen checks verdes y red-team
  corrido, así que `/derivar` está habilitado sobre cualquiera de los dos. La
  alternativa es seguir la cola de decisiones, empezando por especialidades, que
  abre el corte 03 (a qué perfil profesional le paga cada compañía).

---

## 2026-08-25 — corte 03: el dinero sigue al especialista, no al volumen

- **Se decidió:** **D-008 · agrupación de especialidades.** Cinco categorías
  evaluadas en orden: endocrinología, medicina de obesidad, NP/PA, primaria
  (médico), resto. Se frenó antes de implementar, como corresponde.
- **La decisión real fue la regla de prioridad.** "NP/PA" es un tipo de
  proveedor mientras "endocrinología" y "primaria" son especialidades, así que un
  enfermero de Family Medicine podía caer en dos categorías. Se eligió que el
  tipo mande: eso mueve **USD 18,21M**. Sin esa regla escrita, dos
  implementaciones del mismo criterio darían números distintos.
  Endocrinología no genera conflicto: es prácticamente exclusiva de médicos
  (247.067 pagos contra 3 de enfermería).
- **Por qué la especialidad y no el tipo como eje:** el tipo de proveedor casi no
  separa a las compañías (Novo 78,1% a médicos, Lilly 83,8%). La especialidad sí:
  doce puntos de diferencia en endocrinología.
- **Se produjo:** `especialidad` en `src/vistas.py`,
  `analysis/corte-03_especialidades.py`, `charts/g4_especialidades.py`,
  `figures/g4_especialidades[.en].png`, `findings/corte-03_especialidades.md`.
- **El hallazgo:** **5.367 endocrinólogos recibieron USD 65,09M; 120.145
  enfermeros y asistentes, 35,24M.** USD 12.129 por cabeza contra 293, factor 41.
  Endocrinología es el 2,1% de los profesionales alcanzados y el 36% del dinero.
- **Y la diferencia entre compañías:** endocrinología es el **43,6%** del gasto
  de Lilly y el **31,5%** del de Novo. Novo compensa repartiendo más al canal de
  volumen (21,8% a NP/PA contra 16,0%) y al resto de especialidades (16,2% contra
  9,2%).
- **Los tres cortes convergen.** El 01 encontró que la ventaja de Lilly vive en
  pagos que compran la voz del profesional; el 02, que su círculo de voz es la
  mitad de grande que el de Novo; el 03 nombra a ese círculo: son
  endocrinólogos. No es la misma medición tres veces — son tres ángulos
  independientes de la misma estrategia.
- **Dato lateral:** medicina de obesidad son 242 profesionales a USD 9.002 por
  cabeza, el segundo valor más alto de la tabla. Especialidad joven; si crece,
  es un corte propio.
- **Quedó abierto:**
  - **El corte 03 no tiene red-team.** Cinco ataques listados; el más peligroso
    es que la especialidad es **autodeclarada** por el reportante — si un mismo
    `Profile_ID` cambia de especialidad entre años, el corte se cae.
  - El segundo: ¿la brecha entre compañías sobrevive mirando sólo contacto de
    campo, o es un subproducto del corte 01?
  - Verificado que el cambio en `vistas.py` no rompió los cortes 01 y 02: mismos
    números.
  - Cola: D-009 (deflactar), D-010 (75 filas con fecha corrupta de PY2024).
  - Sigue pendiente el test limpio del efecto lanzamiento (C2 del corte 02) y la
    hipótesis de escasez de semaglutida.
  - Ocho commits locales sin pushear.
- **Próximo paso concreto:** `/atacar corte-03`, empezando por la estabilidad de
  la especialidad autodeclarada.
- **Cerrado en la misma sesión:** ver la entrada siguiente.

---

## 2026-08-25 — red-team del corte 03: el ataque encontró una convergencia

- **Se decidió:** nada. Los ataques usaron decisiones ya registradas y sus
  alternativas rechazadas.
- **Se produjo:** `analysis/ataque-07_estabilidad-especialidad.py`,
  `ataque-08_robustez-especialidades.py`, y `charts/g5_convergencia.py` con
  `figures/g5_convergencia[.en].png`, que nació del hallazgo del ataque.
- **Resultado: 15 ataques con test corrido. H1 sobrevivió 12/12, H2 11/12.**
- **El ataque crítico pasó, y de una forma que no esperaba.** La especialidad es
  autodeclarada por el reportante, así que podía ser puro ruido de reporte. Hay
  inestabilidad, pero baja: 3,64% de los profesionales cambian de especialidad
  entre años y 4,21% son declarados distinto por cada compañía. Lo decisivo fue
  **la dirección**: entre los discrepantes hay 179 casos donde Novo declara
  endocrinología y Lilly no, contra 118 al revés. **El sesgo de reporte que
  existe juega en contra del hallazgo, no a favor.** Y excluir a los 5.417
  ambiguos (11,4% del gasto) refuerza H2: la brecha pasa de 12,1 a 14,0 puntos.
- **El hallazgo nuevo, y es el más importante del día: la brecha se está
  cerrando.** El acumulado del corte 03 esconde una trayectoria. El peso de
  endocrinología en el gasto de cada compañía:
  Lilly 51,1 → 58,2 → 51,6 → 41,9 → **27,8**;
  Novo 43,1 → 39,3 → 21,6 → 20,2 → **24,5**.
  La brecha va de 8 puntos (2021) a 30 (2023, el año del lanzamiento de
  Zepbound) y baja a **3,3 en 2025**. Si sigue, "Lilly apuesta al especialista"
  describe 2021–2024 y no el presente. Quedó en el TL;DR y con figura propia.
- **B1 desactivó la preocupación central de D-008.** La regla de prioridad que
  tanto discutí —un NP de Family cuenta como NP/PA— mueve USD 18,21M pero **da
  el resultado idéntico**: 43,6% vs 31,5% con las dos reglas. Endocrinología no
  participa del solapamiento. La decisión importa para leer NP/PA y primaria, no
  para el hallazgo del corte.
- **C2 cerró un pendiente del corte 02.** El efecto lanzamiento, que allá quedó
  sin testear limpiamente por muestra degenerada, acá sí se pudo: mirando sólo
  los seis productos previos a la ventana, H2 se mantiene (46,6% vs 37,9%). La
  apuesta de Lilly no es un artefacto de haber lanzado Mounjaro y Zepbound.
- **Un fallo, el mismo patrón que en el corte 02:** C1 muestra que la diferencia
  entre compañías vive en los pagos de "voz"; en contacto de campo Novo destina
  levemente más a endocrinología (11,1% contra 9,4%). H1 sobrevive en las dos
  mitades, aunque el factor cae de 41x a 6x.
- **Quedó abierto:**
  - **Sigue sin testear si los endocrinólogos reciben más porque son menos.**
    Exige el universo de endocrinólogos de EEUU, fuera de Open Payments.
  - La convergencia de 2025 pide seguimiento en PY2026.
  - Cola: D-009 (deflactar), D-010 (75 filas con fecha corrupta de PY2024).
  - La hipótesis de escasez de semaglutida sigue sin testear.
  - Nueve commits locales sin pushear.
- **Próximo paso concreto:** los tres cortes tienen checks verdes y red-team
  corrido, así que `/derivar` está habilitado sobre cualquiera. Si en cambio se
  sigue analizando, el hilo más vivo es la convergencia: qué hizo Lilly con el
  dinero que sacó de endocrinología entre 2023 y 2025.

---

## 2026-08-25 — corte 04: la convergencia esconde dos movimientos opuestos

- **Se decidió:** **D-009 · reapertura de D-008.** Es la primera reapertura del
  caso. D-008 queda **superada, con su texto intacto** — la historia no se edita,
  se referencia. Lo único que cambia es que la categoría residual se parte: sale
  un bloque "emergentes" (cardiología + nefrología + gastro/hepatología).
- **Por qué hubo que reabrir:** al explorar la convergencia apareció que "resto"
  había dejado de ser residual. Contenía tres especialidades que crecen juntas y
  pasan de **3,7% del gasto en 2023 a 16,3% en 2025**. Publicar el corte 04 sin
  reabrir habría significado un desglose sin decisión detrás — el mismo bug de
  proceso que hubo que corregir en D-006.
- **Verificado que la reapertura no rompe lo publicado:** el corte 03 y sus 12
  ataques se recorrieron con la categoría nueva y dan idéntico (H1 12/12, H2
  11/12). El hallazgo endocrinología-contra-NP/PA no se toca.
- **Se produjo:** `analysis/corte-04_convergencia.py`, `charts/g6_movimiento.py`,
  `figures/g6_movimiento[.en].png`, `findings/corte-04_convergencia.md`. Finding
  del corte 03 actualizado con la categoría nueva.
- **El hallazgo: convergieron en proporción y divergieron en estrategia.** Entre
  2023 y 2025, **Lilly retiró USD 1,85M de endocrinología** —su única categoría
  en baja— y puso 3,59M más en atención primaria. **Novo creció en todas**, y su
  mayor salto fue **+6,43M en cardiología, nefrología y gastro/hepatología**, que
  pasan de 0,96M a 7,39M. En el acumulado, Novo destina 14,74M a ese grupo contra
  1,46M de Lilly: **10 a 1**.
- **El frente lo pagan dos productos:** Wegovy (0,15 → 4,35M) y Ozempic (0,75 →
  2,87M).
- **La lección de método, que vale para el writeup:** el corte 03 midió en
  porcentaje y vio convergencia; el 04 midió en dólares y vio divergencia. **Es
  el mismo dato.** D-005 pedía declarar la unidad líder por corte justamente para
  esto, pero recién acá se ve por qué importa tanto.
- **Lo que el corte NO puede probar, y quedó escrito:** que el movimiento de Novo
  sea *por* las nuevas indicaciones cardiovascular y renal de semaglutida. Encaja
  en el tiempo y es la explicación obvia, pero **Open Payments no registra
  indicaciones**. El nombre "emergentes" quedó declarado en D-009 como
  interpretación, no como dato.
- **Quedó abierto:**
  - **El corte 04 no tiene red-team.** Cinco ataques listados; el más peligroso
    es si los cardiólogos son realmente nuevos o son los mismos profesionales con
    la etiqueta cambiada — el corte 03 ya encontró 3,64% de inestabilidad en la
    especialidad declarada.
  - El segundo: si el movimiento sobrevive al normalizar por escala, dado que el
    gasto total de Novo creció más.
  - Cola: D-010 (deflactar), D-011 (75 filas con fecha corrupta de PY2024).
  - Sigue sin testear si los endocrinólogos reciben más porque son menos.
  - Diez commits locales sin pushear.
- **Próximo paso concreto:** `/atacar corte-04`, empezando por seguir los
  `Profile_ID` de los cardiólogos en el tiempo.
- **Cerrado en la misma sesión:** ver la entrada siguiente.

---

## 2026-08-25 — red-team del corte 04: el frente aguanta, el repliegue depende del pivote

- **Se decidió:** nada. Los ataques usaron decisiones ya registradas.
- **Se produjo:** `analysis/ataque-09_frente-nuevo.py`,
  `ataque-10_robustez-convergencia.py`. Nota de `g6` reescrita para declarar la
  dependencia del pivote.
- **Resultado: 14 ataques con test corrido. H2 sobrevivió 11/11, H1 9/11.**
- **El ataque crítico pasó de forma contundente.** La preocupación era que los
  "cardiólogos de 2025" fueran los mismos profesionales de antes con la etiqueta
  cambiada — el corte 03 había encontrado 3,64% de inestabilidad. Clasificando
  cada profesional del grupo emergente por su historia: **75,9% del gasto va a
  gente que ya estaba declarada en esas especialidades**, 23,0% a nuevos en el
  dataset y sólo **0,7% a reetiquetados**. Lo nuevo no es la etiqueta: es que
  esos cardiólogos empezaron a recibir pagos por GLP-1.
- **C1 descartó el efecto de escala y afiló el hallazgo.** Novo creció más en
  total, así que "creció en todo" podía ser aritmética. Normalizando cada delta
  por el crecimiento de su compañía: **el 40,8% del crecimiento de Novo fue al
  frente emergente; el 67,1% del de Lilly fue a atención primaria**, financiado
  en parte por el −34,6% de endocrinología. No es escala, es composición.
- **C2 mató H1 en dos de tres pivotes, y eso reformuló el hallazgo.** Con 2021
  como base el movimiento se invierte (Lilly +2,32M, Novo −3,52M); con 2022 ambas
  bajan. La serie de Novo en endocrinología tiene forma de U (10,60M → 2,83M →
  7,08M), así que el corte describe **una reversión desde el piso de 2023, no una
  tendencia del período**. El pivote no es arbitrario —es el pico de divergencia
  que encontró el ataque 08— pero determina el signo, y quedó declarado en el
  TL;DR, en la tabla de ataques y en la nota de la figura.
- **C3 es la primera vez en el caso que un hallazgo sobrevive en las dos
  mitades.** Los cortes 02 y 03 tenían su diferencia entre compañías concentrada
  en los pagos de "voz". Acá el frente emergente aparece también en contacto de
  campo (Novo 1,36M contra Lilly 0,08M): es un movimiento comercial completo, no
  un programa de disertantes.
- **Quedó abierto:**
  - Si PY2026 muestra a Novo bajando otra vez en endocrinología, la lectura
    correcta pasa a ser "oscilación" y no "reversión".
  - La causa del frente emergente sigue sin poder probarse con este archivo:
    exige el calendario de aprobaciones de la FDA.
  - Cola: D-010 (deflactar), D-011 (75 filas con fecha corrupta de PY2024).
  - Sigue sin testear si los endocrinólogos reciben más porque son menos.
  - Once commits locales sin pushear.
- **Próximo paso concreto:** los cuatro cortes tienen checks verdes y red-team
  corrido (59 ataques en total), así que `/derivar` está habilitado sobre
  cualquiera. Si se sigue analizando, la cola de decisiones está intacta.

---

## 2026-08-25 — verificación de findings: apareció un error real

- **Se decidió:** nada.
- **Se produjo:** `scripts/05_verificar_findings.py`. Fija las cifras que los
  findings citan y las compara contra `findings/cache/*.json`, más dos checks de
  coherencia (totales que deben cerrar entre cortes, y findings que citen
  decisiones superadas sin aclararlo). **93 cifras cubiertas.**
- **Encontró un error real, que es exactamente para lo que se escribió.** La
  tabla voz/campo del corte 01 tenía **los cinco años desactualizados**: quedaron
  de la partición previa a D-006, cuando consultoría todavía estaba del lado de
  "campo". Publicado decía campo Novo 2025 = 13,31M; el valor real es 12,39M, una
  diferencia de 918.124 dólares. Corregida la tabla entera.
- **Y dos redondeos truncados en el corte 03**: 65,09 en vez de 65,10 millones y
  35,24 en vez de 35,25. Triviales, pero eran números mal escritos.
- **La observación que vale para el writeup:** las **figuras nunca tuvieron el
  error**, porque la regla del proyecto las obliga a leer el cache y no el texto.
  El pipeline protege los gráficos por diseño; el texto escrito a mano era el
  único eslabón sin verificar. Por eso ahora hay dos verificadores —
  `04_checks.py` cierra el dato propio contra CMS, `05_verificar_findings.py`
  cierra el texto publicado contra el dato propio — y los dos tienen que estar
  verdes antes de publicar.
- **Dos falsos positivos que hubo que corregir en el propio verificador**, porque
  un check que grita cuando no debe se vuelve ruido: comparar con tolerancia
  porcentual marcaba en rojo cifras chicas bien redondeadas (un finding que dice
  "0,45M" no afirma 450.000 exactos), y el regex de decisiones superadas cruzaba
  bloques y señalaba D-001 en vez de D-008.
- **Quedó abierto:**
  - **Las cifras de la sección "Intenté matarlo" no están cubiertas**: salen de
    los scripts de ataque, que imprimen pero no cachean. Cubrirlas exigiría que
    los ataques escribieran su propio cache.
  - Cola: D-010 (deflactar), D-011 (75 filas con fecha corrupta de PY2024).
  - Doce commits locales sin pushear.
- **Próximo paso concreto:** pushear, y después `/derivar` sobre el corte 03, que
  es el hallazgo más autocontenido.
- **Cerrado en la misma sesión:** ver la entrada siguiente.

---

## 2026-08-25 — push y primera derivación de contenido

- **Se decidió:** nada.
- **Se produjo:**
  - **Push a origin**: `6300afd..26ba1cf`, diez commits, 46 archivos. `data/`
    quedó fuera, como siempre.
  - `contenido/pieza-03/` con `video.md`, `carrusel.md`, `micropost.md` y
    `PARA-IVAN.md`, en ES y EN. Desarrolla el esqueleto de
    `pieza-03-el-crossover.md` con el dato real. No se commitea: `contenido/`
    está gitignoreado por diseño.
- **El dato no dio ninguna de las cuatro formas de titular que la pieza 3
  preveía.** La serie esperaba una migración del especialista al generalista
  (formas A a D). Lo que hay es una quinta: **las dos compañías se alejaron del
  especialista al mismo tiempo, pero hacia destinos distintos** — Lilly al médico
  de cabecera (25,9% → 37,7%), Novo a cardiología, nefrología y gastro
  (6,5% → 25,6%). Quedó registrado en `carrusel.md` con las opciones y una
  recomendación.
- **Un titular descartado a propósito:** "un endocrinólogo vale 41 enfermeros
  para la industria". Es el más filoso y el más citable, y está mal: el dato
  habla de cómo gastan las compañías, no del valor de las personas. Publicado
  así, el propio finding lo contradice. Anotado en `PARA-IVAN.md` como
  "no usar sin reformular".
- **El micro-post va por un ángulo distinto al video**, como pide la serie: no
  el hallazgo sino **la categoría "resto" que casi lo esconde**, y el costo de
  reabrir una decisión ya publicada. Es la pieza que vende el método.
- **Verificación previa a escribir:** las 18 cifras usadas en las piezas se
  contrastaron contra el cache una por una. Todas coinciden. Un solo
  `[PLACEHOLDER]`: el "trimestre exacto" que la pieza 3 original prometía no
  existe, porque el corte trabaja por año — para tenerlo hay que ampliar el corte
  con `date_trunc('quarter', fecha)`.
- **Privacidad:** ninguna pieza nombra a nadie. El dato del profesional que más
  recibió (USD 403.511, corte 02) se dejó **deliberadamente afuera**: con ese
  número y el dataset público, identificar a la persona es trivial. Queda
  anotado en `PARA-IVAN.md`.
- **Quedó abierto:**
  - `[PLACEHOLDER: link al caso]` en el carrusel, pendiente de `/exportar-caso`.
  - Las piezas 1, 2 y 4 de la serie siguen sin derivar.
  - Cola: D-010 (deflactar), D-011 (75 filas con fecha corrupta de PY2024).
  - El writeup en inglés sigue sin escribirse — es de Iván, Claude sólo ataca.
- **Próximo paso concreto:** el writeup, o `/exportar-caso` para tener el link
  que las piezas necesitan. Analíticamente el caso está cerrado: cuatro cortes
  con red-team, dos verificadores en verde.
- **Cerrado en la misma sesión:** ver la entrada siguiente.

---

## 2026-08-25 — /exportar-caso: andamiaje, no caso terminado

- **Se decidió:** nada.
- **La precondición no se cumplía y el export quedó a propósito incompleto.**
  `/exportar-caso` exige `writeup/` aprobado. `notas-revision.md` está vacío y
  `outline-en.md` son 28 líneas de esquema: el writeup no está escrito. Por la
  regla dura #4 —el writeup lo escribe Iván, Claude ataca y no redacta— el
  cuerpo de los MDX **no se generó**. Escribirlo habría sido hacer el writeup con
  otro nombre, y habría anulado el motivo declarado de esa regla, que es el
  entrenamiento de inglés.
- **Se produjo, en `export/` (gitignoreado, derivado, regenerable):**
  - `site/content/projects/{es,en}/glp1-open-payments/index.mdx` — frontmatter
    completo con los cuatro `metrics` verificados contra findings verdes, la
    estructura de secciones según el outline, los seis `<Figure>` con ruta
    correcta y caption, y `draft: true` en los dos locales. Cada bloque de prosa
    marcado con `{/* OUTLINE §N */}` y con los datos a citar indicados.
  - `site/public/projects/glp1-open-payments/` — las 12 PNG, 1495x886.
  - `INSTRUCCIONES.md` — con una tabla explícita de qué está listo y qué falta,
    el orden recomendado (writeup en inglés primero, después `/atacar` sobre el
    texto, después `05_verificar_findings`, recién ahí volcar y regenerar), y los
    pasos de importación desde el repo del sitio.
- **Frontera verificada:** `git status` quedó vacío después de correr la skill.
  Nada fuera de `export/` fue tocado.
- **Quedó abierto:**
  - **El writeup.** Es lo único que bloquea la publicación. Todo lo demás está.
  - `cover.jpg` no existe.
  - Los `alt` de las figuras y el `tagline`/`description` son texto editorial:
    van con la prosa.
  - `[PLACEHOLDER: link al caso]` en el carrusel de la pieza 3 sigue pendiente,
    porque depende de que el caso esté publicado.
  - Cola: D-010 (deflactar), D-011 (75 filas con fecha corrupta de PY2024).
- **Próximo paso concreto:** escribir el writeup en inglés en `writeup/`. Después
  pedir `/atacar` sobre el texto, correr `05_verificar_findings`, volcar la prosa
  a los MDX y regenerar el export.

---

## 2026-08-25 — D-010 y una corrección a mi propia recomendación

- **Se decidió:** **D-010 · dólares nominales, con el punto de quiebre
  publicado.** USD corrientes en todo el caso, declarado en límites; y donde el
  deflactor puede cambiar el signo de una afirmación, se publica **el deflactor
  que la anula** en vez de resolverla con una fuente externa.
- **Corregí una recomendación que había dado mal.** Al responder las cuatro
  preguntas del writeup dije que deflactar "no cambia ninguna conclusión". Era
  incompleto: había mirado los deltas del corte 04 y no la serie total del corte
  01. Calculando el deflactor de quiebre de cada afirmación temporal apareció una
  frágil: **el crecimiento nominal de Novo entre 2021 y 2025 es +17,4% y se anula
  con un deflactor de 1,174** — 17,4% de inflación acumulada en cuatro años, que
  está dentro del rango del período. En términos reales el gasto de Novo es
  aproximadamente plano, no creciente.
- **Las otras cuatro afirmaciones son inmunes**, y por eso la decisión fue barata:
  Lilly +224,2% necesitaría deflactor 3,242; el aumento de Novo en endocrinología,
  2,505; el frente emergente, 7,703; y la caída de Lilly en endocrinología ya es
  negativa, así que deflactar la refuerza.
- **No pude traer el CPI, y eso pesó en la decisión.** BLS bloquea automatización
  y FRED no sirve el CSV por la vía de `/browse`. Deflactar habría exigido traer
  la serie a mano **y** decidir qué índice usar — CPI-U, PCE o un índice de
  precios médicos son tres decisiones distintas con resultados distintos, porque
  el gasto promocional farmacéutico no sigue la canasta del consumidor. Precio
  alto para cambiar una sola afirmación que se puede declarar en una línea.
- **Se produjo:** D-010 en `decisions.md`; nota de sensibilidad en
  `findings/corte-01_carrera.md` con los cuatro deflactores de quiebre; y cuatro
  aserciones nuevas en `05_verificar_findings.py` para que esas cifras queden
  cubiertas. **97 cifras verificadas, 0 discrepancias.**
- **Quedó abierto:**
  - El writeup sigue siendo lo único que bloquea. La sección de límites ahora
    tiene que decir "nominal USD, sin deflactar" y llevar la nota de Novo.
  - Los defectos D3 y D4 de `writeup/notas-revision.md` son errores míos del
    export y se corrigen al regenerarlo: el caption de g1 repite el claim que C2
    mató, y `INSTRUCCIONES.md` dice "los 6 Figure" cuando los MDX usan 4 —
    faltan g2 y g5, justo las dos que nacieron del red-team.
  - D-011 (75 filas con fecha corrupta) sigue en cola; sólo hace falta si se
    decide el corte trimestral.
- **Próximo paso concreto:** el writeup. Cuando exista, `/atacar` sobre el texto
  y extender el verificador con las cifras que cite (defecto D7).

---

## 2026-08-26 — D-011: "resto" escondía un segundo frente, el de Lilly

- **Se decidió: D-011**, que reabre D-009. Séptima categoría "respiratorio y
  sueño" (neumonología · medicina del sueño · cuidados críticos), evaluada
  **después de NP/PA** —al revés que emergentes, porque acá manda el tipo de
  proveedor (D-008), y la asimetría queda declarada— más un **control permanente
  de `resto`**: desglose por compañía y año, y umbral del 5% del gasto anual que
  obliga a decidir. Opción C de las tres presentadas.
- **Cómo apareció:** revisando el outline del writeup contra los findings. El
  `resto` de Lilly en 2025 estaba en 15,7% de su gasto, el valor más alto de una
  categoría residual en toda la ventana. Adentro había un bloque que salta junto:
  sueño 5 → 726 mil, críticos 2 → 343 mil, neumo 7 → 320 mil entre 2023 y 2025.
  La cláusula "qué la invalidaría" de D-009 había previsto exactamente este caso.
- **Red-team del frente nuevo** (`analysis/ataque-11_frente-respiratorio.py`):
  11 tests con veredicto, **H3 10/11 · H4 10/11**. El reetiquetado da **4,8%**
  del gasto, y el 81,5% son profesionales **nuevos en el dataset** — al revés
  que el frente emergente de Novo, que era 75,9% gente que ya estaba. La
  taxonomía queda descartada: los cinco valores NUCC existen desde 2021. Único
  fallo: **C2, sólo contacto de campo** (8x contra el umbral de 10, dominio 4,4x
  contra 5). El frente de Lilly es, por ahora, un programa de voz: 1,286M de
  1,388M sobre 41 profesionales.
- **El pico de lanzamiento NO se pudo testear y se declaró así**, en vez de
  contarlo como sobreviviente: con 2025 como último año, un frente y un pico son
  indistinguibles. Es la hipótesis viva, a resolver con PY2026.
- **Impacto en lo publicado:** el titular del corte 04 era falso. Pasa a **"Cada
  compañía abrió su propio frente, con dos años de diferencia: Novo en
  cardiología, Lilly en sueño"**. En 2025, Novo supera a Lilly 16 a 1 en
  cardiología y afines; Lilly supera a Novo 36 a 1 en el bloque respiratorio.
- **Dos defectos viejos que aparecieron al recorrer:**
  - `charts/g4_especialidades.py` nunca recibió D-009: su lista de categorías
    tenía cinco y descartaba lo que no estuviera en ella, así que **la figura
    publicada omitía "emergentes"** (16,20M, 9% de la ventana) mientras la tabla
    del finding la incluía. Corregido; ahora son siete.
  - El desglose por dirección del ataque 07 usa `any_value()` y **no es
    reproducible**: cada corrida da números distintos. Los totales sí son
    estables. La afirmación del corte 03 sobre la dirección del sesgo de reporte
    quedó **suspendida** en el texto hasta que el desempate sea una regla.
- **Checks:** `04_checks.py` 36 comparaciones Δ = 0,00% · `05_verificar_findings.py`
  **112 cifras, 0 discrepancias**, con 15 aserciones nuevas. Los dos verdes.
- **Corrección en el propio D-011:** las cifras exploratorias con que se decidió
  (1,389M, 1.539 profesionales, "74% Zepbound") no correspondían a la regla que
  el registro elige. Con la regla: 1,388M, 1.523 y **98,9% Zepbound**. Corregido
  en el registro, con la nota de que la corrección existió.
- **Quedó abierto:**
  - **El writeup**, que sigue siendo lo único que bloquea la publicación.
  - El desempate del ataque 07: necesita `/decidir`, no lo decido solo.
  - `export/` quedó desactualizado: sus captions citan el titular viejo del
    corte 04. Se regenera con `/exportar-caso` cuando el writeup esté.
  - La discrepancia entre el texto de D-008 (primaria "sin subespecialidad") y
    su implementación (Family y General Practice sí admiten subespecialidad,
    0,72M). No la toqué: es una decisión, no un bug de tipeo.
  - Cola: fechas corruptas de PY2024 (pendiente 8).
- **Próximo paso concreto:** el writeup en inglés, con `writeup/notas-revision.md`
  al lado — su segundo pase ya tiene el material por sección y los defectos D1 a
  D11 con su estado.
