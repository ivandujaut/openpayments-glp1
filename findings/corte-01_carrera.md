# Lilly nunca gastó más que Novo en GLP-1 — salvo en una cosa: su programa de disertantes

**Corte 01 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: ninguna, el hallazgo es la divergencia (D-005) · Red-team: 10 ataques, sobrevivió 8 (ver más abajo)**

## TL;DR

Entre 2021 y 2025, Novo Nordisk pagó USD 111,05 millones a profesionales de la
salud por sus productos GLP-1 y Eli Lilly USD 69,13 millones. En el agregado
anual Lilly parece pasar al frente en 2023 y 2024 — pero **esa ventaja es
enteramente su programa de disertantes**: al excluir esa única naturaleza de
pago, Novo supera a Lilly **los cinco años**, con ratios de 1,46x a 7,24x.

Lo que Lilly hizo fue construir un programa de disertantes que casi duplicó su
tamaño (de 6.517 a 12.485 pagos entre 2021 y 2025) mientras Novo achicaba el
suyo (de 6.809 a 4.898). En todo lo demás — comidas, viajes, consultoría — y en
cantidad de pagos y profesionales alcanzados, Novo lideró siempre.

**Lo que NO dice:** nada sobre prescripciones, ventas ni cuota de mercado. Open
Payments registra pagos de la industria a profesionales, no conducta clínica ni
resultados comerciales. Tampoco explica *por qué* Novo recortó: la coincidencia
con la escasez de semaglutida es una hipótesis sin testear.

## Los gráficos

`figures/g1_carrera.png` · `.en.png` — la carrera en las dos unidades, con los
años en que dan ganadores distintos sombreados.

`figures/g2_disertantes.png` · `.en.png` — **el gráfico principal tras el
red-team.** Arriba, sólo honorarios de disertante: las líneas se cruzan. Abajo,
todo el resto: nunca se tocan. Ese vacío en el panel de abajo es el hallazgo.

## Qué es dato y qué es elección mía

| Elemento | Tipo | Fuente / Decisión |
|---|---|---|
| Montos y conteos por año | dato | `analysis/corte-01_carrera.py`, columnas `Total_Amount_of_Payment_USDollars` y `Record_ID` |
| Naturaleza del pago | dato | columna `Nature_of_Payment_or_Transfer_of_Value` |
| Ventana 2021–2025 | elección | **D-001** |
| Qué entidades son "Novo" y "Lilly" | elección | **D-002** — 7 IDs, grupo corporativo completo |
| Qué productos son GLP-1 | elección | **D-003** — nueve; incluye tirzepatida, que es dual GIP/GLP-1 |
| Reparto en pagos multi-producto | elección | **D-004** — prorrateo |
| Mostrar ambas unidades sin subordinar una | elección | **D-005** |
| Separar "disertante" del resto | elección | del ataque 03 (C2), no de una decisión previa |

## Números

Todos salen de `analysis/corte-01_carrera.py` → `findings/cache/corte-01_carrera.json`.
Las figuras leen sólo ese JSON.

**La carrera, agregado anual**

| Año | Novo USD | Lilly USD | ratio | Novo pagos | Lilly pagos | ratio |
|---|---|---|---|---|---|---|
| 2021 | 24.606.070 | 5.954.237 | 4,13 N | 441.569 | 153.190 | 2,88 N |
| 2022 | 28.849.047 | 12.029.720 | 2,40 N | 473.244 | 199.543 | 2,37 N |
| 2023 | 13.119.218 | **13.959.406** | 0,94 L | 425.129 | 268.289 | 1,58 N |
| 2024 | 15.578.370 | **17.885.676** | 0,87 L | 426.795 | 312.032 | 1,37 N |
| 2025 | 28.897.541 | 19.303.449 | 1,50 N | 445.766 | 232.225 | 1,92 N |

Totales: **Novo USD 111.050.245,29 en 2.212.503 pagos · Lilly USD 69.132.487,30
en 1.165.279 pagos.**

**Lo que el agregado escondía** (USD millones, `analysis/ataque-03_explicaciones-negocio.py`)

| Año | Disertantes: Novo | Lilly | Todo el resto: Novo | Lilly |
|---|---|---|---|---|
| 2021 | 14,42 | 4,55 | 10,18 | 1,41 |
| 2022 | 17,22 | 8,66 | 11,63 | 3,37 |
| 2023 | 5,21 | **8,71** | 7,90 | 5,25 |
| 2024 | 6,35 | **11,56** | 9,23 | 6,33 |
| 2025 | 15,58 | 14,11 | 13,31 | 5,19 |

**El mecanismo, en cantidad de pagos de disertante:** Lilly 6.517 → 8.142 →
8.220 → 10.988 → **12.485**. Novo 6.809 → 6.223 → 4.122 → 4.159 → **4.898**.
Lilly casi duplicó su programa; Novo lo redujo a dos tercios.

**Alcance** (profesionales distintos, 2025): Novo 114.861 · Lilly 79.526.

## Intenté matarlo

