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


def heading_titles(markdown: str) -> list[str]:
    return [
        clean_title(match.group(1))
        for match in re.finditer(
            r"(?m)^#{2,6}\s+(.+?)\s*$",
            strip_frontmatter(markdown),
        )
    ]


def blocker_variants(heading: str) -> set[str]:
    variants = {heading.strip()}

    # Los encabezados de rasgos suelen llevar un prefijo mecánico de nivel.
    # Queremos que "Nivel 7: Salto instintivo" también bloquee la frase
    # "Salto instintivo" cuando aparezca en una tabla o en prosa.
    without_level = re.sub(
        r"(?i)^Nivel\s+\d+\s*:\s*",
        "",
        heading,
    ).strip()
    if without_level:
        variants.add(without_level)

    # Equipo usa metadatos de presentación en el propio encabezado, por
    # ejemplo "Paquete de explorador (10 po)". La frase que aparece en otras
    # notas suele omitir ese precio.
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


def build_blockers(
    es_root: Path,
    catalog: dict[str, list[Concept]],
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

    for path in sorted(es_root.rglob("*.md")):
        relative = path.relative_to(es_root)
        if is_alt_path(relative) or is_index(relative):
            continue

        markdown = path.read_text(encoding="utf-8")

        for heading in heading_titles(markdown):
            for candidate in blocker_variants(heading):
                candidate_key = normalized(candidate)

                # Un bloqueador nunca sustituye una entidad cuyo título es
                # exactamente el mismo.
                if candidate_key in catalog:
                    continue

                # Un único matcher comprueba si la frase contiene alguna
                # entidad; evita recorrer todo el catálogo por encabezado.
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


def iter_target_notes(es_root: Path):
    for path in sorted(es_root.rglob("*.md")):
        relative = path.relative_to(es_root)
        if is_alt_path(relative) or is_index(relative):
            continue
        if relative == Path("Espanol.md"):
            continue
        yield path


def is_single_word_spell(concept: Concept) -> bool:
    return concept.kind == "conjuro" and not re.search(r"\s", concept.title)


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
    """Asocia cada fila de datos Markdown con las cabeceras de su tabla."""
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
    """Devuelve la columna Markdown que contiene una posición de la línea."""
    if not line.lstrip().startswith("|"):
        return None

    # En tablas del repositorio las filas empiezan por "|". Cada separador
    # anterior al match incrementa el índice de columna.
    prefix = line[:position]
    index = prefix.count("|") - 1
    return index if index >= 0 else None


SPELL_PROSE_CONTEXT = re.compile(
    r"(?i)\b(?:"
    r"conjuro|conjuros|"
    r"truco|trucos|"
    r"lanzar|lance|lances|lanzado|lanzada|lanzados|lanzadas|lanzando|"
    r"preparar|preparas|prepara|preparado|preparada|preparados|preparadas|"
    r"aprender|aprendes|aprende|aprendido|aprendida|aprendidos|aprendidas"
    r")\b"
)


def single_word_spell_has_context(
    line: str,
    line_index: int,
    match: re.Match[str],
    headers_by_line: dict[int, list[str]],
) -> bool:
    """Exige evidencia explícita para conjuros cuyo nombre es una sola palabra."""
    headers = headers_by_line.get(line_index)

    if headers is not None:
        column = table_cell_index(line, match.start())
        if column is None or column >= len(headers):
            return False

        header = normalized(headers[column])
        return "conjuro" in header or "truco" in header

    # En prosa se usa una ventana local para evitar que la palabra "conjuro"
    # en otro extremo de un párrafo largo legitime una coincidencia accidental.
    start = max(0, match.start() - 120)
    end = min(len(line), match.end() + 120)
    context = line[start:end]
    return bool(SPELL_PROSE_CONTEXT.search(context))


def detect_links(
    note_path: Path,
    markdown: str,
    es_root: Path,
    catalog: dict[str, list[Concept]],
    blockers: dict[str, str],
    matcher: re.Pattern[str],
) -> list[str]:
    current = note_path.relative_to(es_root)
    links: list[str] = []
    seen: set[str] = set()

    text = searchable_body(markdown)
    lines = text.splitlines()
    headers_by_line = table_headers_by_line(lines)

    for line_index, line in enumerate(lines):
        for match in matcher.finditer(line):
            key = normalized(match.group(1))

            # Los bloqueadores participan en el mismo longest-match que las
            # entidades, pero consumen el intervalo sin producir ninguna arista.
            if key in blockers:
                continue

            for concept in catalog.get(key, []):
                if concept.path == current:
                    continue

                # Los conjuros de una sola palabra son especialmente ambiguos
                # con vocabulario ordinario ("luz", "resistencia", "dormir",
                # "escudo"...). Solo se enlazan con evidencia estructural o
                # léxica de que el texto está hablando de un conjuro.
                if (
                    is_single_word_spell(concept)
                    and not single_word_spell_has_context(
                        line,
                        line_index,
                        match,
                        headers_by_line,
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


def main() -> int:
    options = parse_args()
    root = options.root.resolve()
    es_root = root / "ES"

    if not es_root.is_dir():
        raise SystemExit(f"No existe {es_root}")

    catalog = build_catalog(es_root)
    blockers = build_blockers(es_root, catalog)
    matcher = compile_matcher(catalog, blockers)

    scanned = 0
    changed = 0
    link_count = 0

    for path in iter_target_notes(es_root):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        links = detect_links(
            path,
            original,
            es_root,
            catalog,
            blockers,
            matcher,
        )
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
            f"DUPLICADO: {concepts[0].title} -> "
            + ", ".join(concept.path.as_posix() for concept in concepts)
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
