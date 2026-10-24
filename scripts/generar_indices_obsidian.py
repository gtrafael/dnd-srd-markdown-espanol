#!/usr/bin/env python3
"""Genera índices de navegación para main.

Principios:
- cada carpeta canónica tiene exactamente un 00-*-Index.md;
- los índices contienen solo enlaces, nunca contadores;
- los grandes catálogos usan una vista (Alt) alfabética para humanos;
- todos estos índices son derivados y no forman parte de corpus.
"""

from __future__ import annotations

import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RANGOS = [
    ("A-C", "A", "C"),
    ("D-F", "D", "F"),
    ("G-I", "G", "I"),
    ("J-L", "J", "L"),
    ("M-O", "M", "O"),
    ("P-R", "P", "R"),
    ("S-U", "S", "U"),
    ("V-Z", "V", "Z"),
]


@dataclass(frozen=True)
class Catalogo:
    origen: str
    destino: str
    nombre: str


CATALOGOS = [
    Catalogo("ES/Animales", "ES/Animales (Alt)", "Animales"),
    Catalogo("EN/Animals", "EN/Animals (Alt)", "Animals"),
    Catalogo(
        "ES/Conjuros/DescripcionesDeConjuros",
        "ES/Conjuros (Alt)",
        "Conjuros",
    ),
    Catalogo(
        "EN/Spells/Spell Descriptions",
        "EN/Spells (Alt)",
        "Spells",
    ),
    Catalogo(
        "ES/MonstruosDeLaAALaZ",
        "ES/MonstruosDeLaAALaZ (Alt)",
        "Monstruos A-Z",
    ),
    Catalogo(
        "EN/Monsters A-Z",
        "EN/Monsters A-Z (Alt)",
        "Monsters A-Z",
    ),
    Catalogo(
        "ES/ObjetosMagicos/ObjetosMagicosDeLaAALaZ",
        "ES/ObjetosMagicos (Alt)",
        "Objetos mágicos",
    ),
    Catalogo(
        "EN/Magic Items/Magic Items A-Z",
        "EN/Magic Items (Alt)",
        "Magic Items",
    ),
]

ALT_POR_ORIGEN = {c.origen: c for c in CATALOGOS}

ROOT_LABELS = {
    "ES": {
        "ComoJugar": "Cómo jugar",
        "CreacionDePersonajes": "Creación de personajes",
        "Clases": "Clases",
        "OrigenesDePersonaje": "Orígenes de personaje",
        "Dotes": "Dotes",
        "Equipo": "Equipo",
        "Conjuros": "Conjuros",
        "GlosarioDeReglas": "Glosario de reglas",
        "HerramientasDelJuego": "Herramientas del juego",
        "ObjetosMagicos": "Objetos mágicos",
        "Monstruos": "Monstruos",
        "MonstruosDeLaAALaZ": "Monstruos de la A a la Z",
        "Animales": "Animales",
    },
    "EN": {
        "Playing the Game": "Playing the Game",
        "Character Creation": "Character Creation",
        "Classes": "Classes",
        "Character Origins": "Character Origins",
        "Feats": "Feats",
        "Equipment": "Equipment",
        "Spells": "Spells",
        "Rules Glossary": "Rules Glossary",
        "Gameplay Toolbox": "Gameplay Toolbox",
        "Magic Items": "Magic Items",
        "Monsters": "Monsters",
        "Monsters A-Z": "Monsters A-Z",
        "Animals": "Animals",
    },
}


def titulo(path: Path) -> str:
    texto = path.read_text(encoding="utf-8")
    for linea in texto.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", linea)
        if m:
            return re.sub(r"[*_]", "", m.group(1)).strip()
    return path.stem


def inicial(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto)
    limpio = "".join(c for c in limpio if not unicodedata.combining(c)).upper()
    m = re.search(r"[A-Z]", limpio)
    return m.group(0) if m else "Z"


def rango_de(texto: str) -> str:
    letra = inicial(texto)
    for nombre, inicio, fin in RANGOS:
        if inicio <= letra <= fin:
            return nombre
    return "V-Z"


def index_name(folder: Path) -> str:
    return f"00-{folder.name}-Index.md"


def rel_wikilink(lang_root: Path, target: Path, label: str) -> str:
    rel = target.relative_to(lang_root).with_suffix("").as_posix()
    return f"[[{rel}|{label}]]"


