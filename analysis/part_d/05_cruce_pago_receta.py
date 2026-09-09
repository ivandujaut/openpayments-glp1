"""El cruce: por NPI y por año, cuánto cobró y cuánto recetó cada profesional.

La llave es el NPI, que existe de los dos lados con 99,9% de cobertura
(medido en `02_npi_cobertura.py`). No hay matching por nombre ni por dirección.

Unidad de análisis: **(NPI, año, marca)**. La marca importa porque la pregunta
del caso es sobre el producto: cobrar de Novo por Ozempic y recetar Trulicity no
es la misma historia que cobrar por Ozempic y recetar Ozempic.

Cuatro cuadrantes, y el nombre de cada uno dice lo que el dato permite decir:

- **cobró y recetó**: los dos datasets lo tienen.
- **cobró y no figura recetando**: NO es "cobró y no recetó". Part D excluye
  todo par prescriptor-droga con 10 recetas o menos (metodología de CMS,
  sección 4.1). Once recetas es el piso de lo visible.
- **receta y no cobró**: recetó y no hay ningún pago suyo por esa marca ese año.
- (el cuarto cuadrante, ni cobra ni receta, no es observable y no se cuenta.)

Sobre los años: corre con los Parquet de Part D que existan en data/parquet/.
Si faltan años, lo dice en la salida en vez de simular la ventana completa.

Salida: findings/cache/part_d-04_cruce.json + stdout.

Uso:  uv run analysis/part_d/05_cruce_pago_receta.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.vistas import conectar  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PQ = ROOT / "data" / "parquet"
CACHE = ROOT / "findings" / "cache" / "part_d-04_cruce.json"


def anios_disponibles() -> list[int]:
    return sorted(int(p.stem.split("_")[-1]) for p in PQ.glob("part_d_glp1_*.parquet"))


def preparar(con, anios: list[int]) -> None:
    lista = ", ".join(str(a) for a in anios)

    # Lado receta: una fila por (NPI, año, marca del caso). Victoza llega
    # partida en dos presentaciones y se suma acá.
    con.sql(
        f"""
        CREATE VIEW recetas AS
        SELECT Prscrbr_NPI            AS npi,
               anio,
               marca_caso             AS marca,
               grupo,
               any_value(Prscrbr_Type)          AS especialidad_partd,
               any_value(Prscrbr_State_Abrvtn)  AS estado,
               sum(Tot_Clms)                    AS recetas,
               sum(Tot_Drug_Cst)                AS costo_usd
        FROM read_parquet('{PQ}/part_d_glp1_*.parquet', union_by_name=true)
        WHERE Prscrbr_NPI IS NOT NULL
        GROUP BY 1, 2, 3, 4
        """
    )

    # Lado pago: una fila por (NPI, año, marca). El monto es el prorrateado
    # (D-004): una comida que declara Ozempic y Jardiance aporta la mitad.
    con.sql(
        f"""
        CREATE VIEW pagos_npi AS
        SELECT p.Covered_Recipient_NPI          AS npi,
               g.anio,
               g.producto                       AS marca,
               g.grupo,
               any_value(g.especialidad)        AS especialidad_op,
               sum(g.usd)                                       AS usd,
               sum(CASE WHEN g.grupo_naturaleza = 'voz'
                        THEN g.usd ELSE 0 END)                  AS usd_voz,
               count(DISTINCT g.record_id)                      AS pagos
        FROM glp1 g
        JOIN pagos p ON p.Record_ID = g.record_id
        WHERE p.Covered_Recipient_NPI IS NOT NULL
          AND g.anio IN ({lista})
        GROUP BY 1, 2, 3, 4
        """
    )

    con.sql(
        """
        CREATE VIEW cruce AS
        SELECT coalesce(r.npi, g.npi)       AS npi,
               coalesce(r.anio, g.anio)     AS anio,
               coalesce(r.marca, g.marca)   AS marca,
               coalesce(r.grupo, g.grupo)   AS grupo,
               r.especialidad_partd, r.estado,
               coalesce(r.recetas, 0)       AS recetas,
               coalesce(r.costo_usd, 0)     AS costo_usd,
               coalesce(g.usd, 0)           AS usd,
               coalesce(g.usd_voz, 0)       AS usd_voz,
               coalesce(g.pagos, 0)         AS pagos,
               r.npi IS NOT NULL            AS figura_recetando,
               g.npi IS NOT NULL            AS cobro
        FROM recetas r
        FULL OUTER JOIN pagos_npi g
          ON r.npi = g.npi AND r.anio = g.anio AND r.marca = g.marca
        """
    )


def cuadrantes(con) -> list[dict]:
    return con.sql(
        """
        SELECT anio, marca,
               count(*) FILTER (cobro AND figura_recetando)        AS cobro_y_receta,
               count(*) FILTER (cobro AND NOT figura_recetando)    AS cobro_sin_figurar,
               count(*) FILTER (NOT cobro AND figura_recetando)    AS receta_sin_cobrar,
               round(sum(usd) FILTER (cobro AND figura_recetando), 2)     AS usd_cobro_y_receta,
               round(sum(usd) FILTER (cobro AND NOT figura_recetando), 2) AS usd_cobro_sin_figurar,
               sum(recetas) FILTER (cobro AND figura_recetando)    AS recetas_de_los_que_cobran,
               sum(recetas) FILTER (NOT cobro AND figura_recetando) AS recetas_de_los_que_no
        FROM cruce GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df().to_dict("records")


