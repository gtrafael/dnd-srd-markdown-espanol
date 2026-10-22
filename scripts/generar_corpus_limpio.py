#!/usr/bin/env python3
"""Genera in-place la variante limpia destinada a custom/corpus.

Debe ejecutarse únicamente sobre una rama desechable creada desde custom/main.
No corrige contenido normativo: elimina metadatos de Obsidian, índices y
duplicados estructurales ya identificados.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUIR_ES = {
    # Agregado que duplica las notas Letra*.md.
    "GlosarioDeReglas/DefinicionesDeLasReglas.md",
}

EXCLUIR_EN = {
    "Animals/Animals.md",
    "Characterizations/Characterizations.md",
    "Classes/Classes.md",
    "Equipment/Trade Goods.md",
    "Gamemastering/Gamemastering.md",
    "Gamemastering/Objects.md",
    "Gameplay/Gameplay.md",
    "Rules Glossary/Index.md",
    "Spells/Spells.md",
    "Treasure/Treasure.md",
}


def leer_frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return ""
    fin = texto.find("\n---\n", 4)
    return texto[4:fin] if fin >= 0 else ""


def quitar_frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return texto
    fin = texto.find("\n---\n", 4)
    return texto[fin + 5 :] if fin >= 0 else texto


def extraer_relacion(frontmatter: str, campo: str) -> str | None:
    m = re.search(
        rf'^{re.escape(campo)}:\s*"\[\[([^\]]+)\]\]"\s*$',
        frontmatter,
        flags=re.MULTILINE,
    )
    if not m:
        return None
    return m.group(1).split("|", 1)[0].strip()


def limpiar_wikilinks(texto: str) -> str:
    def repl(m: re.Match[str]) -> str:
        contenido = m.group(1)
        if "|" in contenido:
            return contenido.rsplit("|", 1)[1]
        return contenido.rsplit("/", 1)[-1]

    return re.sub(r"\[\[([^\]]+)\]\]", repl, texto)


def limpiar(texto: str) -> str:
    texto = quitar_frontmatter(texto)
    texto = limpiar_wikilinks(texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"<img\b[^>]*>", "", texto, flags=re.IGNORECASE)
    texto = "\n".join(linea.rstrip() for linea in texto.splitlines())
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip() + "\n"


def excluir(rel: Path, idioma: str) -> bool:
    if any("(Alt)" in parte for parte in rel.parts):
        return True
    if rel.name in {"Espanol.md", "English.md"}:
        return True
    if rel.name.endswith("-Index.md"):
        return True
    tabla = EXCLUIR_ES if idioma == "ES" else EXCLUIR_EN
    return rel.as_posix() in tabla


def preparar_idioma(idioma: str, relaciones: list[dict]) -> None:
    raiz = ROOT / idioma
    campo = "related_en" if idioma == "ES" else "related_es"

    for directorio in sorted(
        (p for p in raiz.rglob("*") if p.is_dir() and "(Alt)" in p.name),
        reverse=True,
    ):
        shutil.rmtree(directorio)

    for path in sorted(raiz.rglob("*.md")):
        rel = path.relative_to(raiz)
        if excluir(rel, idioma):
            path.unlink()
            continue

        raw = path.read_text(encoding="utf-8")
        destino = extraer_relacion(leer_frontmatter(raw), campo)
        if destino:
            relaciones.append(
                {
                    "idioma": idioma.lower(),
                    "archivo": rel.as_posix(),
                    "campo": campo,
                    "destino": destino,
                }
            )

        # El agregado Conjuros duplica ObtenerConjuros + LanzarConjuros.
        # Conservamos únicamente la introducción del capítulo.
        if idioma == "ES" and rel.as_posix() == "Conjuros/Conjuros.md":
            cuerpo = quitar_frontmatter(raw)
            corte = cuerpo.find("\n## Obtener conjuros")
            if corte >= 0:
                raw = cuerpo[:corte]

        path.write_text(limpiar(raw), encoding="utf-8")

    for directorio in sorted(
        (p for p in raiz.rglob("*") if p.is_dir()),
        reverse=True,
    ):
        if not any(directorio.iterdir()):
            directorio.rmdir()


def main() -> int:
    relaciones: list[dict] = []
    preparar_idioma("ES", relaciones)
    preparar_idioma("EN", relaciones)

    metadata = ROOT / "metadata"
    metadata.mkdir(exist_ok=True)
    (metadata / "pares-bilingues.json").write_text(
        json.dumps({"relaciones": relaciones}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
