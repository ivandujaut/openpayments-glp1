# Registro de reconciliaciones — nada se publica sin cerrar contra la fuente

Lo escribe `/reconciliar` (paso 5 de la skill) después de cada corrida de
`uv run scripts/04_checks.py`. Una entrada por corrida, en orden cronológico
inverso (la más reciente arriba). Las entradas son inmutables: una corrida
nueva es una entrada nueva, nunca una edición de la vieja.

**Regla dura: cualquier Δ > 1% detiene el análisis.** Un check en rojo no se
archiva ni se explica en prosa — se le cuelgan hipótesis ordenadas por
probabilidad, cada una con su test concreto, y el análisis no sigue hasta que
alguna cierre.

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

(vacío — la primera entrada la escribe /reconciliar, cuando existan datos y
`OFICIALES` esté completo en `scripts/04_checks.py`)
