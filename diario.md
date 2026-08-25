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
