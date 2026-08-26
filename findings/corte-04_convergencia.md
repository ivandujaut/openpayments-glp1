# Convergieron en proporción y divergieron en estrategia: Novo abrió un frente que Lilly no tiene

**Corte 04 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: dólares absolutos (D-005) · Red-team: pendiente**

## TL;DR

El corte 03 mostró que el peso de endocrinología en el gasto de las dos
compañías converge: de 30 puntos de brecha en 2023 a 3,3 en 2025. Este corte
mira el mismo período **en dólares absolutos** y encuentra que la convergencia
esconde dos movimientos opuestos.

**Lilly retiró USD 1,85M de endocrinología** —su única categoría en baja— y puso
USD 3,59M más en atención primaria. **Novo creció en todas**, y su mayor salto
fue en un grupo que Lilly casi no toca: **+USD 6,43M en cardiología, nefrología
y gastro/hepatología**, que pasan de 0,96M a 7,39M en dos años.

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

*(Pendiente: falta correr `/atacar`.)* Los ataques que ya se ven necesarios:

1. **¿El pivote 2023 fabrica el resultado?** Es una elección del corte. Test:
   repetir con 2021, 2022 y 2024 como año base.
2. **¿Es un efecto de escala?** El gasto total de Novo creció más que el de
   Lilly en el período, así que "creció en todo" podría ser aritmética. Test:
   normalizar por el gasto total de cada compañía y ver si el orden se mantiene.
3. **¿Sobrevive a D-009?** La categoría emergente es una elección reciente. Test:
   repetir con cardiología sola, y con las tres separadas.
4. **¿Es "voz" otra vez?** Los dos cortes anteriores encontraron que la
   diferencia entre compañías vive en los pagos de disertante. Test: repetir
   mirando sólo contacto de campo.
5. **¿Los cardiólogos son nuevos o son los mismos de antes?** Si son los mismos
   profesionales que ya recibían pagos y sólo cambió su etiqueta declarada, el
   "frente nuevo" es un artefacto de reporte. Test: seguir `Profile_ID` en el
   tiempo.

## Qué me haría cambiar de opinión

- **Que el ataque 5 muestre que los cardiólogos no son nuevos.** Es el riesgo
  más concreto: el corte 03 ya encontró que un 3,64% de los profesionales cambia
  de especialidad declarada entre años.
- Que el movimiento desaparezca al normalizar por escala (ataque 2), lo que
  volvería el hallazgo una consecuencia de que Novo gastó más.
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
