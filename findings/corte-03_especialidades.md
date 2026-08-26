# 5.367 endocrinólogos reciben casi el doble que 120.145 enfermeros y asistentes

**Corte 03 — 2026-08-25, recorrido 2026-08-26 por D-011 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: dólares (D-005) · Red-team: 15 ataques, H1 sobrevivió 12/12 · H2 11/12**

## TL;DR

El dinero de GLP-1 no sigue al volumen de prescriptores: sigue al especialista.
**5.367 endocrinólogos recibieron USD 65,10 millones entre 2021 y 2025, mientras
120.145 enfermeros y asistentes médicos recibieron 35,25 millones.** Son USD
12.129 por endocrinólogo contra 293 por NP/PA: un factor de **41**.

Las dos compañías apuestan al mismo perfil, pero en dosis distintas.
**Endocrinología es el 43,6% del gasto de Lilly y el 31,5% del de Novo.** Novo
compensa repartiendo más al canal de volumen (21,8% a NP/PA contra 16,0%) y,
sobre todo, a un grupo de especialidades que Lilly casi no toca: **13,3% de su
gasto va a cardiología, nefrología y gastro/hepatología, contra 2,1% de Lilly**
(ver D-009 y el corte 04).

Esto encaja con lo que ya mostraron los cortes anteriores. El corte 01 encontró
que la ventaja de Lilly vive en pagos que compran la voz del profesional; el
corte 02, que su círculo de "voz" es la mitad de grande que el de Novo. Este
corte nombra a ese círculo: **son endocrinólogos**.

**Pero el red-team encontró que la brecha se está cerrando.** El acumulado
esconde una convergencia fuerte: la diferencia entre ambas compañías en el peso
de endocrinología pasó de 30 puntos en 2023 a **3,2 puntos en 2025**. Lilly bajó
de 51,6% a 27,8% mientras Novo subió de 21,6% a 24,5%. Si la tendencia sigue, el
hallazgo de este corte describe un período que se está terminando.

**Lo que NO dice:** nada sobre prescripciones ni sobre si el dinero cambia
conductas. Tampoco dice que los endocrinólogos "cuesten más" — dice que reciben
más, que es un hecho sobre la estrategia de las compañías, no sobre las personas.

## Los gráficos

`figures/g4_especialidades.png` · `.en.png` — barras horizontales por perfil, con
el tamaño de cada población y el dinero por cabeza en la columna derecha. Ese
contraste —cuánta gente hay contra cuánto recibe cada uno— es el hallazgo; la
barra sola no lo muestra.

`figures/g5_convergencia.png` · `.en.png` — **nacida del red-team.** La
trayectoria anual del peso de endocrinología en cada compañía, con la brecha
sombreada: se abre hasta 30 puntos en 2023 y se cierra a 3,2 en 2025. Es la
figura que impide leer el acumulado como si fuera el presente.

## Qué es dato y qué es elección mía

| Elemento | Tipo | Fuente / Decisión |
|---|---|---|
| Especialidad declarada | dato | `Covered_Recipient_Specialty_1`, taxonomía NUCC de CMS |
| Gasto y conteos por perfil | dato | `analysis/corte-03_especialidades.py` |
| Ventana, entidades, productos, prorrateo | elección | **D-001** · **D-002** · **D-003** · **D-004** |
| Las categorías de especialidad y su orden | elección | **D-008**, reabierta por **D-009** y **D-011** — un NP de Family cuenta como NP/PA, no como primaria |
| Agrupación "voz" / "campo" | elección | **D-006** |
| Dólares como unidad líder | elección | **D-005** — declarada por corte |

## Números

Todos salen de `analysis/corte-03_especialidades.py` →
`findings/cache/corte-03_especialidades.json`.

| Perfil | Novo USD | Lilly USD | % Novo | % Lilly | Profesionales | USD por cabeza |
|---|---|---|---|---|---|---|
| Endocrinología | 34,98M | 30,11M | 31,5% | **43,6%** | 5.367 | **12.129** |
| Atención primaria (médico) | 32,41M | 20,39M | 29,2% | 29,5% | 82.949 | 637 |
| Enfermería y asistentes | 24,20M | 11,04M | **21,8%** | 16,0% | 120.145 | 293 |
| Emergentes (cardio, nefro, gastro) | 14,74M | 1,46M | **13,3%** | 2,1% | 16.714 | 969 |
| Resto | 3,19M | 3,64M | 2,9% | 5,3% | 26.032 | 263 |
| Medicina de obesidad | 1,24M | 0,94M | 1,1% | 1,4% | 242 | 9.002 |
| Respiratorio y sueño | 0,21M | 1,54M | 0,2% | **2,2%** | 2.280 | 767 |

