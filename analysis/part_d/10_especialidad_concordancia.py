"""¿Hace falta NPPES para reconciliar la especialidad? Se mide, no se supone.

El plan de fuentes dejó NPPES como candidata para reconciliar la especialidad
del prescriptor entre los dos archivos. Puede ser innecesaria: Part D publica
`Prscrbr_Type`, que su propio diccionario de datos deriva de las claims de
Part B y, en su defecto, de la taxonomía NUCC de NPPES, que es la misma fuente
que alimenta la especialidad de Open Payments. Si las dos clasificaciones
coinciden en la enorme mayoría de los NPI, bajar 900 MB de NPPES agrega trabajo
y no información.

Qué compara: para cada NPI que está de los dos lados del cruce, la categoría
del caso (endocrinología, primaria, NP/PA, emergentes, respiratorio y sueño,
resto) derivada de Open Payments contra la misma categoría derivada del
`Prscrbr_Type` de Part D. La función de mapeo de Part D replica, sobre el
vocabulario del otro archivo, el orden de evaluación de D-008/D-009/D-011: la
primera regla que matchea gana, y el tipo de proveedor manda sobre la
subespecialidad.

Salida: findings/cache/part_d-09_especialidad.json + stdout.

Uso:  uv run analysis/part_d/10_especialidad_concordancia.py
"""

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-09_especialidad.json"

_spec = importlib.util.spec_from_file_location(
    "cruce_pago_receta", Path(__file__).parent / "05_cruce_pago_receta.py"
)
_cruce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cruce)

# El vocabulario de Part D es plano ('Endocrinology', 'Nurse Practitioner'),
# no la taxonomía jerárquica de Open Payments, así que el mapeo se escribe
# aparte. El ORDEN es el mismo de D-008/D-009/D-011 y por eso importa.
CATEGORIA_PARTD = """
    CASE
        WHEN especialidad_partd ILIKE '%endocrin%'          THEN 'endocrinologia'
        WHEN especialidad_partd ILIKE '%obesity%'           THEN 'medicina de obesidad'
        WHEN especialidad_partd ILIKE '%cardio%'
          OR especialidad_partd ILIKE '%nephro%'
          OR especialidad_partd ILIKE '%gastroenter%'
          OR especialidad_partd ILIKE '%hepatol%'           THEN 'emergentes'
        WHEN especialidad_partd ILIKE '%nurse practitioner%'
          OR especialidad_partd ILIKE '%physician assistant%'
          OR especialidad_partd ILIKE '%clinical nurse specialist%'
          OR especialidad_partd ILIKE '%nurse anesthetist%' THEN 'NP/PA'
        WHEN especialidad_partd ILIKE '%pulmonary%'
          OR especialidad_partd ILIKE '%sleep%'
          OR especialidad_partd ILIKE '%critical care%'     THEN 'respiratorio y sueño'
        WHEN especialidad_partd ILIKE '%family%'
          OR especialidad_partd ILIKE '%general practice%'
          OR especialidad_partd = 'Internal Medicine'       THEN 'primaria'
        WHEN especialidad_partd IS NULL                     THEN NULL
        ELSE 'resto'
    END
"""


def preparar(con) -> None:
    """Una fila por NPI con las dos categorías, quedándose con la especialidad
    más frecuente de cada lado (un NPI puede tener varias filas marca-año)."""
    con.sql(
        f"""
        CREATE VIEW especialidades AS
        SELECT npi,
               mode(cat_partd) AS cat_partd,
               mode(cat_op)    AS cat_op
        FROM (
            SELECT c.npi,
                   {CATEGORIA_PARTD} AS cat_partd,
                   g.especialidad    AS cat_op
            FROM cruce c
            JOIN (
                SELECT p.Covered_Recipient_NPI AS npi,
                       mode(g.especialidad)    AS especialidad
                FROM glp1 g JOIN pagos p ON p.Record_ID = g.record_id
                WHERE p.Covered_Recipient_NPI IS NOT NULL
                GROUP BY 1
            ) g ON g.npi = c.npi
            WHERE c.figura_recetando AND c.cobro
        )
        WHERE cat_partd IS NOT NULL AND cat_op IS NOT NULL
        GROUP BY 1
        """
    )


def concordancia(con) -> dict:
    total = con.sql(
        """
        SELECT count(*) AS npi,
               count(*) FILTER (cat_partd = cat_op) AS iguales,
               round(100.0 * count(*) FILTER (cat_partd = cat_op) / count(*), 2) AS pct
        FROM especialidades
        """
    ).df().to_dict("records")[0]
    por_categoria = con.sql(
        """
        SELECT cat_op                                        AS categoria_open_payments,
               count(*)                                      AS npi,
               count(*) FILTER (cat_partd = cat_op)          AS coinciden,
               round(100.0 * count(*) FILTER (cat_partd = cat_op) / count(*), 1) AS pct,
               mode(cat_partd) FILTER (cat_partd <> cat_op)  AS discrepancia_mas_comun
        FROM especialidades GROUP BY 1 ORDER BY 2 DESC
        """
    ).df().to_dict("records")
    pares = con.sql(
        """
        SELECT cat_op AS open_payments, cat_partd AS part_d, count(*) AS npi
        FROM especialidades WHERE cat_partd <> cat_op
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 15
        """
    ).df().to_dict("records")
    return {"total": total, "por_categoria": por_categoria, "discrepancias": pares}


def main() -> int:
    con = _cruce.conectar()
    _cruce.preparar(con, _cruce.anios_disponibles())
    preparar(con)
    res = concordancia(con)
    salida = {
        "pregunta": (
            "¿Hace falta bajar NPPES para reconciliar la especialidad entre Part D y "
            "Open Payments, o el Prscrbr_Type de Part D alcanza?"
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "nota": (
            "Compara la categoría del caso derivada de cada archivo, sobre los NPI que "
            "están de los dos lados. NO mide cuál de las dos tiene razón: mide si "
            "discrepan lo bastante como para que valga la pena una tercera fuente."
        ),
        **res,
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps(salida, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
