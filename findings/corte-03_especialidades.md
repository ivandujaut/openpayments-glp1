# 5.367 endocrinólogos reciben casi el doble que 120.145 enfermeros y asistentes

**Corte 03 — 2026-08-25 · Datos: PY2021–PY2025 (descarga 2026-08-25) · Checks: 🟢 (2026-08-25) · Unidad líder: dólares (D-005) · Red-team: pendiente**

## TL;DR

El dinero de GLP-1 no sigue al volumen de prescriptores: sigue al especialista.
**5.367 endocrinólogos recibieron USD 65,09 millones entre 2021 y 2025, mientras
120.145 enfermeros y asistentes médicos recibieron 35,24 millones.** Son USD
12.129 por endocrinólogo contra 293 por NP/PA: un factor de **41**.

Las dos compañías apuestan al mismo perfil, pero en dosis distintas.
**Endocrinología es el 43,6% del gasto de Lilly y el 31,5% del de Novo.** Novo
compensa repartiendo más al canal de volumen: 21,8% a NP/PA contra 16,0% de
Lilly, y más al "resto" de especialidades (16,2% contra 9,2%).

Esto encaja con lo que ya mostraron los cortes anteriores. El corte 01 encontró
que la ventaja de Lilly vive en pagos que compran la voz del profesional; el
corte 02, que su círculo de "voz" es la mitad de grande que el de Novo. Este
corte nombra a ese círculo: **son endocrinólogos**.

**Lo que NO dice:** nada sobre prescripciones ni sobre si el dinero cambia
conductas. Tampoco dice que los endocrinólogos "cuesten más" — dice que reciben
más, que es un hecho sobre la estrategia de las compañías, no sobre las personas.

## El gráfico

`figures/g4_especialidades.png` · `figures/g4_especialidades.en.png`

Barras horizontales por perfil, con el tamaño de cada población y el dinero por
cabeza en la columna derecha. Ese contraste —cuánta gente hay contra cuánto
recibe cada uno— es el hallazgo; la barra sola no lo muestra.

## Qué es dato y qué es elección mía

| Elemento | Tipo | Fuente / Decisión |
|---|---|---|
| Especialidad declarada | dato | `Covered_Recipient_Specialty_1`, taxonomía NUCC de CMS |
| Gasto y conteos por perfil | dato | `analysis/corte-03_especialidades.py` |
| Ventana, entidades, productos, prorrateo | elección | **D-001** · **D-002** · **D-003** · **D-004** |
| Las cinco categorías y su orden de prioridad | elección | **D-008** — un NP de Family cuenta como NP/PA, no como primaria |
| Agrupación "voz" / "campo" | elección | **D-006** |
| Dólares como unidad líder | elección | **D-005** — declarada por corte |

## Números

Todos salen de `analysis/corte-03_especialidades.py` →
`findings/cache/corte-03_especialidades.json`.

| Perfil | Novo USD | Lilly USD | % Novo | % Lilly | Profesionales | USD por cabeza |
|---|---|---|---|---|---|---|
| Endocrinología | 34,98M | 30,11M | 31,5% | **43,6%** | 5.367 | **12.129** |
| Atención primaria (médico) | 32,52M | 20,65M | 29,3% | 29,9% | 82.994 | 641 |
| Enfermería y asistentes | 24,20M | 11,04M | **21,8%** | 16,0% | 120.145 | 293 |
| Medicina de obesidad | 1,24M | 0,94M | 1,1% | 1,4% | 242 | 9.002 |
| Resto | 18,03M | 6,38M | 16,2% | 9,2% | 44.860 | 544 |

**La pirámide, en una línea:** endocrinología es el 2,1% de los profesionales
alcanzados y el 36% del dinero.

**Medicina de obesidad es minúscula pero cara:** 242 profesionales a USD 9.002
por cabeza, el segundo valor más alto de la tabla. Es una especialidad joven y
el dato no permite decir si crece; ese es un corte aparte.

## Intenté matarlo

*(Pendiente: falta correr `/atacar`.)* Los ataques que ya se ven necesarios:

1. **¿La brecha 43,6% vs 31,5% sobrevive año a año?** Todo el corte es
   acumulado. Si aparece sólo en los años de lanzamiento de Mounjaro y Zepbound,
   el hallazgo es sobre lanzamientos.
2. **¿Es un efecto de "voz"?** Si el reparto por perfil se calcula sólo sobre
   contacto de campo, ¿se mantiene la diferencia entre compañías? Podría ser que
   toda la brecha viva en los honorarios, como pasó en el corte 01.
3. **¿La regla de prioridad de D-008 fabrica el resultado?** Mandar los NP/PA de
   primaria a NP/PA mueve USD 18,21M. Test: recalcular con la regla inversa.
4. **¿La especialidad declarada es confiable?** Es autodeclarada por el
   reportante. Test: ver si un mismo `Profile_ID` cambia de especialidad entre
   años o entre compañías.
5. **¿Los endocrinólogos reciben más porque son menos?** Test de composición:
   comparar contra el universo de endocrinólogos de EEUU, que está fuera de Open
   Payments.

## Qué me haría cambiar de opinión

- Que el ataque 4 muestre que la especialidad declarada es inestable: todo el
  corte descansa en un campo autodeclarado.
- Que la brecha entre compañías desaparezca al mirar sólo contacto de campo, lo
  que la volvería un subproducto del corte 01 y no un hallazgo propio.
- Que la regla de prioridad de D-008 resulte determinante (ataque 3).
- Que CMS publique un refresh que reexprese algún año de la ventana.

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
