"""Reconciliación contra los agregados oficiales de CMS (skill /reconciliar).

Los valores oficiales se cargan UNA vez, a mano, con URL y fecha de captura al
lado. Cualquier Δ > 1% detiene el análisis (regla de la skill).

Tres bloques, de menos a más específico:
  1. OFICIALES         — total de General Payments por año (dólares y registros).
  2. OFICIALES_DETALLE — disputados y pagos a médicos, mismo dataset de resumen.
  3. API_CMS           — counts que devuelve la API datastore de CMS filtrando
                         por entidad y por naturaleza. NO es un agregado
                         publicado: es la MISMA data servida por otra cadena.
                         Sirve para verificar que ZIP → parquet → vista no
                         corrompió nada, que es un riesgo distinto.

Uso:  uv run scripts/04_checks.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402  (después del bootstrap de path)

# Agregados oficiales de CMS, capturados el 2026-08-25 del dataset que alimenta
# la página Summary Data (openpaymentsdata.cms.gov/summary). La API devuelve el
# valor exacto; la página lo muestra redondeado a dos decimales de mil millones,
# inservible para una tolerancia del 1%.
FUENTE = (
    "https://openpaymentsdata.cms.gov/api/1/datastore/query/"
    "e0d225fc-8230-401d-8fad-e2262fb22b4c/0 (capturada 2026-08-25) · filas "
    "'Total Dollar Amount of all Payment Records - General Payments' y "
    "'Total Number of all Payment Records - General Payments'"
)

# CUIDADO: el dataset trae también 'Total ... of all Payment Records' SIN sufijo,
# que suma General + Research + Ownership (PY2025: 14.670.985.192,09 sobre
# 17,07M registros). Ese NO es el agregado de este caso: acá solo hay General
# Payments. Confundirlos da un Δ de -73% y un rojo espurio.
OFICIALES: dict[int, dict] = {
    2021: {"total_usd": 3_270_711_175.77, "total_n": 11_558_469, "fuente": FUENTE},
    2022: {"total_usd": 3_845_496_173.61, "total_n": 13_322_266, "fuente": FUENTE},
    2023: {"total_usd": 3_328_079_279.62, "total_n": 14_734_121, "fuente": FUENTE},
    2024: {"total_usd": 3_424_344_413.22, "total_n": 15_498_687, "fuente": FUENTE},
    2025: {"total_usd": 3_923_550_962.80, "total_n": 16_131_856, "fuente": FUENTE},
}

# Mismo dataset y fecha de captura que OFICIALES.
# 'Companies Making Payments' (1.833 en PY2025) queda deliberadamente afuera:
# cuenta compañías de General + Research + Ownership, y acá solo hay General
# (1.757 pagadores distintos en 2025). Compararlos daría un rojo espurio de -4%.
OFICIALES_DETALLE: dict[int, dict] = {
    2021: {"disputado_usd": 2_371_030.03, "disputado_n": 309,
           "a_medicos_usd": 2_162_165_159.29, "a_medicos_n": 7_944_340},
    2022: {"disputado_usd": 2_059_013.79, "disputado_n": 443,
           "a_medicos_usd": 2_561_357_850.69, "a_medicos_n": 9_038_980},
    2023: {"disputado_usd": 1_354_162.65, "disputado_n": 251,
           "a_medicos_usd": 2_316_449_307.28, "a_medicos_n": 9_685_211},
    2024: {"disputado_usd": 930_621.88, "disputado_n": 327,
           "a_medicos_usd": 2_503_044_925.94, "a_medicos_n": 9_965_643},
    2025: {"disputado_usd": 1_301_839.46, "disputado_n": 305,
           "a_medicos_usd": 2_624_554_749.77, "a_medicos_n": 10_129_623},
}

# API datastore de CMS para el dataset 2025 de General Payments, consultada el
# 2026-08-25 con ?count=true y un filtro por columna:
# https://openpaymentsdata.cms.gov/api/1/datastore/query/
#   fb0b1734-1410-429d-92f6-3f4b35218e5e/0
API_ANIO = 2025
API_ENTIDADES: dict[int, int] = {
    100000000144: 512_725,  # Novo Nordisk Inc
    100000000066: 425_910,  # Lilly USA, LLC
}
# Falta a propósito la 3ª naturaleza del top 5 ("Compensation for services other
# than consulting, …"): su valor contiene comas, que rompen el parser de
# `conditions` de la API. Las cuatro que quedan cubren el 97,7% de PY2025.
API_NATURALEZAS: dict[str, int] = {
    "Food and Beverage": 14_764_648,
    "Travel and Lodging": 623_496,
    "Consulting Fee": 205_079,
    "Education": 161_500,
}

TOLERANCIA = 0.01


class Tablero:
    """Acumula comparaciones y recuerda si alguna se pasó de TOLERANCIA."""

    def __init__(self) -> None:
        self.rojo = False
        self.n = 0
        print(f"{'métrica':<44}{'propio':>18}{'oficial':>18}{'Δ%':>8}")

    def comparar(self, etiqueta: str, propio: float, oficial: float) -> None:
        delta = (propio - oficial) / oficial if oficial else 0.0
        fuera = abs(delta) > TOLERANCIA
        self.rojo = self.rojo or fuera
        self.n += 1
        print(f"{etiqueta:<44}{propio:>18,.0f}{oficial:>18,.0f}{delta:>7.2%}"
              f"{'  ← ROJO' if fuera else ''}")

    def seccion(self, titulo: str) -> None:
        print(f"\n── {titulo} ──")


def main() -> None:
    if not OFICIALES:
        raise SystemExit("Completar OFICIALES antes de reconciliar (con /browse).")
    con = conectar()
    t = Tablero()

    t.seccion("General Payments por año — total (agregado publicado por CMS)")
    propios = con.sql(
        """
        SELECT Program_Year AS anio,
               sum(Total_Amount_of_Payment_USDollars) AS total_usd,
               count(*) AS total_n
        FROM pagos GROUP BY 1 ORDER BY 1
        """
    ).df()
    for _, f in propios.iterrows():
        of = OFICIALES.get(int(f.anio))
        if of:
            t.comparar(f"PY{int(f.anio)} total_usd", f.total_usd, of["total_usd"])
            t.comparar(f"PY{int(f.anio)} total_n", f.total_n, of["total_n"])

    t.seccion("General Payments por año — disputados y pagos a médicos")
    detalle = con.sql(
        """
        SELECT Program_Year AS anio,
               sum(Total_Amount_of_Payment_USDollars)
                   FILTER (Dispute_Status_for_Publication)      AS disputado_usd,
               count(*) FILTER (Dispute_Status_for_Publication) AS disputado_n,
               sum(Total_Amount_of_Payment_USDollars)
                   FILTER (Covered_Recipient_Type = 'Covered Recipient Physician')
                                                                AS a_medicos_usd,
               count(*)
                   FILTER (Covered_Recipient_Type = 'Covered Recipient Physician')
                                                                AS a_medicos_n
        FROM pagos GROUP BY 1 ORDER BY 1
        """
    ).df()
    for _, f in detalle.iterrows():
        of = OFICIALES_DETALLE.get(int(f.anio))
        if of:
            for k in ("disputado_usd", "disputado_n", "a_medicos_usd", "a_medicos_n"):
                t.comparar(f"PY{int(f.anio)} {k}", getattr(f, k), of[k])

    t.seccion(f"PY{API_ANIO} contra la API datastore de CMS — entidades (D-002)")
    for entidad_id, oficial in API_ENTIDADES.items():
        mio = con.sql(
            f"""SELECT count(*) FROM pagos WHERE Program_Year = {API_ANIO}
                AND Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID
                    = {entidad_id}"""
        ).fetchone()[0]
        t.comparar(f"PY{API_ANIO} entidad {entidad_id}", mio, oficial)

    t.seccion(f"PY{API_ANIO} contra la API datastore de CMS — naturaleza de pago")
    for naturaleza, oficial in API_NATURALEZAS.items():
        mio = con.sql(
            f"""SELECT count(*) FROM pagos WHERE Program_Year = {API_ANIO}
                AND Nature_of_Payment_or_Transfer_of_Value = ?""",
            params=[naturaleza],
        ).fetchone()[0]
        t.comparar(f"PY{API_ANIO} {naturaleza[:36]}", mio, oficial)

    print(f"\n{t.n} comparaciones · Estado:",
          "🔴 DETENER: listar hipótesis (ver skill)" if t.rojo else "🟢 verde")


if __name__ == "__main__":
    main()
