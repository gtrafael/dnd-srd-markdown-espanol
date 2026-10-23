#!/usr/bin/env python3
"""Genera relaciones Obsidian en frontmatter para la bóveda ES.

El cuerpo Markdown de las notas no se modifica. El script detecta menciones
textuales a un catálogo de notas y escribe únicamente la propiedad
`wikilinks_auto` en el frontmatter.

Uso:
    python scripts/generar_wikilinks_es.py --dry-run
    python scripts/generar_wikilinks_es.py
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


AUTO_PROPERTY = "wikilinks_auto"

# Las clases son una excepción: la carpeta ES/Clases contiene también notas
# auxiliares que no son clases. Por eso se enumeran explícitamente.
CLASS_FILES = (
    "Barbaro.md",
    "Bardo.md",
    "Brujo.md",
    "Clerigo.md",
    "Druida.md",
    "Explorador.md",
    "Guerrero.md",
    "Hechicero.md",
    "Mago.md",
    "Monje.md",
    "Paladin.md",
    "Picaro.md",
)

# El resto de familias se toman por carpeta, excluyendo *-Index.md.
SOURCE_DIRS = (
    "Animales",
    "Conjuros",
    "Dotes",
    "Equipo",
    "MonstruosDeLaAALaZ",
    "ObjetosMagicos",
)


@dataclass(frozen=True)
class Concept:
    title: str
    path: Path  # ruta relativa a ES/, con extensión .md

    @property
    def wikilink(self) -> str:
        target = self.path.with_suffix("").as_posix()
        return f"[[{target}|{self.title}]]"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Detecta menciones a notas seleccionadas y genera wikilinks "
            "en la propiedad de frontmatter wikilinks_auto."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Raíz del repositorio (por defecto se infiere desde scripts/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calcula los cambios y muestra el resumen sin escribir archivos.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra cada nota que cambiaría y sus relaciones detectadas.",
    )
    return parser.parse_args()


def first_h1(markdown: str) -> str | None:
    """Devuelve el primer H1 del cuerpo, ignorando el frontmatter."""
    body = strip_frontmatter(markdown)
    match = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    if not match:
        return None

    title = match.group(1).strip()
    # Limpieza conservadora de énfasis/código inline alrededor del título.
    title = re.sub(r"^[*_\`]+|[*_\`]+$", "", title).strip()
    return title or None


def strip_frontmatter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown

    match = re.match(r"^---(?:\r?\n)(.*?)(?:\r?\n)---(?:\r?\n|$)", markdown, re.S)
    if not match:
        return markdown
    return markdown[match.end():]


def normalized_title(value: str) -> str:
    """Normalización para comparar títulos sin alterar acentos."""
    return re.sub(r"\s+", " ", value).strip().casefold()


def is_index(path: Path) -> bool:
    return path.name.lower().endswith("-index.md")


def is_alt_path(path: Path) -> bool:
    return any(part.endswith(" (Alt)") for part in path.parts)


def source_files(es_root: Path) -> list[Path]:
    files: list[Path] = []

    classes_dir = es_root / "Clases"
    for name in CLASS_FILES:
        path = classes_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Falta la clase esperada: {path}")
        files.append(path)

    for dirname in SOURCE_DIRS:
        folder = es_root / dirname
        if not folder.is_dir():
            raise FileNotFoundError(f"Falta la carpeta esperada: {folder}")
        files.extend(
            path
            for path in sorted(folder.glob("*.md"))
            if not is_index(path)
        )

    return files


def build_catalog(es_root: Path) -> tuple[dict[str, Concept], dict[str, list[Concept]]]:
    by_key: dict[str, list[Concept]] = defaultdict(list)

    for path in source_files(es_root):
        text = path.read_text(encoding="utf-8")
        title = first_h1(text)
        if not title:
            print(f"AVISO: sin H1, se omite del catálogo: {path}", file=sys.stderr)
            continue

        concept = Concept(title=title, path=path.relative_to(es_root))
        by_key[normalized_title(title)].append(concept)

    ambiguous = {key: values for key, values in by_key.items() if len(values) > 1}
    unique = {key: values[0] for key, values in by_key.items() if len(values) == 1}
    return unique, ambiguous


def compile_matcher(catalog: dict[str, Concept]) -> re.Pattern[str]:
    # Más largos primero para evitar que un concepto corto "robe" parte de otro.
    titles = sorted(
        (concept.title for concept in catalog.values()),
        key=lambda value: (-len(value), value.casefold()),
    )

    alternatives = []
    for title in titles:
        escaped = re.escape(title)
        escaped = escaped.replace(r"\ ", r"\s+")
        alternatives.append(escaped)

    if not alternatives:
        raise RuntimeError("El catálogo de conceptos está vacío.")

    # Límites de palabra Unicode. Evita, por ejemplo, enlazar "Mago" dentro de
    # una palabra mayor, pero permite títulos con espacios o puntuación.
    return re.compile(
        r"(?<!\w)(" + "|".join(alternatives) + r")(?!\w)",
        re.IGNORECASE,
    )


def iter_target_notes(es_root: Path):
    """Notas de contenido que se enriquecen con relaciones automáticas."""
    for path in sorted(es_root.rglob("*.md")):
        rel = path.relative_to(es_root)
        if is_alt_path(rel):
            continue
        if is_index(rel):
            continue
        yield path


def detect_links(
    note_path: Path,
    markdown: str,
    es_root: Path,
    catalog: dict[str, Concept],
    matcher: re.Pattern[str],
) -> list[str]:
    body = strip_frontmatter(markdown)
    current_rel = note_path.relative_to(es_root)

    links: list[str] = []
    seen: set[str] = set()

    for match in matcher.finditer(body):
        key = normalized_title(match.group(1))
        concept = catalog.get(key)
        if concept is None:
            continue
        if concept.path == current_rel:
            continue

        wikilink = concept.wikilink
        if wikilink not in seen:
            seen.add(wikilink)
            links.append(wikilink)

    return links


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def remove_auto_property(frontmatter_lines: list[str]) -> list[str]:
    """Elimina una propiedad wikilinks_auto previa, sea lista o valor simple."""
    result: list[str] = []
    i = 0
    key_pattern = re.compile(rf"^{re.escape(AUTO_PROPERTY)}\s*:")

    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if key_pattern.match(line):
            i += 1
            while i < len(frontmatter_lines):
                next_line = frontmatter_lines[i]
                if next_line.startswith((" ", "\t")) or not next_line.strip():
                    i += 1
                    continue
                break
            continue

        result.append(line)
        i += 1

    return result


def update_frontmatter(markdown: str, links: list[str]) -> str:
    newline = "\r\n" if "\r\n" in markdown[:200] else "\n"

    if markdown.startswith("---" + newline):
        lines = markdown.splitlines(keepends=True)
        close_idx = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                close_idx = idx
                break

        if close_idx is None:
            raise ValueError("Frontmatter abierto pero sin delimitador de cierre.")

        fm_lines = [line.rstrip("\r\n") for line in lines[1:close_idx]]
        body = "".join(lines[close_idx + 1 :])
    else:
        fm_lines = []
        body = markdown

    fm_lines = remove_auto_property(fm_lines)

    # Evita acumular líneas vacías al final del frontmatter.
    while fm_lines and not fm_lines[-1].strip():
        fm_lines.pop()

    if links:
        fm_lines.append(AUTO_PROPERTY + ":")
        fm_lines.extend(f"  - {yaml_quote(link)}" for link in links)

    # Si una nota no tenía frontmatter y tampoco tiene relaciones, no se toca.
    if not fm_lines and not markdown.startswith("---" + newline):
        return markdown

    frontmatter = (
        "---"
        + newline
        + newline.join(fm_lines)
        + newline
        + "---"
        + newline
    )

    # Si ya había frontmatter, el cuerpo comienza exactamente donde comenzaba.
    # Si se crea uno nuevo, se añade una línea en blanco antes del cuerpo.
    if markdown.startswith("---" + newline):
        return frontmatter + body
    return frontmatter + newline + body


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    es_root = root / "ES"

    if not es_root.is_dir():
        print(f"ERROR: no existe {es_root}", file=sys.stderr)
        return 2

    catalog, ambiguous = build_catalog(es_root)

    if ambiguous:
        print(
            f"AVISO: {len(ambiguous)} títulos ambiguos se omiten para evitar enlaces incorrectos:",
            file=sys.stderr,
        )
        for concepts in ambiguous.values():
            details = ", ".join(str(c.path) for c in concepts)
            print(f"  - {concepts[0].title}: {details}", file=sys.stderr)

    matcher = compile_matcher(catalog)

    scanned = 0
    changed = 0
    generated_links = 0

    for path in iter_target_notes(es_root):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        links = detect_links(path, original, es_root, catalog, matcher)
        updated = update_frontmatter(original, links)

        if updated == original:
            continue

        changed += 1
        generated_links += len(links)

        if args.verbose:
            rel = path.relative_to(root)
            print(f"{rel}: {len(links)} enlaces")
            for link in links:
                print(f"  {link}")

        if not args.dry_run:
            path.write_text(updated, encoding="utf-8", newline="")

    mode = "DRY-RUN" if args.dry_run else "ESCRITURA"
    print(
        f"[{mode}] conceptos={len(catalog)} "
        f"ambiguos={len(ambiguous)} "
        f"notas_escaneadas={scanned} "
        f"notas_modificadas={changed} "
        f"wikilinks_generados={generated_links}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
