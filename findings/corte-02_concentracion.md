# Cien médicos concentran el 36% de lo que Lilly gasta en GLP-1 — y trabajan el doble que los de Novo

**Corte 02 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Métrica líder: % del gasto al top 100 (D-007) · Red-team: 20 ataques, sobrevivió 19 (H1) / 18 (H2)**

## TL;DR

El gasto en GLP-1 está extremadamente concentrado en las dos compañías, pero
**Lilly concentra 1,74x más que Novo**: sus cien profesionales mejor pagos
reciben el **35,6%** de todo su gasto GLP-1, contra el **20,4%** en Novo. El
Gini confirma la dirección (0,885 vs. 0,855) y el orden se mantiene en los cinco
cortes probados, del top 10 al top 1.000.

Lo llamativo no es el dinero sino el ritmo: **entrar al top 100 cuesta casi lo
mismo en las dos compañías** (USD 172.608 en Lilly, USD 172.768 en Novo), pero
los cien de Lilly acumulan **431 pagos promedio contra 246 de Novo**. Reciben
cifras parecidas repartidas en casi el doble de contactos.

**El red-team encontró algo más nítido que la métrica original.** La
concentración de Lilly no es general: vive entera en su programa de "voz"
(D-006), que resulta ser un círculo mucho más chico. **Lilly reparte USD 48,42M
entre 657 profesionales; Novo reparte USD 61,73M entre 1.139.** En el contacto
de campo el signo se invierte —Novo concentra algo más (6,72% vs. 4,77%)—
aunque ahí las dos son muy dispersas.

Este corte responde una pregunta que dejó abierta el red-team del corte 01: el
ataque C1 mostró que al recortar el 1% de pagos más caros, Lilly supera a Novo
también en 2025 — o sea que el liderazgo de Novo ese año vivía en su cola de
pagos grandes. La cola existe en las dos, pero **la de Lilly es más pesada**.

**Lo que NO dice:** nada sobre prescripciones, influencia ni conducta clínica.
Tampoco identifica a nadie: el corte trabaja con `Profile_ID` y reporta sólo
perfiles agregados, nunca nombres.

## El gráfico

`figures/g3_concentracion.png` · `figures/g3_concentracion.en.png`

Barras agrupadas por corte, con el top 100 sombreado por ser la métrica líder.
Se eligió barras y no una curva de Lorenz porque la curva sube casi vertical en
el primer 1% y deja el resto plano: ilegible en escala lineal.

## Qué es dato y qué es elección mía

| Elemento | Tipo | Fuente / Decisión |
|---|---|---|
| Gasto por profesional | dato | `analysis/corte-02_concentracion.py`, agregando por `Covered_Recipient_Profile_ID` |
| Tamaño de cada red | dato | profesionales distintos con al menos un pago GLP-1 |
| Ventana, entidades, productos, prorrateo | elección | **D-001** · **D-002** · **D-003** · **D-004** |
| Agrupación "voz" / "campo" | elección | **D-006** |
| Top 100 como métrica, Gini como control | elección | **D-007** — el top 1% mezclaría concentración con tamaño de red |
| Excluir hospitales docentes | forzado por el dato | no tienen `Profile_ID`: 43 pagos, USD 75.300 (0,04%) |

## Números

Todos salen de `analysis/corte-02_concentracion.py` →
`findings/cache/corte-02_concentracion.json`.

**Concentración por compañía**

| | Lilly | Novo |
|---|---|---|
| Profesionales en la red | 152.493 | 209.450 |
| Gasto GLP-1 | USD 69,13M | USD 110,97M |
| **% al top 100** | **35,64%** | **20,44%** |
| % al top 1% de la red | 74,30% | 64,92% |
| Gini | 0,8846 | 0,8549 |
| Mediana por profesional | USD 60,55 | USD 94,37 |
| El profesional que más recibió | USD 403.511,38 | USD 358.682,84 |

**El orden no depende del corte** (% del gasto al top N):

| | top 10 | top 50 | top 100 | top 500 | top 1.000 |
|---|---|---|---|---|---|
| Lilly | 5,24 | 21,14 | **35,64** | 72,17 | 73,60 |
| Novo | 2,83 | 11,79 | **20,44** | 54,23 | 62,79 |

**Los dos círculos de "voz"** — lo que encontró el ataque C3:

| | Lilly | Novo |
|---|---|---|
| Profesionales que reciben pagos de "voz" | **657** | **1.139** |
| Gasto en "voz" | USD 48,42M | USD 61,73M |
| Promedio por profesional | USD 73.700 | USD 54.193 |
| % de ese gasto al top 100 | 49,06% | 32,11% |

Y en contacto de campo, el signo se invierte:

| | Lilly | Novo |
|---|---|---|
| Profesionales | 152.430 | 209.369 |
| Gasto | USD 20,71M | USD 49,25M |
| % al top 100 | 4,77% | **6,72%** |

**Perfil del top 100** — el hallazgo del corte en la métrica declarada:

| | Lilly | Novo |
|---|---|---|
| Gasto promedio | USD 246.402 | USD 226.796 |
| Umbral de entrada | USD 172.608 | USD 172.768 |
| **Pagos promedio** | **431,3** | **246,4** |
| % de su gasto en "voz" (D-006) | 96,4% | 87,2% |

Nota de reconciliación: el total de Novo acá es USD 110,97M contra 111,05M en el
corte 01. La diferencia son los USD 75.300 de hospitales docentes, que no tienen
`Profile_ID` y quedan fuera de toda métrica por profesional.

## Intenté matarlo

