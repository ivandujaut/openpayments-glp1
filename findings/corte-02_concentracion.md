# Cien médicos concentran el 36% de lo que Lilly gasta en GLP-1 — y trabajan el doble que los de Novo

**Corte 02 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Métrica líder: % del gasto al top 100 (D-007) · Red-team: pendiente**

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

**Perfil del top 100** — el hallazgo más nítido del corte:

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

*(Pendiente: falta correr `/atacar`.)* Los ataques que ya se ven necesarios:

1. **¿Es un artefacto de `Profile_ID`?** Si un mismo profesional tuviera varios
   IDs, o si un ID agrupara a más de una persona, la concentración estaría mal
   medida. Test: contrastar `Profile_ID` contra `Covered_Recipient_NPI`.
2. **¿Sobrevive año a año?** Todos los números son del acumulado 2021–2025. Si la
   brecha aparece en un solo año, el hallazgo es otro.
3. **¿Es el tamaño de red y no la estrategia?** Novo llega a 37% más
   profesionales. Test: recortar ambas redes al mismo tamaño y recalcular.
4. **¿Lo explica el mix de productos?** Zepbound y Mounjaro se lanzaron dentro de
   la ventana; un lanzamiento concentra gasto en pocos líderes de opinión.
5. **¿Los 431 pagos son personas trabajando o agregación contable?**
   `Number_of_Payments_Included_in_Total_Amount` puede inflar el conteo.

## Qué me haría cambiar de opinión

- Que el ataque 1 muestre que `Profile_ID` no identifica personas de forma
  estable: toda la métrica descansa en eso.
- Que la brecha desaparezca al emparejar el tamaño de las redes (ataque 3), lo
  que convertiría el hallazgo en un artefacto de alcance.
- Que CMS publique un refresh que reexprese algún año de la ventana.
- Que aparezca concentración institucional que el `Profile_ID` no capta: varios
  profesionales de un mismo centro cuentan hoy como independientes.

## Fuentes

- CMS Open Payments, General Payments PY2021–PY2025. ZIP descargados el
  2026-08-25; sha256 en `scripts/checksums.txt`.
- Reconciliación en `findings/checks.md`: 36 comparaciones, Δ = 0,00%.
- **Alcance del check:** cubre el universo de General Payments y el volumen de
  filas de Novo y Lilly. Las cifras de concentración son cálculo propio
  reproducible bajo D-002/D-003/D-004/D-007; CMS no publica agregados por
  profesional contra los cuales cerrarlas.
