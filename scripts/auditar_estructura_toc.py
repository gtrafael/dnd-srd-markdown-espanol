#!/usr/bin/env python3
"""Audita que main siga el TOC oficial y las reglas canónicas del proyecto.

Convención:
- capítulo de nivel superior -> carpeta;
- entrada directa del capítulo -> archivo;
- catálogos grandes del TOC -> subcarpeta contenedora;
- niveles inferiores -> encabezados dentro del archivo padre;
- la maquetación visual (incluidos recuadros) nunca crea archivos;
- toda carpeta canónica tiene un único 00-*-Index.md generado.
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
    "Glosario de reglas": "GlosarioDeReglas",
    "Herramientas del juego": "HerramientasDelJuego",
    "Objetos mágicos": "ObjetosMagicos",
    "Monstruos": "Monstruos",
    "Monstruos de la A a la Z": "MonstruosDeLaAALaZ",
    "Animales": "Animales",
}

CATALOGOS = {
    ("Conjuros", "Descripciones de conjuros"): "DescripcionesDeConjuros",
    ("Objetos mágicos", "Objetos mágicos de la A a la Z"): "ObjetosMagicosDeLaAALaZ",
}

CARPETAS_ENTIDADES = {"MonstruosDeLaAALaZ", "Animales"}


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


def indice_esperado(folder: Path) -> str:
    return f"00-{folder.name}-Index.md"


def auditar_indices(raiz: Path) -> list[dict]:
    fallos = []
    for folder in sorted(p for p in raiz.rglob("*") if p.is_dir() and "(Alt)" not in p.name):
        indices = [p.name for p in folder.glob("*-Index.md")]
        esperado = indice_esperado(folder)
        if indices != [esperado]:
            fallos.append({"carpeta": str(folder), "indices": indices, "esperado": esperado})
    return fallos


def auditar(indice: dict, raiz: Path) -> dict:
    capitulos = []
    total_fallos = 0

    recuadros = []
    for p in raiz.rglob("*.md"):
        if "(Alt)" in p.as_posix() or p.name.endswith("-Index.md"):
            continue
        fm = frontmatter(p.read_text(encoding="utf-8")).casefold()
        if "recuadro" in fm or "callout" in fm:
            recuadros.append(str(p.relative_to(raiz)))

    fallos_indices = auditar_indices(raiz)
    total_fallos += len(recuadros) + len(fallos_indices)

    for capitulo, carpeta in MAPA_CARPETAS.items():
        meta = indice.get(capitulo)
        if not isinstance(meta, dict):
            capitulos.append({"capitulo": capitulo, "error": "capitulo_no_en_indice"})
            total_fallos += 1
            continue

        root = raiz / carpeta
        if not root.exists():
            capitulos.append({"capitulo": capitulo, "carpeta": carpeta, "error": "carpeta_no_existe"})
            total_fallos += 1
            continue

        children = meta.get("children", {})
        if not isinstance(children, dict):
            children = {}

        archivos = {}
        for p in sorted(root.glob("*.md")):
            if p.name.endswith("-Index.md"):
                continue
            h1 = primer_h1(p.read_text(encoding="utf-8"))
            archivos[p.name] = {"path": p, "h1": h1, "clave_h1": clave(h1 or "")}

        faltantes = []
        duplicados = []
        extras = []
        catalogos_faltantes = []

        claves_hijos = {clave(x) for x in children}
        descendientes = titulos_descendientes(meta)

        for titulo in children:
            catalogo = CATALOGOS.get((capitulo, titulo))
            if catalogo:
                sub = root / catalogo
                if not sub.is_dir():
                    catalogos_faltantes.append({"titulo": titulo, "carpeta": catalogo})
                continue

            k = clave(titulo)
            matches = [x for x in archivos.values() if x["clave_h1"] == k]
            if not matches:
                faltantes.append(titulo)
            elif len(matches) > 1:
                duplicados.append({"titulo": titulo, "archivos": [m["path"].name for m in matches]})

        for nombre, info in archivos.items():
            k = info["clave_h1"]
            if k == clave(capitulo) or k in claves_hijos or k in descendientes:
                continue
            if carpeta in CARPETAS_ENTIDADES:
                continue
            extras.append({"archivo": nombre, "h1": info["h1"]})

        fallos = len(faltantes) + len(duplicados) + len(extras) + len(catalogos_faltantes)
        total_fallos += fallos
        capitulos.append({
            "capitulo": capitulo,
            "carpeta": carpeta,
            "faltantes": faltantes,
            "duplicados": duplicados,
            "catalogos_faltantes": catalogos_faltantes,
            "extras_no_toc": extras,
            "fallos": fallos,
        })

    return {
        "fallos": total_fallos,
        "recuadros_separados": recuadros,
        "indices_incorrectos": fallos_indices,
        "capitulos": capitulos,
    }


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
    if out["recuadros_separados"]:
        print("Recuadros separados:", out["recuadros_separados"])
    if out["indices_incorrectos"]:
        print("Índices incorrectos:", out["indices_incorrectos"])
    for c in out["capitulos"]:
        if c.get("fallos"):
            print(c["capitulo"], json.dumps({
                "faltantes": c["faltantes"],
                "duplicados": c["duplicados"],
                "catalogos_faltantes": c["catalogos_faltantes"],
                "extras_no_toc": c["extras_no_toc"],
            }, ensure_ascii=False))
    return 1 if out["fallos"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
