#!/usr/bin/env python3
"""Genera índices auxiliares (Alt) para navegar custom/main en Obsidian.

Los (Alt) contienen solo wikilinks hacia notas canónicas. No contienen texto
normativo y custom/corpus los descarta por completo.
"""

from __future__ import annotations

import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ocho rangos compartidos por ES y EN para mantener la misma vista de navegación.
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
    excluir: frozenset[str] = frozenset()


CATALOGOS = [
    Catalogo("ES/Animales", "ES/Animales (Alt)", "Animales"),
    Catalogo("EN/Animals", "EN/Animals (Alt)", "Animals"),
    Catalogo(
        "ES/Conjuros", "ES/Conjuros (Alt)", "Conjuros",
        frozenset({"Conjuros", "ObtenerConjuros", "LanzarConjuros"}),
    ),
    Catalogo(
        "EN/Spells", "EN/Spells (Alt)", "Spells",
        frozenset({"Spells", "Gaining Spells", "Casting Spells"}),
    ),
    Catalogo("ES/MonstruosDeLaAALaZ", "ES/MonstruosDeLaAALaZ (Alt)", "Monstruos A-Z"),
    Catalogo("EN/Monsters A-Z", "EN/Monsters A-Z (Alt)", "Monsters A-Z"),
    Catalogo(
        "ES/ObjetosMagicos", "ES/ObjetosMagicos (Alt)", "Objetos mágicos",
        frozenset({
            "ObjetosMagicos", "CategoriasDeObjetosMagicos", "RarezaDeLosObjetosMagicos",
            "ActivarUnObjetoMagico", "ElSiguienteAmanecer", "ObjetosMalditos",
            "ResistenciaDeLosObjetosMagicos", "FabricarObjetosMagicos",
            "ObjetosMagicosConscientes", "ReglasDeObjetosMagicos",
        }),
    ),
    Catalogo(
        "EN/Magic Items", "EN/Magic Items (Alt)", "Magic Items",
        frozenset({
            "Magic Items", "Magic Item Categories", "Magic Item Rarity",
            "Activating a Magic Item", "The Next Dawn", "Cursed Items",
            "Magic Item Resilience", "Crafting Magic Items",
            "Sentient Magic Items", "Magic Item Rules",
        }),
    ),
]


def frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return ""
    fin = texto.find("\n---\n", 4)
    return texto[4:fin] if fin >= 0 else ""


def titulo(path: Path) -> str:
    texto = path.read_text(encoding="utf-8")
    for linea in texto.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", linea)
        if m:
            return re.sub(r"[*_]", "", m.group(1)).strip()
    return path.stem


def es_callout(path: Path) -> bool:
    fm = frontmatter(path.read_text(encoding="utf-8"))
    return bool(re.search(r"tags:\s*\[[^\]]*\b(?:recuadro|callout)\b", fm, re.IGNORECASE))


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


def generar(catalogo: Catalogo) -> None:
    origen = ROOT / catalogo.origen
    destino = ROOT / catalogo.destino

    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)

    grupos: dict[str, list[tuple[str, str]]] = {r[0]: [] for r in RANGOS}

    for path in sorted(origen.glob("*.md")):
        if path.name.endswith("-Index.md") or path.stem in catalogo.excluir or es_callout(path):
            continue
        nombre = titulo(path)
        grupos[rango_de(nombre)].append((nombre, path.stem))

    raiz = [
        f"# {catalogo.nombre} — índice alternativo",
        "",
        "Índice generado para navegación en Obsidian. No contiene texto normativo.",
        "",
    ]

    for rango, _, _ in RANGOS:
        archivo = f"{catalogo.nombre} {rango}"
        entradas = sorted(grupos[rango], key=lambda x: x[0].casefold())
        cuerpo = [
            f"# {archivo}",
            "",
            f"**Entradas:** {len(entradas)}",
            "",
            *[
                f"- [[{catalogo.origen.split('/', 1)[1]}/{stem}|{nombre}]]"
                for nombre, stem in entradas
            ],
            "",
        ]
        (destino / f"{archivo}.md").write_text("\n".join(cuerpo), encoding="utf-8")
        raiz.append(f"- [[{catalogo.destino.split('/', 1)[1]}/{archivo}|{rango}]]")

    raiz += ["", f"**Total:** {sum(len(x) for x in grupos.values())}", ""]
    (destino / f"{catalogo.nombre} (Alt).md").write_text("\n".join(raiz), encoding="utf-8")


def main() -> int:
    for catalogo in CATALOGOS:
        generar(catalogo)
    print("Índices Obsidian (Alt) regenerados de forma simétrica.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
