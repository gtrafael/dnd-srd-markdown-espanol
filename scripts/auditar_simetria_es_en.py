#!/usr/bin/env python3
"""Comprueba que ES, referencia canónica, tenga un espejo EN válido."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


EXCLUIR_ES: set[str] = set()


def frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return ""
    fin = texto.find("\n---\n", 4)
    return texto[4:fin] if fin >= 0 else ""


def norm(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[*_]+", "", s)
    return re.sub(r"\s+", " ", s.casefold()).strip()


def wikilink(fm: str, campo: str) -> str | None:
    m = re.search(rf'^{re.escape(campo)}:\s*"\[\[([^\]]+)\]\]"\s*$', fm, re.MULTILINE)
    return m.group(1).split("|", 1)[0].strip() if m else None


def relaciones_en(fm: str) -> list[tuple[str, str]]:
    out = []
    for campo in ("related_en", "related_en_section"):
        destino = wikilink(fm, campo)
        if destino:
            out.append((campo, destino))
    m = re.search(r"^related_en_sections:\s*\[(.*?)\]\s*$", fm, re.MULTILINE)
    if m:
        out.extend(("related_en_sections", x) for x in re.findall(r'"([^"]+)"', m.group(1)))
    return out


def headings(path: Path) -> set[str]:
    return {
        norm(m.group(1))
        for linea in path.read_text(encoding="utf-8").splitlines()
        if (m := re.match(r"^#{1,6}\s+(.+?)\s*$", linea))
    }


def audit(es_root: Path, en_root: Path) -> dict:
    fallos = []
    revisados = 0
    relaciones = 0

    # Los (Alt) son navegación derivada para Obsidian. Deben existir con la
    # misma forma en ambos idiomas y nunca contener una segunda estructura libre.
    rangos = ("A-C", "D-F", "G-I", "J-L", "M-O", "P-R", "S-U", "V-Z")
    alt_esperados = {
        "es": {
            "Animales (Alt)": "Animales",
            "Conjuros (Alt)": "Conjuros",
            "MonstruosDeLaAALaZ (Alt)": "Monstruos A-Z",
            "ObjetosMagicos (Alt)": "Objetos mágicos",
        },
        "en": {
            "Animals (Alt)": "Animals",
            "Spells (Alt)": "Spells",
            "Monsters A-Z (Alt)": "Monsters A-Z",
            "Magic Items (Alt)": "Magic Items",
        },
    }
    for root, idioma in ((es_root, "es"), (en_root, "en")):
        esperados = alt_esperados[idioma]
        encontrados = {
            p.name for p in root.iterdir()
            if p.is_dir() and "(Alt)" in p.name
        }
        if encontrados != set(esperados):
            fallos.append({
                "tipo": "carpetas_alt_asimetricas",
                "idioma": idioma,
                "esperadas": sorted(esperados),
                "encontradas": sorted(encontrados),
            })
        for carpeta, nombre in esperados.items():
            alt = root / carpeta
            if not alt.is_dir():
                continue
            archivos = {p.name for p in alt.glob("*.md")}
            esperados_archivos = {
                f"{nombre} (Alt).md",
                *(f"{nombre} {rango}.md" for rango in rangos),
            }
            if archivos != esperados_archivos:
                fallos.append({
                    "tipo": "indices_alt_incompletos",
                    "idioma": idioma,
                    "carpeta": carpeta,
                    "esperados": sorted(esperados_archivos),
                    "encontrados": sorted(archivos),
                })

    # Cada vista Alt debe cubrir el mismo número total de destinos canónicos.
    # La distribución por rangos puede variar al traducir nombres.
    for carpeta_es, carpeta_en in (
        ("Animales (Alt)", "Animals (Alt)"),
        ("Conjuros (Alt)", "Spells (Alt)"),
        ("MonstruosDeLaAALaZ (Alt)", "Monsters A-Z (Alt)"),
        ("ObjetosMagicos (Alt)", "Magic Items (Alt)"),
    ):
        enlaces_es = sum(
            len(re.findall(r"\[\[[^\]]+\]\]", p.read_text(encoding="utf-8")))
            for p in (es_root / carpeta_es).glob("*.md")
        )
        enlaces_en = sum(
            len(re.findall(r"\[\[[^\]]+\]\]", p.read_text(encoding="utf-8")))
            for p in (en_root / carpeta_en).glob("*.md")
        )
        if enlaces_es != enlaces_en:
            fallos.append({
                "tipo": "cobertura_alt_asimetrica",
                "catalogo_es": carpeta_es,
                "catalogo_en": carpeta_en,
                "enlaces_es": enlaces_es,
                "enlaces_en": enlaces_en,
            })

    indices_es = sorted(
        p.relative_to(es_root).as_posix()
        for p in es_root.rglob("*-Index.md")
        if "(Alt)" not in p.as_posix()
    )
    indices_en = sorted(
        p.relative_to(en_root).as_posix()
        for p in en_root.rglob("*-Index.md")
        if "(Alt)" not in p.as_posix()
    )
    if len(indices_es) != 13 or len(indices_en) != 13:
        fallos.append({
            "tipo": "indices_navegacion_asimetricos",
            "indices_es": len(indices_es),
            "indices_en": len(indices_en),
        })

    for path in sorted(es_root.rglob("*.md")):
        rel = path.relative_to(es_root)
        if any("(Alt)" in parte for parte in rel.parts):
            continue
        if rel.name == "Espanol.md" or rel.name.endswith("-Index.md") or rel.as_posix() in EXCLUIR_ES:
            continue

        revisados += 1
        raw = path.read_text(encoding="utf-8")
        fm = frontmatter(raw)
        pares = relaciones_en(fm)
        sin_equivalente = "sin-equivalente" in fm

        if not pares:
            fallos.append({"tipo": "sin_relacion_en", "archivo": rel.as_posix()})
            continue
        if sin_equivalente:
            fallos.append({"tipo": "etiqueta_sin_equivalente_obsoleta", "archivo": rel.as_posix()})

        modo = re.search(r'^alignment_mode:\s*"?([^"\n]+)"?\s*$', fm, re.MULTILINE)
        modo = modo.group(1).strip() if modo else "file"

        for campo, destino in pares:
            relaciones += 1
            ruta, _, seccion = destino.partition("#")
            en_path = en_root / f"{ruta}.md"
            if not en_path.exists():
                fallos.append({
                    "tipo": "destino_en_inexistente",
                    "archivo": rel.as_posix(),
                    "destino": destino,
                })
                continue

            if seccion and norm(seccion) not in headings(en_path):
                fallos.append({
                    "tipo": "seccion_en_inexistente",
                    "archivo": rel.as_posix(),
                    "destino": destino,
                })

            if campo == "related_en" and modo == "file":
                en_fm = frontmatter(en_path.read_text(encoding="utf-8"))
                vuelta = wikilink(en_fm, "related_es")
                esperado = rel.with_suffix("").as_posix()
                if vuelta != esperado:
                    fallos.append({
                        "tipo": "relacion_no_reciproca",
                        "archivo": rel.as_posix(),
                        "destino": destino,
                        "related_es": vuelta,
                    })

    return {
        "summary": {
            "archivos_es_revisados": revisados,
            "relaciones_es_en": relaciones,
            "indices_es": len(indices_es),
            "indices_en": len(indices_en),
            "indices_alt_es": sum(1 for p in es_root.rglob("*.md") if "(Alt)" in p.as_posix()),
            "indices_alt_en": sum(1 for p in en_root.rglob("*.md") if "(Alt)" in p.as_posix()),
            "fallos": len(fallos),
        },
        "fallos": fallos,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--es", type=Path, default=Path("ES"))
    ap.add_argument("--en", type=Path, default=Path("EN"))
    ap.add_argument("--salida", type=Path, default=Path("auditoria-simetria.json"))
    args = ap.parse_args()

    out = audit(args.es, args.en)
    args.salida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False))
    for fallo in out["fallos"][:100]:
        print(json.dumps(fallo, ensure_ascii=False))
    return 1 if out["fallos"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
