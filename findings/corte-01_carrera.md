# Quién va ganando la carrera GLP-1 depende de qué midas — y las dos respuestas son ciertas

**Corte 01 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: ninguna, el hallazgo es la divergencia (D-005)**

## TL;DR

Entre 2021 y 2025, Novo Nordisk pagó USD 111,05 millones a profesionales de la
salud por sus productos GLP-1 y Eli Lilly USD 69,13 millones. Pero ese total
esconde una inversión: **en 2023 y 2024 Lilly gastó más que Novo** (13,96 vs.
13,12 millones y 17,89 vs. 15,58), mientras que **en cantidad de pagos Novo
lideró los cinco años sin excepción**. La contradicción no es un error de
medición: los dólares los domina el programa de disertantes (59% del dinero en
el 2,1% de los pagos) y los pagos los dominan las comidas (35% del dinero en el
96,7% de los pagos). Son dos preguntas distintas — cuánto se invierte y a
cuántos se llega — y en 2023-2024 tienen ganadores distintos.

**Lo que NO dice:** nada sobre prescripciones, ventas ni cuota de mercado. Open
Payments registra pagos de la industria a profesionales, no conducta clínica ni
resultados comerciales. Tampoco dice por qué Novo recortó: la coincidencia con
la escasez de semaglutida es una hipótesis sin testear (ver más abajo).

## El gráfico

`figures/g1_carrera.png` · `figures/g1_carrera.en.png`

Título: *En dólares Lilly pasó al frente en 2023 y 2024. En cantidad de pagos,
nunca.* Dos paneles apilados sobre el mismo eje temporal; banda gris en los años
donde cada unidad da un ganador distinto.

## Qué es dato y qué es elección mía

| Elemento | Tipo | Fuente / Decisión |
|---|---|---|
| Montos y conteos por año | dato | `analysis/corte-01_carrera.py`, columnas `Total_Amount_of_Payment_USDollars` y `Record_ID` de CMS |
| Naturaleza del pago (disertante, comida) | dato | columna `Nature_of_Payment_or_Transfer_of_Value` |
| Ventana 2021–2025 | elección | **D-001** — PY2021 es el primer año con NP/PA como covered recipients |
| Qué entidades son "Novo" y "Lilly" | elección | **D-002** — lista de 7 IDs, grupo corporativo completo |
| Qué productos son GLP-1 | elección | **D-003** — nueve productos; incluye tirzepatida, que es dual GIP/GLP-1 |
| Cómo se reparte un pago multi-producto | elección | **D-004** — prorrateo entre todos los productos declarados |
| Mostrar ambas unidades sin subordinar una | elección | **D-005** — la divergencia es el hallazgo |
| "Profesionales alcanzados" = `Covered_Recipient_Profile_ID` distintos | elección | del corte; excluye hospitales docentes, que no tienen profile ID |

## Números

Todos salen de `analysis/corte-01_carrera.py` → `findings/cache/corte-01_carrera.json`.
La figura sale de `charts/g1_carrera.py`, que lee sólo ese JSON.

**La carrera, por año**

| Año | Novo USD | Lilly USD | ratio | Novo pagos | Lilly pagos | ratio |
|---|---|---|---|---|---|---|
| 2021 | 24.606.070 | 5.954.237 | 4,13 N | 441.569 | 153.190 | 2,88 N |
| 2022 | 28.849.047 | 12.029.720 | 2,40 N | 473.244 | 199.543 | 2,37 N |
| 2023 | 13.119.218 | **13.959.406** | **0,94 L** | 425.129 | 268.289 | 1,58 N |
| 2024 | 15.578.370 | **17.885.676** | **0,87 L** | 426.795 | 312.032 | 1,37 N |
| 2025 | 28.897.541 | 19.303.449 | 1,50 N | 445.766 | 232.225 | 1,92 N |

Totales del período: **Novo USD 111.050.245,29 en 2.212.503 pagos · Lilly USD
69.132.487,30 en 1.165.279 pagos.**

**Por qué divergen: dos poblaciones de pago**

| Naturaleza | Novo USD | Lilly USD | Novo pagos | Lilly pagos | % del dinero | % de los pagos |
|---|---|---|---|---|---|---|
| Honorarios de disertante | 58.785.091,35 | 47.583.806,25 | 26.211 | 46.352 | 59% | 2,1% |
| Comidas | 42.947.644,97 | 19.673.817,47 | 2.160.488 | 1.106.270 | 35% | 96,7% |

Monto típico: USD 2.243 por honorario en Novo, USD 1.026 en Lilly; unos USD 20
por comida en ambas.

**El mecanismo de la inversión**: el monto promedio por pago de Novo cae de USD
60,96 (2022) a USD 30,86 (2023) y USD 36,50 (2024), mientras Lilly se sostiene
entre 52,03 y 57,32. Novo sostuvo el volumen de contactos y recortó lo caro.

**Alcance** (profesionales distintos, 2025): Novo 114.861 · Lilly 79.526. Novo
lidera esta unidad los cinco años, igual que en cantidad de pagos.

## Intenté matarlo

*(Pendiente: lo llena `/atacar`. El corte todavía no fue sometido a red-team.)*

Ataques que ya conviene tener en la lista:

1. **¿La inversión 2023-2024 sobrevive a otra regla de entidades?** D-002 usa
   grupo corporativo completo; probar con sólo la entidad operativa US.
2. **¿Sobrevive a otra regla de prorrateo?** D-004 mueve el ranking por
   producto; hay que verificar si mueve también el ranking por compañía y año.
3. **¿Es un artefacto de la clase de productos?** Si se excluye tirzepatida
   (D-003), Lilly casi desaparece y la inversión no puede existir.
4. **¿Y si se excluyen los honorarios de disertante?** Si la inversión
   desaparece al sacar esa naturaleza, el hallazgo es sobre un programa
   específico, no sobre "la carrera".

## Qué me haría cambiar de opinión

- Que la inversión de 2023-2024 no sobreviva a los ataques 1 o 2: sería un
  artefacto de mis reglas, no un hecho del mercado.
- Que CMS publique un refresh que reexprese 2023 o 2024 (los checks cortan solos
  si cambian los sha256).
- Que aparezca una filial de Novo o Lilly pagando GLP-1 fuera de la lista de
  D-002; hoy el filtro devuelve exactamente cinco entidades, todas listadas.
- **La hipótesis de la escasez de semaglutida no está testeada.** Novo enfrentó
  restricciones de suministro en ese período, lo que haría racional recortar
  promoción. El dato de este corte es compatible con esa explicación pero **no
  la prueba**: haría falta contrastar contra el calendario de suministro, que
  está fuera de Open Payments. Cualquier afirmación causal necesita esa fuente.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP anuales descargados el
  2026-08-25 desde `openpaymentsdata.cms.gov/datasets/download`; sha256 de cada
  archivo en `scripts/checksums.txt`.
- Agregados oficiales para reconciliación: dataset de resumen
  `/api/1/datastore/query/e0d225fc-8230-401d-8fad-e2262fb22b4c/0` (capturado
  2026-08-25). Resultado en `findings/checks.md`: 36 comparaciones, todas
  Δ = 0,00%.
- **Alcance del check:** el verde cubre el universo de General Payments y el
  volumen de filas de Novo y Lilly. Las cifras de la clase GLP-1 son cálculo
  propio reproducible bajo D-002/D-003/D-004; CMS no publica agregados por
  compañía ni por clase terapéutica contra los cuales cerrarlas.
