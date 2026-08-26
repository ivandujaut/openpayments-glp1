# Convergieron en proporción y divergieron en estrategia: Novo abrió un frente que Lilly no tiene

**Corte 04 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: dólares absolutos (D-005) · Red-team: 14 ataques, H2 sobrevivió 11/11 · H1 9/11 (depende del pivote)**

## TL;DR

El corte 03 mostró que el peso de endocrinología en el gasto de las dos
compañías converge: de 30 puntos de brecha en 2023 a 3,3 en 2025. Este corte
mira el mismo período **en dólares absolutos** y encuentra que la convergencia
esconde dos movimientos opuestos.

**Lilly retiró USD 1,85M de endocrinología** —su única categoría en baja— y puso
USD 3,59M más en atención primaria. **Novo creció en todas**, y su mayor salto
fue en un grupo que Lilly casi no toca: **+USD 6,43M en cardiología, nefrología
y gastro/hepatología**, que pasan de 0,96M a 7,39M en dos años.

**El red-team acotó una de las dos afirmaciones.** El repliegue de Lilly desde
endocrinología es real desde 2023, pero **no es una tendencia del período
completo**: con 2021 como año base el movimiento se invierte (Lilly +2,32M, Novo
−3,52M). La trayectoria de Novo en endocrinología tiene forma de U —10,60M en
2021, 2,83M en 2023, 7,08M en 2025— así que el corte describe **una reversión
desde un pico, no una dirección sostenida**. La afirmación sobre el frente
emergente, en cambio, sobrevivió los once tests.

Ese grupo lo pagan dos productos: **Wegovy (0,15 → 4,35M) y Ozempic (0,75 →
2,87M)**. En el acumulado del período, Novo destina USD 14,74M a esas
especialidades contra 1,46M de Lilly — una relación de **10 a 1**.

Las dos compañías se parecen más en proporciones porque se movieron en
direcciones distintas, no porque hagan lo mismo.

**Lo que NO dice:** que el movimiento de Novo sea *por* las nuevas indicaciones
cardiovascular y renal de la semaglutida. Es la explicación obvia y encaja en el
tiempo, pero **Open Payments no registra indicaciones** y este archivo no puede
probarlo. Ver "Qué me haría cambiar de opinión".

## El gráfico

`figures/g6_movimiento.png` · `figures/g6_movimiento.en.png`

Barras de cambio desde cero entre 2023 y 2025. Lilly tiene una sola barra
negativa —endocrinología— y Novo ninguna. La comparación con
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
| El nombre "emergentes" | **interpretación** | mía, declarada en D-009: el dato dice a qué especialidad se paga, no por qué indicación |
| Ventana, entidades, productos, prorrateo | elección | **D-001** · **D-002** · **D-003** · **D-004** |

## Números

Todos salen de `analysis/corte-04_convergencia.py` →
`findings/cache/corte-04_convergencia.json`.

**Movimiento entre 2023 y 2025, en USD millones**

| Perfil | Lilly 2023 → 2025 | Δ | Novo 2023 → 2025 | Δ |
|---|---|---|---|---|
| Cardio/nefro/gastro | 0,05 → 0,45 | +0,39 | 0,96 → 7,39 | **+6,43** |
| Endocrinología | 7,21 → 5,36 | **−1,85** | 2,83 → 7,08 | +4,25 |
| Atención primaria | 3,69 → 7,28 | **+3,59** | 4,84 → 7,20 | +2,35 |
| Enfermería y asistentes | 2,58 → 2,70 | +0,13 | 3,82 → 5,91 | +2,09 |
| Medicina de obesidad | 0,00 → 0,48 | +0,48 | 0,19 → 0,41 | +0,21 |
| Resto | 0,43 → 3,04 | +2,61 | 0,47 → 0,88 | +0,41 |

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

## Intenté matarlo

**14 ataques con test corrido: 3 estructurales sobre el origen de los
profesionales y 11 sobre las hipótesis. H2 sobrevivió 11/11 · H1 sobrevivió
9/11.** Scripts: `analysis/ataque-09_frente-nuevo.py` ·
`ataque-10_robustez-convergencia.py`.

- **H1**: entre el pivote y 2025, Lilly redujo su gasto en endocrinología y Novo
  lo aumentó.
- **H2**: Novo destina mucho más que Lilly al grupo emergente.

### El ataque crítico: ¿el frente nuevo es nuevo, o es reetiquetado? (pasa)

El corte 03 encontró que un 3,64% de los profesionales cambia de especialidad
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
| Lilly | **Atención primaria** | **+67,1%** |
| Lilly | Resto | +48,8% |
| Lilly | **Endocrinología** | **−34,6%** |

No es escala: la **composición** del crecimiento es distinta. Cuatro de cada diez
dólares nuevos de Novo fueron al frente emergente; dos de cada tres dólares
nuevos de Lilly fueron a atención primaria, financiados en parte por el recorte
en endocrinología.

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

## Qué me haría cambiar de opinión

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
  cardiólogos desde 2024" es lo máximo que se puede afirmar.
- Que CMS publique un refresh que reexprese algún año de la ventana.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP descargados el
  2026-08-25; sha256 en `scripts/checksums.txt`.
- Reconciliación en `findings/checks.md`: 36 comparaciones, Δ = 0,00%.
- **Alcance del check:** cubre el universo de General Payments y el volumen de
  filas de Novo y Lilly. El reparto por especialidad y producto es cálculo propio
  reproducible bajo D-002/D-003/D-004/D-009; CMS no publica agregados por
  especialidad contra los cuales cerrarlo.
