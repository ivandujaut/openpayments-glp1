"""Verifica que TODA cifra publicada en un writeup salga del dato del caso.

Los otros dos verificadores cubren los eslabones de adentro:

  04_checks.py            el dato propio contra los agregados oficiales de CMS
  05_verificar_findings   el texto de findings/ contra findings/cache/

Falta el último: el texto que se publica afuera (el MDX del sitio, o el espejo
de export/). Ese texto se escribe a mano, cita más de cien cifras y hoy no lo
mira ningún script. El precedente existe: la tabla voz/campo del corte 01 quedó
cinco años con valores viejos después de que D-006 los moviera, y eso lo
encontró un script, no una relectura.

La diferencia con 05 es la dirección del chequeo. 05 pregunta "¿esta cifra que
declaré sigue coincidiendo con el cache?". Acá se pregunta al revés:

    ¿hay en el texto alguna cifra que NO tenga fuente?

Por eso el script extrae TODOS los números del texto publicado y exige que cada
uno caiga en una de tres categorías:

  1. lo respalda una aserción contra findings/cache/*.json;
  2. lo respalda una aserción recalculada acá mismo contra los Parquet (las
     cifras que hoy sólo producen los scripts de ataque, que no cachean);
  3. está en la lista de exentos, con motivo escrito (años, tamaños de figura,
     códigos de decisión, conteos de proceso).

Cualquier número que no entre en ninguna sale como SIN FUENTE. No hay cuarta
categoría, y ese es el punto: una cifra nueva pegada en el texto rompe el check
sola.

El recálculo de la categoría 2 es deliberadamente una segunda implementación,
independiente de la del ataque que la produjo. Si las dos coinciden, la cifra
está bien; si no, una de las dos tiene un error y hay que mirar.

Uso:  uv run scripts/06_verificar_writeup.py [ruta.mdx ...]

Sin argumentos verifica lo que haya en export/site/content/**/index.mdx. Se le
puede pasar cualquier ruta, incluida la del repo del sitio: este script LEE, no
escribe, así que no rompe la frontera con ivandujaut.com.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vistas import conectar  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "findings" / "cache"

# Precisión con que el texto cita cada tipo de cifra: media unidad del último
# dígito publicado. Misma convención que 05.
P_ENTERO = 0.5
P_1DEC = 0.05
P_2DEC = 0.005
P_MILLON_2DEC = 5_000
P_MILLON_3DEC = 500

# Números que no son dato del caso. Cada uno con su motivo: la lista es parte
# de la evidencia, no una tapadera para lo que no cierra.
EXENTOS = {
    2016: "año de pre-historia retirado por CMS (D-014)",
    2017: "año de pre-historia (D-014)",
    2018: "año de pre-historia (D-014)",
    2019: "año de pre-historia (D-014)",
    2020: "año de pre-historia (D-014)",
    2015: "mención del límite de la pre-historia",
    30: "criterio de descarte publicado (30%)",
    8: "cantidad de ataques del corte 05",
    5000: "corte de banda (D-016)",
    25000: "corte de banda (D-016)",
    5: "corte de banda en miles (D-016)",
    75: "corte de banda en miles (D-016)",
    2021: "año de la ventana",
    2022: "año de la ventana",
    2023: "año de la ventana",
    2024: "año de la ventana",
    2025: "año de la ventana",
    2026: "año de publicación / próximo Program Year",
    1495: "ancho en píxeles de las figuras",
    886: "alto en píxeles de las figuras",
    1: "código de decisión (D-001), GLP-1, ordinal o denominador de una razón",
    2: "código de decisión, ordinal",
    3: "código de decisión, ordinal",
    4: "código de decisión, ordinal",
    5: "código de decisión, ordinal",
    6: "código de decisión, ordinal",
    7: "código de decisión, ordinal",
    8: "código de decisión, ordinal",
    9: "código de decisión, ordinal",
    10: "código de decisión (D-010), corte top 10",
    11: "código de decisión (D-011), cantidad de decisiones registradas",
    12: "meses del piloto propuesto (juicio, declarado como tal)",
    30: "umbral de descarte del experimento 2 (juicio, declarado como tal)",
    36: "cantidad de comparaciones de 04_checks.py, registrada en findings/checks.md",
    70: "cantidad de ataques corridos, contada en los encabezados de los cuatro findings",
    100: "top 100, el corte de la métrica de concentración (D-007)",
    500: "corte top 500",
    1000: "corte top 1.000",
    50: "corte top 50",
    25: "fecha de descarga (25/08/2026)",
    "0,00": "resultado de la reconciliación, registrado en findings/checks.md",
}


def cargar(nombre: str) -> dict:
    ruta = CACHE / f"{nombre}.json"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Correr los cortes de analysis/ primero.")
    return json.loads(ruta.read_text())


def buscar(filas, **claves):
    for f in filas:
        if all(f.get(k) == v for k, v in claves.items()):
            return f
    raise KeyError(f"sin fila para {claves}")


def texto_publicado(ruta: Path) -> str:
    """El texto que un lector ve, incluidos alt y caption; sin metadatos técnicos.

    Se sacan las rutas de imagen y los width/height porque son configuración, no
    cifras del análisis; el alt y el caption SÍ entran, porque se publican y ya
    citaron números que después cambiaron.
    """
    crudo = ruta.read_text()
    partes = crudo.split("---", 2)
    fm, cuerpo = (partes[1], partes[2]) if len(partes) == 3 else ("", crudo)

    # Del frontmatter sólo lo que se lee: tagline, description y las métricas.
    lineas = [
        l
        for l in fm.splitlines()
        if re.match(r"\s*(tagline|description|label|value|alt):", l)
    ]
    # Los comentarios MDX no se publican: son notas para quien edita el archivo.
    cuerpo = re.sub(r"\{/\*.*?\*/\}", " ", cuerpo, flags=re.S)
    cuerpo = re.sub(r"\b(width|height)=\{[^}]*\}", " ", cuerpo)
    cuerpo = re.sub(r'src="[^"]*"', " ", cuerpo)
    cuerpo = re.sub(r"\]\(https?://[^)]+\)", "]", cuerpo)  # URLs, no prosa
    return "\n".join(lineas) + "\n" + cuerpo


def numeros(texto: str, locale: str = "es"):
    """(literal, valor, contexto) de cada número, según el formato del locale.

    El caso es bilingüe y los dos idiomas escriben distinto el mismo número:
    5.367 en castellano, 5,367 en inglés. Parsear el inglés con las reglas
    castellanas convierte cinco mil trescientos sesenta y siete en cinco coma
    tres, y el error pasa desapercibido porque el número "existe" igual.
    """
    if locale == "en":
        patron = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
        limpiar = lambda x: x.replace(",", "")  # noqa: E731
    else:
        patron = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
        limpiar = lambda x: x.replace(".", "").replace(",", ".")  # noqa: E731
    for m in re.finditer(patron, texto):
        lit = m.group(0)
        val = float(limpiar(lit))
        ini, fin = max(0, m.start() - 45), m.end() + 25
        ctx = " ".join(texto[ini:fin].split())
        yield lit, val, ctx


def redondeos(etiqueta: str, valor: float, precision: float) -> list[tuple[str, float, float]]:
    """La misma cifra citada con dos precisiones.

    El cuerpo cita "34,98 millones" y el alt de la figura dice "35 millones". Las
    dos son la misma cifra y las dos se publican, así que las dos se declaran.
    """
    return [(etiqueta, valor, precision), (f"{etiqueta} (redondeada)", valor, P_ENTERO)]


def aserciones_cache() -> list[tuple[str, float, float]]:
    """(etiqueta, valor, precisión) para lo que sale de findings/cache."""
    a = []
    c1, c2, c3, c4 = (
        cargar("corte-01_carrera"),
        cargar("corte-02_concentracion"),
        cargar("corte-03_especialidades"),
        cargar("corte-04_convergencia"),
    )

    t = c1["totales"]
    s25 = buscar(c1["serie"], anio=2025)
    v21, v25 = buscar(c1["voz_vs_campo"], anio=2021), buscar(c1["voz_vs_campo"], anio=2025)
    a += [
        *redondeos("corte 01 · Novo total, en millones", t["novo_usd"] / 1e6, P_2DEC),
        *redondeos("corte 01 · Lilly total, en millones", t["lilly_usd"] / 1e6, P_2DEC),
        ("corte 01 · Novo total, con un decimal", t["novo_usd"] / 1e6, P_1DEC),
        ("corte 01 · Lilly total, con un decimal", t["lilly_usd"] / 1e6, P_1DEC),
        ("corte 01 · Novo + Lilly, en millones", (t["novo_usd"] + t["lilly_usd"]) / 1e6, P_1DEC),
        ("corte 01 · profesionales de Novo en 2025", s25["novo_hcp"], P_ENTERO),
        ("corte 01 · profesionales de Lilly en 2025", s25["lilly_hcp"], P_ENTERO),
        ("corte 01 · pagos de voz de Lilly en 2021", v21["lilly_voz_n"], P_ENTERO),
        ("corte 01 · pagos de voz de Lilly en 2025", v25["lilly_voz_n"], P_ENTERO),
        ("corte 01 · pagos de voz de Novo en 2021", v21["novo_voz_n"], P_ENTERO),
        ("corte 01 · pagos de voz de Novo en 2025", v25["novo_voz_n"], P_ENTERO),
        ("corte 01 · Novo + Lilly, en millones enteros", (t["novo_usd"] + t["lilly_usd"]) / 1e6, P_ENTERO),
    ]
    # Los cuatro valores de cada año: el alt de g2 los cita y ya se desactualizaron
    # una vez enteros, cuando D-006 movió consultoría de campo a voz.
    for f in c1["voz_vs_campo"]:
        for col, quien in (("novo_voz", "Novo, voz"), ("lilly_voz", "Lilly, voz"),
                           ("novo_campo", "Novo, campo"), ("lilly_campo", "Lilly, campo")):
            a.append((f"corte 01 · {quien} en {f['anio']}, en millones", f[col] / 1e6, P_1DEC))

    lil = buscar(c2["concentracion"], grupo="lilly")
    nov = buscar(c2["concentracion"], grupo="novo")
    plil = buscar(c2["perfil_top100"], grupo="lilly")
    pnov = buscar(c2["perfil_top100"], grupo="novo")
    vlil = buscar(c2["por_naturaleza"], grupo="lilly", grupo_naturaleza="voz")
    vnov = buscar(c2["por_naturaleza"], grupo="novo", grupo_naturaleza="voz")
    a += [
        ("corte 02 · % al top 100 de Lilly", lil["top100"], P_1DEC),
        ("corte 02 · % al top 100 de Novo", nov["top100"], P_1DEC),
        ("corte 02 · razón de concentración", lil["top100"] / nov["top100"], P_2DEC),
        ("corte 02 · Gini de Lilly", lil["gini"], P_2DEC),
        ("corte 02 · Gini de Novo", nov["gini"], P_2DEC),
        ("corte 02 · umbral de entrada al top 100, Lilly", plil["usd_minimo"], P_ENTERO),
        ("corte 02 · umbral de entrada al top 100, Novo", pnov["usd_minimo"], P_ENTERO),
        ("corte 02 · pagos promedio del top 100, Lilly", plil["pagos_promedio"], P_ENTERO),
        ("corte 02 · pagos promedio del top 100, Novo", pnov["pagos_promedio"], P_ENTERO),
        ("corte 02 · profesionales de voz, Lilly", vlil["red_hcps"], P_ENTERO),
        ("corte 02 · profesionales de voz, Novo", vnov["red_hcps"], P_ENTERO),
        ("corte 02 · gasto de voz, Lilly, en millones", vlil["usd"] / 1e6, P_2DEC),
        ("corte 02 · gasto de voz, Novo, en millones", vnov["usd"] / 1e6, P_2DEC),
        ("corte 02 · diferencia entre umbrales", abs(plil["usd_minimo"] - pnov["usd_minimo"]), P_ENTERO),
        # "sobre 172 mil": el texto trunca a miles, así que la tolerancia es de mil.
        ("corte 02 · umbral de entrada, en miles", plil["usd_minimo"] / 1e3, 1.0),
    ]
    for corte in ("top10", "top50", "top500", "top1000"):
        a += [
            (f"corte 02 · % al {corte} de Lilly", lil[corte], P_1DEC),
            (f"corte 02 · % al {corte} de Novo", nov[corte], P_1DEC),
        ]

    endo = buscar(c3["reparto"], especialidad="endocrinologia")
    nppa = buscar(c3["reparto"], especialidad="NP/PA")
    a += [
        ("corte 03 · endocrinólogos alcanzados", endo["hcps"], P_ENTERO),
        ("corte 03 · enfermeros y asistentes alcanzados", nppa["hcps"], P_ENTERO),
        ("corte 03 · USD por endocrinólogo", endo["usd_por_hcp"], P_ENTERO),
        ("corte 03 · USD por enfermero o asistente", nppa["usd_por_hcp"], P_ENTERO),
        ("corte 03 · razón por cabeza", endo["usd_por_hcp"] / nppa["usd_por_hcp"], P_ENTERO),
        ("corte 03 · gasto en endocrinología, en millones", (endo["novo_usd"] + endo["lilly_usd"]) / 1e6, P_2DEC),
        ("corte 03 · gasto en NP/PA, en millones", (nppa["novo_usd"] + nppa["lilly_usd"]) / 1e6, P_2DEC),
        ("corte 03 · % de endocrinología en Lilly", endo["lilly_pct"], P_1DEC),
        ("corte 03 · % de endocrinología en Novo", endo["novo_pct"], P_1DEC),
        ("corte 03 · % de NP/PA en Novo", nppa["novo_pct"], P_1DEC),
        ("corte 03 · % de NP/PA en Lilly", nppa["lilly_pct"], P_1DEC),
        ("corte 03 · razón entre poblaciones NP/PA y endocrinología", nppa["hcps"] / endo["hcps"], P_1DEC),
    ]
    hcps_total = sum(f["hcps"] for f in c3["reparto"])
    usd_total = sum(f["novo_usd"] + f["lilly_usd"] for f in c3["reparto"])
    a += [
        ("corte 03 · % de los profesionales que son endocrinólogos", 100 * endo["hcps"] / hcps_total, P_1DEC),
        ("corte 03 · % del dinero que va a endocrinología", 100 * (endo["novo_usd"] + endo["lilly_usd"]) / usd_total, P_ENTERO),
    ]
    for f in c3["reparto"]:
        for col, quien in (("novo_usd", "Novo"), ("lilly_usd", "Lilly")):
            a += redondeos(f"corte 03 · {f['especialidad']}, {quien}, en millones", f[col] / 1e6, P_2DEC)
    for f in c3["serie"]:
        if f["especialidad"] == "endocrinologia":
            a += [
                (f"corte 03 · % de endocrinología en Lilly, {f['anio']}", f["lilly_pct"], P_1DEC),
                (f"corte 03 · % de endocrinología en Novo, {f['anio']}", f["novo_pct"], P_1DEC),
            ]
    for anio in (2023, 2025):
        e = buscar(c3["serie"], anio=anio, especialidad="endocrinologia")
        a += [
            (f"corte 03 · % de endocrinología en Lilly, {anio}", e["lilly_pct"], P_1DEC),
            (f"corte 03 · % de endocrinología en Novo, {anio}", e["novo_pct"], P_1DEC),
            (f"corte 03 · brecha de endocrinología, {anio}", e["lilly_pct"] - e["novo_pct"], P_1DEC),
        ]

    mov = c4["movimiento"]
    mel, men = buscar(mov, grupo="lilly", especialidad="emergentes"), buscar(mov, grupo="novo", especialidad="emergentes")
    mrl, mrn = buscar(mov, grupo="lilly", especialidad="respiratorio y sueño"), buscar(mov, grupo="novo", especialidad="respiratorio y sueño")
    endl = buscar(mov, grupo="lilly", especialidad="endocrinologia")
    a += [
        ("corte 04 · emergentes de Novo en 2023, en millones", men["usd_pivote"] / 1e6, P_2DEC),
        ("corte 04 · emergentes de Novo en 2025, en millones", men["usd_final"] / 1e6, P_2DEC),
        ("corte 04 · crecimiento de Novo en emergentes, en millones", men["delta"] / 1e6, P_2DEC),
        ("corte 04 · caída de Lilly en endocrinología, en millones", abs(endl["delta"]) / 1e6, P_2DEC),
        ("corte 04 · bloque respiratorio de Lilly en 2025, en millones", mrl["usd_final"] / 1e6, P_2DEC),
        ("corte 04 · bloque respiratorio de Lilly en 2023, en miles", mrl["usd_pivote"] / 1e3, P_ENTERO),
        ("corte 04 · razón en emergentes, Novo sobre Lilly", men["usd_final"] / mel["usd_final"], P_ENTERO),
        ("corte 04 · razón en respiratorio, Lilly sobre Novo", mrl["usd_final"] / mrn["usd_final"], P_ENTERO),
    ]
    for f in mov:
        a.append((f"corte 04 · cambio 2023-2025 de {f['grupo']} en {f['especialidad']}, en millones",
                  f["delta"] / 1e6, P_2DEC))

    # ---------- corte 05 (caso influencers-ozempic) ----------
    c5 = cargar("corte-05_rotacion")
    for f in c5["retencion"]:
        g, anio = f["grupo"], int(f["anio"])
        a += [
            (f"corte 05 · miembros {g} {anio}", f["miembros"], P_ENTERO),
            (f"corte 05 · rotación {g} {anio}→{anio+1} (%)", f["rotacion_pct"], P_1DEC),
            (f"corte 05 · fichados {g} {anio}", f["fichados"], P_ENTERO),
            (f"corte 05 · salidas {g} {anio}", f["miembros"] - f["retenidos"], P_ENTERO),
        ]
    for f in c5["tres_anios"]:
        a.append((f"corte 05 · activos 3 años después, {f['grupo']} {int(f['anio'])} (%)",
                  f["pct"], P_1DEC))
    for f in c5["acumulada"]:
        a += [
            (f"corte 05 · círculo {f['grupo']}", f["circulo"], P_ENTERO),
            (f"corte 05 · los cinco años {f['grupo']}", f["los_cinco"], P_ENTERO),
        ]
    a.append(("corte 05 · círculo total de los dos",
              sum(f["circulo"] for f in c5["acumulada"]), P_ENTERO))
    for g in ("lilly", "novo"):
        a.append((f"corte 05 · salidas totales {g} en la ventana",
                  sum(f["miembros"] - f["retenidos"] for f in c5["retencion"] if f["grupo"] == g),
                  P_ENTERO))
    for f in c5["retencion_por_banda"]:
        a.append((f"corte 05 · retención banda {f['banda']} {f['grupo']} (%)",
                  f["retencion_pct"], P_1DEC))
    # Retención agrupando las dos bandas altas (25 mil o más), ponderada.
    for g in ("lilly", "novo"):
        altas = [f for f in c5["retencion_por_banda"]
                 if f["grupo"] == g and f["banda"] in ("c 25-75k", "d 75k+")]
        pool = sum(f["retencion_pct"] * f["prof_anios"] for f in altas) / sum(
            f["prof_anios"] for f in altas)
        a.append((f"corte 05 · retención de 25 mil o más, {g} (%, redondeada)", pool, P_ENTERO))
    # Retención agregada (ponderada) y su complemento, derivadas de la tabla.
    for g in ("lilly", "novo"):
        filas = [f for f in c5["retencion"] if f["grupo"] == g]
        ret = 100.0 * sum(f["retenidos"] for f in filas) / sum(f["miembros"] for f in filas)
        a.append((f"corte 05 · retención agregada {g} (%)", ret, P_1DEC))
    # El presupuesto de voz que explica el éxodo de Novo (de cohortes, en %).
    usd = {(f["grupo"], int(f["anio"])): f["usd"] for f in c5["cohortes"]}
    a += [
        ("corte 05 · recorte de voz de Novo 2022→23 (%, valor absoluto)",
         abs(100.0 * (usd[("novo", 2023)] - usd[("novo", 2022)]) / usd[("novo", 2022)]), P_ENTERO),
        ("corte 05 · reconstrucción de voz de Novo 2024→25 (%)",
         100.0 * (usd[("novo", 2025)] - usd[("novo", 2024)]) / usd[("novo", 2024)], P_ENTERO),
    ]
    return a


def aserciones_recalculadas(con) -> list[tuple[str, float, float]]:
    """Lo que hoy sólo producen los scripts de ataque, recalculado acá aparte."""
    a = []

    q = lambda sql: con.sql(sql).fetchone()  # noqa: E731

    # Filas del universo por año: el caso cita el rango, no un promedio.
    lo, hi = q("SELECT min(n), max(n) FROM (SELECT count(*) n FROM pagos GROUP BY Program_Year)")
    a += [
        ("universo · año más chico, en millones de filas", lo / 1e6, P_1DEC),
        ("universo · año más grande, en millones de filas", hi / 1e6, P_1DEC),
    ]

    # Ataque C2 del corte 01: sin el grupo "voz", ¿por cuánto gana Novo cada año?
    ratios = con.sql(
        """
        SELECT sum(usd) FILTER (grupo = 'novo') / sum(usd) FILTER (grupo = 'lilly') AS r
        FROM glp1 WHERE grupo_naturaleza = 'campo' GROUP BY anio
        """
    ).df()["r"]
    a += [
        ("ataque C2 · ventaja mínima de Novo sin el grupo voz", ratios.min(), P_1DEC),
        ("ataque C2 · ventaja máxima de Novo sin el grupo voz", ratios.max(), P_1DEC),
    ]

    # Corte 05, ataques 12 y 13 (segunda implementación, aparte de los scripts).
    hay_previa = q("SELECT count(DISTINCT anio) FROM voz_entidades WHERE anio BETWEEN 2017 AND 2020")[0]
    if hay_previa == 4:
        con.sql(
            """
            CREATE OR REPLACE TEMP VIEW miembros05 AS
            SELECT DISTINCT grupo, anio, receptor_id FROM glp1
            WHERE grupo_naturaleza = 'voz' AND receptor_id IS NOT NULL
            """
        )
        for g in ("lilly", "novo"):
            pct = q(f"""
                SELECT 100.0*count(*) FILTER (EXISTS (SELECT 1 FROM voz_entidades v
                     WHERE v.grupo=m.grupo AND v.anio BETWEEN 2017 AND 2020
                       AND v.receptor_id=m.receptor_id))/count(*)
                FROM miembros05 m WHERE m.anio=2021 AND m.grupo='{g}'""")[0]
            a.append((f"ataque 12 · cohorte 2021 de {g} con voz previa (%)", pct, P_1DEC))
        pct = q("""
            WITH e AS (SELECT grupo, receptor_id, min(anio) AS entrada
                       FROM miembros05 GROUP BY 1,2)
            SELECT 100.0*count(*) FILTER (EXISTS (SELECT 1 FROM voz_entidades v
                 WHERE v.grupo=e.grupo AND v.receptor_id=e.receptor_id AND v.anio < e.entrada))
                 /count(*)
            FROM e WHERE e.grupo='lilly' AND e.entrada=2025""")[0]
        a.append(("ataque 12 · entrantes 2025 de Lilly con voz previa (%)", pct, P_1DEC))
        a.append(("ataque 12 · entrantes 2025 de Lilly sin voz previa (%)", 100 - pct, P_1DEC))
    novo_5k = q("""
        WITH m AS (SELECT grupo, anio, receptor_id FROM glp1
                   WHERE grupo_naturaleza='voz' AND receptor_id IS NOT NULL
                   GROUP BY 1,2,3 HAVING sum(usd) >= 5000),
             pares AS (SELECT m.anio, count(*) n,
                       count(*) FILTER (EXISTS (SELECT 1 FROM m r WHERE r.grupo=m.grupo
                            AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id)) ret
                       FROM m WHERE m.grupo='novo' AND m.anio < 2025 GROUP BY 1)
        SELECT max(100.0*(n-ret)/n) FROM pares""")[0]
    a.append(("ataque 13 · rotación máxima de Novo con umbral de 5.000 (%)", novo_5k, P_1DEC))
    fich = q("""
        WITH m AS (SELECT DISTINCT grupo, anio, receptor_id FROM glp1
                   WHERE grupo_naturaleza='voz' AND receptor_id IS NOT NULL)
        SELECT count(*) FROM m
        WHERE m.grupo='lilly' AND m.anio < 2025
          AND NOT EXISTS (SELECT 1 FROM m r WHERE r.grupo='lilly'
               AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id)
          AND EXISTS (SELECT 1 FROM m r WHERE r.grupo='novo'
               AND r.anio=m.anio+1 AND r.receptor_id=m.receptor_id)""")[0]
    a.append(("ataque 13 · salidas de Lilly con voz del rival, peor caso", fich, P_ENTERO))

    # Ataque 11: el frente de Lilly. Origen de los profesionales y peso de Zepbound.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW origen AS
        WITH b25 AS (
            SELECT DISTINCT receptor_id FROM glp1
            WHERE especialidad = 'respiratorio y sueño' AND anio = 2025 AND receptor_id IS NOT NULL
        ), h AS (
            SELECT b.receptor_id,
                   count(*) FILTER (g.anio < 2025) AS previos,
                   count(*) FILTER (g.anio < 2025 AND g.especialidad = 'respiratorio y sueño') AS previos_bloque,
                   count(*) FILTER (g.anio < 2025 AND g.especialidad <> 'respiratorio y sueño') AS previos_otra
            FROM b25 b LEFT JOIN glp1 g USING (receptor_id) GROUP BY 1
        )
        SELECT receptor_id,
               CASE WHEN previos = 0 THEN 'nuevo'
                    WHEN previos_otra = 0 THEN 'misma etiqueta'
                    WHEN previos_bloque = 0 THEN 'reetiquetado'
                    ELSE 'mixta' END AS origen
        FROM h
        """
    )
    nuevos, reeti = q(
        """
        SELECT 100.0 * sum(g.usd) FILTER (o.origen = 'nuevo') / sum(g.usd),
               100.0 * sum(g.usd) FILTER (o.origen = 'reetiquetado') / sum(g.usd)
        FROM origen o JOIN glp1 g ON g.receptor_id = o.receptor_id
                                 AND g.anio = 2025 AND g.especialidad = 'respiratorio y sueño'
        """
    )
    a += [
        ("ataque 11 · % del frente de Lilly que va a profesionales nuevos", nuevos, P_1DEC),
        ("ataque 11 · % del frente de Lilly que es reetiquetado", reeti, P_1DEC),
    ]

    (zep,) = q(
        """
        SELECT 100.0 * sum(usd) FILTER (producto = 'ZEPBOUND') / sum(usd)
        FROM glp1 WHERE especialidad = 'respiratorio y sueño' AND grupo = 'lilly' AND anio = 2025
        """
    )
    a.append(("D-011 · % del bloque de Lilly que es Zepbound", zep, P_1DEC))

    # Composición del crecimiento 2023 → 2025 (ataque 10, familia C1).
    comp = con.sql(
        """
        WITH d AS (
            SELECT grupo, especialidad,
                   sum(usd) FILTER (anio = 2025) - sum(usd) FILTER (anio = 2023) AS delta
            FROM glp1 WHERE especialidad IS NOT NULL GROUP BY 1, 2
        ), t AS (SELECT grupo, sum(delta) AS tot FROM d GROUP BY 1)
        SELECT d.grupo, d.especialidad, 100.0 * d.delta / t.tot AS pct
        FROM d JOIN t USING (grupo)
        """
    ).df()
    for g, e, etiqueta in (
        ("novo", "emergentes", "ataque 10 · % del crecimiento de Novo que fue a emergentes"),
        ("lilly", "respiratorio y sueño", "ataque 11 · % del crecimiento de Lilly que fue al bloque respiratorio"),
    ):
        pct = comp[(comp.grupo == g) & (comp.especialidad == e)]["pct"].iloc[0]
        a.append((etiqueta, pct, P_1DEC))

    # Ataque 09: reetiquetado del frente emergente de Novo, y su contracara.
    con.sql(
        """
        CREATE OR REPLACE TEMP VIEW origen_eme AS
        WITH b25 AS (
            SELECT DISTINCT receptor_id FROM glp1
            WHERE especialidad = 'emergentes' AND anio = 2025 AND receptor_id IS NOT NULL
        ), h AS (
            SELECT b.receptor_id,
                   count(*) FILTER (g.anio < 2025) AS previos,
                   count(*) FILTER (g.anio < 2025 AND g.especialidad = 'emergentes') AS previos_bloque,
                   count(*) FILTER (g.anio < 2025 AND g.especialidad <> 'emergentes') AS previos_otra
            FROM b25 b LEFT JOIN glp1 g USING (receptor_id) GROUP BY 1
        )
        SELECT receptor_id,
               CASE WHEN previos = 0 THEN 'nuevo'
                    WHEN previos_otra = 0 THEN 'misma etiqueta'
                    WHEN previos_bloque = 0 THEN 'reetiquetado' ELSE 'mixta' END AS origen
        FROM h
        """
    )
    (reeti_eme,) = q(
        """
        SELECT 100.0 * sum(g.usd) FILTER (o.origen = 'reetiquetado') / sum(g.usd)
        FROM origen_eme o JOIN glp1 g ON g.receptor_id = o.receptor_id
                                     AND g.anio = 2025 AND g.especialidad = 'emergentes'
        """
    )
    a.append(("ataque 09 · % del frente de Novo que es reetiquetado", reeti_eme, P_1DEC))

    # D-010: la única afirmación temporal frágil del caso.
    (crec,) = q(
        """
        SELECT 100.0 * (sum(usd) FILTER (anio = 2025) / sum(usd) FILTER (anio = 2021) - 1)
        FROM glp1 WHERE grupo = 'novo'
        """
    )
    a += [
        ("D-010 · crecimiento nominal de Novo entre 2021 y 2025", crec, P_1DEC),
        ("D-010 · deflactor que lo anula", 1 + crec / 100, P_2DEC),
    ]
    # Los otros dos deflactores que cita el caso: los que harían falta para dar
    # vuelta las dos afirmaciones temporales que sí son robustas.
    defl = con.sql(
        """
        SELECT especialidad,
               sum(usd) FILTER (anio = 2025) / sum(usd) FILTER (anio = 2023) AS d
        FROM glp1 WHERE grupo = 'novo' AND especialidad IN ('endocrinologia', 'emergentes')
        GROUP BY 1
        """
    ).df()
    for _, r in defl.iterrows():
        a.append((f"D-010 · deflactor que anularía el crecimiento de Novo en {r.especialidad}", r.d, P_1DEC))
    return a


