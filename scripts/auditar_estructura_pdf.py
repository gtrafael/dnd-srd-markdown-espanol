#!/usr/bin/env python3
"""Audita estructura visual del SRD directamente sobre los PDF oficiales.

No modifica el corpus. Genera evidencia para G1:
- jerarquía/TOC con páginas;
- candidatos a recuadros o callouts;
- tablas detectadas;
- posibles continuaciones de tablas entre páginas consecutivas.

Los resultados son candidatos de QA: una detección geométrica no decide por sí sola
la estructura canónica.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import fitz  # PyMuPDF


def color_gris(fill) -> tuple[bool, float | None]:
    if fill is None:
        return False, None
    if len(fill) == 1:
        brillo = float(fill[0])
        return True, brillo
    if len(fill) >= 3:
        r, g, b = map(float, fill[:3])
        gris = max(r, g, b) - min(r, g, b) <= 0.06
        return gris, (r + g + b) / 3
    return False, None


def texto_en_rect(page: fitz.Page, rect: fitz.Rect) -> str:
    bloques = []
    for b in page.get_text("blocks"):
        br = fitz.Rect(b[:4])
        centro = fitz.Point((br.x0 + br.x1) / 2, (br.y0 + br.y1) / 2)
        if rect.contains(centro):
            texto = re.sub(r"\s+", " ", str(b[4])).strip()
            if texto:
                bloques.append((br.y0, br.x0, texto))
    bloques.sort()
    return "\n".join(x[2] for x in bloques)


def detectar_callouts(page: fitz.Page) -> list[dict]:
    candidatos = []
    area_pagina = page.rect.width * page.rect.height

    for dibujo in page.get_drawings():
        rect = dibujo.get("rect")
        fill = dibujo.get("fill")
        if rect is None or fill is None:
            continue

        rect = fitz.Rect(rect)
        gris, brillo = color_gris(fill)
        if not gris or brillo is None:
            continue

        area = rect.width * rect.height
        # Los recuadros del SRD son cajas relativamente grandes. Se deja margen
        # para no perder recuadros pequeños; tablas y bandas se filtran después.
        if rect.width < 120 or rect.height < 34:
            continue
        if area < 6500 or area > area_pagina * 0.75:
            continue
        if not (0.45 <= brillo <= 0.96):
            continue

        texto = texto_en_rect(page, rect)
        palabras = re.findall(r"\w+", texto, flags=re.UNICODE)
        if len(palabras) < 12:
            continue

        lineas = [x.strip() for x in texto.splitlines() if x.strip()]
        titulo = lineas[0][:160] if lineas else ""
        candidatos.append(
            {
                "bbox": [round(rect.x0, 2), round(rect.y0, 2), round(rect.x1, 2), round(rect.y1, 2)],
                "brillo_relleno": round(brillo, 4),
                "texto": texto,
                "titulo_candidato": titulo,
                "palabras": len(palabras),
            }
        )

    # Deduplicar cajas casi idénticas o anidadas.
    salida = []
    for c in sorted(candidatos, key=lambda x: (x["bbox"][1], x["bbox"][0], -x["palabras"])):
        r = fitz.Rect(c["bbox"])
        duplicado = False
        for e in salida:
            er = fitz.Rect(e["bbox"])
            inter = r & er
            if inter.is_empty:
                continue
            menor = min(r.get_area(), er.get_area())
            if menor and inter.get_area() / menor > 0.90:
                duplicado = True
                break
        if not duplicado:
            salida.append(c)
    return salida


def solapamiento(a: list[float], b: list[float]) -> float:
    ra, rb = fitz.Rect(a), fitz.Rect(b)
    inter = ra & rb
    if inter.is_empty:
        return 0.0
    menor = min(ra.get_area(), rb.get_area())
    return inter.get_area() / menor if menor else 0.0


def ratio_lineas_numeradas(texto: str) -> float:
    lineas = [x.strip() for x in texto.splitlines() if x.strip()]
    if not lineas:
        return 0.0
    numeradas = sum(bool(re.match(r"^\d{1,3}(?:\s|$)", x)) for x in lineas)
    return numeradas / len(lineas)


def clasificar_cajas(cajas: list[dict], tablas_pagina: list[dict]) -> list[dict]:
    salida = []
    for caja in cajas:
        overlaps = [solapamiento(caja["bbox"], t["bbox"]) for t in tablas_pagina]
        max_overlap = max(overlaps, default=0.0)
        ratio_num = ratio_lineas_numeradas(caja["texto"])
        titulo = caja.get("titulo_candidato", "").strip()
        parece_fila = bool(
            re.match(r"^\\d{1,3}(?:\\s|[–—-]\\d{1,3})", titulo)
            or re.match(r"^\\d{1,3}–\\d{1,3}", titulo)
        )
        if max_overlap >= 0.45:
            tipo = "tabla_o_bloque_tabular"
        elif ratio_num >= 0.45 or parece_fila:
            tipo = "fragmento_tabular"
        else:
            tipo = "recuadro"
        caja = dict(caja)
        caja["tipo"] = tipo
        caja["solapamiento_tabla"] = round(max_overlap, 4)
        caja["ratio_lineas_numeradas"] = round(ratio_num, 4)
        salida.append(caja)
    return salida


def tabla_a_dict(tabla, page: fitz.Page, pagina: int, indice: int) -> dict:
    bbox = list(map(float, tabla.bbox))
    datos = tabla.extract() or []
    filas = []
    for fila in datos:
        filas.append([None if c is None else re.sub(r"\s+", " ", str(c)).strip() for c in fila])
    cols = max((len(f) for f in filas), default=0)
    superior = fitz.Rect(
        max(0, bbox[0] - 4),
        max(0, bbox[1] - 42),
        min(page.rect.width, bbox[2] + 4),
        bbox[1],
    )
    contexto = re.sub(r"\s+", " ", page.get_textbox(superior)).strip()
    return {
        "id_local": f"p{pagina}-t{indice}",
        "pagina": pagina,
        "bbox": [round(x, 2) for x in bbox],
        "filas": len(filas),
        "columnas": cols,
        "contexto_superior": contexto,
        "datos": filas,
        "muestra": filas[:4],
    }


def detectar_tablas(doc: fitz.Document) -> list[dict]:
    tablas = []
    for pno in range(len(doc)):
        page = doc[pno]
        try:
            finder = page.find_tables()
            encontradas = list(finder.tables)
        except Exception:
            encontradas = []
        for i, tabla in enumerate(encontradas, 1):
            tablas.append(tabla_a_dict(tabla, page, pno + 1, i))
    return tablas


def compatibilidad_columnas(a: dict, b: dict, ancho_pagina: float) -> float:
    if a["columnas"] != b["columnas"] or a["columnas"] == 0:
        return 0.0
    ar = a["bbox"]
    br = b["bbox"]
    # Una tabla puede saltar de la columna derecha a la izquierda al cambiar
    # de página. Por eso se compara principalmente número de columnas y ancho,
    # no la coordenada X absoluta.
    wa = ar[2] - ar[0]
    wb = br[2] - br[0]
    if not wa or not wb:
        return 0.0
    return min(wa, wb) / max(wa, wb)


def continuaciones_tablas(doc: fitz.Document, tablas: list[dict], cajas: list[dict]) -> list[dict]:
    por_pagina: dict[int, list[dict]] = {}
    for t in tablas:
        por_pagina.setdefault(t["pagina"], []).append(t)
    cajas_por_pagina: dict[int, list[dict]] = {}
    for caja in cajas:
        cajas_por_pagina.setdefault(caja["pagina"], []).append(caja)

    candidatos = []
    vistos = set()
    for p in range(1, len(doc)):
        page_a = doc[p - 1]
        page_b = doc[p]
        altura_a = page_a.rect.height
        altura_b = page_b.rect.height
        ancho = page_a.rect.width

        final = [t for t in por_pagina.get(p, []) if t["bbox"][3] >= altura_a * 0.74]
        inicio = [t for t in por_pagina.get(p + 1, []) if t["bbox"][1] <= altura_b * 0.30]

        for a in final:
            for b in inicio:
                score = compatibilidad_columnas(a, b, ancho)
                if score < 0.72:
                    continue
                cab_a = a["muestra"][0] if a["muestra"] else []
                cab_b = b["muestra"][0] if b["muestra"] else []
                key=(p,p+1,a["id_local"],b["id_local"])
                if key in vistos:
                    continue
                vistos.add(key)
                candidatos.append({
                    "tipo": "tabla_a_tabla",
                    "pagina_origen": p,
                    "pagina_destino": p + 1,
                    "tabla_origen": a["id_local"],
                    "tabla_destino": b["id_local"],
                    "columnas": a["columnas"],
                    "compatibilidad_geometrica": round(score, 4),
                    "cabecera_repetida": bool(cab_a and cab_b and cab_a == cab_b),
                    "muestra_final": a["muestra"][-2:],
                    "muestra_inicio": b["muestra"][:2],
                })

        # Algunas continuaciones pierden la estructura vectorial de tabla en la
        # página siguiente (p. ej. Bagatelas 30→31). Se conserva como candidato
        # si el bloque gris superior está dominado por filas que empiezan por número.
        fragmentos = [
            x for x in cajas_por_pagina.get(p + 1, [])
            if x.get("tipo") == "fragmento_tabular" and x["bbox"][1] <= altura_b * 0.32
        ]
        for a in final:
            for frag in fragmentos:
                key=(p,p+1,a["id_local"],tuple(frag["bbox"]))
                if key in vistos:
                    continue
                vistos.add(key)
                candidatos.append({
                    "tipo": "tabla_a_fragmento",
                    "pagina_origen": p,
                    "pagina_destino": p + 1,
                    "tabla_origen": a["id_local"],
                    "fragmento_destino_bbox": frag["bbox"],
                    "ratio_lineas_numeradas": frag["ratio_lineas_numeradas"],
                    "muestra_final": a["muestra"][-2:],
                    "muestra_inicio": frag["texto"].splitlines()[:3],
                })
    return candidatos


def toc_jerarquico(doc: fitz.Document) -> list[dict]:
    toc = doc.get_toc(simple=True)
    salida: list[dict] = []
    pila: list[str] = []
    for nivel, titulo, pagina in toc:
        nivel = max(1, int(nivel))
        pila = pila[: nivel - 1]
        pila.append(str(titulo).strip())
        salida.append(
            {
                "nivel": nivel,
                "titulo": str(titulo).strip(),
                "pagina": int(pagina),
                "jerarquia": list(pila),
            }
        )
    return salida


def auditar(pdf: Path, idioma: str) -> dict:
    doc = fitz.open(pdf)
    cajas_raw = []
    for pno in range(len(doc)):
        page = doc[pno]
        for caja in detectar_callouts(page):
            caja["pagina"] = pno + 1
            cajas_raw.append(caja)

    tablas = detectar_tablas(doc)
    tablas_por_pagina: dict[int, list[dict]] = {}
    for t in tablas:
        tablas_por_pagina.setdefault(t["pagina"], []).append(t)

    cajas = []
    for pno in range(1, len(doc)+1):
        pagina = [x for x in cajas_raw if x["pagina"] == pno]
        cajas.extend(clasificar_cajas(pagina, tablas_por_pagina.get(pno, [])))

    recuadros = [x for x in cajas if x["tipo"] == "recuadro"]
    continuaciones = continuaciones_tablas(doc, tablas, cajas)

    controles = {}
    if idioma == "es":
        esperados = {
            8: "Inspiración heroica",
            13: "Orden de marcha",
            14: "Jugar con una cuadrícula",
            98: "Armas improvisadas",
            116: "Identificar un conjuro activo",
        }
        controles["recuadros_conocidos"] = {
            str(p): any(
                x["pagina"] == p and titulo.lower() in x["texto"].lower()
                for x in recuadros
            )
            for p, titulo in esperados.items()
        }
        pares={(x["pagina_origen"],x["pagina_destino"]) for x in continuaciones}
        controles["tablas_multipagina_conocidas"] = {
            "22-23": (22,23) in pares,
            "30-31": (30,31) in pares,
        }

    return {
        "idioma": idioma,
        "pdf": pdf.name,
        "paginas": len(doc),
        "toc": toc_jerarquico(doc),
        "cajas_grises": cajas,
        "callouts": recuadros,
        "tablas": tablas,
        "continuaciones_tabla": continuaciones,
        "controles": controles,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-es", type=Path, required=True)
    parser.add_argument("--pdf-en", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()

    informe = {
        "es": auditar(args.pdf_es, "es"),
        "en": auditar(args.pdf_en, "en"),
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    controles = informe["es"].get("controles", {})
    fallos = []
    for grupo, valores in controles.items():
        for nombre, ok in valores.items():
            if not ok:
                fallos.append(f"{grupo}:{nombre}")
    if fallos:
        raise SystemExit("Auditoría estructural: no se detectaron controles conocidos: " + ", ".join(fallos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
