"""Ataque 12 — censura a izquierda (D-014).

La ventana arranca en 2021, pero las relaciones de voz no. Dos preguntas:
  C1. De la cohorte 2021 de cada compañía, ¿cuántos ya cobraban voz de esa
      misma compañía en 2017-2020 (cualquier producto)? Si son mayoría, las
      "duraciones" de la ventana subestiman la relación real.
  C2. Los ENTRANTES de cada año (primer año de voz GLP-1 en la ventana),
      ¿eran nuevos de verdad o disertantes de otras drogas de la casa? El
      crecimiento de Lilly (178 → 493) puede ser reclutamiento o redespliegue.

Los años 2017-2020 se usan SOLO acá (D-014): ningún número de esta corrida
entra a una figura ni a un titular. PY2016 no está disponible (retirado de la
publicación activa de CMS) y la pre-historia queda acotada a cuatro años.

Uso:  uv run analysis/ataque-12_censura.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402


def main() -> None:
    con = conectar()
    anios_previos = con.sql(
        "SELECT count(DISTINCT anio) FROM voz_entidades WHERE anio BETWEEN 2017 AND 2020"
    ).fetchone()[0]
    if anios_previos < 4:
        raise SystemExit(f"Sólo {anios_previos} años previos en disco; correr la descarga D-014.")

    con.sql(
        """
        CREATE TEMP TABLE miembros AS
        SELECT DISTINCT grupo, anio, receptor_id
        FROM glp1 WHERE grupo_naturaleza='voz' AND receptor_id IS NOT NULL
        """
    )

    print("C1 · cohorte 2021 con voz previa de la misma casa (2017-2020, cualquier producto)")
    print(con.sql(
        """
        SELECT m.grupo, count(*) AS cohorte_2021,
               count(*) FILTER (EXISTS (SELECT 1 FROM voz_entidades v
                    WHERE v.grupo=m.grupo AND v.anio BETWEEN 2017 AND 2020
                      AND v.receptor_id=m.receptor_id))          AS con_previa,
               round(100.0*count(*) FILTER (EXISTS (SELECT 1 FROM voz_entidades v
                    WHERE v.grupo=m.grupo AND v.anio BETWEEN 2017 AND 2020
                      AND v.receptor_id=m.receptor_id))/count(*),1) AS pct
        FROM miembros m WHERE m.anio = 2021 GROUP BY 1 ORDER BY 1
        """
    ).fetchall())

    print("\nC2 · entrantes por año: % con voz previa de la misma casa (redespliegue)")
    print(con.sql(
        """
        WITH entrantes AS (
          SELECT grupo, receptor_id, min(anio) AS entrada FROM miembros GROUP BY 1,2)
        SELECT e.entrada, e.grupo, count(*) AS n,
               round(100.0*count(*) FILTER (EXISTS (SELECT 1 FROM voz_entidades v
                    WHERE v.grupo=e.grupo AND v.receptor_id=e.receptor_id
                      AND v.anio < e.entrada))/count(*),1) AS pct_con_previa
        FROM entrantes e GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).fetchall())


if __name__ == "__main__":
    main()
