#!/usr/bin/env python3
"""Genera wikilinks automáticos deterministas en las bóvedas ES y EN.

Principios:
- solo enlaza a notas físicas que ya representan una entidad;
- nunca crea notas auxiliares;
- nunca modifica el cuerpo Markdown;
- excluye índices, carpetas (Alt) y notas contenedoras como destinos;
- resuelve primero la coincidencia textual más larga;
- conserva todos los destinos cuando dos entidades reales comparten nombre;
- protege los conjuros/spells de una sola palabra mediante contexto.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

AUTO_PROPERTY = "wikilinks_auto"
LANGUAGES = ("ES", "EN")


@dataclass(frozen=True)
class Concept:
    title: str
    path: Path
    kind: str

    @property
    def wikilink(self) -> str:
        target = self.path.with_suffix("").as_posix()
        return f"[[{target}|{self.title}]]"


ENTITY_RULES = {
    "ES": (
        ("Clases", "class"),
        ("Animales", "animal"),
        ("Conjuros", "spell"),
        ("Dotes", "feat"),
        ("MonstruosDeLaAALaZ", "monster"),
        ("ObjetosMagicos", "magic_item"),
    ),
    "EN": (
        ("Classes", "class"),
        ("Animals", "animal"),
        ("Spells", "spell"),
        ("Feats", "feat"),
        ("Monsters A-Z", "monster"),
        ("Magic Items/Magic Items A-Z", "magic_item"),
    ),
}

SPELL_MARKERS = {
    "ES": (
        "**Tiempo de lanzamiento:**",
        "**Alcance:**",
        "**Componentes:**",
        "**Duración:**",
    ),
    "EN": (
        "**Casting Time:**",
        "**Range:**",
        "**Components:**",
        "**Duration:**",
    ),
}

RARITY_WORDS = {
    "ES": ("común", "infrecuente", "raro", "muy raro", "legendario", "artefacto"),
    "EN": ("common", "uncommon", "rare", "very rare", "legendary", "artifact"),
}

SPELL_TABLE_TERMS = {
    "ES": ("conjuro", "truco"),
    "EN": ("spell", "cantrip"),
}

SPELL_PROSE_CONTEXT = {
    "ES": re.compile(
        r"(?i)\b(?:"
        r"conjuro|conjuros|"
        r"truco|trucos|"
        r"lanzar|lance|lances|lanzado|lanzada|lanzados|lanzadas|lanzando|"
        r"preparar|preparas|prepara|preparado|preparada|preparados|preparadas|"
        r"aprender|aprendes|aprende|aprendido|aprendida|aprendidos|aprendidas"
        r")\b"
    ),
    "EN": re.compile(
        r"(?i)\b(?:"
        r"spell|spells|"
        r"cantrip|cantrips|"
        r"cast|casts|casting|casted|"
        r"prepare|prepares|prepared|preparing|"
        r"learn|learns|learned|learning"
        r")\b"
    ),
}

HEADING_RE = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera relaciones Obsidian deterministas en ES y/o EN."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Raíz del repositorio.",
    )
    parser.add_argument(
        "--lang",
        choices=("ES", "EN", "all"),
        default="all",
        help="Idioma a procesar. Por defecto procesa ES y EN.",
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


def first_heading(markdown: str) -> str | None:
    match = HEADING_RE.search(strip_frontmatter(markdown))
    return clean_title(match.group(1)) if match else None


def first_heading_match(markdown: str) -> tuple[re.Match[str] | None, str]:
    body = strip_frontmatter(markdown)
    return HEADING_RE.search(body), body


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def heading_titles(markdown: str) -> list[str]:
    return [
        clean_title(match.group(1))
        for match in re.finditer(
            r"(?m)^#{2,6}\s+(.+?)\s*$",
            strip_frontmatter(markdown),
        )
    ]


def blocker_variants(heading: str, language: str) -> set[str]:
    variants = {heading.strip()}
    level_word = "Nivel" if language == "ES" else "Level"

    without_level = re.sub(
        rf"(?i)^{level_word}\s+\d+\s*:\s*",
        "",
        heading,
    ).strip()
    if without_level:
        variants.add(without_level)

    for value in tuple(variants):
        without_suffix = re.sub(
            r"\s*\([^()]+\)\s*$",
            "",
            value,
        ).strip()
        if without_suffix:
            variants.add(without_suffix)

    return variants


def is_index(path: Path) -> bool:
    return path.name.casefold().endswith("-index.md")


def is_alt_path(path: Path) -> bool:
    return any(part.endswith(" (Alt)") for part in path.parts)


def is_class(markdown: str, language: str) -> bool:
    body = strip_frontmatter(markdown)

    if language == "ES":
        return bool(
            re.search(r"(?mi)^Atributos básicos de\s+", body)
            and re.search(r"(?mi)^##\s+Convertirse en\s+", body)
        )

    return bool(
        re.search(r"(?mi)^##\s+Core\s+.+?\s+Traits\s*$", body)
        and re.search(r"(?mi)^##\s+Becoming a\s+", body)
    )


def is_statblock(markdown: str, language: str) -> bool:
    if language == "ES":
        return all(
            marker in markdown
            for marker in ("**CA:**", "**PG:**", "**Velocidad:**")
        )

    return all(
        re.search(pattern, markdown, flags=re.MULTILINE)
        for pattern in (
            r"^\*\*AC\b",
            r"^\*\*HP\b",
            r"^\*\*Speed\b",
        )
    )


def is_spell(markdown: str, language: str) -> bool:
    return all(marker in markdown for marker in SPELL_MARKERS[language])


def is_magic_item(markdown: str, language: str) -> bool:
    heading, body = first_heading_match(markdown)
    if not heading:
        return False

    following = [
        line.strip().strip("*_").strip()
        for line in body[heading.end() :].splitlines()
        if line.strip()
    ][:4]
    descriptor = " ".join(following).casefold()

    return any(
        re.search(rf"(?<!\w){re.escape(word)}(?!\w)", descriptor)
        for word in RARITY_WORDS[language]
    )


def is_feat(markdown: str, language: str) -> bool:
    heading, body = first_heading_match(markdown)
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

    if language == "ES":
        return bool(re.match(r"(?i)^Dote(?:\s|$)", first_nonblank))

    return bool(re.search(r"(?i)\bFeat\s*$", first_nonblank))


def is_entity(markdown: str, language: str, kind: str) -> bool:
    if kind == "class":
        return is_class(markdown, language)
    if kind in {"animal", "monster"}:
        return is_statblock(markdown, language)
    if kind == "spell":
        return is_spell(markdown, language)
    if kind == "feat":
        return is_feat(markdown, language)
    if kind == "magic_item":
        return is_magic_item(markdown, language)
    raise ValueError(f"Tipo de entidad desconocido: {kind}")


def build_catalog(
    language_root: Path,
    language: str,
) -> dict[str, list[Concept]]:
    catalog: dict[str, list[Concept]] = defaultdict(list)

    for folder_name, kind in ENTITY_RULES[language]:
        folder = language_root / folder_name
        if not folder.is_dir():
            continue

        for path in sorted(folder.rglob("*.md")):
            relative = path.relative_to(language_root)
            if is_index(relative) or is_alt_path(relative):
                continue

            markdown = path.read_text(encoding="utf-8")
            if not is_entity(markdown, language, kind):
                continue

            title = first_heading(markdown)
            if not title:
                continue

            catalog[normalized(title)].append(
                Concept(title=title, path=relative, kind=kind)
            )

    for concepts in catalog.values():
        concepts.sort(key=lambda item: (item.kind, item.path.as_posix()))

    return dict(catalog)


def build_blockers(
    language_root: Path,
    catalog: dict[str, list[Concept]],
    language: str,
) -> dict[str, str]:
    """Frases estructurales que consumen texto pero nunca crean enlaces."""
    blockers: dict[str, str] = {}

    entity_titles = [
        concepts[0].title
        for concepts in catalog.values()
    ]
    entity_titles.sort(key=lambda value: (-len(value), value.casefold()))

    entity_matcher = re.compile(
        r"(?<!\w)("
        + "|".join(
            re.escape(title).replace(r"\ ", r"\s+")
            for title in entity_titles
        )
        + r")(?!\w)",
        re.IGNORECASE,
    )

    for path in sorted(language_root.rglob("*.md")):
        relative = path.relative_to(language_root)
        if is_alt_path(relative) or is_index(relative):
            continue

        markdown = path.read_text(encoding="utf-8")

        for heading in heading_titles(markdown):
            for candidate in blocker_variants(heading, language):
                candidate_key = normalized(candidate)

                if candidate_key in catalog:
                    continue

                if entity_matcher.search(candidate):
                    blockers[candidate_key] = candidate

    return blockers


def compile_matcher(
    catalog: dict[str, list[Concept]],
    blockers: dict[str, str],
) -> re.Pattern[str]:
    phrases = [
        concepts[0].title
        for concepts in catalog.values()
    ] + list(blockers.values())

    phrases.sort(key=lambda value: (-len(value), value.casefold()))

    alternatives = [
        re.escape(phrase).replace(r"\ ", r"\s+")
        for phrase in phrases
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


def iter_target_notes(language_root: Path):
    for path in sorted(language_root.rglob("*.md")):
        relative = path.relative_to(language_root)

        if is_alt_path(relative) or is_index(relative):
            continue

        yield path


def is_single_word_spell(concept: Concept) -> bool:
    return concept.kind == "spell" and not re.search(r"\s", concept.title)


def split_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [
        cell.strip()
        for cell in stripped.strip("|").split("|")
    ]


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))
        for cell in cells
    )


def table_headers_by_line(lines: list[str]) -> dict[int, list[str]]:
    headers_by_line: dict[int, list[str]] = {}
    current_headers: list[str] | None = None
    in_table = False

    for index, line in enumerate(lines):
        cells = split_table_cells(line)

        if not cells:
            current_headers = None
            in_table = False
            continue

        if not in_table:
            current_headers = cells
            in_table = True
            continue

        if is_table_separator(cells):
            continue

        if current_headers is not None:
            headers_by_line[index] = current_headers

    return headers_by_line


def table_cell_index(line: str, position: int) -> int | None:
    if not line.lstrip().startswith("|"):
        return None

    prefix = line[:position]
    index = prefix.count("|") - 1
    return index if index >= 0 else None


def single_word_spell_has_context(
    line: str,
    line_index: int,
    match: re.Match[str],
    headers_by_line: dict[int, list[str]],
    language: str,
) -> bool:
    headers = headers_by_line.get(line_index)

    if headers is not None:
        column = table_cell_index(line, match.start())
        if column is None or column >= len(headers):
            return False

        header = normalized(headers[column])
        return any(term in header for term in SPELL_TABLE_TERMS[language])

    start = max(0, match.start() - 120)
    end = min(len(line), match.end() + 120)
    context = line[start:end]
    return bool(SPELL_PROSE_CONTEXT[language].search(context))


def detect_links(
    note_path: Path,
    markdown: str,
    language_root: Path,
    catalog: dict[str, list[Concept]],
    blockers: dict[str, str],
    matcher: re.Pattern[str],
    language: str,
) -> list[str]:
    current = note_path.relative_to(language_root)
    links: list[str] = []
    seen: set[str] = set()

    text = searchable_body(markdown)
    lines = text.splitlines()
    headers_by_line = table_headers_by_line(lines)

    for line_index, line in enumerate(lines):
        for match in matcher.finditer(line):
            key = normalized(match.group(1))

            if key in blockers:
                continue

            for concept in catalog.get(key, []):
                if concept.path == current:
                    continue

                if (
                    is_single_word_spell(concept)
                    and not single_word_spell_has_context(
                        line,
                        line_index,
                        match,
                        headers_by_line,
                        language,
                    )
                ):
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


def process_language(
    root: Path,
    language: str,
    dry_run: bool,
    verbose: bool,
) -> dict[str, int]:
    language_root = root / language

    if not language_root.is_dir():
        raise SystemExit(f"No existe {language_root}")

    catalog = build_catalog(language_root, language)
    blockers = build_blockers(language_root, catalog, language)
    matcher = compile_matcher(catalog, blockers)

    scanned = 0
    changed = 0
    link_count = 0

    for path in iter_target_notes(language_root):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        links = detect_links(
            path,
            original,
            language_root,
            catalog,
            blockers,
            matcher,
            language,
        )
        link_count += len(links)
        updated = update_frontmatter(original, links)

        if updated == original:
            continue

        changed += 1

        if verbose:
            print(f"{path.relative_to(root)}: {len(links)} enlaces")
            for link in links:
                print(f"  {link}")

        if not dry_run:
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

    mode = "DRY-RUN" if dry_run else "ESCRITURA"
    kinds = " ".join(
        f"{kind}={count}"
        for kind, count in sorted(counts.items())
    )

    print(
        f"[{mode}][{language}] entidades={sum(counts.values())} "
        f"titulos={len(catalog)} bloqueadores={len(blockers)} "
        f"duplicados={len(duplicates)} "
        f"notas={scanned} modificadas={changed} "
        f"wikilinks={link_count} {kinds}"
    )

    for concepts in sorted(
        duplicates.values(),
        key=lambda values: values[0].title.casefold(),
    ):
        print(
            f"DUPLICADO[{language}]: {concepts[0].title} -> "
            + ", ".join(concept.path.as_posix() for concept in concepts)
        )

    return {
        "entities": sum(counts.values()),
        "titles": len(catalog),
        "blockers": len(blockers),
        "duplicates": len(duplicates),
        "notes": scanned,
        "changed": changed,
        "wikilinks": link_count,
    }


def main() -> int:
    options = parse_args()
    root = options.root.resolve()

    languages = LANGUAGES if options.lang == "all" else (options.lang,)

    for language in languages:
        process_language(
            root=root,
            language=language,
            dry_run=options.dry_run,
            verbose=options.verbose,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