def limpiar_indices_generados() -> None:
    for lang in ("ES", "EN"):
        root = ROOT / lang
        for p in root.rglob("*.md"):
            if any("(Alt)" in parte for parte in p.parts):
                continue
            if p.name.startswith("00-") and p.name.endswith("-Index.md"):
                p.unlink()
            elif p.name.endswith("-Index.md"):
                p.unlink()

        for nombre in ("Espanol.md", "English.md"):
            p = root / nombre
            if p.exists():
                p.unlink()


def generar_alt(catalogo: Catalogo) -> None:
    origen = ROOT / catalogo.origen
    destino = ROOT / catalogo.destino
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)

    lang_root = ROOT / catalogo.origen.split("/", 1)[0]
    grupos: dict[str, list[tuple[str, Path]]] = {r[0]: [] for r in RANGOS}

    for path in sorted(origen.glob("*.md")):
        if path.name.endswith("-Index.md"):
            continue
        nombre = titulo(path)
        grupos[rango_de(nombre)].append((nombre, path))

    raiz = [f"# {catalogo.nombre} — índice alfabético", ""]

    for rango, _, _ in RANGOS:
        archivo = f"{catalogo.nombre} {rango}"
        entradas = sorted(grupos[rango], key=lambda x: x[0].casefold())
        cuerpo = [f"# {archivo}", ""]
        cuerpo += [f"- {rel_wikilink(lang_root, path, nombre)}" for nombre, path in entradas]
        cuerpo.append("")
        (destino / f"{archivo}.md").write_text("\n".join(cuerpo), encoding="utf-8")
        rel = (destino / f"{archivo}.md").relative_to(lang_root).with_suffix("").as_posix()
        raiz.append(f"- [[{rel}|{rango}]]")

    raiz.append("")
    (destino / f"00-{catalogo.nombre} (Alt)-Index.md").write_text(
        "\n".join(raiz), encoding="utf-8"
    )


def generar_indice_carpeta(lang: str, folder: Path) -> None:
    lang_root = ROOT / lang
    rel_folder = folder.relative_to(ROOT).as_posix()

    if rel_folder in ALT_POR_ORIGEN:
        alt = ROOT / ALT_POR_ORIGEN[rel_folder].destino
        alt_index = alt / f"00-{ALT_POR_ORIGEN[rel_folder].nombre} (Alt)-Index.md"
        contenido = [
            f"# {folder.name}",
            "",
            f"- {rel_wikilink(lang_root, alt_index, 'Índice alfabético' if lang == 'ES' else 'Alphabetical index')}",
            "",
        ]
    else:
        notas = [
            p for p in folder.glob("*.md")
            if not p.name.endswith("-Index.md") and not p.name.startswith("00-")
        ]
        subdirs = [
            p for p in folder.iterdir()
            if p.is_dir() and "(Alt)" not in p.name
        ]
        enlaces: list[tuple[str, str]] = []
        for p in notas:
            enlaces.append((titulo(p), rel_wikilink(lang_root, p, titulo(p))))
        for d in subdirs:
            idx = d / index_name(d)
            label = d.name
            enlaces.append((label, rel_wikilink(lang_root, idx, label)))
        enlaces.sort(key=lambda x: x[0].casefold())
        contenido = [f"# {folder.name}", ""] + [f"- {link}" for _, link in enlaces] + [""]

    (folder / index_name(folder)).write_text("\n".join(contenido), encoding="utf-8")


def generar_indices_normales() -> None:
    for lang in ("ES", "EN"):
        lang_root = ROOT / lang
        dirs = sorted(
            (
                p for p in lang_root.rglob("*")
                if p.is_dir() and "(Alt)" not in p.name
            ),
            key=lambda p: len(p.parts),
            reverse=True,
        )
        for folder in dirs:
            generar_indice_carpeta(lang, folder)

        labels = ROOT_LABELS[lang]
        titulo_raiz = "Español" if lang == "ES" else "English"
        raiz = [f"# {titulo_raiz}", ""]
        for folder_name, label in labels.items():
            folder = lang_root / folder_name
            if not folder.exists():
                raise SystemExit(f"Falta carpeta raíz esperada: {folder}")
            idx = folder / index_name(folder)
            raiz.append(f"- {rel_wikilink(lang_root, idx, label)}")
        raiz.append("")
        root_file = lang_root / ("00-Espanol-Index.md" if lang == "ES" else "00-English-Index.md")
        root_file.write_text("\n".join(raiz), encoding="utf-8")


def main() -> int:
    limpiar_indices_generados()
    for catalogo in CATALOGOS:
        generar_alt(catalogo)
    generar_indices_normales()
    print("Índices de navegación regenerados sin contadores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
