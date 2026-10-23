#!/usr/bin/env python3
"""Genera la capa determinista de relaciones Obsidian para ES (v2)."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

AUTO_PROPERTY = "wikilinks_auto"
GENERATED_ROOT = "_Entidades"

CLASS_FILES = (
    "Barbaro.md", "Bardo.md", "Brujo.md", "Clerigo.md", "Druida.md",
    "Explorador.md", "Guerrero.md", "Hechicero.md", "Mago.md", "Monje.md",
    "Paladin.md", "Picaro.md",
)
FEAT_FILES = (
    "DotesDeDonEpico.md", "DotesDeEstiloDeCombate.md",
    "DotesDeOrigen.md", "DotesGenerales.md",
)
EQUIPMENT_HEADING_FILES = ("EquipoDeAventureros.md", "Herramientas.md")
EQUIPMENT_TABLE_FILES = ("Armaduras.md", "Armas.md", "MonturasYVehiculos.md")
GENERIC_EQUIPMENT_HEADINGS = {
    "competencia con herramientas",
    "herramientas de artesano",
    "otras herramientas",
}
TABLE_HEADERS = {"armadura", "nombre", "silla", "animal", "elemento", "vehículo"}


@dataclass(frozen=True)
class Concept:
    title: str
    path: Path
    kind: str

    @property
    def wikilink(self) -> str:
        return f"[[{self.path.with_suffix('').as_posix()}|{self.title}]]"


@dataclass
class EmbeddedEntity:
    title: str
    kind: str
    sources: list[tuple[Path, str | None]] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def split_frontmatter(text: str) -> tuple[list[str] | None, str, str]:
    newline = "\r\n" if "\r\n" in text[:200] else "\n"
    if not text.startswith("---" + newline):
        return None, text, newline
    lines = text.splitlines(keepends=True)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return [x.rstrip("\r\n") for x in lines[1:i]], "".join(lines[i + 1:]), newline
    raise ValueError("Frontmatter sin cierre")


def body(text: str) -> str:
    return split_frontmatter(text)[1]


def clean_title(value: str) -> str:
    value = re.sub(r"^[*_]+|[*_]+$", "", value.strip()).strip()
    return re.sub(r"\s+", " ", value)


def h1(text: str) -> str | None:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", body(text))
    return clean_title(match.group(1)) if match else None


def h2s(text: str) -> list[str]:
    return [clean_title(m.group(1)) for m in re.finditer(r"(?m)^##\s+(.+?)\s*$", body(text))]


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    parts = re.findall(r"[A-Za-z0-9]+", value)
    return "".join(p[:1].upper() + p[1:] for p in parts) or "Entidad"


def is_index(path: Path) -> bool:
    return path.name.casefold().endswith("-index.md")


def is_alt(path: Path) -> bool:
    return any(part.endswith(" (Alt)") for part in path.parts)


def is_spell(text: str) -> bool:
    return all(x in text for x in (
        "**Tiempo de lanzamiento:**", "**Alcance:**",
        "**Componentes:**", "**Duración:**",
    ))


def is_statblock(text: str) -> bool:
    return all(x in text for x in ("**CA:**", "**PG:**", "**Velocidad:**"))


def is_magic_item(text: str) -> bool:
    content = body(text)
    title = re.search(r"(?m)^#\s+.+?\s*$", content)
    if not title:
        return False
    first = next((line.strip() for line in content[title.end():].splitlines() if line.strip()), "")
    if not (first.startswith("*") and first.endswith("*")):
        return False
    first = first.casefold()
    return any(word in first for word in (
        "común", "infrecuente", "raro", "muy raro", "legendario", "artefacto"
    ))


def file_concepts(es: Path) -> list[Concept]:
    result: list[Concept] = []

    def add(path: Path, kind: str, predicate=None) -> None:
        text = path.read_text(encoding="utf-8")
        if predicate and not predicate(text):
            return
        title = h1(text)
        if title:
            result.append(Concept(title, path.relative_to(es), kind))

    for name in CLASS_FILES:
        add(es / "Clases" / name, "clase")

    for folder, kind in (("Animales", "animal"), ("MonstruosDeLaAALaZ", "monstruo")):
        for path in sorted((es / folder).glob("*.md")):
            if not is_index(path):
                add(path, kind, is_statblock)

    for path in sorted((es / "Conjuros").glob("*.md")):
        if not is_index(path):
            add(path, "conjuro", is_spell)

    for path in sorted((es / "ObjetosMagicos").glob("*.md")):
        if not is_index(path):
            add(path, "objeto_magico", is_magic_item)

    return result


def add_embedded(
    entities: dict[tuple[str, str], EmbeddedEntity],
    title: str,
    kind: str,
    source: Path,
    section: str | None,
) -> None:
    title = clean_title(title)
    if not title:
        return
    key = (kind, norm(title))
    entity = entities.setdefault(key, EmbeddedEntity(title, kind))
    pair = (source, section)
    if pair not in entity.sources:
        entity.sources.append(pair)


def strip_price(title: str) -> str:
    return re.sub(
        r"\s*\((?:[^()]*(?:po|pp|pc|pe|ppt|variable)[^()]*)\)\s*$",
        "", title, flags=re.IGNORECASE,
    ).strip()


def embedded_entities(es: Path) -> list[EmbeddedEntity]:
    entities: dict[tuple[str, str], EmbeddedEntity] = {}

    for name in FEAT_FILES:
        path = es / "Dotes" / name
        for title in h2s(path.read_text(encoding="utf-8")):
            add_embedded(entities, title, "dote", path.relative_to(es), title)

    for name in EQUIPMENT_HEADING_FILES:
        path = es / "Equipo" / name
        for raw in h2s(path.read_text(encoding="utf-8")):
            title = strip_price(raw)
            if norm(title) not in GENERIC_EQUIPMENT_HEADINGS:
                add_embedded(entities, title, "equipo", path.relative_to(es), raw)

    headers = {x.casefold() for x in TABLE_HEADERS}
    for name in EQUIPMENT_TABLE_FILES:
        path = es / "Equipo" / name
        section = None
        table_header = None
        for line in body(path.read_text(encoding="utf-8")).splitlines():
            heading = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
            if heading:
                section = clean_title(heading.group(1))
                table_header = None
                continue
            if not line.startswith("|"):
                continue
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if not cells:
                continue
            first = clean_title(cells[0])
            if not first or first.replace(":", "").replace("-", "").strip() == "":
                continue
            if norm(first) in headers:
                table_header = norm(first)
                continue

            # Las filas de la tabla de animales ya tienen identidad propia en
            # ES/Animales. No generamos un segundo nodo de Equipo para ellas.
            if name == "MonturasYVehiculos.md" and table_header == "animal":
                continue

            title = first
            if name == "MonturasYVehiculos.md" and table_header == "silla":
                title = "Silla " + first.casefold()
            add_embedded(entities, title, "equipo", path.relative_to(es), section)

    return list(entities.values())


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def entity_path(entity: EmbeddedEntity) -> Path:
    folder = "Dotes" if entity.kind == "dote" else "Equipo"
    return Path(GENERATED_ROOT) / folder / (slug(entity.title) + ".md")


def render_entity(entity: EmbeddedEntity) -> str:
    """Nodo de identidad sin enlaces a la nota contenedora.

    La procedencia se guarda como texto YAML deliberadamente. Si usáramos un
    wikilink en sources, Obsidian volvería a introducir el capítulo contenedor
    (por ejemplo Equipo/Armas) en el grafo.
    """
    tag = "entidad_dote" if entity.kind == "dote" else "entidad_equipo"
    lines = [
        "---",
        f"aliases: [{yaml_quote(entity.title)}]",
        f"tags: [srd, espanol, generado, {tag}]",
        f"entity_type: {entity.kind}",
        "generated: true",
        "generated_by: scripts/generar_wikilinks_es.py",
        "sources:",
    ]
    for note, section in entity.sources:
        lines.append("  - note: " + yaml_quote(note.as_posix()))
        if section:
            lines.append("    section: " + yaml_quote(section))
    lines.append("---")
    return "\n".join(lines) + "\n"


def generated_concepts(es: Path, entities: list[EmbeddedEntity], dry_run: bool) -> list[Concept]:
    by_path: dict[Path, EmbeddedEntity] = {}
    for entity in entities:
        path = entity_path(entity)
        previous = by_path.get(path)
        if previous and norm(previous.title) != norm(entity.title):
            raise RuntimeError(f"Colisión: {previous.title} / {entity.title} -> {path}")
        by_path[path] = entity

    concepts = [Concept(entity.title, path, entity.kind) for path, entity in by_path.items()]

    if not dry_run:
        root = es / GENERATED_ROOT
        if root.exists():
            shutil.rmtree(root)
        for path, entity in by_path.items():
            target = es / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_entity(entity), encoding="utf-8", newline="")

    return concepts


def catalog(concepts: list[Concept]) -> dict[str, list[Concept]]:
    result: dict[str, list[Concept]] = defaultdict(list)
    for concept in concepts:
        result[norm(concept.title)].append(concept)
    for values in result.values():
        values.sort(key=lambda x: (x.kind, x.path.as_posix()))
    return dict(result)


def build_matcher(cat: dict[str, list[Concept]]) -> re.Pattern[str]:
    titles = sorted((v[0].title for v in cat.values()), key=lambda x: (-len(x), x.casefold()))
    parts = [re.escape(x).replace(r"\ ", r"\s+") for x in titles]
    return re.compile(r"(?<!\w)(" + "|".join(parts) + r")(?!\w)", re.IGNORECASE)


def searchable(text: str) -> str:
    content = body(text)
    content = re.sub(r"!?\[\[.*?\]\]", " ", content)

    # Los encabezados describen la estructura de la nota actual. No son
    # evidencia de una relación externa: "Defensa sin armadura" no debe
    # convertir "Defensa" en una referencia automática a la dote Defensa.
    content = re.sub(r"(?m)^#{1,6}\s+.+?\s*$", " ", content)
    return content


def target_notes(es: Path):
    for path in sorted(es.rglob("*.md")):
        rel = path.relative_to(es)
        if rel.parts and rel.parts[0] == GENERATED_ROOT:
            continue
        if is_alt(rel) or is_index(rel) or rel == Path("Espanol.md"):
            continue
        yield path


def detect(path: Path, text: str, es: Path, cat: dict[str, list[Concept]], rx: re.Pattern[str]) -> list[str]:
    current = path.relative_to(es)
    result, seen = [], set()
    for match in rx.finditer(searchable(text)):
        for concept in cat.get(norm(match.group(1)), []):
            if concept.path == current:
                continue
            link = concept.wikilink
            if link not in seen:
                seen.add(link)
                result.append(link)
    return result


def remove_auto(lines: list[str]) -> list[str]:
    result, i = [], 0
    key = re.compile(rf"^{re.escape(AUTO_PROPERTY)}\s*:")
    while i < len(lines):
        if key.match(lines[i]):
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                i += 1
            continue
        result.append(lines[i])
        i += 1
    return result


def update_frontmatter(text: str, links: list[str]) -> str:
    fm, content, newline = split_frontmatter(text)
    had = fm is not None
    fm = [] if fm is None else remove_auto(fm)
    while fm and not fm[-1].strip():
        fm.pop()
    if links:
        fm.append(AUTO_PROPERTY + ":")
        fm.extend("  - " + yaml_quote(link) for link in links)
    if not fm and not had:
        return text
    return "---" + newline + newline.join(fm) + newline + "---" + newline + content


def main() -> int:
    opt = parse_args()
    root = opt.root.resolve()
    es = root / "ES"
    files = file_concepts(es)
    generated = generated_concepts(es, embedded_entities(es), opt.dry_run)
    cat = catalog(files + generated)
    rx = build_matcher(cat)

    scanned = changed = links_count = 0
    for path in target_notes(es):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        links = detect(path, original, es, cat, rx)
        updated = update_frontmatter(original, links)
        if updated != original:
            changed += 1
            links_count += len(links)
            if opt.verbose:
                print(path.relative_to(root), links)
            if not opt.dry_run:
                path.write_text(updated, encoding="utf-8", newline="")

    duplicates = {k: v for k, v in cat.items() if len(v) > 1}
    mode = "DRY-RUN" if opt.dry_run else "ESCRITURA"
    print(
        f"[{mode}] entidades_con_nota={len(files)} entidades_generadas={len(generated)} "
        f"titulos={len(cat)} duplicados={len(duplicates)} notas={scanned} "
        f"modificadas={changed} wikilinks={links_count}"
    )
    for values in sorted(duplicates.values(), key=lambda x: x[0].title.casefold()):
        print("DUPLICADO:", values[0].title, "->", ", ".join(x.path.as_posix() for x in values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
