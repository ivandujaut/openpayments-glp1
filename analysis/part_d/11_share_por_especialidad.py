"""La condición de muerte de la tesis: ¿la puerta es el honorario o la especialidad?

La tesis acordada dice que pasar de recibir comidas a cobrar honorarios va con
recetar seis o siete veces más GLP-1 como proporción de la práctica (C10). Hay
una explicación alternativa que la mataría entera: que los que cobran honorarios
sean endocrinólogos, y que el share alto sea de la especialidad y no del pago.

Este script la pone a prueba de la única forma que la mata de verdad: comparando
**dentro de cada especialidad**. Si los endocrinólogos con honorarios tienen el
mismo share que los endocrinólogos sin pago, la puerta es la especialidad y la
tesis se cae.

Dos cortes:

1. `share_por_especialidad_y_clase`: el share mediano por (especialidad, clase de
   pago), que es la comparación que decide.
2. `composicion`: qué especialidad es cada clase de pago, para saber cuánto de la
   brecha bruta podía ser composición desde el principio.

La especialidad sale del `Prscrbr_Type` de Part D y **no** de Open Payments, por
una razón que no es de gusto: los que no cobraron nada no tienen especialidad en
Open Payments, así que el grupo de control no existiría. C12 midió que las dos
clasificaciones coinciden en el 96,30% de los NPI que están de los dos lados.

Salida: findings/cache/part_d-10_share_especialidad.json + stdout.

Uso:  uv run analysis/part_d/11_share_por_especialidad.py
"""

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-10_share_especialidad.json"

_spec = importlib.util.spec_from_file_location(
    "cruce_pago_receta", Path(__file__).parent / "05_cruce_pago_receta.py"
)
_cruce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cruce)

_spec2 = importlib.util.spec_from_file_location(
    "proporcion_practica", Path(__file__).parent / "09_proporcion_practica.py"
)
_prop = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_prop)

_spec3 = importlib.util.spec_from_file_location(
    "especialidad_concordancia", Path(__file__).parent / "10_especialidad_concordancia.py"
)
_esp = importlib.util.module_from_spec(_spec3)
_spec3.loader.exec_module(_esp)

FOCO = [(2022, "OZEMPIC"), (2024, "OZEMPIC"), (2024, "MOUNJARO")]

# Mínimo por celda. Con menos que esto una mediana es una anécdota, y la celda
# que decide la tesis (endocrinología con honorarios) es justamente la chica.
MIN_CELDA = 20


def _base(con) -> None:
    filtro = " OR ".join(f"(c.anio = {a} AND c.marca = '{m}')" for a, m in FOCO)
    con.sql(
        f"""
        CREATE VIEW base_share AS
        SELECT c.anio, c.marca, c.npi,
               {_esp.CATEGORIA_PARTD.replace('especialidad_partd', 'c.especialidad_partd')}
                                                          AS especialidad,
               c.recetas, p.recetas_totales,
               100.0 * c.recetas / p.recetas_totales      AS share,
               CASE WHEN NOT c.cobro     THEN 'sin pago'
                    WHEN c.usd_voz > 0   THEN 'voz'
                    ELSE                      'solo campo' END AS clase
        FROM cruce c
        JOIN practica p ON p.npi = c.npi AND p.anio = c.anio
        WHERE c.figura_recetando AND p.recetas_totales > 0 AND ({filtro})
        """
    )


def share_por_especialidad_y_clase(con) -> list[dict]:
    return con.sql(
        f"""
        SELECT anio, marca, especialidad, clase,
               count(*)                          AS n,
               round(median(recetas), 1)         AS mediana_recetas_marca,
               round(median(recetas_totales), 1) AS mediana_practica,
               round(median(share), 2)           AS mediana_share_pct
        FROM base_share
        WHERE especialidad IS NOT NULL
        GROUP BY 1, 2, 3, 4
        HAVING count(*) >= {MIN_CELDA}
        ORDER BY 1, 2, 3, 4
        """
    ).df().to_dict("records")


def composicion(con) -> list[dict]:
    """Qué especialidad es cada clase de pago. Si el grupo de honorarios fuera
    mayoritariamente endocrinología y el de sin pago mayoritariamente primaria,
    la brecha bruta de C10 sería en buena parte composición."""
    return con.sql(
        """
        SELECT anio, marca, clase, especialidad,
               count(*) AS n,
               round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY anio, marca, clase), 1)
                        AS pct_de_la_clase
        FROM base_share
        WHERE especialidad IS NOT NULL
        GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 6 DESC
        """
    ).df().to_dict("records")


def veredicto(filas: list[dict]) -> list[dict]:
    """Para cada (año, marca, especialidad) con las tres clases presentes, la
    razón entre el share de los que cobran honorarios y el de los que no cobran.
    Es el número que decide: cerca de 1 mata la tesis, muy por encima la sostiene."""
    por_celda: dict[tuple, dict] = {}
    for f in filas:
        por_celda.setdefault((f["anio"], f["marca"], f["especialidad"]), {})[f["clase"]] = f
    salida = []
    for (anio, marca, esp), clases in sorted(por_celda.items(), key=lambda x: str(x[0])):
        if "voz" not in clases or "sin pago" not in clases:
            continue
        voz, sin = clases["voz"], clases["sin pago"]
        campo = clases.get("solo campo")
        salida.append({
            "anio": anio, "marca": marca, "especialidad": esp,
            "n_voz": voz["n"], "n_sin_pago": sin["n"],
            "share_voz": voz["mediana_share_pct"],
            "share_solo_campo": campo["mediana_share_pct"] if campo else None,
            "share_sin_pago": sin["mediana_share_pct"],
            "razon_voz_sobre_sin_pago": round(
                voz["mediana_share_pct"] / sin["mediana_share_pct"], 2
            ) if sin["mediana_share_pct"] else None,
        })
    return salida


def main() -> int:
    con = _cruce.conectar()
    _cruce.preparar(con, _cruce.anios_disponibles())
    _prop.preparar_practica(con, _cruce.anios_disponibles())
    _base(con)
    filas = share_por_especialidad_y_clase(con)
    salida = {
        "pregunta": (
            "¿El share alto de los que cobran honorarios es del honorario o de la "
            "especialidad? Se compara dentro de cada especialidad. Una razón cercana a 1 "
            "mata la tesis de la puerta."
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "minimo_por_celda": MIN_CELDA,
        "advertencia": (
            "No dice dirección, igual que todo el resto del caso: que el share siga siendo "
            "más alto dentro de la especialidad es compatible con que el honorario mueva la "
            "mezcla y con que se elija disertante a quien ya la tenía."
        ),
        "veredicto": veredicto(filas),
        "share_por_especialidad_y_clase": filas,
        "composicion": composicion(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    for v in salida["veredicto"]:
        print(
            f"{v['anio']} {v['marca']:9} {v['especialidad']:22} "
            f"voz {v['share_voz']:>5}% (n={v['n_voz']:>4})  "
            f"campo {str(v['share_solo_campo']):>5}%  "
            f"sin pago {v['share_sin_pago']:>5}% (n={v['n_sin_pago']:>6})  "
            f"razon {v['razon_voz_sobre_sin_pago']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