*(Categorías de **D-011**, que reabrió D-009 para sacar de la categoría residual
un segundo bloque: neumonología, medicina del sueño y cuidados críticos, que en
2025 es el 7,2% del gasto de Lilly. El hallazgo del corte no cambió: se
recorrieron el corte y sus 12 ataques con la categoría nueva y dan idéntico.
Antes de D-011, atención primaria incluía la medicina del sueño declarada bajo
Family Medicine —0,38M— y el resto de ese bloque vivía en "resto".)*

**El bloque nuevo casi no toca a Novo:** 1,54M de Lilly contra 0,21M, y todo el
movimiento ocurre en 2025. El corte 04 lo analiza; acá sólo se declara para que
la tabla sume lo que dice.

**La pirámide, en una línea:** endocrinología es el 2,1% de los profesionales
alcanzados y el 36% del dinero.

**Medicina de obesidad es minúscula pero cara:** 242 profesionales a USD 9.002
por cabeza, el segundo valor más alto de la tabla. Es una especialidad joven y
el dato no permite decir si crece; ese es un corte aparte.

**La convergencia, año por año** (% del gasto de cada compañía que va a
endocrinología, de `analysis/ataque-08_robustez-especialidades.py`):

| Año | Lilly | Novo | Brecha |
|---|---|---|---|
| 2021 | 51,1% | 43,1% | 8,0 |
| 2022 | 58,2% | 39,3% | 18,9 |
| 2023 | 51,6% | 21,6% | **30,0** |
| 2024 | 41,9% | 20,2% | 21,7 |
| 2025 | 27,8% | 24,5% | **3,2** |

La brecha se calcula sin redondear (27,76 − 24,53 = 3,23): restar los valores
redondeados de la tabla da 3,3 y es un artefacto del redondeo.

El pico de divergencia es 2023, el año en que Lilly lanzó Zepbound. Para 2025 las
dos compañías destinan proporciones casi iguales a endocrinología.

## Intenté matarlo

**15 ataques con test corrido: 3 estructurales sobre la estabilidad de la
especialidad y 12 sobre las hipótesis. H1 sobrevivió 12/12 · H2 sobrevivió
11/12.** Scripts: `analysis/ataque-07_estabilidad-especialidad.py` ·
`ataque-08_robustez-especialidades.py`.

- **H1**: endocrinología recibe mucho más por cabeza que NP/PA.
- **H2**: Lilly destina más de su gasto a endocrinología que Novo.

### El ataque crítico: la especialidad es autodeclarada por el reportante

| Test | Resultado |
|---|---|
| A1 mismo profesional, distinta especialidad entre años | 5.099 de 137.669 · **3,70%** |
| A2 mismo profesional, declarado distinto por cada compañía | 4.866 de 113.817 · **4,28%** |
| A3 taxonomía comparable entre años | 257 a 304 valores NUCC según el año, **pero siempre 7 categorías** (D-011) |

La inestabilidad existe y es baja.

> **Suspendido — el desglose por dirección no es reproducible.** La versión
> anterior de este finding afirmaba que entre los profesionales declarados
> distinto hay más casos donde Novo declara endocrinología y Lilly no que al
> revés, y usaba eso para decir que el sesgo de reporte juega en contra de H2.
> Al recorrer el ataque se detectó que esa tabla usa `any_value()` para elegir
> la especialidad de un profesional dentro de una compañía cuando declara más
> de una: **cada corrida da números distintos**. Los conteos totales (5.099 y
> 4.866) sí son estables; el desglose por dirección no. La afirmación queda
> suspendida hasta que el desempate sea una regla declarada. No es un problema
> que haya traído D-011: estaba desde que se escribió el ataque, y se ve ahora
> porque el corte se recorrió.

Lo que sí se mantiene y es reproducible es A4: los 5.517 profesionales con
especialidad ambigua concentran USD 20,86M (11,6% del gasto), y **excluirlos
refuerza H2** — la brecha pasa de 12,1 a 14,1 puntos (43,9% vs 29,8%). Es decir:
la ambigüedad de la especialidad no sostiene el hallazgo, lo modera.