def comparacion_medianas(con) -> list[dict]:
    """La medida de ProPublica: entre los que SÍ figuran recetando una marca,
    ¿recetan más los que cobraron por ella? Mediana y media, y el n de cada
    lado, porque una media sobre colas largas engaña sola."""
    return con.sql(
        """
        SELECT anio, marca,
               count(*) FILTER (cobro)                                   AS n_con_pago,
               count(*) FILTER (NOT cobro)                               AS n_sin_pago,
               round(median(recetas) FILTER (cobro), 1)                  AS mediana_con_pago,
               round(median(recetas) FILTER (NOT cobro), 1)              AS mediana_sin_pago,
               round(avg(recetas) FILTER (cobro), 1)                     AS media_con_pago,
               round(avg(recetas) FILTER (NOT cobro), 1)                 AS media_sin_pago
        FROM cruce WHERE figura_recetando
        GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).df().to_dict("records")


def concentracion(con) -> list[dict]:
    """La distribución, no el promedio: ¿los que más cobran son los que más
    recetan? Deciles de dinero contra recetas, entre los que cobraron algo."""
    return con.sql(
        """
        WITH base AS (
            SELECT anio, marca, npi, usd, recetas, figura_recetando,
                   ntile(10) OVER (PARTITION BY anio, marca ORDER BY usd) AS decil_usd
            FROM cruce WHERE cobro
        )
        SELECT anio, marca, decil_usd,
               count(*)                                     AS npi,
               round(sum(usd), 2)                           AS usd,
               round(median(usd), 2)                        AS mediana_usd,
               sum(recetas)                                 AS recetas,
               round(median(recetas), 1)                    AS mediana_recetas,
               round(100.0 * count(*) FILTER (figura_recetando) / count(*), 1)
                                                            AS pct_figura_recetando
        FROM base GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def main() -> int:
    anios = anios_disponibles()
    if not anios:
        raise SystemExit(
            "No hay Parquet de Part D en data/parquet/. "
            "Correr antes: uv run analysis/part_d/03_extraer_glp1.py"
        )
    con = conectar()
    preparar(con, anios)
    salida = {
        "anios_procesados": anios,
        "ventana_objetivo": [2021, 2022, 2023, 2024],
        "faltan": [a for a in (2021, 2022, 2023, 2024) if a not in anios],
        "advertencia_censura": (
            "'cobro_sin_figurar' incluye a quien recetó entre 1 y 10 veces: Part D "
            "excluye todo par prescriptor-droga con menos de 11 recetas."
        ),
        "cuadrantes": cuadrantes(con),
        "medianas": comparacion_medianas(con),
        "concentracion": concentracion(con),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(json.dumps({k: v for k, v in salida.items() if k != "concentracion"},
                     indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
