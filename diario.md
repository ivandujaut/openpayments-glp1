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
