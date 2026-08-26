# Registro de reconciliaciones — nada se publica sin cerrar contra la fuente

Lo escribe `/reconciliar` (paso 5 de la skill) después de cada corrida de
`uv run scripts/04_checks.py`. Una entrada por corrida, en orden cronológico
inverso (la más reciente arriba). Las entradas son inmutables: una corrida
nueva es una entrada nueva, nunca una edición de la vieja.

**Regla dura: cualquier Δ > 1% detiene el análisis.** Un check en rojo no se
archiva ni se explica en prosa — se le cuelgan hipótesis ordenadas por
probabilidad, cada una con su test concreto, y el análisis no sigue hasta que
alguna cierre.

## Los dos extremos de la cadena

Hay dos verificadores y cubren cosas distintas. Los dos tienen que estar verdes
antes de publicar:

- `scripts/04_checks.py` — el **dato propio contra CMS**. 36 comparaciones.
- `scripts/05_verificar_findings.py` — el **texto publicado contra el dato
  propio**. 93 cifras, más coherencia entre cortes y decisiones citadas.

El segundo nació de un error real: la tabla voz/campo del corte 01 quedó con los
valores previos a D-006 cuando esa decisión movió consultoría de "campo" a "voz".
Las figuras no se vieron afectadas —leen el cache, no el texto— pero el finding
publicaba cuatro cifras viejas. La arquitectura del pipeline protege los
gráficos; el texto escrito a mano es el eslabón que hay que verificar aparte.

## Vigencia — cuándo un check verde deja de servir

Un check vale para **una versión de datos**, identificada por los sha256 de
`scripts/checksums.txt`. Queda vencido si:

- se recargó cualquier año de la ventana (refresh de CMS, redescarga);
- cambió una decisión que toca el filtrado o la agregación (D-002 entidades,
  D-003 productos, D-004 multi-producto, D-001 ventana);
- se amplió `scripts/04_checks.py` con métricas nuevas todavía no corridas.

Un finding solo puede citar números cuyo último check esté **verde y vigente**.
`/derivar` y `/exportar-caso` lo verifican antes de generar nada.

## Formato de entrada

```
## AAAA-MM-DD — 🟢 verde | 🔴 rojo
- **Versión de datos:** PY20XX–PY20XX · descarga AAAA-MM-DD · sha256 en `scripts/checksums.txt`
- **Corrida:** `uv run scripts/04_checks.py`
- **Oficiales:** URL de los agregados de CMS (capturada AAAA-MM-DD)

| métrica | propio | oficial | Δ% |
|---|---|---|---|
| PY20XX total_usd | | | |
| PY20XX total_n | | | |
| PY20XX naturaleza <top 5> | | | |
| PY20XX manufacturer Novo | | | |
| PY20XX manufacturer Lilly | | | |

- **Hipótesis abiertas (solo si rojo):** una por línea, ordenadas por
  probabilidad, cada una con su test concreto y el script que lo corre.
- **Findings habilitados:** los que pueden citar números con este check.
```

## Reconciliaciones

## 2026-08-25 (b) — 🟢 verde · alineación de findings
- **Versión de datos:** PY2021–PY2025 · descarga 2026-08-25 · sin recarga
- **Corrida:** `uv run scripts/05_verificar_findings.py` · **93 cifras, 0 discrepancias**
- **Qué encontró:** la tabla voz/campo del corte 01 tenía los cuatro valores de
  2025 desactualizados (campo Novo 13,31M publicado contra 12,39M real, campo
  Lilly 5,19M contra 4,88M), y en realidad **los cinco años estaban viejos**:
  quedaron de la partición previa a D-006. Corregidos. También dos redondeos
  truncados en el corte 03 (65,09 → 65,10 y 35,24 → 35,25 millones).
- **Qué NO encontró:** ninguna incoherencia entre cortes, y ningún finding
  citando una decisión superada sin aclararlo.
- **Cobertura:** las 93 cifras son las de TL;DR, tablas de Números y titulares de
  los cuatro findings. Las cifras que aparecen sólo dentro de la sección "Intenté
  matarlo" **no** están cubiertas: salen de los scripts de ataque, que no cachean.