**20 ataques con test corrido. H1 sobrevivió 19/20 · H2 sobrevivió 18/20.**
Scripts: `analysis/ataque-04_identidad-receptor.py` ·
`ataque-05_robustez-concentracion.py` · `ataque-06_concentracion-negocio.py`.

- **H1**: Lilly concentra más que Novo (% del gasto al top 100).
- **H2**: El top 100 de Lilly acumula más pagos que el de Novo.

### El ataque crítico: ¿mide personas o identificadores? (3/3 pasa)

Toda la métrica descansa en que `Covered_Recipient_Profile_ID` identifique una
persona de forma estable. Contrastado contra `Covered_Recipient_NPI`:

| Test | Resultado |
|---|---|
| Profile_ID con más de un NPI (inflaría la concentración) | **0** |
| NPI bajo más de un Profile_ID (fragmentaría) | **0** |
| Recalcular todo con NPI como clave | 35,65% vs 20,46% — **ratio 1,74x idéntico** |

La correspondencia es uno a uno. La métrica mide personas.

### Familia A — artefactos del dato

| Ataque | Resultado |
|---|---|
| A2 año por año (2021 · 2022 · 2023 · 2024 · 2025) | ✓ H1 en los cinco (2,23x · 2,05x · 1,84x · 1,57x · 1,72x) — **✗ H2 sólo en 2021** |
| A3 pagos ponderados por `Number_of_Payments` | ✓ H1 ✓ H2 (443 vs 283) |
| A4 sólo médicos, sin NP/PA | ✓ H1 ✓ H2 (41,80 vs 25,77) |

**H2 falla en 2021 y eso es informativo, no un problema:** ese año el top 100 de
Novo acumulaba más pagos que el de Lilly (80 vs 64). Lilly construyó su programa
después — de 64 pagos promedio en 2021 a 118 en 2024. El patrón que describe el
corte se forma dentro de la ventana, no la precede.

### Familia B — sensibilidad a mis decisiones (4/4 sobrevive)

| Ataque | Resultado |
|---|---|
| B1 D-002 alt: sólo entidad operativa US | ✓ H1 ✓ H2 (1,75x) |
| B2 D-004 alt: fila entera, sin prorratear | ✓ H1 ✓ H2 (1,88x) |
| B3 D-007 alt: top 1% y Gini, las métricas rechazadas | ✓ ambas ordenan igual (74,30 vs 64,92 · 0,8846 vs 0,8549) |

### Familia C — explicaciones alternativas

| Ataque | Resultado |
|---|---|
| C1 redes recortadas a 1.000 / 10.000 / 50.000 / 152.493 | ✓ H1 ✓ H2 en las cuatro (1,49x a 1,73x) |
| C2 sin productos lanzados en la ventana | **no concluyente**, ver abajo |
| C3 sólo contacto de campo | **✗ H1** — el signo se invierte (0,71x) |
| C3b sólo el grupo "voz" | ✓ H1 ✓ H2 (1,53x) |

**C1 era la explicación más plausible y falló.** Novo llega a 37% más
profesionales, así que su denominador podría diluir el peso del top 100 por
construcción. Emparejando las redes a cuatro tamaños distintos, Lilly sigue
concentrando más en todos. No es artefacto de alcance.

**C2 no concluye, y hay que decirlo:** al excluir Mounjaro, Zepbound y Wegovy, a
Lilly le queda **sólo Trulicity (USD 8,27M)** contra USD 85,25M de Novo. La
comparación deja de ser entre estrategias y pasa a ser entre una compañía con
negocio y otra sin él. El test da 2,68x a favor de Lilly, pero ese número no
significa nada: la muestra quedó degenerada. **Un test limpio del efecto
lanzamiento exige otro diseño** — por ejemplo excluir sólo el año de lanzamiento
de cada producto — y queda pendiente.

**C3 invirtió el signo y refinó el hallazgo.** Mirando sólo contacto de campo,
Novo concentra más que Lilly (6,72% vs. 4,77%). La concentración de Lilly no es
un rasgo general de su gasto: **es un rasgo de su programa de voz**, que reparte
USD 48,42M entre 657 profesionales contra los 1.139 de Novo. Eso no mata H1 en el
agregado —que es lo que el corte afirma— pero acota su alcance, y el TL;DR lo
dice.

## Qué me haría cambiar de opinión

- **Un test limpio del efecto lanzamiento**, que C2 no logró ser. Si al excluir
  sólo el año de lanzamiento de cada producto la brecha desapareciera, el
  hallazgo sería sobre lanzamientos y no sobre estrategia sostenida.
- Que aparezca concentración institucional que el `Profile_ID` no capta: varios
  profesionales de un mismo centro cuentan hoy como independientes, y una red
  aparentemente dispersa podría ser un puñado de instituciones.
- Que CMS publique un refresh que reexprese algún año de la ventana (los checks
  cortan solos si cambian los sha256).
- Ya **no** me haría cambiar de opinión que `Profile_ID` sea inestable: quedó
  descartado con NPI (0 colisiones en ambas direcciones). Ni el tamaño de red:
  la brecha aguanta emparejando las redes a cuatro tamaños distintos.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP descargados el
  2026-08-25; sha256 en `scripts/checksums.txt`.
- Reconciliación en `findings/checks.md`: 36 comparaciones, Δ = 0,00%.
- **Alcance del check:** cubre el universo de General Payments y el volumen de
  filas de Novo y Lilly. Las cifras de concentración son cálculo propio
  reproducible bajo D-002/D-003/D-004/D-007; CMS no publica agregados por
  profesional contra los cuales cerrarlas.