**10 ataques con test corrido. H1 sobrevivió 8/10 · H2 sobrevivió 9/10.**
Scripts: `analysis/ataque-01_sensibilidad-decisiones.py` ·
`ataque-02_artefactos-dato.py` · `ataque-03_explicaciones-negocio.py`.

Hipótesis atacadas:
- **H1**: Lilly > Novo en dólares exactamente en 2023 y 2024.
- **H2**: Novo > Lilly en cantidad de pagos los cinco años.

### Familia B — sensibilidad a mis decisiones (4/4 sobrevive, ambas)
| Ataque | Resultado |
|---|---|
| D-002 alt: sólo entidad operativa US | ✓ H1 ✓ H2 |
| D-004 alt: fila entera a cada producto | ✓ H1 ✓ H2 |
| D-004 alt: sólo el primer producto declarado | ✓ H1 ✓ H2 |
| D-003 alt: sin legacy (Victoza, Saxenda, Trulicity, Xultophy) | ✓ H1 ✓ H2 |

Ninguna de las alternativas que las decisiones rechazaron cambia el resultado.

### Familia A — artefactos del dato (3/3 sobrevive, ambas)
| Ataque | Resultado |
|---|---|
| A1 sólo médicos (excluye NP/PA y hospitales docentes) | ✓ H1 ✓ H2 |
| A2 sin registros disputados | ✓ H1 ✓ H2 |
| A3 pagos reales, ponderando por `Number_of_Payments` | ✓ H1 ✓ H2 |
| A4 productos en Diabetes/Obesity fuera de la lista de D-003 | descriptivo: 19 productos, **ninguno es GLP-1** (SGLT2, DPP-4, insulinas, glucagón) |

### Familia C — explicaciones alternativas (H1 1/3, H2 2/3) ← acá se rompe

| Ataque | Resultado |
|---|---|
| C1 sin el 1% de pagos más caros de cada compañía/año | **✗ H1** ✓ H2 |
| C2 **sin honorarios de disertante** | **✗ H1** ✓ H2 |
| C2b sólo honorarios de disertante | ✓ H1 **✗ H2** |

**C2 mató H1 y reescribió el finding.** Sin honorarios de disertante, Lilly no
supera a Novo **en ningún año**. La ventaja de Lilly en el agregado no es "Lilly
invirtió más": es "Lilly invirtió más en un programa". El título original de este
finding decía *"En dólares Lilly pasó al frente en 2023 y 2024"* — cierto como
aritmética, engañoso como afirmación sobre la carrera. Cambiado.

**C1 mostró algo que no buscaba:** al recortar el 1% de pagos más caros, Lilly
supera a Novo también en **2025**. El liderazgo de Novo en 2025 depende de su
cola de pagos grandes; en el cuerpo de la distribución, Lilly ya estaba arriba.
Es un hallazgo colateral que merece su propio corte.

**C2b es la contracara y confirma el mecanismo:** en el universo de honorarios de
disertante, Novo gana en cantidad de pagos sólo 1 de 5 años. Ahí Lilly domina en
volumen *y* en dinero.

**C3 (descriptivo, sin veredicto):** el gasto de Lilly en 2023-2024 se concentra
en Mounjaro (13,53M y 11,89M), con Zepbound sumando desde 2024 (5,95M) y
Trulicity ya extinguido (0,04M). Del lado de Novo, Rybelsus se desploma de 13,32M
a 4,01M y Ozempic de 10,67M a 4,45M entre 2022 y 2023. Compatible con un pico de
lanzamiento del lado de Lilly, pero no lo prueba.

## Qué me haría cambiar de opinión

- Que aparezca una razón por la cual los honorarios de disertante **no** deban
  separarse del resto: hoy la separación es una elección mía, nacida del ataque,
  no una decisión registrada previa. Merece su propia D-NNN si el corte se
  publica.
- Que CMS publique un refresh que reexprese 2023 o 2024 (los checks cortan solos
  si cambian los sha256 de `scripts/checksums.txt`).
- Que aparezca una filial de Novo o Lilly pagando GLP-1 fuera de la lista de
  D-002; hoy el filtro devuelve exactamente cinco entidades, todas listadas.
- **La hipótesis de la escasez de semaglutida sigue sin testear.** Novo enfrentó
  restricciones de suministro en el período en que recortó. El dato es compatible
  con esa explicación pero **no la prueba**: contrastarla exige el calendario de
  suministro, fuera de Open Payments. Cualquier afirmación causal necesita esa
  fuente.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP anuales descargados el
  2026-08-25 desde `openpaymentsdata.cms.gov/datasets/download`; sha256 en
  `scripts/checksums.txt`.
- Agregados oficiales: dataset de resumen
  `/api/1/datastore/query/e0d225fc-8230-401d-8fad-e2262fb22b4c/0` (capturado
  2026-08-25). Resultado en `findings/checks.md`: 36 comparaciones, Δ = 0,00%.
- **Alcance del check:** el verde cubre el universo de General Payments y el
  volumen de filas de Novo y Lilly. Las cifras de la clase GLP-1 son cálculo
  propio reproducible bajo D-002/D-003/D-004; CMS no publica agregados por
  compañía ni por clase terapéutica contra los cuales cerrarlas.