def main() -> None:
    rutas = [Path(x) for x in sys.argv[1:]] or sorted(
        (ROOT / "export" / "site" / "content").rglob("index.mdx")
    )
    if not rutas:
        raise SystemExit("No hay writeup que verificar. Pasar una ruta .mdx.")

    con = conectar()
    ase = aserciones_cache() + aserciones_recalculadas(con)
    print(f"{len(ase)} cifras de referencia: "
          f"{len(aserciones_cache())} del cache y el resto recalculadas contra los Parquet.\n")

    rojo = 0
    for ruta in rutas:
        # El locale sale de la ruta, igual que en el lint del sitio.
        locale = "en" if re.search(r"/(content/[a-z]+/)?en/", str(ruta)) else "es"
        texto = texto_publicado(ruta)
        cubiertos, exentos, huerfanos = [], [], []
        for lit, val, ctx in numeros(texto, locale):
            match = next((et for et, v, p in ase if abs(val - v) <= p), None)
            if match:
                cubiertos.append((lit, match))
            elif val in EXENTOS or lit in EXENTOS:
                exentos.append((lit, EXENTOS.get(val) or EXENTOS[lit]))
            else:
                huerfanos.append((lit, ctx))

        print(f"── {ruta} ({locale}) ──")
        print(f"   {len(cubiertos)} cifras con fuente · {len(exentos)} exentas declaradas · "
              f"{len(huerfanos)} SIN FUENTE")
        for lit, et in sorted(set(cubiertos), key=lambda x: x[1]):
            print(f"     ✓ {lit:>12}  ←  {et}")
        for lit, motivo in sorted(set(exentos)):
            print(f"     ~ {lit:>12}  ←  exenta: {motivo}")
        for lit, ctx in huerfanos:
            print(f"     ✖ {lit:>12}  ←  sin fuente: ...{ctx}...")
        print()
        rojo += len(huerfanos)

    print("Estado: 🔴 hay cifras sin fuente" if rojo else "Estado: 🟢 verde")
    sys.exit(1 if rojo else 0)


if __name__ == "__main__":
    main()
