"""La condición de muerte de la tesis: ¿el share sobrevive a la censura de CMS?

La tesis dice que cobrar honorarios va con un share de GLP-1 de 4 a 7 veces
mayor entre médicos de primaria y enfermería (C13). Ese share se calcula sólo
entre los que **figuran** recetando la marca, y Part D esconde todo par
prescriptor-droga con 10 recetas o menos (P2). La objeción que la mataría: que
la brecha sea un artefacto de quién queda visible.

El mecanismo del sesgo, para saber qué se está probando. Los que cobran recetan
más, así que superan el umbral de once más seguido. El grupo "sin pago" visible
es entonces un recorte por arriba del "sin pago" real: le faltan justamente sus
recetadores chicos. Eso **infla** el share del grupo sin pago y **achica** la
brecha medida. Por ese razonamiento el sesgo conocido corre en contra del
hallazgo. Pero un razonamiento no es una medición, y esto lo mide.

Cómo. Se define un universo cerrado e identificable: **los prescriptores que
recetaron al menos una marca GLP-1 del caso ese año** (los NPI del recorte). Son
médicos que sí recetan GLP-1, así que suponerles recetas ocultas de otra marca
GLP-1 es plausible, no imposible. Dentro de ese universo, para una marca dada,
al que no figura con esa marca se le imputan 0, 5 o 10 recetas de ella:

- **0** es el escenario que el artículo asumiría implícitamente si contara a los
  invisibles como cero.
- **10** es el techo absoluto de lo que el umbral de CMS puede esconder.
- **5** es el punto medio, para ver si la razón se mueve linealmente o salta.

El universo NO se abre a todos los prescriptores de Part D (más de un millón,
la mayoría de especialidades que nunca recetarían un GLP-1): imputarle diez
Ozempic a un oftalmólogo no es un peor caso, es un caso imposible, y un peor
caso imposible no informa nada.

Salida: findings/cache/part_d-11_censura_imputada.json + stdout.

Uso:  uv run analysis/part_d/12_censura_imputada.py
"""

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "findings" / "cache" / "part_d-11_censura_imputada.json"


