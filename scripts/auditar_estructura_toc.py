#!/usr/bin/env python3
"""Audita que la estructura ES siga el índice/TOC oficial.

Convención:
- capítulo de nivel superior -> carpeta;
- entrada directa del capítulo con contenido propio -> archivo;
- niveles inferiores -> pueden permanecer como encabezados dentro del archivo padre;
- recuadros/callouts son excepciones permitidas;
- notas hoja de catálogos también son permitidas.

No modifica archivos.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

MAPA_CARPETAS = {
    "Cómo jugar": "ComoJugar",
    "Creación de personajes": "CreacionDePersonajes",
    "Clases": "Clases",
    "Orígenes de personaje": "OrigenesDePersonaje",
    "Dotes": "Dotes",
    "Equipo": "Equipo",
    "Conjuros": "Conjuros",
    "Herramientas del juego": "HerramientasDelJuego",
    "Objetos mágicos": "ObjetosMagicos",
    "Monstruos": "Monstruos",
}

CATALOGOS = {
    ("Conjuros", "Descripciones de conjuros"),
    ("Objetos mágicos", "Objetos mágicos de la A a la Z"),
}

CARPETAS_CON_ENTIDADES = {"Conjuros", "ObjetosMagicos"}


def clave(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.casefold())


def frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return ""
    fin = texto.find("\n---\n", 4)
    return texto[4:fin] if fin >= 0 else ""


def primer_h1(texto: str) -> str | None:
    for linea in texto.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", linea)
        if m:
            return re.sub(r"[*_]", "", m.group(1)).strip()
    return None


def es_recuadro(texto: str) -> bool:
    fm = frontmatter(texto).casefold()
    return "recuadro" in fm or "callout" in fm


def titulos_descendientes(meta: dict) -> set[str]:
    out: set[str] = set()
    children = meta.get("children", {})
    if not isinstance(children, dict):
        return out
    for titulo, child in children.items():
        out.add(clave(titulo))
        if isinstance(child, dict):
            out |= titulos_descendientes(child)
    return out


def auditar(indice: dict, raiz: Path) -> dict:
    capitulos = []
    total_fallos = 0

    for capitulo, carpeta in MAPA_CARPETAS.items():
        meta = indice.get(capitulo)
        if not isinstance(meta, dict):
            capitulos.append({"capitulo": capitulo, "error": "capitulo_no_en_indice"})
            total_fallos += 1
            continue

        children = meta.get("children", {})
        if not isinstance(children, dict):
            children = {}

        root = raiz / carpeta
        archivos = {}
        if root.exists():
            for p in sorted(root.glob("*.md")):
                if p.name.endswith("-Index.md"):
                    continue
                raw = p.read_text(encoding="utf-8")
                h1 = primer_h1(raw)
                archivos[p.name] = {
                    "path": p,
                    "h1": h1,
                    "clave_h1": clave(h1 or ""),
                    "recuadro": es_recuadro(raw),
                }

        requeridos = []
        faltantes = []
        nombres_incoherentes = []
        duplicados = []

        claves_hijos = {clave(x) for x in children}

        for titulo in children:
            if (capitulo, titulo) in CATALOGOS:
                continue
            k = clave(titulo)
            matches = [x for x in archivos.values() if x["clave_h1"] == k]
            requeridos.append(titulo)
            if not matches:
                faltantes.append(titulo)
                continue
            if len(matches) > 1:
                duplicados.append({
                    "titulo": titulo,
                    "archivos": [m["path"].name for m in matches],
                })
                continue
            stem = matches[0]["path"].stem
            if clave(stem) != k:
                nombres_incoherentes.append({
                    "titulo": titulo,
                    "archivo": matches[0]["path"].name,
                })

        descendientes = titulos_descendientes(meta)
        extras = []
        for nombre, info in archivos.items():
            if info["recuadro"]:
                continue
            k = info["clave_h1"]
            if k == clave(capitulo):
                continue
            if k in claves_hijos:
                continue
            if k in descendientes:
                continue
            if carpeta in CARPETAS_CON_ENTIDADES:
                continue
            extras.append({"archivo": nombre, "h1": info["h1"]})

        fallos = len(faltantes) + len(nombres_incoherentes) + len(duplicados) + len(extras)
        total_fallos += fallos
        capitulos.append({
            "capitulo": capitulo,
            "carpeta": carpeta,
            "requeridos": requeridos,
            "faltantes": faltantes,
            "nombres_incoherentes": nombres_incoherentes,
            "duplicados": duplicados,
            "extras_no_toc": extras,
            "fallos": fallos,
        })

    return {"fallos": total_fallos, "capitulos": capitulos}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--indice", type=Path, required=True)
    ap.add_argument("--es", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    args = ap.parse_args()

    indice = json.loads(args.indice.read_text(encoding="utf-8"))
    out = auditar(indice, args.es)
    args.salida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Fallos estructurales:", out["fallos"])
    for c in out["capitulos"]:
        if c.get("fallos"):
            print(c["capitulo"], json.dumps({
                "faltantes": c["faltantes"],
                "nombres_incoherentes": c["nombres_incoherentes"],
                "duplicados": c["duplicados"],
                "extras_no_toc": c["extras_no_toc"],
            }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