## 2026-08-25 — 🟢 verde
- **Versión de datos:** PY2021–PY2025 · descarga 2026-08-25 · sha256 en `scripts/checksums.txt`
- **Corrida:** `uv run scripts/04_checks.py` · 36 comparaciones, todas Δ = 0,00%
- **Oficiales:** dataset de resumen que alimenta openpaymentsdata.cms.gov/summary
  (`/api/1/datastore/query/e0d225fc-8230-401d-8fad-e2262fb22b4c/0`, capturado
  2026-08-25) y API datastore del dataset PY2025 de General Payments
  (`.../fb0b1734-1410-429d-92f6-3f4b35218e5e/0`, capturada 2026-08-25).

**Total de General Payments — agregado publicado por CMS**

| métrica | propio | oficial | Δ% |
|---|---|---|---|
| PY2021 total_usd | 3.270.711.175,77 | 3.270.711.175,77 | 0,00% |
| PY2021 total_n | 11.558.469 | 11.558.469 | 0,00% |
| PY2022 total_usd | 3.845.496.173,61 | 3.845.496.173,61 | 0,00% |
| PY2022 total_n | 13.322.266 | 13.322.266 | 0,00% |
| PY2023 total_usd | 3.328.079.279,62 | 3.328.079.279,62 | 0,00% |
| PY2023 total_n | 14.734.121 | 14.734.121 | 0,00% |
| PY2024 total_usd | 3.424.344.413,22 | 3.424.344.413,22 | 0,00% |
| PY2024 total_n | 15.498.687 | 15.498.687 | 0,00% |
| PY2025 total_usd | 3.923.550.962,80 | 3.923.550.962,80 | 0,00% |
| PY2025 total_n | 16.131.856 | 16.131.856 | 0,00% |

**Disputados y pagos a médicos** — 20 comparaciones (4 métricas × 5 años), todas
Δ = 0,00%. Disputados PY2021–PY2025: 309 · 443 · 251 · 327 · 305 registros.
Pagos a médicos PY2025: USD 2.624.554.749,77 sobre 10.129.623 registros.

**Contra la API datastore de CMS** (misma data, otra cadena de entrega: verifica
que ZIP → parquet → vista no corrompió nada)

| métrica | propio | oficial | Δ% |
|---|---|---|---|
| PY2025 entidad 100000000144 (Novo Nordisk Inc) | 512.725 | 512.725 | 0,00% |
| PY2025 entidad 100000000066 (Lilly USA, LLC) | 425.910 | 425.910 | 0,00% |
| PY2025 Food and Beverage | 14.764.648 | 14.764.648 | 0,00% |
| PY2025 Travel and Lodging | 623.496 | 623.496 | 0,00% |
| PY2025 Consulting Fee | 205.079 | 205.079 | 0,00% |
| PY2025 Education | 161.500 | 161.500 | 0,00% |

- **Hipótesis abiertas:** ninguna. Los 36 Δ son cero.

- **Cobertura, con sus huecos declarados:**
  - **No hay agregado oficial por manufacturer.** El dataset de resumen de CMS
    no desagrega por compañía, así que la verificación de D-002 se hace contra
    la API datastore: confirma que el pipeline no perdió ni duplicó filas de
    Novo y Lilly, pero **no** valida la regla de entidades contra una definición
    externa, porque CMS no publica una.
  - **Sólo 4 de las 5 naturalezas del top 5.** Falta "Compensation for services
    other than consulting, …" (249.154 filas): su valor contiene comas, que
    rompen el parser de `conditions` de la API. Las cuatro verificadas cubren
    el 97,7% de las filas de PY2025.
  - **El check por entidad y por naturaleza es sólo de PY2025.** Cada consulta
    a la API es una navegación; extenderlo a los cinco años es posible pero no
    se hizo en esta corrida.
  - **`Companies Making Payments` queda fuera a propósito.** El agregado de CMS
    (1.833 en PY2025) cuenta compañías de General + Research + Ownership; el
    dato propio sólo tiene General (1.757 pagadores distintos). Compararlos daría
    un rojo espurio de −4,15%.
  - **Nada de esto valida los números de GLP-1.** Lo reconciliado es el universo
    completo de General Payments y el volumen de las dos compañías. Las cifras
    de D-003 y D-004 (Novo 111,05M vs. Lilly 69,13M) descansan en reglas propias
    que CMS no publica y **no tienen contraparte oficial contra la cual cerrar**.

- **Findings habilitados:** cualquiera que cite totales de General Payments
  PY2021–PY2025, conteos por año, disputados, pagos a médicos, o volumen de
  filas de Novo Nordisk Inc y Lilly USA en PY2025. Los agregados de la clase
  GLP-1 quedan habilitados **como cálculo propio reproducible**, no como cifra
  reconciliada: el writeup debe presentarlos así.