def _cargar(nombre: str, archivo: str):
    spec = importlib.util.spec_from_file_location(
        nombre, Path(__file__).parent / archivo
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cruce = _cargar("cruce_pago_receta", "05_cruce_pago_receta.py")
_prop = _cargar("proporcion_practica", "09_proporcion_practica.py")
_esp = _cargar("especialidad_concordancia", "10_especialidad_concordancia.py")

FOCO = [(2022, "OZEMPIC"), (2024, "OZEMPIC"), (2024, "MOUNJARO")]
IMPUTACIONES = (0, 5, 10)
MIN_CELDA = 20


def preparar_universo(con) -> None:
    """El universo: quien recetó alguna marca GLP-1 del caso ese año, cruzado
    contra cada marca del foco y contra su clase de pago para esa marca."""
    filtro = " OR ".join(f"(f.anio = {a} AND f.marca = '{m}')" for a, m in FOCO)
    con.sql(
        """
        CREATE VIEW receta_algun_glp1 AS
        SELECT DISTINCT npi, anio FROM cruce WHERE figura_recetando
        """
    )
    con.sql("CREATE VIEW marcas_foco AS "
            + " UNION ALL ".join(f"SELECT {a} AS anio, '{m}' AS marca" for a, m in FOCO))
    # Producto cartesiano universo x marca del foco, y a cada fila se le pega lo
    # que el cruce sepa de ese (npi, año, marca): recetas si figura, pago si
    # cobró. Lo que no figura queda NULL y es lo que después se imputa.
    con.sql(
        f"""
        CREATE VIEW universo AS
        SELECT f.anio, f.marca, u.npi,
               {_esp.CATEGORIA_PARTD.replace('especialidad_partd', 'pd.especialidad')}
                                                    AS especialidad,
               p.recetas_totales,
               c.recetas                            AS recetas_visibles,
               coalesce(c.figura_recetando, false)  AS figura,
               CASE WHEN coalesce(c.cobro, false) IS false THEN 'sin pago'
                    WHEN c.usd_voz > 0                     THEN 'voz'
                    ELSE                                        'solo campo' END AS clase
        FROM receta_algun_glp1 u
        JOIN marcas_foco f       ON f.anio = u.anio
        JOIN practica p          ON p.npi = u.npi AND p.anio = u.anio
        JOIN (SELECT npi, anio, any_value(especialidad_partd) AS especialidad
              FROM cruce WHERE especialidad_partd IS NOT NULL
              GROUP BY 1, 2) pd ON pd.npi = u.npi AND pd.anio = u.anio
        LEFT JOIN cruce c        ON c.npi = u.npi AND c.anio = f.anio
                                AND c.marca = f.marca
        WHERE p.recetas_totales > 0 AND ({filtro})
        """
    )


def tamano_universo(con) -> list[dict]:
    return con.sql(
        """
        SELECT anio, marca, clase,
               count(*)                                          AS npi,
               count(*) FILTER (figura)                           AS figuran,
               count(*) FILTER (NOT figura)                       AS invisibles,
               round(100.0 * count(*) FILTER (NOT figura) / count(*), 1) AS pct_invisible
        FROM universo GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
        """
    ).df().to_dict("records")


def share_imputado(con, k: int) -> list[dict]:
    return con.sql(
        f"""
        SELECT anio, marca, especialidad, clase,
               count(*)                                              AS n,
               round(median(100.0 * coalesce(recetas_visibles, {k})
                            / recetas_totales), 3)                   AS mediana_share_pct,
               round(avg(100.0 * coalesce(recetas_visibles, {k})
                         / recetas_totales), 3)                      AS media_share_pct
        FROM universo
        WHERE especialidad IS NOT NULL
        GROUP BY 1, 2, 3, 4
        HAVING count(*) >= {MIN_CELDA}
        ORDER BY 1, 2, 3, 4
        """
    ).df().to_dict("records")


def razones(por_k: dict[int, list[dict]]) -> list[dict]:
    """La razón voz / sin pago en cada escenario. Es el número que decide: si
    cae cerca de 1 en primaria y NP/PA, la tesis se cae."""
    salida = []
    llaves = {
        (f["anio"], f["marca"], f["especialidad"])
        for f in por_k[IMPUTACIONES[0]]
    }
    for anio, marca, esp in sorted(llaves, key=str):
        fila = {"anio": anio, "marca": marca, "especialidad": esp}
        completa = True
        for k in IMPUTACIONES:
            celdas = {
                f["clase"]: f
                for f in por_k[k]
                if (f["anio"], f["marca"], f["especialidad"]) == (anio, marca, esp)
            }
            if "voz" not in celdas or "sin pago" not in celdas:
                completa = False
                break
            voz, sin = celdas["voz"], celdas["sin pago"]
            fila[f"n_voz_k{k}"] = voz["n"]
            fila[f"n_sin_pago_k{k}"] = sin["n"]
            fila[f"mediana_voz_k{k}"] = voz["mediana_share_pct"]
            fila[f"mediana_sin_pago_k{k}"] = sin["mediana_share_pct"]
            fila[f"razon_mediana_k{k}"] = (
                round(voz["mediana_share_pct"] / sin["mediana_share_pct"], 2)
                if sin["mediana_share_pct"] else None
            )
            fila[f"razon_media_k{k}"] = (
                round(voz["media_share_pct"] / sin["media_share_pct"], 2)
                if sin["media_share_pct"] else None
            )
        if completa:
            salida.append(fila)
    return salida


def main() -> int:
    anios = _cruce.anios_disponibles()
    con = _cruce.conectar()
    _cruce.preparar(con, anios)
    _prop.preparar_practica(con, anios)
    preparar_universo(con)
    por_k = {k: share_imputado(con, k) for k in IMPUTACIONES}
    salida = {
        "pregunta": (
            "¿La brecha de share entre quienes cobran honorarios y quienes no cobran nada "
            "sobrevive a imputarle a los invisibles las recetas que la censura de CMS "
            "puede estar escondiendo?"
        ),
        "capturado": time.strftime("%Y-%m-%d"),
        "universo": (
            "Prescriptores que recetaron al menos una marca GLP-1 del caso ese año y "
            "aparecen en el archivo by Provider. A quien no figura con la marca mirada se "
            "le imputan k recetas de esa marca."
        ),
        "imputaciones": list(IMPUTACIONES),
        "minimo_por_celda": MIN_CELDA,
        "advertencia": (
            "k=10 es el techo del umbral de CMS y supone que TODOS los invisibles recetaron "
            "el máximo oculto, lo cual es imposible en conjunto: es el peor caso, no una "
            "estimación. La lectura correcta es si la razón se sostiene a lo largo de la "
            "escala, no el valor de un solo escenario."
        ),
        "tamano_universo": tamano_universo(con),
        "razones": razones(por_k),
        "share_por_escenario": {str(k): v for k, v in por_k.items()},
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(salida, indent=2, default=str))
    print(f"{'año':>5} {'marca':10} {'especialidad':22} "
          + "  ".join(f"razón k={k}" for k in IMPUTACIONES))
    for r in salida["razones"]:
        print(
            f"{r['anio']:>5} {r['marca']:10} {r['especialidad']:22} "
            + "  ".join(f"{str(r[f'razon_mediana_k{k}']):>9}" for k in IMPUTACIONES)
            + "   | medias: "
            + "  ".join(f"{str(r[f'razon_media_k{k}']):>6}" for k in IMPUTACIONES)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