### Familia A — artefactos del dato

| Ataque | Resultado |
|---|---|
| A4 excluyendo profesionales con especialidad ambigua | ✓ H1 ✓ H2 (43x · 43,9 vs 29,8) |
| A5 año por año | ✓ H1 ✓ H2 en los cinco — pero revela la **convergencia** de arriba |

### Familia B — sensibilidad a mis decisiones (3/3 sobrevive)

| Ataque | Resultado |
|---|---|
| B1 D-008 alt: la especialidad clínica manda sobre el tipo | ✓ H1 ✓ H2 — **idéntico** (43,6 vs 31,5) |
| B2 D-004 alt: fila entera, sin prorratear | ✓ H1 ✓ H2 (32x · 40,1 vs 27,5) |
| B3 D-002 alt: sólo entidad operativa US | ✓ H1 ✓ H2 (41x · 43,7 vs 31,5) |

**B1 merece un párrafo porque desactiva la preocupación central de D-008.** La
regla de prioridad —que un NP de Family cuente como NP/PA y no como primaria—
mueve USD 18,21M, pero **no cambia el resultado en absoluto**: endocrinología da
43,6% vs 31,5% con las dos reglas. El motivo es que la regla sólo redistribuye
entre NP/PA y primaria, y endocrinología no participa de ese solapamiento. La
decisión importa para leer esas dos categorías, no para el hallazgo del corte.

### Familia C — explicaciones alternativas

| Ataque | Resultado |
|---|---|
| C1 sólo contacto de campo | ✓ H1 — **✗ H2**, se invierte (Lilly 9,4% vs Novo 11,1%) |
| C1b sólo el grupo "voz" | ✓ H1 ✓ H2 (58,2% vs 47,8%) |
| C2 sólo productos previos a la ventana | ✓ H1 ✓ H2 (36x · 46,6 vs 37,9) |

**C1 acota el alcance de H2, igual que pasó en el corte 02.** La diferencia entre
compañías vive en los pagos que compran la voz del profesional; en contacto de
campo, Novo destina levemente **más** a endocrinología que Lilly. H1 —la pirámide
de dinero por cabeza— sobrevive en las dos mitades, aunque el factor cae de 41x
a 6x en campo.

**C2 descarta el efecto lanzamiento**, que en el corte 02 había quedado sin
testear limpiamente. Mirando sólo los seis productos que existían antes de la
ventana, H2 se mantiene (46,6% vs 37,9%): la apuesta de Lilly a endocrinología no
es un artefacto de haber lanzado Mounjaro y Zepbound dentro del período.

## Qué me haría cambiar de opinión

- **Que la convergencia siga.** Es lo más probable que invalide la lectura de
  este corte: en 2025 la brecha es de 3,2 puntos contra 30 en 2023. Si PY2026 la
  cierra del todo, "Lilly apuesta al especialista" pasa a ser una descripción de
  2021–2024, no del presente.
- Que aparezca un sesgo sistemático de reporte que hoy no se ve: la dirección de
  las discrepancias juega en contra de H2, no a favor.
- Que CMS publique un refresh que reexprese algún año de la ventana (los checks
  cortan solos si cambian los sha256).
- Ya **no** me haría cambiar de opinión la regla de prioridad de D-008: da el
  mismo resultado con la regla inversa. Ni el efecto lanzamiento: H2 se sostiene
  mirando sólo productos previos a la ventana.
- **Sigue sin testear** si los endocrinólogos reciben más *porque son menos*.
  Eso exige el universo de endocrinólogos de EEUU, que está fuera de Open
  Payments.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP descargados el
  2026-08-25; sha256 en `scripts/checksums.txt`.
- Taxonomía de especialidades: NUCC, tal como la publica CMS en
  `Covered_Recipient_Specialty_1` (340 valores distintos en la ventana).
- Reconciliación en `findings/checks.md`: 36 comparaciones, Δ = 0,00%.
- **Alcance del check:** cubre el universo de General Payments y el volumen de
  filas de Novo y Lilly. El reparto por especialidad es cálculo propio
  reproducible bajo D-002/D-003/D-004/D-008; CMS no publica agregados por
  especialidad contra los cuales cerrarlo.
