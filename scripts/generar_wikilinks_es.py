#!/usr/bin/env python3
"""Genera wikilinks automáticos en ES sin crear ni alterar entidades.

V3:
- solo enlaza a notas físicas que ya representan una entidad;
- nunca crea notas auxiliares;
- nunca modifica el cuerpo Markdown;
- excluye índices, carpetas (Alt) y notas contenedoras como destinos;
- resuelve primero la coincidencia textual más larga;
- conserva todos los destinos cuando dos entidades reales comparten nombre.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

AUTO_PROPERTY = "wikilinks_auto"


@dataclass(frozen=True)
class Concept:
    title: str
    path: Path
    kind: str

    @property
    def wikilink(self) -> str:
        target = self.path.with_suffix("").as_posix()
        return f"[[{target}|{self.title}]]"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera relaciones Obsidian entre entidades físicas de ES."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Raíz del repositorio.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def split_frontmatter(markdown: str) -> tuple[list[str] | None, str, str]:
    newline = "\r\n" if "\r\n" in markdown[:200] else "\n"
    if not markdown.startswith("---" + newline):
        return None, markdown, newline

    lines = markdown.splitlines(keepends=True)
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = [line.rstrip("\r\n") for line in lines[1:index]]
            body = "".join(lines[index + 1 :])
            return frontmatter, body, newline

    raise ValueError("Frontmatter abierto pero sin delimitador de cierre.")


def strip_frontmatter(markdown: str) -> str:
    return split_frontmatter(markdown)[1]


def clean_title(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[*_]+|[*_]+$", "", value).strip()
    return re.sub(r"\s+", " ", value)


def first_h1(markdown: str) -> str | None:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", strip_frontmatter(markdown))
    return clean_title(match.group(1)) if match else None


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def is_index(path: Path) -> bool:
    return path.name.casefold().endswith("-index.md")


def is_alt_path(path: Path) -> bool:
    return any(part.endswith(" (Alt)") for part in path.parts)


def is_class(markdown: str) -> bool:
    body = strip_frontmatter(markdown)
    return bool(
        re.search(r"(?mi)^Atributos básicos de\s+", body)
        and re.search(r"(?mi)^##\s+Convertirse en\s+", body)
    )


def is_statblock(markdown: str) -> bool:
    return all(
        marker in markdown
        for marker in ("**CA:**", "**PG:**", "**Velocidad:**")
    )


def is_spell(markdown: str) -> bool:
    return all(
        marker in markdown
        for marker in (
            "**Tiempo de lanzamiento:**",
            "**Alcance:**",
            "**Componentes:**",
            "**Duración:**",
        )
    )


def is_magic_item(markdown: str) -> bool:
    body = strip_frontmatter(markdown)
    heading = re.search(r"(?m)^#\s+.+?\s*$", body)
    if not heading:
        return False

    first_nonblank = next(
        (
            line.strip()
            for line in body[heading.end() :].splitlines()
            if line.strip()
        ),
        "",
    )
    if not (
        first_nonblank.startswith("*")
        and first_nonblank.endswith("*")
    ):
        return False

    descriptor = first_nonblank.casefold()
    return any(
        word in descriptor
        for word in (
            "común",
            "infrecuente",
            "raro",
            "muy raro",
            "legendario",
            "artefacto",
        )
    )


def is_feat(markdown: str) -> bool:
    body = strip_frontmatter(markdown)
    heading = re.search(r"(?m)^#\s+.+?\s*$", body)
    if not heading:
        return False

    first_nonblank = next(
        (
            line.strip().strip("*_").strip()
            for line in body[heading.end() :].splitlines()
            if line.strip()
        ),
        "",
    )
    return bool(re.match(r"(?i)^Dote(?:\s|$)", first_nonblank))


ENTITY_RULES = (
    ("Clases", "clase", is_class),
    ("Animales", "animal", is_statblock),
    ("Conjuros", "conjuro", is_spell),
    ("Dotes", "dote", is_feat),
    ("MonstruosDeLaAALaZ", "monstruo", is_statblock),
    ("ObjetosMagicos", "objeto_magico", is_magic_item),
)


def build_catalog(es_root: Path) -> dict[str, list[Concept]]:
    catalog: dict[str, list[Concept]] = defaultdict(list)

    for folder_name, kind, validator in ENTITY_RULES:
        folder = es_root / folder_name
        if not folder.is_dir():
            continue

        for path in sorted(folder.rglob("*.md")):
            relative = path.relative_to(es_root)
            if is_index(relative) or is_alt_path(relative):
                continue

            markdown = path.read_text(encoding="utf-8")
            if not validator(markdown):
                continue

            title = first_h1(markdown)
            if not title:
                continue

            catalog[normalized(title)].append(
                Concept(title=title, path=relative, kind=kind)
            )

    for concepts in catalog.values():
        concepts.sort(key=lambda item: (item.kind, item.path.as_posix()))

    return dict(catalog)


def compile_matcher(catalog: dict[str, list[Concept]]) -> re.Pattern[str]:
    titles = [concepts[0].title for concepts in catalog.values()]
    titles.sort(key=lambda value: (-len(value), value.casefold()))
    alternatives = [
        re.escape(title).replace(r"\ ", r"\s+")
        for title in titles
    ]

    if not alternatives:
        raise RuntimeError("El catálogo de entidades está vacío.")

    return re.compile(
        r"(?<!\w)(" + "|".join(alternatives) + r")(?!\w)",
        re.IGNORECASE,
    )


def searchable_body(markdown: str) -> str:
    body = strip_frontmatter(markdown)
    body = re.sub(r"!?\[\[.*?\]\]", " ", body)
    body = re.sub(r"(?m)^#{1,6}\s+.+?\s*$", " ", body)
    body = re.sub(r"\x60\x60\x60.*?\x60\x60\x60", " ", body, flags=re.S)
    return body


def iter_target_notes(es_root: Path):
    for path in sorted(es_root.rglob("*.md")):
        relative = path.relative_to(es_root)
        if is_alt_path(relative) or is_index(relative):
            continue
        if relative == Path("Espanol.md"):
            continue
        yield path


def detect_links(
    note_path: Path,
    markdown: str,
    es_root: Path,
    catalog: dict[str, list[Concept]],
    matcher: re.Pattern[str],
) -> list[str]:
    current = note_path.relative_to(es_root)
    links: list[str] = []
    seen: set[str] = set()

    for match in matcher.finditer(searchable_body(markdown)):
        key = normalized(match.group(1))

        for concept in catalog.get(key, []):
            if concept.path == current:
                continue

            wikilink = concept.wikilink
            if wikilink in seen:
                continue

            seen.add(wikilink)
            links.append(wikilink)

    return links


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def remove_auto_property(frontmatter: list[str]) -> list[str]:
    result: list[str] = []
    index = 0
    key = re.compile(rf"^{re.escape(AUTO_PROPERTY)}\s*:")

    while index < len(frontmatter):
        line = frontmatter[index]

        if key.match(line):
            index += 1
            while index < len(frontmatter):
                next_line = frontmatter[index]
                if next_line.startswith((" ", "\t")) or not next_line.strip():
                    index += 1
                    continue
                break
            continue

        result.append(line)
        index += 1

    return result


def update_frontmatter(markdown: str, links: list[str]) -> str:
    frontmatter, body, newline = split_frontmatter(markdown)
    had_frontmatter = frontmatter is not None
    frontmatter = [] if frontmatter is None else remove_auto_property(frontmatter)

    while frontmatter and not frontmatter[-1].strip():
        frontmatter.pop()

    if links:
        frontmatter.append(AUTO_PROPERTY + ":")
        frontmatter.extend(
            f"  - {yaml_quote(link)}"
            for link in links
        )

    if not frontmatter and not had_frontmatter:
        return markdown

    return (
        "---"
        + newline
        + newline.join(frontmatter)
        + newline
        + "---"
        + newline
        + body
    )


def main() -> int:
    options = parse_args()
    root = options.root.resolve()
    es_root = root / "ES"

    if not es_root.is_dir():
        raise SystemExit(f"No existe {es_root}")

    catalog = build_catalog(es_root)
    matcher = compile_matcher(catalog)

    scanned = 0
    changed = 0
    link_count = 0

    for path in iter_target_notes(es_root):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        links = detect_links(path, original, es_root, catalog, matcher)
        link_count += len(links)
        updated = update_frontmatter(original, links)

        if updated == original:
            continue

        changed += 1

        if options.verbose:
            print(f"{path.relative_to(root)}: {len(links)} enlaces")
            for link in links:
                print(f"  {link}")

        if not options.dry_run:
            path.write_text(updated, encoding="utf-8", newline="")

    duplicates = {
        key: concepts
        for key, concepts in catalog.items()
        if len(concepts) > 1
    }

    counts: dict[str, int] = defaultdict(int)
    for concepts in catalog.values():
        for concept in concepts:
            counts[concept.kind] += 1

    mode = "DRY-RUN" if options.dry_run else "ESCRITURA"
    kinds = " ".join(
        f"{kind}={count}"
        for kind, count in sorted(counts.items())
    )

    print(
        f"[{mode}] entidades={sum(counts.values())} "
        f"titulos={len(catalog)} duplicados={len(duplicates)} "
        f"notas={scanned} modificadas={changed} "
        f"wikilinks={link_count} {kinds}"
    )

    for concepts in sorted(
        duplicates.values(),
        key=lambda values: values[0].title.casefold(),
    ):
        print(
            f"DUPLICADO: {concepts[0].title} -> "
            + ", ".join(concept.path.as_posix() for concept in concepts)
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
